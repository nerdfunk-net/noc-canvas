"""
Device cache service for managing cached network device data.
Provides CRUD operations and cache management functionality.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.device_cache import (
    DeviceCache, InterfaceCache, IPAddressCache, ARPCache,
    StaticRouteCache, OSPFRouteCache, BGPRouteCache, MACAddressTableCache, CDPNeighborCache
)
from ..schemas.device_cache import (
    DeviceCacheCreate,
    InterfaceCacheCreate,
    IPAddressCacheCreate,
    ARPCacheCreate,
    StaticRouteCacheCreate,
    OSPFRouteCacheCreate,
    BGPRouteCacheCreate,
    MACAddressTableCacheCreate,
    CDPNeighborCacheCreate,
    BulkCacheUpdate,
)

logger = logging.getLogger(__name__)


class DeviceCacheService:
    """Service for managing device cache data."""

    @staticmethod
    def get_device(db: Session, device_id: str) -> Optional[DeviceCache]:
        """Get device cache by device ID."""
        return db.query(DeviceCache).filter(DeviceCache.device_id == device_id).first()

    @staticmethod
    def get_device_cache(db: Session, device_id: str) -> Optional[DeviceCache]:
        """Get device cache by device ID (alias for backward compatibility)."""
        return DeviceCacheService.get_device(db, device_id)

    @staticmethod
    def get_all_devices(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        polling_enabled: Optional[bool] = None
    ) -> List[DeviceCache]:
        """Get all cached devices with optional filtering."""
        query = db.query(DeviceCache)
        if polling_enabled is not None:
            query = query.filter(DeviceCache.polling_enabled == polling_enabled)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_device_by_name(db: Session, device_name: str) -> Optional[DeviceCache]:
        """Get device by name."""
        return db.query(DeviceCache).filter(DeviceCache.device_name == device_name).first()

    @staticmethod
    def update_polling_status(db: Session, device_id: str, enabled: bool) -> Optional[DeviceCache]:
        """Enable or disable polling for a device."""
        device = DeviceCacheService.get_device(db, device_id)
        if device:
            device.polling_enabled = enabled
            db.commit()
            db.refresh(device)
        return device

    @staticmethod
    def invalidate_device_cache(db: Session, device_id: str) -> bool:
        """Delete device cache."""
        device = DeviceCacheService.get_device(db, device_id)
        if device:
            db.delete(device)
            db.commit()
            return True
        return False

    @staticmethod
    def clean_expired_cache(db: Session, device_id: Optional[str] = None) -> int:
        """Clean expired cache entries."""
        now = datetime.utcnow()
        logger.info(f"🧹 Cleaning expired cache. Current UTC time: {now}")

        # Only clean entries that have an expiration date AND are expired
        query = db.query(DeviceCache).filter(
            DeviceCache.cache_valid_until.isnot(None),
            DeviceCache.cache_valid_until <= now
        )
        if device_id:
            query = query.filter(DeviceCache.device_id == device_id)

        # Log expired entries before deletion
        expired_entries = query.all()
        for entry in expired_entries:
            logger.info(f"  📅 Expired: {entry.device_name} (valid until: {entry.cache_valid_until})")

        count = len(expired_entries)
        if count > 0:
            query.delete(synchronize_session=False)
            db.commit()
            logger.info(f"✅ Cleaned {count} expired cache entries")
        else:
            logger.info(f"✅ No expired cache entries to clean")
        return count

    @staticmethod
    def get_or_create_device_cache(
        db: Session, device_data: DeviceCacheCreate, ttl_minutes: int = 60
    ) -> DeviceCache:
        """Get existing device cache or create new one with default TTL."""
        device = DeviceCacheService.get_device_cache(db, device_data.device_id)
        now = datetime.utcnow()

        if device:
            # Update existing device
            for key, value in device_data.model_dump().items():
                if value is not None:
                    setattr(device, key, value)
            device.last_updated = now
            # Update cache expiration if not set or if being refreshed
            if not device.cache_valid_until or device.cache_valid_until < now:
                device.cache_valid_until = now + timedelta(minutes=ttl_minutes)
        else:
            # Create new device with expiration
            device_dict = device_data.model_dump()
            device_dict['cache_valid_until'] = now + timedelta(minutes=ttl_minutes)
            device = DeviceCache(**device_dict)

        db.add(device)
        db.commit()
        db.refresh(device)
        logger.info(f"Device cache {'updated' if device.last_updated != now else 'created'}: {device.device_name}, expires: {device.cache_valid_until}")
        return device

    @staticmethod
    def is_cache_valid(device: DeviceCache) -> bool:
        """Check if device cache is still valid."""
        if not device.cache_valid_until:
            return False
        return datetime.utcnow() < device.cache_valid_until

    @staticmethod
    def set_cache_ttl(
        db: Session, device_id: str, ttl_minutes: int = 60
    ) -> None:
        """Set cache validity period."""
        device = DeviceCacheService.get_device_cache(db, device_id)
        if device:
            device.cache_valid_until = datetime.utcnow() + timedelta(minutes=ttl_minutes)
            db.commit()

    @staticmethod
    def invalidate_cache(db: Session, device_id: str) -> None:
        """Invalidate device cache (set expiry to now)."""
        device = DeviceCacheService.get_device_cache(db, device_id)
        if device:
            device.cache_valid_until = datetime.utcnow()
            db.commit()

    # Interface Cache Operations
    @staticmethod
    def get_interface(
        db: Session, device_id: str, interface_name: str
    ) -> Optional[InterfaceCache]:
        """Get specific interface by device ID and interface name."""
        return db.query(InterfaceCache).filter(
            and_(
                InterfaceCache.device_id == device_id,
                InterfaceCache.interface_name == interface_name,
            )
        ).first()

    @staticmethod
    def get_interfaces_by_mac(db: Session, mac_address: str) -> List[InterfaceCache]:
        """Find interfaces by MAC address (reverse lookup)."""
        return db.query(InterfaceCache).filter(
            InterfaceCache.mac_address == mac_address
        ).all()

    @staticmethod
    def upsert_interface(
        db: Session, interface_data: InterfaceCacheCreate
    ) -> InterfaceCache:
        """Insert or update interface data."""
        interface = DeviceCacheService.get_interface(
            db, interface_data.device_id, interface_data.interface_name
        )

        if interface:
            # Update existing
            for key, value in interface_data.model_dump().items():
                if value is not None:
                    setattr(interface, key, value)
            interface.last_updated = datetime.utcnow()
        else:
            # Create new
            interface = InterfaceCache(**interface_data.model_dump())

        db.add(interface)
        db.commit()
        db.refresh(interface)
        return interface

    @staticmethod
    def bulk_upsert_interfaces(
        db: Session, device_id: str, interfaces: List[InterfaceCacheCreate]
    ) -> None:
        """Bulk insert/update interfaces for a device."""
        # Delete existing interfaces not in the new list
        interface_names = [i.interface_name for i in interfaces]
        db.query(InterfaceCache).filter(
            and_(
                InterfaceCache.device_id == device_id,
                InterfaceCache.interface_name.notin_(interface_names)
            )
        ).delete(synchronize_session=False)

        # Upsert each interface
        for interface_data in interfaces:
            DeviceCacheService.upsert_interface(db, interface_data)

    # IP Address Cache Operations
    @staticmethod
    def get_devices_by_ip(db: Session, ip_address: str) -> List[IPAddressCache]:
        """Find which device(s) have a specific IP address."""
        return db.query(IPAddressCache).filter(
            IPAddressCache.ip_address == ip_address
        ).all()

    @staticmethod
    def upsert_ip_address(
        db: Session, ip_data: IPAddressCacheCreate
    ) -> IPAddressCache:
        """Insert or update IP address data."""
        ip_entry = db.query(IPAddressCache).filter(
            and_(
                IPAddressCache.device_id == ip_data.device_id,
                IPAddressCache.interface_name == ip_data.interface_name,
                IPAddressCache.ip_address == ip_data.ip_address,
            )
        ).first()

        if ip_entry:
            # Update existing
            for key, value in ip_data.model_dump().items():
                if value is not None:
                    setattr(ip_entry, key, value)
            ip_entry.last_updated = datetime.utcnow()
        else:
            # Create new
            ip_entry = IPAddressCache(**ip_data.model_dump())

        db.add(ip_entry)
        db.commit()
        db.refresh(ip_entry)
        return ip_entry

    @staticmethod
    def bulk_upsert_ips(
        db: Session, device_id: str, ip_addresses: List[IPAddressCacheCreate]
    ) -> None:
        """Bulk insert/update IP addresses for a device."""
        # Delete existing IPs not in the new list
        new_ips = [(ip.interface_name, ip.ip_address) for ip in ip_addresses]
        existing = db.query(IPAddressCache).filter(
            IPAddressCache.device_id == device_id
        ).all()

        for existing_ip in existing:
            if (existing_ip.interface_name, existing_ip.ip_address) not in new_ips:
                db.delete(existing_ip)

        # Upsert each IP
        for ip_data in ip_addresses:
            DeviceCacheService.upsert_ip_address(db, ip_data)

    # ARP Cache Operations
    @staticmethod
    def get_arp_by_mac(db: Session, mac_address: str) -> List[ARPCache]:
        """Find ARP entries by MAC address."""
        return db.query(ARPCache).filter(ARPCache.mac_address == mac_address).all()

    @staticmethod
    def get_arp_by_ip(db: Session, ip_address: str) -> List[ARPCache]:
        """Find ARP entries by IP address."""
        return db.query(ARPCache).filter(ARPCache.ip_address == ip_address).all()

    @staticmethod
    def get_arp_entries_by_mac(db: Session, mac_address: str) -> List[ARPCache]:
        """Find ARP entries by MAC address (alias)."""
        return DeviceCacheService.get_arp_by_mac(db, mac_address)

    @staticmethod
    def get_arp_entries_by_ip(db: Session, ip_address: str) -> List[ARPCache]:
        """Find ARP entries by IP address (alias)."""
        return DeviceCacheService.get_arp_by_ip(db, ip_address)

    @staticmethod
    def bulk_replace_arp(
        db: Session, device_id: str, arp_entries: List[ARPCacheCreate]
    ) -> None:
        """Replace all ARP entries for a device."""
        # Delete all existing ARP entries for this device
        db.query(ARPCache).filter(ARPCache.device_id == device_id).delete()

        # Insert new entries
        for arp_data in arp_entries:
            arp_entry = ARPCache(**arp_data.model_dump())
            db.add(arp_entry)

        db.commit()

    # Bulk Operations
    @staticmethod
    def bulk_update_device_cache(
        db: Session, cache_data: BulkCacheUpdate, cache_ttl_minutes: int = 60
    ) -> DeviceCache:
        """
        Bulk update entire device cache from discovery data.
        This is the main method for populating cache after running device commands.
        """
        logger.info(f"Bulk updating cache for device: {cache_data.device.device_id}")

        # Update device
        device = DeviceCacheService.get_or_create_device_cache(db, cache_data.device)

        # Set cache TTL
        device.cache_valid_until = datetime.utcnow() + timedelta(minutes=cache_ttl_minutes)
        db.commit()

        # Update interfaces first
        if cache_data.interfaces:
            DeviceCacheService.bulk_upsert_interfaces(
                db, device.device_id, cache_data.interfaces
            )

        # Update IP addresses - need to set interface_id from interface_name
        if cache_data.ip_addresses:
            for ip_data in cache_data.ip_addresses:
                # Look up interface_id if interface_name is provided
                if ip_data.interface_name and not ip_data.interface_id:
                    interface = DeviceCacheService.get_interface(
                        db, ip_data.device_id, ip_data.interface_name
                    )
                    if interface:
                        ip_data.interface_id = interface.id

            DeviceCacheService.bulk_upsert_ips(
                db, device.device_id, cache_data.ip_addresses
            )

        # Update ARP entries
        if cache_data.arp_entries:
            DeviceCacheService.bulk_replace_arp(
                db, device.device_id, cache_data.arp_entries
            )

        logger.info(
            f"Cache updated: {len(cache_data.interfaces)} interfaces, "
            f"{len(cache_data.ip_addresses)} IPs, "
            f"{len(cache_data.arp_entries)} ARP entries"
        )

        return device

    # Static Route Cache Operations
    @staticmethod
    def bulk_replace_static_routes(
        db: Session, device_id: str, routes: List[StaticRouteCacheCreate]
    ) -> None:
        """Replace all static routes for a device."""
        # Delete all existing static routes for this device
        db.query(StaticRouteCache).filter(StaticRouteCache.device_id == device_id).delete()

        # Insert new routes
        for route_data in routes:
            route = StaticRouteCache(**route_data.model_dump())
            db.add(route)

        db.commit()

    # OSPF Route Cache Operations
    @staticmethod
    def bulk_replace_ospf_routes(
        db: Session, device_id: str, routes: List[OSPFRouteCacheCreate]
    ) -> None:
        """Replace all OSPF routes for a device."""
        # Delete all existing OSPF routes for this device
        db.query(OSPFRouteCache).filter(OSPFRouteCache.device_id == device_id).delete()

        # Insert new routes
        for route_data in routes:
            route = OSPFRouteCache(**route_data.model_dump())
            db.add(route)

        db.commit()

    # BGP Route Cache Operations
    @staticmethod
    def bulk_replace_bgp_routes(
        db: Session, device_id: str, routes: List[BGPRouteCacheCreate]
    ) -> None:
        """Replace all BGP routes for a device."""
        # Delete all existing BGP routes for this device
        db.query(BGPRouteCache).filter(BGPRouteCache.device_id == device_id).delete()

        # Insert new routes
        for route_data in routes:
            route = BGPRouteCache(**route_data.model_dump())
            db.add(route)

        db.commit()

    # MAC Address Table Cache Operations
    @staticmethod
    def bulk_replace_mac_table(
        db: Session, device_id: str, entries: List[MACAddressTableCacheCreate]
    ) -> None:
        """Replace all MAC address table entries for a device."""
        # Delete all existing MAC table entries for this device
        db.query(MACAddressTableCache).filter(MACAddressTableCache.device_id == device_id).delete()

        # Insert new entries
        for entry_data in entries:
            entry = MACAddressTableCache(**entry_data.model_dump())
            db.add(entry)

        db.commit()

    # CDP Neighbor Cache Operations
    @staticmethod
    def bulk_replace_cdp_neighbors(
        db: Session, device_id: str, neighbors: List[CDPNeighborCacheCreate]
    ) -> None:
        """Replace all CDP neighbor entries for a device."""
        # Delete all existing CDP neighbors for this device
        db.query(CDPNeighborCache).filter(CDPNeighborCache.device_id == device_id).delete()

        # Insert new neighbors
        for neighbor_data in neighbors:
            neighbor = CDPNeighborCache(**neighbor_data.model_dump())
            db.add(neighbor)

        db.commit()


# Singleton instance
device_cache_service = DeviceCacheService()
