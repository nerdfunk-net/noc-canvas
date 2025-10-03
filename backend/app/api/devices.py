"""
Device communication API router for sending commands to network devices.
Uses netmiko to connect and execute commands on devices.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..core.security import get_current_user
from ..core.database import get_db
from ..services.nautobot import nautobot_service
from ..services.device_communication import device_communication_service
from ..models.settings import DeviceCommand

logger = logging.getLogger(__name__)
router = APIRouter()


class DeviceCommandResponse(BaseModel):
    """Response model for device commands."""

    success: bool
    output: Optional[Any] = None  # Can be string (raw) or list/dict (parsed)
    error: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    command: Optional[str] = None
    execution_time: Optional[float] = None
    parsed: Optional[bool] = None  # Indicates if output was parsed
    parser_used: Optional[str] = None  # Which parser was used


class DeviceConnectionInfo(BaseModel):
    """Device connection information extracted from Nautobot."""

    device_id: str
    name: str
    primary_ip: str
    platform: str
    network_driver: str


async def get_device_connection_info(
    device_id: str, username: str
) -> DeviceConnectionInfo:
    """Get device connection information from Nautobot."""
    try:
        # Get device details from Nautobot
        device_data = await nautobot_service.get_device(device_id, username=username)

        if not device_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {device_id} not found in Nautobot",
            )

        # Extract primary IP address
        primary_ip4 = device_data.get("primary_ip4")
        if not primary_ip4 or not primary_ip4.get("address"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Device {device_id} does not have a primary IPv4 address configured",
            )

        # Extract IP address without subnet mask
        primary_ip = primary_ip4["address"].split("/")[0]

        # Extract platform information
        platform_info = device_data.get("platform")
        if not platform_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Device {device_id} does not have a platform configured",
            )

        network_driver = platform_info.get("network_driver")
        if not network_driver:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Device {device_id} platform does not have a network_driver configured",
            )

        return DeviceConnectionInfo(
            device_id=device_id,
            name=device_data.get("name", ""),
            primary_ip=primary_ip,
            platform=platform_info.get("name", ""),
            network_driver=network_driver,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device connection info for {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get device connection information: {str(e)}",
        )


@router.get("/{device_id}/running-config", response_model=DeviceCommandResponse)
async def get_running_config(
    device_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get the running configuration from a network device."""
    try:
        username = (
            current_user.get("username")
            if isinstance(current_user, dict)
            else current_user.username
        )
        logger.info(f"Getting running config for device {device_id}, user: {username}")

        # Get device connection information
        logger.debug(f"Fetching device connection info for device {device_id}")
        device_info = await get_device_connection_info(device_id, username)
        logger.debug(f"Device connection info: {device_info}")
        logger.debug(f"Device connection info type: {type(device_info)}")

        # Execute command on device
        logger.debug(
            f"Executing command 'show running-config' on device {device_info.name}"
        )
        result = await device_communication_service.execute_command(
            device_info=device_info, command="show running-config", username=username
        )
        logger.debug(f"Command execution result: success={result.get('success')}")

        return DeviceCommandResponse(
            success=result["success"],
            output=result.get("output"),
            error=result.get("error"),
            device_info=device_info.model_dump(),
            command="show running-config",
            execution_time=result.get("execution_time"),
            parsed=result.get("parsed", False),
            parser_used=result.get("parser_used"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting running config for device {device_id}: {str(e)}")
        logger.exception("Full exception details:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get running configuration: {str(e)}",
        )


@router.get("/{device_id}/startup-config", response_model=DeviceCommandResponse)
async def get_startup_config(
    device_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get the startup configuration from a network device."""
    try:
        username = (
            current_user.get("username")
            if isinstance(current_user, dict)
            else current_user.username
        )

        # Get device connection information
        device_info = await get_device_connection_info(device_id, username)

        # Execute command on device
        result = await device_communication_service.execute_command(
            device_info=device_info, command="show startup-config", username=username
        )

        return DeviceCommandResponse(
            success=result["success"],
            output=result.get("output"),
            error=result.get("error"),
            device_info=device_info.model_dump(),
            command="show startup-config",
            execution_time=result.get("execution_time"),
            parsed=result.get("parsed", False),
            parser_used=result.get("parser_used"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting startup config for device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get startup configuration: {str(e)}",
        )


@router.get("/{device_id}/cdp-neighbors", response_model=DeviceCommandResponse)
async def get_cdp_neighbors(
    device_id: str,
    use_textfsm: bool = False,
    current_user: dict = Depends(get_current_user),
):
    """Get CDP neighbors from a network device.

    Args:
        device_id: The ID of the device to query
        use_textfsm: If True, parse output using TextFSM. Default is False.
        current_user: The authenticated user

    Returns:
        DeviceCommandResponse with parsed or raw output
    """
    try:
        username = (
            current_user.get("username")
            if isinstance(current_user, dict)
            else current_user.username
        )

        # Get device connection information
        device_info = await get_device_connection_info(device_id, username)

        # Execute command on device with optional TextFSM parsing
        result = await device_communication_service.execute_command(
            device_info=device_info,
            command="show cdp neighbors",
            username=username,
            parser="TEXTFSM" if use_textfsm else None,
        )

        return DeviceCommandResponse(
            success=result["success"],
            output=result.get("output"),
            error=result.get("error"),
            device_info=device_info.model_dump(),
            command="show cdp neighbors",
            execution_time=result.get("execution_time"),
            parsed=result.get("parsed", False),
            parser_used=result.get("parser_used"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting CDP neighbors for device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get CDP neighbors: {str(e)}",
        )


@router.get("/{device_id}/ospf-neighbors", response_model=DeviceCommandResponse)
async def get_ospf_neighbors(
    device_id: str,
    use_textfsm: bool = False,
    current_user: dict = Depends(get_current_user),
):
    """Get OSPF neighbors from a network device.

    Args:
        device_id: The ID of the device to query
        use_textfsm: If True, parse output using TextFSM. Default is False.
        current_user: The authenticated user

    Returns:
        DeviceCommandResponse with parsed or raw output
    """
    try:
        username = (
            current_user.get("username")
            if isinstance(current_user, dict)
            else current_user.username
        )

        # Get device connection information
        device_info = await get_device_connection_info(device_id, username)

        # Execute command on device with optional TextFSM parsing
        result = await device_communication_service.execute_command(
            device_info=device_info,
            command="show ip ospf neighbor",
            username=username,
            parser="TEXTFSM" if use_textfsm else None,
        )

        return DeviceCommandResponse(
            success=result["success"],
            output=result.get("output"),
            error=result.get("error"),
            device_info=device_info.model_dump(),
            command="show ip ospf neighbor",
            execution_time=result.get("execution_time"),
            parsed=result.get("parsed", False),
            parser_used=result.get("parser_used"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting OSPF neighbors for device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get OSPF neighbors: {str(e)}",
        )


@router.get("/{device_id}/ip-route", response_model=DeviceCommandResponse)
async def get_ip_routes(
    device_id: str,
    use_textfsm: bool = False,
    current_user: dict = Depends(get_current_user),
):
    """Get IP routing table from a network device.

    Args:
        device_id: The ID of the device to query
        use_textfsm: If True, parse output using TextFSM. Default is False.
        current_user: The authenticated user

    Returns:
        DeviceCommandResponse with parsed or raw output
    """
    try:
        username = (
            current_user.get("username")
            if isinstance(current_user, dict)
            else current_user.username
        )

        # Get device connection information
        device_info = await get_device_connection_info(device_id, username)

        # Execute command on device with optional TextFSM parsing
        result = await device_communication_service.execute_command(
            device_info=device_info,
            command="show ip route",
            username=username,
            parser="TEXTFSM" if use_textfsm else None,
        )

        return DeviceCommandResponse(
            success=result["success"],
            output=result.get("output"),
            error=result.get("error"),
            device_info=device_info.model_dump(),
            command="show ip route",
            execution_time=result.get("execution_time"),
            parsed=result.get("parsed", False),
            parser_used=result.get("parser_used"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting IP routes for device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get IP routes: {str(e)}",
        )


@router.get("/{device_id}/ip-route/static", response_model=DeviceCommandResponse)
async def get_static_routes(
    device_id: str,
    use_textfsm: bool = False,
    current_user: dict = Depends(get_current_user),
):
    """Get static IP routes from a network device.

    Args:
        device_id: The ID of the device to query
        use_textfsm: If True, parse output using TextFSM. Default is False.
        current_user: The authenticated user

    Returns:
        DeviceCommandResponse with parsed or raw output
    """
    try:
        username = (
            current_user.get("username")
            if isinstance(current_user, dict)
            else current_user.username
        )

        # Get device connection information
        device_info = await get_device_connection_info(device_id, username)

        # Execute command on device with optional TextFSM parsing
        result = await device_communication_service.execute_command(
            device_info=device_info,
            command="show ip route static",
            username=username,
            parser="TEXTFSM" if use_textfsm else None,
        )

        return DeviceCommandResponse(
            success=result["success"],
            output=result.get("output"),
            error=result.get("error"),
            device_info=device_info.model_dump(),
            command="show ip route static",
            execution_time=result.get("execution_time"),
            parsed=result.get("parsed", False),
            parser_used=result.get("parser_used"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting static routes for device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get static routes: {str(e)}",
        )


@router.get("/{device_id}/ip-route/ospf", response_model=DeviceCommandResponse)
async def get_ospf_routes(
    device_id: str,
    use_textfsm: bool = False,
    current_user: dict = Depends(get_current_user),
):
    """Get OSPF IP routes from a network device.

    Args:
        device_id: The ID of the device to query
        use_textfsm: If True, parse output using TextFSM. Default is False.
        current_user: The authenticated user

    Returns:
        DeviceCommandResponse with parsed or raw output
    """
    try:
        username = (
            current_user.get("username")
            if isinstance(current_user, dict)
            else current_user.username
        )

        # Get device connection information
        device_info = await get_device_connection_info(device_id, username)

        # Execute command on device with optional TextFSM parsing
        result = await device_communication_service.execute_command(
            device_info=device_info,
            command="show ip route ospf",
            username=username,
            parser="TEXTFSM" if use_textfsm else None,
        )

        return DeviceCommandResponse(
            success=result["success"],
            output=result.get("output"),
            error=result.get("error"),
            device_info=device_info.model_dump(),
            command="show ip route ospf",
            execution_time=result.get("execution_time"),
            parsed=result.get("parsed", False),
            parser_used=result.get("parser_used"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting OSPF routes for device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get OSPF routes: {str(e)}",
        )


@router.get("/{device_id}/ip-route/bgp", response_model=DeviceCommandResponse)
async def get_bgp_routes(
    device_id: str,
    use_textfsm: bool = False,
    current_user: dict = Depends(get_current_user),
):
    """Get BGP IP routes from a network device.

    Args:
        device_id: The ID of the device to query
        use_textfsm: If True, parse output using TextFSM. Default is False.
        current_user: The authenticated user

    Returns:
        DeviceCommandResponse with parsed or raw output
    """
    try:
        username = (
            current_user.get("username")
            if isinstance(current_user, dict)
            else current_user.username
        )

        # Get device connection information
        device_info = await get_device_connection_info(device_id, username)

        # Execute command on device with optional TextFSM parsing
        result = await device_communication_service.execute_command(
            device_info=device_info,
            command="show ip route bgp",
            username=username,
            parser="TEXTFSM" if use_textfsm else None,
        )

        return DeviceCommandResponse(
            success=result["success"],
            output=result.get("output"),
            error=result.get("error"),
            device_info=device_info.model_dump(),
            command="show ip route bgp",
            execution_time=result.get("execution_time"),
            parsed=result.get("parsed", False),
            parser_used=result.get("parser_used"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting BGP routes for device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get BGP routes: {str(e)}",
        )


@router.get("/{device_id}/ip-arp", response_model=DeviceCommandResponse)
async def get_ip_arp(
    device_id: str,
    use_textfsm: bool = False,
    current_user: dict = Depends(get_current_user),
):
    """Get IP ARP table from a network device.

    Args:
        device_id: The ID of the device to query
        use_textfsm: If True, parse output using TextFSM. Default is False.
        current_user: The authenticated user

    Returns:
        DeviceCommandResponse with parsed or raw output
    """
    try:
        username = (
            current_user.get("username")
            if isinstance(current_user, dict)
            else current_user.username
        )

        # Get device connection information
        device_info = await get_device_connection_info(device_id, username)

        # Execute command on device with optional TextFSM parsing
        result = await device_communication_service.execute_command(
            device_info=device_info,
            command="show ip arp",
            username=username,
            parser="TEXTFSM" if use_textfsm else None,
        )

        return DeviceCommandResponse(
            success=result["success"],
            output=result.get("output"),
            error=result.get("error"),
            device_info=device_info.model_dump(),
            command="show ip arp",
            execution_time=result.get("execution_time"),
            parsed=result.get("parsed", False),
            parser_used=result.get("parser_used"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ARP table for device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ARP table: {str(e)}",
        )


@router.get("/{device_id}/mac-address-table", response_model=DeviceCommandResponse)
async def get_mac_address_table(
    device_id: str,
    use_textfsm: bool = False,
    current_user: dict = Depends(get_current_user),
):
    """Get MAC address table from a network device.

    Args:
        device_id: The ID of the device to query
        use_textfsm: If True, parse output using TextFSM. Default is False.
        current_user: The authenticated user

    Returns:
        DeviceCommandResponse with parsed or raw output
    """
    try:
        username = (
            current_user.get("username")
            if isinstance(current_user, dict)
            else current_user.username
        )

        # Get device connection information
        device_info = await get_device_connection_info(device_id, username)

        # Execute command on device with optional TextFSM parsing
        result = await device_communication_service.execute_command(
            device_info=device_info,
            command="show mac address-table",
            username=username,
            parser="TEXTFSM" if use_textfsm else None,
        )

        return DeviceCommandResponse(
            success=result["success"],
            output=result.get("output"),
            error=result.get("error"),
            device_info=device_info.model_dump(),
            command="show mac address-table",
            execution_time=result.get("execution_time"),
            parsed=result.get("parsed", False),
            parser_used=result.get("parser_used"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting MAC address table for device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get MAC address table: {str(e)}",
        )


@router.get("/{device_id}/access-lists", response_model=DeviceCommandResponse)
async def get_access_lists(
    device_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get access lists from a network device."""
    try:
        username = (
            current_user.get("username")
            if isinstance(current_user, dict)
            else current_user.username
        )

        # Get device connection information
        device_info = await get_device_connection_info(device_id, username)

        # Execute command on device
        result = await device_communication_service.execute_command(
            device_info=device_info, command="show access-lists", username=username
        )

        return DeviceCommandResponse(
            success=result["success"],
            output=result.get("output"),
            error=result.get("error"),
            device_info=device_info.model_dump(),
            command="show access-lists",
            execution_time=result.get("execution_time"),
            parsed=result.get("parsed", False),
            parser_used=result.get("parser_used"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting access lists for device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get access lists: {str(e)}",
        )


@router.post("/{device_id}/send/{command_id}", response_model=DeviceCommandResponse)
async def send_custom_command(
    device_id: str,
    command_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a custom command to a network device using predefined command ID."""
    try:
        username = (
            current_user.get("username")
            if isinstance(current_user, dict)
            else current_user.username
        )

        # Get device connection information
        device_info = await get_device_connection_info(device_id, username)

        # Get command from database using command_id
        logger.debug(f"Fetching command with ID {command_id} from database")
        device_command = (
            db.query(DeviceCommand).filter(DeviceCommand.id == command_id).first()
        )

        if not device_command:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Command with ID {command_id} not found",
            )

        logger.info(
            f"Found command: {device_command.command} (parser: {device_command.parser.value})"
        )

        # Execute command on device with parser if specified
        result = await device_communication_service.execute_command(
            device_info=device_info,
            command=device_command.command,
            username=username,
            parser=device_command.parser.value,
        )

        return DeviceCommandResponse(
            success=result["success"],
            output=result.get("output"),
            error=result.get("error"),
            device_info=device_info.model_dump(),
            command=device_command.command,
            execution_time=result.get("execution_time"),
            parsed=result.get("parsed", False),
            parser_used=result.get("parser_used"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error sending custom command {command_id} to device {device_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send custom command: {str(e)}",
        )
