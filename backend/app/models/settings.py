"""
Settings models for storing configuration in database.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from ..core.database import Base
from pydantic import BaseModel
from typing import Optional


class AppSettings(Base):
    """Application settings stored in database."""

    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Pydantic models for API


class NautobotSettings(BaseModel):
    """Nautobot configuration settings."""

    url: Optional[str] = None
    token: Optional[str] = None
    timeout: int = 30
    verify_ssl: bool = True


class CheckMKSettings(BaseModel):
    """CheckMK configuration settings."""

    url: Optional[str] = None
    site: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30
    verify_ssl: bool = True


class CacheSettings(BaseModel):
    """Cache configuration settings."""

    enabled: bool = True
    ttl_seconds: int = 600
    prefetch_on_startup: bool = True
    refresh_interval_minutes: int = 0
    prefetch_items: dict = {"devices": False, "locations": False, "statistics": True}


class AppSettingsUpdate(BaseModel):
    """Settings update model."""

    key: str
    value: Optional[str] = None
    description: Optional[str] = None


class AppSettingsResponse(BaseModel):
    """Settings response model."""

    id: int
    key: str
    value: Optional[str]
    description: Optional[str]
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class SettingsTest(BaseModel):
    """Settings test response."""

    success: bool
    message: str
    connection_source: str = "manual_test"


class NautobotTestRequest(BaseModel):
    """Nautobot connection test request."""

    url: str
    token: str
    timeout: int = 30
    verify_ssl: bool = True


class CheckMKTestRequest(BaseModel):
    """CheckMK connection test request."""

    url: str
    site: str
    username: str
    password: str
    timeout: int = 30
    verify_ssl: bool = True


class UnifiedSettings(BaseModel):
    """Unified settings model for frontend."""

    nautobot: dict = {
        "enabled": False,
        "url": "",
        "token": "",
        "verifyTls": True,
        "timeout": 30,
    }
    checkmk: dict = {
        "enabled": False,
        "url": "",
        "site": "cmk",
        "username": "",
        "password": "",
        "verifyTls": True,
    }
    canvas: dict = {"autoSaveInterval": 60, "gridEnabled": True}
    database: dict = {
        "host": "",
        "port": 5432,
        "database": "noc_canvas",
        "username": "",
        "password": "",
        "ssl": False,
    }


class CredentialsSettings(BaseModel):
    """User credentials settings."""

    credentials: list = []


class PasswordChangeRequest(BaseModel):
    """Password change request."""

    current_password: str
    new_password: str
