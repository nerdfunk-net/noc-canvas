"""
CheckMK API router for host management and monitoring.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from ..core.security import get_current_user, verify_admin_user
from ..models.checkmk import (
    CheckMKTestConnectionRequest,
    CheckMKTestConnectionResponse,
    CheckMKHostCreateRequest,
    CheckMKHostUpdateRequest,
    CheckMKHostMoveRequest,
    CheckMKHostRenameRequest,
    CheckMKBulkHostCreateRequest,
    CheckMKBulkHostUpdateRequest,
    CheckMKBulkHostDeleteRequest,
    CheckMKServiceQueryRequest,
    CheckMKServiceDiscoveryRequest,
    CheckMKDiscoveryPhaseUpdateRequest,
    CheckMKAcknowledgeHostRequest,
    CheckMKAcknowledgeServiceRequest,
    CheckMKDowntimeRequest,
    CheckMKCommentRequest,
    CheckMKActivateChangesRequest,
    CheckMKHostGroupCreateRequest,
    CheckMKHostGroupUpdateRequest,
    CheckMKHostGroupBulkUpdateRequest,
    CheckMKHostGroupBulkDeleteRequest,
    CheckMKFolderCreateRequest,
    CheckMKFolderUpdateRequest,
    CheckMKFolderMoveRequest,
    CheckMKFolderBulkUpdateRequest,
    CheckMKHostTagGroupCreateRequest,
    CheckMKHostTagGroupUpdateRequest,
    CheckMKHostListResponse,
    CheckMKFolderListResponse,
    CheckMKHostTagGroupListResponse,
    CheckMKVersionResponse,
    CheckMKOperationResponse,
    CheckMKStats,
    CheckMKHealthCheck,
)
from ..services.checkmk import checkmk_service
from ..services.checkmk_client import CheckMKAPIError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/test", response_model=CheckMKTestConnectionResponse)
async def test_checkmk_connection(
    request: CheckMKTestConnectionRequest,
    current_user: dict = Depends(verify_admin_user),
):
    """Test CheckMK connection with provided settings."""
    try:
        success, message = await checkmk_service.test_connection(
            request.url,
            request.site,
            request.username,
            request.password,
            request.verify_ssl,
        )

        return CheckMKTestConnectionResponse(
            success=success,
            message=message,
            checkmk_url=request.url,
            connection_source="manual_test",
        )
    except Exception as e:
        logger.error(f"Error testing CheckMK connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test CheckMK connection: {str(e)}",
        )


@router.get("/test")
async def test_current_checkmk_connection(
    current_user: dict = Depends(verify_admin_user),
):
    """Test current CheckMK connection using configured settings."""
    try:
        from ..core.config import settings

        if not settings.checkmk_url or not settings.checkmk_site or not settings.checkmk_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CheckMK settings not configured. Please configure CheckMK settings first.",
            )

        success, message = await checkmk_service.test_connection(
            settings.checkmk_url,
            settings.checkmk_site,
            settings.checkmk_username,
            settings.checkmk_password,
            settings.checkmk_verify_ssl,
        )

        return {
            "success": success,
            "message": message,
            "checkmk_url": settings.checkmk_url,
            "connection_source": "environment",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing CheckMK connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test CheckMK connection: {str(e)}",
        )


@router.get("/stats", response_model=CheckMKStats)
async def get_checkmk_stats(current_user: dict = Depends(verify_admin_user)):
    """Get CheckMK statistics."""
    try:
        stats = await checkmk_service.get_stats()
        return CheckMKStats(**stats)
    except Exception as e:
        logger.error(f"Error fetching CheckMK stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch CheckMK statistics: {str(e)}",
        )


@router.get("/version", response_model=CheckMKVersionResponse)
async def get_version(current_user: dict = Depends(verify_admin_user)):
    """Get CheckMK version information."""
    try:
        version_data = await checkmk_service.get_version()
        return CheckMKVersionResponse(
            version=version_data.get("version", "unknown"),
            edition=version_data.get("edition"),
            demo=version_data.get("demo", False),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting CheckMK version: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get CheckMK version: {str(e)}",
        )


# Host Management Endpoints

@router.get("/hosts", response_model=CheckMKHostListResponse)
async def get_all_hosts(
    effective_attributes: bool = False,
    include_links: bool = False,
    site: Optional[str] = None,
    current_user: dict = Depends(verify_admin_user),
):
    """Get all hosts from CheckMK."""
    try:
        result = await checkmk_service.get_all_hosts(
            effective_attributes=effective_attributes,
            include_links=include_links,
            site=site,
        )

        hosts = []
        for host_data in result.get("value", []):
            hosts.append(
                {
                    "host_name": host_data.get("id"),
                    "folder": host_data.get("extensions", {}).get("folder", "/"),
                    "attributes": host_data.get("extensions", {}).get("attributes", {}),
                    "effective_attributes": host_data.get("extensions", {}).get(
                        "effective_attributes"
                    )
                    if effective_attributes
                    else None,
                }
            )

        return CheckMKHostListResponse(hosts=hosts, total=len(hosts))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting hosts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get hosts: {str(e)}",
        )


@router.get("/hosts/{hostname}", response_model=CheckMKOperationResponse)
async def get_host(
    hostname: str,
    effective_attributes: bool = False,
    current_user: dict = Depends(verify_admin_user),
):
    """Get specific host configuration."""
    try:
        result = await checkmk_service.get_host(hostname, effective_attributes)
        return CheckMKOperationResponse(
            success=True, message=f"Host {hostname} retrieved successfully", data=result
        )
    except CheckMKAPIError as e:
        if e.status_code == 404:
            logger.info(f"Host {hostname} not found in CheckMK")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Host '{hostname}' not found in CheckMK",
            )
        else:
            logger.error(
                f"CheckMK API error getting host {hostname}: {str(e)} (status: {e.status_code})"
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"CheckMK API error: {str(e)}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting host {hostname}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get host {hostname}: {str(e)}",
        )


@router.post("/hosts", response_model=CheckMKOperationResponse)
async def create_host(
    request: CheckMKHostCreateRequest,
    current_user: dict = Depends(verify_admin_user),
):
    """Create new host in CheckMK."""
    try:
        result = await checkmk_service.create_host(
            hostname=request.host_name,
            folder=request.folder,
            attributes=request.attributes,
            bake_agent=request.bake_agent,
        )

        return CheckMKOperationResponse(
            success=True,
            message=f"Host {request.host_name} created successfully",
            data=result,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating host {request.host_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create host {request.host_name}: {str(e)}",
        )


@router.put("/hosts/{hostname}", response_model=CheckMKOperationResponse)
async def update_host(
    hostname: str,
    request: CheckMKHostUpdateRequest,
    current_user: dict = Depends(verify_admin_user),
):
    """Update existing host configuration."""
    try:
        result = await checkmk_service.update_host(hostname, request.attributes)
        return CheckMKOperationResponse(
            success=True, message=f"Host {hostname} updated successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating host {hostname}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update host {hostname}: {str(e)}",
        )


@router.delete("/hosts/{hostname}", response_model=CheckMKOperationResponse)
async def delete_host(
    hostname: str,
    current_user: dict = Depends(verify_admin_user),
):
    """Delete host from CheckMK."""
    try:
        await checkmk_service.delete_host(hostname)
        return CheckMKOperationResponse(
            success=True, message=f"Host {hostname} deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting host {hostname}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete host {hostname}: {str(e)}",
        )


@router.post("/hosts/{hostname}/move", response_model=CheckMKOperationResponse)
async def move_host(
    hostname: str,
    request: CheckMKHostMoveRequest,
    current_user: dict = Depends(verify_admin_user),
):
    """Move host to different folder."""
    try:
        result = await checkmk_service.move_host(hostname, request.target_folder)
        return CheckMKOperationResponse(
            success=True,
            message=f"Host {hostname} moved to {request.target_folder} successfully",
            data=result,
        )
    except CheckMKAPIError as e:
        if e.status_code == 428:
            raise HTTPException(
                status_code=status.HTTP_428_PRECONDITION_REQUIRED,
                detail=f"Cannot move host '{hostname}' - CheckMK changes need to be activated first",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST
                if e.status_code == 400
                else status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to move host '{hostname}': {str(e)}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error moving host {hostname}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to move host {hostname}: {str(e)}",
        )


@router.post("/hosts/{hostname}/rename", response_model=CheckMKOperationResponse)
async def rename_host(
    hostname: str,
    request: CheckMKHostRenameRequest,
    current_user: dict = Depends(verify_admin_user),
):
    """Rename host."""
    try:
        result = await checkmk_service.rename_host(hostname, request.new_name)
        return CheckMKOperationResponse(
            success=True,
            message=f"Host {hostname} renamed to {request.new_name} successfully",
            data=result,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error renaming host {hostname}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rename host {hostname}: {str(e)}",
        )


# Bulk Host Operations

@router.post("/hosts/bulk-create", response_model=CheckMKOperationResponse)
async def bulk_create_hosts(
    request: CheckMKBulkHostCreateRequest,
    current_user: dict = Depends(verify_admin_user),
):
    """Create multiple hosts in one request."""
    try:
        # Convert request to format expected by CheckMK client
        hosts = []
        for host_req in request.entries:
            hosts.append(
                {
                    "host_name": host_req.host_name,
                    "folder": host_req.folder,
                    "attributes": host_req.attributes,
                }
            )

        result = await checkmk_service.bulk_create_hosts(hosts)
        return CheckMKOperationResponse(
            success=True,
            message=f"Created {len(request.entries)} hosts successfully",
            data=result,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk creating hosts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk create hosts: {str(e)}",
        )


@router.post("/hosts/bulk-update", response_model=CheckMKOperationResponse)
async def bulk_update_hosts(
    request: CheckMKBulkHostUpdateRequest,
    current_user: dict = Depends(verify_admin_user),
):
    """Update multiple hosts in one request."""
    try:
        # Convert request to format expected by CheckMK client
        hosts = {}
        for hostname, update_req in request.entries.items():
            hosts[hostname] = {"attributes": update_req.attributes}

        result = await checkmk_service.bulk_update_hosts(hosts)
        return CheckMKOperationResponse(
            success=True,
            message=f"Updated {len(request.entries)} hosts successfully",
            data=result,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk updating hosts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update hosts: {str(e)}",
        )


@router.post("/hosts/bulk-delete", response_model=CheckMKOperationResponse)
async def bulk_delete_hosts(
    request: CheckMKBulkHostDeleteRequest,
    current_user: dict = Depends(verify_admin_user),
):
    """Delete multiple hosts in one request."""
    try:
        result = await checkmk_service.bulk_delete_hosts(request.entries)
        return CheckMKOperationResponse(
            success=True,
            message=f"Deleted {len(request.entries)} hosts successfully",
            data=result,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk deleting hosts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk delete hosts: {str(e)}",
        )


# Host Monitoring & Status Endpoints

@router.get("/monitoring/hosts", response_model=CheckMKOperationResponse)
async def get_all_monitored_hosts(
    request: CheckMKServiceQueryRequest = None,
    current_user: dict = Depends(verify_admin_user),
):
    """Get all monitored hosts with status information."""
    try:
        columns = request.columns if request else None
        query = request.query if request else None

        result = await checkmk_service.get_all_monitored_hosts(columns=columns, query=query)
        return CheckMKOperationResponse(
            success=True, message="Retrieved monitored hosts successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting monitored hosts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitored hosts: {str(e)}",
        )


@router.get("/monitoring/hosts/{hostname}", response_model=CheckMKOperationResponse)
async def get_monitored_host(
    hostname: str,
    request: CheckMKServiceQueryRequest = None,
    current_user: dict = Depends(verify_admin_user),
):
    """Get monitored host with status information."""
    try:
        columns = request.columns if request else None
        result = await checkmk_service.get_monitored_host(hostname, columns=columns)

        return CheckMKOperationResponse(
            success=True,
            message=f"Retrieved monitoring data for host {hostname} successfully",
            data=result,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting monitored host {hostname}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitored host {hostname}: {str(e)}",
        )


@router.get("/hosts/{hostname}/services", response_model=CheckMKOperationResponse)
async def get_host_services(
    hostname: str,
    request: CheckMKServiceQueryRequest = None,
    current_user: dict = Depends(verify_admin_user),
):
    """Get services for a specific host."""
    try:
        columns = request.columns if request else None
        query = request.query if request else None

        result = await checkmk_service.get_host_services(hostname, columns=columns, query=query)
        return CheckMKOperationResponse(
            success=True,
            message=f"Retrieved services for host {hostname} successfully",
            data=result,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting services for host {hostname}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get services for host {hostname}: {str(e)}",
        )


# Service Discovery Endpoints

@router.get("/hosts/{hostname}/discovery", response_model=CheckMKOperationResponse)
async def get_service_discovery(
    hostname: str,
    current_user: dict = Depends(verify_admin_user),
):
    """Get service discovery status for a host."""
    try:
        result = await checkmk_service.get_service_discovery(hostname)
        return CheckMKOperationResponse(
            success=True,
            message=f"Retrieved service discovery status for host {hostname} successfully",
            data=result,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service discovery for host {hostname}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service discovery for host {hostname}: {str(e)}",
        )


@router.post("/hosts/{hostname}/discovery/start", response_model=CheckMKOperationResponse)
async def start_service_discovery(
    hostname: str,
    request: CheckMKServiceDiscoveryRequest = CheckMKServiceDiscoveryRequest(),
    current_user: dict = Depends(verify_admin_user),
):
    """Start service discovery for a host."""
    try:
        result = await checkmk_service.start_service_discovery(hostname, request.mode)
        return CheckMKOperationResponse(
            success=True,
            message=f"Started service discovery for host {hostname} successfully",
            data=result,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting service discovery for host {hostname}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start service discovery for host {hostname}: {str(e)}",
        )


# Configuration Management Endpoints

@router.get("/changes/pending", response_model=CheckMKOperationResponse)
async def get_pending_changes(
    current_user: dict = Depends(verify_admin_user),
):
    """Get pending configuration changes."""
    try:
        result = await checkmk_service.get_pending_changes()
        return CheckMKOperationResponse(
            success=True, message="Retrieved pending changes successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pending changes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending changes: {str(e)}",
        )


@router.post("/changes/activate", response_model=CheckMKOperationResponse)
async def activate_changes(
    request: CheckMKActivateChangesRequest = CheckMKActivateChangesRequest(),
    current_user: dict = Depends(verify_admin_user),
):
    """Activate pending configuration changes."""
    try:
        result = await checkmk_service.activate_changes(
            sites=request.sites,
            force_foreign_changes=request.force_foreign_changes,
            redirect=request.redirect,
        )

        return CheckMKOperationResponse(
            success=True,
            message="Activated configuration changes successfully",
            data=result,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating changes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate changes: {str(e)}",
        )


# Folder Management Endpoints

@router.get("/folders", response_model=CheckMKFolderListResponse)
async def get_all_folders(
    parent: Optional[str] = None,
    recursive: bool = False,
    show_hosts: bool = False,
    current_user: dict = Depends(verify_admin_user),
):
    """Get all folders."""
    try:
        result = await checkmk_service.get_all_folders(
            parent=parent, recursive=recursive, show_hosts=show_hosts
        )

        folders = []
        for folder_data in result.get("value", []):
            folder_info = folder_data.get("extensions", {})
            folders.append(
                {
                    "name": folder_data.get("id", ""),
                    "title": folder_data.get("title", ""),
                    "parent": folder_info.get("parent", "/"),
                    "path": folder_info.get("path", "/"),
                    "attributes": folder_info.get("attributes", {}),
                    "hosts": folder_info.get("hosts", []) if show_hosts else None,
                }
            )

        return CheckMKFolderListResponse(folders=folders, total=len(folders))
    except CheckMKAPIError as e:
        logger.error(f"CheckMK API error getting folders: status={e.status_code}, parent={parent}")

        if e.status_code == 400:
            checkmk_error_detail = "Invalid folder request"
            if hasattr(e, "response_data") and e.response_data:
                response_data = e.response_data
                if "fields" in response_data and "parent" in response_data["fields"]:
                    parent_errors = response_data["fields"]["parent"]
                    if parent_errors:
                        checkmk_error_detail = parent_errors[0]
                elif "detail" in response_data:
                    checkmk_error_detail = response_data["detail"]

            if "could not be found" in checkmk_error_detail.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=checkmk_error_detail,
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=checkmk_error_detail,
                )
        elif e.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent folder '{parent}' not found in CheckMK",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"CheckMK API error: {str(e)}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting folders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get folders: {str(e)}",
        )


@router.get("/folders/{folder_path}", response_model=CheckMKOperationResponse)
async def get_folder(
    folder_path: str,
    show_hosts: bool = False,
    current_user: dict = Depends(verify_admin_user),
):
    """Get specific folder."""
    try:
        result = await checkmk_service.get_folder(folder_path, show_hosts=show_hosts)
        return CheckMKOperationResponse(
            success=True,
            message=f"Retrieved folder {folder_path} successfully",
            data=result,
        )
    except CheckMKAPIError as e:
        if e.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Folder '{folder_path}' not found in CheckMK",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"CheckMK API error: {str(e)}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting folder {folder_path}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get folder {folder_path}: {str(e)}",
        )


@router.post("/folders", response_model=CheckMKOperationResponse)
async def create_folder(
    request: CheckMKFolderCreateRequest,
    current_user: dict = Depends(verify_admin_user),
):
    """Create new folder."""
    try:
        result = await checkmk_service.create_folder(
            name=request.name,
            title=request.title,
            parent=request.parent,
            attributes=request.attributes,
        )

        return CheckMKOperationResponse(
            success=True,
            message=f"Created folder {request.name} successfully",
            data=result,
        )
    except CheckMKAPIError as e:
        checkmk_error_detail = str(e)
        validation_errors = []

        if hasattr(e, "response_data") and e.response_data:
            response_data = e.response_data

            if isinstance(response_data, dict):
                if "detail" in response_data:
                    checkmk_error_detail = response_data["detail"]

                if "fields" in response_data and response_data["fields"]:
                    for field, errors in response_data["fields"].items():
                        if errors is not None:
                            if isinstance(errors, list):
                                for error in errors:
                                    validation_errors.append(f"{field}: {error}")
                            else:
                                validation_errors.append(f"{field}: {errors}")

        if validation_errors:
            checkmk_error_detail = f"{checkmk_error_detail} - {'; '.join(validation_errors)}"

        logger.error(f"CheckMK folder creation failed: {checkmk_error_detail}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST
            if e.status_code == 400
            else status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to create folder: {checkmk_error_detail}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating folder {request.name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create folder {request.name}: {str(e)}",
        )


@router.get("/health-check", response_model=CheckMKHealthCheck)
async def checkmk_health_check(
    current_user: dict = Depends(get_current_user),
):
    """Simple health check to verify CheckMK connectivity."""
    try:
        stats = await checkmk_service.get_stats()
        return CheckMKHealthCheck(
            status="connected",
            message="CheckMK is accessible",
            total_hosts=stats.get("total_hosts", 0),
        )
    except Exception as e:
        logger.error(f"CheckMK health check failed: {str(e)}")

        error_msg = str(e)
        if "403" in error_msg or "Invalid" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="CheckMK connection failed: Invalid credentials or insufficient permissions.",
            )
        elif "ConnectionError" in error_msg or "timeout" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="CheckMK connection failed: Cannot reach CheckMK server.",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"CheckMK connection failed: {error_msg}",
            )