"""
Background job service for long-running tasks.
"""

import logging
from typing import Dict, Any, Optional, List
from ..core.config import settings

logger = logging.getLogger(__name__)

try:
    from celery import Celery

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
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 minutes
        task_soft_time_limit=25 * 60,  # 25 minutes
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        result_extended=True,  # Store task name and other metadata in results
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


# Global service instance
background_job_service = BackgroundJobService()
