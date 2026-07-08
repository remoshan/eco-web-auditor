"""
main.py
───────
EcoWeb Auditor – FastAPI Application Entry Point

BSc (Hons) Software Engineering – Final Year Project
Author  : Wilson Francis Remoshan (2541691)
Module  : Research Methodologies and Emerging Technologies

Run with:
    uvicorn main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import create_tables
from app.routes.audit import router as audit_router

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup / shutdown hook.
    On startup: ensures all database tables exist.
    On shutdown: logs a clean exit message.
    """
    logger.info("🌿  EcoWeb Auditor – starting up")
    await create_tables()
    logger.info("✅  Database ready")
    yield
    logger.info("🌿  EcoWeb Auditor – shutting down")


# ── Application instance ──────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",   # Swagger UI
    redoc_url="/redoc", # ReDoc UI
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Allows the frontend (served on a different port or via file://) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.ALLOWED_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(audit_router)


# ── Root endpoints ────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return JSONResponse(
        {
            "project": "EcoWeb Auditor",
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": "/health",
        }
    )


@app.get("/health", tags=["System"], summary="Health check")
async def health_check():
    """Returns a 200 OK when the service is running."""
    return {"status": "healthy", "service": "ecoweb-auditor"}
