"""
Updated Settings API router using local databases for credentials and settings.
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..core.security import verify_token
from ..models.user import User
from ..models.credential import (
    UserCredential, 
    CredentialCreate, 
    CredentialUpdate,
    CredentialResponse,
    CredentialWithPassword,
    CredentialsListWithPasswords,
    get_credentials_session,
    encrypt_password,
    decrypt_password
)
from ..models.local_settings import (
    ApplicationSetting,
    get_settings_session,
    store_setting,
    get_setting,
    get_user_settings
)
from ..models.settings import (
    NautobotSettings,
    CheckMKSettings,
    NautobotTestRequest,
    CheckMKTestRequest,
    UnifiedSettings,
    PasswordChangeRequest,
)
from ..services.nautobot import nautobot_service
from ..services.checkmk import checkmk_service
from ..core.database import get_db
from sqlalchemy.orm import Session
from passlib.context import CryptContext

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_current_user_from_db(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user from main database."""
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


# Credentials endpoints using local database

@router.get("/credentials", response_model=CredentialsListWithPasswords)
async def get_user_credentials(
    current_user: User = Depends(get_current_user_from_db)
):
    """Get user credentials from local database."""
    try:
        credentials_session = get_credentials_session()
        credentials = credentials_session.query(UserCredential).filter(
            UserCredential.owner == current_user.username
        ).all()
        
        result = []
        for cred in credentials:
            try:
                # Decrypt password
                decrypted_password = decrypt_password(cred.encrypted_password)
                result.append({
                    "id": cred.id,
                    "owner": cred.owner,
                    "name": cred.name,
                    "username": cred.username,
                    "password": decrypted_password,
                    "created_at": cred.created_at.isoformat() if cred.created_at else None,
                    "updated_at": cred.updated_at.isoformat() if cred.updated_at else None
                })
            except Exception as decrypt_error:
                logger.error(f"Failed to decrypt password for credential {cred.id}: {str(decrypt_error)}")
                # Skip credentials that can't be decrypted
                continue
        
        credentials_session.close()
        return {"credentials": result}
        
    except Exception as e:
        logger.error(f"Error getting credentials: {str(e)}")
        return {"credentials": []}


@router.post("/credentials")
async def save_user_credentials(
    credentials_data: dict,
    current_user: User = Depends(get_current_user_from_db)
):
    """Save user credentials to local database."""
    try:
        credentials_session = get_credentials_session()
        
        # Clear existing credentials for this user
        credentials_session.query(UserCredential).filter(
            UserCredential.owner == current_user.username
        ).delete()
        
        # Add new credentials
        for cred_data in credentials_data.get("credentials", []):
            if not all(k in cred_data for k in ("name", "username", "password")):
                continue
                
            # Encrypt password
            encrypted_password = encrypt_password(cred_data["password"])
            
            credential = UserCredential(
                owner=current_user.username,
                name=cred_data["name"],
                username=cred_data["username"],
                encrypted_password=encrypted_password
            )
            credentials_session.add(credential)
        
        credentials_session.commit()
        credentials_session.close()
        
        return {"message": "Credentials saved successfully"}
        
    except Exception as e:
        logger.error(f"Error saving credentials: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save credentials: {str(e)}"
        )


@router.post("/credentials/add")
async def add_user_credential(
    credential_data: CredentialCreate,
    current_user: User = Depends(get_current_user_from_db)
):
    """Add a single user credential."""
    try:
        credentials_session = get_credentials_session()
        
        # Encrypt password
        encrypted_password = encrypt_password(credential_data.password)
        
        credential = UserCredential(
            owner=current_user.username,
            name=credential_data.name,
            username=credential_data.username,
            encrypted_password=encrypted_password
        )
        
        credentials_session.add(credential)
        credentials_session.commit()
        
        result = {
            "id": credential.id,
            "owner": credential.owner,
            "name": credential.name,
            "username": credential.username,
            "password": credential_data.password,  # Return unencrypted for frontend
            "created_at": credential.created_at.isoformat() if credential.created_at else None,
            "updated_at": credential.updated_at.isoformat() if credential.updated_at else None
        }
        
        credentials_session.close()
        return result
        
    except Exception as e:
        logger.error(f"Error adding credential: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add credential: {str(e)}"
        )


@router.delete("/credentials/{credential_id}")
async def delete_user_credential(
    credential_id: int,
    current_user: User = Depends(get_current_user_from_db)
):
    """Delete a user credential."""
    try:
        credentials_session = get_credentials_session()
        
        credential = credentials_session.query(UserCredential).filter(
            UserCredential.id == credential_id,
            UserCredential.owner == current_user.username
        ).first()
        
        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found"
            )
        
        credentials_session.delete(credential)
        credentials_session.commit()
        credentials_session.close()
        
        return {"message": "Credential deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting credential: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete credential: {str(e)}"
        )


# Settings endpoints using local database

@router.get("/unified")
async def get_unified_settings(
    current_user: User = Depends(get_current_user_from_db)
):
    """Get all user settings from local database."""
    try:
        settings = get_user_settings(current_user.username)
        logger.info(f"Retrieved settings for user {current_user.username}: {settings}")
        
        # Helper function to convert string values to appropriate types
        def convert_value(value, default_value):
            if value is None or value == "":
                return default_value
            if isinstance(default_value, bool):
                return value.lower() == "true" if isinstance(value, str) else bool(value)
            if isinstance(default_value, int):
                return int(value) if str(value).isdigit() else default_value
            return value
        
        # Structure the response to match expected format
        nautobot_settings = settings.get("nautobot", {})
        checkmk_settings = settings.get("checkmk", {})
        canvas_settings = settings.get("canvas", {})
        
        unified = {
            "nautobot": {
                "enabled": convert_value(nautobot_settings.get("enabled"), False),
                "url": nautobot_settings.get("url", ""),
                "token": nautobot_settings.get("token", ""),
                "verifyTls": convert_value(nautobot_settings.get("verifyTls"), True),
                "timeout": convert_value(nautobot_settings.get("timeout"), 30)
            },
            "checkmk": {
                "enabled": convert_value(checkmk_settings.get("enabled"), False),
                "url": checkmk_settings.get("url", ""),
                "site": checkmk_settings.get("site", "cmk"),
                "username": checkmk_settings.get("username", ""),
                "password": checkmk_settings.get("password", ""),
                "verifyTls": convert_value(checkmk_settings.get("verifyTls"), True)
            },
            "canvas": {
                "autoSaveInterval": convert_value(canvas_settings.get("autoSaveInterval"), 60),
                "gridEnabled": convert_value(canvas_settings.get("gridEnabled"), True)
            }
        }
        
        logger.info(f"Returning unified settings: {unified}")
        return unified
        
    except Exception as e:
        logger.error(f"Error getting unified settings: {str(e)}")
        # Return default settings on error
        return {
            "nautobot": {
                "enabled": False,
                "url": "",
                "token": "",
                "verifyTls": True,
                "timeout": 30
            },
            "checkmk": {
                "enabled": False,
                "url": "",
                "site": "cmk",
                "username": "",
                "password": "",
                "verifyTls": True
            },
            "canvas": {
                "autoSaveInterval": 60,
                "gridEnabled": True
            }
        }


@router.post("/unified")
async def save_unified_settings(
    settings_data: dict,
    current_user: User = Depends(get_current_user_from_db)
):
    """Save unified settings to local database."""
    try:
        logger.info(f"Saving settings for user {current_user.username}: {settings_data}")
        
        # Save each category of settings
        for category, settings in settings_data.items():
            if category in ["nautobot", "checkmk", "canvas"]:
                for key, value in settings.items():
                    # Encrypt sensitive fields
                    is_encrypted = key in ["token", "password"]
                    
                    # Convert value to appropriate format for storage
                    if isinstance(value, bool):
                        store_value = "true" if value else "false"
                    else:
                        store_value = str(value) if value is not None else ""
                    
                    if is_encrypted and store_value:
                        store_value = encrypt_password(store_value)
                    
                    logger.info(f"Storing {category}.{key} = {store_value} (encrypted: {is_encrypted})")
                    
                    store_setting(
                        owner=current_user.username,
                        category=category,
                        key=key,
                        value=store_value,
                        is_encrypted=is_encrypted
                    )
        
        return {"message": "Settings saved successfully"}
        
    except Exception as e:
        logger.error(f"Error saving unified settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save settings: {str(e)}"
        )


# Test connection endpoints
@router.post("/test-nautobot")
async def test_nautobot_connection(
    test_request: NautobotTestRequest,
    current_user: User = Depends(get_current_user_from_db)
):
    """Test Nautobot connection."""
    try:
        logger.info(f"Testing Nautobot connection for user {current_user.username}")
        logger.info(f"URL: {test_request.url}, timeout: {test_request.timeout}, verify_ssl: {test_request.verify_ssl}")
        
        success, message = await nautobot_service.test_connection(
            url=test_request.url,
            token=test_request.token,
            verify_ssl=test_request.verify_ssl,
            timeout=test_request.timeout,
        )
        
        logger.info(f"Nautobot test result: success={success}, message={message}")
        
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
    test_request: CheckMKTestRequest,
    current_user: User = Depends(get_current_user_from_db)
):
    """Test CheckMK connection."""
    try:
        logger.info(f"Testing CheckMK connection for user {current_user.username}")
        logger.info(f"URL: {test_request.url}, site: {test_request.site}, username: {test_request.username}, verify_ssl: {test_request.verify_ssl}")
        
        success, message = await checkmk_service.test_connection(
            url=test_request.url,
            site=test_request.site,
            username=test_request.username,
            password=test_request.password,
            verify_ssl=test_request.verify_ssl,
        )
        
        logger.info(f"CheckMK test result: success={success}, message={message}")
        
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