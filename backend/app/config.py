from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ALLOWED_ORIGINS: str = "https://eco-web-auditor.vercel.app"
    SCRAPER_TIMEOUT: int = 30
    MAX_ASSETS_PER_PAGE: int = 80
    AUDITS_PER_MINUTE: int = 10
    ALLOW_PRIVATE_URLS: bool = False


settings = Settings()
