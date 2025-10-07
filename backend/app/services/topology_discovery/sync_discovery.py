"""
Sync topology discovery for Celery workers (background execution).

This module handles topology discovery when called from Celery background tasks.
It uses direct SSH communication to devices, bypassing HTTP layers entirely.

Execution Path:
    Celery Task → SyncTopologyDiscoveryService → Direct SSH → Network Device
"""

import asyncio
import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from ...schemas.device_cache import (
    ARPCacheCreate,
    BGPRouteCacheCreate,
    CDPNeighborCacheCreate,
    DeviceCacheCreate,
    InterfaceCacheCreate,
    IPAddressCacheCreate,
    MACAddressTableCacheCreate,
    OSPFRouteCacheCreate,
    StaticRouteCacheCreate,
)
from ...services.device_cache_service import device_cache_service
from ...services.device_communication import DeviceCommunicationService
from ...services.nautobot import nautobot_service
from .base import TopologyDiscoveryBase

logger = logging.getLogger(__name__)


class SyncTopologyDiscoveryService(TopologyDiscoveryBase):
    """Sync topology discovery service for Celery/background execution."""

    @staticmethod
    def _call_device_endpoint_sync(
        device_id: str, endpoint: str, auth_token: str
    ) -> Dict[str, Any]:
        """
        Direct device command execution for Celery workers (no HTTP calls).

        This method uses direct SSH communication via DeviceCommunicationService,
        bypassing any HTTP layers. Perfect for Celery workers that need to scale
        independently.

        Args:
            device_id: The device ID
            endpoint: The endpoint path (e.g., 'cdp-neighbors', 'ip-route/static')
            auth_token: Authentication token (used to extract username)

        Returns:
            Command execution result as dict with 'success' and 'output' keys
        """
        try:
            # Extract username from token
            username = SyncTopologyDiscoveryService._get_username_from_token(
                auth_token
            )

            # Get the command for this endpoint
            command = SyncTopologyDiscoveryService._get_device_command(endpoint)

            # Define async function to get device info and execute command
            async def execute_device_command():
                # Check JSON blob cache first for any command
                try:
                    import json
                    from ...core.database import SessionLocal
                    from ...services.json_cache_service import JSONCacheService
                    
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
                            logger.info(f"✅ Using cached data for device {device_id}, command '{command}' (endpoint: {endpoint})")
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
                    logger.warning(f"Failed to check cache for device {device_id}, command '{command}', will execute: {str(cache_error)}")

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
                    logger.error(
                        f"Device {device_id} does not have a primary IPv4 address"
                    )
                    return {
                        "success": False,
                        "error": "Device does not have a primary IPv4 address",
                    }

                platform_info = device_data.get("platform")
                if not platform_info or not platform_info.get("network_driver"):
                    logger.error(
                        f"Device {device_id} does not have a platform/network_driver configured"
                    )
                    return {
                        "success": False,
                        "error": "Device platform or network_driver not configured",
                    }

                # Create transformed device info with flattened structure
                device_info = {
                    "device_id": device_id,
                    "name": device_data.get("name", ""),
                    "primary_ip": primary_ip4["address"].split("/")[
                        0
                    ],  # Remove subnet mask
                    "platform": platform_info.get("name", ""),
                    "network_driver": platform_info["network_driver"],
                }

                # Execute command directly using DeviceCommunicationService
                device_service = DeviceCommunicationService()
                result = await device_service.execute_command(
                    device_info=device_info,
                    command=command,
                    username=username,
                    parser="TEXTFSM",
                )
                
                # Cache data after successful execution for any command
                if result.get("success") and result.get("parsed") and isinstance(result.get("output"), list):
                    try:
                        import json
                        from ...core.database import SessionLocal
                        from ...services.json_cache_service import JSONCacheService
                        
                        db = SessionLocal()
                        try:
                            json_data = json.dumps(result["output"])
                            JSONCacheService.set_cache(
                                db=db,
                                device_id=device_id,
                                command=command,
                                json_data=json_data
                            )
                            logger.info(f"✅ Cached data for device {device_id}, command '{command}' (endpoint: {endpoint})")
                        finally:
                            db.close()
                    except Exception as cache_error:
                        logger.error(f"Failed to cache data for device {device_id}, command '{command}': {str(cache_error)}")
                
                return result

            # Use asyncio.run for sync context (Celery worker)
            result = asyncio.run(execute_device_command())
            return result

        except Exception as e:
            logger.error(
                f"Direct device call failed for {device_id}/{endpoint}: {e}",
                exc_info=True,
            )
            return {"success": False, "error": str(e)}

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
        auth_token: str = "",
    ) -> Dict[str, Any]:
        """
        Synchronous version of discover_device_data for Celery workers.

        This method is called from Celery tasks and runs in the Celery worker context.
        It uses direct device communication (no HTTP) and updates task progress via
        Celery state.

        Args:
            db: Database session
            device_id: Device ID to discover
            task: Celery task instance for progress updates
            include_*: Flags for what data to collect
            cache_results: Whether to cache results to database
            auth_token: Authentication token (for username extraction)

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
            # that reference the device_cache table
            if cache_results:
                try:
                    # Extract username from token to get device info
                    username = SyncTopologyDiscoveryService._get_username_from_token(
                        auth_token
                    )

                    # Get device info from Nautobot to populate device cache
                    async def get_device_info():
                        return await nautobot_service.get_device(device_id, username)

                    device_info = asyncio.run(get_device_info())

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

            # Static Routes
            if include_static_routes:
                task.update_state(
                    state="PROGRESS",
                    meta={
                        "progress": int(completed_tasks / total_tasks * 100),
                        "current_task": "Discovering static routes",
                    },
                )
                try:
                    logger.info(
                        f"📍 Executing command for static routes on device {device_id}"
                    )
                    result = SyncTopologyDiscoveryService._call_device_endpoint_sync(
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
                        if cache_results:
                            SyncTopologyDiscoveryService._cache_static_routes_sync(
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
                task.update_state(
                    state="PROGRESS",
                    meta={
                        "progress": int(completed_tasks / total_tasks * 100),
                        "current_task": "Discovering OSPF routes",
                    },
                )
                try:
                    result = SyncTopologyDiscoveryService._call_device_endpoint_sync(
                        device_id=device_id,
                        endpoint="ip-route/ospf",
                        auth_token=auth_token,
                    )
                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["ospf_routes"] = result["output"]

                        # Cache if requested
                        if cache_results:
                            SyncTopologyDiscoveryService._cache_ospf_routes_sync(
                                db, device_id, result["output"]
                            )
                except Exception as e:
                    logger.error(f"Failed to get OSPF routes for {device_id}: {e}")

                completed_tasks += 1

            # BGP Routes
            if include_bgp_routes:
                task.update_state(
                    state="PROGRESS",
                    meta={
                        "progress": int(completed_tasks / total_tasks * 100),
                        "current_task": "Discovering BGP routes",
                    },
                )
                try:
                    result = SyncTopologyDiscoveryService._call_device_endpoint_sync(
                        device_id=device_id, endpoint="ip-route/bgp", auth_token=auth_token
                    )
                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["bgp_routes"] = result["output"]

                        # Cache if requested
                        if cache_results:
                            SyncTopologyDiscoveryService._cache_bgp_routes_sync(
                                db, device_id, result["output"]
                            )
                except Exception as e:
                    logger.error(f"Failed to get BGP routes for {device_id}: {e}")

                completed_tasks += 1

            # MAC Address Table
            if include_mac_table:
                task.update_state(
                    state="PROGRESS",
                    meta={
                        "progress": int(completed_tasks / total_tasks * 100),
                        "current_task": "Discovering MAC address table",
                    },
                )
                try:
                    result = SyncTopologyDiscoveryService._call_device_endpoint_sync(
                        device_id=device_id,
                        endpoint="mac-address-table",
                        auth_token=auth_token,
                    )
                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["mac_table"] = result["output"]

                        # Cache if requested
                        if cache_results:
                            SyncTopologyDiscoveryService._cache_mac_table_sync(
                                db, device_id, result["output"]
                            )
                except Exception as e:
                    logger.error(f"Failed to get MAC table for {device_id}: {e}")

                completed_tasks += 1

            # CDP Neighbors
            if include_cdp_neighbors:
                task.update_state(
                    state="PROGRESS",
                    meta={
                        "progress": int(completed_tasks / total_tasks * 100),
                        "current_task": "Discovering CDP neighbors",
                    },
                )
                try:
                    result = SyncTopologyDiscoveryService._call_device_endpoint_sync(
                        device_id=device_id,
                        endpoint="cdp-neighbors",
                        auth_token=auth_token,
                    )
                    if result.get("success") and isinstance(result.get("output"), list):
                        device_data["cdp_neighbors"] = result["output"]

                        # Cache if requested
                        if cache_results:
                            SyncTopologyDiscoveryService._cache_cdp_neighbors_sync(
                                db, device_id, result["output"]
                            )
                except Exception as e:
                    logger.error(f"Failed to get CDP neighbors for {device_id}: {e}")

                completed_tasks += 1

            # ARP Entries
            if include_arp:
                task.update_state(
                    state="PROGRESS",
                    meta={
                        "progress": int(completed_tasks / total_tasks * 100),
                        "current_task": "Discovering ARP entries",
                    },
                )
                try:
                    logger.info(
                        f"📍 Executing command for ARP entries on device {device_id}"
                    )
                    result = SyncTopologyDiscoveryService._call_device_endpoint_sync(
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
                        if cache_results:
                            SyncTopologyDiscoveryService._cache_arp_entries_sync(
                                db, device_id, result["output"]
                            )
                    else:
                        logger.warning(
                            f"⚠️ No ARP data: success={result.get('success')}, "
                            f"output={result.get('output')}"
                        )
                except Exception as e:
                    logger.error(
                        f"❌ Failed to get ARP entries for {device_id}: {e}",
                        exc_info=True,
                    )

                completed_tasks += 1

            # Interfaces
            if include_interfaces:
                task.update_state(
                    state="PROGRESS",
                    meta={
                        "progress": int(completed_tasks / total_tasks * 100),
                        "current_task": "Discovering interfaces",
                    },
                )
                try:
                    logger.info(
                        f"📍 Executing command for interfaces on device {device_id}"
                    )
                    result = SyncTopologyDiscoveryService._call_device_endpoint_sync(
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
                        if cache_results:
                            SyncTopologyDiscoveryService._cache_interfaces_sync(
                                db, device_id, result["output"]
                            )
                    else:
                        logger.warning(
                            f"⚠️ No interfaces data: success={result.get('success')}, "
                            f"output={result.get('output')}"
                        )
                except Exception as e:
                    logger.error(
                        f"❌ Failed to get interfaces for {device_id}: {e}",
                        exc_info=True,
                    )

                completed_tasks += 1

            task.update_state(
                state="PROGRESS",
                meta={"progress": 100, "current_task": "Discovery completed"},
            )

            logger.info(f"✅ Sync discovery completed for device {device_id}")
            return device_data

        except Exception as e:
            error_msg = f"Discovery failed: {str(e)}"
            logger.error(
                f"❌ Sync discovery failed for device {device_id}: {e}", exc_info=True
            )
            raise

    # Synchronous cache methods for Celery workers

    @staticmethod
    def _cache_static_routes_sync(
        db: Session, device_id: str, routes: List[Dict[str, Any]]
    ) -> None:
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
                    metric=route.get("metric"),
                )
                cache_entries.append(cache_entry)

            # Use bulk replace method
            if cache_entries:
                device_cache_service.bulk_replace_static_routes(
                    db, device_id, cache_entries
                )
                logger.debug(
                    f"Cached {len(routes)} static routes for device {device_id}"
                )
        except Exception as e:
            logger.error(f"Failed to cache static routes for {device_id}: {e}")
            # Rollback the session to recover from the error
            db.rollback()

    @staticmethod
    def _cache_ospf_routes_sync(
        db: Session, device_id: str, routes: List[Dict[str, Any]]
    ) -> None:
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
                    route_type=route.get("route_type"),
                )
                cache_entries.append(cache_entry)

            # Use bulk replace method
            if cache_entries:
                device_cache_service.bulk_replace_ospf_routes(
                    db, device_id, cache_entries
                )
                logger.debug(f"Cached {len(routes)} OSPF routes for device {device_id}")
        except Exception as e:
            logger.error(f"Failed to cache OSPF routes for {device_id}: {e}")
            db.rollback()

    @staticmethod
    def _cache_bgp_routes_sync(
        db: Session, device_id: str, routes: List[Dict[str, Any]]
    ) -> None:
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
                    weight=route.get("weight"),
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
    def _cache_mac_table_sync(
        db: Session, device_id: str, mac_entries: List[Dict[str, Any]]
    ) -> None:
        """Synchronous cache method for MAC address table."""
        try:
            cache_entries = []
            for entry in mac_entries:
                cache_entry = MACAddressTableCacheCreate(
                    device_id=device_id,
                    vlan=entry.get("vlan", ""),
                    mac_address=entry.get("destination_address", ""),
                    interface=entry.get("destination_port", ""),
                    type=entry.get("type", ""),
                )
                cache_entries.append(cache_entry)

            # Use bulk replace method
            if cache_entries:
                device_cache_service.bulk_replace_mac_table(db, device_id, cache_entries)
                logger.debug(
                    f"Cached {len(mac_entries)} MAC entries for device {device_id}"
                )
        except Exception as e:
            logger.error(f"Failed to cache MAC table for {device_id}: {e}")
            db.rollback()

    @staticmethod
    def _cache_cdp_neighbors_sync(
        db: Session, device_id: str, neighbors: List[Dict[str, Any]]
    ) -> None:
        """Synchronous cache method for CDP neighbors."""
        try:
            cache_entries = []
            for neighbor in neighbors:
                # Extract fields with case-insensitive fallback (TextFSM may return uppercase)
                neighbor_name_raw = (
                    neighbor.get("NEIGHBOR")
                    or neighbor.get("neighbor")
                    or neighbor.get("NEIGHBOR_NAME")
                    or neighbor.get("neighbor_name")
                    or neighbor.get("DESTINATION_HOST")
                    or neighbor.get("destination_host")
                    or ""
                )
                local_interface_raw = (
                    neighbor.get("LOCAL_INTERFACE")
                    or neighbor.get("local_interface")
                    or neighbor.get("LOCAL_PORT")
                    or neighbor.get("local_port")
                    or ""
                )
                neighbor_ip_raw = (
                    neighbor.get("MANAGEMENT_IP")
                    or neighbor.get("management_ip")
                    or neighbor.get("NEIGHBOR_IP")
                    or neighbor.get("neighbor_ip")
                    or ""
                )
                neighbor_interface_raw = (
                    neighbor.get("NEIGHBOR_INTERFACE")
                    or neighbor.get("neighbor_interface")
                    or neighbor.get("NEIGHBOR_PORT")
                    or neighbor.get("neighbor_port")
                    or ""
                )
                platform_raw = neighbor.get("PLATFORM") or neighbor.get("platform") or ""
                capabilities_raw = (
                    neighbor.get("CAPABILITIES") or neighbor.get("capabilities") or ""
                )

                # Handle if fields are lists (some TextFSM templates return lists)
                if isinstance(neighbor_name_raw, list):
                    neighbor_name = neighbor_name_raw[0] if neighbor_name_raw else ""
                else:
                    neighbor_name = neighbor_name_raw
                neighbor_name = neighbor_name.strip() if neighbor_name else ""

                if isinstance(local_interface_raw, list):
                    local_interface = (
                        local_interface_raw[0] if local_interface_raw else ""
                    )
                else:
                    local_interface = local_interface_raw
                local_interface = local_interface.strip() if local_interface else ""

                # Skip entries without neighbor name or local interface
                if not neighbor_name or not local_interface:
                    logger.warning(
                        f"Skipping CDP neighbor with missing name or interface: {neighbor}"
                    )
                    continue

                # Handle other fields
                if isinstance(neighbor_ip_raw, list):
                    neighbor_ip = neighbor_ip_raw[0] if neighbor_ip_raw else ""
                else:
                    neighbor_ip = neighbor_ip_raw
                neighbor_ip = neighbor_ip.strip() if neighbor_ip else ""

                if isinstance(neighbor_interface_raw, list):
                    neighbor_interface = (
                        neighbor_interface_raw[0] if neighbor_interface_raw else ""
                    )
                else:
                    neighbor_interface = neighbor_interface_raw
                neighbor_interface = (
                    neighbor_interface.strip() if neighbor_interface else ""
                )

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
                    capabilities=capabilities if capabilities else None,
                )
                cache_entries.append(cache_entry)

            # Use bulk replace method
            if cache_entries:
                device_cache_service.bulk_replace_cdp_neighbors(
                    db, device_id, cache_entries
                )
                logger.debug(
                    f"Cached {len(cache_entries)} CDP neighbors for device {device_id}"
                )
        except Exception as e:
            logger.error(f"Failed to cache CDP neighbors for {device_id}: {e}")
            db.rollback()

    @staticmethod
    def _cache_arp_entries_sync(
        db: Session, device_id: str, arp_entries: List[Dict[str, Any]]
    ) -> None:
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
                if age and age.strip() and age.strip() != "-":
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
                    age=age_int,
                )
                cache_entries.append(cache_entry)

            # Use bulk replace method
            if cache_entries:
                device_cache_service.bulk_replace_arp(db, device_id, cache_entries)
                logger.debug(
                    f"Cached {len(cache_entries)} ARP entries for device {device_id}"
                )
        except Exception as e:
            logger.error(f"Failed to cache ARP entries for {device_id}: {e}")
            db.rollback()

    @staticmethod
    def _cache_interfaces_sync(
        db: Session, device_id: str, interfaces: List[Dict[str, Any]]
    ) -> None:
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
                    vlan_id=None,  # Parse from interface name if needed (e.g., Gi0/0.100)
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
                        is_primary=False,
                    )
                    ip_entries.append(ip_entry)

            # Use upsert for interfaces
            if interface_entries:
                for interface_entry in interface_entries:
                    device_cache_service.upsert_interface(db, interface_entry)
                logger.debug(
                    f"Cached {len(interface_entries)} interfaces for device {device_id}"
                )

            # Cache IP addresses using bulk upsert
            if ip_entries:
                device_cache_service.bulk_upsert_ips(db, device_id, ip_entries)
                logger.debug(
                    f"Cached {len(ip_entries)} IP addresses for device {device_id}"
                )
        except Exception as e:
            logger.error(f"Failed to cache interfaces for {device_id}: {e}")
            db.rollback()
