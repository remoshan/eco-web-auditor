import re
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator

Verdict = Literal["better", "worse", "same"]
Issue = Literal["uncompressed", "legacy_format", "no_cache"]
Amount = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Count = Annotated[int, Field(ge=0)]
SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:(?!\d)", re.I)


class AuditRequest(BaseModel):
    url: HttpUrl = Field(examples=["python.org"])
    refresh: bool = False

    @field_validator("url", mode="before")
    @classmethod
    def add_scheme(cls, v: object) -> object:
        if isinstance(v, str) and (v := v.strip()) and not SCHEME.match(v):
            return "https://" + v
        return v


class AssetInfo(BaseModel):
    name: str
    url: str
    asset_type: Literal["image", "script", "css", "font", "media"]
    size_bytes: int
    co2_grams: float
    saving_co2_grams: float
    status: Literal["green", "amber", "red"]
    issues: list[Issue]
    optimization_tip: str


class CategoryBreakdown(BaseModel):
    name: str
    count: Count
    total_bytes: Count
    total_co2: Amount
    percentage: Amount


class MLPrediction(BaseModel):
    predicted_co2_grams: float
    model_name: str
    r2_score: float
    difference_pct: float | None
    agreement: Literal["close", "divergent"] | None


class Potential(BaseModel):
    total_co2: float
    grade: str
    score: int
    saving_pct: float


class DeliveryChecks(BaseModel):
    uncompressed: int
    legacy_format: int
    no_cache: int


class GreenHosting(BaseModel):
    green: bool
    hosted_by: str | None


class CompareSide(BaseModel):
    id: str
    url: str
    audited_at: datetime
    grade: str
    score: Annotated[int, Field(ge=0, le=100)]
    total_co2: Amount


class AuditSummary(CompareSide):
    annual_co2_kg: Amount
    total_bytes: Count
    request_count: Count
    categories: list[CategoryBreakdown] = Field(max_length=10)


class AuditResponse(AuditSummary):
    rating: str
    trees_to_offset: float
    page_weight_mb: float
    comparison: str
    assets: list[AssetInfo]
    ml_prediction: MLPrediction
    potential: Potential
    green_hosting: GreenHosting | None
    delivery: DeliveryChecks


class CompareRequest(BaseModel):
    a: AuditSummary
    b: AuditSummary


class CompareRow(BaseModel):
    key: Literal["score", "total_co2", "annual_co2_kg", "total_bytes", "request_count", "category"]
    label: str
    older: float
    newer: float
    change_pct: int | None
    direction: Literal["up", "down", "same"]
    verdict: Verdict


class CompareResponse(BaseModel):
    older: CompareSide
    newer: CompareSide
    verdict: Verdict
    summary: str
    metrics: list[CompareRow]
    categories: list[CompareRow]


class GradeBand(BaseModel):
    grade: str
    max_co2: float | None
    score: int


class RatingBand(BaseModel):
    min_score: int
    label: str


class ModelInfo(BaseModel):
    model_name: str
    r2_score: float
    mae: float
    rmse: float
    n_samples: int
    n_features: int
    agreement_tolerance_pct: int


class Methodology(BaseModel):
    energy_per_gb: float
    carbon_intensity: float
    car_grams_per_km: float
    monthly_visits: int
    tree_kg_per_year: float
    grades: list[GradeBand]
    ratings: list[RatingBand]
    asset_status: dict[str, dict[str, int]]
    savings_rates: dict[str, dict[str, float]]
    compression_saving: float
    ml_model: ModelInfo
