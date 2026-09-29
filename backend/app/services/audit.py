import uuid
from datetime import datetime, timezone

from app.services import carbon, predictor
from app.services.scraper import scrape_page


async def run_audit(url: str) -> dict:
    scraped = await scrape_page(url)
    assets = []
    for asset in scraped["assets"]:
        status = carbon.get_asset_status(asset["asset_type"], asset["size_bytes"])
        assets.append({**asset, "co2_grams": carbon.calculate_co2_grams(asset["size_bytes"]), "status": status,
                       "optimization_tip": carbon.OPTIMIZATION_TIPS[asset["asset_type"]][status]})
    assets.sort(key=lambda a: a["co2_grams"], reverse=True)

    total_bytes = scraped["html_size"] + sum(a["size_bytes"] for a in assets)
    total_co2 = carbon.calculate_co2_grams(total_bytes)
    grade, score = carbon.get_grade_and_score(total_co2)
    return {
        "id": str(uuid.uuid4()),
        "url": url,
        "audited_at": datetime.now(timezone.utc),
        "grade": grade,
        "score": score,
        "rating": carbon.get_rating(score),
        "total_co2": round(total_co2, 4),
        **carbon.calculate_annual_metrics(total_co2),
        "total_bytes": total_bytes,
        "page_weight_mb": round(total_bytes / 1024 ** 2, 2),
        "request_count": len(assets),
        "comparison": carbon.get_real_world_comparison(total_co2),
        "categories": categorise(assets, total_co2),
        "assets": assets,
        "ml_prediction": ml_cross_check(scraped["html_size"], assets, total_co2),
    }


def categorise(assets: list[dict], total_co2: float) -> list[dict]:
    groups: dict[str, dict] = {}
    for a in assets:
        g = groups.setdefault(a["asset_type"], {"name": a["asset_type"].capitalize(), "count": 0, "total_bytes": 0,
                                                "total_co2": 0.0})
        g["count"] += 1
        g["total_bytes"] += a["size_bytes"]
        g["total_co2"] += a["co2_grams"]
    for g in groups.values():
        g["percentage"] = round(g["total_co2"] / total_co2 * 100, 1) if total_co2 else 0.0
        g["total_co2"] = round(g["total_co2"], 4)
    return sorted(groups.values(), key=lambda g: -g["total_co2"])


def ml_cross_check(html_size: int, assets: list[dict], swd_co2: float) -> dict:
    predicted = predictor.predict_co2(predictor.build_features(html_size, assets))
    diff = round((predicted - swd_co2) / swd_co2 * 100, 1) if swd_co2 else None
    info = predictor.model_info()
    return {
        "predicted_co2_grams": predicted,
        "model_name": info["model_name"],
        "r2_score": info["r2_score"],
        "difference_pct": diff,
        "agreement": None if diff is None else "close" if abs(diff) <= predictor.AGREEMENT_TOLERANCE_PCT else "divergent",
    }
