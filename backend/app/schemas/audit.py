"""Pydantic request/response schemas for the /api/audit endpoints."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, HttpUrl, Field, field_validator


class AuditRequest(BaseModel):
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


class AssetInfo(BaseModel):
    name: str
    url: str
    asset_type: str          # image | script | css | font | media | other
    size_bytes: int
    size_kb: float
    co2_grams: float
    status: str              # green | amber | red
    optimization_tip: Optional[str] = None

    model_config = {"from_attributes": True}


class CategoryBreakdown(BaseModel):
    name: str
    count: int
    total_bytes: int
    total_co2: float
    percentage: float


class MLPrediction(BaseModel):
    predicted_co2_grams: float
    model_name: str
    r2_score: Optional[float] = None
    difference_pct: Optional[float] = None

    model_config = {"protected_namespaces": ()}


class AuditResponse(BaseModel):
    audit_id: int
    url: str

    grade: str
    score: int

    total_co2: float = Field(..., description="Grams of CO2 per page visit")
    annual_co2_kg: float
    annual_co2_grams: float
    trees_to_offset: float

    total_bytes: int
    page_weight_mb: float
    request_count: int

    comparison: str

    categories: List[CategoryBreakdown]
    assets: List[AssetInfo]

    ml_prediction: Optional[MLPrediction] = None

    model_config = {"from_attributes": True}


class RecentAuditItem(BaseModel):
    audit_id: int
    url: str
    grade: str
    score: int
    total_co2: float
    page_weight_mb: float
    created_at: datetime

    model_config = {"from_attributes": True}
