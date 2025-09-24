"""
Credentials API router for managing user credentials with database storage.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.security import get_current_user
from ..core.database import get_db
from ..models.credential import (
    UserCredential,
    CredentialCreate,
    CredentialUpdate,
    CredentialResponse,
    CredentialWithPassword,
    CredentialsList,
    CredentialsListWithPasswords,
    CredentialPurpose,
    encrypt_password,
    decrypt_password,
    create_credentials_tables,
    get_credentials_session,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Credentials database initialization is handled in main application startup


@router.get("/", response_model=CredentialsList)
async def get_user_credentials(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all credentials for the current user (without passwords)."""
    try:
        username = (
            current_user.get("username")
            if isinstance(current_user, dict)
            else current_user.username
        )

        # Query credentials for the current user
        credentials = (
            db.query(UserCredential)
            .filter(UserCredential.owner == username)
            .all()
        )

        # Convert to response models
        credential_responses = []
        for cred in credentials:
            credential_responses.append(
                CredentialResponse(
                    id=cred.id,
                    owner=cred.owner,
                    name=cred.name,
                    username=cred.username,
                    purpose=cred.purpose,
                    created_at=cred.created_at.isoformat(),
                    updated_at=cred.updated_at.isoformat() if cred.updated_at else None,
                )
            )

        return CredentialsList(credentials=credential_responses)

    except Exception as e:
        logger.error(f"Error getting user credentials: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get credentials: {str(e)}",
        )


@router.get("/with-passwords", response_model=CredentialsListWithPasswords)
async def get_user_credentials_with_passwords(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all credentials for the current user (including decrypted passwords)."""
    try:
        username = (
            current_user.get("username")
            if isinstance(current_user, dict)
            else current_user.username
        )

        # Query credentials for the current user
        credentials = (
            db.query(UserCredential)
            .filter(UserCredential.owner == username)
            .all()
        )

        # Convert to response models with passwords
        credential_responses = []
        for cred in credentials:
            try:
                decrypted_password = decrypt_password(cred.encrypted_password)
                credential_responses.append(
                    CredentialWithPassword(
                        id=cred.id,
                        owner=cred.owner,
                        name=cred.name,
                        username=cred.username,
                        purpose=cred.purpose,
                        password=decrypted_password,
                        created_at=cred.created_at.isoformat(),
                        updated_at=cred.updated_at.isoformat() if cred.updated_at else None,
                    )
                )
            except Exception as decrypt_error:
                logger.error(f"Error decrypting password for credential {cred.id}: {str(decrypt_error)}")
                # Skip credentials that can't be decrypted
                continue

        return CredentialsListWithPasswords(credentials=credential_responses)

    except Exception as e:
        logger.error(f"Error getting user credentials with passwords: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get credentials: {str(e)}",
        )


@router.get("/{credential_id}", response_model=CredentialResponse)
async def get_credential(
    credential_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific credential by ID (without password)."""
    try:
        username = (
            current_user.get("username")
            if isinstance(current_user, dict)
            else current_user.username
        )

        credential = (
            db.query(UserCredential)
            .filter(
                UserCredential.id == credential_id,
                UserCredential.owner == username
            )
            .first()
        )

        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credential {credential_id} not found"
            )

        return CredentialResponse(
            id=credential.id,
            owner=credential.owner,
            name=credential.name,
            username=credential.username,
            purpose=credential.purpose,
            created_at=credential.created_at.isoformat(),
            updated_at=credential.updated_at.isoformat() if credential.updated_at else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting credential {credential_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get credential: {str(e)}",
        )


@router.post("/", response_model=CredentialResponse)
async def create_credential(
    credential_data: CredentialCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new credential."""
    try:
        username = (
            current_user.get("username")
            if isinstance(current_user, dict)
            else current_user.username
        )

        # Encrypt the password
        encrypted_password = encrypt_password(credential_data.password)

        # Create new credential
        new_credential = UserCredential(
            owner=username,
            name=credential_data.name,
            username=credential_data.username,
            encrypted_password=encrypted_password,
            purpose=credential_data.purpose,
        )

        db.add(new_credential)
        db.commit()
        db.refresh(new_credential)

        logger.info(f"Created new credential '{credential_data.name}' for user {username}")

        return CredentialResponse(
            id=new_credential.id,
            owner=new_credential.owner,
            name=new_credential.name,
            username=new_credential.username,
            purpose=new_credential.purpose,
            created_at=new_credential.created_at.isoformat(),
            updated_at=new_credential.updated_at.isoformat() if new_credential.updated_at else None,
        )

    except Exception as e:
        logger.error(f"Error creating credential: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create credential: {str(e)}",
        )


@router.put("/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    credential_id: int,
    credential_data: CredentialUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an existing credential."""
    try:
        username = (
            current_user.get("username")
            if isinstance(current_user, dict)
            else current_user.username
        )

        # Get existing credential
        credential = (
            db.query(UserCredential)
            .filter(
                UserCredential.id == credential_id,
                UserCredential.owner == username
            )
            .first()
        )

        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credential {credential_id} not found"
            )

        # Update fields if provided
        if credential_data.name is not None:
            credential.name = credential_data.name
        if credential_data.username is not None:
            credential.username = credential_data.username
        if credential_data.purpose is not None:
            credential.purpose = credential_data.purpose
        if credential_data.password is not None:
            credential.encrypted_password = encrypt_password(credential_data.password)

        db.commit()
        db.refresh(credential)

        logger.info(f"Updated credential {credential_id} for user {username}")

        return CredentialResponse(
            id=credential.id,
            owner=credential.owner,
            name=credential.name,
            username=credential.username,
            purpose=credential.purpose,
            created_at=credential.created_at.isoformat(),
            updated_at=credential.updated_at.isoformat() if credential.updated_at else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating credential {credential_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update credential: {str(e)}",
        )


@router.delete("/{credential_id}")
async def delete_credential(
    credential_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a credential."""
    try:
        username = (
            current_user.get("username")
            if isinstance(current_user, dict)
            else current_user.username
        )

        # Get existing credential
        credential = (
            db.query(UserCredential)
            .filter(
                UserCredential.id == credential_id,
                UserCredential.owner == username
            )
            .first()
        )

        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credential {credential_id} not found"
            )

        db.delete(credential)
        db.commit()

        logger.info(f"Deleted credential {credential_id} for user {username}")

        return {"message": "Credential deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting credential {credential_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete credential: {str(e)}",
        )


@router.get("/by-purpose/{purpose}", response_model=CredentialsList)
async def get_credentials_by_purpose(
    purpose: CredentialPurpose,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get credentials filtered by purpose (e.g., 'ssh' or 'tacacs')."""
    try:
        username = (
            current_user.get("username")
            if isinstance(current_user, dict)
            else current_user.username
        )

        # Query credentials for the current user filtered by purpose
        credentials = (
            db.query(UserCredential)
            .filter(
                UserCredential.owner == username,
                UserCredential.purpose == purpose
            )
            .all()
        )

        # Convert to response models
        credential_responses = []
        for cred in credentials:
            credential_responses.append(
                CredentialResponse(
                    id=cred.id,
                    owner=cred.owner,
                    name=cred.name,
                    username=cred.username,
                    purpose=cred.purpose,
                    created_at=cred.created_at.isoformat(),
                    updated_at=cred.updated_at.isoformat() if cred.updated_at else None,
                )
            )

        return CredentialsList(credentials=credential_responses)

    except Exception as e:
        logger.error(f"Error getting credentials by purpose {purpose}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get credentials by purpose: {str(e)}",
        )