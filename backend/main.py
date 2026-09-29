import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)

app = FastAPI(title="EcoWeb Auditor API", version="2.0.0",
              description="Estimates the carbon footprint of web pages, element by element.")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.ALLOWED_ORIGINS.split(",")],
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
app.include_router(router)


@app.exception_handler(RequestValidationError)
async def readable_validation_error(_, exc: RequestValidationError):
    error = exc.errors()[0]
    field = ".".join(str(part) for part in error["loc"] if part != "body")
    message = error["msg"].removeprefix("Value error, ")
    return JSONResponse({"detail": f"{field}: {message}" if field else message}, status_code=422)


@app.get("/", include_in_schema=False)
@app.get("/health", tags=["System"])
async def health():
    return {"status": "healthy", "service": "ecoweb-auditor"}
