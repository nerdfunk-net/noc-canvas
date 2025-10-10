"""
Dynamic Settings Loader
Loads settings from database with fallback to environment variables
"""

from typing import Optional
from sqlalchemy.orm import Session
from .config import settings as env_settings
from ..models.settings import AppSettings


def get_dynamic_setting(
    db: Session, key: str, default: Optional[str] = None
) -> Optional[str]:
    """
    Get a setting value with priority:
    1. Database (latest saved value)
    2. Environment variable
    3. Default value
    """
    # Try database first
    setting = db.query(AppSettings).filter(AppSettings.key == key).first()
    if setting and setting.value:
        return setting.value

    # Fallback to environment variable
    env_value = getattr(env_settings, key, None)
    if env_value is not None:
        return str(env_value)

    # Finally use default
    return default


def get_nautobot_config(db: Session) -> dict:
    """Get Nautobot configuration from database with env fallback"""
    return {
        "url": get_dynamic_setting(db, "nautobot_url", env_settings.nautobot_url),
        "token": get_dynamic_setting(db, "nautobot_token", env_settings.nautobot_token),
        "timeout": int(
            get_dynamic_setting(
                db, "nautobot_timeout", str(env_settings.nautobot_timeout)
            )
        ),
        "verify_ssl": get_dynamic_setting(
            db, "nautobot_verify_tls", str(env_settings.nautobot_verify_ssl)
        ).lower()
        == "true",
    }


def get_checkmk_config(db: Session) -> dict:
    """Get CheckMK configuration from database with env fallback"""
    return {
        "url": get_dynamic_setting(db, "checkmk_url", env_settings.checkmk_url),
        "site": get_dynamic_setting(db, "checkmk_site", env_settings.checkmk_site),
        "username": get_dynamic_setting(
            db, "checkmk_username", env_settings.checkmk_username
        ),
        "password": get_dynamic_setting(
            db, "checkmk_password", env_settings.checkmk_password
        ),
        "verify_ssl": get_dynamic_setting(
            db, "checkmk_verify_ssl", str(env_settings.checkmk_verify_ssl)
        ).lower()
        == "true",
        "timeout": int(
            get_dynamic_setting(
                db, "checkmk_timeout", str(env_settings.checkmk_timeout)
            )
        ),
    }
