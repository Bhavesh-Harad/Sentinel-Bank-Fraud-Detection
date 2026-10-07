"""
SENTINEL — Customers API router.
GET /api/customers                — paginated list
GET /api/customers/{customer_id}  — full profile + history
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("")
async def list_customers(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    search: Optional[str] = Query(default=None, description="Filter by customer_id"),
    db: AsyncSession = Depends(get_db),
):
    """Return paginated customer profiles ordered by total transaction count."""
    return await CustomerService.get_customers(db, page=page, limit=limit, search=search)


@router.get("/{customer_id}")
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return full customer profile with recent transaction history (last 20)."""
    detail = await CustomerService.get_customer_detail(db, customer_id)
    if not detail:
        raise HTTPException(
            status_code=404,
            detail=f"Customer profile for '{customer_id}' not found.",
        )
    return detail
