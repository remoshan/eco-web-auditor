"""
app/config.py
─────────────
Application-wide settings loaded from the .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:password@localhost:5432/ecoweb_db"
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Stored as a plain comma-separated string to avoid pydantic-settings
    # trying to JSON-decode a List[str] field before validators can run.
    # Split into a list by main.py when passed to CORSMiddleware.
    ALLOWED_ORIGINS: str = (
        "http://localhost:5500,http://127.0.0.1:5500,"
        "http://localhost:3000,null"
    )

    # ── Scraper ───────────────────────────────────────────────────────────────
    SCRAPER_TIMEOUT: int = 30
    MAX_ASSETS_PER_PAGE: int = 80

    # ── App ───────────────────────────────────────────────────────────────────
    DEBUG: bool = False
    APP_TITLE: str = "EcoWeb Auditor API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "A tool for estimating and visualising the carbon footprint "
        "of web pages via element-level analysis. "
        "BSc (Hons) Software Engineering – Final Year Project."
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()