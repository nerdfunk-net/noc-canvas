"""
Settings database models for storing application settings in separate database.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, Any, Dict
import os
import json

# Create separate base for settings database
SettingsBase = declarative_base()

class ApplicationSetting(SettingsBase):
    """Application settings stored in separate database."""
    __tablename__ = "application_settings"

    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String(255), index=True, nullable=False)  # Username of the owner
    category = Column(String(100), nullable=False)  # nautobot, checkmk, canvas, etc.
    key = Column(String(255), nullable=False)  # Setting key
    value = Column(Text, nullable=True)  # Setting value (JSON string)
    is_encrypted = Column(Boolean, default=False)  # Whether the value is encrypted
    description = Column(Text, nullable=True)  # Setting description
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Database setup for settings
def get_settings_db_path():
    """Get path to settings database."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    db_dir = os.path.join(base_dir, "data", "settings")
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "settings.db")


def get_settings_engine():
    """Create SQLAlchemy engine for settings database."""
    db_path = get_settings_db_path()
    database_url = f"sqlite:///{db_path}"
    return create_engine(database_url, connect_args={"check_same_thread": False})


def create_settings_tables():
    """Create settings database tables."""
    engine = get_settings_engine()
    SettingsBase.metadata.create_all(bind=engine)


def get_settings_session():
    """Get database session for settings."""
    engine = get_settings_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


# Settings utilities
def store_setting(owner: str, category: str, key: str, value: Any, is_encrypted: bool = False, description: str = None):
    """Store a setting in the database."""
    session = get_settings_session()
    try:
        # Convert value to JSON string
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value)
        else:
            value_str = str(value)

        # Check if setting already exists
        existing = session.query(ApplicationSetting).filter(
            ApplicationSetting.owner == owner,
            ApplicationSetting.category == category,
            ApplicationSetting.key == key
        ).first()

        if existing:
            existing.value = value_str
            existing.is_encrypted = is_encrypted
            existing.description = description
        else:
            setting = ApplicationSetting(
                owner=owner,
                category=category,
                key=key,
                value=value_str,
                is_encrypted=is_encrypted,
                description=description
            )
            session.add(setting)

        session.commit()
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_setting(owner: str, category: str, key: str, default_value: Any = None):
    """Get a setting from the database."""
    session = get_settings_session()
    try:
        setting = session.query(ApplicationSetting).filter(
            ApplicationSetting.owner == owner,
            ApplicationSetting.category == category,
            ApplicationSetting.key == key
        ).first()

        if not setting:
            return default_value

        # Try to parse JSON, fallback to string
        try:
            return json.loads(setting.value)
        except (json.JSONDecodeError, TypeError):
            return setting.value or default_value
    finally:
        session.close()


def get_user_settings(owner: str, category: str = None):
    """Get all settings for a user, optionally filtered by category."""
    session = get_settings_session()
    try:
        query = session.query(ApplicationSetting).filter(ApplicationSetting.owner == owner)
        if category:
            query = query.filter(ApplicationSetting.category == category)
        
        settings = query.all()
        result = {}
        
        for setting in settings:
            if setting.category not in result:
                result[setting.category] = {}
            
            # Handle encrypted values
            value = setting.value
            if setting.is_encrypted and value:
                try:
                    from .credential import decrypt_password
                    value = decrypt_password(value)
                except Exception as e:
                    # If decryption fails, return None or empty string
                    print(f"Failed to decrypt setting {setting.category}.{setting.key}: {e}")
                    value = ""
            
            # Try to parse JSON, fallback to string
            try:
                if value:
                    # First try to parse as JSON
                    parsed_value = json.loads(value)
                else:
                    parsed_value = value
            except (json.JSONDecodeError, TypeError):
                # If JSON parsing fails, handle boolean strings
                if isinstance(value, str):
                    if value.lower() == "true":
                        parsed_value = True
                    elif value.lower() == "false":
                        parsed_value = False
                    elif value.isdigit():
                        parsed_value = int(value)
                    else:
                        parsed_value = value
                else:
                    parsed_value = value
            
            result[setting.category][setting.key] = parsed_value
        
        return result
    finally:
        session.close()


def delete_setting(owner: str, category: str, key: str):
    """Delete a setting from the database."""
    session = get_settings_session()
    try:
        setting = session.query(ApplicationSetting).filter(
            ApplicationSetting.owner == owner,
            ApplicationSetting.category == category,
            ApplicationSetting.key == key
        ).first()

        if setting:
            session.delete(setting)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


# Pydantic models for API
class SettingBase(BaseModel):
    """Base setting model."""
    category: str
    key: str
    value: Optional[str] = None
    is_encrypted: bool = False
    description: Optional[str] = None


class SettingCreate(SettingBase):
    """Setting creation model."""
    pass


class SettingUpdate(BaseModel):
    """Setting update model."""
    value: Optional[str] = None
    is_encrypted: Optional[bool] = None
    description: Optional[str] = None


class SettingResponse(BaseModel):
    """Setting response model."""
    id: int
    owner: str
    category: str
    key: str
    value: Optional[str] = None
    is_encrypted: bool = False
    description: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class UserSettingsResponse(BaseModel):
    """User settings response model."""
    settings: Dict[str, Dict[str, Any]]


# Initialize settings database on import
create_settings_tables()