"""The /api endpoints."""

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Request

from app.config import settings
from app.schemas import AuditRequest, AuditResponse, CompareRequest, CompareResponse, Methodology
from app.services import carbon, predictor
from app.services.audit import run_audit
from app.services.compare import compare_audits

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Audit"])

RATE_WINDOW_SECONDS = 60
_recent_audits: dict[str, list[float]] = {}


def rate_limit(request: Request) -> None:
    # ponytail: in-process and per-IP from the leftmost X-Forwarded-For (spoofable, resets on restart);
    # move to Redis or the edge if abuse or multiple instances make that matter.
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")
    now = time.monotonic()

    if len(_recent_audits) > 1000:
        for stale in [k for k, hits in _recent_audits.items() if now - hits[-1] > RATE_WINDOW_SECONDS]:
            del _recent_audits[stale]

    hits = [t for t in _recent_audits.get(ip, []) if now - t < RATE_WINDOW_SECONDS]
    if len(hits) >= settings.AUDITS_PER_MINUTE:
        _recent_audits[ip] = hits
        raise HTTPException(429, "Too many audits from your network. Please wait a minute and try again.",
                            headers={"Retry-After": str(RATE_WINDOW_SECONDS)})
    hits.append(now)
    _recent_audits[ip] = hits


@router.post("/audit", response_model=AuditResponse, summary="Run a carbon audit",
             dependencies=[Depends(rate_limit)])
async def audit(request: AuditRequest):
    url = str(request.url)
    try:
        result = await run_audit(url)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    except Exception:
        logger.exception("Unexpected audit failure for %s", url)
        raise HTTPException(500, "An unexpected error occurred while scraping the page.")
    logger.info("Audited %s  grade=%s  co2=%.4fg  assets=%d",
                url, result["grade"], result["total_co2"], result["request_count"])
    return result


@router.post("/compare", response_model=CompareResponse, summary="Compare two audits")
async def compare(request: CompareRequest):
    return compare_audits(request.a, request.b)


@router.get("/methodology", response_model=Methodology,
            summary="Carbon model constants, thresholds and ML model details")
async def methodology():
    return {**carbon.methodology(), "ml_model": predictor.model_info()}
