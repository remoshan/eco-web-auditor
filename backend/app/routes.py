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
WINDOW_SECONDS = 60
CACHE_SECONDS = 600
CACHE_SIZE = 100
_hits: dict[str, list[float]] = {}
_cache: dict[str, tuple[float, dict]] = {}


def rate_limit(request: Request) -> None:
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or getattr(request.client, "host", "")
    now = time.monotonic()
    if len(_hits) > 1000:
        for stale in [k for k, times in _hits.items() if now - times[-1] > WINDOW_SECONDS]:
            del _hits[stale]
    _hits[ip] = [t for t in _hits.get(ip, []) if now - t < WINDOW_SECONDS]
    if len(_hits[ip]) >= settings.AUDITS_PER_MINUTE:
        raise HTTPException(429, "Too many audits from your network. Please wait a minute and try again.",
                            headers={"Retry-After": str(WINDOW_SECONDS)})
    _hits[ip].append(now)


@router.post("/audit", response_model=AuditResponse, dependencies=[Depends(rate_limit)])
async def audit(request: AuditRequest):
    url = str(request.url)
    cached = _cache.get(url)
    if cached and not request.refresh and cached[0] > time.monotonic():
        return cached[1]
    try:
        result = await run_audit(url)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    except Exception:
        logger.exception("Audit failed for %s", url)
        raise HTTPException(500, "An unexpected error occurred while scraping the page.")
    logger.info("Audited %s  grade=%s  co2=%.4fg  assets=%d", url, result["grade"], result["total_co2"],
                result["request_count"])
    _cache.pop(url, None)
    _cache[url] = (time.monotonic() + CACHE_SECONDS, result)
    if len(_cache) > CACHE_SIZE:
        del _cache[next(iter(_cache))]
    return result


@router.post("/compare", response_model=CompareResponse)
async def compare(request: CompareRequest):
    return compare_audits(request.a, request.b)


@router.get("/methodology", response_model=Methodology)
async def methodology():
    return {**carbon.methodology(), "ml_model": predictor.model_info()}
