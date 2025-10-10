"""
Background job service for long-running tasks.
"""

import logging
from typing import Dict, Any, Optional, List
from ..core.config import settings

logger = logging.getLogger(__name__)

try:
    from celery import Celery
    import pytz

    CELERY_AVAILABLE = True

    # Create Celery app
    celery_app = Celery(
        "noc_canvas",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
        include=[
            "app.tasks.topology_tasks",
            "app.tasks.nautobot_tasks",
            "app.tasks.checkmk_tasks",
            "app.tasks.cache_tasks",
            "app.tasks.cleanup_tasks",
            "app.tasks.test_tasks",
            "app.tasks.baseline_tasks",
        ],
    )
except ImportError:
    logger.warning("Celery not available. Background jobs will be disabled.")
    CELERY_AVAILABLE = False
    celery_app = None

# Configure Celery
if CELERY_AVAILABLE and celery_app:
    from ..core.database import engine

    # Get database URI with password for Celery Beat
    # SQLAlchemy 2.0+ uses render_as_string, older versions use __str__
    try:
        db_uri = engine.url.render_as_string(hide_password=False)
    except AttributeError:
        # Fallback for older SQLAlchemy versions
        db_uri = str(engine.url).replace('***', engine.url.password or '')

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone=pytz.UTC,
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 minutes
        task_soft_time_limit=25 * 60,  # 25 minutes
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        result_extended=True,  # Store task name and other metadata in results
        # Configure Celery Beat with SQLAlchemy scheduler
        beat_scheduler='celery_sqlalchemy_scheduler.schedulers:DatabaseScheduler',
        beat_dburi=db_uri,  # Use the same database as the app with password
        beat_schema='celerybeat',  # Schema for beat tables (optional)
    )


class BackgroundJobService:
    """Service for managing background jobs."""

    def __init__(self):
        self.celery = celery_app
        self.enabled = CELERY_AVAILABLE and celery_app is not None

    def submit_job(self, task_name: str, *args, **kwargs) -> str:
        """Submit a background job."""
        if not self.enabled:
            raise Exception(
                "Background job service is not available. Please install and configure Celery."
            )

        try:
            task = self.celery.send_task(task_name, args=args, kwargs=kwargs)
            logger.info(f"Submitted job {task_name} with ID: {task.id}")
            return task.id
        except Exception as e:
            logger.error(f"Error submitting job {task_name}: {str(e)}")
            raise

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status and result."""
        if not self.enabled:
            return {
                "id": job_id,
                "status": "ERROR",
                "result": None,
                "traceback": "Background job service is not available",
                "info": None,
            }

        try:
            task_result = self.celery.AsyncResult(job_id)
            return {
                "id": job_id,
                "status": task_result.status,
                "result": task_result.result,
                "traceback": task_result.traceback,
                "info": task_result.info,
            }
        except Exception as e:
            logger.error(f"Error getting job status for {job_id}: {str(e)}")
            return {
                "id": job_id,
                "status": "ERROR",
                "result": None,
                "traceback": str(e),
                "info": None,
            }

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job."""
        if not self.enabled:
            return False

        try:
            self.celery.control.revoke(job_id, terminate=True)
            logger.info(f"Cancelled job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling job {job_id}: {str(e)}")
            return False




# Register all tasks
if CELERY_AVAILABLE and celery_app:
    # Import and register tasks from task modules
    from ..tasks import nautobot_tasks
    from ..tasks import checkmk_tasks
    from ..tasks import cache_tasks
    from ..tasks import cleanup_tasks
    from ..tasks import test_tasks
    from ..tasks import baseline_tasks
    
    # Register tasks with the Celery app
    nautobot_tasks.register_tasks(celery_app)
    checkmk_tasks.register_tasks(celery_app)
    cache_tasks.register_tasks(celery_app)
    cleanup_tasks.register_tasks(celery_app)
    test_tasks.register_tasks(celery_app)
    baseline_tasks.register_tasks(celery_app)


# Global service instance
background_job_service = BackgroundJobService()
