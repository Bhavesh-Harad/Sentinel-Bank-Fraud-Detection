"""
SENTINEL — Prediction & RiskFactor Pydantic schemas (v2).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class RiskFactorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_id: str
    factor_name: str
    factor_score: float
    factor_weight: float
    weighted_contribution: float
    explanation: str


class PredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_id: str
    anomaly_score: float
    reconstruction_error: float
    risk_score: float
    risk_level: str
    prediction: str
    actual_label: Optional[int] = None
    created_at: datetime
