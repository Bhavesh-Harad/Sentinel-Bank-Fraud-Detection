"""
SENTINEL Fraud Detection Platform — FastAPI application entry point.

Registers all routers, middleware, and lifespan handlers.
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import create_tables

# ── Import all models so metadata is populated ────────────────────────────────
import app.models  # noqa: F401

# ── Routers ───────────────────────────────────────────────────────────────────
from app.api.transactions import router as transactions_router
from app.api.analyze import router as analyze_router
from app.api.customers import router as customers_router
from app.api.alerts import router as alerts_router
from app.api.analytics import router as analytics_router
from app.api.model import router as model_router
from app.api.geospatial import router as geospatial_router
from app.api.reports import router as reports_router

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create database tables on startup."""
    logger.info("SENTINEL backend starting up …")
    try:
        await create_tables()
        logger.info("Database tables verified/created ✓")
    except Exception as exc:
        logger.error(f"Database initialisation failed: {exc}")
    yield
    logger.info("SENTINEL backend shutting down.")


# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="SENTINEL AI Fraud Detection API",
    description=(
        "Real-time fraud detection powered by a deep autoencoder and "
        "10-component hybrid risk engine. Analyses bank transactions and "
        "returns risk scores, factor breakdowns, and human-readable explanations."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request logging middleware ────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    t_start = time.time()
    response = await call_next(request)
    duration = (time.time() - t_start) * 1000
    logger.info(
        f"{request.method} {request.url.path} → {response.status_code} "
        f"({duration:.1f} ms)"
    )
    return response


# ── Error handlers ────────────────────────────────────────────────────────────
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "The requested resource was not found.", "path": str(request.url.path)},
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.exception(f"Unhandled exception on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """Lightweight health probe — returns service status and version."""
    return {
        "status": "healthy",
        "service": "SENTINEL Fraud Detection API",
        "version": "1.0.0",
    }


# ── Register all routers ──────────────────────────────────────────────────────
API_PREFIX = "/api"

app.include_router(transactions_router, prefix=API_PREFIX)
app.include_router(analyze_router, prefix=API_PREFIX)
app.include_router(customers_router, prefix=API_PREFIX)
app.include_router(alerts_router, prefix=API_PREFIX)
app.include_router(analytics_router, prefix=API_PREFIX)
app.include_router(model_router, prefix=API_PREFIX)
app.include_router(geospatial_router, prefix=API_PREFIX)
app.include_router(reports_router, prefix=API_PREFIX)
