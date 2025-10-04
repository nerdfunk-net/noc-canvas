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


# Static Route Cache Schemas
class StaticRouteCacheBase(BaseModel):
    device_id: str
    network: str
    nexthop_ip: Optional[str] = None
    metric: Optional[int] = None
    distance: Optional[int] = None
    interface_name: Optional[str] = None


class StaticRouteCacheCreate(StaticRouteCacheBase):
    pass


class StaticRouteCacheResponse(StaticRouteCacheBase):
    id: int
    last_updated: datetime

    class Config:
        from_attributes = True


# OSPF Route Cache Schemas
class OSPFRouteCacheBase(BaseModel):
    device_id: str
    network: str
    nexthop_ip: Optional[str] = None
    metric: Optional[int] = None
    distance: Optional[int] = None
    interface_name: Optional[str] = None
    area: Optional[str] = None
    route_type: Optional[str] = None


class OSPFRouteCacheCreate(OSPFRouteCacheBase):
    pass


class OSPFRouteCacheResponse(OSPFRouteCacheBase):
    id: int
    last_updated: datetime

    class Config:
        from_attributes = True


# BGP Route Cache Schemas
class BGPRouteCacheBase(BaseModel):
    device_id: str
    network: str
    nexthop_ip: Optional[str] = None
    metric: Optional[int] = None
    local_pref: Optional[int] = None
    weight: Optional[int] = None
    as_path: Optional[str] = None
    origin: Optional[str] = None
    status: Optional[str] = None


class BGPRouteCacheCreate(BGPRouteCacheBase):
    pass


class BGPRouteCacheResponse(BGPRouteCacheBase):
    id: int
    last_updated: datetime

    class Config:
        from_attributes = True


# MAC Address Table Cache Schemas
class MACAddressTableCacheBase(BaseModel):
    device_id: str
    mac_address: str
    vlan_id: Optional[int] = None
    interface_name: Optional[str] = None
    entry_type: Optional[str] = None


class MACAddressTableCacheCreate(MACAddressTableCacheBase):
    pass


class MACAddressTableCacheResponse(MACAddressTableCacheBase):
    id: int
    last_updated: datetime

    class Config:
        from_attributes = True


# CDP Neighbor Cache Schemas
class CDPNeighborCacheBase(BaseModel):
    device_id: str
    neighbor_name: str
    neighbor_ip: Optional[str] = None
    local_interface: str
    neighbor_interface: Optional[str] = None
    platform: Optional[str] = None
    capabilities: Optional[str] = None


class CDPNeighborCacheCreate(CDPNeighborCacheBase):
    pass


class CDPNeighborCacheResponse(CDPNeighborCacheBase):
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
    static_routes: List[StaticRouteCacheResponse] = []
    ospf_routes: List[OSPFRouteCacheResponse] = []
    bgp_routes: List[BGPRouteCacheResponse] = []
    mac_table_entries: List[MACAddressTableCacheResponse] = []
    cdp_neighbors: List[CDPNeighborCacheResponse] = []


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
