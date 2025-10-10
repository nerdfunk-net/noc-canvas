"""
Device communication API router for sending commands to network devices.
Uses netmiko to connect and execute commands on devices.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..core.security import get_current_user
from ..core.database import get_db
from ..services.nautobot import nautobot_service
from ..services.device_communication import device_communication_service
from ..services.device_cache_service import device_cache_service
from ..models.settings import DeviceCommand
from ..schemas.device_cache import (
    InterfaceCacheCreate,
    DeviceCacheCreate,
    IPAddressCacheCreate,
    ARPCacheCreate,
    StaticRouteCacheCreate,
    OSPFRouteCacheCreate,
    MACAddressTableCacheCreate,
    CDPNeighborCacheCreate,
)

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
    cached: Optional[bool] = None  # Indicates if output came from cache


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
            cached=False,
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
            cached=False,
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
    db: Session = Depends(get_db),
):
    """Get CDP neighbors from a network device.

    Args:
        device_id: The ID of the device to query
        use_textfsm: If True, parse output using TextFSM and cache the results. Default is False.
        current_user: The authenticated user
        db: Database session

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

        # If TextFSM was used and parsing succeeded, cache the CDP neighbor data
        if use_textfsm and result.get("parsed") and result.get("success"):
            output = result.get("output")
            if isinstance(output, list):
                logger.info(
                    f"Caching {len(output)} CDP neighbors for device {device_id}"
                )

                # Store the parsed JSON output in the JSON blob cache
                try:
                    import json
                    from app.services.json_cache_service import JSONCacheService

                    json_data = json.dumps(output)
                    JSONCacheService.set_cache(
                        db=db,
                        device_id=device_id,
                        command="show cdp neighbors",
                        json_data=json_data,
                    )
                    logger.info(
                        f"Successfully cached JSON output for device {device_id}, command: show cdp neighbors"
                    )
                except Exception as cache_error:
                    logger.error(f"Failed to cache JSON output: {str(cache_error)}")
                    # Continue processing even if JSON cache fails

                # Ensure device exists in cache
                device_cache_data = DeviceCacheCreate(
                    device_id=device_id,
                    device_name=device_info.name,
                    primary_ip=device_info.primary_ip,
                    platform=device_info.platform,
                )
                device_cache_service.get_or_create_device_cache(db, device_cache_data)

                neighbors_to_cache = []

                for cdp_data in output:
                    # Try both uppercase and lowercase field names
                    neighbor_name_raw = (
                        cdp_data.get("NEIGHBOR")
                        or cdp_data.get("neighbor")
                        or cdp_data.get("NEIGHBOR_NAME")
                        or cdp_data.get("neighbor_name")
                        or cdp_data.get("DESTINATION_HOST")
                        or cdp_data.get("destination_host")
                        or ""
                    )
                    local_interface_raw = (
                        cdp_data.get("LOCAL_INTERFACE")
                        or cdp_data.get("local_interface")
                        or cdp_data.get("LOCAL_PORT")
                        or cdp_data.get("local_port")
                        or ""
                    )

                    # Handle if fields are lists
                    if isinstance(neighbor_name_raw, list):
                        neighbor_name = (
                            neighbor_name_raw[0] if neighbor_name_raw else ""
                        )
                    else:
                        neighbor_name = neighbor_name_raw
                    neighbor_name = neighbor_name.strip() if neighbor_name else ""

                    if isinstance(local_interface_raw, list):
                        local_interface = (
                            local_interface_raw[0] if local_interface_raw else ""
                        )
                    else:
                        local_interface = local_interface_raw
                    local_interface = local_interface.strip() if local_interface else ""

                    # Skip entries without neighbor name or local interface
                    if not neighbor_name or not local_interface:
                        logger.warning(
                            f"Skipping CDP neighbor with missing name or interface: {cdp_data}"
                        )
                        continue

                    # Extract other fields
                    neighbor_ip_raw = (
                        cdp_data.get("MANAGEMENT_IP")
                        or cdp_data.get("management_ip")
                        or cdp_data.get("NEIGHBOR_IP")
                        or cdp_data.get("neighbor_ip")
                        or ""
                    )
                    neighbor_interface_raw = (
                        cdp_data.get("NEIGHBOR_INTERFACE")
                        or cdp_data.get("neighbor_interface")
                        or cdp_data.get("NEIGHBOR_PORT")
                        or cdp_data.get("neighbor_port")
                        or ""
                    )
                    platform_raw = (
                        cdp_data.get("PLATFORM") or cdp_data.get("platform") or ""
                    )
                    capabilities_raw = (
                        cdp_data.get("CAPABILITIES")
                        or cdp_data.get("capabilities")
                        or ""
                    )

                    # Handle lists
                    if isinstance(neighbor_ip_raw, list):
                        neighbor_ip = neighbor_ip_raw[0] if neighbor_ip_raw else ""
                    else:
                        neighbor_ip = neighbor_ip_raw
                    neighbor_ip = neighbor_ip.strip() if neighbor_ip else ""

                    if isinstance(neighbor_interface_raw, list):
                        neighbor_interface = (
                            neighbor_interface_raw[0] if neighbor_interface_raw else ""
                        )
                    else:
                        neighbor_interface = neighbor_interface_raw
                    neighbor_interface = (
                        neighbor_interface.strip() if neighbor_interface else ""
                    )

                    if isinstance(platform_raw, list):
                        platform = platform_raw[0] if platform_raw else ""
                    else:
                        platform = platform_raw
                    platform = platform.strip() if platform else ""

                    if isinstance(capabilities_raw, list):
                        capabilities = (
                            ", ".join(capabilities_raw) if capabilities_raw else ""
                        )
                    else:
                        capabilities = capabilities_raw
                    capabilities = capabilities.strip() if capabilities else ""

                    cdp_neighbor = CDPNeighborCacheCreate(
                        device_id=device_id,
                        neighbor_name=neighbor_name,
                        neighbor_ip=neighbor_ip if neighbor_ip else None,
                        local_interface=local_interface,
                        neighbor_interface=neighbor_interface
                        if neighbor_interface
                        else None,
                        platform=platform if platform else None,
                        capabilities=capabilities if capabilities else None,
                    )
                    neighbors_to_cache.append(cdp_neighbor)

                # Bulk replace CDP neighbors
                if neighbors_to_cache:
                    device_cache_service.bulk_replace_cdp_neighbors(
                        db, device_id, neighbors_to_cache
                    )
                    logger.info(
                        f"Successfully cached {len(neighbors_to_cache)} CDP neighbors"
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
    db: Session = Depends(get_db),
):
    """Get static IP routes from a network device.

    Args:
        device_id: The ID of the device to query
        use_textfsm: If True, parse output using TextFSM and cache the results. Default is False.
        current_user: The authenticated user
        db: Database session

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

        # If TextFSM was used and parsing succeeded, cache the static route data
        if use_textfsm and result.get("parsed") and result.get("success"):
            output = result.get("output")
            if isinstance(output, list):
                logger.info(
                    f"Caching {len(output)} static routes for device {device_id}"
                )

                # Store the parsed JSON output in the JSON blob cache
                try:
                    import json
                    from app.services.json_cache_service import JSONCacheService

                    json_data = json.dumps(output)
                    JSONCacheService.set_cache(
                        db=db,
                        device_id=device_id,
                        command="show ip route static",
                        json_data=json_data,
                    )
                    logger.info(
                        f"Successfully cached JSON output for device {device_id}, command: show ip route static"
                    )
                except Exception as cache_error:
                    logger.error(f"Failed to cache JSON output: {str(cache_error)}")
                    # Continue processing even if JSON cache fails

                # Ensure device exists in cache
                device_cache_data = DeviceCacheCreate(
                    device_id=device_id,
                    device_name=device_info.name,
                    primary_ip=device_info.primary_ip,
                    platform=device_info.platform,
                )
                device_cache_service.get_or_create_device_cache(db, device_cache_data)

                routes_to_cache = []

                for route_data in output:
                    # Try both uppercase and lowercase field names
                    network = (
                        route_data.get("NETWORK") or route_data.get("network") or ""
                    ).strip()
                    nexthop_ip = (
                        route_data.get("NEXTHOP_IP")
                        or route_data.get("nexthop_ip")
                        or ""
                    ).strip()

                    # Skip routes without network
                    if not network:
                        logger.warning(
                            f"Skipping route with missing network: {route_data}"
                        )
                        continue

                    # Extract other fields
                    metric = route_data.get("METRIC") or route_data.get("metric")
                    distance = route_data.get("DISTANCE") or route_data.get("distance")
                    interface_name = (
                        route_data.get("INTERFACE") or route_data.get("interface") or ""
                    ).strip()

                    # Convert metric and distance to integers if possible
                    metric_int = None
                    if metric:
                        try:
                            metric_int = int(metric)
                        except (ValueError, TypeError):
                            pass

                    distance_int = None
                    if distance:
                        try:
                            distance_int = int(distance)
                        except (ValueError, TypeError):
                            pass

                    route_cache = StaticRouteCacheCreate(
                        device_id=device_id,
                        network=network,
                        nexthop_ip=nexthop_ip if nexthop_ip else None,
                        metric=metric_int,
                        distance=distance_int,
                        interface_name=interface_name if interface_name else None,
                    )
                    routes_to_cache.append(route_cache)

                # Bulk replace static routes
                if routes_to_cache:
                    device_cache_service.bulk_replace_static_routes(
                        db, device_id, routes_to_cache
                    )
                    logger.info(
                        f"Successfully cached {len(routes_to_cache)} static routes"
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
    db: Session = Depends(get_db),
):
    """Get OSPF IP routes from a network device.

    Args:
        device_id: The ID of the device to query
        use_textfsm: If True, parse output using TextFSM and cache the results. Default is False.
        current_user: The authenticated user
        db: Database session

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

        # If TextFSM was used and parsing succeeded, cache the OSPF route data
        if use_textfsm and result.get("parsed") and result.get("success"):
            output = result.get("output")
            if isinstance(output, list):
                logger.info(f"Caching {len(output)} OSPF routes for device {device_id}")

                # Store the parsed JSON output in the JSON blob cache
                try:
                    import json
                    from app.services.json_cache_service import JSONCacheService

                    json_data = json.dumps(output)
                    JSONCacheService.set_cache(
                        db=db,
                        device_id=device_id,
                        command="show ip route ospf",
                        json_data=json_data,
                    )
                    logger.info(
                        f"Successfully cached JSON output for device {device_id}, command: show ip route ospf"
                    )
                except Exception as cache_error:
                    logger.error(f"Failed to cache JSON output: {str(cache_error)}")
                    # Continue processing even if JSON cache fails

                # Ensure device exists in cache
                device_cache_data = DeviceCacheCreate(
                    device_id=device_id,
                    device_name=device_info.name,
                    primary_ip=device_info.primary_ip,
                    platform=device_info.platform,
                )
                device_cache_service.get_or_create_device_cache(db, device_cache_data)

                routes_to_cache = []

                for route_data in output:
                    # Try both uppercase and lowercase field names
                    network = (
                        route_data.get("NETWORK") or route_data.get("network") or ""
                    ).strip()
                    nexthop_ip = (
                        route_data.get("NEXTHOP_IP")
                        or route_data.get("nexthop_ip")
                        or ""
                    ).strip()

                    # Skip routes without network
                    if not network:
                        logger.warning(
                            f"Skipping OSPF route with missing network: {route_data}"
                        )
                        continue

                    # Extract other fields
                    metric = route_data.get("METRIC") or route_data.get("metric")
                    distance = route_data.get("DISTANCE") or route_data.get("distance")
                    interface_name = (
                        route_data.get("INTERFACE") or route_data.get("interface") or ""
                    ).strip()
                    area = (
                        route_data.get("AREA") or route_data.get("area") or ""
                    ).strip()
                    route_type = (
                        route_data.get("TYPE")
                        or route_data.get("type")
                        or route_data.get("ROUTE_TYPE")
                        or route_data.get("route_type")
                        or ""
                    ).strip()

                    # Convert metric and distance to integers if possible
                    metric_int = None
                    if metric:
                        try:
                            metric_int = int(metric)
                        except (ValueError, TypeError):
                            pass

                    distance_int = None
                    if distance:
                        try:
                            distance_int = int(distance)
                        except (ValueError, TypeError):
                            pass

                    route_cache = OSPFRouteCacheCreate(
                        device_id=device_id,
                        network=network,
                        nexthop_ip=nexthop_ip if nexthop_ip else None,
                        metric=metric_int,
                        distance=distance_int,
                        interface_name=interface_name if interface_name else None,
                        area=area if area else None,
                        route_type=route_type if route_type else None,
                    )
                    routes_to_cache.append(route_cache)

                # Bulk replace OSPF routes
                if routes_to_cache:
                    device_cache_service.bulk_replace_ospf_routes(
                        db, device_id, routes_to_cache
                    )
                    logger.info(
                        f"Successfully cached {len(routes_to_cache)} OSPF routes"
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
    db: Session = Depends(get_db),
):
    """Get BGP IP routes from a network device.

    Args:
        device_id: The ID of the device to query
        use_textfsm: If True, parse output using TextFSM and cache the results. Default is False.
        current_user: The authenticated user
        db: Database session

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

        # If TextFSM was used and parsing succeeded, cache the BGP route data
        if use_textfsm and result.get("parsed") and result.get("success"):
            output = result.get("output")
            if isinstance(output, list):
                logger.info(f"Caching {len(output)} BGP routes for device {device_id}")

                # Store the parsed JSON output in the JSON blob cache
                try:
                    import json
                    from app.services.json_cache_service import JSONCacheService

                    json_data = json.dumps(output)
                    JSONCacheService.set_cache(
                        db=db,
                        device_id=device_id,
                        command="show ip route bgp",
                        json_data=json_data,
                    )
                    logger.info(
                        f"Successfully cached JSON output for device {device_id}, command: show ip route bgp"
                    )
                except Exception as cache_error:
                    logger.error(f"Failed to cache JSON output: {str(cache_error)}")
                    # Continue processing even if JSON cache fails

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
    db: Session = Depends(get_db),
):
    """Get IP ARP table from a network device.

    Args:
        device_id: The ID of the device to query
        use_textfsm: If True, parse output using TextFSM and cache the results. Default is False.
        current_user: The authenticated user
        db: Database session

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

        # If TextFSM was used and parsing succeeded, cache the ARP data
        if use_textfsm and result.get("parsed") and result.get("success"):
            output = result.get("output")
            if isinstance(output, list):
                logger.info(f"Caching {len(output)} ARP entries for device {device_id}")

                # Store the parsed JSON output in the JSON blob cache
                try:
                    import json
                    from app.services.json_cache_service import JSONCacheService

                    json_data = json.dumps(output)
                    JSONCacheService.set_cache(
                        db=db,
                        device_id=device_id,
                        command="show ip arp",
                        json_data=json_data,
                    )
                    logger.info(
                        f"Successfully cached JSON output for device {device_id}, command: show ip arp"
                    )
                except Exception as cache_error:
                    logger.error(f"Failed to cache JSON output: {str(cache_error)}")
                    # Continue processing even if JSON cache fails

                # Ensure device exists in cache
                device_cache_data = DeviceCacheCreate(
                    device_id=device_id,
                    device_name=device_info.name,
                    primary_ip=device_info.primary_ip,
                    platform=device_info.platform,
                )
                device_cache_service.get_or_create_device_cache(db, device_cache_data)

                arp_entries_to_cache = []

                for arp_data in output:
                    # Try both uppercase and lowercase field names (different TextFSM templates use different cases)
                    ip_address = (
                        arp_data.get("ADDRESS")
                        or arp_data.get("address")
                        or arp_data.get("IP_ADDRESS")
                        or arp_data.get("ip_address")
                        or ""
                    ).strip()
                    mac_address = (
                        arp_data.get("MAC")
                        or arp_data.get("mac")
                        or arp_data.get("MAC_ADDRESS")
                        or arp_data.get("mac_address")
                        or ""
                    ).strip()

                    # Skip entries without IP or MAC
                    if not ip_address or not mac_address:
                        logger.warning(
                            f"Skipping ARP entry with missing IP or MAC: {arp_data}"
                        )
                        continue

                    interface_name = (
                        arp_data.get("INTERFACE") or arp_data.get("interface") or ""
                    ).strip()
                    age = arp_data.get("AGE") or arp_data.get("age")
                    arp_type = (
                        arp_data.get("TYPE")
                        or arp_data.get("type")
                        or arp_data.get("PROTOCOL")
                        or arp_data.get("protocol")
                        or ""
                    ).strip()

                    # Convert age to integer if possible
                    age_int = None
                    if age:
                        try:
                            age_int = int(age)
                        except (ValueError, TypeError):
                            pass

                    arp_cache = ARPCacheCreate(
                        device_id=device_id,
                        ip_address=ip_address,
                        mac_address=mac_address,
                        interface_name=interface_name if interface_name else None,
                        age=age_int,
                        arp_type=arp_type if arp_type else None,
                    )
                    arp_entries_to_cache.append(arp_cache)

                # Bulk replace ARP entries (removes old entries and adds new ones)
                if arp_entries_to_cache:
                    device_cache_service.bulk_replace_arp(
                        db, device_id, arp_entries_to_cache
                    )
                    logger.info(
                        f"Successfully cached {len(arp_entries_to_cache)} ARP entries"
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
    db: Session = Depends(get_db),
):
    """Get MAC address table from a network device.

    Args:
        device_id: The ID of the device to query
        use_textfsm: If True, parse output using TextFSM and cache the results. Default is False.
        current_user: The authenticated user
        db: Database session

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

        # If TextFSM was used and parsing succeeded, cache the MAC address table data
        if use_textfsm and result.get("parsed") and result.get("success"):
            output = result.get("output")
            if isinstance(output, list):
                logger.info(
                    f"Caching {len(output)} MAC address table entries for device {device_id}"
                )

                # Store the parsed JSON output in the JSON blob cache
                try:
                    import json
                    from app.services.json_cache_service import JSONCacheService

                    json_data = json.dumps(output)
                    JSONCacheService.set_cache(
                        db=db,
                        device_id=device_id,
                        command="show mac address-table",
                        json_data=json_data,
                    )
                    logger.info(
                        f"Successfully cached JSON output for device {device_id}, command: show mac address-table"
                    )
                except Exception as cache_error:
                    logger.error(f"Failed to cache JSON output: {str(cache_error)}")
                    # Continue processing even if JSON cache fails

                # Ensure device exists in cache
                device_cache_data = DeviceCacheCreate(
                    device_id=device_id,
                    device_name=device_info.name,
                    primary_ip=device_info.primary_ip,
                    platform=device_info.platform,
                )
                device_cache_service.get_or_create_device_cache(db, device_cache_data)

                entries_to_cache = []

                for mac_data in output:
                    # Try both uppercase and lowercase field names
                    mac_address_raw = (
                        mac_data.get("DESTINATION_ADDRESS")
                        or mac_data.get("destination_address")
                        or mac_data.get("MAC_ADDRESS")
                        or mac_data.get("mac_address")
                        or ""
                    )

                    # Handle if mac_address is a list (some TextFSM templates return lists)
                    if isinstance(mac_address_raw, list):
                        mac_address = mac_address_raw[0] if mac_address_raw else ""
                    else:
                        mac_address = mac_address_raw

                    mac_address = mac_address.strip() if mac_address else ""

                    # Skip entries without MAC address
                    if not mac_address:
                        logger.warning(
                            f"Skipping MAC entry with missing MAC address: {mac_data}"
                        )
                        continue

                    # Extract other fields
                    vlan = mac_data.get("VLAN") or mac_data.get("vlan")

                    # Handle interface name (might be a list)
                    interface_raw = (
                        mac_data.get("DESTINATION_PORT")
                        or mac_data.get("destination_port")
                        or mac_data.get("INTERFACE")
                        or mac_data.get("interface")
                        or ""
                    )
                    if isinstance(interface_raw, list):
                        interface_name = (
                            ", ".join(interface_raw) if interface_raw else ""
                        )
                    else:
                        interface_name = interface_raw
                    interface_name = interface_name.strip() if interface_name else ""

                    # Handle entry type (might be a list)
                    type_raw = (
                        mac_data.get("TYPE")
                        or mac_data.get("type")
                        or mac_data.get("ENTRY_TYPE")
                        or mac_data.get("entry_type")
                        or ""
                    )
                    if isinstance(type_raw, list):
                        entry_type = type_raw[0] if type_raw else ""
                    else:
                        entry_type = type_raw
                    entry_type = entry_type.strip() if entry_type else ""

                    # Convert VLAN to integer if possible
                    vlan_id = None
                    if vlan:
                        try:
                            vlan_id = int(vlan)
                        except (ValueError, TypeError):
                            pass

                    mac_entry = MACAddressTableCacheCreate(
                        device_id=device_id,
                        mac_address=mac_address,
                        vlan_id=vlan_id,
                        interface_name=interface_name if interface_name else None,
                        entry_type=entry_type if entry_type else None,
                    )
                    entries_to_cache.append(mac_entry)

                # Bulk replace MAC table entries
                if entries_to_cache:
                    device_cache_service.bulk_replace_mac_table(
                        db, device_id, entries_to_cache
                    )
                    logger.info(
                        f"Successfully cached {len(entries_to_cache)} MAC address table entries"
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
        logger.error(
            f"Error getting MAC address table for device {device_id}: {str(e)}"
        )
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


@router.get("/{device_id}/interfaces", response_model=DeviceCommandResponse)
async def get_interfaces(
    device_id: str,
    use_textfsm: bool = False,
    disable_cache: bool = False,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get interfaces from a network device.

    Args:
        device_id: The ID of the device to query
        use_textfsm: If True, parse output using TextFSM and cache the results. Default is False.
        disable_cache: If True, bypass cache and execute command directly. Cache will still be updated. Default is False.
        current_user: The authenticated user
        db: Database session

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

        # Check if we have valid cached data when TextFSM parsing is requested and cache is not disabled
        cached_output = None
        used_cache = False
        if use_textfsm and not disable_cache:
            try:
                import json
                from app.services.json_cache_service import JSONCacheService

                valid_cache = JSONCacheService.get_valid_cache(
                    db=db, device_id=device_id, command="show interfaces"
                )

                if valid_cache:
                    # Use cached data
                    cached_output = json.loads(valid_cache.json_data)
                    used_cache = True
                    logger.info(
                        f"Using cached data for device {device_id}, command: show interfaces"
                    )
            except Exception as cache_error:
                logger.warning(
                    f"Failed to check cache, will execute command: {str(cache_error)}"
                )

        # Execute command only if we don't have valid cached data
        if not used_cache:
            # Execute command on device with optional TextFSM parsing
            result = await device_communication_service.execute_command(
                device_info=device_info,
                command="show interfaces",
                username=username,
                parser="TEXTFSM" if use_textfsm else None,
            )
        else:
            # Use cached data - simulate successful result
            result = {
                "success": True,
                "output": cached_output,
                "parsed": True,
                "parser_used": "TEXTFSM (from cache)",
                "execution_time": 0.0,
            }

        # If TextFSM was used and parsing succeeded, cache/update the interface data
        if (
            use_textfsm
            and result.get("parsed")
            and result.get("success")
            and not used_cache
        ):
            output = result.get("output")
            if isinstance(output, list):
                logger.info(f"Caching {len(output)} interfaces for device {device_id}")

                # Store the parsed JSON output in the JSON blob cache
                try:
                    import json
                    from app.services.json_cache_service import JSONCacheService

                    json_data = json.dumps(output)
                    JSONCacheService.set_cache(
                        db=db,
                        device_id=device_id,
                        command="show interfaces",
                        json_data=json_data,
                    )
                    logger.info(
                        f"Successfully cached JSON output for device {device_id}, command: show interfaces"
                    )
                except Exception as cache_error:
                    logger.error(f"Failed to cache JSON output: {str(cache_error)}")
                    # Continue processing even if JSON cache fails

                # Ensure device exists in cache before adding interfaces
                device_cache_data = DeviceCacheCreate(
                    device_id=device_id,
                    device_name=device_info.name,
                    primary_ip=device_info.primary_ip,
                    platform=device_info.platform,
                )
                device_cache_service.get_or_create_device_cache(db, device_cache_data)

                interfaces_to_cache = []
                ip_addresses_to_cache = []

                for interface_data in output:
                    # Try both uppercase and lowercase field names (different TextFSM templates use different cases)
                    interface_name = (
                        interface_data.get("INTERFACE")
                        or interface_data.get("interface")
                        or ""
                    ).strip()
                    if not interface_name:
                        logger.warning(
                            f"Skipping interface with empty name: {interface_data}"
                        )
                        continue

                    # Get speed - try speed field first, then bandwidth as fallback
                    speed = (
                        interface_data.get("SPEED")
                        or interface_data.get("speed")
                        or interface_data.get("BANDWIDTH")
                        or interface_data.get("bandwidth")
                        or ""
                    ).strip()

                    # Get duplex
                    duplex = (
                        interface_data.get("DUPLEX")
                        or interface_data.get("duplex")
                        or ""
                    ).strip()

                    # Get VLAN ID
                    vlan_str = (
                        interface_data.get("VLAN_ID")
                        or interface_data.get("vlan_id")
                        or ""
                    ).strip()
                    vlan_id = None
                    if vlan_str and vlan_str.isdigit():
                        vlan_id = int(vlan_str)

                    # Get description
                    description = (
                        interface_data.get("DESCRIPTION")
                        or interface_data.get("description")
                        or ""
                    ).strip()

                    # Map TextFSM fields to cache schema (try both cases)
                    interface_cache = InterfaceCacheCreate(
                        device_id=device_id,
                        interface_name=interface_name,
                        mac_address=interface_data.get("MAC_ADDRESS")
                        or interface_data.get("mac_address"),
                        status=interface_data.get("LINK_STATUS")
                        or interface_data.get("link_status"),
                        description=description if description else None,
                        speed=speed if speed else None,
                        duplex=duplex if duplex else None,
                        vlan_id=vlan_id,
                    )
                    interfaces_to_cache.append(interface_cache)

                    # Extract IP address information if present
                    ip_address = (
                        interface_data.get("IP_ADDRESS")
                        or interface_data.get("ip_address")
                        or ""
                    ).strip()
                    if ip_address and ip_address != "":
                        prefix_length = (
                            interface_data.get("PREFIX_LENGTH")
                            or interface_data.get("prefix_length")
                            or ""
                        ).strip()

                        # Convert prefix length to subnet mask if needed
                        subnet_mask = None
                        if prefix_length and prefix_length.isdigit():
                            # Store as CIDR notation (e.g., "/24")
                            subnet_mask = f"/{prefix_length}"

                        ip_cache = IPAddressCacheCreate(
                            device_id=device_id,
                            interface_name=interface_name,
                            ip_address=ip_address,
                            subnet_mask=subnet_mask,
                            ip_version=4,  # Assuming IPv4 from show interfaces
                            is_primary=False,  # Would need additional logic to determine primary
                        )
                        ip_addresses_to_cache.append(ip_cache)

                # Bulk upsert interfaces
                device_cache_service.bulk_upsert_interfaces(
                    db, device_id, interfaces_to_cache
                )
                logger.info(
                    f"Successfully cached {len(interfaces_to_cache)} interfaces"
                )

                # Bulk upsert IP addresses
                if ip_addresses_to_cache:
                    device_cache_service.bulk_upsert_ips(
                        db, device_id, ip_addresses_to_cache
                    )
                    logger.info(
                        f"Successfully cached {len(ip_addresses_to_cache)} IP addresses"
                    )

        return DeviceCommandResponse(
            success=result["success"],
            output=result.get("output"),
            error=result.get("error"),
            device_info=device_info.model_dump(),
            command="show interfaces",
            execution_time=result.get("execution_time"),
            parsed=result.get("parsed", False),
            parser_used=result.get("parser_used"),
            cached=used_cache,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting interfaces for device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get interfaces: {str(e)}",
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
            cached=False,
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
