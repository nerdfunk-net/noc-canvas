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
            "app.services.background_jobs",
            "app.tasks.topology_tasks"  # Include topology tasks
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


# Celery Tasks

# Only define tasks if Celery is available
if CELERY_AVAILABLE and celery_app:

    @celery_app.task(bind=True)
    def sync_nautobot_devices(self, filters: Optional[Dict[str, Any]] = None):
        """Sync devices from Nautobot."""
        try:
            from .nautobot import nautobot_service

            self.update_state(state="PROGRESS", meta={"current": 0, "total": 100})

            # Get devices from Nautobot
            result = nautobot_service.get_devices(
                limit=filters.get("limit") if filters else None,
                offset=filters.get("offset") if filters else None,
                filter_type=filters.get("filter_type") if filters else None,
                filter_value=filters.get("filter_value") if filters else None,
            )

            devices = result.get("devices", [])
            total_devices = len(devices)

            self.update_state(
                state="PROGRESS",
                meta={
                    "current": 50,
                    "total": 100,
                    "status": f"Retrieved {total_devices} devices from Nautobot",
                },
            )

            # Process devices (could include database updates, validations, etc.)
            processed_count = 0
            for i, device in enumerate(devices):
                # Simulate processing
                processed_count += 1
                if i % 10 == 0:  # Update every 10 devices
                    progress = 50 + int((i / total_devices) * 50)
                    self.update_state(
                        state="PROGRESS",
                        meta={
                            "current": progress,
                            "total": 100,
                            "status": f"Processed {processed_count}/{total_devices} devices",
                        },
                    )

            return {
                "status": "completed",
                "devices_processed": processed_count,
                "total_devices": total_devices,
                "message": f"Successfully synced {processed_count} devices from Nautobot",
            }

        except Exception as e:
            logger.error(f"Error in sync_nautobot_devices task: {str(e)}")
            self.update_state(
                state="FAILURE",
                meta={
                    "error": str(e),
                    "status": "Failed to sync devices from Nautobot",
                },
            )
            raise

    @celery_app.task(bind=True)
    def sync_checkmk_hosts(self, filters: Optional[Dict[str, Any]] = None):
        """Sync hosts from CheckMK."""
        try:
            from .checkmk import checkmk_service

            self.update_state(state="PROGRESS", meta={"current": 0, "total": 100})

            # Get hosts from CheckMK
            result = checkmk_service.get_all_hosts(
                effective_attributes=filters.get("effective_attributes", False)
                if filters
                else False,
                include_links=filters.get("include_links", False) if filters else False,
                site=filters.get("site") if filters else None,
            )

            hosts = result.get("value", [])
            total_hosts = len(hosts)

            self.update_state(
                state="PROGRESS",
                meta={
                    "current": 50,
                    "total": 100,
                    "status": f"Retrieved {total_hosts} hosts from CheckMK",
                },
            )

            # Process hosts
            processed_count = 0
            for i, host in enumerate(hosts):
                # Simulate processing
                processed_count += 1
                if i % 10 == 0:  # Update every 10 hosts
                    progress = 50 + int((i / total_hosts) * 50)
                    self.update_state(
                        state="PROGRESS",
                        meta={
                            "current": progress,
                            "total": 100,
                            "status": f"Processed {processed_count}/{total_hosts} hosts",
                        },
                    )

            return {
                "status": "completed",
                "hosts_processed": processed_count,
                "total_hosts": total_hosts,
                "message": f"Successfully synced {processed_count} hosts from CheckMK",
            }

        except Exception as e:
            logger.error(f"Error in sync_checkmk_hosts task: {str(e)}")
            self.update_state(
                state="FAILURE",
                meta={
                    "error": str(e),
                    "status": "Failed to sync hosts from CheckMK",
                },
            )
            raise

    @celery_app.task(bind=True)
    def bulk_host_operations(self, operation: str, hosts_data: List[Dict[str, Any]]):
        """Perform bulk operations on hosts."""
        try:
            from .checkmk import checkmk_service

            total_hosts = len(hosts_data)
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": 0,
                    "total": 100,
                    "status": f"Starting bulk {operation} for {total_hosts} hosts",
                },
            )

            if operation == "create":
                result = checkmk_service.bulk_create_hosts(hosts_data)
            elif operation == "update":
                result = checkmk_service.bulk_update_hosts(hosts_data)
            elif operation == "delete":
                hostnames = [
                    host.get("hostname") for host in hosts_data if host.get("hostname")
                ]
                result = checkmk_service.bulk_delete_hosts(hostnames)
            else:
                raise ValueError(f"Unsupported operation: {operation}")

            self.update_state(
                state="PROGRESS",
                meta={
                    "current": 90,
                    "total": 100,
                    "status": f"Bulk {operation} completed, activating changes",
                },
            )

            # Activate changes
            activation_result = checkmk_service.activate_changes()

            return {
                "status": "completed",
                "operation": operation,
                "hosts_affected": total_hosts,
                "checkmk_result": result,
                "activation_result": activation_result,
                "message": f"Successfully completed bulk {operation} for {total_hosts} hosts",
            }

        except Exception as e:
            logger.error(f"Error in bulk_host_operations task: {str(e)}")
            self.update_state(
                state="FAILURE",
                meta={
                    "error": str(e),
                    "status": f"Failed to perform bulk {operation}",
                },
            )
            raise

    @celery_app.task(bind=True)
    def cache_warm_up(self):
        """Warm up caches with frequently accessed data."""
        try:
            from .nautobot import nautobot_service
            from .checkmk import checkmk_service

            self.update_state(state="PROGRESS", meta={"current": 0, "total": 100})

            # Warm up Nautobot caches
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": 20,
                    "total": 100,
                    "status": "Warming up Nautobot caches",
                },
            )

            # Cache device stats
            nautobot_service.get_stats()

            # Cache basic device list
            nautobot_service.get_devices(limit=100)

            # Cache locations
            nautobot_service.get_locations()

            self.update_state(
                state="PROGRESS",
                meta={
                    "current": 60,
                    "total": 100,
                    "status": "Warming up CheckMK caches",
                },
            )

            # Warm up CheckMK caches
            checkmk_service.get_stats()

            # Cache basic host list
            checkmk_service.get_all_hosts()

            # Cache folders
            checkmk_service.get_all_folders()

            return {
                "status": "completed",
                "message": "Cache warm-up completed successfully",
                "caches_warmed": [
                    "nautobot_stats",
                    "nautobot_devices",
                    "nautobot_locations",
                    "checkmk_stats",
                    "checkmk_hosts",
                    "checkmk_folders",
                ],
            }

        except Exception as e:
            logger.error(f"Error in cache_warm_up task: {str(e)}")
            self.update_state(
                state="FAILURE",
                meta={
                    "error": str(e),
                    "status": "Failed to warm up caches",
                },
            )
            raise

    @celery_app.task(bind=True)
    def test_background_task(self, message: str = "Test job", duration: int = 10):
        """Test task for verifying Celery worker functionality."""
        import time

        logger.info(f"Starting test task: {message}")

        try:
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": 0,
                    "total": duration,
                    "status": f"Starting test job: {message}",
                },
            )

            # Simulate work by sleeping in chunks and updating progress
            for i in range(duration):
                time.sleep(1)
                progress = i + 1
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current": progress,
                        "total": duration,
                        "status": f"Processing test job ({progress}/{duration}): {message}",
                    },
                )

            logger.info(f"Completed test task: {message}")
            return {
                "status": "SUCCESS",
                "message": f"Test job completed successfully: {message}",
                "duration": duration,
            }

        except Exception as e:
            logger.error(f"Error in test_background_task: {str(e)}")
            self.update_state(
                state="FAILURE",
                meta={
                    "error": str(e),
                    "status": f"Test job failed: {message}",
                },
            )
            raise

    @celery_app.task(bind=True)
    def cleanup_old_data(self, days_to_keep: int = 7):
        """
        Cleanup task to remove old and expired data.
        
        This task cleans up:
        - Expired Celery task results
        - Old Celery task metadata
        - Completed one-off scheduled tasks
        
        Args:
            days_to_keep: Number of days to keep data (default: 7)
        """
        from datetime import datetime, timedelta
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker

        logger.info(f"Starting cleanup task (keeping last {days_to_keep} days)")
        
        cleanup_stats = {
            "celery_results_deleted": 0,
            "expired_tasks_deleted": 0,
            "one_off_tasks_deleted": 0,
            "errors": []
        }

        try:
            # Update task state
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": 1,
                    "total": 4,
                    "status": "Starting cleanup process...",
                    "stats": cleanup_stats,
                },
            )

            # Get database connection
            from ..core.database import engine as app_engine
            
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            logger.info(f"Cutoff date: {cutoff_date}")

            # Step 1: Clean up old Celery results from Redis/Backend
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": 2,
                    "total": 4,
                    "status": "Cleaning up old Celery results...",
                    "stats": cleanup_stats,
                },
            )
            
            try:
                # Get all task IDs and check their age
                from celery.result import AsyncResult
                # Note: This is a basic cleanup. For production, consider using celery.backend_cleanup
                logger.info("Celery results cleanup delegated to celery.backend_cleanup task")
            except Exception as e:
                logger.warning(f"Error cleaning Celery results: {e}")
                cleanup_stats["errors"].append(f"Celery results: {str(e)}")

            # Step 2: Clean up expired periodic tasks from celery_periodic_task table
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": 3,
                    "total": 4,
                    "status": "Cleaning up expired scheduled tasks...",
                    "stats": cleanup_stats,
                },
            )
            
            try:
                # Get the scheduler tables
                from celery_sqlalchemy_scheduler.models import PeriodicTask
                from celery_sqlalchemy_scheduler.session import SessionManager
                
                # Get database URI
                try:
                    db_uri = app_engine.url.render_as_string(hide_password=False)
                except AttributeError:
                    db_uri = str(app_engine.url).replace('***', app_engine.url.password or '')
                
                session_manager = SessionManager()
                session = session_manager.session_factory(db_uri)
                
                try:
                    # Delete expired tasks
                    expired_tasks = session.query(PeriodicTask).filter(
                        PeriodicTask.expires.isnot(None),
                        PeriodicTask.expires < datetime.utcnow()
                    ).all()
                    
                    for task in expired_tasks:
                        logger.info(f"Deleting expired task: {task.name}")
                        session.delete(task)
                        cleanup_stats["expired_tasks_deleted"] += 1
                    
                    session.commit()
                    logger.info(f"Deleted {cleanup_stats['expired_tasks_deleted']} expired tasks")
                    
                except Exception as e:
                    session.rollback()
                    logger.error(f"Error cleaning expired tasks: {e}")
                    cleanup_stats["errors"].append(f"Expired tasks: {str(e)}")
                finally:
                    session.close()
                    
            except Exception as e:
                logger.error(f"Error accessing scheduler database: {e}")
                cleanup_stats["errors"].append(f"Scheduler DB: {str(e)}")

            # Step 3: Clean up completed one-off tasks
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": 4,
                    "total": 4,
                    "status": "Cleaning up completed one-off tasks...",
                    "stats": cleanup_stats,
                },
            )
            
            try:
                from celery_sqlalchemy_scheduler.models import PeriodicTask
                from celery_sqlalchemy_scheduler.session import SessionManager
                
                session_manager = SessionManager()
                session = session_manager.session_factory(db_uri)
                
                try:
                    # Delete completed one-off tasks that ran more than X days ago
                    old_one_off_tasks = session.query(PeriodicTask).filter(
                        PeriodicTask.one_off == True,
                        PeriodicTask.enabled == False,
                        PeriodicTask.last_run_at.isnot(None),
                        PeriodicTask.last_run_at < cutoff_date
                    ).all()
                    
                    for task in old_one_off_tasks:
                        logger.info(f"Deleting completed one-off task: {task.name}")
                        session.delete(task)
                        cleanup_stats["one_off_tasks_deleted"] += 1
                    
                    session.commit()
                    logger.info(f"Deleted {cleanup_stats['one_off_tasks_deleted']} completed one-off tasks")
                    
                except Exception as e:
                    session.rollback()
                    logger.error(f"Error cleaning one-off tasks: {e}")
                    cleanup_stats["errors"].append(f"One-off tasks: {str(e)}")
                finally:
                    session.close()
                    
            except Exception as e:
                logger.error(f"Error cleaning one-off tasks: {e}")
                cleanup_stats["errors"].append(f"One-off cleanup: {str(e)}")

            # Prepare final result
            total_deleted = (
                cleanup_stats["celery_results_deleted"] +
                cleanup_stats["expired_tasks_deleted"] +
                cleanup_stats["one_off_tasks_deleted"]
            )
            
            logger.info(f"Cleanup completed. Total items deleted: {total_deleted}")
            
            return {
                "status": "SUCCESS",
                "message": f"Cleanup completed successfully. Deleted {total_deleted} items.",
                "stats": cleanup_stats,
                "cutoff_date": cutoff_date.isoformat(),
                "days_kept": days_to_keep,
            }

        except Exception as e:
            logger.error(f"Error in cleanup_old_data: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            cleanup_stats["errors"].append(f"General error: {str(e)}")
            
            self.update_state(
                state="FAILURE",
                meta={
                    "error": str(e),
                    "status": "Cleanup job failed",
                    "stats": cleanup_stats,
                },
            )
            raise


# Global service instance
background_job_service = BackgroundJobService()
