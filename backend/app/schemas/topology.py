"""
Topology schemas for network topology builder.
Defines data models for nodes, links, and graphs.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum


class LinkType(str, Enum):
    """Types of topology links."""
    CDP_NEIGHBOR = "cdp_neighbor"
    LLDP_NEIGHBOR = "lldp_neighbor"
    STATIC_ROUTE = "static_route"
    OSPF_ROUTE = "ospf_route"
    BGP_ROUTE = "bgp_route"
    ARP_DISCOVERED = "arp_discovered"
    MAC_TABLE = "mac_table"


class TopologyNode(BaseModel):
    """Represents a device node in the topology."""
    device_id: str
    device_name: str
    primary_ip: Optional[str] = None
    platform: Optional[str] = None
    device_type: Optional[str] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class TopologyLink(BaseModel):
    """Represents a connection between two devices."""
    source_device_id: str
    target_device_id: str
    source_device_name: str
    target_device_name: str
    source_interface: Optional[str] = None
    target_interface: Optional[str] = None
    link_type: LinkType
    bidirectional: bool = False
    link_metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class TopologyGraph(BaseModel):
    """Complete topology graph with nodes and links."""
    nodes: List[TopologyNode]
    links: List[TopologyLink]
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class TopologyStatistics(BaseModel):
    """Statistics about the topology."""
    total_devices: int
    total_links: int
    link_types_breakdown: Dict[str, int]
    devices_by_platform: Dict[str, int]
    isolated_devices: int  # Devices with no links
    average_connections_per_device: float


class TopologyBuildRequest(BaseModel):
    """Request parameters for building topology."""
    device_ids: Optional[List[str]] = None
    include_cdp: bool = True
    include_routing: bool = False
    route_types: List[str] = ["static", "ospf", "bgp"]
    include_layer2: bool = False
    auto_layout: bool = True
    layout_algorithm: Optional[str] = "force_directed"  # force_directed, hierarchical, circular


class NeighborResolution(BaseModel):
    """Result of neighbor name/IP resolution."""
    neighbor_name: str
    neighbor_ip: Optional[str]
    device_id: Optional[str]
    device_name: Optional[str]
    matched_by: Optional[str]  # "name", "ip", "both", "none"
    confidence: str  # "high", "medium", "low"


class TopologyDiscoveryRequest(BaseModel):
    """Request for topology discovery."""
    device_ids: List[str]
    include_static_routes: bool = True
    include_ospf_routes: bool = True
    include_bgp_routes: bool = True
    include_mac_table: bool = True
    include_cdp_neighbors: bool = True
    include_arp: bool = True
    include_interfaces: bool = True
    run_in_background: bool = False
    cache_results: bool = True


class DeviceDiscoveryProgress(BaseModel):
    """Progress for a single device discovery."""
    device_id: str
    device_name: str
    status: str  # "pending", "in_progress", "completed", "failed"
    progress_percentage: int
    current_task: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class TopologyDiscoveryProgress(BaseModel):
    """Overall topology discovery progress."""
    job_id: str
    status: str  # "pending", "in_progress", "completed", "failed"
    total_devices: int
    completed_devices: int
    failed_devices: int
    progress_percentage: int
    devices: List[DeviceDiscoveryProgress]
    started_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None


class TopologyDiscoveryResult(BaseModel):
    """Result of topology discovery."""
    job_id: str
    status: str
    total_devices: int
    successful_devices: int
    failed_devices: int
    devices_data: Dict[str, Any]  # device_id -> discovery data
    errors: Dict[str, str]  # device_id -> error message
    duration_seconds: float
