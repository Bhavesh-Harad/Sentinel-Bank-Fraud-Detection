"""
SENTINEL — Alert service.
Alert feed management with filtering and mark-as-read.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert


class AlertService:

    @staticmethod
    async def get_alerts(
        db: AsyncSession,
        limit: int = 50,
        risk_level: Optional[str] = None,
        unread_only: bool = False,
    ) -> list[dict[str, Any]]:
        """Fetch recent alerts, optionally filtered."""
        q = select(Alert).order_by(Alert.created_at.desc())
        if risk_level:
            q = q.where(Alert.risk_level == risk_level)
        if unread_only:
            q = q.where(Alert.is_read == False)
        q = q.limit(limit)

        alerts = (await db.execute(q)).scalars().all()
        return [
            {
                "id": a.id,
                "alert_id": str(a.id),
                "transaction_id": a.transaction_id,
                "customer_id": a.customer_id,
                "risk_level": a.risk_level,
                "risk_score": a.risk_score,
                "alert_type": a.alert_type,
                "message": a.message,
                "city": a.city,
                "amount": a.amount,
                "is_read": a.is_read,
                "timestamp": a.created_at.isoformat() if a.created_at else "",
                "created_at": a.created_at,
            }
            for a in alerts
        ]

    @staticmethod
    async def mark_as_read(db: AsyncSession, alert_id: int) -> Optional[dict[str, Any]]:
        """Mark an alert as read and return the updated record."""
        q = update(Alert).where(Alert.id == alert_id).values(is_read=True)
        await db.execute(q)
        await db.commit()
        # Re-fetch the updated alert (SQLite doesn't support RETURNING)
        fetch_q = select(Alert).where(Alert.id == alert_id)
        a = (await db.execute(fetch_q)).scalar_one_or_none()
        if not a:
            return None
        return {
            "id": a.id,
            "alert_id": str(a.id),
            "transaction_id": a.transaction_id,
            "customer_id": a.customer_id,
            "risk_level": a.risk_level,
            "risk_score": a.risk_score,
            "alert_type": a.alert_type,
            "message": a.message,
            "city": a.city,
            "amount": a.amount,
            "is_read": a.is_read,
            "timestamp": a.created_at.isoformat() if a.created_at else "",
            "created_at": a.created_at,
        }

    @staticmethod
    async def get_unread_count(db: AsyncSession) -> int:
        q = select(func.count(Alert.id)).where(Alert.is_read == False)
        return (await db.execute(q)).scalar() or 0
