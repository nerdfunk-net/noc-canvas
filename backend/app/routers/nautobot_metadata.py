"""
Nautobot Metadata Router
Handles metadata endpoints (locations, roles, platforms, statuses, etc.)
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from pydantic import BaseModel
import logging
from ..api.auth import get_current_user
from ..services.nautobot import nautobot_service
from ..queries.nautobot_queries import NAMESPACES_QUERY, SECRET_GROUPS_QUERY

router = APIRouter()
logger = logging.getLogger(__name__)


# Pydantic Models
class Location(BaseModel):
    id: str
    name: str
    description: str = ""


class NautobotStats(BaseModel):
    total_devices: int
    total_locations: int
    total_roles: int


class NautobotNamespace(BaseModel):
    id: str
    name: str
    description: str = ""


class NautobotRole(BaseModel):
    id: str
    name: str
    description: str = ""


class NautobotPlatform(BaseModel):
    id: str
    name: str
    network_driver: str = ""


class NautobotStatus(BaseModel):
    id: str
    name: str
    description: str = ""


class NautobotSecretGroup(BaseModel):
    id: str
    name: str


# Helper Functions
def get_username(current_user: dict) -> str:
    """Extract username from current user"""
    if isinstance(current_user, dict):
        return current_user.get("username", "unknown")
    return getattr(current_user, "username", "unknown")


@router.get("/locations", response_model=List[Location])
async def get_locations(
    current_user: dict = Depends(get_current_user),
):
    """Get list of locations from Nautobot."""
    try:
        username = get_username(current_user)
        locations = await nautobot_service.get_locations(username=username)
        return [Location(**location) for location in locations]
    except Exception as e:
        logger.error(f"Error fetching locations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch locations: {str(e)}",
        )


@router.get("/stats", response_model=NautobotStats)
async def get_nautobot_stats(
    current_user: dict = Depends(get_current_user),
):
    """Get Nautobot statistics."""
    try:
        username = get_username(current_user)
        stats = await nautobot_service.get_stats(username=username)
        return NautobotStats(**stats)
    except Exception as e:
        logger.error(f"Error fetching Nautobot stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch statistics: {str(e)}",
        )


@router.get("/namespaces", response_model=List[NautobotNamespace])
async def get_namespaces(
    current_user: dict = Depends(get_current_user),
):
    """Get list of namespaces from Nautobot."""
    try:
        username = get_username(current_user)
        result = await nautobot_service.graphql_query(
            NAMESPACES_QUERY, username=username
        )

        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")

        namespaces = result["data"]["namespaces"]
        return [NautobotNamespace(**ns) for ns in namespaces]
    except Exception as e:
        logger.error(f"Error fetching namespaces: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch namespaces: {str(e)}",
        )


@router.get("/roles", response_model=List[NautobotRole])
async def get_nautobot_roles(
    current_user: dict = Depends(get_current_user),
):
    """Get Nautobot device roles."""
    try:
        username = get_username(current_user)
        result = await nautobot_service.rest_request("extras/roles/", username=username)
        roles = result.get("results", [])
        return [NautobotRole(**role) for role in roles]
    except Exception as e:
        logger.error(f"Error fetching roles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch roles: {str(e)}",
        )


@router.get("/roles/devices", response_model=List[NautobotRole])
async def get_nautobot_device_roles(
    current_user: dict = Depends(get_current_user),
):
    """Get Nautobot roles specifically for dcim.device content type."""
    try:
        username = get_username(current_user)
        result = await nautobot_service.rest_request(
            "extras/roles/?content_types=dcim.device", username=username
        )
        roles = result.get("results", [])
        return [NautobotRole(**role) for role in roles]
    except Exception as e:
        logger.error(f"Error fetching device roles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch device roles: {str(e)}",
        )


@router.get("/platforms", response_model=List[NautobotPlatform])
async def get_nautobot_platforms(
    current_user: dict = Depends(get_current_user),
):
    """Get Nautobot platforms."""
    try:
        username = get_username(current_user)
        result = await nautobot_service.rest_request(
            "dcim/platforms/", username=username
        )
        platforms = result.get("results", [])
        return [NautobotPlatform(**platform) for platform in platforms]
    except Exception as e:
        logger.error(f"Error fetching platforms: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch platforms: {str(e)}",
        )


@router.get("/statuses", response_model=List[NautobotStatus])
async def get_nautobot_statuses(
    current_user: dict = Depends(get_current_user),
):
    """Get all Nautobot statuses."""
    try:
        username = get_username(current_user)
        result = await nautobot_service.rest_request(
            "extras/statuses/", username=username
        )
        statuses = result.get("results", [])
        return [NautobotStatus(**status) for status in statuses]
    except Exception as e:
        logger.error(f"Error fetching statuses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch statuses: {str(e)}",
        )


@router.get("/statuses/device", response_model=List[NautobotStatus])
async def get_nautobot_device_statuses(
    current_user: dict = Depends(get_current_user),
):
    """Get Nautobot device statuses."""
    try:
        username = get_username(current_user)
        result = await nautobot_service.rest_request(
            "extras/statuses/?content_types=dcim.device", username=username
        )
        statuses = result.get("results", [])
        return [NautobotStatus(**status) for status in statuses]
    except Exception as e:
        logger.error(f"Error fetching device statuses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch device statuses: {str(e)}",
        )


@router.get("/secret-groups", response_model=List[NautobotSecretGroup])
async def get_nautobot_secret_groups(
    current_user: dict = Depends(get_current_user),
):
    """Get Nautobot secret groups."""
    try:
        username = get_username(current_user)
        result = await nautobot_service.graphql_query(
            SECRET_GROUPS_QUERY, username=username
        )

        if "errors" in result:
            logger.warning(f"GraphQL errors fetching secret groups: {result['errors']}")
            return []

        secret_groups = result["data"]["secrets_groups"]
        return [NautobotSecretGroup(**group) for group in secret_groups]
    except Exception as e:
        logger.warning(f"Secret groups endpoint not available: {str(e)}")
        return []
