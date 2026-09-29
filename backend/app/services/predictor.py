"""Linear-regression CO2 estimate that cross-validates the SWD formula.

The model was trained with scikit-learn (StandardScaler + LinearRegression) and exported
to ml/model.json, so a prediction is sum(coef * (x - mean) / scale) + intercept.
"""

import json
from pathlib import Path

AGREEMENT_TOLERANCE_PCT = 15

_MODEL = json.loads((Path(__file__).parent.parent / "ml" / "model.json").read_text(encoding="utf-8"))


def build_features(html_size: int, assets: list[dict]) -> dict[str, float]:
    """Must produce every name in model.json's "features", or predictions become meaningless."""
    by_type = {t: [a["size_bytes"] / 1024 for a in assets if a["asset_type"] == t]
               for t in ("image", "script", "css", "font", "media")}
    all_kb = html_size / 1024 + sum(a["size_bytes"] for a in assets) / 1024

    features: dict[str, float] = {
        "html_size_kb": round(html_size / 1024, 2),
        "total_assets": len(assets),
        "max_single_asset_kb": round(max((a["size_bytes"] for a in assets), default=0) / 1024, 2),
    }
    for t, sizes in by_type.items():
        features[f"{t}_count"] = len(sizes)
        features[f"{t}_total_kb"] = round(sum(sizes), 2)
        features[f"{t}_avg_kb"] = round(sum(sizes) / len(sizes), 2) if sizes else 0
        features[f"max_{t}_kb"] = round(max(sizes, default=0), 2)
    for status in ("red", "amber", "green"):
        features[f"{status}_asset_count"] = sum(1 for a in assets if a["status"] == status)
    for t in ("image", "script"):
        features[f"{t}_pct_of_weight"] = round(sum(by_type[t]) / max(all_kb, 1) * 100, 1)
    return features


def predict_co2(features: dict[str, float]) -> float:
    total = _MODEL["intercept"] + sum(
        coef * (features[name] - mean) / scale
        for name, coef, mean, scale in zip(_MODEL["features"], _MODEL["coef"], _MODEL["mean"], _MODEL["scale"])
    )
    return round(max(0.0, total), 6)


def model_info() -> dict:
    return {
        "model_name": _MODEL["model_name"],
        "r2_score": round(_MODEL["r2_score"], 4),
        "mae": _MODEL["mae"],
        "rmse": _MODEL["rmse"],
        "n_samples": _MODEL["n_samples"],
        "n_features": len(_MODEL["features"]),
        "agreement_tolerance_pct": AGREEMENT_TOLERANCE_PCT,
    }
