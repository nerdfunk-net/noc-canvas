# PostgreSQL Migration Plan

## Current State Analysis

### Current Database Architecture
- **Main Database**: SQLite (`noc_canvas.db`) - Application settings via `AppSettings` model
- **Credentials Database**: SQLite (`./data/settings/credentials.db`) - Encrypted user credentials via `UserCredential` model
- **Configuration**: Environment/config-based settings in `config.py`
- **Encryption**: Fernet encryption for passwords with key stored in `./data/settings/.encryption_key`

### Current File Structure
```
./data/settings/
├── credentials.db (SQLite - UserCredential table)
├── settings.db (SQLite - AppSettings table)
└── .encryption_key (Fernet encryption key)
```

## Migration Requirements

1. ✅ Remove database "enabled" slider from frontend settings
2. ✅ Store database settings in `./data/settings/database.yaml`
3. ✅ Check environment variables on startup (NOC_DATABASE, NOC_USERNAME, NOC_PASSWORD)
4. ✅ Initialize PostgreSQL database with required tables
5. ✅ Migrate from current SQLite databases to PostgreSQL-only

## Implementation Plan

### Phase 1: Frontend Changes

#### 1.1 Remove Database Toggle from Settings Store
**File**: `frontend/src/stores/settings.ts`
- Remove `enabled` field from `DatabaseSettings` interface
- Remove `enabled: false` from default settings
- Update `loadSettings` and `saveSettings` to handle missing database config

#### 1.2 Update Settings View
**File**: `frontend/src/views/SettingsView.vue`
- Remove database enabled toggle switch
- Update database panel to show connection status instead
- Add connection test functionality

### Phase 2: Backend Configuration System

#### 2.1 Create YAML Configuration Handler
**File**: `backend/app/core/yaml_config.py`
```python
import yaml
import os
from typing import Optional, Dict, Any
from pydantic import BaseModel

class DatabaseConfig(BaseModel):
    host: str
    port: int = 5432
    database: str
    username: str
    password: str
    ssl: bool = False

def load_database_config() -> Optional[DatabaseConfig]:
    """Load database config from YAML file or environment variables."""
    config_path = "./data/settings/database.yaml"

    # Check environment variables first
    env_host = os.getenv("NOC_DATABASE")
    env_username = os.getenv("NOC_USERNAME")
    env_password = os.getenv("NOC_PASSWORD")

    if env_host and env_username and env_password:
        return DatabaseConfig(
            host=env_host,
            database="noc_canvas",
            username=env_username,
            password=env_password
        )

    # Fall back to YAML file
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
            return DatabaseConfig(**config_data)

    return None

def save_database_config(config: DatabaseConfig):
    """Save database config to YAML file."""
    os.makedirs("./data/settings", exist_ok=True)
    config_path = "./data/settings/database.yaml"

    with open(config_path, 'w') as f:
        yaml.dump(config.dict(), f, default_flow_style=False)
```

#### 2.2 Update Core Database Module
**File**: `backend/app/core/database.py`
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .yaml_config import load_database_config
import os

def get_database_url() -> str:
    """Get PostgreSQL database URL from config or environment."""
    config = load_database_config()

    if not config:
        raise RuntimeError("No database configuration found. Please set environment variables or create database.yaml")

    if config.ssl:
        return f"postgresql://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}?sslmode=require"
    else:
        return f"postgresql://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"

# Create engine with PostgreSQL URL
engine = create_engine(get_database_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### 2.3 Create Database Initialization System
**File**: `backend/app/core/db_init.py`
```python
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from .yaml_config import load_database_config
from ..models.settings import Base as SettingsBase
from ..models.credential import CredentialsBase
import logging

logger = logging.getLogger(__name__)

def create_database_if_not_exists():
    """Create PostgreSQL database if it doesn't exist."""
    config = load_database_config()
    if not config:
        raise RuntimeError("No database configuration found")

    # Connect to PostgreSQL server (not specific database)
    server_url = f"postgresql://{config.username}:{config.password}@{config.host}:{config.port}/postgres"

    try:
        engine = create_engine(server_url)
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{config.database}'"))
            if not result.fetchone():
                # Create database
                conn.execute(text("COMMIT"))  # Close any transaction
                conn.execute(text(f"CREATE DATABASE {config.database}"))
                logger.info(f"Created database: {config.database}")
    except OperationalError as e:
        logger.error(f"Failed to create database: {e}")
        raise

def initialize_tables():
    """Create all required tables in PostgreSQL."""
    from .database import engine

    # Create settings tables
    SettingsBase.metadata.create_all(bind=engine)

    # Create credentials tables
    CredentialsBase.metadata.create_all(bind=engine)

    logger.info("Database tables initialized successfully")

def migrate_sqlite_data():
    """Migrate data from SQLite databases to PostgreSQL."""
    import sqlite3
    from sqlalchemy.orm import sessionmaker
    from .database import engine
    from ..models.settings import AppSettings
    from ..models.credential import UserCredential, decrypt_password, encrypt_password

    SessionLocal = sessionmaker(bind=engine)

    # Migrate settings data
    settings_db_path = "./data/settings/settings.db"
    if os.path.exists(settings_db_path):
        sqlite_conn = sqlite3.connect(settings_db_path)
        sqlite_conn.row_factory = sqlite3.Row

        with SessionLocal() as session:
            cursor = sqlite_conn.execute("SELECT * FROM app_settings")
            for row in cursor:
                existing = session.query(AppSettings).filter_by(key=row['key']).first()
                if not existing:
                    setting = AppSettings(
                        key=row['key'],
                        value=row['value'],
                        description=row['description']
                    )
                    session.add(setting)
            session.commit()
        sqlite_conn.close()
        logger.info("Migrated settings data from SQLite")

    # Migrate credentials data
    credentials_db_path = "./data/settings/credentials.db"
    if os.path.exists(credentials_db_path):
        sqlite_conn = sqlite3.connect(credentials_db_path)
        sqlite_conn.row_factory = sqlite3.Row

        with SessionLocal() as session:
            cursor = sqlite_conn.execute("SELECT * FROM user_credentials")
            for row in cursor:
                existing = session.query(UserCredential).filter_by(
                    owner=row['owner'],
                    name=row['name']
                ).first()
                if not existing:
                    credential = UserCredential(
                        owner=row['owner'],
                        name=row['name'],
                        username=row['username'],
                        encrypted_password=row['encrypted_password']
                    )
                    session.add(credential)
            session.commit()
        sqlite_conn.close()
        logger.info("Migrated credentials data from SQLite")

def full_database_setup():
    """Complete database setup process."""
    try:
        create_database_if_not_exists()
        initialize_tables()
        migrate_sqlite_data()
        logger.info("Database setup completed successfully")
        return True
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False
```

### Phase 3: Update Models and Remove SQLite Dependencies

#### 3.1 Update Credential Model
**File**: `backend/app/models/credential.py`
- Remove SQLite-specific database functions
- Update to use main PostgreSQL connection
- Keep encryption functionality unchanged

#### 3.2 Update Configuration
**File**: `backend/app/core/config.py`
- Remove `database_url` from settings
- Add database configuration validation
- Update to use YAML config system

### Phase 4: Application Startup Integration

#### 4.1 Update Main Application
**File**: `backend/app/main.py`
```python
from .core.db_init import full_database_setup
import logging

logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    logger.info("Starting database initialization...")
    success = full_database_setup()
    if not success:
        logger.error("Failed to initialize database. Application may not work correctly.")
    else:
        logger.info("Database initialization completed successfully")
```

#### 4.2 Add Environment Variable Documentation
**File**: `README.md` or `.env.example`
```env
# Database Configuration (Optional - overrides database.yaml)
NOC_DATABASE=localhost
NOC_USERNAME=noc_user
NOC_PASSWORD=secure_password
```

### Phase 5: API Endpoints Update

#### 5.1 Update Settings API
**File**: `backend/app/api/settings.py`
- Remove database "enabled" field from unified settings
- Add database connection test endpoint
- Update to use YAML configuration

#### 5.2 Add Database Management Endpoints
```python
@router.post("/database/test")
async def test_database_connection(config: DatabaseConfig):
    """Test database connection with provided configuration."""

@router.post("/database/config")
async def save_database_config(config: DatabaseConfig):
    """Save database configuration to YAML file."""

@router.get("/database/status")
async def get_database_status():
    """Get current database connection status."""
```

### Phase 6: Migration Script

#### 6.1 Create Migration Command
**File**: `backend/migrate_to_postgresql.py`
```python
#!/usr/bin/env python3
"""
Migration script to move from SQLite to PostgreSQL.
Usage: python migrate_to_postgresql.py
"""

import sys
import os
from app.core.db_init import full_database_setup
from app.core.yaml_config import DatabaseConfig, save_database_config

def interactive_setup():
    """Interactive setup for database configuration."""
    print("PostgreSQL Migration Setup")
    print("=" * 30)

    host = input("Database Host [localhost]: ") or "localhost"
    port = int(input("Database Port [5432]: ") or "5432")
    database = input("Database Name [noc_canvas]: ") or "noc_canvas"
    username = input("Database Username: ")
    password = input("Database Password: ")
    ssl = input("Use SSL? [y/N]: ").lower().startswith('y')

    config = DatabaseConfig(
        host=host,
        port=port,
        database=database,
        username=username,
        password=password,
        ssl=ssl
    )

    save_database_config(config)
    return config

if __name__ == "__main__":
    try:
        # Check if database config exists
        from app.core.yaml_config import load_database_config

        config = load_database_config()
        if not config:
            print("No database configuration found.")
            config = interactive_setup()

        print(f"Using database: {config.host}:{config.port}/{config.database}")

        # Run migration
        success = full_database_setup()
        if success:
            print("✅ Migration completed successfully!")
            print("\nNext steps:")
            print("1. Verify data in PostgreSQL database")
            print("2. Update your application to use the new database")
            print("3. Remove old SQLite files when satisfied")
        else:
            print("❌ Migration failed. Check logs for details.")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Migration error: {e}")
        sys.exit(1)
```

### Phase 7: Cleanup and Validation

#### 7.1 Post-Migration Validation
- Verify all data migrated correctly
- Test all API endpoints
- Confirm encryption/decryption works
- Validate configuration loading

#### 7.2 SQLite Removal (Final Step)
- Remove SQLite database files
- Remove SQLite-specific code
- Update documentation

## Migration Timeline

1. **Phase 1-2**: Frontend and backend configuration setup (1-2 days)
2. **Phase 3-4**: Model updates and application integration (1-2 days)
3. **Phase 5**: API endpoint updates (1 day)
4. **Phase 6**: Migration script and testing (1-2 days)
5. **Phase 7**: Validation and cleanup (1 day)

**Total Estimated Time**: 5-8 days

## Risk Mitigation

1. **Backup Strategy**: Create backups of existing SQLite databases before migration
2. **Rollback Plan**: Keep SQLite functionality available during transition
3. **Testing**: Comprehensive testing of data integrity post-migration
4. **Documentation**: Clear documentation for environment setup and configuration

## Success Criteria

- ✅ PostgreSQL database successfully initialized
- ✅ All existing data migrated without loss
- ✅ Environment variable configuration working
- ✅ YAML configuration file system operational
- ✅ All API endpoints functioning correctly
- ✅ Encryption/decryption maintaining data security
- ✅ Frontend database configuration panel updated
- ✅ SQLite dependencies completely removed