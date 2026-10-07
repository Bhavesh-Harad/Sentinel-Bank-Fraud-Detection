"""
SENTINEL — Deep Autoencoder for anomaly detection.

Architecture
------------
Encoder : input → 128 → 64 → 32 → 16 (latent)
Decoder : 16   → 32  → 64 → 128 → input
Activations : ReLU
Regularisation : BatchNorm1d + Dropout(0.2) in encoder layers

AutoencoderTrainer handles epoch training, validation, threshold computation
and scoring.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

logger = logging.getLogger(__name__)


# ── Model definition ──────────────────────────────────────────────────────────
class FraudAutoencoder(nn.Module):
    """
    Symmetric deep autoencoder with BatchNorm and Dropout.

    Parameters
    ----------
    input_dim : int
        Number of input features (after preprocessing).
    latent_dim : int
        Size of the bottleneck / latent representation (default: 16).
    dropout_rate : float
        Dropout probability applied in the encoder (default: 0.2).
    """

    def __init__(
        self,
        input_dim: int,
        latent_dim: int = 16,
        dropout_rate: float = 0.2,
    ) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.dropout_rate = dropout_rate

        # ── Encoder ───────────────────────────────────────────────────────────
        self.encoder = nn.Sequential(
            # Layer 1: input → 128
            nn.Linear(input_dim, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout_rate),
            # Layer 2: 128 → 64
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout_rate),
            # Layer 3: 64 → 32
            nn.Linear(64, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout_rate),
            # Layer 4: 32 → latent
            nn.Linear(32, latent_dim),
            nn.ReLU(inplace=True),
        )

        # ── Decoder ───────────────────────────────────────────────────────────
        self.decoder = nn.Sequential(
            # Layer 1: latent → 32
            nn.Linear(latent_dim, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(inplace=True),
            # Layer 2: 32 → 64
            nn.Linear(32, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(inplace=True),
            # Layer 3: 64 → 128
            nn.Linear(64, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            # Output layer: 128 → input (no activation — reconstruction)
            nn.Linear(128, input_dim),
        )

        # Weight initialisation
        self._init_weights()

    def _init_weights(self) -> None:
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.kaiming_normal_(module.weight, mode="fan_out", nonlinearity="relu")
                if module.bias is not None:
                    nn.init.zeros_(module.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        latent = self.encoder(x)
        reconstructed = self.decoder(latent)
        return reconstructed

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """Return the latent representation."""
        return self.encoder(x)

    @property
    def architecture_description(self) -> list[str]:
        return [
            f"Encoder: {self.input_dim}→128→64→32→{self.latent_dim} (latent)",
            f"Decoder: {self.latent_dim}→32→64→128→{self.input_dim}",
            "Activations: ReLU",
            "Regularisation: BatchNorm1d + Dropout(0.2)",
        ]


# ── Trainer ───────────────────────────────────────────────────────────────────
class AutoencoderTrainer:
    """
    Training, validation and threshold logic for FraudAutoencoder.

    Parameters
    ----------
    model  : FraudAutoencoder instance
    device : torch.device to run computations on
    """

    def __init__(self, model: FraudAutoencoder, device: torch.device) -> None:
        self.model = model
        self.device = device
        self.criterion = nn.MSELoss(reduction="mean")

    # ── Training ──────────────────────────────────────────────────────────────
    def train_epoch(self, dataloader: DataLoader, optimizer: torch.optim.Optimizer) -> float:
        """Run one training epoch. Returns mean batch loss."""
        self.model.train()
        total_loss = 0.0
        n_batches = 0

        for (batch_x,) in dataloader:
            batch_x = batch_x.to(self.device)
            optimizer.zero_grad()
            reconstructed = self.model(batch_x)
            loss = self.criterion(reconstructed, batch_x)
            loss.backward()
            # Gradient clipping for stability
            nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            optimizer.step()
            total_loss += loss.item()
            n_batches += 1

        return total_loss / max(n_batches, 1)

    def validate_epoch(self, dataloader: DataLoader) -> float:
        """Run one validation pass. Returns mean batch loss."""
        self.model.eval()
        total_loss = 0.0
        n_batches = 0

        with torch.no_grad():
            for (batch_x,) in dataloader:
                batch_x = batch_x.to(self.device)
                reconstructed = self.model(batch_x)
                loss = self.criterion(reconstructed, batch_x)
                total_loss += loss.item()
                n_batches += 1

        return total_loss / max(n_batches, 1)

    # ── Reconstruction error ──────────────────────────────────────────────────
    def compute_reconstruction_error(
        self,
        features_tensor: torch.Tensor,
        batch_size: int = 4096,
    ) -> np.ndarray:
        """
        Compute per-sample MSE reconstruction error.

        Parameters
        ----------
        features_tensor : (N, D) float32 tensor
        batch_size      : mini-batch size for memory-efficient inference

        Returns
        -------
        errors : (N,) numpy array of MSE values
        """
        self.model.eval()
        errors: list[np.ndarray] = []

        with torch.no_grad():
            for start in range(0, len(features_tensor), batch_size):
                batch = features_tensor[start : start + batch_size].to(self.device)
                reconstructed = self.model(batch)
                # Per-sample MSE: mean over feature dim
                mse = ((batch - reconstructed) ** 2).mean(dim=1).cpu().numpy()
                errors.append(mse)

        return np.concatenate(errors, axis=0)

    # ── Threshold computation ─────────────────────────────────────────────────
    def compute_threshold(
        self,
        normal_errors: np.ndarray,
        percentile: float = 95.0,
    ) -> float:
        """
        Determine reconstruction-error anomaly threshold at the given
        percentile of normal-sample errors.
        """
        threshold = float(np.percentile(normal_errors, percentile))
        logger.info(
            f"Threshold computed at {percentile}th percentile = {threshold:.6f} "
            f"(max normal error = {normal_errors.max():.6f})"
        )
        return threshold

    # ── Anomaly score ─────────────────────────────────────────────────────────
    def anomaly_score(
        self,
        reconstruction_error: float | np.ndarray,
        threshold: float,
    ) -> float | np.ndarray:
        """
        Normalise reconstruction error to [0, 1] using the threshold.

        score = error / (2 × threshold)  clamped to [0, 1]

        At threshold the score ≈ 0.5; above threshold it approaches 1.
        """
        raw = np.asarray(reconstruction_error, dtype=np.float64)
        normalised = np.clip(raw / (2.0 * max(threshold, 1e-9)), 0.0, 1.0)
        if normalised.ndim == 0:
            return float(normalised)
        return normalised
