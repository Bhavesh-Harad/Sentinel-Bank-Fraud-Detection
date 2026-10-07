"""
SENTINEL — Transaction ORM model.
Maps to the `transactions` table which stores every ingested bank transaction.
"""

from datetime import date, time, datetime
from sqlalchemy import (
    BigInteger, String, Date, Time, DateTime, Integer, Float,
    Boolean, Index, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    # ── Primary key ───────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ── Identifiers ───────────────────────────────────────────────────────────
    transaction_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # ── Temporal ──────────────────────────────────────────────────────────────
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    transaction_time: Mapped[time] = mapped_column(Time, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    hour_of_day: Mapped[int] = mapped_column(Integer, nullable=False)
    is_weekend: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_night_transaction: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── Geographic ────────────────────────────────────────────────────────────
    country: Mapped[str] = mapped_column(String(128), nullable=False)
    city: Mapped[str] = mapped_column(String(128), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Transaction context ───────────────────────────────────────────────────
    merchant_category: Mapped[str] = mapped_column(String(128), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(64), nullable=False)
    device_type: Mapped[str] = mapped_column(String(64), nullable=False)

    # ── Customer attributes ───────────────────────────────────────────────────
    customer_age: Mapped[int] = mapped_column(Integer, nullable=False)
    credit_score: Mapped[int] = mapped_column(Integer, nullable=False)
    account_age_years: Mapped[float] = mapped_column(Float, nullable=False)
    account_balance: Mapped[float] = mapped_column(Float, nullable=False)

    # ── Transaction attributes ────────────────────────────────────────────────
    transaction_amount: Mapped[float] = mapped_column(Float, nullable=False)
    num_prev_transactions: Mapped[int] = mapped_column(Integer, nullable=False)
    transaction_freq_monthly: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_from_home_km: Mapped[float] = mapped_column(Float, nullable=False)
    time_since_last_txn_hrs: Mapped[float] = mapped_column(Float, nullable=False)
    is_international: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pin_changed_recently: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── Labels ────────────────────────────────────────────────────────────────
    is_fraud: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    fraud_type: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # ── Metadata ──────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # ── Compound indexes ──────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_transactions_customer_timestamp", "customer_id", "timestamp"),
        Index("ix_transactions_fraud", "is_fraud"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Transaction {self.transaction_id} amount={self.transaction_amount}>"
