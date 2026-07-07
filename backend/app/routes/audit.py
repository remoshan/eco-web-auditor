"""
app/routes/audit.py
───────────────────
FastAPI router defining all /api/* endpoints.

Endpoints:
  POST /api/audit            – Submit a URL for auditing
  GET  /api/audits/recent    – List recent audit results
  GET  /api/audit/{id}       – Retrieve a specific audit by ID
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.audit import Audit, AuditAsset
from app.schemas.audit import (
    AuditRequest,
    AuditResponse,
    AssetInfo,
    CategoryBreakdown,
    RecentAuditItem,
)
from app.services.carbon import (
    calculate_co2_grams,
    calculate_annual_metrics,
    get_asset_status,
    get_grade_and_score,
    get_optimization_tip,
    get_real_world_comparison,
)
from app.services.scraper import scrape_page

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Audit"])


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/audit
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/audit", response_model=AuditResponse, summary="Run a carbon audit")
async def run_audit(
    request: AuditRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Accept a URL, scrape its assets, compute per-element CO2 using the SWD
    model, persist the results, and return the full audit report.
    """
    url = str(request.url)
    logger.info("Audit requested for: %s", url)

    # ── 1. Scrape ─────────────────────────────────────────────────────────────
    try:
        scrape_result = await scrape_page(url)
    except ValueError as exc:
        # Friendly error the frontend can display directly
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected scrape failure for %s", url)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while scraping the page.",
        )

    # ── 2. Calculate per-asset carbon ─────────────────────────────────────────
    assets_data: list[dict] = []
    # Start total from the HTML document itself
    total_bytes: int = scrape_result["html_size"]

    for raw in scrape_result["assets"]:
        size = raw["size_bytes"]
        total_bytes += size

        atype = raw["asset_type"]
        co2 = calculate_co2_grams(size)
        status = get_asset_status(atype, size)
        tip = get_optimization_tip(atype, status)

        assets_data.append(
            {
                "name": raw["name"],
                "url": raw["url"],
                "asset_type": atype,
                "size_bytes": size,
                "size_kb": round(size / 1024, 1),
                "co2_grams": round(co2, 6),
                "status": status,
                "optimization_tip": tip,
            }
        )

    # Sort assets from most to least carbon-intensive
    assets_data.sort(key=lambda a: a["co2_grams"], reverse=True)

    # ── 3. Page-level metrics ─────────────────────────────────────────────────
    total_co2 = calculate_co2_grams(total_bytes)
    grade, score = get_grade_and_score(total_co2)
    comparison = get_real_world_comparison(total_co2)
    annual = calculate_annual_metrics(total_co2)
    page_weight_mb = round(total_bytes / (1024 * 1024), 2)

    # ── 4. Category breakdown (for charts) ────────────────────────────────────
    category_map: dict[str, dict] = {}
    for asset in assets_data:
        atype = asset["asset_type"]
        if atype not in category_map:
            category_map[atype] = {"count": 0, "total_bytes": 0, "total_co2": 0.0}
        category_map[atype]["count"] += 1
        category_map[atype]["total_bytes"] += asset["size_bytes"]
        category_map[atype]["total_co2"] += asset["co2_grams"]

    categories: list[CategoryBreakdown] = [
        CategoryBreakdown(
            name=name.capitalize(),
            count=data["count"],
            total_bytes=data["total_bytes"],
            total_co2=round(data["total_co2"], 4),
            percentage=(
                round((data["total_co2"] / total_co2) * 100, 1)
                if total_co2 > 0 else 0.0
            ),
        )
        for name, data in sorted(
            category_map.items(), key=lambda x: -x[1]["total_co2"]
        )
    ]

    # ── 5. Persist to database ────────────────────────────────────────────────
    audit_record = Audit(
        url=url,
        total_bytes=total_bytes,
        total_co2=total_co2,
        annual_co2_kg=annual["annual_kg"],
        grade=grade,
        score=score,
        page_weight_mb=page_weight_mb,
        request_count=len(assets_data),
    )
    db.add(audit_record)
    await db.flush()  # Generates the audit ID

    for asset in assets_data:
        db.add(
            AuditAsset(
                audit_id=audit_record.id,
                name=asset["name"],
                url=asset["url"],
                asset_type=asset["asset_type"],
                size_bytes=asset["size_bytes"],
                co2_grams=asset["co2_grams"],
                status=asset["status"],
                optimization_tip=asset["optimization_tip"],
            )
        )

    await db.commit()
    await db.refresh(audit_record)
    logger.info(
        "Audit #%d saved. Grade=%s  CO2=%.4fg  Assets=%d",
        audit_record.id, grade, total_co2, len(assets_data),
    )

    # ── 6. Build and return the response ─────────────────────────────────────
    return AuditResponse(
        audit_id=audit_record.id,
        url=url,
        grade=grade,
        score=score,
        total_co2=round(total_co2, 4),
        total_bytes=total_bytes,
        page_weight_mb=page_weight_mb,
        request_count=len(assets_data),
        comparison=comparison,
        annual_co2_kg=annual["annual_kg"],
        annual_co2_grams=annual["annual_grams"],
        trees_to_offset=annual["trees_to_offset"],
        categories=categories,
        assets=[AssetInfo(**a) for a in assets_data],
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/audits/recent
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/audits/recent",
    response_model=List[RecentAuditItem],
    summary="List recent audits",
)
async def get_recent_audits(
    limit: int = Query(default=10, ge=1, le=50, description="Max results to return"),
    db: AsyncSession = Depends(get_db),
):
    """Return a summary list of the most recently completed audits."""
    result = await db.execute(
        select(Audit).order_by(desc(Audit.created_at)).limit(limit)
    )
    audits = result.scalars().all()

    return [
        RecentAuditItem(
            audit_id=a.id,
            url=a.url,
            grade=a.grade,
            score=a.score,
            total_co2=round(a.total_co2, 4),
            page_weight_mb=a.page_weight_mb,
            created_at=a.created_at,
        )
        for a in audits
    ]


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/audit/{audit_id}
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/audit/{audit_id}",
    response_model=AuditResponse,
    summary="Get audit by ID",
)
async def get_audit_by_id(audit_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve a previously stored audit report by its database ID."""
    audit_result = await db.execute(select(Audit).where(Audit.id == audit_id))
    audit = audit_result.scalar_one_or_none()

    if not audit:
        raise HTTPException(status_code=404, detail=f"Audit {audit_id} not found.")

    # Assets are eagerly loaded via the `lazy="selectin"` relationship setting
    total_co2 = audit.total_co2
    annual = calculate_annual_metrics(total_co2)

    categories_map: dict[str, dict] = {}
    assets_out: list[AssetInfo] = []

    for a in audit.assets:
        assets_out.append(
            AssetInfo(
                name=a.name,
                url=a.url,
                asset_type=a.asset_type,
                size_bytes=a.size_bytes,
                size_kb=round(a.size_bytes / 1024, 1),
                co2_grams=a.co2_grams,
                status=a.status,
                optimization_tip=a.optimization_tip,
            )
        )
        t = a.asset_type
        if t not in categories_map:
            categories_map[t] = {"count": 0, "total_bytes": 0, "total_co2": 0.0}
        categories_map[t]["count"] += 1
        categories_map[t]["total_bytes"] += a.size_bytes
        categories_map[t]["total_co2"] += a.co2_grams

    categories = [
        CategoryBreakdown(
            name=name.capitalize(),
            count=data["count"],
            total_bytes=data["total_bytes"],
            total_co2=round(data["total_co2"], 4),
            percentage=(
                round((data["total_co2"] / total_co2) * 100, 1)
                if total_co2 > 0 else 0.0
            ),
        )
        for name, data in sorted(
            categories_map.items(), key=lambda x: -x[1]["total_co2"]
        )
    ]

    return AuditResponse(
        audit_id=audit.id,
        url=audit.url,
        grade=audit.grade,
        score=audit.score,
        total_co2=round(total_co2, 4),
        total_bytes=audit.total_bytes,
        page_weight_mb=audit.page_weight_mb,
        request_count=audit.request_count,
        comparison=get_real_world_comparison(total_co2),
        annual_co2_kg=annual["annual_kg"],
        annual_co2_grams=annual["annual_grams"],
        trees_to_offset=annual["trees_to_offset"],
        categories=categories,
        assets=assets_out,
    )
