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

    # Redis settings
    noc_redis_host: str = "localhost"
    noc_redis_port: int = 6379
    noc_redis_password: Optional[str] = None
    noc_redis_ssl: bool = False

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

    @property
    def redis_url(self) -> str:
        """Construct Redis URL with authentication."""
        scheme = "rediss" if self.noc_redis_ssl else "redis"
        if self.noc_redis_password:
            return f"{scheme}://:{self.noc_redis_password}@{self.noc_redis_host}:{self.noc_redis_port}"
        return f"{scheme}://{self.noc_redis_host}:{self.noc_redis_port}"

    @property 
    def celery_broker_url(self) -> str:
        """Construct Celery broker URL with authentication."""
        return f"{self.redis_url}/1"
        
    @property
    def celery_result_backend(self) -> str:
        """Construct Celery result backend URL with authentication."""  
        return f"{self.redis_url}/2"

    # Cache TTL settings
    cache_ttl_seconds: int = 600  # 10 minutes default

    class Config:
        env_file = ".env"
        # Ignore extra environment variables (like NOC_* database config vars)
        extra = "ignore"


settings = Settings()
