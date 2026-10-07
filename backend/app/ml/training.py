"""
SENTINEL — Complete training pipeline for FraudAutoencoder.

Usage:
    python -m app.ml.training
    # or via scripts/train_model.py

Steps
-----
1. Load & preprocess bank_fraud.csv
2. Split: 80 % normal-only rows for train, 20 % for validation
3. Train FraudAutoencoder for up to 50 epochs with early stopping (patience=5)
4. Evaluate on full dataset using is_fraud labels
5. Save: model weights, preprocessor, threshold, metrics, training history
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm

# Allow running as a standalone script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config import settings
from app.ml.autoencoder import FraudAutoencoder, AutoencoderTrainer
from app.ml.preprocessing import FraudPreprocessor, load_and_preprocess

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── Hyperparameters ───────────────────────────────────────────────────────────
EPOCHS: int = 50
PATIENCE: int = 5
BATCH_SIZE: int = 2048
LEARNING_RATE: float = 1e-3
WEIGHT_DECAY: float = 1e-5
THRESHOLD_PERCENTILE: float = 95.0
LATENT_DIM: int = 16
RANDOM_SEED: int = 42


def _set_seed(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _get_device() -> torch.device:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")
    return device


def _make_dataloader(
    X: np.ndarray, batch_size: int, shuffle: bool = True
) -> DataLoader:
    tensor = torch.tensor(X, dtype=torch.float32)
    dataset = TensorDataset(tensor)
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, pin_memory=False)


def train(
    csv_path: str | Path | None = None,
    model_dir: str | Path | None = None,
) -> dict[str, Any]:
    """
    Full training pipeline.

    Returns a dict with paths to saved artefacts and final metrics.
    """
    _set_seed(RANDOM_SEED)

    csv_path = Path(csv_path) if csv_path else settings.data_path_resolved
    model_dir = Path(model_dir) if model_dir else settings.model_path_resolved
    model_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading data from {csv_path}")
    df = load_and_preprocess(csv_path)
    logger.info(f"Dataset loaded: {len(df):,} rows")

    # ── Split normal vs fraud ─────────────────────────────────────────────────
    if "is_fraud" in df.columns:
        normal_df = df[df["is_fraud"] == 0].copy()
        logger.info(f"Normal rows: {len(normal_df):,}  |  Fraud rows: {len(df) - len(normal_df):,}")
    else:
        normal_df = df.copy()
        logger.warning("is_fraud column not found — using all rows as normal")

    # ── Preprocess ────────────────────────────────────────────────────────────
    preprocessor = FraudPreprocessor()
    X_normal = preprocessor.fit_transform(normal_df)
    logger.info(f"Feature matrix shape: {X_normal.shape}")

    # Shuffle & split 80/20
    idx = np.random.permutation(len(X_normal))
    split = int(len(X_normal) * 0.8)
    X_train = X_normal[idx[:split]]
    X_val = X_normal[idx[split:]]
    logger.info(f"Train size: {len(X_train):,}  |  Val size: {len(X_val):,}")

    # ── Model ─────────────────────────────────────────────────────────────────
    device = _get_device()
    input_dim = X_train.shape[1]
    model = FraudAutoencoder(input_dim=input_dim, latent_dim=LATENT_DIM).to(device)
    trainer = AutoencoderTrainer(model, device)

    optimizer = torch.optim.Adam(
        model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=3
    )

    train_loader = _make_dataloader(X_train, BATCH_SIZE, shuffle=True)
    val_loader = _make_dataloader(X_val, BATCH_SIZE, shuffle=False)

    # ── Training loop ─────────────────────────────────────────────────────────
    history: list[dict] = []
    best_val_loss = float("inf")
    patience_counter = 0
    best_model_state: dict | None = None

    logger.info("Starting training …")
    epoch_bar = tqdm(range(1, EPOCHS + 1), desc="Training", unit="epoch")
    for epoch in epoch_bar:
        t0 = time.time()
        train_loss = trainer.train_epoch(train_loader, optimizer)
        val_loss = trainer.validate_epoch(val_loader)
        scheduler.step(val_loss)
        elapsed = time.time() - t0

        history.append(
            {"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss}
        )
        epoch_bar.set_postfix(
            train=f"{train_loss:.6f}",
            val=f"{val_loss:.6f}",
            best=f"{best_val_loss:.6f}",
        )
        logger.info(
            f"Epoch {epoch:3d}/{EPOCHS} | "
            f"train_loss={train_loss:.6f} | val_loss={val_loss:.6f} | "
            f"time={elapsed:.1f}s"
        )

        if val_loss < best_val_loss - 1e-7:
            best_val_loss = val_loss
            patience_counter = 0
            best_model_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        else:
            patience_counter += 1
            if patience_counter >= PATIENCE:
                logger.info(f"Early stopping at epoch {epoch} (patience={PATIENCE})")
                break

    # Restore best weights
    if best_model_state is not None:
        model.load_state_dict(best_model_state)

    # ── Threshold on validation set ───────────────────────────────────────────
    logger.info("Computing anomaly threshold on validation set …")
    X_val_tensor = torch.tensor(X_val, dtype=torch.float32)
    val_errors = trainer.compute_reconstruction_error(X_val_tensor)
    threshold = trainer.compute_threshold(val_errors, percentile=THRESHOLD_PERCENTILE)
    logger.info(f"Anomaly threshold (p{THRESHOLD_PERCENTILE}): {threshold:.6f}")

    # ── Full-dataset evaluation (using is_fraud labels) ───────────────────────
    metrics: dict[str, Any] = {}
    if "is_fraud" in df.columns:
        logger.info("Running full-dataset evaluation …")
        from sklearn.metrics import (
            precision_score, recall_score, f1_score,
            roc_auc_score, average_precision_score,
            confusion_matrix, accuracy_score,
        )

        X_all = preprocessor.transform(df)
        X_all_tensor = torch.tensor(X_all, dtype=torch.float32)
        all_errors = trainer.compute_reconstruction_error(X_all_tensor)
        anomaly_scores = trainer.anomaly_score(all_errors, threshold)

        y_true = df["is_fraud"].astype(int).values
        y_pred = (all_errors > threshold).astype(int)
        y_prob = anomaly_scores

        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel() if cm.shape == (2, 2) else (0, 0, 0, 0)

        metrics = {
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "f1": float(f1_score(y_true, y_pred, zero_division=0)),
            "roc_auc": float(roc_auc_score(y_true, y_prob)),
            "pr_auc": float(average_precision_score(y_true, y_prob)),
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "confusion_matrix": {
                "true_negative": int(tn),
                "false_positive": int(fp),
                "false_negative": int(fn),
                "true_positive": int(tp),
            },
            "threshold": float(threshold),
            "total_evaluated": int(len(y_true)),
            "fraud_detected": int(tp),
            "fraud_missed": int(fn),
        }
        logger.info(
            f"Metrics → precision={metrics['precision']:.4f} | "
            f"recall={metrics['recall']:.4f} | "
            f"f1={metrics['f1']:.4f} | "
            f"roc_auc={metrics['roc_auc']:.4f}"
        )

    # ── Save artefacts ────────────────────────────────────────────────────────
    # 1. Model weights
    model_path = model_dir / "autoencoder.pt"
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "input_dim": input_dim,
            "latent_dim": LATENT_DIM,
            "threshold": threshold,
            "feature_names": preprocessor.feature_names,
            "training_samples": len(X_train),
            "validation_samples": len(X_val),
            "epochs_trained": len(history),
            "best_val_loss": best_val_loss,
        },
        model_path,
    )
    logger.info(f"Model saved → {model_path}")

    # 2. Preprocessor
    preprocessor_path = model_dir / "preprocessor.pkl"
    preprocessor.save(preprocessor_path)

    # 3. Threshold
    threshold_path = model_dir / "threshold.json"
    threshold_data = {
        "threshold": float(threshold),
        "percentile": THRESHOLD_PERCENTILE,
        "training_samples": len(X_train),
        "validation_samples": len(X_val),
    }
    threshold_path.write_text(json.dumps(threshold_data, indent=2))
    logger.info(f"Threshold saved → {threshold_path}")

    # 4. Metrics
    if metrics:
        metrics_path = model_dir / "metrics.json"
        metrics_path.write_text(json.dumps(metrics, indent=2))
        logger.info(f"Metrics saved → {metrics_path}")

    # 5. Training history
    history_path = model_dir / "training_history.json"
    history_path.write_text(json.dumps(history, indent=2))
    logger.info(f"Training history saved → {history_path}")

    logger.info("Training complete ✓")
    return {
        "model_path": str(model_path),
        "preprocessor_path": str(preprocessor_path),
        "threshold": threshold,
        "metrics": metrics,
        "history_length": len(history),
    }


if __name__ == "__main__":
    result = train()
    print("\n=== Training Summary ===")
    print(f"Threshold      : {result['threshold']:.6f}")
    print(f"Epochs trained : {result['history_length']}")
    if result["metrics"]:
        m = result["metrics"]
        print(f"Precision      : {m.get('precision', 0):.4f}")
        print(f"Recall         : {m.get('recall', 0):.4f}")
        print(f"F1 Score       : {m.get('f1', 0):.4f}")
        print(f"ROC-AUC        : {m.get('roc_auc', 0):.4f}")
