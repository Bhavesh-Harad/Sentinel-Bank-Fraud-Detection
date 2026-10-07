"""
SENTINEL Fraud Detection Platform — Application Configuration
Loads all settings from environment variables / .env file.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://sentinel:sentinel123@localhost:5432/sentinel_db",
        description="Async SQLAlchemy database URL",
    )
    SYNC_DATABASE_URL: str = Field(
        default="postgresql://sentinel:sentinel123@localhost:5432/sentinel_db",
        description="Sync SQLAlchemy database URL (used by Alembic / scripts)",
    )

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = Field(
        default="change-me-in-production-sentinel-secret-key-2024",
        description="JWT signing secret",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ── Paths ─────────────────────────────────────────────────────────────────
    MODEL_PATH: str = Field(
        default="../models",
        description="Directory where trained model artefacts are stored",
    )
    DATA_PATH: str = Field(
        default="../data/raw/bank_fraud.csv",
        description="Path to the raw bank_fraud.csv dataset",
    )

    # ── Risk Thresholds ───────────────────────────────────────────────────────
    NORMAL_THRESHOLD: float = Field(default=30.0, description="Risk score ≤ this → NORMAL")
    SUSPICIOUS_THRESHOLD: float = Field(default=60.0, description="Risk score ≤ this → SUSPICIOUS")
    HIGH_RISK_THRESHOLD: float = Field(default=80.0, description="Risk score ≤ this → HIGH_RISK; above → CRITICAL")

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = Field(
        default="http://localhost:5173",
        description="Comma-separated list of allowed CORS origins",
    )

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    # ── Helpers ───────────────────────────────────────────────────────────────
    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def model_path_resolved(self) -> Path:
        base = Path(__file__).resolve().parent.parent  # backend/
        p = Path(self.MODEL_PATH)
        return p if p.is_absolute() else (base / p).resolve()

    @property
    def data_path_resolved(self) -> Path:
        base = Path(__file__).resolve().parent.parent  # backend/
        p = Path(self.DATA_PATH)
        return p if p.is_absolute() else (base / p).resolve()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
