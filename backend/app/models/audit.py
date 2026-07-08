"""
app/models/audit.py
───────────────────
SQLAlchemy ORM models for storing audit results.

Two tables:
  - audits       : One row per URL audit (summary-level data)
  - audit_assets : One row per discovered asset within an audit
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Audit(Base):
    """
    Represents a complete website carbon audit.
    Stores summary metrics for a single URL submission.
    """

    __tablename__ = "audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)

    # ── Carbon metrics ────────────────────────────────────────────────────────
    total_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    total_co2: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    annual_co2_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # ── Grade & score ─────────────────────────────────────────────────────────
    grade: Mapped[str] = mapped_column(String(3), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── Page stats ────────────────────────────────────────────────────────────
    page_weight_mb: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── Timestamp ─────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationship ──────────────────────────────────────────────────────────
    assets: Mapped[list["AuditAsset"]] = relationship(
        "AuditAsset",
        back_populates="audit",
        cascade="all, delete-orphan",
        lazy="selectin",  # Eagerly load assets when audit is fetched
    )

    def __repr__(self) -> str:
        return f"<Audit id={self.id} grade={self.grade} url={self.url[:40]}>"


class AuditAsset(Base):
    """
    Represents a single external asset discovered during a page audit.
    Each asset has its own CO2 estimate derived from the SWD model.
    """

    __tablename__ = "audit_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key back to the parent audit
    audit_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("audits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Asset identity ────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    asset_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # image | script | css | font | media | other

    # ── Size & carbon ─────────────────────────────────────────────────────────
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    co2_grams: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # ── Status ────────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # green | amber | red
    optimization_tip: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationship ──────────────────────────────────────────────────────────
    audit: Mapped["Audit"] = relationship("Audit", back_populates="assets")

    def __repr__(self) -> str:
        return (
            f"<AuditAsset {self.asset_type} {self.name!r} "
            f"{self.size_bytes}B status={self.status}>"
        )
