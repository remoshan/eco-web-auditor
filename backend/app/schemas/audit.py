"""
app/schemas/audit.py
────────────────────
Pydantic models used for:
  - Request body validation  (what the client sends)
  - Response serialisation   (what the API returns as JSON)
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, HttpUrl, Field, field_validator


# ── Request ───────────────────────────────────────────────────────────────────

class AuditRequest(BaseModel):
    """Body for POST /api/audit"""

    url: HttpUrl = Field(
        ...,
        description="The full URL of the website to audit.",
        examples=["https://example.com"],
    )

    @field_validator("url")
    @classmethod
    def must_be_http(cls, v: HttpUrl) -> HttpUrl:
        scheme = str(v).split("://")[0]
        if scheme not in ("http", "https"):
            raise ValueError("URL must use the http or https scheme.")
        return v


# ── Nested response objects ───────────────────────────────────────────────────

class AssetInfo(BaseModel):
    """Carbon data for one individual page asset."""

    name: str
    url: str
    asset_type: str          # image | script | css | font | media | other
    size_bytes: int
    size_kb: float           # Convenience field, pre-calculated
    co2_grams: float
    status: str              # green | amber | red
    optimization_tip: Optional[str] = None

    model_config = {"from_attributes": True}


class CategoryBreakdown(BaseModel):
    """Aggregated carbon data for an asset category (used for charts)."""

    name: str                # Category label e.g. "Images"
    count: int
    total_bytes: int
    total_co2: float
    percentage: float        # Share of overall page CO2 (0–100)


class MLPrediction(BaseModel):
    """
    Independent ML-based CO2 prediction, used to cross-validate the
    SWD formula's result (research validation component).
    """

    predicted_co2_grams: float
    model_name: str
    r2_score: Optional[float] = None
    difference_pct: Optional[float] = None


# ── Primary response ──────────────────────────────────────────────────────────

class AuditResponse(BaseModel):
    """Full audit result returned by POST /api/audit."""

    audit_id: int
    url: str

    # ── Grade ─────────────────────────────────────────────────────────────────
    grade: str               # A+, A, B+, B, C, D, F
    score: int               # 0–100

    # ── Carbon metrics ────────────────────────────────────────────────────────
    total_co2: float = Field(..., description="Grams of CO2 per page visit")
    annual_co2_kg: float     # At 10,000 monthly visitors
    annual_co2_grams: float
    trees_to_offset: float   # Trees needed to offset annual emissions

    # ── Page stats ────────────────────────────────────────────────────────────
    total_bytes: int
    page_weight_mb: float
    request_count: int

    # ── Human-readable comparison ─────────────────────────────────────────────
    comparison: str          # e.g. "Equivalent to driving 18 metres in a petrol car"

    # ── Breakdown (for charts) ────────────────────────────────────────────────
    categories: List[CategoryBreakdown]

    # ── Individual assets ─────────────────────────────────────────────────────
    assets: List[AssetInfo]

    # ── ML cross-validation (research component) ─────────────────────────────
    ml_prediction: Optional[MLPrediction] = None

    model_config = {"from_attributes": True}


# ── History list item ─────────────────────────────────────────────────────────

class RecentAuditItem(BaseModel):
    """Compact summary used in the recent-audits list."""

    audit_id: int
    url: str
    grade: str
    score: int
    total_co2: float
    page_weight_mb: float
    created_at: datetime

    model_config = {"from_attributes": True}
