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
        
        # Structure the response to match expected format
        unified = {
            "nautobot": settings.get("nautobot", {
                "enabled": False,
                "url": "",
                "token": "",
                "verifyTls": True,
                "timeout": 30
            }),
            "checkmk": settings.get("checkmk", {
                "enabled": False,
                "url": "",
                "site": "cmk",
                "username": "",
                "password": "",
                "verifyTls": True
            }),
            "canvas": settings.get("canvas", {
                "autoSaveInterval": 60,
                "gridEnabled": True
            })
        }
        
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
        # Save each category of settings
        for category, settings in settings_data.items():
            if category in ["nautobot", "checkmk", "canvas"]:
                for key, value in settings.items():
                    # Encrypt sensitive fields
                    is_encrypted = key in ["token", "password"]
                    if is_encrypted and value:
                        value = encrypt_password(str(value))
                    
                    store_setting(
                        owner=current_user.username,
                        category=category,
                        key=key,
                        value=value,
                        is_encrypted=is_encrypted
                    )
        
        return {"message": "Settings saved successfully"}
        
    except Exception as e:
        logger.error(f"Error saving unified settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save settings: {str(e)}"
        )


# Test connection endpoints (unchanged)
@router.post("/test-nautobot")
async def test_nautobot_connection(
    test_request: NautobotTestRequest,
    current_user: User = Depends(get_current_user_from_db)
):
    """Test Nautobot connection."""
    try:
        await nautobot_service.test_connection(
            url=test_request.url,
            token=test_request.token,
            verify_ssl=test_request.verify_ssl,
            timeout=test_request.timeout,
        )
        message = "Successfully connected to Nautobot"
        return {
            "success": True,
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
        success, message = await checkmk_service.test_connection(
            url=test_request.url,
            site=test_request.site,
            username=test_request.username,
            password=test_request.password,
            verify_ssl=test_request.verify_ssl,
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