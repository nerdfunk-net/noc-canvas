"""
Nautobot Jobs Router
Handles job execution endpoints (onboarding, sync)
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
from sqlalchemy.orm import Session
from ..core.config import settings
from ..core.database import get_db
from ..core.dynamic_settings import get_nautobot_config
from ..api.auth import get_current_user
from ..services.nautobot import nautobot_service

router = APIRouter()
logger = logging.getLogger(__name__)


# Pydantic Models
class DeviceOnboardRequest(BaseModel):
    ip_address: str
    location_id: str
    secret_groups_id: str
    role_id: str
    namespace_id: str
    status_id: str
    interface_status_id: str
    ip_address_status_id: str
    platform_id: str = "detect"
    port: int = 22
    timeout: int = 30


class OnboardingResponse(BaseModel):
    success: bool
    message: str
    job_id: Optional[str] = None
    job_status: Optional[str] = None
    device_data: Optional[Dict[str, Any]] = None
    nautobot_response: Optional[Dict[str, Any]] = None


class SyncNetworkDataRequest(BaseModel):
    data: Dict[str, Any]


class SyncResponse(BaseModel):
    success: bool
    message: str
    job_id: Optional[str] = None
    job_status: Optional[str] = None
    nautobot_response: Optional[Dict[str, Any]] = None


# Helper Functions
def get_username(current_user: dict) -> str:
    """Extract username from current user"""
    if isinstance(current_user, dict):
        return current_user.get("username", "unknown")
    return getattr(current_user, "username", "unknown")


async def execute_nautobot_job(
    job_url: str, job_data: Dict[str, Any], username: str, job_description: str = "Job"
) -> Dict[str, Any]:
    """
    Execute a Nautobot job and return standardized response.

    Args:
        job_url: The job endpoint URL
        job_data: The job data payload
        username: Username for authentication
        job_description: Description of the job for logging

    Returns:
        Dict containing job_id, job_status, and full result
    """
    result = await nautobot_service.rest_request(
        job_url, method="POST", data=job_data, username=username
    )

    job_id = result.get("job_result", {}).get("id") or result.get("id")
    job_status = result.get("job_result", {}).get("status") or result.get(
        "status", "pending"
    )

    return {"job_id": job_id, "job_status": job_status, "result": result}


@router.post("/devices/onboard", response_model=OnboardingResponse)
async def onboard_device(
    request: DeviceOnboardRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Onboard a new device to Nautobot."""
    try:
        nautobot_config = get_nautobot_config(db)
        if not nautobot_config["url"] or not nautobot_config["token"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nautobot settings not configured.",
            )

        username = get_username(current_user)

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
                "platform": None
                if request.platform_id == "detect"
                else request.platform_id,
                "port": request.port,
                "timeout": request.timeout,
                "update_devices_without_primary_ip": False,
            }
        }

        # Execute onboarding job
        job_url = "extras/jobs/Sync%20Devices%20From%20Network/run/"
        job_result = await execute_nautobot_job(
            job_url, job_data, username, "Device onboarding"
        )

        return OnboardingResponse(
            success=True,
            message=f"Device onboarding job started successfully for {request.ip_address}",
            job_id=job_result["job_id"],
            job_status=job_result["job_status"],
            device_data=request.dict(),
            nautobot_response=job_result["result"],
        )
    except HTTPException:
        raise
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sync network data with Nautobot."""
    try:
        nautobot_config = get_nautobot_config(db)
        if not nautobot_config["url"] or not nautobot_config["token"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nautobot settings not configured.",
            )

        username = get_username(current_user)

        # Prepare job data
        job_data = {
            "data": {
                "devices": request.data.get("devices", []),
                "default_prefix_status": request.data.get("default_prefix_status"),
                "interface_status": request.data.get("interface_status"),
                "ip_address_status": request.data.get("ip_address_status"),
                "namespace": request.data.get("namespace"),
                "sync_cables": request.data.get("sync_cables", False),
                "sync_software_version": request.data.get(
                    "sync_software_version", False
                ),
                "sync_vlans": request.data.get("sync_vlans", False),
                "sync_vrfs": request.data.get("sync_vrfs", False),
            }
        }

        # Execute network data sync job
        job_url = "extras/jobs/Sync%20Network%20Data%20From%20Network/run/"
        job_result = await execute_nautobot_job(
            job_url, job_data, username, "Network data sync"
        )

        return SyncResponse(
            success=True,
            message="Network data sync job started successfully",
            job_id=job_result["job_id"],
            job_status=job_result["job_status"],
            nautobot_response=job_result["result"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing network data: {str(e)}")
        return SyncResponse(
            success=False,
            message=f"Failed to sync network data: {str(e)}",
        )
