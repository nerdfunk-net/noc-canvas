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
