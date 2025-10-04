"""
Pydantic schemas for device cache data.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


# Device Cache Schemas
class DeviceCacheBase(BaseModel):
    device_id: str
    device_name: str
    primary_ip: Optional[str] = None
    platform: Optional[str] = None
    polling_enabled: bool = True


class DeviceCacheCreate(DeviceCacheBase):
    cache_valid_until: Optional[datetime] = None


class DeviceCacheUpdate(BaseModel):
    device_name: Optional[str] = None
    primary_ip: Optional[str] = None
    platform: Optional[str] = None
    polling_enabled: Optional[bool] = None
    cache_valid_until: Optional[datetime] = None


class DeviceCacheResponse(DeviceCacheBase):
    last_updated: datetime
    cache_valid_until: Optional[datetime] = None

    class Config:
        from_attributes = True


# Interface Cache Schemas
class InterfaceCacheBase(BaseModel):
    device_id: str
    interface_name: str
    mac_address: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    speed: Optional[str] = None
    duplex: Optional[str] = None
    vlan_id: Optional[int] = None


class InterfaceCacheCreate(InterfaceCacheBase):
    pass


class InterfaceCacheUpdate(BaseModel):
    mac_address: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    speed: Optional[str] = None
    duplex: Optional[str] = None
    vlan_id: Optional[int] = None


class InterfaceCacheResponse(InterfaceCacheBase):
    id: int
    last_updated: datetime

    class Config:
        from_attributes = True


# IP Address Cache Schemas
class IPAddressCacheBase(BaseModel):
    device_id: str
    interface_name: Optional[str] = None
    ip_address: str
    subnet_mask: Optional[str] = None
    ip_version: int = 4
    is_primary: bool = False


class IPAddressCacheCreate(IPAddressCacheBase):
    interface_id: Optional[int] = None


class IPAddressCacheUpdate(BaseModel):
    subnet_mask: Optional[str] = None
    is_primary: Optional[bool] = None


class IPAddressCacheResponse(IPAddressCacheBase):
    id: int
    interface_id: Optional[int] = None
    last_updated: datetime

    class Config:
        from_attributes = True


# ARP Cache Schemas
class ARPCacheBase(BaseModel):
    device_id: str
    ip_address: str
    mac_address: str
    interface_name: Optional[str] = None
    age: Optional[int] = None
    arp_type: Optional[str] = None


class ARPCacheCreate(ARPCacheBase):
    pass


class ARPCacheUpdate(BaseModel):
    mac_address: Optional[str] = None
    interface_name: Optional[str] = None
    age: Optional[int] = None
    arp_type: Optional[str] = None


class ARPCacheResponse(ARPCacheBase):
    id: int
    last_updated: datetime

    class Config:
        from_attributes = True


# Composite schemas for bulk operations
class DeviceCacheWithDetails(DeviceCacheResponse):
    """Device cache with all related data."""
    interfaces: List[InterfaceCacheResponse] = []
    ip_addresses: List[IPAddressCacheResponse] = []
    arp_entries: List[ARPCacheResponse] = []


class InterfaceWithIPs(InterfaceCacheResponse):
    """Interface with its IP addresses."""
    ip_addresses: List[IPAddressCacheResponse] = []


# Bulk update schemas
class BulkCacheUpdate(BaseModel):
    """For updating entire device cache from discovery."""
    device: DeviceCacheCreate
    interfaces: List[InterfaceCacheCreate] = []
    ip_addresses: List[IPAddressCacheCreate] = []
    arp_entries: List[ARPCacheCreate] = []
