"""
Credential models for storing user credentials in PostgreSQL database.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, List
import os
import enum
from cryptography.fernet import Fernet
import base64
from ..core.database import Base, engine

# Use main database Base for credentials
CredentialsBase = Base


class CredentialPurpose(enum.Enum):
    """Purpose of the credential."""
    TACACS = "tacacs"
    SSH = "ssh"


class UserCredential(CredentialsBase):
    """User credentials stored in separate database."""

    __tablename__ = "user_credentials"

    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String(255), index=True, nullable=False)  # Username of the owner
    name = Column(String(255), nullable=False)  # Credential name/description
    username = Column(String(255), nullable=False)  # Stored username
    encrypted_password = Column(Text, nullable=False)  # Encrypted password
    purpose = Column(Enum(CredentialPurpose), nullable=False, default=CredentialPurpose.SSH)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Database setup for credentials using main PostgreSQL database
def create_credentials_tables():
    """Create credentials database tables."""
    CredentialsBase.metadata.create_all(bind=engine)


def get_credentials_session():
    """Get database session for credentials."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


# Encryption utilities
def get_or_create_encryption_key():
    """Get or create encryption key for passwords."""
    key_dir = "./data/settings"
    os.makedirs(key_dir, exist_ok=True)
    key_file = os.path.join(key_dir, ".encryption_key")

    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(key)
        # Set restrictive permissions on key file
        os.chmod(key_file, 0o600)
        return key


def encrypt_password(password: str) -> str:
    """Encrypt password using Fernet encryption."""
    key = get_or_create_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(password.encode())
    return base64.b64encode(encrypted).decode()


def decrypt_password(encrypted_password: str) -> str:
    """Decrypt password using Fernet encryption."""
    key = get_or_create_encryption_key()
    f = Fernet(key)
    encrypted_bytes = base64.b64decode(encrypted_password.encode())
    decrypted = f.decrypt(encrypted_bytes)
    return decrypted.decode()


# Pydantic models for API
class CredentialBase(BaseModel):
    """Base credential model."""

    name: str
    username: str
    password: str
    purpose: CredentialPurpose = CredentialPurpose.SSH


class CredentialCreate(CredentialBase):
    """Credential creation model."""

    pass


class CredentialUpdate(BaseModel):
    """Credential update model."""

    name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    purpose: Optional[CredentialPurpose] = None


class CredentialResponse(BaseModel):
    """Credential response model (without password)."""

    id: int
    owner: str
    name: str
    username: str
    purpose: CredentialPurpose
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class CredentialWithPassword(CredentialResponse):
    """Credential response model with decrypted password."""

    password: str


class CredentialsList(BaseModel):
    """List of credentials response."""

    credentials: List[CredentialResponse]


class CredentialsListWithPasswords(BaseModel):
    """List of credentials response with passwords."""

    credentials: List[CredentialWithPassword]


# Note: Database tables will be initialized during application startup
