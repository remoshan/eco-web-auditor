"""Application settings. Defaults suit local development; override with environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Comma-separated so pydantic-settings doesn't try to JSON-decode it.
    # Locally the Vite dev/preview server proxies /api, so only the deployed frontend needs CORS.
    ALLOWED_ORIGINS: str = "https://eco-web-auditor.vercel.app"

    SCRAPER_TIMEOUT: int = 30
    MAX_ASSETS_PER_PAGE: int = 80
    AUDITS_PER_MINUTE: int = 10
    ALLOW_PRIVATE_URLS: bool = False

    DEBUG: bool = False
    APP_TITLE: str = "EcoWeb Auditor API"
    APP_VERSION: str = "2.0.0"
    APP_DESCRIPTION: str = (
        "A tool for estimating and visualising the carbon footprint "
        "of web pages via element-level analysis."
    )

    model_config = SettingsConfigDict(case_sensitive=True)


settings = Settings()
