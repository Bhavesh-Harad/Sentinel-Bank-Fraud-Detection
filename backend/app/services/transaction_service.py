"""
SENTINEL — Transaction service.
Business logic for transaction CRUD and risk data joins.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from sqlalchemy import select, func, and_, or_, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.models.fraud_prediction import FraudPrediction
from app.models.risk_factor import RiskFactor


class TransactionService:

    @staticmethod
    async def get_transactions(
        db: AsyncSession,
        page: int = 1,
        limit: int = 50,
        risk_level: Optional[str] = None,
        city: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        search: Optional[str] = None,
        amount_min: Optional[float] = None,
        amount_max: Optional[float] = None,
    ) -> dict[str, Any]:
        """Paginated, filterable transaction list with joined prediction data."""
        offset = (page - 1) * limit

        # Base query — left-join predictions
        base = (
            select(
                Transaction,
                FraudPrediction.risk_score,
                FraudPrediction.risk_level,
                FraudPrediction.anomaly_score,
                FraudPrediction.prediction,
            )
            .outerjoin(
                FraudPrediction,
                Transaction.transaction_id == FraudPrediction.transaction_id,
            )
        )

        filters = []
        if risk_level:
            filters.append(FraudPrediction.risk_level == risk_level)
        if city:
            filters.append(Transaction.city.ilike(f"%{city}%"))
        if date_from:
            from datetime import date as d_type
            filters.append(Transaction.transaction_date >= date_from)
        if date_to:
            filters.append(Transaction.transaction_date <= date_to)
        if search:
            filters.append(
                or_(
                    Transaction.transaction_id.ilike(f"%{search}%"),
                    Transaction.customer_id.ilike(f"%{search}%"),
                    Transaction.city.ilike(f"%{search}%"),
                )
            )
        if amount_min is not None:
            filters.append(Transaction.transaction_amount >= amount_min)
        if amount_max is not None:
            filters.append(Transaction.transaction_amount <= amount_max)

        if filters:
            base = base.where(and_(*filters))

        # Count
        count_q = select(func.count()).select_from(base.subquery())
        total_result = await db.execute(count_q)
        total = total_result.scalar() or 0

        # Paged data
        data_q = base.order_by(Transaction.timestamp.desc()).offset(offset).limit(limit)
        rows = (await db.execute(data_q)).all()

        transactions = []
        for row in rows:
            txn = row[0]
            d = {
                "id": txn.id,
                "transaction_id": txn.transaction_id,
                "customer_id": txn.customer_id,
                "timestamp": txn.timestamp,
                "city": txn.city,
                "country": txn.country,
                "transaction_amount": txn.transaction_amount,
                "amount": txn.transaction_amount,
                "merchant_category": txn.merchant_category,
                "payment_method": txn.payment_method,
                "device_type": txn.device_type,
                "is_fraud": txn.is_fraud,
                "fraud_type": txn.fraud_type,
                "is_international": txn.is_international,
                "is_night_transaction": txn.is_night_transaction,
                "distance_from_home_km": txn.distance_from_home_km,
                "risk_score": round(row[1], 2) if row[1] is not None else 0.0,
                "risk_level": row[2],
                "anomaly_score": row[3],
                "prediction": row[4],
                "created_at": txn.created_at,
            }
            transactions.append(d)

        pages = math.ceil(total / limit) if limit > 0 else 1
        return {"total": total, "page": page, "limit": limit, "pages": pages, "total_pages": pages, "transactions": transactions, "data": transactions}

    @staticmethod
    async def get_transaction_detail(
        db: AsyncSession, transaction_id: str
    ) -> Optional[dict[str, Any]]:
        """Full transaction detail with risk factors."""
        q = (
            select(
                Transaction,
                FraudPrediction.anomaly_score,
                FraudPrediction.reconstruction_error,
                FraudPrediction.risk_score,
                FraudPrediction.risk_level,
                FraudPrediction.prediction,
            )
            .outerjoin(
                FraudPrediction,
                Transaction.transaction_id == FraudPrediction.transaction_id,
            )
            .where(Transaction.transaction_id == transaction_id)
        )
        result = await db.execute(q)
        row = result.first()
        if not row:
            return None

        txn = row[0]
        # Risk factors
        rf_q = select(RiskFactor).where(RiskFactor.transaction_id == transaction_id)
        rf_rows = (await db.execute(rf_q)).scalars().all()
        risk_factors = [
            {
                "id": rf.id,
                "factor_name": rf.factor_name,
                "factor_score": rf.factor_score,
                "factor_weight": rf.factor_weight,
                "weighted_contribution": rf.weighted_contribution,
                "explanation": rf.explanation,
            }
            for rf in rf_rows
        ]

        return {
            "id": txn.id,
            "transaction_id": txn.transaction_id,
            "customer_id": txn.customer_id,
            "transaction_date": txn.transaction_date,
            "transaction_time": txn.transaction_time,
            "timestamp": txn.timestamp,
            "hour_of_day": txn.hour_of_day,
            "is_weekend": txn.is_weekend,
            "is_night_transaction": txn.is_night_transaction,
            "country": txn.country,
            "city": txn.city,
            "latitude": txn.latitude,
            "longitude": txn.longitude,
            "merchant_category": txn.merchant_category,
            "payment_method": txn.payment_method,
            "device_type": txn.device_type,
            "customer_age": txn.customer_age,
            "credit_score": txn.credit_score,
            "account_age_years": txn.account_age_years,
            "account_balance": txn.account_balance,
            "transaction_amount": txn.transaction_amount,
            "num_prev_transactions": txn.num_prev_transactions,
            "transaction_freq_monthly": txn.transaction_freq_monthly,
            "distance_from_home_km": txn.distance_from_home_km,
            "time_since_last_txn_hrs": txn.time_since_last_txn_hrs,
            "is_international": txn.is_international,
            "failed_attempts": txn.failed_attempts,
            "pin_changed_recently": txn.pin_changed_recently,
            "is_fraud": txn.is_fraud,
            "fraud_type": txn.fraud_type,
            "created_at": txn.created_at,
            "anomaly_score": round(row[1], 4) if row[1] is not None else 0.0,
            "reconstruction_error": round(row[2], 6) if row[2] is not None else 0.0,
            "risk_score": round(row[3], 2) if row[3] is not None else 0.0,
            "risk_level": row[4],
            "prediction": row[5],
            "risk_factors": risk_factors,
        }
