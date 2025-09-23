"""
Settings models for storing configuration in database.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, UniqueConstraint
from sqlalchemy.sql import func
from ..core.database import Base
from pydantic import BaseModel, field_serializer
from typing import Optional
import enum
from datetime import datetime


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


# Device Commands models

class CommandPlatform(enum.Enum):
    """Supported device platforms."""
    IOS = "IOS"
    IOS_XE = "IOS XE"
    NEXUS = "Nexus"


class CommandParser(enum.Enum):
    """Supported command parsers."""
    TEXTFSM = "TextFSM"
    TTP = "TTP"
    SCRAPLI = "Scrapli"


class DeviceCommand(Base):
    """Device commands stored in database."""

    __tablename__ = "device_commands"

    id = Column(Integer, primary_key=True, index=True)
    command = Column(Text, nullable=False)
    display = Column(Text, nullable=True)
    platform = Column(Enum(CommandPlatform), nullable=False)
    parser = Column(Enum(CommandParser), nullable=False, default=CommandParser.TEXTFSM)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Unique constraint on command + platform combination
    __table_args__ = (
        UniqueConstraint('command', 'platform', name='unique_command_platform'),
    )


class DeviceCommandCreate(BaseModel):
    """Device command creation model."""

    command: str
    display: Optional[str] = None
    platform: CommandPlatform
    parser: CommandParser = CommandParser.TEXTFSM


class DeviceCommandUpdate(BaseModel):
    """Device command update model."""

    command: Optional[str] = None
    display: Optional[str] = None
    platform: Optional[CommandPlatform] = None
    parser: Optional[CommandParser] = None


class DeviceCommandResponse(BaseModel):
    """Device command response model."""

    id: int
    command: str
    display: Optional[str] = None
    platform: str
    parser: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @field_serializer('created_at')
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()

    @field_serializer('updated_at')
    def serialize_updated_at(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None

    @field_serializer('platform')
    def serialize_platform(self, value) -> str:
        return value.value if hasattr(value, 'value') else str(value)

    @field_serializer('parser')
    def serialize_parser(self, value) -> str:
        return value.value if hasattr(value, 'value') else str(value)
