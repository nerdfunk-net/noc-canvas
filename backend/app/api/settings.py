"""
Settings API router for managing application configuration.
"""

import logging
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..core.config import settings as app_settings
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
    DeviceCommand,
    DeviceCommandCreate,
    DeviceCommandUpdate,
    DeviceCommandResponse,
)
from ..services.nautobot import nautobot_service
from ..services.checkmk import checkmk_service

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


# =============================================================================
# Helper Functions
# =============================================================================


def get_setting_value(db: Session, key: str, default: str = "") -> str:
    """Get a setting value from database or return default."""
    setting = db.query(AppSettings).filter(AppSettings.key == key).first()
    return setting.value if setting else default


def upsert_setting(
    db: Session, key: str, value: str, description: Optional[str] = None
) -> AppSettings:
    """Create or update a setting in the database."""
    setting = db.query(AppSettings).filter(AppSettings.key == key).first()

    if setting:
        setting.value = value
        if description is not None:
            setting.description = description
    else:
        setting = AppSettings(key=key, value=value, description=description)
        db.add(setting)

    return setting


def build_nautobot_settings(db: Session) -> Dict[str, Any]:
    """Build Nautobot settings dict from database and environment."""
    stored_settings = {s.key: s.value for s in db.query(AppSettings).all()}

    return {
        "enabled": stored_settings.get("nautobot_enabled", "false").lower() == "true",
        "url": stored_settings.get("nautobot_url") or app_settings.nautobot_url or "",
        "token": "***"
        if (stored_settings.get("nautobot_token") or app_settings.nautobot_token)
        else "",
        "verifyTls": stored_settings.get(
            "nautobot_verify_tls", str(app_settings.nautobot_verify_ssl)
        ).lower()
        == "true",
        "timeout": int(
            stored_settings.get("nautobot_timeout", str(app_settings.nautobot_timeout))
        ),
    }


def build_checkmk_settings(db: Session) -> Dict[str, Any]:
    """Build CheckMK settings dict from database and environment."""
    stored_settings = {s.key: s.value for s in db.query(AppSettings).all()}

    return {
        "enabled": stored_settings.get("checkmk_enabled", "false").lower() == "true",
        "url": stored_settings.get("checkmk_url") or app_settings.checkmk_url or "",
        "site": stored_settings.get("checkmk_site")
        or app_settings.checkmk_site
        or "cmk",
        "username": stored_settings.get("checkmk_username")
        or app_settings.checkmk_username
        or "",
        "password": "***"
        if (stored_settings.get("checkmk_password") or app_settings.checkmk_password)
        else "",
        "verifyTls": stored_settings.get(
            "checkmk_verify_tls", str(app_settings.checkmk_verify_ssl)
        ).lower()
        == "true",
    }


def build_canvas_settings(db: Session) -> Dict[str, Any]:
    """Build canvas settings dict from database."""
    return {
        "autoSaveInterval": int(
            get_setting_value(db, "canvas_autosave_interval", "60")
        ),
        "gridEnabled": get_setting_value(db, "canvas_grid_enabled", "true").lower()
        == "true",
    }


def build_database_settings() -> Dict[str, Any]:
    """Build database settings dict from YAML config."""
    try:
        from ..core.yaml_config import load_database_config

        db_config = load_database_config()
        if db_config:
            return {
                "host": db_config.host,
                "port": db_config.port,
                "database": db_config.database,
                "username": db_config.username,
                "password": "***" if db_config.password else "",
                "ssl": db_config.ssl,
            }
    except Exception as e:
        logger.warning(f"Could not load database config: {e}")

    # Default empty configuration
    return {
        "host": "",
        "port": 5432,
        "database": "noc_canvas",
        "username": "",
        "password": "",
        "ssl": False,
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
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
    unified = UnifiedSettings()
    unified.nautobot = build_nautobot_settings(db)
    unified.checkmk = build_checkmk_settings(db)
    unified.canvas = build_canvas_settings(db)
    unified.database = build_database_settings()
    return unified


@router.get("/credentials")
async def get_user_credentials(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user credentials."""
    try:
        key = f"user_credentials_{current_user.username}"
        value = get_setting_value(db, key)
        if value:
            credentials = json.loads(value)
            return {"credentials": credentials}
        return {"credentials": []}
    except Exception as e:
        logger.error(f"Error getting credentials: {str(e)}")
        return {"credentials": []}


# Device Commands endpoints (must be before generic /{key} route)


@router.get("/commands", response_model=List[DeviceCommandResponse])
async def get_device_commands(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all device commands."""
    commands = db.query(DeviceCommand).all()
    return commands


@router.post("/commands", response_model=DeviceCommandResponse)
async def create_device_command(
    command_data: DeviceCommandCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new device command."""
    try:
        # Check for existing command with same command + platform combination
        existing_command = (
            db.query(DeviceCommand)
            .filter(
                DeviceCommand.command == command_data.command,
                DeviceCommand.platform == command_data.platform,
            )
            .first()
        )

        if existing_command:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A command '{command_data.command}' already exists for platform '{command_data.platform.value}'. Duplicates are not allowed.",
            )

        command = DeviceCommand(
            command=command_data.command,
            display=command_data.display,
            template=command_data.template,
            platform=command_data.platform,
            parser=command_data.parser,
        )
        db.add(command)
        db.commit()
        db.refresh(command)
        return command
    except HTTPException:
        # Re-raise HTTP exceptions (like duplicate validation)
        raise
    except Exception as e:
        logger.error(f"Error creating device command: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create device command: {str(e)}",
        )


@router.get("/commands/{command_id}", response_model=DeviceCommandResponse)
async def get_device_command(
    command_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get specific device command by ID."""
    command = db.query(DeviceCommand).filter(DeviceCommand.id == command_id).first()
    if not command:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device command with ID {command_id} not found",
        )
    return command


@router.put("/commands/{command_id}", response_model=DeviceCommandResponse)
async def update_device_command(
    command_id: int,
    command_update: DeviceCommandUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a device command."""
    command = db.query(DeviceCommand).filter(DeviceCommand.id == command_id).first()
    if not command:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device command with ID {command_id} not found",
        )

    try:
        # If updating command or platform, check for duplicates
        new_command = (
            command_update.command
            if command_update.command is not None
            else command.command
        )
        new_platform = (
            command_update.platform
            if command_update.platform is not None
            else command.platform
        )

        # Check for existing command with same command + platform combination (excluding current record)
        existing_command = (
            db.query(DeviceCommand)
            .filter(
                DeviceCommand.command == new_command,
                DeviceCommand.platform == new_platform,
                DeviceCommand.id != command_id,  # Exclude current record
            )
            .first()
        )

        if existing_command:
            platform_value = (
                new_platform.value
                if hasattr(new_platform, "value")
                else str(new_platform)
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A command '{new_command}' already exists for platform '{platform_value}'. Duplicates are not allowed.",
            )

        if command_update.command is not None:
            command.command = command_update.command
        if command_update.display is not None:
            command.display = command_update.display
        if command_update.template is not None:
            command.template = command_update.template
        if command_update.platform is not None:
            command.platform = command_update.platform
        if command_update.parser is not None:
            command.parser = command_update.parser

        db.commit()
        db.refresh(command)
        return command
    except HTTPException:
        # Re-raise HTTP exceptions (like duplicate validation)
        raise
    except Exception as e:
        logger.error(f"Error updating device command: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update device command: {str(e)}",
        )


@router.delete("/commands/{command_id}")
async def delete_device_command(
    command_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a device command."""
    command = db.query(DeviceCommand).filter(DeviceCommand.id == command_id).first()
    if not command:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device command with ID {command_id} not found",
        )

    try:
        db.delete(command)
        db.commit()
        return {"message": f"Device command with ID {command_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting device command: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete device command: {str(e)}",
        )


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
    setting = upsert_setting(
        db, setting_update.key, setting_update.value, setting_update.description
    )
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
    return NautobotSettings(
        url=app_settings.nautobot_url,
        token="***" if app_settings.nautobot_token else None,
        timeout=app_settings.nautobot_timeout,
        verify_ssl=app_settings.nautobot_verify_ssl,
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
    return CheckMKSettings(
        url=app_settings.checkmk_url,
        site=app_settings.checkmk_site,
        username=app_settings.checkmk_username,
        password="***" if app_settings.checkmk_password else None,
        timeout=app_settings.checkmk_timeout,
        verify_ssl=app_settings.checkmk_verify_ssl,
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
    return CacheSettings(
        enabled=True,
        ttl_seconds=app_settings.cache_ttl_seconds,
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
        # Collect all settings to save
        settings_to_save = [
            ("nautobot_enabled", str(settings_data.nautobot.get("enabled", False))),
            ("checkmk_enabled", str(settings_data.checkmk.get("enabled", False))),
            (
                "canvas_autosave_interval",
                str(settings_data.canvas.get("autoSaveInterval", 60)),
            ),
            ("canvas_grid_enabled", str(settings_data.canvas.get("gridEnabled", True))),
        ]

        # Add Nautobot settings
        if hasattr(settings_data, "nautobot") and settings_data.nautobot:
            nautobot_config = settings_data.nautobot
            settings_to_save.extend(
                [
                    ("nautobot_url", nautobot_config.get("url", "")),
                    ("nautobot_token", nautobot_config.get("token", "")),
                    (
                        "nautobot_verify_tls",
                        str(nautobot_config.get("verifyTls", True)),
                    ),
                    ("nautobot_timeout", str(nautobot_config.get("timeout", 30))),
                ]
            )

        # Add CheckMK settings
        if hasattr(settings_data, "checkmk") and settings_data.checkmk:
            checkmk_config = settings_data.checkmk
            settings_to_save.extend(
                [
                    ("checkmk_url", checkmk_config.get("url", "")),
                    ("checkmk_site", checkmk_config.get("site", "")),
                    ("checkmk_username", checkmk_config.get("username", "")),
                    ("checkmk_password", checkmk_config.get("password", "")),
                    ("checkmk_verify_tls", str(checkmk_config.get("verifyTls", True))),
                ]
            )

        # Save all settings using helper function
        for key, value in settings_to_save:
            if value != "***":  # Skip masked passwords
                upsert_setting(db, key, value)

        # Save database configuration to YAML
        if hasattr(settings_data, "database") and settings_data.database:
            try:
                from ..core.yaml_config import DatabaseConfig, save_database_config

                db_data = settings_data.database
                if db_data.get("password") != "***" and db_data.get("host"):
                    config = DatabaseConfig(
                        host=db_data.get("host", ""),
                        port=db_data.get("port", 5432),
                        database=db_data.get("database", "noc_canvas"),
                        username=db_data.get("username", ""),
                        password=db_data.get("password", ""),
                        ssl=db_data.get("ssl", False),
                    )
                    save_database_config(config)
                    logger.info("Database configuration saved to YAML file")
            except Exception as db_error:
                logger.warning(f"Could not save database config: {db_error}")

        db.commit()
        return {"message": "Settings saved successfully"}
    except Exception as e:
        logger.error(f"Error saving unified settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save settings: {str(e)}",
        )


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
            ssl=test_data.get("ssl", False),
        )

        # Get database URL and test connection
        database_url = get_database_url(config)
        engine = create_engine(database_url, pool_pre_ping=True)

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        return {"success": True, "message": "Database connection successful"}

    except Exception as e:
        logger.error(f"Error testing database connection: {str(e)}")
        return {"success": False, "message": f"Database connection failed: {str(e)}"}


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
            ssl=config_data.get("ssl", False),
        )

        success = save_database_config(config)
        if success:
            return {"message": "Database configuration saved successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save database configuration",
            )

    except Exception as e:
        logger.error(f"Error saving database config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save database configuration: {str(e)}",
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
        return {"error": f"Failed to get database status: {str(e)}"}


@router.post("/credentials")
async def save_user_credentials(
    credentials_data: CredentialsSettings,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save user credentials."""
    try:
        key = f"user_credentials_{current_user.username}"
        credentials_json = json.dumps(credentials_data.credentials)
        upsert_setting(db, key, credentials_json)
        db.commit()
        return {"message": "Credentials saved successfully"}
    except Exception as e:
        logger.error(f"Error saving credentials: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save credentials: {str(e)}",
        )


@router.get("/jobs/status")
async def get_job_status(
    current_user: User = Depends(get_current_user),
):
    """Get Celery job status and worker information."""
    try:
        from ..services.background_jobs import celery_app, CELERY_AVAILABLE

        if not CELERY_AVAILABLE or not celery_app:
            return {
                "workerActive": False,
                "queueSize": 0,
                "activeJobs": 0,
                "workers": [],
                "recentJobs": [],
                "error": "Celery not available",
            }

        # Get worker stats with error handling
        inspect = celery_app.control.inspect()

        # Initialize default values
        active_workers = {}
        stats = {}
        worker_info = []
        total_active_jobs = 0

        try:
            # Try to get active workers
            active_workers = inspect.active() or {}
        except Exception as e:
            logger.warning(f"Could not get active workers: {e}")

        try:
            # Try to get worker stats
            stats = inspect.stats() or {}
        except Exception as e:
            logger.warning(f"Could not get worker stats: {e}")

        # Check if any workers responded to ping
        try:
            ping_response = inspect.ping() or {}
            available_workers = list(ping_response.keys()) if ping_response else []
        except Exception as e:
            logger.warning(f"Could not ping workers: {e}")
            available_workers = []

        # Process worker information
        for worker_name, worker_stats in stats.items():
            active_jobs_for_worker = len(active_workers.get(worker_name, []))
            total_active_jobs += active_jobs_for_worker

            worker_info.append(
                {
                    "name": worker_name,
                    "status": "active" if worker_name in active_workers else "inactive",
                    "loadavg": worker_stats.get("rusage", {}).get("loadavg"),
                    "activeJobs": active_jobs_for_worker,
                }
            )

        # If we have available workers from ping but no stats, add them
        for worker_name in available_workers:
            if worker_name not in [w["name"] for w in worker_info]:
                active_jobs_for_worker = len(active_workers.get(worker_name, []))
                total_active_jobs += active_jobs_for_worker
                worker_info.append(
                    {
                        "name": worker_name,
                        "status": "active",
                        "loadavg": None,
                        "activeJobs": active_jobs_for_worker,
                    }
                )

        # Get queue size (approximate)
        queue_size = 0
        try:
            reserved = inspect.reserved() or {}
            queue_size = sum(len(jobs) for jobs in reserved.values())
        except Exception as e:
            logger.warning(f"Could not get queue size: {e}")

        # Get recent job results
        recent_jobs = []
        try:
            for worker_name in active_workers.keys():
                for job in active_workers[worker_name]:
                    recent_jobs.append(
                        {
                            "id": job.get("id", "unknown"),
                            "name": job.get("name", "Unknown Task"),
                            "state": "RUNNING",
                            "timestamp": job.get("time_start", ""),
                            "worker": worker_name,
                        }
                    )
        except Exception as e:
            logger.warning(f"Could not get recent jobs: {e}")

        return {
            "workerActive": len(worker_info) > 0,
            "queueSize": queue_size,
            "activeJobs": total_active_jobs,
            "workers": worker_info,
            "recentJobs": recent_jobs[-10:] if recent_jobs else [],  # Last 10 jobs
            "availableWorkers": available_workers,
        }

    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        return {
            "workerActive": False,
            "queueSize": 0,
            "activeJobs": 0,
            "workers": [],
            "recentJobs": [],
            "error": f"Connection error: {str(e)}",
        }


@router.post("/jobs/test")
async def submit_test_job(
    current_user: User = Depends(get_current_user),
):
    """Submit a test job to verify Celery worker functionality."""
    try:
        from ..services.background_jobs import test_background_task, CELERY_AVAILABLE

        if not CELERY_AVAILABLE:
            raise HTTPException(status_code=503, detail="Celery is not available")

        # Submit test job with a 10-second delay to demonstrate functionality
        result = test_background_task.delay("Test job from settings", 10)

        return {
            "success": True,
            "jobId": result.id,
            "message": "Test job submitted successfully",
        }

    except Exception as e:
        logger.error(f"Error submitting test job: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to submit test job: {str(e)}"
        )
