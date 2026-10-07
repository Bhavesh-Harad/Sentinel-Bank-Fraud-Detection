"""
SENTINEL — Analytics API router.
All dashboard chart & KPI endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview")
async def get_overview(db: AsyncSession = Depends(get_db)):
    """
    Top-level KPI cards:
    total_transactions, total_volume, fraud_alerts, high_risk_count,
    detection_rate, avg_risk_score, critical_count, suspicious_count, normal_count
    """
    return await AnalyticsService.get_overview(db)


@router.get("/fraud-trend")
async def get_fraud_trend(
    period: str = Query(
        default="24h",
        description="Time window: '24h', '7d', or '30d'",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Time-bucketed fraud alert trend for the specified period.
    Each bucket contains: timestamp, transactions, fraud_alerts, fraud_rate.
    """
    return await AnalyticsService.get_fraud_trend(db, period=period)


@router.get("/risk-distribution")
async def get_risk_distribution(db: AsyncSession = Depends(get_db)):
    """
    Count and percentage of transactions in each risk level:
    NORMAL, SUSPICIOUS, HIGH_RISK, CRITICAL.
    """
    return await AnalyticsService.get_risk_distribution(db)


@router.get("/fraud-by-category")
async def get_fraud_by_category(db: AsyncSession = Depends(get_db)):
    """
    Per-merchant-category breakdown: total transactions, fraud count,
    fraud rate, and average transaction amount.
    """
    return await AnalyticsService.get_fraud_by_category(db)


@router.get("/anomaly-distribution")
async def get_anomaly_distribution(
    bins: int = Query(default=20, ge=5, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Histogram of anomaly scores split by normal/fraud label.
    Useful for visualising model discrimination ability.
    """
    return await AnalyticsService.get_anomaly_distribution(db, bins=bins)


@router.get("/behavior")
async def get_behavior_analytics(db: AsyncSession = Depends(get_db)):
    """
    Aggregate behavioural statistics across all transactions:
    top cities, payment methods, device types, night/international rates, etc.
    """
    return await AnalyticsService.get_behavior_analytics(db)
