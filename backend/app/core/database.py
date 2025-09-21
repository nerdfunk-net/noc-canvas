from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .yaml_config import get_database_url
import logging

logger = logging.getLogger(__name__)


# Create engine with PostgreSQL URL
def create_database_engine():
    """Create SQLAlchemy engine for PostgreSQL database."""
    try:
        database_url = get_database_url()
        logger.info("Creating database engine for PostgreSQL")
        return create_engine(database_url, pool_pre_ping=True, pool_recycle=300)
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        raise


engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_database_connection() -> bool:
    """
    Test database connection.

    Returns:
        True if connection successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False
