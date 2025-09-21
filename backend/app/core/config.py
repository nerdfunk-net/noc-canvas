from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application settings
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Note: Database configuration now handled via YAML config or environment variables
    # See: app.core.yaml_config for database configuration

    # CORS settings
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Redis settings for caching
    redis_url: str = "redis://localhost:6379"
    cache_ttl_seconds: int = 600  # 10 minutes default

    # Nautobot settings
    nautobot_url: Optional[str] = None
    nautobot_token: Optional[str] = None
    nautobot_timeout: int = 30
    nautobot_verify_ssl: bool = True

    # CheckMK settings
    checkmk_url: Optional[str] = None
    checkmk_site: Optional[str] = None
    checkmk_username: Optional[str] = None
    checkmk_password: Optional[str] = None
    checkmk_verify_ssl: bool = True
    checkmk_timeout: int = 30

    # Background job settings
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    class Config:
        env_file = ".env"
        # Ignore extra environment variables (like NOC_* database config vars)
        extra = "ignore"


settings = Settings()