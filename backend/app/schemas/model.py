"""
SENTINEL — Model info/metrics Pydantic schemas (v2).
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class ModelInfoResponse(BaseModel):
    model_name: str
    input_features: int
    latent_dim: int
    training_samples: int
    validation_samples: int
    threshold: float
    anomaly_rate: float
    model_version: str
    architecture: List[str]
    feature_names: List[str]


class ConfusionMatrix(BaseModel):
    true_negative: int
    false_positive: int
    false_negative: int
    true_positive: int


class ModelMetricsResponse(BaseModel):
    precision: float
    recall: float
    f1: float
    roc_auc: float
    pr_auc: float
    accuracy: float
    confusion_matrix: ConfusionMatrix
    threshold: float
    total_evaluated: int
    fraud_detected: int
    fraud_missed: int


class TrainingHistoryPoint(BaseModel):
    epoch: int
    train_loss: float
    val_loss: float
