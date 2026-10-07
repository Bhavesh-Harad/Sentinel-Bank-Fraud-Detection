"""
SENTINEL — Alert ORM model.
Real-time alert feed for high-risk and critical transactions.
"""

from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, func, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ── Transaction reference ─────────────────────────────────────────────────
    transaction_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # ── Risk classification ───────────────────────────────────────────────────
    risk_level: Mapped[str] = mapped_column(
        String(16), nullable=False, comment="HIGH_RISK | CRITICAL"
    )
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)

    # ── Alert metadata ────────────────────────────────────────────────────────
    alert_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="IMPOSSIBLE_TRAVEL | AMOUNT_SPIKE | VELOCITY | NIGHT_TRANSACTION | INTERNATIONAL | BEHAVIORAL",
    )
    message: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Human-readable alert description"
    )

    # ── Contextual fields ─────────────────────────────────────────────────────
    city: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # ── State ─────────────────────────────────────────────────────────────────
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── Metadata ──────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True
    )

    __table_args__ = (
        Index("ix_alerts_risk_level_created", "risk_level", "created_at"),
        Index("ix_alerts_is_read", "is_read"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Alert {self.alert_type} txn={self.transaction_id} "
            f"score={self.risk_score:.1f} read={self.is_read}>"
        )
