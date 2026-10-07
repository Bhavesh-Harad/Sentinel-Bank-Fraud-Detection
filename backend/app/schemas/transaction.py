"""
SENTINEL — Transaction Pydantic schemas (v2).
"""

from __future__ import annotations

from datetime import date, time, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class TransactionBase(BaseModel):
    transaction_id: str
    customer_id: str
    transaction_date: date
    transaction_time: time
    timestamp: datetime
    hour_of_day: int
    is_weekend: bool
    is_night_transaction: bool
    country: str
    city: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    merchant_category: str
    payment_method: str
    device_type: str
    customer_age: int
    credit_score: int
    account_age_years: float
    account_balance: float
    transaction_amount: float
    num_prev_transactions: int
    transaction_freq_monthly: int
    distance_from_home_km: float
    time_since_last_txn_hrs: float
    is_international: bool
    failed_attempts: int
    pin_changed_recently: bool
    is_fraud: Optional[bool] = None
    fraud_type: Optional[str] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_id: str
    customer_id: str
    timestamp: datetime
    city: str
    country: str
    transaction_amount: float
    merchant_category: str
    payment_method: str
    device_type: str
    is_fraud: Optional[bool] = None
    fraud_type: Optional[str] = None
    is_international: bool
    is_night_transaction: bool
    distance_from_home_km: float
    # Joined from fraud_predictions (may be None when model not run yet)
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    anomaly_score: Optional[float] = None
    prediction: Optional[str] = None
    created_at: datetime


class TransactionDetail(TransactionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    anomaly_score: Optional[float] = None
    reconstruction_error: Optional[float] = None
    prediction: Optional[str] = None
    risk_factors: Optional[List[dict]] = None


class TransactionListResponse(BaseModel):
    total: int
    page: int
    limit: int
    pages: int
    data: List[TransactionResponse]
