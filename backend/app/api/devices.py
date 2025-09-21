from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..core.database import get_db
from ..models.device import Device, Connection, DeviceType
from ..api.auth import get_current_user
from ..models.user import User

router = APIRouter()


class DeviceCreate(BaseModel):
    name: str
    device_type: DeviceType
    ip_address: Optional[str] = None
    position_x: float = 0
    position_y: float = 0
    properties: Optional[str] = None


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    properties: Optional[str] = None


class DeviceResponse(BaseModel):
    id: int
    name: str
    device_type: DeviceType
    ip_address: Optional[str] = None
    position_x: float
    position_y: float
    properties: Optional[str] = None


class ConnectionCreate(BaseModel):
    source_device_id: int
    target_device_id: int
    connection_type: str = "ethernet"
    properties: Optional[str] = None


class ConnectionResponse(BaseModel):
    id: int
    source_device_id: int
    target_device_id: int
    connection_type: str
    properties: Optional[str] = None


@router.get("/", response_model=List[DeviceResponse])
async def get_devices(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    devices = db.query(Device).all()
    return devices


@router.post("/", response_model=DeviceResponse)
async def create_device(
    device: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_device = Device(**device.dict())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_update: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    for field, value in device_update.dict(exclude_unset=True).items():
        setattr(device, field, value)

    db.commit()
    db.refresh(device)
    return device


@router.delete("/{device_id}")
async def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    db.delete(device)
    db.commit()
    return {"message": "Device deleted successfully"}


@router.get("/connections", response_model=List[ConnectionResponse])
async def get_connections(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    connections = db.query(Connection).all()
    return connections


@router.post("/connections", response_model=ConnectionResponse)
async def create_connection(
    connection: ConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_connection = Connection(**connection.dict())
    db.add(db_connection)
    db.commit()
    db.refresh(db_connection)
    return db_connection
