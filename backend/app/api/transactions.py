"""
SENTINEL — Transactions API router.
GET /api/transactions          — paginated, filterable list
GET /api/transactions/{id}     — full detail with risk factors
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("")
async def list_transactions(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=50, ge=1, le=500, description="Records per page"),
    risk_level: Optional[str] = Query(default=None, description="Filter by risk level"),
    city: Optional[str] = Query(default=None, description="Filter by city (partial match)"),
    date_from: Optional[str] = Query(default=None, description="Start date YYYY-MM-DD"),
    date_to: Optional[str] = Query(default=None, description="End date YYYY-MM-DD"),
    search: Optional[str] = Query(default=None, description="Search txn/customer ID or city"),
    amount_min: Optional[float] = Query(default=None, ge=0),
    amount_max: Optional[float] = Query(default=None, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Return a paginated list of transactions with their risk scores.

    Supports filtering by risk_level, city, date range, amount range,
    and free-text search across transaction_id, customer_id, and city.
    """
    result = await TransactionService.get_transactions(
        db,
        page=page,
        limit=limit,
        risk_level=risk_level,
        city=city,
        date_from=date_from,
        date_to=date_to,
        search=search,
        amount_min=amount_min,
        amount_max=amount_max,
    )
    return result


@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Return full transaction detail including all risk factors and prediction data.
    """
    detail = await TransactionService.get_transaction_detail(db, transaction_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found.")
    return detail
