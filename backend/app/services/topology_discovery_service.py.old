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

from ..core.config import settings
from ..services.device_cache_service import device_cache_service
from ..services.device_communication import DeviceCommunicationService
from ..services.nautobot import nautobot_service
from ..schemas.device_cache import (
    DeviceCacheCreate,
    StaticRouteCacheCreate, OSPFRouteCacheCreate, BGPRouteCacheCreate,
    MACAddressTableCacheCreate, CDPNeighborCacheCreate, ARPCacheCreate,
    InterfaceCacheCreate, IPAddressCacheCreate
)

logger = logging.getLogger(__name__)

# In-memory storage for job progress (will be replaced with Redis/Celery later)
_discovery_jobs: Dict[str, Dict[str, Any]] = {}


class TopologyDiscoveryService:
    """Service for discovering topology data from devices."""

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
        """Get the device command for an endpoint."""
        return TopologyDiscoveryService.ENDPOINT_COMMANDS.get(endpoint, f"show {endpoint}")

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
        base_url = settings.internal_api_url
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
    def _get_username_from_token(auth_token: str) -> str:
        """Extract username from JWT token."""
        try:
            from jose import jwt
            from ..core.config import settings

            payload = jwt.decode(auth_token, settings.secret_key, algorithms=[settings.algorithm])
            return payload.get("sub", "admin")  # Default to 'admin' if not found
        except Exception as e:
            logger.warning(f"Could not decode token: {e}, using default username 'admin'")
            return "admin"

    @staticmethod
    def _call_device_endpoint_sync(device_id: str, endpoint: str, auth_token: str) -> Dict[str, Any]:
        """
        Direct device command execution for Celery workers (no HTTP calls).

        Args:
            device_id: The device ID
            endpoint: The endpoint path (e.g., 'cdp-neighbors', 'ip-route/static')
            auth_token: Authentication token (used to extract username)

        Returns:
            Command execution result as dict
        """
        try:
            # Extract username from token
            username = TopologyDiscoveryService._get_username_from_token(auth_token)

            # Get the command for this endpoint
            command = TopologyDiscoveryService._get_device_command(endpoint)

            # Define async function to get device info and execute command
            async def execute_device_command():
                # Get device info from Nautobot (returns raw GraphQL structure)
                device_data = await nautobot_service.get_device(device_id, username)
                if not device_data:
                    logger.error(f"Device {device_id} not found in Nautobot")
                    return {"success": False, "error": "Device not found"}

                # Transform device data to match expected structure
                # The GraphQL response has nested structure, but DeviceCommunicationService
                # expects a flat structure with network_driver at top level
                primary_ip4 = device_data.get("primary_ip4")
                if not primary_ip4 or not primary_ip4.get("address"):
                    logger.error(f"Device {device_id} does not have a primary IPv4 address")
                    return {"success": False, "error": "Device does not have a primary IPv4 address"}

                platform_info = device_data.get("platform")
                if not platform_info or not platform_info.get("network_driver"):
                    logger.error(f"Device {device_id} does not have a platform/network_driver configured")
                    return {"success": False, "error": "Device platform or network_driver not configured"}

                # Create transformed device info with flattened structure
                device_info = {
                    "device_id": device_id,
                    "name": device_data.get("name", ""),
                    "primary_ip": primary_ip4["address"].split("/")[0],  # Remove subnet mask
                    "platform": platform_info.get("name", ""),
                    "network_driver": platform_info["network_driver"]
                }

                # Execute command directly using DeviceCommunicationService
                device_service = DeviceCommunicationService()
                result = await device_service.execute_command(
                    device_info=device_info,
                    command=command,
                    username=username,
                    parser="TEXTFSM"
                )
                return result

            # Use asyncio.run for sync context (Celery worker)
            result = asyncio.run(execute_device_command())
            return result

        except Exception as e:
            logger.error(f"Direct device call failed for {device_id}/{endpoint}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

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
        include_arp: bool = True,
        include_interfaces: bool = True,
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
            "cdp_neighbors": [],
            "arp_entries": [],
            "interfaces": []
        }

        total_tasks = sum([
            include_static_routes,
            include_ospf_routes,
            include_bgp_routes,
            include_mac_table,
            include_cdp_neighbors,
            include_arp,
            include_interfaces
        ])
        completed_tasks = 0

        try:
            # Interfaces
            if include_interfaces:
                TopologyDiscoveryService.update_device_progress(
                    job_id, device_id, "in_progress",
                    int(completed_tasks / total_tasks * 100),
                    "Discovering interfaces"
                )
                try:
                    logger.info(f"📍 Calling API endpoint for interfaces on device {device_id}")
                    result = await TopologyDiscoveryService._call_device_endpoint(
                        device_id=device_id,
                        endpoint="interfaces",
                        auth_token=auth_token
                    )
                    logger.info(f"📍 Interfaces Result: success={result.get('success')}, output type={type(result.get('output'))}")

                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["interfaces"] = result["output"]
                        logger.info(f"✅ Got {len(result['output'])} interfaces")

                        # Cache if requested
                        if cache_results and db:
                            await TopologyDiscoveryService._cache_interfaces(
                                db, device_id, result["output"]
                            )
                    else:
                        logger.warning(f"⚠️ No interfaces data: success={result.get('success')}, output={result.get('output')}")
                except Exception as e:
                    logger.error(f"❌ Failed to get interfaces for {device_id}: {e}", exc_info=True)

                completed_tasks += 1

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

            # ARP Entries
            if include_arp:
                TopologyDiscoveryService.update_device_progress(
                    job_id, device_id, "in_progress",
                    int(completed_tasks / total_tasks * 100),
                    "Discovering ARP entries"
                )
                try:
                    logger.info(f"📍 Calling API endpoint for ARP entries on device {device_id}")
                    result = await TopologyDiscoveryService._call_device_endpoint(
                        device_id=device_id,
                        endpoint="ip-arp",
                        auth_token=auth_token
                    )
                    logger.info(f"📍 ARP Result: success={result.get('success')}, output type={type(result.get('output'))}")

                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["arp_entries"] = result["output"]
                        logger.info(f"✅ Got {len(result['output'])} ARP entries")

                        # Cache if requested
                        if cache_results and db:
                            await TopologyDiscoveryService._cache_arp_entries(
                                db, device_id, result["output"]
                            )
                    else:
                        logger.warning(f"⚠️ No ARP data: success={result.get('success')}, output={result.get('output')}")
                except Exception as e:
                    logger.error(f"❌ Failed to get ARP entries for {device_id}: {e}", exc_info=True)

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
    def discover_device_data_sync(
        db: Session,
        device_id: str,
        task: Any,
        include_static_routes: bool = True,
        include_ospf_routes: bool = True,
        include_bgp_routes: bool = True,
        include_mac_table: bool = True,
        include_cdp_neighbors: bool = True,
        include_arp: bool = True,
        include_interfaces: bool = True,
        cache_results: bool = True,
        auth_token: str = ""
    ) -> Dict[str, Any]:
        """
        Synchronous version of discover_device_data for Celery workers.
        
        This method is called from discover_single_device_task and runs
        in the Celery worker context. It uses synchronous HTTP calls
        and updates task progress via Celery state.

        Args:
            db: Database session
            device_id: Device ID to discover
            task: Celery task instance for progress updates
            include_*: Flags for what data to collect
            cache_results: Whether to cache results to database
            auth_token: Authentication token for API calls

        Returns:
            Dictionary with discovered data for each category
        """
        logger.info(f"🔍 Starting sync discovery for device {device_id}")

        device_data = {
            "device_id": device_id,
            "static_routes": [],
            "ospf_routes": [],
            "bgp_routes": [],
            "mac_table": [],
            "cdp_neighbors": [],
            "arp_entries": [],
            "interfaces": []
        }

        total_tasks = sum([
            include_static_routes,
            include_ospf_routes,
            include_bgp_routes,
            include_mac_table,
            include_cdp_neighbors,
            include_arp,
            include_interfaces
        ])
        completed_tasks = 0

        try:
            # Ensure device cache entry exists before caching any data
            # This is required because all cache tables have foreign key constraints
            # that reference the device_cache table
            if cache_results:
                try:
                    # Extract username from token to get device info
                    username = TopologyDiscoveryService._get_username_from_token(auth_token)
                    
                    # Get device info from Nautobot to populate device cache
                    async def get_device_info():
                        return await nautobot_service.get_device(device_id, username)
                    
                    device_info = asyncio.run(get_device_info())
                    
                    if device_info:
                        # Extract primary IP
                        primary_ip4 = device_info.get("primary_ip4")
                        primary_ip = primary_ip4["address"].split("/")[0] if primary_ip4 and primary_ip4.get("address") else None
                        
                        # Extract platform
                        platform_info = device_info.get("platform")
                        platform = platform_info.get("name") if platform_info else None
                        
                        # Create or update device cache entry
                        device_cache_data = DeviceCacheCreate(
                            device_id=device_id,
                            device_name=device_info.get("name", ""),
                            primary_ip=primary_ip,
                            platform=platform
                        )
                        device_cache_service.get_or_create_device_cache(db, device_cache_data)
                        logger.info(f"✅ Device cache entry ensured for {device_id}")
                    else:
                        logger.warning(f"⚠️ Could not get device info from Nautobot for {device_id}")
                except Exception as e:
                    logger.error(f"❌ Failed to create device cache entry for {device_id}: {e}")
                    # Continue anyway - caching will fail but data will still be returned

            # Static Routes
            if include_static_routes:
                task.update_state(
                    state='PROGRESS',
                    meta={
                        'progress': int(completed_tasks / total_tasks * 100),
                        'current_task': 'Discovering static routes'
                    }
                )
                try:
                    logger.info(f"📍 Calling API endpoint for static routes on device {device_id}")
                    result = TopologyDiscoveryService._call_device_endpoint_sync(
                        device_id=device_id,
                        endpoint="ip-route/static",
                        auth_token=auth_token
                    )
                    logger.info(f"📍 Result: success={result.get('success')}, output type={type(result.get('output'))}")

                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["static_routes"] = result["output"]
                        logger.info(f"✅ Got {len(result['output'])} static routes")

                        # Cache if requested
                        if cache_results:
                            TopologyDiscoveryService._cache_static_routes_sync(
                                db, device_id, result["output"]
                            )
                    else:
                        logger.warning(f"⚠️ No static routes data: success={result.get('success')}, output={result.get('output')}")
                except Exception as e:
                    logger.error(f"❌ Failed to get static routes for {device_id}: {e}", exc_info=True)

                completed_tasks += 1

            # OSPF Routes
            if include_ospf_routes:
                task.update_state(
                    state='PROGRESS',
                    meta={
                        'progress': int(completed_tasks / total_tasks * 100),
                        'current_task': 'Discovering OSPF routes'
                    }
                )
                try:
                    result = TopologyDiscoveryService._call_device_endpoint_sync(
                        device_id=device_id,
                        endpoint="ip-route/ospf",
                        auth_token=auth_token
                    )
                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["ospf_routes"] = result["output"]

                        # Cache if requested
                        if cache_results:
                            TopologyDiscoveryService._cache_ospf_routes_sync(
                                db, device_id, result["output"]
                            )
                except Exception as e:
                    logger.error(f"Failed to get OSPF routes for {device_id}: {e}")

                completed_tasks += 1

            # BGP Routes
            if include_bgp_routes:
                task.update_state(
                    state='PROGRESS',
                    meta={
                        'progress': int(completed_tasks / total_tasks * 100),
                        'current_task': 'Discovering BGP routes'
                    }
                )
                try:
                    result = TopologyDiscoveryService._call_device_endpoint_sync(
                        device_id=device_id,
                        endpoint="ip-route/bgp",
                        auth_token=auth_token
                    )
                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["bgp_routes"] = result["output"]

                        # Cache if requested
                        if cache_results:
                            TopologyDiscoveryService._cache_bgp_routes_sync(
                                db, device_id, result["output"]
                            )
                except Exception as e:
                    logger.error(f"Failed to get BGP routes for {device_id}: {e}")

                completed_tasks += 1

            # MAC Address Table
            if include_mac_table:
                task.update_state(
                    state='PROGRESS',
                    meta={
                        'progress': int(completed_tasks / total_tasks * 100),
                        'current_task': 'Discovering MAC address table'
                    }
                )
                try:
                    result = TopologyDiscoveryService._call_device_endpoint_sync(
                        device_id=device_id,
                        endpoint="mac-address-table",
                        auth_token=auth_token
                    )
                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["mac_table"] = result["output"]

                        # Cache if requested
                        if cache_results:
                            TopologyDiscoveryService._cache_mac_table_sync(
                                db, device_id, result["output"]
                            )
                except Exception as e:
                    logger.error(f"Failed to get MAC table for {device_id}: {e}")

                completed_tasks += 1

            # CDP Neighbors
            if include_cdp_neighbors:
                task.update_state(
                    state='PROGRESS',
                    meta={
                        'progress': int(completed_tasks / total_tasks * 100),
                        'current_task': 'Discovering CDP neighbors'
                    }
                )
                try:
                    result = TopologyDiscoveryService._call_device_endpoint_sync(
                        device_id=device_id,
                        endpoint="cdp-neighbors",
                        auth_token=auth_token
                    )
                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["cdp_neighbors"] = result["output"]

                        # Cache if requested
                        if cache_results:
                            TopologyDiscoveryService._cache_cdp_neighbors_sync(
                                db, device_id, result["output"]
                            )
                except Exception as e:
                    logger.error(f"Failed to get CDP neighbors for {device_id}: {e}")

                completed_tasks += 1

            # ARP Entries
            if include_arp:
                task.update_state(
                    state='PROGRESS',
                    meta={
                        'progress': int(completed_tasks / total_tasks * 100),
                        'current_task': 'Discovering ARP entries'
                    }
                )
                try:
                    logger.info(f"📍 Calling API endpoint for ARP entries on device {device_id}")
                    result = TopologyDiscoveryService._call_device_endpoint_sync(
                        device_id=device_id,
                        endpoint="ip-arp",
                        auth_token=auth_token
                    )
                    logger.info(f"📍 ARP Result: success={result.get('success')}, output type={type(result.get('output'))}")

                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["arp_entries"] = result["output"]
                        logger.info(f"✅ Got {len(result['output'])} ARP entries")

                        # Cache if requested
                        if cache_results:
                            TopologyDiscoveryService._cache_arp_entries_sync(
                                db, device_id, result["output"]
                            )
                    else:
                        logger.warning(f"⚠️ No ARP data: success={result.get('success')}, output={result.get('output')}")
                except Exception as e:
                    logger.error(f"❌ Failed to get ARP entries for {device_id}: {e}", exc_info=True)

                completed_tasks += 1

            # Interfaces
            if include_interfaces:
                task.update_state(
                    state='PROGRESS',
                    meta={
                        'progress': int(completed_tasks / total_tasks * 100),
                        'current_task': 'Discovering interfaces'
                    }
                )
                try:
                    logger.info(f"📍 Calling API endpoint for interfaces on device {device_id}")
                    result = TopologyDiscoveryService._call_device_endpoint_sync(
                        device_id=device_id,
                        endpoint="interfaces",
                        auth_token=auth_token
                    )
                    logger.info(f"📍 Interfaces Result: success={result.get('success')}, output type={type(result.get('output'))}")

                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["interfaces"] = result["output"]
                        logger.info(f"✅ Got {len(result['output'])} interfaces")

                        # Cache if requested
                        if cache_results:
                            TopologyDiscoveryService._cache_interfaces_sync(
                                db, device_id, result["output"]
                            )
                    else:
                        logger.warning(f"⚠️ No interfaces data: success={result.get('success')}, output={result.get('output')}")
                except Exception as e:
                    logger.error(f"❌ Failed to get interfaces for {device_id}: {e}", exc_info=True)

                completed_tasks += 1

            task.update_state(
                state='PROGRESS',
                meta={
                    'progress': 100,
                    'current_task': 'Discovery completed'
                }
            )

            logger.info(f"✅ Sync discovery completed for device {device_id}")
            return device_data

        except Exception as e:
            error_msg = f"Discovery failed: {str(e)}"
            logger.error(f"❌ Sync discovery failed for device {device_id}: {e}", exc_info=True)
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
    async def _cache_arp_entries(db: Session, device_id: str, arp_entries: List[Dict[str, Any]]):
        """Cache ARP entries to database."""
        pass

    @staticmethod
    async def _cache_interfaces(db: Session, device_id: str, interfaces: List[Dict[str, Any]]):
        """Cache interfaces to database."""
        pass

    # Synchronous cache methods for Celery workers
    @staticmethod
    def _cache_static_routes_sync(db: Session, device_id: str, routes: List[Dict[str, Any]]):
        """Synchronous cache method for static routes."""
        try:
            cache_entries = []
            for route in routes:
                cache_entry = StaticRouteCacheCreate(
                    device_id=device_id,
                    network=route.get("network", ""),
                    nexthop_ip=route.get("nexthop_ip"),
                    interface_name=route.get("nexthop_if"),
                    distance=route.get("distance"),
                    metric=route.get("metric")
                )
                cache_entries.append(cache_entry)
            
            # Use bulk replace method
            if cache_entries:
                device_cache_service.bulk_replace_static_routes(db, device_id, cache_entries)
                logger.debug(f"Cached {len(routes)} static routes for device {device_id}")
        except Exception as e:
            logger.error(f"Failed to cache static routes for {device_id}: {e}")
            # Rollback the session to recover from the error
            db.rollback()

    @staticmethod
    def _cache_ospf_routes_sync(db: Session, device_id: str, routes: List[Dict[str, Any]]):
        """Synchronous cache method for OSPF routes."""
        try:
            cache_entries = []
            for route in routes:
                cache_entry = OSPFRouteCacheCreate(
                    device_id=device_id,
                    network=route.get("network", ""),
                    nexthop_ip=route.get("nexthop_ip"),
                    interface_name=route.get("nexthop_if"),
                    distance=route.get("distance"),
                    metric=route.get("metric"),
                    area=route.get("area"),
                    route_type=route.get("route_type")
                )
                cache_entries.append(cache_entry)
            
            # Use bulk replace method
            if cache_entries:
                device_cache_service.bulk_replace_ospf_routes(db, device_id, cache_entries)
                logger.debug(f"Cached {len(routes)} OSPF routes for device {device_id}")
        except Exception as e:
            logger.error(f"Failed to cache OSPF routes for {device_id}: {e}")
            db.rollback()

    @staticmethod
    def _cache_bgp_routes_sync(db: Session, device_id: str, routes: List[Dict[str, Any]]):
        """Synchronous cache method for BGP routes."""
        try:
            cache_entries = []
            for route in routes:
                cache_entry = BGPRouteCacheCreate(
                    device_id=device_id,
                    network=route.get("network", ""),
                    nexthop_ip=route.get("nexthop_ip"),
                    as_path=route.get("as_path"),
                    local_pref=route.get("local_pref"),
                    metric=route.get("metric"),
                    weight=route.get("weight")
                )
                cache_entries.append(cache_entry)
            
            # Use bulk replace method
            if cache_entries:
                device_cache_service.bulk_replace_bgp_routes(db, device_id, cache_entries)
                logger.debug(f"Cached {len(routes)} BGP routes for device {device_id}")
        except Exception as e:
            logger.error(f"Failed to cache BGP routes for {device_id}: {e}")
            db.rollback()

    @staticmethod
    def _cache_mac_table_sync(db: Session, device_id: str, mac_entries: List[Dict[str, Any]]):
        """Synchronous cache method for MAC address table."""
        try:
            cache_entries = []
            for entry in mac_entries:
                cache_entry = MACAddressTableCacheCreate(
                    device_id=device_id,
                    vlan=entry.get("vlan", ""),
                    mac_address=entry.get("destination_address", ""),
                    interface=entry.get("destination_port", ""),
                    type=entry.get("type", "")
                )
                cache_entries.append(cache_entry)
            
            # Use bulk replace method
            if cache_entries:
                device_cache_service.bulk_replace_mac_table(db, device_id, cache_entries)
                logger.debug(f"Cached {len(mac_entries)} MAC entries for device {device_id}")
        except Exception as e:
            logger.error(f"Failed to cache MAC table for {device_id}: {e}")
            db.rollback()

    @staticmethod
    def _cache_cdp_neighbors_sync(db: Session, device_id: str, neighbors: List[Dict[str, Any]]):
        """Synchronous cache method for CDP neighbors."""
        try:
            cache_entries = []
            for neighbor in neighbors:
                # Extract fields with case-insensitive fallback (TextFSM may return uppercase)
                neighbor_name_raw = (
                    neighbor.get("NEIGHBOR") or neighbor.get("neighbor") or
                    neighbor.get("NEIGHBOR_NAME") or neighbor.get("neighbor_name") or
                    neighbor.get("DESTINATION_HOST") or neighbor.get("destination_host") or ""
                )
                local_interface_raw = (
                    neighbor.get("LOCAL_INTERFACE") or neighbor.get("local_interface") or
                    neighbor.get("LOCAL_PORT") or neighbor.get("local_port") or ""
                )
                neighbor_ip_raw = (
                    neighbor.get("MANAGEMENT_IP") or neighbor.get("management_ip") or
                    neighbor.get("NEIGHBOR_IP") or neighbor.get("neighbor_ip") or ""
                )
                neighbor_interface_raw = (
                    neighbor.get("NEIGHBOR_INTERFACE") or neighbor.get("neighbor_interface") or
                    neighbor.get("NEIGHBOR_PORT") or neighbor.get("neighbor_port") or ""
                )
                platform_raw = neighbor.get("PLATFORM") or neighbor.get("platform") or ""
                capabilities_raw = neighbor.get("CAPABILITIES") or neighbor.get("capabilities") or ""
                
                # Handle if fields are lists (some TextFSM templates return lists)
                if isinstance(neighbor_name_raw, list):
                    neighbor_name = neighbor_name_raw[0] if neighbor_name_raw else ""
                else:
                    neighbor_name = neighbor_name_raw
                neighbor_name = neighbor_name.strip() if neighbor_name else ""
                
                if isinstance(local_interface_raw, list):
                    local_interface = local_interface_raw[0] if local_interface_raw else ""
                else:
                    local_interface = local_interface_raw
                local_interface = local_interface.strip() if local_interface else ""
                
                # Skip entries without neighbor name or local interface
                if not neighbor_name or not local_interface:
                    logger.warning(f"Skipping CDP neighbor with missing name or interface: {neighbor}")
                    continue
                
                # Handle other fields
                if isinstance(neighbor_ip_raw, list):
                    neighbor_ip = neighbor_ip_raw[0] if neighbor_ip_raw else ""
                else:
                    neighbor_ip = neighbor_ip_raw
                neighbor_ip = neighbor_ip.strip() if neighbor_ip else ""
                
                if isinstance(neighbor_interface_raw, list):
                    neighbor_interface = neighbor_interface_raw[0] if neighbor_interface_raw else ""
                else:
                    neighbor_interface = neighbor_interface_raw
                neighbor_interface = neighbor_interface.strip() if neighbor_interface else ""
                
                if isinstance(platform_raw, list):
                    platform = platform_raw[0] if platform_raw else ""
                else:
                    platform = platform_raw
                platform = platform.strip() if platform else ""
                
                if isinstance(capabilities_raw, list):
                    capabilities = ", ".join(capabilities_raw) if capabilities_raw else ""
                else:
                    capabilities = capabilities_raw
                capabilities = capabilities.strip() if capabilities else ""
                
                cache_entry = CDPNeighborCacheCreate(
                    device_id=device_id,
                    local_interface=local_interface,
                    neighbor_name=neighbor_name,
                    neighbor_interface=neighbor_interface if neighbor_interface else None,
                    neighbor_ip=neighbor_ip if neighbor_ip else None,
                    platform=platform if platform else None,
                    capabilities=capabilities if capabilities else None
                )
                cache_entries.append(cache_entry)
            
            # Use bulk replace method
            if cache_entries:
                device_cache_service.bulk_replace_cdp_neighbors(db, device_id, cache_entries)
                logger.debug(f"Cached {len(cache_entries)} CDP neighbors for device {device_id}")
        except Exception as e:
            logger.error(f"Failed to cache CDP neighbors for {device_id}: {e}")
            db.rollback()

    @staticmethod
    def _cache_arp_entries_sync(db: Session, device_id: str, arp_entries: List[Dict[str, Any]]):
        """Synchronous cache method for ARP entries."""
        try:
            cache_entries = []
            for entry in arp_entries:
                # Handle case-insensitive field names
                protocol = entry.get("protocol") or entry.get("PROTOCOL") or "Internet"
                address = entry.get("address") or entry.get("ADDRESS") or ""
                age = entry.get("age") or entry.get("AGE") or ""
                mac = entry.get("mac") or entry.get("MAC") or ""
                interface = entry.get("interface") or entry.get("INTERFACE") or ""

                # Handle list values (some parsers return lists)
                if isinstance(protocol, list):
                    protocol = protocol[0] if protocol else "Internet"
                if isinstance(address, list):
                    address = address[0] if address else ""
                if isinstance(age, list):
                    age = age[0] if age else ""
                if isinstance(mac, list):
                    mac = mac[0] if mac else ""
                if isinstance(interface, list):
                    interface = interface[0] if interface else ""

                # Convert age to integer or None
                age_int = None
                if age and age.strip() and age.strip() != '-':
                    try:
                        age_int = int(age.strip())
                    except ValueError:
                        # If age can't be converted to int, leave it as None
                        pass

                cache_entry = ARPCacheCreate(
                    device_id=device_id,
                    ip_address=address.strip() if address else "",
                    mac_address=mac.strip() if mac else "",
                    interface_name=interface.strip() if interface else None,
                    arp_type=protocol.strip() if protocol else None,
                    age=age_int
                )
                cache_entries.append(cache_entry)

            # Use bulk replace method
            if cache_entries:
                device_cache_service.bulk_replace_arp(db, device_id, cache_entries)
                logger.debug(f"Cached {len(cache_entries)} ARP entries for device {device_id}")
        except Exception as e:
            logger.error(f"Failed to cache ARP entries for {device_id}: {e}")
            db.rollback()

    @staticmethod
    def _cache_interfaces_sync(db: Session, device_id: str, interfaces: List[Dict[str, Any]]):
        """Synchronous cache method for interfaces."""
        try:
            interface_entries = []
            ip_entries = []

            for iface in interfaces:
                # Determine status from link_status and protocol_status
                link_status = iface.get("link_status", "").lower()
                protocol_status = iface.get("protocol_status", "").lower()

                # Combine statuses (e.g., "up/up", "down/down", "up/down")
                status = None
                if link_status or protocol_status:
                    status = f"{link_status or 'unknown'}/{protocol_status or 'unknown'}"

                # Create interface entry
                interface_entry = InterfaceCacheCreate(
                    device_id=device_id,
                    interface_name=iface.get("name") or iface.get("interface", ""),
                    description=iface.get("description"),
                    mac_address=iface.get("mac_address") or iface.get("phys_address"),
                    status=status,
                    speed=iface.get("bandwidth"),
                    duplex=iface.get("duplex"),
                    vlan_id=None  # Parse from interface name if needed (e.g., Gi0/0.100)
                )
                interface_entries.append(interface_entry)

                # Create IP address entries if present
                ip_address = iface.get("ip_address")
                if ip_address and ip_address != "unassigned":
                    # Parse IP and subnet mask if in CIDR format (e.g., "10.0.0.1/24")
                    subnet_mask = None
                    if "/" in ip_address:
                        ip_addr, prefix = ip_address.split("/")
                        ip_address = ip_addr
                        subnet_mask = prefix  # Can be converted to dotted decimal if needed

                    ip_entry = IPAddressCacheCreate(
                        device_id=device_id,
                        interface_id=None,  # Will be set by bulk_replace
                        interface_name=iface.get("name") or iface.get("interface", ""),
                        ip_address=ip_address,
                        subnet_mask=subnet_mask,
                        ip_version=4 if "." in ip_address else 6,
                        is_primary=False
                    )
                    ip_entries.append(ip_entry)

            # Use upsert for interfaces (bulk methods don't exist yet)
            if interface_entries:
                for interface_entry in interface_entries:
                    device_cache_service.upsert_interface(db, interface_entry)
                logger.debug(f"Cached {len(interface_entries)} interfaces for device {device_id}")

            # Note: IP address caching would need upsert_ip_address method
            # Skipping IP address caching for now as bulk method doesn't exist
            if ip_entries:
                logger.debug(f"Skipping {len(ip_entries)} IP addresses (bulk method not implemented)")
        except Exception as e:
            logger.error(f"Failed to cache interfaces for {device_id}: {e}")
            db.rollback()

    @staticmethod
    async def discover_topology(
        device_ids: List[str],
        include_static_routes: bool = True,
        include_ospf_routes: bool = True,
        include_bgp_routes: bool = True,
        include_mac_table: bool = True,
        include_cdp_neighbors: bool = True,
        include_arp: bool = True,
        include_interfaces: bool = True,
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
        logger.info(f"   Options: static={include_static_routes}, ospf={include_ospf_routes}, bgp={include_bgp_routes}, mac={include_mac_table}, cdp={include_cdp_neighbors}, arp={include_arp}, interfaces={include_interfaces}")

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
                    include_arp=include_arp,
                    include_interfaces=include_interfaces,
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
