"""
Cache warming tasks.

This module contains Celery tasks for warming up application caches.
"""

import logging

logger = logging.getLogger(__name__)


def register_tasks(celery_app):
    """Register cache tasks with the Celery app."""

    @celery_app.task(bind=True, name="app.tasks.cache_tasks.cache_warm_up")
    def cache_warm_up(self):
        """
        Warm up caches with frequently accessed data.

        This task pre-loads commonly accessed data into the cache to improve
        application performance. It caches:
        - Nautobot device stats, device list, and locations
        - CheckMK host stats, host list, and folders

        Returns:
            Dictionary with cache warm-up results
        """
        try:
            from ..services.nautobot import nautobot_service
            from ..services.checkmk import checkmk_service

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

            logger.info("Cache warm-up completed successfully")

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

    return {
        "cache_warm_up": cache_warm_up,
    }
