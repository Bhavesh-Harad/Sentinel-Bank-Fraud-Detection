"""
SENTINEL — Inference engine (singleton pattern).

Loads model artefacts once at startup and exposes:
- predict_single(transaction_dict) → (anomaly_score, reconstruction_error)
- predict_batch(df)                → DataFrame with anomaly scores
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
import torch

from app.config import settings
from app.ml.autoencoder import FraudAutoencoder, AutoencoderTrainer
from app.ml.preprocessing import FraudPreprocessor, load_and_preprocess

logger = logging.getLogger(__name__)

# ── Singleton state ───────────────────────────────────────────────────────────
_lock = threading.Lock()
_engine_instance: Optional["InferenceEngine"] = None


class ModelNotReadyError(RuntimeError):
    """Raised when inference is requested before the model has been loaded."""


class InferenceEngine:
    """
    Singleton inference wrapper. Call InferenceEngine.get_instance() to
    obtain the shared instance; it loads from disk on first access.
    """

    def __init__(
        self,
        model: FraudAutoencoder,
        trainer: AutoencoderTrainer,
        preprocessor: FraudPreprocessor,
        threshold: float,
        feature_names: list[str],
        metadata: dict[str, Any],
    ) -> None:
        self.model = model
        self.trainer = trainer
        self.preprocessor = preprocessor
        self.threshold = threshold
        self.feature_names = feature_names
        self.metadata = metadata
        self._ready = True

    # ── Singleton factory ─────────────────────────────────────────────────────
    @classmethod
    def get_instance(cls, model_dir: str | Path | None = None) -> "InferenceEngine":
        """Load and cache the inference engine (thread-safe singleton)."""
        global _engine_instance
        with _lock:
            if _engine_instance is None:
                _engine_instance = cls._load(model_dir)
        return _engine_instance

    @classmethod
    def reset_instance(cls) -> None:
        """Force reload on next access (useful for hot-swapping models)."""
        global _engine_instance
        with _lock:
            _engine_instance = None

    @classmethod
    def _load(cls, model_dir: str | Path | None = None) -> "InferenceEngine":
        """Load all artefacts from the model directory."""
        import json

        model_dir = Path(model_dir) if model_dir else settings.model_path_resolved
        model_path = model_dir / "autoencoder.pt"
        preprocessor_path = model_dir / "preprocessor.pkl"
        threshold_path = model_dir / "threshold.json"

        if not model_path.exists():
            raise ModelNotReadyError(
                f"Model weights not found at {model_path}. "
                "Run training first: python scripts/train_model.py"
            )
        if not preprocessor_path.exists():
            raise ModelNotReadyError(
                f"Preprocessor not found at {preprocessor_path}."
            )

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Loading model from {model_path} on {device}")

        checkpoint = torch.load(model_path, map_location=device)
        input_dim = checkpoint["input_dim"]
        latent_dim = checkpoint.get("latent_dim", 16)
        threshold = float(checkpoint.get("threshold", 0.01))
        feature_names = checkpoint.get("feature_names", [])
        metadata = {
            "input_dim": input_dim,
            "latent_dim": latent_dim,
            "threshold": threshold,
            "training_samples": checkpoint.get("training_samples", 0),
            "validation_samples": checkpoint.get("validation_samples", 0),
            "epochs_trained": checkpoint.get("epochs_trained", 0),
            "best_val_loss": checkpoint.get("best_val_loss", 0.0),
            "feature_names": feature_names,
        }

        model = FraudAutoencoder(input_dim=input_dim, latent_dim=latent_dim).to(device)
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()

        # Override threshold from threshold.json if present
        if threshold_path.exists():
            t_data = json.loads(threshold_path.read_text())
            threshold = float(t_data.get("threshold", threshold))

        preprocessor = FraudPreprocessor.load(preprocessor_path)

        trainer = AutoencoderTrainer(model, device)

        logger.info(
            f"InferenceEngine ready — input_dim={input_dim}, "
            f"latent_dim={latent_dim}, threshold={threshold:.6f}"
        )
        return cls(model, trainer, preprocessor, threshold, feature_names, metadata)

    # ── Inference helpers ─────────────────────────────────────────────────────
    def _preprocess_single(self, transaction: dict[str, Any]) -> torch.Tensor:
        """Convert a raw transaction dict to a (1, D) float32 tensor."""
        row = pd.DataFrame([transaction])
        features = self.preprocessor.transform(row)
        return torch.tensor(features, dtype=torch.float32)

    # ── Public API ────────────────────────────────────────────────────────────
    def predict_single(
        self, transaction: dict[str, Any]
    ) -> tuple[float, float]:
        """
        Score a single transaction.

        Returns
        -------
        anomaly_score        : normalised [0, 1]
        reconstruction_error : raw MSE
        """
        tensor = self._preprocess_single(transaction)
        errors = self.trainer.compute_reconstruction_error(tensor)
        reconstruction_error = float(errors[0])
        anomaly_score = float(self.trainer.anomaly_score(reconstruction_error, self.threshold))
        return anomaly_score, reconstruction_error

    def predict_batch(
        self,
        df: pd.DataFrame,
        batch_size: int = 4096,
    ) -> pd.DataFrame:
        """
        Score an entire DataFrame.

        Returns a copy of `df` with added columns:
        - reconstruction_error
        - anomaly_score
        - is_anomaly (bool, True when error > threshold)
        """
        result = df.copy()
        features = self.preprocessor.transform(df)
        tensor = torch.tensor(features, dtype=torch.float32)
        errors = self.trainer.compute_reconstruction_error(tensor, batch_size=batch_size)
        scores = self.trainer.anomaly_score(errors, self.threshold)

        result["reconstruction_error"] = errors
        result["anomaly_score"] = scores
        result["is_anomaly"] = errors > self.threshold
        return result

    def is_ready(self) -> bool:
        return self._ready
