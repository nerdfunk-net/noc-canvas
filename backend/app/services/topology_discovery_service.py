"""
Topology discovery service for collecting device data.
Discovers topology by calling device endpoints and caching results.
"""

import logging
import asyncio
import uuid
import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from ..services.device_cache_service import device_cache_service
from ..schemas.device_cache import (
    StaticRouteCacheCreate, OSPFRouteCacheCreate, BGPRouteCacheCreate,
    MACAddressTableCacheCreate, CDPNeighborCacheCreate
)

logger = logging.getLogger(__name__)

# In-memory storage for job progress (will be replaced with Redis/Celery later)
_discovery_jobs: Dict[str, Dict[str, Any]] = {}


class TopologyDiscoveryService:
    """Service for discovering topology data from devices."""

    @staticmethod
    async def _call_device_endpoint(device_id: str, endpoint: str, auth_token: str) -> Dict[str, Any]:
        """
        Call a device API endpoint internally.

        Args:
            device_id: The device ID
            endpoint: The endpoint path (e.g., 'cdp-neighbors', 'ip-route/static')
            auth_token: Authentication token for internal API call

        Returns:
            API response as dict
        """
        base_url = "http://localhost:8000"  # Internal API call
        url = f"{base_url}/api/devices/{device_id}/{endpoint}?use_textfsm=true"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {auth_token}"},
                timeout=30.0
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API call failed: {response.status_code} - {response.text}")
                return {"success": False, "error": f"HTTP {response.status_code}"}

    @staticmethod
    def create_job(device_ids: List[str]) -> str:
        """Create a new discovery job and return job ID."""
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
                    "completed_at": None
                }
                for device_id in device_ids
            ],
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "error": None,
            "devices_data": {},
            "errors": {}
        }
        return job_id

    @staticmethod
    def get_job_progress(job_id: str) -> Optional[Dict[str, Any]]:
        """Get progress for a discovery job."""
        return _discovery_jobs.get(job_id)

    @staticmethod
    def update_job_status(job_id: str, status: str, error: Optional[str] = None):
        """Update overall job status."""
        if job_id in _discovery_jobs:
            _discovery_jobs[job_id]["status"] = status
            if error:
                _discovery_jobs[job_id]["error"] = error
            if status in ["completed", "failed"]:
                _discovery_jobs[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()

    @staticmethod
    def update_device_progress(
        job_id: str,
        device_id: str,
        status: str,
        progress: int,
        current_task: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Update progress for a specific device."""
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
            (job["completed_devices"] + job["failed_devices"]) / job["total_devices"] * 100
        )

    @staticmethod
    async def discover_device_data(
        device_id: str,
        job_id: str,
        include_static_routes: bool = True,
        include_ospf_routes: bool = True,
        include_bgp_routes: bool = True,
        include_mac_table: bool = True,
        include_cdp_neighbors: bool = True,
        cache_results: bool = True,
        auth_token: str = "",
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Discover all topology data for a single device.

        Returns:
            Dictionary with discovered data for each category
        """
        logger.info(f"🔍 Starting discovery for device {device_id}")

        TopologyDiscoveryService.update_device_progress(
            job_id, device_id, "in_progress", 0, "Initializing"
        )

        device_data = {
            "device_id": device_id,
            "static_routes": [],
            "ospf_routes": [],
            "bgp_routes": [],
            "mac_table": [],
            "cdp_neighbors": []
        }

        total_tasks = sum([
            include_static_routes,
            include_ospf_routes,
            include_bgp_routes,
            include_mac_table,
            include_cdp_neighbors
        ])
        completed_tasks = 0

        try:
            # Static Routes
            if include_static_routes:
                TopologyDiscoveryService.update_device_progress(
                    job_id, device_id, "in_progress",
                    int(completed_tasks / total_tasks * 100),
                    "Discovering static routes"
                )
                try:
                    logger.info(f"📍 Calling API endpoint for static routes on device {device_id}")
                    result = await TopologyDiscoveryService._call_device_endpoint(
                        device_id=device_id,
                        endpoint="ip-route/static",
                        auth_token=auth_token
                    )
                    logger.info(f"📍 Result: success={result.get('success')}, output type={type(result.get('output'))}")

                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["static_routes"] = result["output"]
                        logger.info(f"✅ Got {len(result['output'])} static routes")

                        # Cache if requested
                        if cache_results and db:
                            await TopologyDiscoveryService._cache_static_routes(
                                db, device_id, result["output"]
                            )
                    else:
                        logger.warning(f"⚠️ No static routes data: success={result.get('success')}, output={result.get('output')}")
                except Exception as e:
                    logger.error(f"❌ Failed to get static routes for {device_id}: {e}", exc_info=True)

                completed_tasks += 1

            # OSPF Routes
            if include_ospf_routes:
                TopologyDiscoveryService.update_device_progress(
                    job_id, device_id, "in_progress",
                    int(completed_tasks / total_tasks * 100),
                    "Discovering OSPF routes"
                )
                try:
                    result = await TopologyDiscoveryService._call_device_endpoint(
                        device_id=device_id,
                        endpoint="ip-route/ospf",
                        auth_token=auth_token
                    )
                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["ospf_routes"] = result["output"]

                        # Cache if requested
                        if cache_results and db:
                            await TopologyDiscoveryService._cache_ospf_routes(
                                db, device_id, result["output"]
                            )
                except Exception as e:
                    logger.error(f"Failed to get OSPF routes for {device_id}: {e}")

                completed_tasks += 1

            # BGP Routes
            if include_bgp_routes:
                TopologyDiscoveryService.update_device_progress(
                    job_id, device_id, "in_progress",
                    int(completed_tasks / total_tasks * 100),
                    "Discovering BGP routes"
                )
                try:
                    result = await TopologyDiscoveryService._call_device_endpoint(
                        device_id=device_id,
                        endpoint="ip-route/bgp",
                        auth_token=auth_token
                    )
                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["bgp_routes"] = result["output"]

                        # Cache if requested
                        if cache_results and db:
                            await TopologyDiscoveryService._cache_bgp_routes(
                                db, device_id, result["output"]
                            )
                except Exception as e:
                    logger.error(f"Failed to get BGP routes for {device_id}: {e}")

                completed_tasks += 1

            # MAC Address Table
            if include_mac_table:
                TopologyDiscoveryService.update_device_progress(
                    job_id, device_id, "in_progress",
                    int(completed_tasks / total_tasks * 100),
                    "Discovering MAC address table"
                )
                try:
                    result = await TopologyDiscoveryService._call_device_endpoint(
                        device_id=device_id,
                        endpoint="mac-address-table",
                        auth_token=auth_token
                    )
                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["mac_table"] = result["output"]

                        # Cache if requested
                        if cache_results and db:
                            await TopologyDiscoveryService._cache_mac_table(
                                db, device_id, result["output"]
                            )
                except Exception as e:
                    logger.error(f"Failed to get MAC table for {device_id}: {e}")

                completed_tasks += 1

            # CDP Neighbors
            if include_cdp_neighbors:
                TopologyDiscoveryService.update_device_progress(
                    job_id, device_id, "in_progress",
                    int(completed_tasks / total_tasks * 100),
                    "Discovering CDP neighbors"
                )
                try:
                    result = await TopologyDiscoveryService._call_device_endpoint(
                        device_id=device_id,
                        endpoint="cdp-neighbors",
                        auth_token=auth_token
                    )
                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["cdp_neighbors"] = result["output"]

                        # Cache if requested
                        if cache_results and db:
                            await TopologyDiscoveryService._cache_cdp_neighbors(
                                db, device_id, result["output"]
                            )
                except Exception as e:
                    logger.error(f"Failed to get CDP neighbors for {device_id}: {e}")

                completed_tasks += 1

            TopologyDiscoveryService.update_device_progress(
                job_id, device_id, "completed", 100, "Discovery completed"
            )

            logger.info(f"✅ Discovery completed for device {device_id}")
            return device_data

        except Exception as e:
            error_msg = f"Discovery failed: {str(e)}"
            logger.error(f"❌ Discovery failed for device {device_id}: {e}")
            TopologyDiscoveryService.update_device_progress(
                job_id, device_id, "failed", 0, None, error_msg
            )
            raise

    @staticmethod
    async def _cache_static_routes(db: Session, device_id: str, routes: List[Dict[str, Any]]):
        """Cache static routes to database."""
        # Implementation similar to existing cache endpoints
        pass

    @staticmethod
    async def _cache_ospf_routes(db: Session, device_id: str, routes: List[Dict[str, Any]]):
        """Cache OSPF routes to database."""
        pass

    @staticmethod
    async def _cache_bgp_routes(db: Session, device_id: str, routes: List[Dict[str, Any]]):
        """Cache BGP routes to database."""
        pass

    @staticmethod
    async def _cache_mac_table(db: Session, device_id: str, mac_entries: List[Dict[str, Any]]):
        """Cache MAC address table to database."""
        pass

    @staticmethod
    async def _cache_cdp_neighbors(db: Session, device_id: str, neighbors: List[Dict[str, Any]]):
        """Cache CDP neighbors to database."""
        pass

    @staticmethod
    async def discover_topology(
        device_ids: List[str],
        include_static_routes: bool = True,
        include_ospf_routes: bool = True,
        include_bgp_routes: bool = True,
        include_mac_table: bool = True,
        include_cdp_neighbors: bool = True,
        cache_results: bool = True,
        auth_token: str = "",
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Discover topology data for multiple devices.

        Args:
            device_ids: List of device IDs to discover
            include_*: Flags for what data to collect
            cache_results: Whether to cache results to database
            db: Database session for caching

        Returns:
            Dictionary with job_id and discovery results
        """
        job_id = TopologyDiscoveryService.create_job(device_ids)

        logger.info(f"🚀 Starting topology discovery for {len(device_ids)} devices (job: {job_id})")
        logger.info(f"   Device IDs: {device_ids}")
        logger.info(f"   Options: static={include_static_routes}, ospf={include_ospf_routes}, bgp={include_bgp_routes}, mac={include_mac_table}, cdp={include_cdp_neighbors}")

        TopologyDiscoveryService.update_job_status(job_id, "in_progress")

        start_time = datetime.now(timezone.utc)
        devices_data = {}
        errors = {}

        # Discover devices sequentially (parallel execution will be added with Celery)
        for device_id in device_ids:
            try:
                device_data = await TopologyDiscoveryService.discover_device_data(
                    device_id=device_id,
                    job_id=job_id,
                    include_static_routes=include_static_routes,
                    include_ospf_routes=include_ospf_routes,
                    include_bgp_routes=include_bgp_routes,
                    include_mac_table=include_mac_table,
                    include_cdp_neighbors=include_cdp_neighbors,
                    cache_results=cache_results,
                    auth_token=auth_token,
                    db=db
                )
                devices_data[device_id] = device_data
            except Exception as e:
                errors[device_id] = str(e)

        duration = (datetime.now(timezone.utc) - start_time).total_seconds()

        # Update job with results
        job = _discovery_jobs[job_id]
        job["devices_data"] = devices_data
        job["errors"] = errors
        job["duration_seconds"] = duration

        if errors and len(errors) == len(device_ids):
            TopologyDiscoveryService.update_job_status(job_id, "failed", "All devices failed")
        else:
            TopologyDiscoveryService.update_job_status(job_id, "completed")

        logger.info(f"✅ Topology discovery completed (job: {job_id})")
        logger.info(f"   Success: {len(devices_data)}, Failed: {len(errors)}, Duration: {duration:.2f}s")

        return {
            "job_id": job_id,
            "status": job["status"],
            "total_devices": len(device_ids),
            "successful_devices": len(devices_data),
            "failed_devices": len(errors),
            "devices_data": devices_data,
            "errors": errors,
            "duration_seconds": duration
        }
