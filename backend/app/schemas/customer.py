"""
SENTINEL — Customer Pydantic schemas (v2).
"""

from __future__ import annotations

from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict


class CustomerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: str
    total_transactions: int
    avg_amount: float
    median_amount: float
    std_amount: float
    min_amount: float
    max_amount: float
    common_city: str
    common_country: str
    common_merchant_category: str
    common_payment_method: str
    common_device_type: str
    avg_hour: float
    transactions_per_day: float
    fraud_count: int
    last_updated: datetime


class CustomerListResponse(BaseModel):
    total: int
    page: int
    limit: int
    pages: int
    data: List[CustomerProfileResponse]
