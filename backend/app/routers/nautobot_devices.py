"""
Nautobot Devices Router
Handles device-related API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
import requests
from sqlalchemy.orm import Session
from ..core.config import settings
from ..core.database import get_db
from ..core.dynamic_settings import get_nautobot_config
from ..api.auth import get_current_user
from ..models.user import User
from ..queries.nautobot_queries import COMPLETE_DEVICE_DATA_QUERY, DEVICE_DETAILS_QUERY

router = APIRouter()


# Pydantic Models
class Device(BaseModel):
    id: str
    name: str
    device_type: Optional[dict] = None
    role: Optional[dict] = None
    platform: Optional[dict] = None
    location: Optional[dict] = None
    status: Optional[dict] = None
    primary_ip4: Optional[dict] = None
    cf_last_backup: Optional[str] = None


class DeviceListResponse(BaseModel):
    devices: List[Device]
    count: int
    has_more: bool = False
    is_paginated: bool = True
    current_offset: int = 0
    current_limit: int = 10000
    next: Optional[str] = None
    previous: Optional[str] = None


class DeviceType(BaseModel):
    id: str
    model: str
    manufacturer: dict


class DeviceTypeListResponse(BaseModel):
    device_types: List[DeviceType]
    count: int


# Helper Functions
def get_username(current_user: User = Depends(get_current_user)) -> str:
    """Extract username from current user"""
    return current_user.username


@router.get("/devices", response_model=DeviceListResponse)
async def get_devices(
    limit: Optional[int] = 10000,
    offset: Optional[int] = 0,
    location: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all devices from Nautobot with optional filters"""
    # Load Nautobot config from database with env fallback
    nautobot_config = get_nautobot_config(db)

    if not nautobot_config["url"] or not nautobot_config["token"]:
        raise HTTPException(status_code=500, detail="Nautobot configuration missing")

    url = f"{nautobot_config['url']}/api/dcim/devices/"
    headers = {
        "Authorization": f"Token {nautobot_config['token']}",
        "Content-Type": "application/json",
    }

    params = {"limit": limit, "offset": offset}
    if location:
        params["location"] = location
    if role:
        params["role"] = role
    if status:
        params["status"] = status

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        devices = [Device(**device) for device in data.get("results", [])]

        return DeviceListResponse(
            devices=devices,
            count=data.get("count", len(devices)),
            has_more=bool(data.get("next")),
            is_paginated=True,
            current_offset=offset,
            current_limit=limit,
            next=data.get("next"),
            previous=data.get("previous"),
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch devices: {str(e)}")


@router.get("/devices/{device_id}", response_model=Device)
async def get_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific device by ID from Nautobot"""
    nautobot_config = get_nautobot_config(db)

    if not nautobot_config["url"] or not nautobot_config["token"]:
        raise HTTPException(status_code=500, detail="Nautobot configuration missing")

    url = f"{nautobot_config['url']}/api/dcim/devices/{device_id}/"
    headers = {
        "Authorization": f"Token {nautobot_config['token']}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return Device(**response.json())
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch device: {str(e)}")


@router.get("/devices/{device_id}/nautobot-data")
async def get_device_nautobot_data(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get complete device data from Nautobot using GraphQL"""
    nautobot_config = get_nautobot_config(db)

    if not nautobot_config["url"] or not nautobot_config["token"]:
        raise HTTPException(status_code=500, detail="Nautobot configuration missing")

    graphql_url = f"{nautobot_config['url']}/api/graphql/"
    headers = {
        "Authorization": f"Token {nautobot_config['token']}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            graphql_url,
            json={"query": COMPLETE_DEVICE_DATA_QUERY, "variables": {"device_id": device_id}},
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            raise HTTPException(status_code=400, detail=data["errors"])

        return data.get("data", {}).get("device", {})
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch device data: {str(e)}")


@router.get("/devices/{device_id}/details")
async def get_device_details(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed device information using GraphQL"""
    nautobot_config = get_nautobot_config(db)

    if not nautobot_config["url"] or not nautobot_config["token"]:
        raise HTTPException(status_code=500, detail="Nautobot configuration missing")

    graphql_url = f"{nautobot_config['url']}/api/graphql/"
    headers = {
        "Authorization": f"Token {nautobot_config['token']}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            graphql_url,
            json={"query": DEVICE_DETAILS_QUERY, "variables": {"deviceId": device_id}},
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            raise HTTPException(status_code=400, detail=data["errors"])

        return data.get("data", {}).get("device", {})
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch device details: {str(e)}")


@router.post("/devices/search", response_model=DeviceListResponse)
async def search_devices(
    name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search for devices by name"""
    nautobot_config = get_nautobot_config(db)
    if not nautobot_config["url"] or not nautobot_config["token"]:
        raise HTTPException(status_code=500, detail="Nautobot configuration missing")

    url = f"{nautobot_config['url']}/api/dcim/devices/"
    headers = {
        "Authorization": f"Token {nautobot_config['token']}",
        "Content-Type": "application/json",
    }

    params = {}
    if name:
        params["name__ic"] = name  # Case-insensitive contains

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        devices = [Device(**device) for device in data.get("results", [])]

        return DeviceListResponse(
            devices=devices,
            count=data.get("count", len(devices)),
            has_more=bool(data.get("next")),
            is_paginated=True,
            current_offset=0,
            current_limit=10000,
            next=data.get("next"),
            previous=data.get("previous"),
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to search devices: {str(e)}")


@router.get("/device-types", response_model=DeviceTypeListResponse)
async def get_device_types(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get all device types from Nautobot"""
    nautobot_config = get_nautobot_config(db)
    if not nautobot_config["url"] or not nautobot_config["token"]:
        raise HTTPException(status_code=500, detail="Nautobot configuration missing")

    url = f"{nautobot_config['url']}/api/dcim/device-types/"
    headers = {
        "Authorization": f"Token {nautobot_config['token']}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, params={"limit": 10000}, timeout=30)
        response.raise_for_status()
        data = response.json()

        device_types = [DeviceType(**dt) for dt in data.get("results", [])]

        return DeviceTypeListResponse(device_types=device_types, count=len(device_types))
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch device types: {str(e)}")
