"""
SENTINEL — Alert Pydantic schema (v2).
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_id: str
    customer_id: str
    risk_level: str
    risk_score: float
    alert_type: str
    message: str
    city: str
    amount: float
    is_read: bool
    created_at: datetime
