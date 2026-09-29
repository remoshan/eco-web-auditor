"""FastAPI application entry point. Run with: uvicorn main:app --reload --port 8000"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routes import router

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI(title=settings.APP_TITLE, version=settings.APP_VERSION, description=settings.APP_DESCRIPTION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.ALLOWED_ORIGINS.split(",")],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(router)


@app.exception_handler(RequestValidationError)
async def readable_validation_error(request: Request, exc: RequestValidationError):
    error = exc.errors()[0]
    field = ".".join(str(part) for part in error["loc"] if part != "body")
    message = error["msg"].removeprefix("Value error, ")
    return JSONResponse({"detail": f"{field}: {message}" if field else message}, status_code=422)


@app.get("/", include_in_schema=False)
async def root():
    return {"project": "EcoWeb Auditor", "version": settings.APP_VERSION, "docs": "/docs"}


@app.get("/health", tags=["System"], summary="Health check")
async def health_check():
    return {"status": "healthy", "service": "ecoweb-auditor"}
