from sqlalchemy import Column, Integer, String, Float, Text, Enum
from ..core.database import Base
import enum


class DeviceType(enum.Enum):
    ROUTER = "router"
    SWITCH = "switch"
    FIREWALL = "firewall"
    VPN_GATEWAY = "vpn_gateway"


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    device_type = Column(Enum(DeviceType), nullable=False)
    ip_address = Column(String)
    position_x = Column(Float, default=0)
    position_y = Column(Float, default=0)
    properties = Column(Text)  # JSON string for additional properties


class Connection(Base):
    __tablename__ = "connections"

    id = Column(Integer, primary_key=True, index=True)
    source_device_id = Column(Integer, nullable=False)
    target_device_id = Column(Integer, nullable=False)
    connection_type = Column(String, default="ethernet")
    properties = Column(Text)  # JSON string for additional properties
