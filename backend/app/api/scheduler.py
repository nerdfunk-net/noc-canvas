"""
Scheduler API for managing periodic tasks (cron jobs).
"""

import json
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from ..core.database import get_db
from ..core.security import verify_token
from ..models.user import User
from ..models.scheduled_task_owner import ScheduledTaskOwner
from ..services.background_jobs import celery_app, CELERY_AVAILABLE

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get current authenticated user."""
    token = credentials.credentials
    token_data = verify_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = token_data["username"]
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


# Pydantic models for API

class CrontabSchedule(BaseModel):
    """Crontab schedule configuration."""
    minute: str = Field(default="*", description="Minute (0-59, *, */5, etc.)")
    hour: str = Field(default="*", description="Hour (0-23, *, */2, etc.)")
    day_of_week: str = Field(default="*", description="Day of week (0-6, mon-sun, *, etc.)")
    day_of_month: str = Field(default="*", description="Day of month (1-31, *, */2, etc.)")
    month_of_year: str = Field(default="*", description="Month (1-12, jan-dec, *, etc.)")


class IntervalSchedule(BaseModel):
    """Interval schedule configuration."""
    every: int = Field(gt=0, description="Interval value")
    period: str = Field(description="Period type: seconds, minutes, hours, days")


class PeriodicTaskCreate(BaseModel):
    """Create a new periodic task."""
    name: str = Field(description="Unique task name")
    task: str = Field(description="Task to execute (e.g., 'app.tasks.nautobot_tasks.sync_nautobot_devices')")
    description: Optional[str] = Field(None, description="Task description")

    # Schedule type - either crontab or interval
    schedule_type: str = Field(description="Schedule type: 'crontab' or 'interval'")
    crontab: Optional[CrontabSchedule] = None
    interval: Optional[IntervalSchedule] = None

    # Task arguments
    args: Optional[List[Any]] = Field(default_factory=list, description="Positional arguments as JSON array")
    kwargs: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Keyword arguments as JSON object")

    # Task options
    enabled: bool = Field(default=True, description="Whether the task is enabled")
    one_off: bool = Field(default=False, description="If True, run only once then disable")
    expires: Optional[datetime] = Field(None, description="Task expiry datetime")


class PeriodicTaskUpdate(BaseModel):
    """Update a periodic task."""
    name: Optional[str] = None
    task: Optional[str] = None
    description: Optional[str] = None
    schedule_type: Optional[str] = None
    crontab: Optional[CrontabSchedule] = None
    interval: Optional[IntervalSchedule] = None
    args: Optional[List[Any]] = None
    kwargs: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None
    one_off: Optional[bool] = None
    expires: Optional[datetime] = None


class PeriodicTaskResponse(BaseModel):
    """Periodic task response."""
    id: int
    name: str
    task: str
    description: Optional[str]
    schedule_type: str
    crontab: Optional[Dict[str, str]]
    interval: Optional[Dict[str, Any]]
    args: List[Any]
    kwargs: Dict[str, Any]
    enabled: bool
    one_off: bool
    last_run_at: Optional[datetime]
    total_run_count: int
    date_changed: datetime
    expires: Optional[datetime]
    owner_username: Optional[str] = None  # Owner of the scheduled task


# Helper functions

def get_schedule_tables():
    """Get schedule tables from celery-sqlalchemy-scheduler."""
    if not CELERY_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Celery is not available"
        )

    from celery_sqlalchemy_scheduler.models import (
        PeriodicTask,
        IntervalSchedule as IntervalScheduleModel,
        CrontabSchedule as CrontabScheduleModel,
    )
    from celery_sqlalchemy_scheduler.session import SessionManager

    return PeriodicTask, IntervalScheduleModel, CrontabScheduleModel, SessionManager


def get_db_uri():
    """Get the database URI for Celery Beat scheduler."""
    from ..core.database import engine

    # Get database URI with password
    try:
        db_uri = engine.url.render_as_string(hide_password=False)
    except AttributeError:
        # Fallback for older SQLAlchemy versions
        db_uri = str(engine.url).replace('***', engine.url.password or '')

    return db_uri


def deserialize_json_field(value, default):
    """Safely deserialize a JSON field from the database."""
    if value is None:
        return default
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return default
    return value


# API Endpoints

@router.get("/tasks", response_model=List[PeriodicTaskResponse])
async def list_periodic_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all periodic tasks."""
    try:
        PeriodicTask, _, _, SessionManager = get_schedule_tables()
        db_uri = get_db_uri()

        session_manager = SessionManager()
        session = session_manager.session_factory(db_uri)

        try:
            tasks = session.query(PeriodicTask).all()

            result = []
            for task in tasks:
                # Look up owner from our tracking table
                owner = db.query(ScheduledTaskOwner).filter(
                    ScheduledTaskOwner.periodic_task_id == task.id
                ).first()
                
                task_data = {
                    "id": task.id,
                    "name": task.name,
                    "task": task.task,
                    "description": task.description,
                    "schedule_type": "",
                    "crontab": None,
                    "interval": None,
                    "args": deserialize_json_field(task.args, []),
                    "kwargs": deserialize_json_field(task.kwargs, {}),
                    "enabled": task.enabled if task.enabled is not None else True,
                    "one_off": task.one_off if task.one_off is not None else False,
                    "last_run_at": task.last_run_at,
                    "total_run_count": task.total_run_count if task.total_run_count is not None else 0,
                    "date_changed": task.date_changed,
                    "expires": task.expires,
                    "owner_username": owner.owner_username if owner else None,
                }

                # Determine schedule type and data
                if task.crontab:
                    task_data["schedule_type"] = "crontab"
                    task_data["crontab"] = {
                        "minute": task.crontab.minute,
                        "hour": task.crontab.hour,
                        "day_of_week": task.crontab.day_of_week,
                        "day_of_month": task.crontab.day_of_month,
                        "month_of_year": task.crontab.month_of_year,
                    }
                elif task.interval:
                    task_data["schedule_type"] = "interval"
                    task_data["interval"] = {
                        "every": task.interval.every,
                        "period": task.interval.period,
                    }

                result.append(PeriodicTaskResponse(**task_data))

            return result
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error listing periodic tasks: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list periodic tasks: {str(e)}"
        )


@router.post("/tasks", response_model=PeriodicTaskResponse)
async def create_periodic_task(
    task_data: PeriodicTaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new periodic task."""
    try:
        PeriodicTask, IntervalScheduleModel, CrontabScheduleModel, SessionManager = get_schedule_tables()
        db_uri = get_db_uri()

        session_manager = SessionManager()
        session = session_manager.session_factory(db_uri)

        try:
            # Check if task with same name already exists
            existing = session.query(PeriodicTask).filter(PeriodicTask.name == task_data.name).first()
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Task with name '{task_data.name}' already exists"
                )

            # Create schedule
            schedule = None
            if task_data.schedule_type == "crontab":
                if not task_data.crontab:
                    raise HTTPException(status_code=400, detail="Crontab schedule is required")

                # Check if crontab schedule already exists
                schedule = session.query(CrontabScheduleModel).filter(
                    CrontabScheduleModel.minute == task_data.crontab.minute,
                    CrontabScheduleModel.hour == task_data.crontab.hour,
                    CrontabScheduleModel.day_of_week == task_data.crontab.day_of_week,
                    CrontabScheduleModel.day_of_month == task_data.crontab.day_of_month,
                    CrontabScheduleModel.month_of_year == task_data.crontab.month_of_year,
                ).first()

                if not schedule:
                    schedule = CrontabScheduleModel(
                        minute=task_data.crontab.minute,
                        hour=task_data.crontab.hour,
                        day_of_week=task_data.crontab.day_of_week,
                        day_of_month=task_data.crontab.day_of_month,
                        month_of_year=task_data.crontab.month_of_year,
                    )
                    session.add(schedule)
                    session.flush()

            elif task_data.schedule_type == "interval":
                if not task_data.interval:
                    raise HTTPException(status_code=400, detail="Interval schedule is required")

                # Check if interval schedule already exists
                schedule = session.query(IntervalScheduleModel).filter(
                    IntervalScheduleModel.every == task_data.interval.every,
                    IntervalScheduleModel.period == task_data.interval.period,
                ).first()

                if not schedule:
                    schedule = IntervalScheduleModel(
                        every=task_data.interval.every,
                        period=task_data.interval.period,
                    )
                    session.add(schedule)
                    session.flush()
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Schedule type must be 'crontab' or 'interval'"
                )

            # Prepare kwargs - inject username for credential lookup
            task_kwargs = task_data.kwargs.copy() if task_data.kwargs else {}
            # Add username to kwargs so background tasks can look up the correct user's credentials
            if 'username' not in task_kwargs:
                task_kwargs['username'] = current_user.username
            
            # Create periodic task
            periodic_task = PeriodicTask(
                name=task_data.name,
                task=task_data.task,
                description=task_data.description,
                enabled=task_data.enabled,
                one_off=task_data.one_off,
                expires=task_data.expires,
                args=json.dumps(task_data.args) if task_data.args else '[]',
                kwargs=json.dumps(task_kwargs),
            )

            # Set the schedule
            if task_data.schedule_type == "crontab":
                periodic_task.crontab = schedule
            else:
                periodic_task.interval = schedule

            session.add(periodic_task)
            session.commit()
            session.refresh(periodic_task)
            
            # Record task ownership in our tracking table
            try:
                task_owner = ScheduledTaskOwner(
                    periodic_task_id=periodic_task.id,
                    owner_username=current_user.username,
                    owner_id=current_user.id
                )
                db.add(task_owner)
                db.commit()
                logger.info(f"Recorded ownership: task {periodic_task.id} owned by {current_user.username}")
            except Exception as e:
                logger.error(f"Failed to record task ownership: {e}")
                # Don't fail the entire operation, but log the error
                db.rollback()

            # Build response
            response_data = {
                "id": periodic_task.id,
                "name": periodic_task.name,
                "task": periodic_task.task,
                "description": periodic_task.description,
                "schedule_type": task_data.schedule_type,
                "crontab": task_data.crontab.dict() if task_data.crontab else None,
                "interval": task_data.interval.dict() if task_data.interval else None,
                "args": deserialize_json_field(periodic_task.args, []),
                "kwargs": deserialize_json_field(periodic_task.kwargs, {}),
                "enabled": periodic_task.enabled if periodic_task.enabled is not None else True,
                "one_off": periodic_task.one_off if periodic_task.one_off is not None else False,
                "last_run_at": periodic_task.last_run_at,
                "total_run_count": periodic_task.total_run_count if periodic_task.total_run_count is not None else 0,
                "date_changed": periodic_task.date_changed,
                "expires": periodic_task.expires,
                "owner_username": current_user.username,  # Include owner in response
            }

            logger.info(f"Created periodic task: {periodic_task.name}")
            return PeriodicTaskResponse(**response_data)

        except HTTPException:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create periodic task: {str(e)}"
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating periodic task: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create periodic task: {str(e)}"
        )


@router.get("/tasks/{task_id}", response_model=PeriodicTaskResponse)
async def get_periodic_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific periodic task."""
    try:
        PeriodicTask, _, _, SessionManager = get_schedule_tables()
        db_uri = get_db_uri()

        session_manager = SessionManager()
        session = session_manager.session_factory(db_uri)

        try:
            task = session.query(PeriodicTask).filter(PeriodicTask.id == task_id).first()
            if not task:
                raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")

            # Look up owner from our tracking table
            owner = db.query(ScheduledTaskOwner).filter(
                ScheduledTaskOwner.periodic_task_id == task.id
            ).first()

            task_data = {
                "id": task.id,
                "name": task.name,
                "task": task.task,
                "description": task.description,
                "schedule_type": "",
                "crontab": None,
                "interval": None,
                "args": deserialize_json_field(task.args, []),
                "kwargs": deserialize_json_field(task.kwargs, {}),
                "enabled": task.enabled if task.enabled is not None else True,
                "one_off": task.one_off if task.one_off is not None else False,
                "last_run_at": task.last_run_at,
                "total_run_count": task.total_run_count if task.total_run_count is not None else 0,
                "date_changed": task.date_changed,
                "expires": task.expires,
                "owner_username": owner.owner_username if owner else None,
            }

            if task.crontab:
                task_data["schedule_type"] = "crontab"
                task_data["crontab"] = {
                    "minute": task.crontab.minute,
                    "hour": task.crontab.hour,
                    "day_of_week": task.crontab.day_of_week,
                    "day_of_month": task.crontab.day_of_month,
                    "month_of_year": task.crontab.month_of_year,
                }
            elif task.interval:
                task_data["schedule_type"] = "interval"
                task_data["interval"] = {
                    "every": task.interval.every,
                    "period": task.interval.period,
                }

            return PeriodicTaskResponse(**task_data)
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting periodic task: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get periodic task: {str(e)}"
        )


@router.put("/tasks/{task_id}", response_model=PeriodicTaskResponse)
async def update_periodic_task(
    task_id: int,
    task_update: PeriodicTaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a periodic task."""
    try:
        PeriodicTask, IntervalScheduleModel, CrontabScheduleModel, SessionManager = get_schedule_tables()
        db_uri = get_db_uri()

        session_manager = SessionManager()
        session = session_manager.session_factory(db_uri)

        try:
            task = session.query(PeriodicTask).filter(PeriodicTask.id == task_id).first()
            if not task:
                raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")

            # Get only fields that were explicitly set in the request
            update_data = task_update.model_dump(exclude_unset=True)

            # Update basic fields
            if 'name' in update_data:
                # Check for name conflict
                if task_update.name:
                    existing = session.query(PeriodicTask).filter(
                        PeriodicTask.name == task_update.name,
                        PeriodicTask.id != task_id
                    ).first()
                    if existing:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Task with name '{task_update.name}' already exists"
                        )
                task.name = task_update.name

            if 'task' in update_data:
                task.task = task_update.task
            if 'description' in update_data:
                task.description = task_update.description
            if 'enabled' in update_data:
                task.enabled = task_update.enabled
            if 'one_off' in update_data:
                task.one_off = task_update.one_off
            if 'expires' in update_data:
                # This will now properly set expires to None when explicitly sent as null
                task.expires = task_update.expires
            if 'args' in update_data:
                task.args = json.dumps(task_update.args) if task_update.args is not None else '[]'
            if 'kwargs' in update_data:
                task.kwargs = json.dumps(task_update.kwargs) if task_update.kwargs is not None else '{}'

            # Update schedule if provided
            if 'schedule_type' in update_data:
                if task_update.schedule_type == "crontab" and task_update.crontab:
                    # Find or create crontab schedule
                    schedule = session.query(CrontabScheduleModel).filter(
                        CrontabScheduleModel.minute == task_update.crontab.minute,
                        CrontabScheduleModel.hour == task_update.crontab.hour,
                        CrontabScheduleModel.day_of_week == task_update.crontab.day_of_week,
                        CrontabScheduleModel.day_of_month == task_update.crontab.day_of_month,
                        CrontabScheduleModel.month_of_year == task_update.crontab.month_of_year,
                    ).first()

                    if not schedule:
                        schedule = CrontabScheduleModel(
                            minute=task_update.crontab.minute,
                            hour=task_update.crontab.hour,
                            day_of_week=task_update.crontab.day_of_week,
                            day_of_month=task_update.crontab.day_of_month,
                            month_of_year=task_update.crontab.month_of_year,
                        )
                        session.add(schedule)
                        session.flush()

                    task.crontab = schedule
                    task.interval = None

                elif task_update.schedule_type == "interval" and task_update.interval:
                    # Find or create interval schedule
                    schedule = session.query(IntervalScheduleModel).filter(
                        IntervalScheduleModel.every == task_update.interval.every,
                        IntervalScheduleModel.period == task_update.interval.period,
                    ).first()

                    if not schedule:
                        schedule = IntervalScheduleModel(
                            every=task_update.interval.every,
                            period=task_update.interval.period,
                        )
                        session.add(schedule)
                        session.flush()

                    task.interval = schedule
                    task.crontab = None

            session.commit()
            session.refresh(task)

            # Build response
            response_data = {
                "id": task.id,
                "name": task.name,
                "task": task.task,
                "description": task.description,
                "schedule_type": "",
                "crontab": None,
                "interval": None,
                "args": deserialize_json_field(task.args, []),
                "kwargs": deserialize_json_field(task.kwargs, {}),
                "enabled": task.enabled if task.enabled is not None else True,
                "one_off": task.one_off if task.one_off is not None else False,
                "last_run_at": task.last_run_at,
                "total_run_count": task.total_run_count if task.total_run_count is not None else 0,
                "date_changed": task.date_changed,
                "expires": task.expires,
            }

            if task.crontab:
                response_data["schedule_type"] = "crontab"
                response_data["crontab"] = {
                    "minute": task.crontab.minute,
                    "hour": task.crontab.hour,
                    "day_of_week": task.crontab.day_of_week,
                    "day_of_month": task.crontab.day_of_month,
                    "month_of_year": task.crontab.month_of_year,
                }
            elif task.interval:
                response_data["schedule_type"] = "interval"
                response_data["interval"] = {
                    "every": task.interval.every,
                    "period": task.interval.period,
                }

            logger.info(f"Updated periodic task: {task.name}")
            return PeriodicTaskResponse(**response_data)

        except HTTPException:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update periodic task: {str(e)}"
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating periodic task: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update periodic task: {str(e)}"
        )


@router.delete("/tasks/{task_id}")
async def delete_periodic_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a periodic task."""
    try:
        PeriodicTask, _, _, SessionManager = get_schedule_tables()
        db_uri = get_db_uri()

        session_manager = SessionManager()
        session = session_manager.session_factory(db_uri)

        try:
            task = session.query(PeriodicTask).filter(PeriodicTask.id == task_id).first()
            if not task:
                raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")

            task_name = task.name
            session.delete(task)
            session.commit()
            
            # Also delete the ownership record
            try:
                owner = db.query(ScheduledTaskOwner).filter(
                    ScheduledTaskOwner.periodic_task_id == task_id
                ).first()
                if owner:
                    db.delete(owner)
                    db.commit()
                    logger.info(f"Deleted ownership record for task {task_id}")
            except Exception as e:
                logger.error(f"Failed to delete ownership record: {e}")
                db.rollback()

            logger.info(f"Deleted periodic task: {task_name}")
            return {"message": f"Periodic task '{task_name}' deleted successfully"}

        except HTTPException:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete periodic task: {str(e)}"
            )
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting periodic task: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete periodic task: {str(e)}"
        )


@router.get("/available-tasks")
async def get_available_tasks(
    current_user: User = Depends(get_current_user),
):
    """Get list of available tasks that can be scheduled."""
    # Return list of tasks registered in Celery
    available_tasks = [
        {
            "name": "sync_nautobot_devices",
            "task": "app.tasks.nautobot_tasks.sync_nautobot_devices",
            "description": "Synchronize devices from Nautobot",
            "supports_inventory": False,
            "args_schema": {},
            "kwargs_schema": {
                "limit": "int (optional)",
                "offset": "int (optional)",
                "filter_type": "string (optional)",
                "filter_value": "string (optional)",
            }
        },
        {
            "name": "sync_checkmk_hosts",
            "task": "app.tasks.checkmk_tasks.sync_checkmk_hosts",
            "description": "Synchronize hosts from CheckMK",
            "supports_inventory": False,
            "args_schema": {},
            "kwargs_schema": {
                "effective_attributes": "boolean (optional)",
                "include_links": "boolean (optional)",
                "site": "string (optional)",
            }
        },
        {
            "name": "cache_warm_up",
            "task": "app.tasks.cache_tasks.cache_warm_up",
            "description": "Pre-load frequently accessed data into cache",
            "supports_inventory": False,
            "args_schema": {},
            "kwargs_schema": {}
        },
        {
            "name": "discover_topology",
            "task": "app.tasks.topology_tasks.discover_topology_task",
            "description": "Discover and map network topology",
            "supports_inventory": True,
            "args_schema": {},
            "kwargs_schema": {
                "seed_devices": "array of device IDs (optional) - If not provided and inventory_id is set, uses inventory devices",
                "inventory_id": "int (optional) - Use devices from this inventory",
                "max_depth": "int (optional, default: 3)",
                "discover_neighbors": "boolean (optional, default: true)",
            }
        },
        {
            "name": "cleanup_old_data",
            "task": "app.tasks.cleanup_tasks.cleanup_old_data",
            "description": "Remove old tasks and stale data",
            "supports_inventory": False,
            "args_schema": {},
            "kwargs_schema": {
                "days_to_keep": "int (optional, default: 7) - Number of days to keep historical data",
            }
        },
        {
            "name": "create_baseline",
            "task": "app.tasks.baseline_tasks.create_baseline",
            "description": "Create baseline configuration snapshots for devices",
            "supports_inventory": True,
            "args_schema": {},
            "kwargs_schema": {
                "device_ids": "array of device IDs (optional) - If not provided and inventory_id is set, uses inventory devices",
                "inventory_id": "int (optional) - Use devices from this inventory",
                "commands": "array of commands (optional) - Specific commands to execute. If not provided, runs all default commands",
                "notes": "string (optional) - Notes about this baseline (e.g., 'Pre-upgrade baseline')",
                "username": "string (auto-injected) - Username for credential lookup. Automatically set to the user who created the scheduled task",
            }
        },
        {
            "name": "test_job",
            "task": "app.tasks.test_tasks.test_background_task",
            "description": "Test task for system verification",
            "supports_inventory": False,
            "args_schema": {},
            "kwargs_schema": {
                "message": "string (optional)",
                "duration": "int (optional, seconds)",
            }
        },
    ]

    return available_tasks


@router.get("/inventories")
async def get_inventories_for_scheduler(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get list of available inventories for task scheduling."""
    from ..models.inventory import Inventory
    
    inventories = db.query(Inventory).order_by(Inventory.name).all()
    
    return [
        {
            "id": inv.id,
            "name": inv.name,
            "description": inv.description or "",
        }
        for inv in inventories
    ]
