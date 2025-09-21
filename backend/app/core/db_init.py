"""
Database initialization system for PostgreSQL.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from .yaml_config import load_database_config, get_database_url, DatabaseConfig
import logging
import os

logger = logging.getLogger(__name__)


def create_database_if_not_exists() -> bool:
    """
    Create PostgreSQL database if it doesn't exist.

    Returns:
        True if database exists or was created successfully, False otherwise
    """
    try:
        config = load_database_config()
        if not config:
            logger.error("No database configuration found")
            return False

        # Connect to PostgreSQL server (not specific database)
        server_url = f"postgresql://{config.username}:{config.password}@{config.host}:{config.port}/postgres"

        try:
            engine = create_engine(server_url)
            with engine.connect() as conn:
                # Check if database exists
                result = conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                    {"dbname": config.database}
                )

                if not result.fetchone():
                    # Create database
                    conn.execute(text("COMMIT"))  # Close any transaction
                    conn.execute(text(f'CREATE DATABASE "{config.database}"'))
                    logger.info(f"Created database: {config.database}")
                else:
                    logger.info(f"Database {config.database} already exists")

            return True

        except OperationalError as e:
            logger.error(f"Failed to connect to PostgreSQL server: {e}")
            return False
        except ProgrammingError as e:
            logger.error(f"Failed to create database: {e}")
            return False

    except Exception as e:
        logger.error(f"Unexpected error creating database: {e}")
        return False


def initialize_tables() -> bool:
    """
    Create all required tables in PostgreSQL.

    Returns:
        True if tables created successfully, False otherwise
    """
    try:
        from .database import engine, Base
        from ..models.settings import AppSettings
        from ..models.credential import UserCredential
        from ..models.user import User

        # Create all tables using the main Base (includes users, settings, credentials)
        Base.metadata.create_all(bind=engine)
        logger.info("All database tables created successfully")

        return True

    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        return False


def create_default_admin_user() -> bool:
    """
    Create default admin user if no users exist in the database.

    Returns:
        True if admin user created or already exists, False on error
    """
    try:
        import os
        from dotenv import load_dotenv
        from sqlalchemy.orm import sessionmaker
        from .database import engine
        from ..models.user import User
        from ..core.security import get_password_hash

        # Ensure environment variables are loaded
        load_dotenv()

        # Get admin credentials from environment
        admin_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
        admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "password")

        if not admin_username or not admin_password:
            logger.warning("No default admin credentials found in environment variables")
            return False

        SessionLocal = sessionmaker(bind=engine)

        with SessionLocal() as session:
            # Check if any users exist
            user_count = session.query(User).count()

            if user_count == 0:
                logger.info("No users found, creating default admin user")

                # Create default admin user
                hashed_password = get_password_hash(admin_password)
                admin_user = User(
                    username=admin_username,
                    hashed_password=hashed_password,
                    is_active=True
                )

                session.add(admin_user)
                session.commit()

                logger.info(f"Default admin user '{admin_username}' created successfully")
                return True
            else:
                logger.info(f"Users table already has {user_count} users, skipping admin user creation")
                return True

    except Exception as e:
        logger.error(f"Failed to create default admin user: {e}")
        return False




def validate_database() -> bool:
    """
    Validate that database is working correctly.

    Returns:
        True if validation successful, False otherwise
    """
    try:
        from sqlalchemy.orm import sessionmaker
        from .database import engine
        from ..models.settings import AppSettings
        from ..models.credential import UserCredential
        from ..models.user import User

        SessionLocal = sessionmaker(bind=engine)

        with SessionLocal() as session:
            # Check that tables exist and can be queried
            settings_count = session.query(AppSettings).count()
            credentials_count = session.query(UserCredential).count()
            users_count = session.query(User).count()

            logger.info(f"PostgreSQL validation - Settings: {settings_count}, Credentials: {credentials_count}, Users: {users_count}")

            # Basic validation - tables should be accessible
            return True

    except Exception as e:
        logger.error(f"Database validation failed: {e}")
        return False


def full_database_setup() -> bool:
    """
    Complete database setup process.

    Returns:
        True if setup completed successfully, False otherwise
    """
    try:
        logger.info("Starting PostgreSQL database setup process")

        # Step 1: Create PostgreSQL database
        logger.info("Step 1: Creating PostgreSQL database if needed")
        if not create_database_if_not_exists():
            logger.error("Failed to create PostgreSQL database")
            return False

        # Step 2: Initialize tables
        logger.info("Step 2: Initializing database tables")
        if not initialize_tables():
            logger.error("Failed to initialize database tables")
            return False

        # Step 3: Create default admin user
        logger.info("Step 3: Creating default admin user if needed")
        if not create_default_admin_user():
            logger.warning("Failed to create default admin user")
            # Don't fail the entire setup for this

        # Step 4: Validate database
        logger.info("Step 4: Validating database")
        if not validate_database():
            logger.error("Database validation failed")
            return False

        logger.info("✅ Database setup completed successfully")
        return True

    except Exception as e:
        logger.error(f"Database setup failed with unexpected error: {e}")
        return False


def check_database_status() -> dict:
    """
    Check current database status and configuration.

    Returns:
        Dict with status information
    """
    status = {
        "config_found": False,
        "config_source": None,
        "connection_test": False,
        "tables_exist": False
    }

    try:
        # Check configuration
        config = load_database_config()
        if config:
            status["config_found"] = True
            # Determine config source
            if all(os.getenv(var) for var in ["NOC_DATABASE", "NOC_USERNAME", "NOC_PASSWORD"]):
                status["config_source"] = "environment"
            else:
                status["config_source"] = "yaml"

        # Test connection
        from .database import test_database_connection
        status["connection_test"] = test_database_connection()

        # Check if tables exist
        if status["connection_test"]:
            from sqlalchemy.orm import sessionmaker
            from .database import engine
            SessionLocal = sessionmaker(bind=engine)

            try:
                with SessionLocal() as session:
                    session.execute(text("SELECT 1 FROM app_settings LIMIT 1"))
                    session.execute(text("SELECT 1 FROM user_credentials LIMIT 1"))
                    session.execute(text("SELECT 1 FROM users LIMIT 1"))
                    status["tables_exist"] = True
            except:
                status["tables_exist"] = False

    except Exception as e:
        logger.error(f"Error checking database status: {e}")

    return status