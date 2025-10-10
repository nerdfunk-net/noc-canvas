"""
Settings API router for managing application configuration.
"""

import logging
import json
import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
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
    DeviceTemplate,
    DeviceTemplateCreate,
    DeviceTemplateUpdate,
    DeviceTemplateResponse,
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
        "url": stored_settings.get("nautobot_url") or app_settings.nautobot_url or "",
        "token": stored_settings.get("nautobot_token") or app_settings.nautobot_token or "",
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
        "password": stored_settings.get("checkmk_password")
        or app_settings.checkmk_password
        or "",
        "verifyTls": stored_settings.get(
            "checkmk_verify_tls", str(app_settings.checkmk_verify_ssl)
        ).lower()
        == "true",
    }


def build_netmiko_settings(db: Session) -> Dict[str, Any]:
    """Build Netmiko settings dict from database."""
    stored_settings = {s.key: s.value for s in db.query(AppSettings).all()}

    return {
        "readTimeout": int(stored_settings.get("netmiko_read_timeout", "10")),
        "lastRead": int(stored_settings.get("netmiko_last_read")) if stored_settings.get("netmiko_last_read") else None,
        "connTimeout": int(stored_settings.get("netmiko_conn_timeout", "10")),
        "authTimeout": int(stored_settings.get("netmiko_auth_timeout")) if stored_settings.get("netmiko_auth_timeout") else None,
        "bannerTimeout": int(stored_settings.get("netmiko_banner_timeout", "15")),
        "blockingTimeout": int(stored_settings.get("netmiko_blocking_timeout", "20")),
        "timeout": int(stored_settings.get("netmiko_timeout", "100")),
        "sessionTimeout": int(stored_settings.get("netmiko_session_timeout", "60")),
    }


def build_canvas_settings(db: Session) -> Dict[str, Any]:
    """Build canvas settings dict from database."""
    return {
        "autoSaveEnabled": get_setting_value(db, "canvas_autosave_enabled", "false").lower()
        == "true",
        "autoSaveInterval": int(
            get_setting_value(db, "canvas_autosave_interval", "60")
        ),
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
    unified.netmiko = build_netmiko_settings(db)
    unified.canvas = build_canvas_settings(db)
    unified.database = build_database_settings()
    return unified
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


# Device Templates endpoints (must be before generic /{key} route)


@router.get("/device-templates", response_model=List[DeviceTemplateResponse])
async def get_device_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all device templates."""
    templates = db.query(DeviceTemplate).all()
    # Parse JSON strings to lists
    result = []
    for template in templates:
        result.append(
            DeviceTemplateResponse(
                id=template.id,
                name=template.name,
                filename=template.filename,
                platforms=json.loads(template.platforms) if template.platforms else [],
                device_types=json.loads(template.device_types) if template.device_types else [],
            )
        )
    return result


@router.post("/device-templates", response_model=DeviceTemplateResponse)
async def create_device_template(
    template_data: DeviceTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new device template."""
    try:
        # Check for existing template with same name
        existing_template = (
            db.query(DeviceTemplate)
            .filter(DeviceTemplate.name == template_data.name)
            .first()
        )

        if existing_template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A device template with name '{template_data.name}' already exists.",
            )

        template = DeviceTemplate(
            name=template_data.name,
            filename=template_data.filename,
            platforms=json.dumps(template_data.platforms),
            device_types=json.dumps(template_data.device_types),
        )
        db.add(template)
        db.commit()
        db.refresh(template)

        return DeviceTemplateResponse(
            id=template.id,
            name=template.name,
            filename=template.filename,
            platforms=template_data.platforms,
            device_types=template_data.device_types,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating device template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create device template: {str(e)}",
        )


@router.get("/device-templates/{template_id}", response_model=DeviceTemplateResponse)
async def get_device_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get specific device template by ID."""
    template = db.query(DeviceTemplate).filter(DeviceTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device template with ID {template_id} not found",
        )

    return DeviceTemplateResponse(
        id=template.id,
        name=template.name,
        filename=template.filename,
        platforms=json.loads(template.platforms) if template.platforms else [],
        device_types=json.loads(template.device_types) if template.device_types else [],
    )


@router.put("/device-templates/{template_id}", response_model=DeviceTemplateResponse)
async def update_device_template(
    template_id: int,
    template_update: DeviceTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a device template."""
    template = db.query(DeviceTemplate).filter(DeviceTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device template with ID {template_id} not found",
        )

    try:
        # Check for name uniqueness if name is being updated
        if template_update.name is not None and template_update.name != template.name:
            existing_template = (
                db.query(DeviceTemplate)
                .filter(
                    DeviceTemplate.name == template_update.name,
                    DeviceTemplate.id != template_id,
                )
                .first()
            )

            if existing_template:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A device template with name '{template_update.name}' already exists.",
                )

        if template_update.name is not None:
            template.name = template_update.name
        if template_update.filename is not None:
            template.filename = template_update.filename
        if template_update.platforms is not None:
            template.platforms = json.dumps(template_update.platforms)
        if template_update.device_types is not None:
            template.device_types = json.dumps(template_update.device_types)

        db.commit()
        db.refresh(template)

        return DeviceTemplateResponse(
            id=template.id,
            name=template.name,
            filename=template.filename,
            platforms=json.loads(template.platforms) if template.platforms else [],
            device_types=json.loads(template.device_types) if template.device_types else [],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating device template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update device template: {str(e)}",
        )


@router.delete("/device-templates/{template_id}")
async def delete_device_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a device template."""
    template = db.query(DeviceTemplate).filter(DeviceTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device template with ID {template_id} not found",
        )

    try:
        # Check if this filename is used by other templates before deleting the file
        other_templates_using_file = (
            db.query(DeviceTemplate)
            .filter(
                DeviceTemplate.filename == template.filename,
                DeviceTemplate.id != template_id
            )
            .count()
        )

        # Only delete the file if no other templates are using it
        if other_templates_using_file == 0:
            icons_dir = Path(__file__).parent.parent.parent.parent / "frontend" / "icons"
            file_path = icons_dir / template.filename
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted icon file: {template.filename} (not used by other templates)")
        else:
            logger.info(f"Keeping icon file: {template.filename} (used by {other_templates_using_file} other template(s))")

        db.delete(template)
        db.commit()
        return {"message": f"Device template with ID {template_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting device template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete device template: {str(e)}",
        )


@router.post("/device-templates/upload")
async def upload_device_template_icon(
    file: UploadFile = File(...),
    override: bool = Query(False),
    current_user: User = Depends(get_current_user),
):
    """Upload an SVG icon for device templates."""
    try:
        # Validate file extension
        if not file.filename.endswith('.svg'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only SVG files are supported",
            )

        # Create icons directory if it doesn't exist
        icons_dir = Path(__file__).parent.parent.parent.parent / "frontend" / "icons"
        icons_dir.mkdir(parents=True, exist_ok=True)

        # Generate safe filename
        filename = file.filename.replace(" ", "_")
        file_path = icons_dir / filename

        # Check if file already exists and override not confirmed
        if file_path.exists() and not override:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{filename}' already exists",
            )

        # Save file (will overwrite if exists and override=True)
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Uploaded icon file: {filename} (override={override})")

        return {
            "message": "File uploaded successfully",
            "filename": filename,
            "path": str(file_path.relative_to(icons_dir.parent)),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading icon file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}",
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


@router.post("/test-nautobot", response_model=SettingsTest)
async def test_nautobot_settings_legacy(
    test_request: NautobotTestRequest,
    current_user: User = Depends(get_current_user),
):
    """Test Nautobot connection settings (legacy endpoint for backward compatibility)."""
    return await test_nautobot_settings(test_request, current_user)


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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current cache settings."""
    # Try to get settings from database
    cache_settings = db.query(AppSettings).filter(
        AppSettings.key == "cache_settings"
    ).first()

    if cache_settings and cache_settings.value:
        import json
        settings_data = json.loads(cache_settings.value)
        return CacheSettings(
            enabled=True,
            ttl_seconds=settings_data.get("defaultTtlMinutes", 60) * 60,
            prefetch_on_startup=True,
            refresh_interval_minutes=settings_data.get("autoRefreshIntervalMinutes", 30),
            prefetch_items={
                "devices": False,
                "locations": False,
                "statistics": True,
            },
        )

    # Default settings
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


@router.post("/cache/settings")
async def save_cache_settings(
    settings: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save cache settings to database."""
    import json

    # Get or create cache settings entry
    cache_settings = db.query(AppSettings).filter(
        AppSettings.key == "cache_settings"
    ).first()

    if cache_settings:
        cache_settings.value = json.dumps(settings)
        cache_settings.updated_at = func.now()
    else:
        cache_settings = AppSettings(
            key="cache_settings",
            value=json.dumps(settings),
            description="Cache configuration settings"
        )
        db.add(cache_settings)

    db.commit()
    logger.info(f"💾 Cache settings saved: {settings}")

    return {"message": "Cache settings saved successfully", "settings": settings}


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
        logger.info(f"💾 Saving unified settings: {settings_data}")

        # Collect all settings to save
        settings_to_save = [
            ("checkmk_enabled", str(settings_data.checkmk.get("enabled", False))),
            (
                "canvas_autosave_enabled",
                str(settings_data.canvas.get("autoSaveEnabled", False)),
            ),
            (
                "canvas_autosave_interval",
                str(settings_data.canvas.get("autoSaveInterval", 60)),
            ),
        ]

        # Add Nautobot settings
        if hasattr(settings_data, "nautobot") and settings_data.nautobot:
            logger.info(f"💾 Nautobot settings to save: {settings_data.nautobot}")
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

        # Add Netmiko settings
        if hasattr(settings_data, "netmiko") and settings_data.netmiko:
            netmiko_config = settings_data.netmiko
            settings_to_save.extend(
                [
                    ("netmiko_read_timeout", str(netmiko_config.get("readTimeout", 10))),
                    ("netmiko_last_read", str(netmiko_config.get("lastRead")) if netmiko_config.get("lastRead") is not None else ""),
                    ("netmiko_conn_timeout", str(netmiko_config.get("connTimeout", 10))),
                    ("netmiko_auth_timeout", str(netmiko_config.get("authTimeout")) if netmiko_config.get("authTimeout") is not None else ""),
                    ("netmiko_banner_timeout", str(netmiko_config.get("bannerTimeout", 15))),
                    ("netmiko_blocking_timeout", str(netmiko_config.get("blockingTimeout", 20))),
                    ("netmiko_timeout", str(netmiko_config.get("timeout", 100))),
                    ("netmiko_session_timeout", str(netmiko_config.get("sessionTimeout", 60))),
                ]
            )

        # Save all settings using helper function
        logger.info(f"💾 Total settings to save: {len(settings_to_save)}")
        for key, value in settings_to_save:
            if value != "***":  # Skip masked passwords
                logger.info(f"💾 Saving setting: {key} = {value[:50] if len(str(value)) > 50 else value}")
                upsert_setting(db, key, value)
            else:
                logger.info(f"💾 Skipping masked value for: {key}")

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
        logger.info("✅ Settings saved successfully and committed to database")
        return {"message": "Settings saved successfully"}
    except Exception as e:
        logger.error(f"❌ Error saving unified settings: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
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

        # Get recent job results - both running and completed
        recent_jobs = []
        task_ids_seen = set()
        
        try:
            # First, add currently running jobs
            for worker_name in active_workers.keys():
                for job in active_workers[worker_name]:
                    task_id = job.get('id', 'unknown')
                    if task_id not in task_ids_seen:
                        recent_jobs.append(
                            {
                                "id": task_id,
                                "name": job.get("name", "Unknown Task"),
                                "state": "RUNNING",
                                "timestamp": job.get("time_start", ""),
                                "worker": worker_name,
                            }
                        )
                        task_ids_seen.add(task_id)
        except Exception as e:
            logger.warning(f"Could not get running jobs: {e}")

        # Now try to get completed/failed jobs from result backend
        try:
            from celery.result import AsyncResult
            # Get recent task IDs from registered tasks
            # We'll check for results of recently executed tasks
            
            # Try to get reserved tasks which includes queued jobs
            try:
                reserved = inspect.reserved() or {}
                for worker_name, tasks in reserved.items():
                    for task in tasks:
                        task_id = task.get('id', 'unknown')
                        if task_id not in task_ids_seen:
                            recent_jobs.append({
                                "id": task_id,
                                "name": task.get("name", "Unknown Task"),
                                "state": "PENDING",
                                "timestamp": "",
                                "worker": worker_name,
                            })
                            task_ids_seen.add(task_id)
            except Exception as e:
                logger.warning(f"Could not get reserved tasks: {e}")
            
            # Try to query the result backend directly for recent results
            # This is implementation-specific to Redis backend
            try:
                from celery import current_app
                import redis
                
                # Get Redis connection from Celery config
                redis_url = current_app.conf.result_backend
                if redis_url and redis_url.startswith('redis://'):
                    r = redis.from_url(redis_url)
                    
                    # Scan for celery task result keys
                    # Results are stored with key pattern: celery-task-meta-{task_id}
                    cursor = 0
                    max_jobs = 20
                    jobs_found = 0
                    
                    while jobs_found < max_jobs:
                        cursor, keys = r.scan(cursor, match='celery-task-meta-*', count=100)
                        
                        for key in keys:
                            if jobs_found >= max_jobs:
                                break
                                
                            try:
                                # Extract task ID from key
                                task_id = key.decode('utf-8').replace('celery-task-meta-', '')

                                if task_id not in task_ids_seen:
                                    # Get the task result
                                    result = AsyncResult(task_id, app=celery_app)

                                    # Only add if we can get status
                                    if result.state:
                                        # Try to get task name from result backend metadata
                                        task_name = "Unknown Task"
                                        timestamp = ""
                                        try:
                                            # Get the full result metadata from Redis
                                            result_meta = r.get(key)
                                            if result_meta:
                                                import json
                                                meta_data = json.loads(result_meta)

                                                # With result_extended=True, Celery stores task name in 'name' field
                                                if 'name' in meta_data:
                                                    task_name = meta_data['name']
                                                elif 'task' in meta_data:
                                                    task_name = meta_data['task']

                                                # Get timestamp
                                                if 'date_done' in meta_data:
                                                    timestamp = meta_data['date_done']

                                                # Format task name for better readability
                                                if task_name and task_name != "Unknown Task":
                                                    # Convert task paths to readable names
                                                    # e.g., "app.tasks.topology_tasks.discover_single_device_task" -> "Discover Single Device"
                                                    # e.g., "app.tasks.test_tasks.test_background_task" -> "Test Background Task"
                                                    if '.' in task_name:
                                                        task_name = task_name.split('.')[-1]  # Get last part
                                                    # Convert snake_case to Title Case
                                                    task_name = task_name.replace('_task', '').replace('_', ' ').title()
                                        except Exception as name_error:
                                            logger.debug(f"Could not extract task name from metadata: {name_error}")

                                        job_data = {
                                            "id": task_id,
                                            "name": task_name,
                                            "state": result.state,
                                            "timestamp": timestamp,
                                        }

                                        # Add result details if available
                                        if result.state == 'SUCCESS':
                                            job_data["result"] = str(result.result)[:200]  # Truncate long results
                                        elif result.state == 'FAILURE':
                                            job_data["traceback"] = str(result.traceback)[:500] if result.traceback else "Unknown error"

                                        recent_jobs.append(job_data)
                                        task_ids_seen.add(task_id)
                                        jobs_found += 1
                            except Exception as e:
                                logger.debug(f"Error processing task result {key}: {e}")
                                continue
                        
                        if cursor == 0:  # Scan complete
                            break
                            
            except Exception as e:
                logger.warning(f"Could not query Redis result backend: {e}")
                
        except Exception as e:
            logger.warning(f"Could not get completed jobs: {e}")

        # Sort by state priority: RUNNING > PENDING > FAILURE > SUCCESS
        state_priority = {"RUNNING": 0, "PENDING": 1, "STARTED": 2, "FAILURE": 3, "SUCCESS": 4}
        recent_jobs.sort(key=lambda x: state_priority.get(x.get("state", ""), 99))

        return {
            "workerActive": len(worker_info) > 0,
            "queueSize": queue_size,
            "activeJobs": total_active_jobs,
            "workers": worker_info,
            "recentJobs": recent_jobs[:20],  # Return top 20 jobs
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
        from ..services.background_jobs import celery_app, CELERY_AVAILABLE

        if not CELERY_AVAILABLE:
            raise HTTPException(status_code=503, detail="Celery is not available")

        # Submit test job with a 10-second delay to demonstrate functionality
        result = celery_app.send_task(
            "app.tasks.test_tasks.test_background_task",
            kwargs={"duration": 10}
        )

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


@router.post("/jobs/clear")
async def clear_job_logs(
    current_user: User = Depends(get_current_user),
):
    """Clear all Celery job result logs from Redis backend."""
    try:
        from ..services.background_jobs import celery_app, CELERY_AVAILABLE
        
        if not CELERY_AVAILABLE or not celery_app:
            raise HTTPException(
                status_code=503, 
                detail="Celery is not available"
            )
        
        # Clear job results from Redis backend
        try:
            from celery import current_app
            import redis
            
            # Get Redis connection from Celery config
            redis_url = current_app.conf.result_backend
            if not redis_url or not redis_url.startswith('redis://'):
                raise HTTPException(
                    status_code=500,
                    detail="Redis result backend not configured"
                )
            
            r = redis.from_url(redis_url)
            
            # Scan for all celery task result keys
            cursor = 0
            deleted_count = 0
            
            while True:
                cursor, keys = r.scan(cursor, match='celery-task-meta-*', count=100)
                
                if keys:
                    # Delete all found keys
                    deleted_count += r.delete(*keys)
                
                # Scan complete
                if cursor == 0:
                    break
            
            logger.info(f"Cleared {deleted_count} job result(s) from Redis")
            
            return {
                "success": True,
                "message": f"Successfully cleared {deleted_count} job log(s)",
                "deleted_count": deleted_count,
            }
            
        except redis.RedisError as e:
            logger.error(f"Redis error while clearing jobs: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to clear jobs from Redis: {str(e)}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing job logs: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to clear job logs: {str(e)}"
        )
