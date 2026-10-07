"""
SENTINEL - Database engine & session factories.
Provides both async (FastAPI) and sync (scripts/Alembic) access.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import create_engine

from app.config import settings

class Base(DeclarativeBase):
    pass

is_sqlite = "sqlite" in settings.DATABASE_URL
async_kwargs = {"echo": False}
sync_kwargs = {"echo": False}

if is_sqlite:
    async_kwargs["connect_args"] = {"check_same_thread": False}
    sync_kwargs["connect_args"] = {"check_same_thread": False}
else:
    async_kwargs.update({"pool_pre_ping": True, "pool_size": 10, "max_overflow": 20})
    sync_kwargs.update({"pool_pre_ping": True, "pool_size": 5, "max_overflow": 10})

async_engine = create_async_engine(settings.DATABASE_URL, **async_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

sync_engine = create_engine(settings.SYNC_DATABASE_URL, **sync_kwargs)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autoflush=False,
    autocommit=False,
)

async def get_db() -> AsyncSession:
    """Yield an async database session and ensure it is closed afterwards."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def create_tables() -> None:
    """Create all tables that have been defined via the ORM models."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
