"""
API endpoints for device cache operations.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.schemas.device_cache import (
    DeviceCacheResponse,
    InterfaceCacheResponse,
    IPAddressCacheResponse,
    ARPCacheResponse,
    BulkCacheUpdate,
    DeviceCacheWithDetails,
)
from app.services.device_cache_service import DeviceCacheService
from app.models.device_cache import DeviceCache, InterfaceCache, IPAddressCache, ARPCache

router = APIRouter(prefix="/cache", tags=["cache"])


@router.get("/statistics")
def get_cache_statistics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get cache statistics and overview."""
    now = datetime.utcnow()

    # Total counts
    total_devices = db.query(func.count(DeviceCache.device_id)).scalar()
    total_interfaces = db.query(func.count(InterfaceCache.id)).scalar()
    total_ips = db.query(func.count(IPAddressCache.id)).scalar()
    total_arp = db.query(func.count(ARPCache.id)).scalar()

    # Valid vs expired cache entries
    valid_devices = db.query(func.count(DeviceCache.device_id)).filter(
        DeviceCache.cache_valid_until > now
    ).scalar()
    expired_devices = total_devices - valid_devices

    # Polling status
    polling_enabled = db.query(func.count(DeviceCache.device_id)).filter(
        DeviceCache.polling_enabled == True
    ).scalar()
    polling_disabled = total_devices - polling_enabled

    # Most recently updated
    recent_updates = db.query(DeviceCache).order_by(
        DeviceCache.last_updated.desc()
    ).limit(5).all()

    # Devices with most interfaces
    top_devices = db.query(
        DeviceCache.device_name,
        func.count(InterfaceCache.id).label('interface_count')
    ).join(InterfaceCache).group_by(
        DeviceCache.device_id, DeviceCache.device_name
    ).order_by(
        func.count(InterfaceCache.id).desc()
    ).limit(5).all()

    return {
        "total": {
            "devices": total_devices,
            "interfaces": total_interfaces,
            "ip_addresses": total_ips,
            "arp_entries": total_arp,
        },
        "cache_status": {
            "valid": valid_devices,
            "expired": expired_devices,
            "valid_percentage": round((valid_devices / total_devices * 100) if total_devices > 0 else 0, 1),
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


@router.get("/interfaces/{device_id}/{interface_name}", response_model=InterfaceCacheResponse)
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


@router.get("/interfaces/by-mac/{mac_address}", response_model=List[InterfaceCacheResponse])
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
            detail="Device ID in path must match device ID in request body"
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


@router.delete("/expired")
def clean_all_expired_cache(
    db: Session = Depends(get_db),
):
    """Clean all expired cache entries."""
    count = DeviceCacheService.clean_expired_cache(db, None)
    return {"message": f"Cleaned {count} expired cache entries"}


@router.delete("/devices/{device_id}/expired")
def clean_device_expired_cache(
    device_id: str,
    db: Session = Depends(get_db),
):
    """Clean expired cache entries for a specific device."""
    count = DeviceCacheService.clean_expired_cache(db, device_id)
    return {"message": f"Cleaned {count} expired cache entries for device {device_id}"}
