"""
SENTINEL — Customer service.
Customer profile aggregation and lookup.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer_profile import CustomerProfile
from app.models.transaction import Transaction
from app.models.fraud_prediction import FraudPrediction


class CustomerService:

    @staticmethod
    async def get_customers(
        db: AsyncSession,
        page: int = 1,
        limit: int = 50,
        search: Optional[str] = None,
    ) -> dict[str, Any]:
        """Paginated customer profiles."""
        offset = (page - 1) * limit
        q = select(CustomerProfile)
        if search:
            q = q.where(CustomerProfile.customer_id.ilike(f"%{search}%"))

        count_q = select(func.count()).select_from(q.subquery())
        total = (await db.execute(count_q)).scalar() or 0

        data_q = q.order_by(CustomerProfile.total_transactions.desc()).offset(offset).limit(limit)
        profiles = (await db.execute(data_q)).scalars().all()

        pages = math.ceil(total / limit) if limit > 0 else 1
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
            "total_pages": pages,
            "customers": [
                {
                    "id": p.id,
                    "customer_id": p.customer_id,
                    "total_transactions": p.total_transactions,
                    "avg_amount": p.avg_amount,
                    "median_amount": p.median_amount,
                    "std_amount": p.std_amount,
                    "min_amount": p.min_amount,
                    "max_amount": p.max_amount,
                    "common_city": p.common_city,
                    "common_country": p.common_country,
                    "common_merchant_category": p.common_merchant_category,
                    "common_payment_method": p.common_payment_method,
                    "common_device_type": p.common_device_type,
                    "avg_hour": p.avg_hour,
                    "transactions_per_day": p.transactions_per_day,
                    "fraud_count": p.fraud_count,
                    "last_updated": p.last_updated,
                }
                for p in profiles
            ],
        }

    @staticmethod
    async def get_customer_detail(
        db: AsyncSession, customer_id: str
    ) -> Optional[dict[str, Any]]:
        """Full customer profile + recent transaction history."""
        # Profile
        profile_q = select(CustomerProfile).where(CustomerProfile.customer_id == customer_id)
        profile = (await db.execute(profile_q)).scalar_one_or_none()
        if not profile:
            return None

        # Recent transactions (last 20)
        txn_q = (
            select(
                Transaction,
                FraudPrediction.risk_score,
                FraudPrediction.risk_level,
                FraudPrediction.prediction,
            )
            .outerjoin(
                FraudPrediction,
                Transaction.transaction_id == FraudPrediction.transaction_id,
            )
            .where(Transaction.customer_id == customer_id)
            .order_by(Transaction.timestamp.desc())
            .limit(20)
        )
        rows = (await db.execute(txn_q)).all()
        recent_txns = [
            {
                "transaction_id": r[0].transaction_id,
                "timestamp": r[0].timestamp,
                "amount": r[0].transaction_amount,
                "city": r[0].city,
                "merchant_category": r[0].merchant_category,
                "risk_score": r[1],
                "risk_level": r[2],
                "prediction": r[3],
                "is_fraud": r[0].is_fraud,
            }
            for r in rows
        ]

        return {
            "id": profile.id,
            "customer_id": profile.customer_id,
            "total_transactions": profile.total_transactions,
            "avg_amount": profile.avg_amount,
            "median_amount": profile.median_amount,
            "std_amount": profile.std_amount,
            "min_amount": profile.min_amount,
            "max_amount": profile.max_amount,
            "common_city": profile.common_city,
            "common_country": profile.common_country,
            "common_merchant_category": profile.common_merchant_category,
            "common_payment_method": profile.common_payment_method,
            "common_device_type": profile.common_device_type,
            "avg_hour": profile.avg_hour,
            "transactions_per_day": profile.transactions_per_day,
            "fraud_count": profile.fraud_count,
            "last_updated": profile.last_updated,
            "recent_transactions": recent_txns,
        }

    @staticmethod
    async def get_customer_profile_dict(
        db: AsyncSession, customer_id: str
    ) -> Optional[dict[str, Any]]:
        """Return a plain dict suitable for the risk engine."""
        q = select(CustomerProfile).where(CustomerProfile.customer_id == customer_id)
        profile = (await db.execute(q)).scalar_one_or_none()
        if not profile:
            return None
        return {
            "customer_id": profile.customer_id,
            "avg_amount": profile.avg_amount,
            "median_amount": profile.median_amount,
            "std_amount": profile.std_amount,
            "min_amount": profile.min_amount,
            "max_amount": profile.max_amount,
            "common_city": profile.common_city,
            "common_country": profile.common_country,
            "common_merchant_category": profile.common_merchant_category,
            "common_payment_method": profile.common_payment_method,
            "common_device_type": profile.common_device_type,
            "avg_hour": profile.avg_hour,
            "transactions_per_day": profile.transactions_per_day,
            "fraud_count": profile.fraud_count,
        }
