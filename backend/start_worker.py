#!/usr/bin/env python3
"""
Start Celery Worker for background task processing.

This script starts a Celery Worker that processes background tasks
dispatched by the Celery Beat scheduler or API endpoints.

Usage:
    python start_worker.py

    or with custom options:
    python start_worker.py --loglevel=debug --concurrency=4
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


def list_registered_tasks():
    """List all registered Celery tasks."""
    try:
        from app.services.background_jobs import celery_app, CELERY_AVAILABLE

        if not CELERY_AVAILABLE or not celery_app:
            return []

        tasks = sorted(celery_app.tasks.keys())
        # Filter out celery internal tasks
        tasks = [t for t in tasks if not t.startswith("celery.")]
        return tasks
    except Exception as e:
        logger.warning(f"Could not list tasks: {e}")
        return []


def start_worker():
    """Start Celery Worker."""
    try:
        from app.services.background_jobs import celery_app, CELERY_AVAILABLE

        if not CELERY_AVAILABLE or not celery_app:
            logger.error("✗ Celery is not available")
            return False

        logger.info("=" * 60)
        logger.info("Starting Celery Worker")
        logger.info("=" * 60)
        logger.info("")

        # List registered tasks
        tasks = list_registered_tasks()
        if tasks:
            logger.info(f"Registered tasks ({len(tasks)}):")
            for task in tasks:
                logger.info(f"  • {task}")
        else:
            logger.info("No tasks registered yet")

        logger.info("")
        logger.info("This worker will:")
        logger.info("  1. Process tasks sent to the queue")
        logger.info("  2. Execute scheduled tasks from Celery Beat")
        logger.info("  3. Report task results to the result backend")
        logger.info("")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        logger.info("")

        # Parse command line arguments
        argv = sys.argv[1:]
        if not argv:
            argv = ["worker", "--loglevel=info"]
        elif "worker" not in argv:
            argv.insert(0, "worker")

        # Start Celery Worker
        celery_app.start(argv=argv)

    except KeyboardInterrupt:
        logger.info("\n\n" + "=" * 60)
        logger.info("Celery Worker stopped by user")
        logger.info("=" * 60)
        return True
    except Exception as e:
        logger.error(f"✗ Failed to start Celery Worker: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("NOC Canvas - Celery Worker")
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

    # All checks passed, start Worker
    logger.info("All checks passed! Starting Celery Worker...\n")

    success = start_worker()

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
