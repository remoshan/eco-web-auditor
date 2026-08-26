"""Application-wide settings, loaded from the .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:password@localhost:5432/ecoweb_db"
    )

    # Comma-separated rather than a List[str] so pydantic-settings doesn't try to JSON-decode it before it can be split in main.py.
    ALLOWED_ORIGINS: str = (
        "http://localhost:5500,http://127.0.0.1:5500,"
        "http://localhost:3000,null"
    )

    SCRAPER_TIMEOUT: int = 30
    MAX_ASSETS_PER_PAGE: int = 80

    DEBUG: bool = False
    APP_TITLE: str = "EcoWeb Auditor API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "A tool for estimating and visualising the carbon footprint "
        "of web pages via element-level analysis."
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
