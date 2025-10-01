"""
Jobs API router for background task management.

This module has been significantly reduced as most job endpoints are unused by the frontend.
The new job monitoring functionality is now handled via /api/settings/jobs/* endpoints.
"""

import logging
from fastapi import APIRouter, Depends
from ..core.security import get_current_user
from ..services.background_jobs import background_job_service

logger = logging.getLogger(__name__)
router = APIRouter()


# Job Health and Monitoring - Keeping these for potential future use


@router.get("/health")
async def get_job_system_health(
    current_user: dict = Depends(get_current_user),
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
            "active_tasks_count": sum(len(tasks) for tasks in active_tasks.values())
            if active_tasks
            else 0,
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
    current_user: dict = Depends(get_current_user),
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
                    "active_tasks": len(active_tasks.get(worker_name, []))
                    if active_tasks
                    else 0,
                    "reserved_tasks": len(reserved_tasks.get(worker_name, []))
                    if reserved_tasks
                    else 0,
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
