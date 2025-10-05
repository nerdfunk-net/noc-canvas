"""
API endpoints for network topology building and visualization.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.topology import (
    TopologyGraph,
    TopologyStatistics,
    TopologyBuildRequest,
    NeighborResolution,
    TopologyDiscoveryRequest,
    TopologyDiscoveryProgress,
    TopologyDiscoveryResult
)
from app.services.topology_builder_service import TopologyBuilderService
from app.services.topology_discovery_service import TopologyDiscoveryService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/topology", tags=["topology"])


@router.get("/build", response_model=TopologyGraph)
async def build_topology(
    device_ids: Optional[List[str]] = Query(None, description="Device IDs to include (empty = all cached devices)"),
    include_cdp: bool = Query(True, description="Include CDP/LLDP neighbor links"),
    include_routing: bool = Query(False, description="Include routing table links"),
    route_types: List[str] = Query(["static", "ospf", "bgp"], description="Route types to include"),
    include_layer2: bool = Query(False, description="Include Layer 2 MAC/ARP links"),
    auto_layout: bool = Query(True, description="Auto-calculate node positions"),
    layout_algorithm: str = Query("force_directed", description="Layout algorithm (force_directed, hierarchical, circular)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Build topology from cached data with flexible options.

    This is the main endpoint for topology building. It allows you to:
    - Select specific devices or use all cached devices
    - Choose which data sources to include (CDP, routing, Layer 2)
    - Filter routing data by type (static, OSPF, BGP)
    - Auto-calculate node positions using various layout algorithms

    Returns a complete topology graph with nodes and links.
    """
    try:
        logger.info(f"Building topology. CDP: {include_cdp}, Routing: {include_routing}, L2: {include_layer2}")

        topology = TopologyBuilderService.build_topology_from_cache(
            db=db,
            device_ids=device_ids,
            include_cdp=include_cdp,
            include_routing=include_routing,
            route_types=route_types,
            include_layer2=include_layer2,
            auto_layout=auto_layout,
            layout_algorithm=layout_algorithm
        )

        logger.info(f"Topology built: {len(topology.nodes)} nodes, {len(topology.links)} links")
        return topology

    except Exception as e:
        logger.error(f"Error building topology: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to build topology: {str(e)}")


@router.post("/build", response_model=TopologyGraph)
async def build_topology_post(
    request: TopologyBuildRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Build topology using POST request with JSON body.

    Alternative to GET endpoint for complex requests.
    """
    try:
        topology = TopologyBuilderService.build_topology_from_cache(
            db=db,
            device_ids=request.device_ids,
            include_cdp=request.include_cdp,
            include_routing=request.include_routing,
            route_types=request.route_types,
            include_layer2=request.include_layer2,
            auto_layout=request.auto_layout,
            layout_algorithm=request.layout_algorithm or "force_directed"
        )

        return topology

    except Exception as e:
        logger.error(f"Error building topology: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to build topology: {str(e)}")


@router.get("/cdp", response_model=TopologyGraph)
async def get_cdp_topology(
    device_ids: Optional[List[str]] = Query(None, description="Device IDs to include"),
    auto_layout: bool = Query(True, description="Auto-calculate node positions"),
    layout_algorithm: str = Query("force_directed", description="Layout algorithm"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get CDP/LLDP neighbor-based topology only.

    This builds a physical topology showing direct Layer 2/3 connections
    between devices based on CDP/LLDP neighbor discovery.
    """
    try:
        topology = TopologyBuilderService.build_cdp_topology(
            db=db,
            device_ids=device_ids,
            auto_layout=auto_layout
        )

        return topology

    except Exception as e:
        logger.error(f"Error building CDP topology: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to build CDP topology: {str(e)}")


@router.get("/routing", response_model=TopologyGraph)
async def get_routing_topology(
    device_ids: Optional[List[str]] = Query(None, description="Device IDs to include"),
    route_types: List[str] = Query(["static", "ospf", "bgp"], description="Route types to include"),
    auto_layout: bool = Query(True, description="Auto-calculate node positions"),
    layout_algorithm: str = Query("force_directed", description="Layout algorithm"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get routing table-based topology.

    This builds a logical Layer 3 topology showing routing relationships
    between devices based on their routing tables (static, OSPF, BGP).
    """
    try:
        topology = TopologyBuilderService.build_routing_topology(
            db=db,
            device_ids=device_ids,
            route_types=route_types,
            auto_layout=auto_layout
        )

        return topology

    except Exception as e:
        logger.error(f"Error building routing topology: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to build routing topology: {str(e)}")


@router.get("/layer2", response_model=TopologyGraph)
async def get_layer2_topology(
    device_ids: Optional[List[str]] = Query(None, description="Device IDs to include"),
    auto_layout: bool = Query(True, description="Auto-calculate node positions"),
    layout_algorithm: str = Query("force_directed", description="Layout algorithm"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get Layer 2 topology from MAC/ARP tables.

    This builds a topology based on MAC address learning and ARP tables,
    showing which devices are connected at Layer 2.
    """
    try:
        topology = TopologyBuilderService.build_layer2_topology(
            db=db,
            device_ids=device_ids,
            auto_layout=auto_layout
        )

        return topology

    except Exception as e:
        logger.error(f"Error building Layer 2 topology: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to build Layer 2 topology: {str(e)}")


@router.post("/resolve-neighbor", response_model=NeighborResolution)
async def resolve_neighbor(
    neighbor_name: str,
    neighbor_ip: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Resolve neighbor name/IP to device_id in cache.

    Useful for debugging neighbor resolution issues or validating
    that CDP neighbors can be matched to cached devices.
    """
    try:
        resolution = TopologyBuilderService.resolve_neighbor(
            db=db,
            neighbor_name=neighbor_name,
            neighbor_ip=neighbor_ip
        )

        return resolution

    except Exception as e:
        logger.error(f"Error resolving neighbor: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to resolve neighbor: {str(e)}")


@router.get("/statistics", response_model=TopologyStatistics)
async def get_topology_statistics(
    device_ids: Optional[List[str]] = Query(None, description="Device IDs to include"),
    include_cdp: bool = Query(True, description="Include CDP links"),
    include_routing: bool = Query(False, description="Include routing links"),
    route_types: List[str] = Query(["static", "ospf", "bgp"], description="Route types"),
    include_layer2: bool = Query(False, description="Include Layer 2 links"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get statistics about the topology.

    Returns comprehensive statistics including:
    - Total devices and links
    - Link types breakdown
    - Devices by platform
    - Isolated devices count
    - Average connections per device
    """
    try:
        # Build topology first
        topology = TopologyBuilderService.build_topology_from_cache(
            db=db,
            device_ids=device_ids,
            include_cdp=include_cdp,
            include_routing=include_routing,
            route_types=route_types,
            include_layer2=include_layer2,
            auto_layout=False  # Don't need positions for statistics
        )

        # Calculate statistics
        statistics = TopologyBuilderService.get_topology_statistics(db, topology)

        return statistics

    except Exception as e:
        logger.error(f"Error getting topology statistics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get topology statistics: {str(e)}")


@router.post("/discover", response_model=TopologyDiscoveryResult)
async def discover_topology(
    request: TopologyDiscoveryRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
):
    """
    Discover topology data from devices.

    This endpoint collects all necessary data from devices to build a topology:
    - Static routes (show ip route static)
    - OSPF routes (show ip route ospf)
    - BGP routes (show ip route bgp)
    - MAC address table (show mac address-table)
    - CDP neighbors (show cdp neighbors)

    The discovery can run in foreground (blocking) or background (non-blocking).
    Progress can be tracked using the /topology/discover/progress/{job_id} endpoint.

    Args:
        request: Discovery request with device IDs and options
        run_in_background: If True, runs as background job (future: Celery)
        cache_results: If True, stores results in cache database

    Returns:
        Discovery result with job_id, status, and collected data
    """
    try:
        logger.info(f"📡 Topology discovery requested for {len(request.device_ids)} devices")
        logger.info(f"   Background: {request.run_in_background}, Cache: {request.cache_results}")

        if request.run_in_background:
            # For now, just create a job and return immediately
            # TODO: Implement with Celery for true background execution
            job_id = TopologyDiscoveryService.create_job(request.device_ids)

            # Start discovery in background (placeholder - will use Celery)
            import asyncio
            asyncio.create_task(
                TopologyDiscoveryService.discover_topology(
                    device_ids=request.device_ids,
                    include_static_routes=request.include_static_routes,
                    include_ospf_routes=request.include_ospf_routes,
                    include_bgp_routes=request.include_bgp_routes,
                    include_mac_table=request.include_mac_table,
                    include_cdp_neighbors=request.include_cdp_neighbors,
                    cache_results=request.cache_results,
                    auth_token=credentials.credentials,
                    db=db
                )
            )

            return {
                "job_id": job_id,
                "status": "in_progress",
                "total_devices": len(request.device_ids),
                "successful_devices": 0,
                "failed_devices": 0,
                "devices_data": {},
                "errors": {},
                "duration_seconds": 0
            }
        else:
            # Run in foreground (blocking)
            result = await TopologyDiscoveryService.discover_topology(
                device_ids=request.device_ids,
                include_static_routes=request.include_static_routes,
                include_ospf_routes=request.include_ospf_routes,
                include_bgp_routes=request.include_bgp_routes,
                include_mac_table=request.include_mac_table,
                include_cdp_neighbors=request.include_cdp_neighbors,
                cache_results=request.cache_results,
                auth_token=credentials.credentials,
                db=db
            )

            return result

    except Exception as e:
        logger.error(f"Error during topology discovery: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to discover topology: {str(e)}")


@router.get("/discover/progress/{job_id}", response_model=TopologyDiscoveryProgress)
async def get_discovery_progress(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get progress for a topology discovery job.

    This endpoint allows you to track the progress of a discovery job,
    including per-device status and overall completion percentage.

    Args:
        job_id: The job ID returned from the /topology/discover endpoint

    Returns:
        Discovery progress with device-level details
    """
    try:
        progress = TopologyDiscoveryService.get_job_progress(job_id)

        if not progress:
            raise HTTPException(status_code=404, detail=f"Discovery job {job_id} not found")

        return progress

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting discovery progress: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get discovery progress: {str(e)}")


@router.get("/discover/result/{job_id}", response_model=TopologyDiscoveryResult)
async def get_discovery_result(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the final result of a topology discovery job.

    This endpoint returns the complete discovery results including all
    collected data from devices.

    Args:
        job_id: The job ID returned from the /topology/discover endpoint

    Returns:
        Complete discovery result with all device data
    """
    try:
        job = TopologyDiscoveryService.get_job_progress(job_id)

        if not job:
            raise HTTPException(status_code=404, detail=f"Discovery job {job_id} not found")

        if job["status"] not in ["completed", "failed"]:
            raise HTTPException(
                status_code=400,
                detail=f"Discovery job {job_id} is still {job['status']}. Use /discover/progress/{job_id} to check progress."
            )

        return {
            "job_id": job["job_id"],
            "status": job["status"],
            "total_devices": job["total_devices"],
            "successful_devices": job["completed_devices"] - job["failed_devices"],
            "failed_devices": job["failed_devices"],
            "devices_data": job.get("devices_data", {}),
            "errors": job.get("errors", {}),
            "duration_seconds": job.get("duration_seconds", 0)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting discovery result: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get discovery result: {str(e)}")
