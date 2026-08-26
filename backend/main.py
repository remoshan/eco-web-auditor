"""FastAPI application entry point.

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

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("EcoWeb Auditor starting up")
    await create_tables()
    logger.info("Database ready")
    yield
    logger.info("EcoWeb Auditor shutting down")


app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.ALLOWED_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(audit_router)


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
    return {"status": "healthy", "service": "ecoweb-auditor"}
