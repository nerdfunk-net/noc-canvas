"""
Jobs API router for background task management.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from ..core.security import verify_admin_user
from ..services.background_jobs import background_job_service

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response Models

class JobSubmissionRequest(BaseModel):
    """Job submission request."""
    task_name: str = Field(..., description="Name of the task to execute")
    args: List[Any] = Field(default_factory=list, description="Positional arguments")
    kwargs: Dict[str, Any] = Field(default_factory=dict, description="Keyword arguments")


class JobStatusResponse(BaseModel):
    """Job status response."""
    id: str
    status: str
    result: Optional[Any] = None
    traceback: Optional[str] = None
    info: Optional[Any] = None


class JobSubmissionResponse(BaseModel):
    """Job submission response."""
    job_id: str
    message: str
    status: str = "submitted"


class SyncDevicesRequest(BaseModel):
    """Sync devices job request."""
    limit: Optional[int] = None
    offset: Optional[int] = None
    filter_type: Optional[str] = None
    filter_value: Optional[str] = None


class SyncHostsRequest(BaseModel):
    """Sync hosts job request."""
    effective_attributes: bool = False
    include_links: bool = False
    site: Optional[str] = None


class BulkHostOperationRequest(BaseModel):
    """Bulk host operation request."""
    operation: str = Field(..., description="Operation type: create, update, delete")
    hosts_data: List[Dict[str, Any]] = Field(..., description="Host data for the operation")


# Job Management Endpoints

@router.post("/submit", response_model=JobSubmissionResponse)
async def submit_job(
    request: JobSubmissionRequest,
    current_user: dict = Depends(verify_admin_user),
):
    """Submit a background job."""
    try:
        job_id = background_job_service.submit_job(
            request.task_name,
            *request.args,
            **request.kwargs
        )

        return JobSubmissionResponse(
            job_id=job_id,
            message=f"Job {request.task_name} submitted successfully",
        )
    except Exception as e:
        logger.error(f"Error submitting job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit job: {str(e)}",
        )


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(verify_admin_user),
):
    """Get job status and result."""
    try:
        job_status = background_job_service.get_job_status(job_id)
        return JobStatusResponse(**job_status)
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}",
        )


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    current_user: dict = Depends(verify_admin_user),
):
    """Cancel a running job."""
    try:
        success = background_job_service.cancel_job(job_id)
        if success:
            return {"message": f"Job {job_id} cancelled successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to cancel job {job_id}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel job: {str(e)}",
        )


# Predefined Job Types

@router.post("/sync/nautobot-devices", response_model=JobSubmissionResponse)
async def sync_nautobot_devices(
    request: SyncDevicesRequest = SyncDevicesRequest(),
    current_user: dict = Depends(verify_admin_user),
):
    """Start a job to sync devices from Nautobot."""
    try:
        filters = {
            "limit": request.limit,
            "offset": request.offset,
            "filter_type": request.filter_type,
            "filter_value": request.filter_value,
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}

        job_id = background_job_service.submit_job(
            "app.services.background_jobs.sync_nautobot_devices",
            filters if filters else None
        )

        return JobSubmissionResponse(
            job_id=job_id,
            message="Nautobot device sync job started successfully",
        )
    except Exception as e:
        logger.error(f"Error starting Nautobot sync job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start Nautobot sync job: {str(e)}",
        )


@router.post("/sync/checkmk-hosts", response_model=JobSubmissionResponse)
async def sync_checkmk_hosts(
    request: SyncHostsRequest = SyncHostsRequest(),
    current_user: dict = Depends(verify_admin_user),
):
    """Start a job to sync hosts from CheckMK."""
    try:
        filters = {
            "effective_attributes": request.effective_attributes,
            "include_links": request.include_links,
            "site": request.site,
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}

        job_id = background_job_service.submit_job(
            "app.services.background_jobs.sync_checkmk_hosts",
            filters if filters else None
        )

        return JobSubmissionResponse(
            job_id=job_id,
            message="CheckMK host sync job started successfully",
        )
    except Exception as e:
        logger.error(f"Error starting CheckMK sync job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start CheckMK sync job: {str(e)}",
        )


@router.post("/bulk/host-operations", response_model=JobSubmissionResponse)
async def bulk_host_operations(
    request: BulkHostOperationRequest,
    current_user: dict = Depends(verify_admin_user),
):
    """Start a job for bulk host operations."""
    try:
        if request.operation not in ["create", "update", "delete"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Operation must be one of: create, update, delete",
            )

        job_id = background_job_service.submit_job(
            "app.services.background_jobs.bulk_host_operations",
            request.operation,
            request.hosts_data
        )

        return JobSubmissionResponse(
            job_id=job_id,
            message=f"Bulk {request.operation} job started successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting bulk operation job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start bulk operation job: {str(e)}",
        )


@router.post("/cache/warm-up", response_model=JobSubmissionResponse)
async def warm_up_cache(
    current_user: dict = Depends(verify_admin_user),
):
    """Start a job to warm up application caches."""
    try:
        job_id = background_job_service.submit_job(
            "app.services.background_jobs.cache_warm_up"
        )

        return JobSubmissionResponse(
            job_id=job_id,
            message="Cache warm-up job started successfully",
        )
    except Exception as e:
        logger.error(f"Error starting cache warm-up job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start cache warm-up job: {str(e)}",
        )


# Job Health and Monitoring

@router.get("/health")
async def get_job_system_health(
    current_user: dict = Depends(verify_admin_user),
):
    """Get job system health status."""
    try:
        # Try to inspect active tasks
        inspect = background_job_service.celery.control.inspect()

        # Get worker stats
        stats = inspect.stats()
        active_tasks = inspect.active()

        return {
            "status": "healthy" if stats else "no_workers",
            "message": "Job system is operational" if stats else "No workers available",
            "workers": list(stats.keys()) if stats else [],
            "active_tasks_count": sum(len(tasks) for tasks in active_tasks.values()) if active_tasks else 0,
        }
    except Exception as e:
        logger.error(f"Error checking job system health: {str(e)}")
        return {
            "status": "error",
            "message": f"Job system health check failed: {str(e)}",
            "workers": [],
            "active_tasks_count": 0,
        }


@router.get("/workers")
async def get_worker_info(
    current_user: dict = Depends(verify_admin_user),
):
    """Get information about active workers."""
    try:
        inspect = background_job_service.celery.control.inspect()

        stats = inspect.stats()
        active_tasks = inspect.active()
        reserved_tasks = inspect.reserved()

        workers_info = []

        if stats:
            for worker_name, worker_stats in stats.items():
                worker_info = {
                    "name": worker_name,
                    "status": "online",
                    "pool": worker_stats.get("pool", {}),
                    "active_tasks": len(active_tasks.get(worker_name, [])) if active_tasks else 0,
                    "reserved_tasks": len(reserved_tasks.get(worker_name, [])) if reserved_tasks else 0,
                    "processed_tasks": worker_stats.get("total", {}),
                }
                workers_info.append(worker_info)

        return {
            "workers": workers_info,
            "total_workers": len(workers_info),
        }
    except Exception as e:
        logger.error(f"Error getting worker info: {str(e)}")
        return {
            "workers": [],
            "total_workers": 0,
            "error": str(e),
        }