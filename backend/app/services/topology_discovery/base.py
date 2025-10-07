"""
Base topology discovery functionality shared by async and sync implementations.

This module contains:
- Command mappings for network devices
- Job management (creation, progress tracking, status updates)
- Utility functions (JWT token parsing, command lookup)
- Cache methods for topology data (interfaces, routes, ARP, CDP, MAC table)
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

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

    # Cache methods for topology data
    # These methods are used by both sync and async discovery implementations

    @staticmethod
    def _cache_static_routes(
        db: Session, device_id: str, routes: List[Dict[str, Any]]
    ) -> None:
        """Cache static routes to database."""
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

            if cache_entries:
                device_cache_service.bulk_replace_static_routes(
                    db, device_id, cache_entries
                )
                logger.debug(
                    f"Cached {len(routes)} static routes for device {device_id}"
                )
        except Exception as e:
            logger.error(f"Failed to cache static routes for {device_id}: {e}")
            db.rollback()

    @staticmethod
    def _cache_ospf_routes(
        db: Session, device_id: str, routes: List[Dict[str, Any]]
    ) -> None:
        """Cache OSPF routes to database."""
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

            if cache_entries:
                device_cache_service.bulk_replace_ospf_routes(
                    db, device_id, cache_entries
                )
                logger.debug(f"Cached {len(routes)} OSPF routes for device {device_id}")
        except Exception as e:
            logger.error(f"Failed to cache OSPF routes for {device_id}: {e}")
            db.rollback()

    @staticmethod
    def _cache_bgp_routes(
        db: Session, device_id: str, routes: List[Dict[str, Any]]
    ) -> None:
        """Cache BGP routes to database."""
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

            if cache_entries:
                device_cache_service.bulk_replace_bgp_routes(db, device_id, cache_entries)
                logger.debug(f"Cached {len(routes)} BGP routes for device {device_id}")
        except Exception as e:
            logger.error(f"Failed to cache BGP routes for {device_id}: {e}")
            db.rollback()

    @staticmethod
    def _cache_mac_table(
        db: Session, device_id: str, mac_entries: List[Dict[str, Any]]
    ) -> None:
        """Cache MAC address table to database."""
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

            if cache_entries:
                device_cache_service.bulk_replace_mac_table(db, device_id, cache_entries)
                logger.debug(
                    f"Cached {len(mac_entries)} MAC entries for device {device_id}"
                )
        except Exception as e:
            logger.error(f"Failed to cache MAC table for {device_id}: {e}")
            db.rollback()

    @staticmethod
    def _cache_cdp_neighbors(
        db: Session, device_id: str, neighbors: List[Dict[str, Any]]
    ) -> None:
        """Cache CDP neighbors to database."""
        try:
            cache_entries = []
            for neighbor in neighbors:
                # Extract fields with case-insensitive fallback
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

                # Handle if fields are lists
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
    def _cache_arp_entries(
        db: Session, device_id: str, arp_entries: List[Dict[str, Any]]
    ) -> None:
        """Cache ARP entries to database."""
        try:
            cache_entries = []
            for entry in arp_entries:
                # Handle case-insensitive field names
                protocol = entry.get("protocol") or entry.get("PROTOCOL") or "Internet"
                address = entry.get("address") or entry.get("ADDRESS") or ""
                age = entry.get("age") or entry.get("AGE") or ""
                mac = entry.get("mac") or entry.get("MAC") or ""
                interface = entry.get("interface") or entry.get("INTERFACE") or ""

                # Handle list values
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

            if cache_entries:
                device_cache_service.bulk_replace_arp(db, device_id, cache_entries)
                logger.debug(
                    f"Cached {len(cache_entries)} ARP entries for device {device_id}"
                )
        except Exception as e:
            logger.error(f"Failed to cache ARP entries for {device_id}: {e}")
            db.rollback()

    @staticmethod
    def _cache_interfaces(
        db: Session, device_id: str, interfaces: List[Dict[str, Any]]
    ) -> None:
        """Cache interfaces and their IP addresses to database."""
        try:
            interface_entries = []
            ip_entries = []

            for iface in interfaces:
                # Determine status from link_status and protocol_status
                link_status = iface.get("link_status", "").lower()
                protocol_status = iface.get("protocol_status", "").lower()

                # Combine statuses
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
                    vlan_id=None,
                )
                interface_entries.append(interface_entry)

                # Create IP address entries if present
                ip_address = iface.get("ip_address")
                if ip_address and ip_address != "unassigned":
                    subnet_mask = None
                    if "/" in ip_address:
                        ip_addr, prefix = ip_address.split("/")
                        ip_address = ip_addr
                        subnet_mask = prefix

                    ip_entry = IPAddressCacheCreate(
                        device_id=device_id,
                        interface_id=None,
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
