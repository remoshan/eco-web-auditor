"""
app/database.py
───────────────
Async SQLAlchemy engine, session factory, and base model class.

Usage (in route handlers):
    async def my_route(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(MyModel))
"""

import logging

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)

# ── Engine ────────────────────────────────────────────────────────────────────
# echo=True logs every SQL statement – useful during development.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Checks connection health before use
)

# ── Session factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keeps objects usable after commit
)


# ── Declarative base ──────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """All ORM models inherit from this base class."""
    pass


# ── Dependency ────────────────────────────────────────────────────────────────
async def get_db():
    """
    FastAPI dependency that provides a database session per request.
    Automatically rolls back on error and always closes the session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Table creation ────────────────────────────────────────────────────────────
async def create_tables() -> None:
    """
    Create all database tables on application startup.
    Safe to call multiple times (uses CREATE IF NOT EXISTS semantics).
    """
    async with engine.begin() as conn:
        # Import models here so Base knows about them before create_all
        from app.models import audit  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialised successfully.")
