"""
SENTINEL — Alerts API router.
GET   /api/alerts              — alert feed
PATCH /api/alerts/{id}/read    — mark as read
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("")
async def get_alerts(
    limit: int = Query(default=50, ge=1, le=500),
    risk_level: Optional[str] = Query(default=None, description="HIGH_RISK or CRITICAL"),
    unread_only: bool = Query(default=False, description="Only return unread alerts"),
    db: AsyncSession = Depends(get_db),
):
    """
    Return the real-time alert feed, newest first.
    Optionally filter by risk level or unread status.
    """
    alerts = await AlertService.get_alerts(
        db, limit=limit, risk_level=risk_level, unread_only=unread_only
    )
    unread_count = await AlertService.get_unread_count(db)
    return {"unread_count": unread_count, "data": alerts}


@router.patch("/{alert_id}/read")
async def mark_alert_read(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Mark an alert as read and return the updated alert."""
    updated = await AlertService.mark_as_read(db, alert_id)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found.")
    return updated
