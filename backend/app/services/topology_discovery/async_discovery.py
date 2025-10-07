"""
Async topology discovery for API requests (foreground execution).

This module handles topology discovery when called from API endpoints.
It uses HTTP calls to internal API endpoints for device communication.

Execution Path:
    API Request → AsyncTopologyDiscoveryService → HTTP calls → Device API
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

from ...core.config import settings
from ...schemas.device_cache import (
    ARPCacheCreate,
    BGPRouteCacheCreate,
    CDPNeighborCacheCreate,
    InterfaceCacheCreate,
    IPAddressCacheCreate,
    MACAddressTableCacheCreate,
    OSPFRouteCacheCreate,
    StaticRouteCacheCreate,
)
from ...services.device_cache_service import device_cache_service
from .base import TopologyDiscoveryBase

logger = logging.getLogger(__name__)


class AsyncTopologyDiscoveryService(TopologyDiscoveryBase):
    """Async topology discovery service for API/foreground execution."""

    @staticmethod
    async def _call_device_endpoint(
        device_id: str, endpoint: str, auth_token: str
    ) -> Dict[str, Any]:
        """
        Call a device API endpoint internally via HTTP.

        This method is used in the async/API path to make internal HTTP calls
        to device endpoints. It reuses the existing device API infrastructure.
        
        Before making the HTTP call, checks the JSON blob cache for existing data.
        If valid cached data exists, returns it immediately without making the API call.

        Args:
            device_id: The device ID
            endpoint: The endpoint path (e.g., 'cdp-neighbors', 'ip-route/static')
            auth_token: Authentication token for internal API call

        Returns:
            API response as dict with 'success' and 'output' keys
        """
        # Check JSON blob cache first
        try:
            import json
            from ...core.database import SessionLocal
            from ...services.json_cache_service import JSONCacheService
            
            # Get the command for this endpoint
            command = AsyncTopologyDiscoveryService._get_device_command(endpoint)
            
            db = SessionLocal()
            try:
                valid_cache = JSONCacheService.get_valid_cache(
                    db=db,
                    device_id=device_id,
                    command=command
                )
                
                if valid_cache:
                    # Use cached data
                    cached_output = json.loads(valid_cache.json_data)
                    logger.info(f"✅ Using cached data for device {device_id}, command '{command}' (endpoint: {endpoint}) in async discovery")
                    return {
                        "success": True,
                        "output": cached_output,
                        "parsed": True,
                        "parser_used": "TEXTFSM (from cache)",
                        "execution_time": 0.0,
                        "cached": True
                    }
            finally:
                db.close()
        except Exception as cache_error:
            logger.warning(f"Failed to check cache for device {device_id}, endpoint '{endpoint}', will call API: {str(cache_error)}")
        
        # No cache or cache check failed, proceed with HTTP call
        base_url = settings.internal_api_url
        url = f"{base_url}/api/devices/{device_id}/{endpoint}?use_textfsm=true"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, headers={"Authorization": f"Bearer {auth_token}"}, timeout=30.0
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"API call failed: {response.status_code} - {response.text}"
                )
                return {"success": False, "error": f"HTTP {response.status_code}"}

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
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Discover all topology data for a single device (async version).

        This method is called from API requests and uses HTTP calls to
        internal device endpoints.

        Args:
            device_id: Device ID to discover
            job_id: Job ID for progress tracking
            include_*: Flags for what data to collect
            cache_results: Whether to cache results to database
            auth_token: Authentication token for internal API calls
            db: Database session for caching

        Returns:
            Dictionary with discovered data for each category
        """
        logger.info(f"🔍 Starting async discovery for device {device_id}")

        AsyncTopologyDiscoveryService.update_device_progress(
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
            "interfaces": [],
        }

        total_tasks = sum(
            [
                include_static_routes,
                include_ospf_routes,
                include_bgp_routes,
                include_mac_table,
                include_cdp_neighbors,
                include_arp,
                include_interfaces,
            ]
        )
        completed_tasks = 0

        try:
            # Ensure device cache entry exists before caching any data
            # This is required because all cache tables have foreign key constraints
            if cache_results and db:
                try:
                    from ...services.nautobot import nautobot_service
                    from ...schemas.device_cache import DeviceCacheCreate
                    
                    # Extract username from token
                    username = AsyncTopologyDiscoveryService._get_username_from_token(
                        auth_token
                    )

                    # Get device info from Nautobot to populate device cache
                    device_info = await nautobot_service.get_device(device_id, username)

                    if device_info:
                        # Extract primary IP
                        primary_ip4 = device_info.get("primary_ip4")
                        primary_ip = (
                            primary_ip4["address"].split("/")[0]
                            if primary_ip4 and primary_ip4.get("address")
                            else None
                        )

                        # Extract platform
                        platform_info = device_info.get("platform")
                        platform = (
                            platform_info.get("name") if platform_info else None
                        )

                        # Create or update device cache entry
                        device_cache_data = DeviceCacheCreate(
                            device_id=device_id,
                            device_name=device_info.get("name", ""),
                            primary_ip=primary_ip,
                            platform=platform,
                        )
                        device_cache_service.get_or_create_device_cache(
                            db, device_cache_data
                        )
                        logger.info(f"✅ Device cache entry ensured for {device_id}")
                    else:
                        logger.warning(
                            f"⚠️ Could not get device info from Nautobot for {device_id}"
                        )
                except Exception as e:
                    logger.error(
                        f"❌ Failed to create device cache entry for {device_id}: {e}"
                    )
                    # Continue anyway - caching will fail but data will still be returned

            # Interfaces
            if include_interfaces:
                AsyncTopologyDiscoveryService.update_device_progress(
                    job_id,
                    device_id,
                    "in_progress",
                    int(completed_tasks / total_tasks * 100),
                    "Discovering interfaces",
                )
                try:
                    logger.info(
                        f"📍 Calling API endpoint for interfaces on device {device_id}"
                    )
                    result = await AsyncTopologyDiscoveryService._call_device_endpoint(
                        device_id=device_id, endpoint="interfaces", auth_token=auth_token
                    )
                    logger.info(
                        f"📍 Interfaces Result: success={result.get('success')}, "
                        f"output type={type(result.get('output'))}"
                    )

                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["interfaces"] = result["output"]
                        logger.info(f"✅ Got {len(result['output'])} interfaces")

                        # Cache if requested
                        if cache_results and db:
                            AsyncTopologyDiscoveryService._cache_interfaces(
                                db, device_id, result["output"]
                            )
                    else:
                        logger.warning(
                            f"⚠️ No interfaces data: success={result.get('success')}, "
                            f"output={result.get('output')}"
                        )
                except Exception as e:
                    logger.error(
                        f"❌ Failed to get interfaces for {device_id}: {e}", exc_info=True
                    )

                completed_tasks += 1

            # Static Routes
            if include_static_routes:
                AsyncTopologyDiscoveryService.update_device_progress(
                    job_id,
                    device_id,
                    "in_progress",
                    int(completed_tasks / total_tasks * 100),
                    "Discovering static routes",
                )
                try:
                    logger.info(
                        f"📍 Calling API endpoint for static routes on device {device_id}"
                    )
                    result = await AsyncTopologyDiscoveryService._call_device_endpoint(
                        device_id=device_id,
                        endpoint="ip-route/static",
                        auth_token=auth_token,
                    )
                    logger.info(
                        f"📍 Result: success={result.get('success')}, "
                        f"output type={type(result.get('output'))}"
                    )

                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["static_routes"] = result["output"]
                        logger.info(f"✅ Got {len(result['output'])} static routes")
                        
                        # Cache if requested
                        if cache_results and db:
                            AsyncTopologyDiscoveryService._cache_static_routes(
                                db, device_id, result["output"]
                            )
                    else:
                        logger.warning(
                            f"⚠️ No static routes data: success={result.get('success')}, "
                            f"output={result.get('output')}"
                        )
                except Exception as e:
                    logger.error(
                        f"❌ Failed to get static routes for {device_id}: {e}",
                        exc_info=True,
                    )

                completed_tasks += 1

            # OSPF Routes
            if include_ospf_routes:
                AsyncTopologyDiscoveryService.update_device_progress(
                    job_id,
                    device_id,
                    "in_progress",
                    int(completed_tasks / total_tasks * 100),
                    "Discovering OSPF routes",
                )
                try:
                    result = await AsyncTopologyDiscoveryService._call_device_endpoint(
                        device_id=device_id, endpoint="ip-route/ospf", auth_token=auth_token
                    )
                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["ospf_routes"] = result["output"]
                        
                        # Cache if requested
                        if cache_results and db:
                            AsyncTopologyDiscoveryService._cache_ospf_routes(
                                db, device_id, result["output"]
                            )
                except Exception as e:
                    logger.error(f"Failed to get OSPF routes for {device_id}: {e}")

                completed_tasks += 1

            # BGP Routes
            if include_bgp_routes:
                AsyncTopologyDiscoveryService.update_device_progress(
                    job_id,
                    device_id,
                    "in_progress",
                    int(completed_tasks / total_tasks * 100),
                    "Discovering BGP routes",
                )
                try:
                    result = await AsyncTopologyDiscoveryService._call_device_endpoint(
                        device_id=device_id, endpoint="ip-route/bgp", auth_token=auth_token
                    )
                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["bgp_routes"] = result["output"]
                        
                        # Cache if requested
                        if cache_results and db:
                            AsyncTopologyDiscoveryService._cache_bgp_routes(
                                db, device_id, result["output"]
                            )
                except Exception as e:
                    logger.error(f"Failed to get BGP routes for {device_id}: {e}")

                completed_tasks += 1

            # MAC Address Table
            if include_mac_table:
                AsyncTopologyDiscoveryService.update_device_progress(
                    job_id,
                    device_id,
                    "in_progress",
                    int(completed_tasks / total_tasks * 100),
                    "Discovering MAC address table",
                )
                try:
                    result = await AsyncTopologyDiscoveryService._call_device_endpoint(
                        device_id=device_id,
                        endpoint="mac-address-table",
                        auth_token=auth_token,
                    )
                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["mac_table"] = result["output"]
                        
                        # Cache if requested
                        if cache_results and db:
                            AsyncTopologyDiscoveryService._cache_mac_table(
                                db, device_id, result["output"]
                            )
                except Exception as e:
                    logger.error(f"Failed to get MAC table for {device_id}: {e}")

                completed_tasks += 1

            # CDP Neighbors
            if include_cdp_neighbors:
                AsyncTopologyDiscoveryService.update_device_progress(
                    job_id,
                    device_id,
                    "in_progress",
                    int(completed_tasks / total_tasks * 100),
                    "Discovering CDP neighbors",
                )
                try:
                    result = await AsyncTopologyDiscoveryService._call_device_endpoint(
                        device_id=device_id,
                        endpoint="cdp-neighbors",
                        auth_token=auth_token,
                    )
                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["cdp_neighbors"] = result["output"]
                        
                        # Cache if requested
                        if cache_results and db:
                            AsyncTopologyDiscoveryService._cache_cdp_neighbors(
                                db, device_id, result["output"]
                            )
                except Exception as e:
                    logger.error(f"Failed to get CDP neighbors for {device_id}: {e}")

                completed_tasks += 1

            # ARP Entries
            if include_arp:
                AsyncTopologyDiscoveryService.update_device_progress(
                    job_id,
                    device_id,
                    "in_progress",
                    int(completed_tasks / total_tasks * 100),
                    "Discovering ARP entries",
                )
                try:
                    logger.info(
                        f"📍 Calling API endpoint for ARP entries on device {device_id}"
                    )
                    result = await AsyncTopologyDiscoveryService._call_device_endpoint(
                        device_id=device_id, endpoint="ip-arp", auth_token=auth_token
                    )
                    logger.info(
                        f"📍 ARP Result: success={result.get('success')}, "
                        f"output type={type(result.get('output'))}"
                    )

                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["arp_entries"] = result["output"]
                        logger.info(f"✅ Got {len(result['output'])} ARP entries")
                        
                        # Cache if requested
                        if cache_results and db:
                            AsyncTopologyDiscoveryService._cache_arp_entries(
                                db, device_id, result["output"]
                            )
                    else:
                        logger.warning(
                            f"⚠️ No ARP data: success={result.get('success')}, "
                            f"output={result.get('output')}"
                        )
                except Exception as e:
                    logger.error(
                        f"❌ Failed to get ARP entries for {device_id}: {e}", exc_info=True
                    )

                completed_tasks += 1

            AsyncTopologyDiscoveryService.update_device_progress(
                job_id, device_id, "completed", 100, "Discovery completed"
            )

            logger.info(f"✅ Async discovery completed for device {device_id}")
            return device_data

        except Exception as e:
            error_msg = f"Discovery failed: {str(e)}"
            logger.error(f"❌ Async discovery failed for device {device_id}: {e}")
            AsyncTopologyDiscoveryService.update_device_progress(
                job_id, device_id, "failed", 0, None, error_msg
            )
            raise

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
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Discover topology data for multiple devices (async version).

        Entry point for API requests. Creates a job and discovers data
        from multiple devices sequentially.

        Args:
            device_ids: List of device IDs to discover
            include_*: Flags for what data to collect
            cache_results: Whether to cache results to database
            auth_token: Authentication token for internal API calls
            db: Database session for caching

        Returns:
            Dictionary with job_id and discovery results
        """
        job_id = AsyncTopologyDiscoveryService.create_job(device_ids)

        logger.info(
            f"🚀 Starting async topology discovery for {len(device_ids)} devices "
            f"(job: {job_id})"
        )
        logger.info(f"   Device IDs: {device_ids}")
        logger.info(
            f"   Options: static={include_static_routes}, ospf={include_ospf_routes}, "
            f"bgp={include_bgp_routes}, mac={include_mac_table}, "
            f"cdp={include_cdp_neighbors}, arp={include_arp}, "
            f"interfaces={include_interfaces}"
        )

        AsyncTopologyDiscoveryService.update_job_status(job_id, "in_progress")

        start_time = datetime.now(timezone.utc)
        devices_data = {}
        errors = {}

        # Discover devices sequentially (parallel execution with Celery is separate)
        for device_id in device_ids:
            try:
                device_data = await AsyncTopologyDiscoveryService.discover_device_data(
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
                    db=db,
                )
                devices_data[device_id] = device_data
            except Exception as e:
                errors[device_id] = str(e)

        duration = (datetime.now(timezone.utc) - start_time).total_seconds()

        # Update job with results
        job = AsyncTopologyDiscoveryService.get_job_progress(job_id)
        if job:
            job["devices_data"] = devices_data
            job["errors"] = errors
            job["duration_seconds"] = duration

        if errors and len(errors) == len(device_ids):
            AsyncTopologyDiscoveryService.update_job_status(
                job_id, "failed", "All devices failed"
            )
        else:
            AsyncTopologyDiscoveryService.update_job_status(job_id, "completed")

        logger.info(f"✅ Async topology discovery completed (job: {job_id})")
        logger.info(
            f"   Success: {len(devices_data)}, Failed: {len(errors)}, "
            f"Duration: {duration:.2f}s"
        )

        return {
            "job_id": job_id,
            "status": job["status"] if job else "unknown",
            "total_devices": len(device_ids),
            "successful_devices": len(devices_data),
            "failed_devices": len(errors),
            "devices_data": devices_data,
            "errors": errors,
            "duration_seconds": duration,
        }

    # Note: Cache methods have been moved to TopologyDiscoveryBase class
    # and are now shared between sync and async implementations
