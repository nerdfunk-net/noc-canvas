"""
Base topology discovery functionality shared by async and sync implementations.

This module contains:
- Command mappings for network devices
- Job management (creation, progress tracking, status updates)
- Utility functions (JWT token parsing, command lookup)
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# In-memory storage for job progress (will be replaced with Redis/Celery later)
_discovery_jobs: Dict[str, Dict[str, Any]] = {}


class TopologyDiscoveryBase:
    """Base class with shared topology discovery functionality."""

    # Command mapping for different endpoints
    ENDPOINT_COMMANDS = {
        "interfaces": "show interfaces",
        "ip-arp": "show ip arp",
        "cdp-neighbors": "show cdp neighbors",
        "mac-address-table": "show mac address-table",
        "ip-route/static": "show ip route static",
        "ip-route/ospf": "show ip route ospf",
        "ip-route/bgp": "show ip route bgp",
    }

    @staticmethod
    def _get_device_command(endpoint: str) -> str:
        """
        Get the device command for an endpoint.

        Args:
            endpoint: The endpoint path (e.g., 'cdp-neighbors', 'ip-route/static')

        Returns:
            The CLI command to execute on the device
        """
        return TopologyDiscoveryBase.ENDPOINT_COMMANDS.get(
            endpoint, f"show {endpoint}"
        )

    @staticmethod
    def _get_username_from_token(auth_token: str) -> str:
        """
        Extract username from JWT token.

        Args:
            auth_token: JWT authentication token

        Returns:
            Username extracted from token, or 'admin' as fallback
        """
        try:
            from jose import jwt

            from ...core.config import settings

            payload = jwt.decode(
                auth_token, settings.secret_key, algorithms=[settings.algorithm]
            )
            return payload.get("sub", "admin")  # Default to 'admin' if not found
        except Exception as e:
            logger.warning(
                f"Could not decode token: {e}, using default username 'admin'"
            )
            return "admin"

    @staticmethod
    def create_job(device_ids: List[str]) -> str:
        """
        Create a new discovery job and return job ID.

        Args:
            device_ids: List of device IDs to discover

        Returns:
            Generated job ID (UUID)
        """
        job_id = str(uuid.uuid4())
        _discovery_jobs[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "total_devices": len(device_ids),
            "completed_devices": 0,
            "failed_devices": 0,
            "progress_percentage": 0,
            "devices": [
                {
                    "device_id": device_id,
                    "device_name": device_id,  # Will be updated when discovered
                    "status": "pending",
                    "progress_percentage": 0,
                    "current_task": None,
                    "error": None,
                    "started_at": None,
                    "completed_at": None,
                }
                for device_id in device_ids
            ],
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "error": None,
            "devices_data": {},
            "errors": {},
        }
        return job_id

    @staticmethod
    def get_job_progress(job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get progress for a discovery job.

        Args:
            job_id: Job ID to query

        Returns:
            Job progress dictionary or None if not found
        """
        return _discovery_jobs.get(job_id)

    @staticmethod
    def update_job_status(
        job_id: str, status: str, error: Optional[str] = None
    ) -> None:
        """
        Update overall job status.

        Args:
            job_id: Job ID to update
            status: New status ('pending', 'in_progress', 'completed', 'failed')
            error: Optional error message if status is 'failed'
        """
        if job_id in _discovery_jobs:
            _discovery_jobs[job_id]["status"] = status
            if error:
                _discovery_jobs[job_id]["error"] = error
            if status in ["completed", "failed"]:
                _discovery_jobs[job_id]["completed_at"] = datetime.now(
                    timezone.utc
                ).isoformat()

    @staticmethod
    def update_device_progress(
        job_id: str,
        device_id: str,
        status: str,
        progress: int,
        current_task: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Update progress for a specific device within a job.

        Args:
            job_id: Job ID containing the device
            device_id: Device ID to update
            status: Device status ('pending', 'in_progress', 'completed', 'failed')
            progress: Progress percentage (0-100)
            current_task: Optional description of current task
            error: Optional error message if device failed
        """
        if job_id not in _discovery_jobs:
            return

        job = _discovery_jobs[job_id]

        # Find and update device progress
        for device in job["devices"]:
            if device["device_id"] == device_id:
                device["status"] = status
                device["progress_percentage"] = progress
                device["current_task"] = current_task
                device["error"] = error

                if status == "in_progress" and not device["started_at"]:
                    device["started_at"] = datetime.now(timezone.utc).isoformat()
                elif status in ["completed", "failed"]:
                    device["completed_at"] = datetime.now(timezone.utc).isoformat()

                    if status == "completed":
                        job["completed_devices"] += 1
                    elif status == "failed":
                        job["failed_devices"] += 1

                break

        # Update overall progress
        job["progress_percentage"] = int(
            (job["completed_devices"] + job["failed_devices"])
            / job["total_devices"]
            * 100
        )
