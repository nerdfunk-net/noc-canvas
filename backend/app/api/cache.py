"""
API endpoints for device cache operations.
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.device_cache import (
    DeviceCacheResponse,
    InterfaceCacheResponse,
    IPAddressCacheResponse,
    ARPCacheResponse,
    BulkCacheUpdate,
    DeviceCacheWithDetails,
    StaticRouteCacheResponse,
    OSPFRouteCacheResponse,
    BGPRouteCacheResponse,
    MACAddressTableCacheResponse,
    CDPNeighborCacheResponse,
)
from app.services.device_cache_service import DeviceCacheService
from app.models.device_cache import (
    DeviceCache,
    InterfaceCache,
    IPAddressCache,
    ARPCache,
    StaticRouteCache,
    OSPFRouteCache,
    BGPRouteCache,
    MACAddressTableCache,
    CDPNeighborCache,
)

router = APIRouter(prefix="/cache", tags=["cache"])


@router.post("/fix-null-expirations")
def fix_null_cache_expirations(
    ttl_minutes: int = 60,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Fix devices with NULL cache_valid_until by setting default TTL."""
    from datetime import timedelta
    import logging

    logger = logging.getLogger(__name__)

    now = datetime.now(timezone.utc)
    null_devices = (
        db.query(DeviceCache).filter(DeviceCache.cache_valid_until.is_(None)).all()
    )

    logger.info(f"🔧 Fixing {len(null_devices)} devices with NULL expiration")
    print(f"\n🔧 Fixing {len(null_devices)} devices with NULL expiration")

    for device in null_devices:
        device.cache_valid_until = now + timedelta(minutes=ttl_minutes)
        logger.info(
            f"  ✅ Fixed: {device.device_name} - expires: {device.cache_valid_until}"
        )
        print(f"  ✅ Fixed: {device.device_name} - expires: {device.cache_valid_until}")

    db.commit()

    return {
        "message": f"Fixed {len(null_devices)} devices with NULL cache_valid_until",
        "devices_fixed": [d.device_name for d in null_devices],
        "new_expiration": (now + timedelta(minutes=ttl_minutes)).isoformat(),
    }


@router.get("/statistics")
def get_cache_statistics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get cache statistics and overview."""
    now = datetime.now(timezone.utc)

    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"📊 Getting cache statistics. Current UTC time: {now}")

    # Total counts
    total_devices = db.query(func.count(DeviceCache.device_id)).scalar()
    total_interfaces = db.query(func.count(InterfaceCache.id)).scalar()
    total_ips = db.query(func.count(IPAddressCache.id)).scalar()
    total_arp = db.query(func.count(ARPCache.id)).scalar()
    total_static_routes = db.query(func.count(StaticRouteCache.id)).scalar()
    total_ospf_routes = db.query(func.count(OSPFRouteCache.id)).scalar()
    total_bgp_routes = db.query(func.count(BGPRouteCache.id)).scalar()
    total_mac_table = db.query(func.count(MACAddressTableCache.id)).scalar()
    total_cdp_neighbors = db.query(func.count(CDPNeighborCache.id)).scalar()

    # JSON Blob Cache count
    from app.models.device_cache import JSONBlobCache

    total_json_blobs = db.query(func.count(JSONBlobCache.id)).scalar()

    # Valid vs expired cache entries (handle NULL values)
    valid_devices = (
        db.query(func.count(DeviceCache.device_id))
        .filter(
            DeviceCache.cache_valid_until.isnot(None),
            DeviceCache.cache_valid_until > now,
        )
        .scalar()
    )
    expired_devices = (
        db.query(func.count(DeviceCache.device_id))
        .filter(
            DeviceCache.cache_valid_until.isnot(None),
            DeviceCache.cache_valid_until <= now,
        )
        .scalar()
    )

    # Debug: Show all devices and their expiration times
    try:
        all_devices = db.query(DeviceCache).all()
        logger.info(f"📋 Total devices in cache: {total_devices}")
        for device in all_devices:
            if device.cache_valid_until:
                status = "✅ VALID" if device.cache_valid_until > now else "❌ EXPIRED"
                logger.info(
                    f"  {status} {device.device_name}: valid until {device.cache_valid_until}"
                )
            else:
                logger.info(f"  ⚠️  {device.device_name}: NO EXPIRATION SET")
        logger.info(f"📊 Statistics: {valid_devices} valid, {expired_devices} expired")
    except Exception as e:
        logger.error(f"❌ Error in debug logging: {e}")

    # Polling status
    polling_enabled = (
        db.query(func.count(DeviceCache.device_id))
        .filter(DeviceCache.polling_enabled)
        .scalar()
    )
    polling_disabled = total_devices - polling_enabled

    # Most recently updated
    recent_updates = (
        db.query(DeviceCache).order_by(DeviceCache.last_updated.desc()).limit(5).all()
    )

    # Devices with most interfaces
    top_devices = (
        db.query(
            DeviceCache.device_name,
            func.count(InterfaceCache.id).label("interface_count"),
        )
        .join(InterfaceCache)
        .group_by(DeviceCache.device_id, DeviceCache.device_name)
        .order_by(func.count(InterfaceCache.id).desc())
        .limit(5)
        .all()
    )

    return {
        "total": {
            "devices": total_devices,
            "interfaces": total_interfaces,
            "ip_addresses": total_ips,
            "arp_entries": total_arp,
            "static_routes": total_static_routes,
            "ospf_routes": total_ospf_routes,
            "bgp_routes": total_bgp_routes,
            "mac_table_entries": total_mac_table,
            "cdp_neighbors": total_cdp_neighbors,
            "json_blobs": total_json_blobs,
        },
        "cache_status": {
            "valid": valid_devices,
            "expired": expired_devices,
            "valid_percentage": round(
                (valid_devices / total_devices * 100) if total_devices > 0 else 0, 1
            ),
        },
        "polling": {
            "enabled": polling_enabled,
            "disabled": polling_disabled,
        },
        "recent_updates": [
            {
                "device_id": d.device_id,
                "device_name": d.device_name,
                "last_updated": d.last_updated.isoformat() if d.last_updated else None,
            }
            for d in recent_updates
        ],
        "top_devices": [
            {
                "device_name": name,
                "interface_count": count,
            }
            for name, count in top_devices
        ],
    }


@router.get("/devices/{device_id}", response_model=DeviceCacheResponse)
def get_device_cache(
    device_id: str,
    db: Session = Depends(get_db),
):
    """Get cached device information."""
    device = DeviceCacheService.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found in cache")
    return device


@router.get("/devices/{device_id}/details", response_model=DeviceCacheWithDetails)
def get_device_cache_with_details(
    device_id: str,
    db: Session = Depends(get_db),
):
    """Get cached device information with all related data (interfaces, IPs, ARP)."""
    device = DeviceCacheService.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found in cache")
    return device


@router.get("/devices", response_model=List[DeviceCacheResponse])
def get_all_devices_cache(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    polling_enabled: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """Get all cached devices with optional filtering."""
    devices = DeviceCacheService.get_all_devices(
        db, skip=skip, limit=limit, polling_enabled=polling_enabled
    )
    return devices


@router.get("/devices/by-name/{device_name}", response_model=DeviceCacheResponse)
def get_device_by_name(
    device_name: str,
    db: Session = Depends(get_db),
):
    """Get device by name."""
    device = DeviceCacheService.get_device_by_name(db, device_name)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found in cache")
    return device


@router.get("/devices/by-ip/{ip_address}", response_model=List[DeviceCacheResponse])
def get_devices_by_ip(
    ip_address: str,
    db: Session = Depends(get_db),
):
    """Find which device(s) have a specific IP address."""
    devices = DeviceCacheService.get_devices_by_ip(db, ip_address)
    return devices


@router.get(
    "/interfaces/{device_id}/{interface_name}", response_model=InterfaceCacheResponse
)
def get_interface(
    device_id: str,
    interface_name: str,
    db: Session = Depends(get_db),
):
    """Get interface details by device and interface name."""
    interface = DeviceCacheService.get_interface(db, device_id, interface_name)
    if not interface:
        raise HTTPException(status_code=404, detail="Interface not found in cache")
    return interface


@router.get(
    "/interfaces/by-mac/{mac_address}", response_model=List[InterfaceCacheResponse]
)
def get_interfaces_by_mac(
    mac_address: str,
    db: Session = Depends(get_db),
):
    """Find interfaces by MAC address."""
    interfaces = DeviceCacheService.get_interfaces_by_mac(db, mac_address)
    return interfaces


@router.get("/interfaces/{device_id}", response_model=List[InterfaceCacheResponse])
def get_device_interfaces(
    device_id: str,
    db: Session = Depends(get_db),
):
    """Get all interfaces for a device."""
    device = DeviceCacheService.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found in cache")
    return device.interfaces


@router.get("/ip-addresses/{device_id}", response_model=List[IPAddressCacheResponse])
def get_device_ip_addresses(
    device_id: str,
    db: Session = Depends(get_db),
):
    """Get all IP addresses for a device."""
    device = DeviceCacheService.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found in cache")
    return device.ip_addresses


@router.get("/arp/{device_id}", response_model=List[ARPCacheResponse])
def get_device_arp_entries(
    device_id: str,
    db: Session = Depends(get_db),
):
    """Get all ARP entries for a device."""
    device = DeviceCacheService.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found in cache")
    return device.arp_entries


@router.get("/arp/by-mac/{mac_address}", response_model=List[ARPCacheResponse])
def get_arp_by_mac(
    mac_address: str,
    db: Session = Depends(get_db),
):
    """Find ARP entries by MAC address."""
    entries = DeviceCacheService.get_arp_by_mac(db, mac_address)
    return entries


@router.get("/arp/by-ip/{ip_address}", response_model=List[ARPCacheResponse])
def get_arp_by_ip(
    ip_address: str,
    db: Session = Depends(get_db),
):
    """Find ARP entries by IP address."""
    entries = DeviceCacheService.get_arp_by_ip(db, ip_address)
    return entries


@router.post("/devices/{device_id}/bulk-update", response_model=DeviceCacheResponse)
def bulk_update_device_cache(
    device_id: str,
    cache_data: BulkCacheUpdate,
    cache_ttl_minutes: int = Query(60, ge=1, le=1440),
    db: Session = Depends(get_db),
):
    """
    Bulk update device cache with discovery data.
    This is the main endpoint for populating cache after device discovery.
    """
    if cache_data.device.device_id != device_id:
        raise HTTPException(
            status_code=400,
            detail="Device ID in path must match device ID in request body",
        )

    updated_device = DeviceCacheService.bulk_update_device_cache(
        db, cache_data, cache_ttl_minutes
    )
    return updated_device


@router.put("/devices/{device_id}/polling", response_model=DeviceCacheResponse)
def update_polling_status(
    device_id: str,
    enabled: bool,
    db: Session = Depends(get_db),
):
    """Enable or disable polling for a device."""
    device = DeviceCacheService.update_polling_status(db, device_id, enabled)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found in cache")
    return device


@router.delete("/devices/{device_id}")
def invalidate_device_cache(
    device_id: str,
    db: Session = Depends(get_db),
):
    """Invalidate (delete) device cache."""
    success = DeviceCacheService.invalidate_device_cache(db, device_id)
    if not success:
        raise HTTPException(status_code=404, detail="Device not found in cache")
    return {"message": f"Cache for device {device_id} invalidated"}


@router.delete("/all")
def clear_all_cache(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Clear ALL cache entries (devices and all related data)."""
    import logging

    logger = logging.getLogger(__name__)

    # Count before deletion
    device_count = db.query(func.count(DeviceCache.device_id)).scalar()
    interface_count = db.query(func.count(InterfaceCache.id)).scalar()
    ip_count = db.query(func.count(IPAddressCache.id)).scalar()
    arp_count = db.query(func.count(ARPCache.id)).scalar()
    static_route_count = db.query(func.count(StaticRouteCache.id)).scalar()
    ospf_route_count = db.query(func.count(OSPFRouteCache.id)).scalar()
    bgp_route_count = db.query(func.count(BGPRouteCache.id)).scalar()
    mac_count = db.query(func.count(MACAddressTableCache.id)).scalar()
    cdp_count = db.query(func.count(CDPNeighborCache.id)).scalar()

    total = (
        device_count
        + interface_count
        + ip_count
        + arp_count
        + static_route_count
        + ospf_route_count
        + bgp_route_count
        + mac_count
        + cdp_count
    )

    logger.info(f"🗑️  Clearing ALL cache: {total} total entries")
    print(f"\n🗑️  Clearing ALL cache: {total} total entries")

    # Delete all cache data (cascade will handle related records)
    db.query(DeviceCache).delete()
    db.commit()

    logger.info("✅ All cache cleared successfully")
    print("✅ All cache cleared successfully")

    return {
        "message": "Cleared all cache entries",
        "total_cleared": total,
        "breakdown": {
            "devices": device_count,
            "interfaces": interface_count,
            "ip_addresses": ip_count,
            "arp_entries": arp_count,
            "static_routes": static_route_count,
            "ospf_routes": ospf_route_count,
            "bgp_routes": bgp_route_count,
            "mac_table": mac_count,
            "cdp_neighbors": cdp_count,
        },
    }


@router.delete("/expired")
def clean_all_expired_cache(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Clean all expired cache entries."""
    import logging

    logger = logging.getLogger(__name__)

    # Debug: Check what's in the database before cleaning
    now = datetime.now(timezone.utc)
    all_devices = db.query(DeviceCache).all()
    print(f"\n🧹 Clean endpoint called. Current UTC: {now}")
    print(f"📋 All devices in cache ({len(all_devices)} total):")
    logger.info(f"🧹 Clean endpoint called. Current UTC: {now}")
    logger.info("📋 All devices in cache:")
    for d in all_devices:
        if d.cache_valid_until:
            is_expired = d.cache_valid_until <= now
            msg = f"  {'❌ EXPIRED' if is_expired else '✅ VALID'}: {d.device_name} - valid_until: {d.cache_valid_until}"
            print(msg)
            logger.info(msg)
        else:
            msg = f"  ⚠️  NULL: {d.device_name} - valid_until: None"
            print(msg)
            logger.info(msg)

    count = DeviceCacheService.clean_expired_cache(db, None)
    return {"message": f"Cleaned {count} expired cache entries"}


@router.delete("/devices/{device_id}/expired")
def clean_device_expired_cache(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Clean expired cache entries for a specific device."""
    count = DeviceCacheService.clean_expired_cache(db, device_id)
    return {"message": f"Cleaned {count} expired cache entries for device {device_id}"}


# Routing Cache Endpoints
@router.get("/routes/static", response_model=Dict[str, Any])
def get_static_routes(
    limit: int = 100,
    offset: int = 0,
    device_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get static routes from cache."""
    query = db.query(StaticRouteCache)

    if device_id:
        query = query.filter(StaticRouteCache.device_id == device_id)

    total = query.count()
    routes = (
        query.order_by(StaticRouteCache.last_updated.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "count": total,
        "results": [StaticRouteCacheResponse.model_validate(r) for r in routes],
    }


@router.get("/routes/ospf", response_model=Dict[str, Any])
def get_ospf_routes(
    limit: int = 100,
    offset: int = 0,
    device_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get OSPF routes from cache."""
    query = db.query(OSPFRouteCache)

    if device_id:
        query = query.filter(OSPFRouteCache.device_id == device_id)

    total = query.count()
    routes = (
        query.order_by(OSPFRouteCache.last_updated.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "count": total,
        "results": [OSPFRouteCacheResponse.model_validate(r) for r in routes],
    }


@router.get("/routes/bgp", response_model=Dict[str, Any])
def get_bgp_routes(
    limit: int = 100,
    offset: int = 0,
    device_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get BGP routes from cache."""
    query = db.query(BGPRouteCache)

    if device_id:
        query = query.filter(BGPRouteCache.device_id == device_id)

    total = query.count()
    routes = (
        query.order_by(BGPRouteCache.last_updated.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "count": total,
        "results": [BGPRouteCacheResponse.model_validate(r) for r in routes],
    }


@router.get("/mac-table", response_model=Dict[str, Any])
def get_mac_address_table_cache(
    limit: int = 100,
    offset: int = 0,
    device_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get MAC address table entries from cache."""
    query = db.query(MACAddressTableCache)

    if device_id:
        query = query.filter(MACAddressTableCache.device_id == device_id)

    total = query.count()
    entries = (
        query.order_by(MACAddressTableCache.last_updated.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "count": total,
        "results": [MACAddressTableCacheResponse.model_validate(e) for e in entries],
    }


@router.get("/cdp-neighbors", response_model=Dict[str, Any])
def get_cdp_neighbors_cache(
    limit: int = 100,
    offset: int = 0,
    device_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get CDP neighbor entries from cache."""
    query = db.query(CDPNeighborCache)

    if device_id:
        query = query.filter(CDPNeighborCache.device_id == device_id)

    total = query.count()
    neighbors = (
        query.order_by(CDPNeighborCache.last_updated.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "count": total,
        "results": [CDPNeighborCacheResponse.model_validate(n) for n in neighbors],
    }


@router.get("/json-blobs", response_model=Dict[str, Any])
def get_json_blobs(
    limit: int = 100,
    offset: int = 0,
    device_id: Optional[str] = None,
    command: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get JSON blob cache entries."""
    from app.models.device_cache import JSONBlobCache
    from app.schemas.device_cache import JSONBlobCacheResponse

    query = db.query(JSONBlobCache)

    if device_id:
        query = query.filter(JSONBlobCache.device_id == device_id)

    if command:
        query = query.filter(JSONBlobCache.command == command)

    total = query.count()
    blobs = (
        query.order_by(JSONBlobCache.updated_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "count": total,
        "results": [JSONBlobCacheResponse.model_validate(b) for b in blobs],
    }


# JSON Blob Cache Endpoints
@router.post("/cache/json/{device_id}")
def set_json_cache(
    device_id: str,
    command: str,
    json_data: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Create or update a JSON cache entry for a device command.

    Args:
        device_id: Device UUID
        command: Command that was executed
        json_data: JSON string data to cache

    Returns:
        The created or updated cache entry
    """
    from app.services.json_cache_service import JSONCacheService
    from app.schemas.device_cache import JSONBlobCacheResponse

    try:
        cache_entry = JSONCacheService.set_cache(
            db=db, device_id=device_id, command=command, json_data=json_data
        )

        return JSONBlobCacheResponse.model_validate(cache_entry)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set cache: {str(e)}")


@router.get("/json/{device_id}")
def get_json_cache(
    device_id: str,
    command: Optional[str] = Query(
        None, description="Specific command to retrieve cache for"
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get cached JSON data for a device.

    Args:
        device_id: Device UUID
        command: Optional specific command. If not provided, returns all cache entries for the device.

    Returns:
        Single entry or list of entries
    """
    from app.services.json_cache_service import JSONCacheService
    from app.schemas.device_cache import JSONBlobCacheResponse

    try:
        cache_data = JSONCacheService.get_cache(
            db=db, device_id=device_id, command=command
        )

        if command and cache_data is None:
            raise HTTPException(
                status_code=404,
                detail=f"No cache found for device {device_id} and command '{command}'",
            )

        if not command and (cache_data is None or len(cache_data) == 0):
            raise HTTPException(
                status_code=404, detail=f"No cache entries found for device {device_id}"
            )

        # Return single item or list based on whether command was specified
        if command:
            return JSONBlobCacheResponse.model_validate(cache_data)
        else:
            return [JSONBlobCacheResponse.model_validate(entry) for entry in cache_data]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache: {str(e)}")


@router.delete("/json/{device_id}")
def delete_json_cache(
    device_id: str,
    command: Optional[str] = Query(
        None, description="Specific command to delete cache for"
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Delete cached JSON data for a device.

    Args:
        device_id: Device UUID
        command: Optional specific command. If not provided, deletes all cache entries for the device.

    Returns:
        Success message with count of deleted entries
    """
    from app.services.json_cache_service import JSONCacheService

    try:
        deleted_count = JSONCacheService.delete_cache(
            db=db, device_id=device_id, command=command
        )

        if deleted_count == 0:
            if command:
                raise HTTPException(
                    status_code=404,
                    detail=f"No cache found for device {device_id} and command '{command}'",
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"No cache entries found for device {device_id}",
                )

        return {
            "success": True,
            "message": f"Deleted {deleted_count} cache entry(ies)",
            "deleted_count": deleted_count,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete cache: {str(e)}")


@router.get("/json/devices/list")
def list_cached_devices(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get list of all device IDs that have cached JSON data.

    Returns:
        List of device UUIDs
    """
    from app.services.json_cache_service import JSONCacheService

    try:
        device_ids = JSONCacheService.get_all_cached_devices(db)
        return {"devices": device_ids}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list cached devices: {str(e)}"
        )


@router.get("/json/{device_id}/commands")
def list_cached_commands(
    device_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get list of all cached commands for a device.

    Args:
        device_id: Device UUID

    Returns:
        List of commands that have cached data
    """
    from app.services.json_cache_service import JSONCacheService

    try:
        commands = JSONCacheService.get_cached_commands(db, device_id)
        if not commands:
            raise HTTPException(
                status_code=404,
                detail=f"No cached commands found for device {device_id}",
            )
        return {"commands": commands}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list cached commands: {str(e)}"
        )
