"""
Credential models for storing user credentials in separate database.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, List
import os
from cryptography.fernet import Fernet
import base64

# Create separate base for credentials database
CredentialsBase = declarative_base()

class UserCredential(CredentialsBase):
    """User credentials stored in separate database."""
    __tablename__ = "user_credentials"

    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String(255), index=True, nullable=False)  # Username of the owner
    name = Column(String(255), nullable=False)  # Credential name/description
    username = Column(String(255), nullable=False)  # Stored username
    encrypted_password = Column(Text, nullable=False)  # Encrypted password
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Database setup for credentials
def get_credentials_db_path():
    """Get path to credentials database."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    db_dir = os.path.join(base_dir, "data", "settings")
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "credentials.db")


def get_credentials_engine():
    """Create SQLAlchemy engine for credentials database."""
    db_path = get_credentials_db_path()
    database_url = f"sqlite:///{db_path}"
    return create_engine(database_url, connect_args={"check_same_thread": False})


def create_credentials_tables():
    """Create credentials database tables."""
    engine = get_credentials_engine()
    CredentialsBase.metadata.create_all(bind=engine)


def get_credentials_session():
    """Get database session for credentials."""
    engine = get_credentials_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


# Encryption utilities
def get_or_create_encryption_key():
    """Get or create encryption key for passwords."""
    key_dir = os.path.dirname(get_credentials_db_path())
    key_file = os.path.join(key_dir, ".encryption_key")
    
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
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


class CredentialCreate(CredentialBase):
    """Credential creation model."""
    pass


class CredentialUpdate(BaseModel):
    """Credential update model."""
    name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class CredentialResponse(BaseModel):
    """Credential response model (without password)."""
    id: int
    owner: str
    name: str
    username: str
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


# Initialize credentials database on import
create_credentials_tables()