"""
Nautobot API router for device management and API interactions.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from ..core.security import get_current_user, verify_admin_user
from ..models.nautobot import (
    DeviceFilter,
    DeviceListResponse,
    Device,
    CheckIPRequest,
    IPAddressCheck,
    DeviceOnboardRequest,
    OnboardingResponse,
    SyncNetworkDataRequest,
    SyncResponse,
    Location,
    NautobotStats,
    HealthCheckResponse,
    ConnectionTestResponse,
    NautobotRole,
    NautobotPlatform,
    NautobotStatus,
    NautobotManufacturer,
    NautobotDeviceType,
    NautobotTag,
    NautobotCustomField,
    NautobotNamespace,
    NautobotSecretGroup,
)
from ..services.nautobot import nautobot_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/test", response_model=ConnectionTestResponse)
async def test_nautobot_connection(
    current_user: dict = Depends(verify_admin_user),
):
    """Test current Nautobot connection using configured settings."""
    try:
        from ..core.config import settings

        if not settings.nautobot_url or not settings.nautobot_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nautobot settings not configured. Please configure Nautobot URL and token.",
            )

        success, message = await nautobot_service.test_connection(
            settings.nautobot_url,
            settings.nautobot_token,
            settings.nautobot_timeout,
            settings.nautobot_verify_ssl,
        )

        return ConnectionTestResponse(
            success=success,
            message=message,
            nautobot_url=settings.nautobot_url,
            connection_source="environment",
        )
    except Exception as e:
        logger.error(f"Error testing Nautobot connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test Nautobot connection: {str(e)}",
        )


@router.get("/devices", response_model=DeviceListResponse)
async def get_devices(
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    filter_type: Optional[str] = None,
    filter_value: Optional[str] = None,
    current_user: dict = Depends(verify_admin_user),
):
    """Get list of devices from Nautobot with optional filtering and pagination."""
    try:
        result = await nautobot_service.get_devices(
            limit=limit,
            offset=offset,
            filter_type=filter_type,
            filter_value=filter_value,
        )
        return DeviceListResponse(**result)
    except Exception as e:
        logger.error(f"Error fetching devices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch devices: {str(e)}",
        )


@router.get("/devices/{device_id}", response_model=Device)
async def get_device(
    device_id: str,
    current_user: dict = Depends(verify_admin_user),
):
    """Get specific device details from Nautobot."""
    try:
        device = await nautobot_service.get_device(device_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {device_id} not found",
            )
        return Device(**device)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch device {device_id}: {str(e)}",
        )


@router.post("/devices/search", response_model=DeviceListResponse)
async def search_devices(
    filters: DeviceFilter,
    current_user: dict = Depends(verify_admin_user),
):
    """Search devices with filters."""
    try:
        result = await nautobot_service.get_devices(
            limit=filters.limit,
            offset=filters.offset,
            filter_type=filters.filter_type,
            filter_value=filters.filter_value,
        )
        return DeviceListResponse(**result)
    except Exception as e:
        logger.error(f"Error searching devices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search devices: {str(e)}",
        )


@router.post("/check-ip", response_model=IPAddressCheck)
async def check_ip_address(
    request: CheckIPRequest,
    current_user: dict = Depends(verify_admin_user),
):
    """Check if an IP address is available in Nautobot."""
    try:
        result = await nautobot_service.check_ip_address(request.ip_address)
        return IPAddressCheck(**result)
    except Exception as e:
        logger.error(f"Error checking IP address {request.ip_address}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check IP address: {str(e)}",
        )


@router.post("/devices/onboard", response_model=OnboardingResponse)
async def onboard_device(
    request: DeviceOnboardRequest,
    current_user: dict = Depends(verify_admin_user),
):
    """Onboard a new device to Nautobot."""
    try:
        from ..core.config import settings

        if not settings.nautobot_url or not settings.nautobot_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nautobot settings not configured.",
            )

        # Prepare job data
        job_data = {
            "data": {
                "location": request.location_id,
                "ip_addresses": request.ip_address,
                "secrets_group": request.secret_groups_id,
                "device_role": request.role_id,
                "namespace": request.namespace_id,
                "device_status": request.status_id,
                "interface_status": request.interface_status_id,
                "ip_address_status": request.ip_address_status_id,
                "platform": None if request.platform_id == "detect" else request.platform_id,
                "port": request.port,
                "timeout": request.timeout,
                "update_devices_without_primary_ip": False,
            }
        }

        # Make job API call via REST
        job_url = f"extras/jobs/Sync%20Devices%20From%20Network/run/"
        result = await nautobot_service.rest_request(job_url, method="POST", data=job_data)

        job_id = result.get("job_result", {}).get("id") or result.get("id")
        job_status = result.get("job_result", {}).get("status") or result.get("status", "pending")

        return OnboardingResponse(
            success=True,
            message=f"Device onboarding job started successfully for {request.ip_address}",
            job_id=job_id,
            job_status=job_status,
            device_data=request.dict(),
            nautobot_response=result,
        )

    except Exception as e:
        logger.error(f"Error onboarding device: {str(e)}")
        return OnboardingResponse(
            success=False,
            message=f"Failed to onboard device: {str(e)}",
            device_data=request.dict(),
        )


@router.post("/sync-network-data", response_model=SyncResponse)
async def sync_network_data(
    request: SyncNetworkDataRequest,
    current_user: dict = Depends(verify_admin_user),
):
    """Sync network data with Nautobot."""
    try:
        from ..core.config import settings

        if not settings.nautobot_url or not settings.nautobot_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nautobot settings not configured.",
            )

        # Prepare job data
        job_data = {
            "data": {
                "devices": request.data.get("devices", []),
                "default_prefix_status": request.data.get("default_prefix_status"),
                "interface_status": request.data.get("interface_status"),
                "ip_address_status": request.data.get("ip_address_status"),
                "namespace": request.data.get("namespace"),
                "sync_cables": request.data.get("sync_cables", False),
                "sync_software_version": request.data.get("sync_software_version", False),
                "sync_vlans": request.data.get("sync_vlans", False),
                "sync_vrfs": request.data.get("sync_vrfs", False),
            }
        }

        # Make job API call via REST
        job_url = f"extras/jobs/Sync%20Network%20Data%20From%20Network/run/"
        result = await nautobot_service.rest_request(job_url, method="POST", data=job_data)

        job_id = result.get("job_result", {}).get("id") or result.get("id")
        job_status = result.get("job_result", {}).get("status") or result.get("status", "pending")

        return SyncResponse(
            success=True,
            message="Network data sync job started successfully",
            job_id=job_id,
            job_status=job_status,
            nautobot_response=result,
        )

    except Exception as e:
        logger.error(f"Error syncing network data: {str(e)}")
        return SyncResponse(
            success=False,
            message=f"Failed to sync network data: {str(e)}",
        )


@router.get("/locations", response_model=List[Location])
async def get_locations(
    current_user: dict = Depends(verify_admin_user),
):
    """Get list of locations from Nautobot."""
    try:
        locations = await nautobot_service.get_locations()
        return [Location(**location) for location in locations]
    except Exception as e:
        logger.error(f"Error fetching locations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch locations: {str(e)}",
        )


@router.get("/stats", response_model=NautobotStats)
async def get_nautobot_stats(
    current_user: dict = Depends(verify_admin_user),
):
    """Get Nautobot statistics."""
    try:
        stats = await nautobot_service.get_stats()
        return NautobotStats(**stats)
    except Exception as e:
        logger.error(f"Error fetching Nautobot stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch statistics: {str(e)}",
        )


@router.get("/namespaces", response_model=List[NautobotNamespace])
async def get_namespaces(
    current_user: dict = Depends(verify_admin_user),
):
    """Get list of namespaces from Nautobot."""
    try:
        query = """
        query {
          namespaces {
            id
            name
            description
          }
        }
        """
        result = await nautobot_service.graphql_query(query)

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
    current_user: dict = Depends(verify_admin_user),
):
    """Get Nautobot device roles."""
    try:
        result = await nautobot_service.rest_request("extras/roles/")
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
    current_user: dict = Depends(verify_admin_user),
):
    """Get Nautobot roles specifically for dcim.device content type."""
    try:
        result = await nautobot_service.rest_request("extras/roles/?content_types=dcim.device")
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
    current_user: dict = Depends(verify_admin_user),
):
    """Get Nautobot platforms."""
    try:
        result = await nautobot_service.rest_request("dcim/platforms/")
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
    current_user: dict = Depends(verify_admin_user),
):
    """Get all Nautobot statuses."""
    try:
        result = await nautobot_service.rest_request("extras/statuses/")
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
    current_user: dict = Depends(verify_admin_user),
):
    """Get Nautobot device statuses."""
    try:
        result = await nautobot_service.rest_request("extras/statuses/?content_types=dcim.device")
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
    current_user: dict = Depends(verify_admin_user),
):
    """Get Nautobot secret groups."""
    try:
        query = """
        query secrets_groups {
          secrets_groups {
            id
            name
          }
        }
        """
        result = await nautobot_service.graphql_query(query)

        if "errors" in result:
            logger.warning(f"GraphQL errors fetching secret groups: {result['errors']}")
            return []

        secret_groups = result["data"]["secrets_groups"]
        return [NautobotSecretGroup(**group) for group in secret_groups]
    except Exception as e:
        logger.warning(f"Secret groups endpoint not available: {str(e)}")
        return []


@router.get("/health-check", response_model=HealthCheckResponse)
async def nautobot_health_check(
    current_user: dict = Depends(get_current_user),
):
    """Simple health check to verify Nautobot connectivity."""
    try:
        result = await nautobot_service.rest_request("dcim/devices/?limit=1")
        return HealthCheckResponse(
            status="connected",
            message="Nautobot is accessible",
            devices_count=result.get("count", 0),
        )
    except Exception as e:
        logger.error(f"Nautobot health check failed: {str(e)}")

        error_msg = str(e)
        if "403" in error_msg or "Invalid token" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Nautobot connection failed: Invalid or missing API token.",
            )
        elif "ConnectionError" in error_msg or "timeout" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Nautobot connection failed: Cannot reach Nautobot server.",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Nautobot connection failed: {error_msg}",
            )