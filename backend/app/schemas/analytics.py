"""
SENTINEL — Analytics Pydantic schemas (v2).
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel


class OverviewResponse(BaseModel):
    total_transactions: int
    total_volume: float
    fraud_alerts: int
    high_risk_count: int
    detection_rate: float
    avg_risk_score: float
    critical_count: int
    suspicious_count: int
    normal_count: int


class FraudTrendPoint(BaseModel):
    timestamp: str
    transactions: int
    fraud_alerts: int
    fraud_rate: float


class FraudTrendResponse(BaseModel):
    period: str
    data: List[FraudTrendPoint]


class RiskDistributionItem(BaseModel):
    level: str
    count: int
    percentage: float


class RiskDistributionResponse(BaseModel):
    data: List[RiskDistributionItem]


class FraudByCategoryItem(BaseModel):
    category: str
    total: int
    fraud_count: int
    fraud_rate: float
    avg_amount: float


class FraudByCategoryResponse(BaseModel):
    data: List[FraudByCategoryItem]


class AnomalyBinItem(BaseModel):
    bin_start: float
    bin_end: float
    normal_count: int
    fraud_count: int


class AnomalyDistributionResponse(BaseModel):
    data: List[AnomalyBinItem]


class BehaviorMetric(BaseModel):
    label: str
    value: float
    unit: Optional[str] = None


class BehaviorAnalyticsResponse(BaseModel):
    avg_transaction_amount: float
    median_transaction_amount: float
    night_transaction_rate: float
    international_rate: float
    avg_failed_attempts: float
    pin_change_rate: float
    top_cities: List[dict]
    top_merchant_categories: List[dict]
    payment_method_distribution: List[dict]
    device_type_distribution: List[dict]
