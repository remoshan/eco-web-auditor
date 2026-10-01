from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator

Verdict = Literal["better", "worse", "same"]


class AuditRequest(BaseModel):
    url: HttpUrl = Field(examples=["python.org"])
    refresh: bool = False

    @field_validator("url", mode="before")
    @classmethod
    def add_scheme(cls, v: object) -> object:
        if isinstance(v, str) and (v := v.strip()) and "://" not in v:
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
    optimization_tip: str


class CategoryBreakdown(BaseModel):
    name: str
    count: int
    total_bytes: int
    total_co2: float
    percentage: float


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


class GreenHosting(BaseModel):
    green: bool
    hosted_by: str | None


class CompareSide(BaseModel):
    id: str
    url: str
    audited_at: datetime
    grade: str
    score: int
    total_co2: float


class AuditSummary(CompareSide):
    annual_co2_kg: float
    total_bytes: int
    request_count: int
    categories: list[CategoryBreakdown]


class AuditResponse(AuditSummary):
    rating: str
    trees_to_offset: float
    page_weight_mb: float
    comparison: str
    assets: list[AssetInfo]
    ml_prediction: MLPrediction
    potential: Potential
    green_hosting: GreenHosting | None


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
    ml_model: ModelInfo
