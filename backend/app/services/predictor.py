import json
from pathlib import Path

AGREEMENT_TOLERANCE_PCT = 15
MODEL = json.loads((Path(__file__).parent.parent / "ml" / "model.json").read_text(encoding="utf-8"))


def build_features(html_size: int, assets: list[dict]) -> dict[str, float]:
    kb = {t: [a["size_bytes"] / 1024 for a in assets if a["asset_type"] == t] for t in ("image", "script", "css", "font", "media")}
    total_kb = (html_size + sum(a["size_bytes"] for a in assets)) / 1024
    features = {
        "html_size_kb": round(html_size / 1024, 2),
        "total_assets": len(assets),
        "max_single_asset_kb": round(max((a["size_bytes"] for a in assets), default=0) / 1024, 2),
        **{f"{s}_asset_count": sum(a["status"] == s for a in assets) for s in ("red", "amber", "green")},
        **{f"{t}_pct_of_weight": round(sum(kb[t]) / max(total_kb, 1) * 100, 1) for t in ("image", "script")},
    }
    for t, sizes in kb.items():
        features |= {f"{t}_count": len(sizes), f"{t}_total_kb": round(sum(sizes), 2),
                     f"{t}_avg_kb": round(sum(sizes) / len(sizes), 2) if sizes else 0, f"max_{t}_kb": round(max(sizes, default=0), 2)}
    return features


def predict_co2(features: dict[str, float]) -> float:
    total = MODEL["intercept"] + sum(coef * (features[name] - mean) / scale for name, coef, mean, scale
                                     in zip(MODEL["features"], MODEL["coef"], MODEL["mean"], MODEL["scale"]))
    return round(max(0.0, total), 6)


def model_info() -> dict:
    return {**{k: MODEL[k] for k in ("model_name", "mae", "rmse", "n_samples")}, "r2_score": round(MODEL["r2_score"], 4),
            "n_features": len(MODEL["features"]), "agreement_tolerance_pct": AGREEMENT_TOLERANCE_PCT}
