"""
Device cache models for storing network device discovery data.
Phase 1: Device, Interface, IP Address, and ARP cache tables.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class DeviceCache(Base):
    """
    Main device cache table.
    Stores basic device information and cache metadata.
    """
    __tablename__ = "device_cache"

    device_id = Column(String, primary_key=True, index=True)  # Nautobot device UUID
    device_name = Column(String, nullable=False, index=True)
    primary_ip = Column(String)
    platform = Column(String)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    cache_valid_until = Column(DateTime(timezone=True))
    polling_enabled = Column(Boolean, default=True)

    # Relationships
    interfaces = relationship("InterfaceCache", back_populates="device", cascade="all, delete-orphan")
    ip_addresses = relationship("IPAddressCache", back_populates="device", cascade="all, delete-orphan")
    arp_entries = relationship("ARPCache", back_populates="device", cascade="all, delete-orphan")
    static_routes = relationship("StaticRouteCache", back_populates="device", cascade="all, delete-orphan")
    ospf_routes = relationship("OSPFRouteCache", back_populates="device", cascade="all, delete-orphan")
    bgp_routes = relationship("BGPRouteCache", back_populates="device", cascade="all, delete-orphan")
    mac_table_entries = relationship("MACAddressTableCache", back_populates="device", cascade="all, delete-orphan")
    cdp_neighbors = relationship("CDPNeighborCache", back_populates="device", cascade="all, delete-orphan")


class InterfaceCache(Base):
    """
    Interface cache table.
    Stores interface details including MAC addresses and status.
    """
    __tablename__ = "interface_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey("device_cache.device_id", ondelete="CASCADE"), nullable=False)
    interface_name = Column(String, nullable=False)
    mac_address = Column(String, index=True)  # Indexed for reverse MAC lookups
    status = Column(String)  # up/down/admin-down
    description = Column(String)
    speed = Column(String)
    duplex = Column(String)
    vlan_id = Column(Integer)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    device = relationship("DeviceCache", back_populates="interfaces")
    ip_addresses = relationship("IPAddressCache", back_populates="interface", cascade="all, delete-orphan")

    # Unique constraint: one entry per device + interface
    __table_args__ = (
        Index('ix_interface_device_name', 'device_id', 'interface_name', unique=True),
    )


class IPAddressCache(Base):
    """
    IP address cache table.
    Stores IP addresses assigned to interfaces.
    """
    __tablename__ = "ip_address_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey("device_cache.device_id", ondelete="CASCADE"), nullable=False)
    interface_id = Column(Integer, ForeignKey("interface_cache.id", ondelete="CASCADE"))
    interface_name = Column(String)  # Denormalized for easier queries
    ip_address = Column(String, nullable=False, index=True)  # Indexed for "which device has this IP" queries
    subnet_mask = Column(String)
    ip_version = Column(Integer, default=4)  # 4 or 6
    is_primary = Column(Boolean, default=False)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    device = relationship("DeviceCache", back_populates="ip_addresses")
    interface = relationship("InterfaceCache", back_populates="ip_addresses")

    # Indexes for common queries
    __table_args__ = (
        Index('ix_ip_device_interface', 'device_id', 'interface_name'),
    )


class ARPCache(Base):
    """
    ARP cache table.
    Stores ARP entries from devices.
    """
    __tablename__ = "arp_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey("device_cache.device_id", ondelete="CASCADE"), nullable=False)
    ip_address = Column(String, nullable=False, index=True)
    mac_address = Column(String, nullable=False, index=True)  # Indexed for MAC lookups
    interface_name = Column(String)
    age = Column(Integer)  # Age in minutes/seconds (depends on device output)
    arp_type = Column(String)  # ARPA, etc.
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    device = relationship("DeviceCache", back_populates="arp_entries")

    # Indexes for common queries
    __table_args__ = (
        Index('ix_arp_device_ip', 'device_id', 'ip_address'),
    )


class StaticRouteCache(Base):
    """
    Static route cache table.
    Stores static routes from devices.
    """
    __tablename__ = "static_route_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey("device_cache.device_id", ondelete="CASCADE"), nullable=False)
    network = Column(String, nullable=False, index=True)  # Destination network (e.g., "10.0.0.0/24")
    nexthop_ip = Column(String, index=True)  # Next hop IP address
    metric = Column(Integer)
    distance = Column(Integer)  # Administrative distance
    interface_name = Column(String)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    device = relationship("DeviceCache", back_populates="static_routes")

    # Indexes for common queries
    __table_args__ = (
        Index('ix_static_route_device_network', 'device_id', 'network'),
    )


class OSPFRouteCache(Base):
    """
    OSPF route cache table.
    Stores OSPF routes from devices.
    """
    __tablename__ = "ospf_route_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey("device_cache.device_id", ondelete="CASCADE"), nullable=False)
    network = Column(String, nullable=False, index=True)  # Destination network
    nexthop_ip = Column(String, index=True)  # Next hop IP address
    metric = Column(Integer)
    distance = Column(Integer)  # Administrative distance
    interface_name = Column(String)
    area = Column(String)  # OSPF area
    route_type = Column(String)  # O, O IA, O E1, O E2, etc.
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    device = relationship("DeviceCache", back_populates="ospf_routes")

    # Indexes for common queries
    __table_args__ = (
        Index('ix_ospf_route_device_network', 'device_id', 'network'),
    )


class BGPRouteCache(Base):
    """
    BGP route cache table.
    Stores BGP routes from devices.
    """
    __tablename__ = "bgp_route_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey("device_cache.device_id", ondelete="CASCADE"), nullable=False)
    network = Column(String, nullable=False, index=True)  # Destination network
    nexthop_ip = Column(String, index=True)  # Next hop IP address
    metric = Column(Integer)
    local_pref = Column(Integer)  # Local preference
    weight = Column(Integer)
    as_path = Column(String)  # AS path
    origin = Column(String)  # IGP, EGP, incomplete
    status = Column(String)  # Valid, best, etc.
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    device = relationship("DeviceCache", back_populates="bgp_routes")

    # Indexes for common queries
    __table_args__ = (
        Index('ix_bgp_route_device_network', 'device_id', 'network'),
    )


class MACAddressTableCache(Base):
    """
    MAC address table cache.
    Stores MAC address table entries from switches.
    """
    __tablename__ = "mac_address_table_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey("device_cache.device_id", ondelete="CASCADE"), nullable=False)
    mac_address = Column(String, nullable=False, index=True)  # MAC address
    vlan_id = Column(Integer, index=True)  # VLAN ID
    interface_name = Column(String, index=True)  # Interface/port
    entry_type = Column(String)  # Dynamic, Static, etc.
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    device = relationship("DeviceCache", back_populates="mac_table_entries")

    # Indexes for common queries
    __table_args__ = (
        Index('ix_mac_table_device_mac', 'device_id', 'mac_address'),
        Index('ix_mac_table_device_vlan', 'device_id', 'vlan_id'),
    )


class CDPNeighborCache(Base):
    """
    CDP neighbor cache table.
    Stores CDP/LLDP neighbor information from devices.
    """
    __tablename__ = "cdp_neighbor_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey("device_cache.device_id", ondelete="CASCADE"), nullable=False)
    neighbor_name = Column(String, nullable=False, index=True)  # Neighbor device name
    neighbor_ip = Column(String, index=True)  # Neighbor IP address
    local_interface = Column(String, nullable=False, index=True)  # Local interface
    neighbor_interface = Column(String)  # Neighbor's interface
    platform = Column(String)  # Neighbor platform
    capabilities = Column(String)  # Neighbor capabilities
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    device = relationship("DeviceCache", back_populates="cdp_neighbors")

    # Indexes for common queries
    __table_args__ = (
        Index('ix_cdp_device_neighbor', 'device_id', 'neighbor_name'),
        Index('ix_cdp_device_interface', 'device_id', 'local_interface'),
    )
