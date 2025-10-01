"""
Nautobot data models for API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# Request Models


class DeviceFilter(BaseModel):
    """Device filtering options."""

    limit: Optional[int] = None
    offset: Optional[int] = None
    filter_type: Optional[str] = None  # 'name', 'location', 'prefix'
    filter_value: Optional[str] = None
    disable_cache: bool = False


class CheckIPRequest(BaseModel):
    """IP address availability check request."""

    ip_address: str = Field(..., description="IP address to check")


class DeviceOnboardRequest(BaseModel):
    """Device onboarding request."""

    location_id: str = Field(..., description="Nautobot location ID")
    ip_address: str = Field(..., description="Device IP address")
    secret_groups_id: Optional[str] = Field(None, description="Secret groups ID")
    role_id: str = Field(..., description="Device role ID")
    namespace_id: str = Field(..., description="IP namespace ID")
    status_id: str = Field(..., description="Device status ID")
    interface_status_id: str = Field(..., description="Interface status ID")
    ip_address_status_id: str = Field(..., description="IP address status ID")
    platform_id: Optional[str] = Field("detect", description="Platform ID or 'detect'")
    port: int = Field(22, description="SSH port")
    timeout: int = Field(30, description="Connection timeout")


class SyncNetworkDataRequest(BaseModel):
    """Network data synchronization request."""

    data: Dict[str, Any] = Field(..., description="Sync configuration data")


# Response Models


class DeviceRole(BaseModel):
    """Device role information."""

    name: str


class DeviceLocation(BaseModel):
    """Device location information."""

    name: str


class DeviceIP(BaseModel):
    """Device IP address information."""

    address: str


class DeviceStatus(BaseModel):
    """Device status information."""

    name: str


class DeviceType(BaseModel):
    """Device type information."""

    model: str


class DevicePlatform(BaseModel):
    """Device platform information."""

    id: Optional[str] = None
    network_driver: Optional[str] = None


class Device(BaseModel):
    """Device information from Nautobot."""

    id: str
    name: str
    role: Optional[DeviceRole] = None
    location: Optional[DeviceLocation] = None
    primary_ip4: Optional[DeviceIP] = None
    status: Optional[DeviceStatus] = None
    device_type: Optional[DeviceType] = None
    platform: Optional[DevicePlatform] = None
    cf_last_backup: Optional[str] = None


class DeviceListResponse(BaseModel):
    """Device list response with pagination."""

    devices: List[Device]
    count: int
    has_more: bool
    is_paginated: bool
    current_offset: int
    current_limit: Optional[int]
    next: Optional[str]
    previous: Optional[str]


class LocationParent(BaseModel):
    """Location parent information."""

    id: str
    name: str
    description: Optional[str] = None


class LocationChild(BaseModel):
    """Location child information."""

    id: str
    name: str
    description: Optional[str] = None


class Location(BaseModel):
    """Location information."""

    id: str
    name: str
    description: Optional[str] = None
    parent: Optional[LocationParent] = None
    children: Optional[List[LocationChild]] = None


class NautobotStats(BaseModel):
    """Nautobot statistics."""

    devices: int
    locations: int
    device_types: int
    ip_addresses: int
    prefixes: int
    timestamp: str
    # Backward compatibility
    total_devices: int
    total_locations: int
    total_device_types: int


class IPAddressDevice(BaseModel):
    """Device information for IP address check."""

    name: str


class IPAddressCheck(BaseModel):
    """IP address availability check result."""

    ip_address: str
    is_available: bool
    exists: bool
    is_assigned_to_device: bool
    assigned_devices: List[IPAddressDevice]
    existing_records: List[Dict[str, Any]]
    details: List[Dict[str, Any]]  # Backward compatibility


class OnboardingJob(BaseModel):
    """Device onboarding job result."""

    id: Optional[str] = None
    status: str = "pending"


class OnboardingResponse(BaseModel):
    """Device onboarding response."""

    success: bool
    message: str
    job_id: Optional[str] = None
    job_status: str = "pending"
    device_data: Dict[str, Any]
    nautobot_response: Optional[Dict[str, Any]] = None
    status_code: Optional[int] = None
    response_body: Optional[str] = None


class SyncJob(BaseModel):
    """Network data sync job result."""

    id: Optional[str] = None
    status: str = "pending"


class SyncResponse(BaseModel):
    """Network data sync response."""

    success: bool
    message: str
    job_id: Optional[str] = None
    job_status: str = "pending"
    nautobot_response: Optional[Dict[str, Any]] = None
    status_code: Optional[int] = None


class NautobotResource(BaseModel):
    """Generic Nautobot resource."""

    id: str
    name: str
    description: Optional[str] = None


class NautobotRole(NautobotResource):
    """Nautobot role."""

    pass


class NautobotPlatform(NautobotResource):
    """Nautobot platform."""

    pass


class NautobotStatus(NautobotResource):
    """Nautobot status."""

    pass


class NautobotManufacturer(NautobotResource):
    """Nautobot manufacturer."""

    pass


class NautobotDeviceType(NautobotResource):
    """Nautobot device type."""

    model: str


class NautobotTag(NautobotResource):
    """Nautobot tag."""

    pass


class NautobotCustomField(NautobotResource):
    """Nautobot custom field."""

    type: str
    required: bool


class NautobotNamespace(NautobotResource):
    """Nautobot namespace."""

    pass


class NautobotSecretGroup(BaseModel):
    """Nautobot secret group."""

    id: str
    name: str


class HealthCheckResponse(BaseModel):
    """Nautobot health check response."""

    status: str
    message: str
    devices_count: Optional[int] = None


class ConnectionTestResponse(BaseModel):
    """Nautobot connection test response."""

    success: bool
    message: str
    nautobot_url: str
    connection_source: str = "manual_test"
