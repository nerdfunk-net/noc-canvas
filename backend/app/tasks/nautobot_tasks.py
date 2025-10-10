"""
Nautobot synchronization tasks.

This module contains Celery tasks for syncing data from Nautobot.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def register_tasks(celery_app):
    """Register Nautobot tasks with the Celery app."""

    @celery_app.task(bind=True, name="app.tasks.nautobot_tasks.sync_nautobot_devices")
    def sync_nautobot_devices(self, filters: Optional[Dict[str, Any]] = None):
        """
        Sync devices from Nautobot.

        Args:
            filters: Optional filters for device query
                - limit: Maximum number of devices to retrieve
                - offset: Offset for pagination
                - filter_type: Type of filter to apply
                - filter_value: Value for the filter

        Returns:
            Dictionary with sync results including device count and status
        """
        try:
            from ..services.nautobot import nautobot_service

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

            logger.info(f"Successfully synced {processed_count} devices from Nautobot")

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

    return {
        "sync_nautobot_devices": sync_nautobot_devices,
    }
