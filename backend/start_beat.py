#!/usr/bin/env python3
"""
Start Celery Beat scheduler with SQLAlchemy database backend.

This script starts the Celery Beat periodic task scheduler that reads
schedules from the PostgreSQL database and dispatches tasks to workers.

Usage:
    python start_beat.py

    or with custom log level:
    python start_beat.py --loglevel=debug
"""

import sys
import logging
from pathlib import Path

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import celery

        logger.info(f"✓ Celery version: {celery.__version__}")
    except ImportError:
        logger.error("✗ Celery is not installed. Run: pip install celery")
        return False

    try:
        import celery_sqlalchemy_scheduler  # noqa: F401

        logger.info("✓ celery-sqlalchemy-scheduler installed")
    except ImportError:
        logger.error(
            "✗ celery-sqlalchemy-scheduler is not installed. Run: pip install celery-sqlalchemy-scheduler"
        )
        return False

    try:
        import redis  # noqa: F401

        logger.info("✓ Redis client installed")
    except ImportError:
        logger.error("✗ Redis client is not installed. Run: pip install redis")
        return False

    return True


def check_redis_connection():
    """Check if Redis is accessible."""
    try:
        import redis
        from app.core.config import settings

        r = redis.from_url(settings.celery_broker_url, socket_connect_timeout=2)
        r.ping()
        logger.info(f"✓ Redis is accessible at {settings.celery_broker_url}")
        return True
    except Exception as e:
        logger.error(f"✗ Cannot connect to Redis: {e}")
        logger.error("  Make sure Redis is running: redis-server")
        return False


def check_database_connection():
    """Check if database is accessible."""
    try:
        from app.core.database import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        logger.info("✓ Database is accessible")
        return True
    except Exception as e:
        logger.error(f"✗ Cannot connect to database: {e}")
        logger.error("  Make sure PostgreSQL is running and configured correctly")
        return False


def start_beat():
    """Start Celery Beat scheduler."""
    try:
        from app.services.background_jobs import celery_app, CELERY_AVAILABLE

        if not CELERY_AVAILABLE or not celery_app:
            logger.error("✗ Celery is not available")
            return False

        logger.info("=" * 60)
        logger.info("Starting Celery Beat Scheduler")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Scheduler: DatabaseScheduler (celery-sqlalchemy-scheduler)")
        logger.info("Database: PostgreSQL")
        logger.info("")
        logger.info("This will:")
        logger.info("  1. Read scheduled tasks from the database")
        logger.info("  2. Dispatch tasks to workers at their scheduled times")
        logger.info("  3. Update last run times and execution counts")
        logger.info("")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        logger.info("")

        # Parse command line arguments
        argv = sys.argv[1:]
        if not argv:
            argv = ["beat", "--loglevel=info"]
        elif "beat" not in argv:
            argv.insert(0, "beat")

        # Start Celery Beat
        celery_app.start(argv=argv)

    except KeyboardInterrupt:
        logger.info("\n\n" + "=" * 60)
        logger.info("Celery Beat stopped by user")
        logger.info("=" * 60)
        return True
    except Exception as e:
        logger.error(f"✗ Failed to start Celery Beat: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("NOC Canvas - Celery Beat Scheduler")
    print("=" * 60 + "\n")

    # Check dependencies
    logger.info("Checking dependencies...")
    if not check_dependencies():
        logger.error("\nPlease install missing dependencies and try again.")
        sys.exit(1)

    logger.info("")

    # Check Redis connection
    logger.info("Checking Redis connection...")
    if not check_redis_connection():
        logger.error("\nPlease start Redis and try again.")
        logger.error("macOS: brew services start redis")
        logger.error("Linux: sudo systemctl start redis")
        sys.exit(1)

    logger.info("")

    # Check database connection
    logger.info("Checking database connection...")
    if not check_database_connection():
        logger.error("\nPlease check your database configuration and try again.")
        sys.exit(1)

    logger.info("")

    # All checks passed, start Beat
    logger.info("All checks passed! Starting Celery Beat...\n")

    success = start_beat()

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
