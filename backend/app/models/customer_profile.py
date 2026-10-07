"""
SENTINEL — CustomerProfile ORM model.
Aggregated behavioural statistics per customer, updated during ingestion.
"""

from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CustomerProfile(Base):
    __tablename__ = "customer_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    # ── Volume statistics ─────────────────────────────────────────────────────
    total_transactions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    median_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    std_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    min_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    max_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # ── Behavioural modes ─────────────────────────────────────────────────────
    common_city: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    common_country: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    common_merchant_category: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    common_payment_method: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    common_device_type: Mapped[str] = mapped_column(String(64), nullable=False, default="")

    # ── Temporal patterns ─────────────────────────────────────────────────────
    avg_hour: Mapped[float] = mapped_column(Float, nullable=False, default=12.0)
    transactions_per_day: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # ── Fraud history ─────────────────────────────────────────────────────────
    fraud_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── Metadata ──────────────────────────────────────────────────────────────
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CustomerProfile {self.customer_id} txns={self.total_transactions}>"
