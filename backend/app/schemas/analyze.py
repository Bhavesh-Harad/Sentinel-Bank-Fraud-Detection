"""
SENTINEL — Analyze request/response Pydantic schemas (v2).
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Payload sent to POST /api/analyze for real-time fraud scoring."""

    customer_id: str = Field(..., example="CUST00121959")
    amount: float = Field(..., gt=0, example=1500.0)
    city: str = Field(..., example="London")
    country: str = Field(..., example="USA")
    merchant_category: str = Field(..., example="Grocery")
    payment_method: str = Field(..., example="Credit Card")
    device_type: str = Field(..., example="Mobile")
    hour_of_day: int = Field(..., ge=0, le=23, example=14)
    is_weekend: bool = Field(default=False)
    is_night_transaction: bool = Field(default=False)
    is_international: bool = Field(default=False)
    failed_attempts: int = Field(default=0, ge=0)
    pin_changed_recently: bool = Field(default=False)
    credit_score: int = Field(..., ge=300, le=850, example=700)
    account_balance: float = Field(..., example=5000.0)
    distance_from_home_km: float = Field(default=0.0, ge=0)
    time_since_last_txn_hrs: float = Field(default=24.0, ge=0)
    # Optional customer context overrides
    customer_age: Optional[int] = Field(default=42, ge=18)
    account_age_years: Optional[float] = Field(default=5.0, ge=0)
    num_prev_transactions: Optional[int] = Field(default=150, ge=0)
    transaction_freq_monthly: Optional[int] = Field(default=20, ge=0)


class RiskFactorDetail(BaseModel):
    name: str
    score: float
    weight: float
    contribution: float
    explanation: str


class AnalyzeResponse(BaseModel):
    transaction_id: str
    customer_id: str
    anomaly_score: float
    reconstruction_error: float
    risk_score: float
    risk_level: str
    prediction: str
    explanation: str
    risk_factors: List[RiskFactorDetail]
    customer_profile_used: bool
    processing_time_ms: float
