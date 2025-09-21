"""
Settings API router for managing application configuration.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..core.security import verify_token
from ..core.database import get_db
from ..models.user import User
from ..models.settings import (
    AppSettings,
    AppSettingsUpdate,
    AppSettingsResponse,
    NautobotSettings,
    CheckMKSettings,
    CacheSettings,
    NautobotTestRequest,
    CheckMKTestRequest,
    SettingsTest,
    UnifiedSettings,
    CredentialsSettings,
    PasswordChangeRequest,
)
from ..services.nautobot import nautobot_service
from ..services.checkmk import checkmk_service

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user."""
    token = credentials.credentials
    token_data = verify_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = token_data["username"]
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


# Specific routes (must be before generic /{key} route)

@router.get("/unified", response_model=UnifiedSettings)
async def get_unified_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get unified settings for frontend."""
    from ..core.config import settings as app_settings

    # Build unified settings from various sources
    unified = UnifiedSettings()

    # Get stored settings from database
    stored_settings = {}
    db_settings = db.query(AppSettings).all()
    for setting in db_settings:
        stored_settings[setting.key] = setting.value

    # Nautobot settings (prefer database, fallback to environment)
    unified.nautobot = {
        "enabled": stored_settings.get("nautobot_enabled", "false").lower() == "true",
        "url": stored_settings.get("nautobot_url") or app_settings.nautobot_url or "",
        "token": "***" if (stored_settings.get("nautobot_token") or app_settings.nautobot_token) else "",
        "verifyTls": stored_settings.get("nautobot_verify_tls", str(app_settings.nautobot_verify_ssl)).lower() == "true",
        "timeout": int(stored_settings.get("nautobot_timeout", str(app_settings.nautobot_timeout)))
    }

    # CheckMK settings (prefer database, fallback to environment)
    unified.checkmk = {
        "enabled": stored_settings.get("checkmk_enabled", "false").lower() == "true",
        "url": stored_settings.get("checkmk_url") or app_settings.checkmk_url or "",
        "site": stored_settings.get("checkmk_site") or app_settings.checkmk_site or "cmk",
        "username": stored_settings.get("checkmk_username") or app_settings.checkmk_username or "",
        "password": "***" if (stored_settings.get("checkmk_password") or app_settings.checkmk_password) else "",
        "verifyTls": stored_settings.get("checkmk_verify_tls", str(app_settings.checkmk_verify_ssl)).lower() == "true"
    }

    # Canvas settings
    unified.canvas = {
        "autoSaveInterval": int(stored_settings.get("canvas_autosave_interval", "60")),
        "gridEnabled": stored_settings.get("canvas_grid_enabled", "true").lower() == "true"
    }

    # Database settings (from YAML config or environment)
    try:
        from ..core.yaml_config import load_database_config
        db_config = load_database_config()
        if db_config:
            unified.database = {
                "host": db_config.host,
                "port": db_config.port,
                "database": db_config.database,
                "username": db_config.username,
                "password": "***" if db_config.password else "",
                "ssl": db_config.ssl
            }
        else:
            # Default empty configuration
            unified.database = {
                "host": "",
                "port": 5432,
                "database": "noc_canvas",
                "username": "",
                "password": "",
                "ssl": False
            }
    except Exception as e:
        logger.warning(f"Could not load database config: {e}")
        unified.database = {
            "host": "",
            "port": 5432,
            "database": "noc_canvas",
            "username": "",
            "password": "",
            "ssl": False
        }

    return unified


@router.get("/credentials")
async def get_user_credentials(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user credentials."""
    try:
        setting = db.query(AppSettings).filter(AppSettings.key == f"user_credentials_{current_user.username}").first()
        if setting and setting.value:
            import json
            credentials = json.loads(setting.value)
            return {"credentials": credentials}
        return {"credentials": []}
    except Exception as e:
        logger.error(f"Error getting credentials: {str(e)}")
        return {"credentials": []}


# Generic routes


@router.get("/", response_model=List[AppSettingsResponse])
async def get_all_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all application settings."""
    settings = db.query(AppSettings).all()
    return settings


@router.get("/{key}", response_model=AppSettingsResponse)
async def get_setting(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get specific setting by key."""
    setting = db.query(AppSettings).filter(AppSettings.key == key).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found",
        )
    return setting


@router.post("/", response_model=AppSettingsResponse)
async def create_or_update_setting(
    setting_update: AppSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create or update a setting."""
    setting = db.query(AppSettings).filter(AppSettings.key == setting_update.key).first()

    if setting:
        # Update existing setting
        setting.value = setting_update.value
        if setting_update.description is not None:
            setting.description = setting_update.description
    else:
        # Create new setting
        setting = AppSettings(
            key=setting_update.key,
            value=setting_update.value,
            description=setting_update.description,
        )
        db.add(setting)

    db.commit()
    db.refresh(setting)
    return setting


@router.delete("/{key}")
async def delete_setting(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a setting."""
    setting = db.query(AppSettings).filter(AppSettings.key == key).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found",
        )

    db.delete(setting)
    db.commit()
    return {"message": f"Setting '{key}' deleted successfully"}


# Nautobot Settings

@router.get("/nautobot/current", response_model=NautobotSettings)
async def get_nautobot_settings(
    current_user: User = Depends(get_current_user),
):
    """Get current Nautobot settings."""
    from ..core.config import settings

    return NautobotSettings(
        url=settings.nautobot_url,
        token="***" if settings.nautobot_token else None,  # Hide actual token
        timeout=settings.nautobot_timeout,
        verify_ssl=settings.nautobot_verify_ssl,
    )


@router.post("/nautobot/test", response_model=SettingsTest)
async def test_nautobot_settings(
    test_request: NautobotTestRequest,
    current_user: User = Depends(get_current_user),
):
    """Test Nautobot connection settings."""
    try:
        success, message = await nautobot_service.test_connection(
            test_request.url,
            test_request.token,
            test_request.timeout,
            test_request.verify_ssl,
        )

        return SettingsTest(
            success=success,
            message=message,
            connection_source="manual_test",
        )
    except Exception as e:
        logger.error(f"Error testing Nautobot settings: {str(e)}")
        return SettingsTest(
            success=False,
            message=f"Test failed: {str(e)}",
            connection_source="manual_test",
        )


# CheckMK Settings

@router.get("/checkmk/current", response_model=CheckMKSettings)
async def get_checkmk_settings(
    current_user: User = Depends(get_current_user),
):
    """Get current CheckMK settings."""
    from ..core.config import settings

    return CheckMKSettings(
        url=settings.checkmk_url,
        site=settings.checkmk_site,
        username=settings.checkmk_username,
        password="***" if settings.checkmk_password else None,  # Hide actual password
        timeout=settings.checkmk_timeout,
        verify_ssl=settings.checkmk_verify_ssl,
    )


@router.post("/checkmk/test", response_model=SettingsTest)
async def test_checkmk_settings(
    test_request: CheckMKTestRequest,
    current_user: User = Depends(get_current_user),
):
    """Test CheckMK connection settings."""
    try:
        success, message = await checkmk_service.test_connection(
            test_request.url,
            test_request.site,
            test_request.username,
            test_request.password,
            test_request.verify_ssl,
        )

        return SettingsTest(
            success=success,
            message=message,
            connection_source="manual_test",
        )
    except Exception as e:
        logger.error(f"Error testing CheckMK settings: {str(e)}")
        return SettingsTest(
            success=False,
            message=f"Test failed: {str(e)}",
            connection_source="manual_test",
        )


# Cache Settings

@router.get("/cache/current", response_model=CacheSettings)
async def get_cache_settings(
    current_user: User = Depends(get_current_user),
):
    """Get current cache settings."""
    from ..core.config import settings

    return CacheSettings(
        enabled=True,  # Always enabled if Redis is available
        ttl_seconds=settings.cache_ttl_seconds,
        prefetch_on_startup=True,
        refresh_interval_minutes=0,
        prefetch_items={
            "devices": False,
            "locations": False,
            "statistics": True,
        },
    )


@router.post("/cache/clear")
async def clear_cache(
    pattern: str = "*",
    current_user: User = Depends(get_current_user),
):
    """Clear cache entries matching a pattern."""
    try:
        from ..core.cache import cache_service

        cleared_count = await cache_service.clear_pattern(pattern)
        return {
            "message": f"Cleared {cleared_count} cache entries matching pattern '{pattern}'",
            "cleared_count": cleared_count,
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}",
        )


@router.get("/cache/info")
async def get_cache_info(
    current_user: User = Depends(get_current_user),
):
    """Get cache status and information."""
    try:
        from ..core.cache import cache_service

        # Test if Redis is connected
        is_connected = cache_service.redis is not None

        if is_connected:
            # Try to ping Redis
            try:
                await cache_service.redis.ping()
                status = "connected"
                message = "Cache is connected and operational"
            except Exception:
                status = "error"
                message = "Cache connection error"
        else:
            status = "disconnected"
            message = "Cache is not connected"

        return {
            "status": status,
            "message": message,
            "redis_connected": is_connected,
        }
    except Exception as e:
        logger.error(f"Error getting cache info: {str(e)}")
        return {
            "status": "error",
            "message": f"Error getting cache info: {str(e)}",
            "redis_connected": False,
        }


@router.post("/unified")
async def save_unified_settings(
    settings_data: UnifiedSettings,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save unified settings from frontend."""
    try:
        # Save plugin enabled states and canvas settings
        settings_to_save = [
            ("nautobot_enabled", str(settings_data.nautobot.get("enabled", False))),
            ("checkmk_enabled", str(settings_data.checkmk.get("enabled", False))),
            ("canvas_autosave_interval", str(settings_data.canvas.get("autoSaveInterval", 60))),
            ("canvas_grid_enabled", str(settings_data.canvas.get("gridEnabled", True))),
        ]

        # Add Nautobot configuration settings
        if hasattr(settings_data, 'nautobot') and settings_data.nautobot:
            nautobot_config = settings_data.nautobot
            settings_to_save.extend([
                ("nautobot_url", nautobot_config.get("url", "")),
                ("nautobot_token", nautobot_config.get("token", "")),
                ("nautobot_verify_tls", str(nautobot_config.get("verifyTls", True))),
                ("nautobot_timeout", str(nautobot_config.get("timeout", 30))),
            ])

        # Add CheckMK configuration settings
        if hasattr(settings_data, 'checkmk') and settings_data.checkmk:
            checkmk_config = settings_data.checkmk
            settings_to_save.extend([
                ("checkmk_url", checkmk_config.get("url", "")),
                ("checkmk_site", checkmk_config.get("site", "")),
                ("checkmk_username", checkmk_config.get("username", "")),
                ("checkmk_password", checkmk_config.get("password", "")),
                ("checkmk_verify_tls", str(checkmk_config.get("verifyTls", True))),
            ])

        # Save all settings to database
        for key, value in settings_to_save:
            # Skip saving masked passwords
            if value == "***":
                continue

            setting = db.query(AppSettings).filter(AppSettings.key == key).first()
            if setting:
                setting.value = value
            else:
                setting = AppSettings(key=key, value=value)
                db.add(setting)

        # Save database configuration to YAML file
        if hasattr(settings_data, 'database') and settings_data.database:
            try:
                from ..core.yaml_config import DatabaseConfig, save_database_config

                # Only save if we have actual values (not masked passwords)
                db_data = settings_data.database
                if db_data.get("password") != "***" and db_data.get("host"):
                    config = DatabaseConfig(
                        host=db_data.get("host", ""),
                        port=db_data.get("port", 5432),
                        database=db_data.get("database", "noc_canvas"),
                        username=db_data.get("username", ""),
                        password=db_data.get("password", ""),
                        ssl=db_data.get("ssl", False)
                    )
                    save_database_config(config)
                    logger.info("Database configuration saved to YAML file")

            except Exception as db_error:
                logger.warning(f"Could not save database config: {db_error}")
                # Don't fail the entire request if database config save fails

        db.commit()
        return {"message": "Settings saved successfully"}

    except Exception as e:
        logger.error(f"Error saving unified settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save settings: {str(e)}"
        )


@router.post("/test-nautobot")
async def test_nautobot_connection(
    test_data: dict,
    current_user: User = Depends(get_current_user),
):
    """Test Nautobot connection with provided settings."""
    try:
        success, message = await nautobot_service.test_connection(
            url=test_data.get("url", ""),
            token=test_data.get("token", ""),
            timeout=test_data.get("timeout", 30),
            verify_ssl=test_data.get("verify_ssl", True),
        )

        return {
            "success": success,
            "message": message
        }
    except Exception as e:
        logger.error(f"Error testing Nautobot connection: {str(e)}")
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}"
        }


@router.post("/test-checkmk")
async def test_checkmk_connection(
    test_data: dict,
    current_user: User = Depends(get_current_user),
):
    """Test CheckMK connection with provided settings."""
    try:
        success, message = await checkmk_service.test_connection(
            url=test_data.get("url", ""),
            site=test_data.get("site", ""),
            username=test_data.get("username", ""),
            password=test_data.get("password", ""),
            verify_ssl=test_data.get("verify_ssl", True),
        )

        return {
            "success": success,
            "message": message
        }
    except Exception as e:
        logger.error(f"Error testing CheckMK connection: {str(e)}")
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}"
        }


@router.post("/test-database")
async def test_database_connection(
    test_data: dict,
    current_user: User = Depends(get_current_user),
):
    """Test database connection with provided settings."""
    try:
        from ..core.yaml_config import DatabaseConfig, get_database_url
        from sqlalchemy import create_engine, text

        # Create DatabaseConfig from test data
        config = DatabaseConfig(
            host=test_data.get("host", ""),
            port=test_data.get("port", 5432),
            database=test_data.get("database", ""),
            username=test_data.get("username", ""),
            password=test_data.get("password", ""),
            ssl=test_data.get("ssl", False)
        )

        # Get database URL and test connection
        database_url = get_database_url(config)
        engine = create_engine(database_url, pool_pre_ping=True)

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        return {
            "success": True,
            "message": "Database connection successful"
        }

    except Exception as e:
        logger.error(f"Error testing database connection: {str(e)}")
        return {
            "success": False,
            "message": f"Database connection failed: {str(e)}"
        }


@router.post("/database/config")
async def save_database_config(
    config_data: dict,
    current_user: User = Depends(get_current_user),
):
    """Save database configuration to YAML file."""
    try:
        from ..core.yaml_config import DatabaseConfig, save_database_config

        config = DatabaseConfig(
            host=config_data.get("host", ""),
            port=config_data.get("port", 5432),
            database=config_data.get("database", ""),
            username=config_data.get("username", ""),
            password=config_data.get("password", ""),
            ssl=config_data.get("ssl", False)
        )

        success = save_database_config(config)
        if success:
            return {"message": "Database configuration saved successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save database configuration"
            )

    except Exception as e:
        logger.error(f"Error saving database config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save database configuration: {str(e)}"
        )


@router.get("/database/status")
async def get_database_status(
    current_user: User = Depends(get_current_user),
):
    """Get current database status and configuration."""
    try:
        from ..core.db_init import check_database_status

        status_info = check_database_status()
        return status_info

    except Exception as e:
        logger.error(f"Error getting database status: {str(e)}")
        return {
            "error": f"Failed to get database status: {str(e)}"
        }


@router.post("/credentials")
async def save_user_credentials(
    credentials_data: CredentialsSettings,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save user credentials."""
    try:
        import json

        key = f"user_credentials_{current_user.username}"
        setting = db.query(AppSettings).filter(AppSettings.key == key).first()

        credentials_json = json.dumps(credentials_data.credentials)

        if setting:
            setting.value = credentials_json
        else:
            setting = AppSettings(key=key, value=credentials_json)
            db.add(setting)

        db.commit()
        return {"message": "Credentials saved successfully"}

    except Exception as e:
        logger.error(f"Error saving credentials: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save credentials: {str(e)}"
        )