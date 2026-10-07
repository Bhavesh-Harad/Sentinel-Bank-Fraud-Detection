"""
SENTINEL — Model info & metrics API router.
GET /api/model/info             — architecture and metadata
GET /api/model/metrics          — evaluation metrics
GET /api/model/training-history — per-epoch loss history
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.ml.inference import InferenceEngine, ModelNotReadyError

router = APIRouter(prefix="/model", tags=["Model"])


def _load_json(filename: str) -> dict:
    path = settings.model_path_resolved / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found. Train the model first.")
    return json.loads(path.read_text())


@router.get("/info")
async def get_model_info():
    """
    Return model architecture metadata: feature count, latent dimension,
    training/validation sample sizes, anomaly threshold, and feature list.
    """
    try:
        engine = InferenceEngine.get_instance()
    except ModelNotReadyError as e:
        raise HTTPException(status_code=503, detail=str(e))

    meta = engine.metadata
    model = engine.model

    # Determine last trained timestamp from saved model file
    import os
    from datetime import datetime
    model_file = settings.model_path_resolved / "autoencoder.pt"
    if model_file.exists():
        last_trained = datetime.fromtimestamp(os.path.getmtime(model_file)).isoformat()
    else:
        last_trained = datetime.utcnow().isoformat()

    return {
        "name": "SENTINEL Deep Autoencoder v2.4",
        "model_name": "SENTINEL Deep Autoencoder v2.4",
        "version": "v2.4.1-prod",
        "model_version": "v2.4.1-prod",
        "input_features": meta.get("input_dim", 22),
        "latent_dim": meta.get("latent_dim", 16),
        "training_samples": meta.get("training_samples", 800000),
        "validation_samples": meta.get("validation_samples", 200000),
        "threshold": round(engine.threshold, 6),
        "anomaly_rate": 0.05,
        "last_trained": last_trained,
        "architecture": model.architecture_description,
        "feature_names": engine.feature_names,
    }


@router.get("/metrics")
async def get_model_metrics():
    """
    Return evaluation metrics: precision, recall, F1, ROC-AUC, PR-AUC,
    accuracy, and structured confusion matrix.
    """
    data = _load_json("metrics.json")
    # Ensure confusion_matrix is a dict (not list)
    cm = data.get("confusion_matrix", {})
    if isinstance(cm, list):
        flat = [x for row in cm for x in (row if isinstance(row, list) else [row])]
        cm = {
            "true_negative": flat[0] if len(flat) > 0 else 0,
            "false_positive": flat[1] if len(flat) > 1 else 0,
            "false_negative": flat[2] if len(flat) > 2 else 0,
            "true_positive": flat[3] if len(flat) > 3 else 0,
        }
    data["confusion_matrix"] = cm
    return data


@router.get("/training-history")
async def get_training_history():
    """Return per-epoch train/validation loss for learning curve charts."""
    data = _load_json("training_history.json")
    # Ensure it's a list of {epoch, train_loss, val_loss}
    if isinstance(data, list):
        return {"history": data}
    return data
