"""Async SQLAlchemy engine, session factory, and declarative base."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)

AUDIT_RETENTION_DAYS = 7

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # keep ORM objects usable after commit
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    async with engine.begin() as conn:
        from app.models import audit  # noqa: F401 - registers models with Base

        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialised successfully.")


async def purge_old_audits() -> None:
    """Delete audits older than AUDIT_RETENTION_DAYS to bound storage growth.

    audit_assets rows are removed too via the DB-level ON DELETE CASCADE on
    Audit's foreign key - a bulk delete like this bypasses SQLAlchemy's ORM
    cascade option, but not Postgres's own cascade.
    """
    from app.models.audit import Audit

    cutoff = datetime.now(timezone.utc) - timedelta(days=AUDIT_RETENTION_DAYS)
    async with AsyncSessionLocal() as session:
        result = await session.execute(delete(Audit).where(Audit.created_at < cutoff))
        await session.commit()
        if result.rowcount:
            logger.info("Purged %d audit(s) older than %d days.", result.rowcount, AUDIT_RETENTION_DAYS)
