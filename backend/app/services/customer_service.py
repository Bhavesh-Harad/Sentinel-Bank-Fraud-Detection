"""
SENTINEL — Customer service.
Customer profile aggregation and lookup.
"""

from __future__ import annotations

import math
from collections import defaultdict
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
        """
        Full customer profile with:
        - Recent 20 transactions (for the table)
        - spending_over_time: daily total amount grouped by transaction_date
          across ALL historical transactions (2020-2024 dataset)
        - hourly_distribution: count per hour-of-day (0-23) across all txns
        - category_distribution: per merchant_category count + total amount
        """
        # ── Profile ──────────────────────────────────────────────────────────
        profile_q = select(CustomerProfile).where(CustomerProfile.customer_id == customer_id)
        profile = (await db.execute(profile_q)).scalar_one_or_none()
        if not profile:
            return None

        # ── All transactions for this customer (needed for chart aggregations) ──
        all_txn_q = (
            select(Transaction)
            .where(Transaction.customer_id == customer_id)
            .order_by(Transaction.timestamp.asc())
        )
        all_txn_rows = (await db.execute(all_txn_q)).scalars().all()

        # ── Spending over time: daily totals from historical data ─────────────
        # Group by transaction_date (stored as date column)
        daily_totals: dict[str, float] = defaultdict(float)
        daily_counts: dict[str, int] = defaultdict(int)
        for txn in all_txn_rows:
            if txn.transaction_date:
                date_key = str(txn.transaction_date)  # "YYYY-MM-DD"
            elif txn.timestamp:
                date_key = txn.timestamp.strftime("%Y-%m-%d")
            else:
                continue
            daily_totals[date_key] += float(txn.transaction_amount or 0)
            daily_counts[date_key] += 1

        spending_over_time = [
            {"date": d, "amount": round(daily_totals[d], 2), "count": daily_counts[d]}
            for d in sorted(daily_totals.keys())
        ]

        # ── Hourly distribution: count per hour across all transactions ───────
        hourly: dict[int, dict] = {h: {"hour": h, "count": 0, "total_amount": 0.0} for h in range(24)}
        for txn in all_txn_rows:
            h = txn.hour_of_day if txn.hour_of_day is not None else (
                txn.timestamp.hour if txn.timestamp else None
            )
            if h is not None and 0 <= h <= 23:
                hourly[h]["count"] += 1
                hourly[h]["total_amount"] += float(txn.transaction_amount or 0)

        hourly_distribution = [
            {
                "hour": hourly[h]["hour"],
                "count": hourly[h]["count"],
                "avg_amount": round(
                    hourly[h]["total_amount"] / max(hourly[h]["count"], 1), 2
                ),
            }
            for h in range(24)
        ]

        # ── Category distribution ─────────────────────────────────────────────
        cat_counts: dict[str, dict] = defaultdict(lambda: {"count": 0, "total_amount": 0.0, "fraud_count": 0})
        for txn in all_txn_rows:
            cat = txn.merchant_category or "Other"
            cat_counts[cat]["count"] += 1
            cat_counts[cat]["total_amount"] += float(txn.transaction_amount or 0)
            if txn.is_fraud:
                cat_counts[cat]["fraud_count"] += 1

        category_distribution = sorted(
            [
                {
                    "category": cat,
                    "count": cat_counts[cat]["count"],
                    "total_amount": round(cat_counts[cat]["total_amount"], 2),
                    "fraud_count": cat_counts[cat]["fraud_count"],
                }
                for cat in cat_counts
            ],
            key=lambda x: x["count"],
            reverse=True,
        )

        # ── Recent 20 transactions (for the table, most recent first) ─────────
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

        # ── Account age from transaction date range ───────────────────────────
        account_age_days = 365  # default
        if spending_over_time:
            from datetime import datetime, date
            first_date = spending_over_time[0]["date"]
            last_date = spending_over_time[-1]["date"]
            try:
                d1 = datetime.strptime(first_date, "%Y-%m-%d").date()
                d2 = datetime.strptime(last_date, "%Y-%m-%d").date()
                account_age_days = max(1, (d2 - d1).days)
            except Exception:
                pass

        # ── Credit score (from first transaction for this customer) ───────────
        credit_score = 650  # default
        if all_txn_rows:
            credit_score = int(all_txn_rows[0].credit_score or 650)

        # ── Date range label for frontend ──────────────────────────────────────
        date_range = ""
        if spending_over_time:
            date_range = f"{spending_over_time[0]['date']} to {spending_over_time[-1]['date']}"

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
            "credit_score": credit_score,
            "account_age_days": account_age_days,
            # Chart data (computed from historical DB records)
            "spending_over_time": spending_over_time,
            "hourly_distribution": hourly_distribution,
            "category_distribution": category_distribution,
            "date_range": date_range,
            # Recent transactions for the table
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
