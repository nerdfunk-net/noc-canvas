"""
Nautobot Network Router
Handles network utility endpoints (connection test, IP check)
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional
import logging
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.dynamic_settings import get_nautobot_config
from ..api.auth import get_current_user
from ..services.nautobot import nautobot_service

router = APIRouter()
logger = logging.getLogger(__name__)


# Pydantic Models
class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    nautobot_url: str
    connection_source: str = "environment"


class CheckIPRequest(BaseModel):
    ip_address: str


class IPAddressCheck(BaseModel):
    available: bool
    message: str
    ip_address: str
    details: Optional[dict] = None


# Helper Functions
def get_username(current_user: dict) -> str:
    """Extract username from current user"""
    if isinstance(current_user, dict):
        return current_user.get("username", "unknown")
    return getattr(current_user, "username", "unknown")


@router.get("/test", response_model=ConnectionTestResponse)
async def test_nautobot_connection(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Test current Nautobot connection using configured settings."""
    try:
        nautobot_config = get_nautobot_config(db)
        if not nautobot_config["url"] or not nautobot_config["token"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nautobot settings not configured. Please configure Nautobot URL and token.",
            )

        success, message = await nautobot_service.test_connection(
            nautobot_config["url"],
            nautobot_config["token"],
            nautobot_config["timeout"],
            nautobot_config["verify_ssl"],
        )

        return ConnectionTestResponse(
            success=success,
            message=message,
            nautobot_url=nautobot_config["url"],
            connection_source="database"
            if nautobot_config.get("_source") == "database"
            else "environment",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing Nautobot connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test Nautobot connection: {str(e)}",
        )


@router.post("/check-ip", response_model=IPAddressCheck)
async def check_ip_address(
    request: CheckIPRequest,
    current_user: dict = Depends(get_current_user),
):
    """Check if an IP address is available in Nautobot."""
    try:
        username = get_username(current_user)
        result = await nautobot_service.check_ip_address(
            request.ip_address, username=username
        )
        return IPAddressCheck(**result)
    except Exception as e:
        logger.error(f"Error checking IP address {request.ip_address}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check IP address: {str(e)}",
        )
