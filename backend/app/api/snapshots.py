"""
Snapshots API for managing device baselines and snapshots.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from ..core.database import get_db
from ..core.security import verify_token
from ..models.user import User
from ..models.device_cache import Snapshot, SnapshotType
from ..services.structured_comparison import StructuredComparator

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
            status_code=401,
            detail="Invalid authentication credentials",
        )
    username = token_data["username"]
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("/check")
async def check_snapshot_exists(
    device_id: str = Query(..., description="Device UUID"),
    type: str = Query("baseline", description="Snapshot type: baseline or snapshot"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Check if a snapshot/baseline exists for a device.

    Returns information about the most recent snapshot/baseline if it exists.
    """
    try:
        # Convert type string to enum
        snapshot_type = SnapshotType.BASELINE if type.lower() == "baseline" else SnapshotType.SNAPSHOT

        # Get the most recent snapshot of the specified type
        latest_snapshot = (
            db.query(Snapshot)
            .filter(
                and_(
                    Snapshot.device_id == device_id,
                    Snapshot.type == snapshot_type,
                )
            )
            .order_by(desc(Snapshot.updated_at))
            .first()
        )

        if not latest_snapshot:
            return {
                "exists": False,
                "device_id": device_id,
                "type": type,
            }

        # Get count of commands for this device
        command_count = (
            db.query(Snapshot)
            .filter(
                and_(
                    Snapshot.device_id == device_id,
                    Snapshot.type == snapshot_type,
                )
            )
            .count()
        )

        return {
            "exists": True,
            "device_id": device_id,
            "device_name": latest_snapshot.device_name,
            "type": type,
            "version": latest_snapshot.version,
            "created_at": latest_snapshot.created_at.isoformat() if latest_snapshot.created_at else None,
            "updated_at": latest_snapshot.updated_at.isoformat() if latest_snapshot.updated_at else None,
            "notes": latest_snapshot.notes,
            "command_count": command_count,
        }

    except Exception as e:
        logger.error(f"Error checking snapshot existence: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check snapshot: {str(e)}"
        )


@router.get("/list")
async def list_snapshots(
    device_id: Optional[str] = Query(None, description="Filter by device UUID"),
    type: Optional[str] = Query(None, description="Filter by type: baseline or snapshot"),
    grouped: bool = Query(True, description="Group snapshots by snapshot_group_id"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List snapshots/baselines.

    Can filter by device_id and/or type.
    If grouped=True, returns grouped snapshots (one entry per snapshot session).
    If grouped=False, returns individual command snapshots.
    """
    try:
        query = db.query(Snapshot)

        if device_id:
            query = query.filter(Snapshot.device_id == device_id)

        if type:
            snapshot_type = SnapshotType.BASELINE if type.lower() == "baseline" else SnapshotType.SNAPSHOT
            query = query.filter(Snapshot.type == snapshot_type)

        snapshots = query.order_by(desc(Snapshot.created_at)).all()

        if grouped:
            # Group snapshots by snapshot_group_id
            groups = {}
            for s in snapshots:
                group_id = s.snapshot_group_id or str(s.id)  # Fallback for old snapshots without group_id
                if group_id not in groups:
                    groups[group_id] = {
                        "snapshot_group_id": s.snapshot_group_id,
                        "device_id": s.device_id,
                        "device_name": s.device_name,
                        "type": s.type.value,
                        "created_at": s.created_at.isoformat() if s.created_at else None,
                        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                        "notes": s.notes,
                        "command_count": 0,
                        "commands": [],
                    }
                groups[group_id]["command_count"] += 1
                groups[group_id]["commands"].append(s.command)
                # Use the latest updated_at if any command was updated
                if s.updated_at:
                    current_updated = groups[group_id]["updated_at"]
                    if not current_updated or s.updated_at.isoformat() > current_updated:
                        groups[group_id]["updated_at"] = s.updated_at.isoformat()

            return list(groups.values())
        else:
            # Return individual snapshots
            return [
                {
                    "id": s.id,
                    "device_id": s.device_id,
                    "device_name": s.device_name,
                    "command": s.command,
                    "type": s.type.value,
                    "version": s.version,
                    "snapshot_group_id": s.snapshot_group_id,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                    "notes": s.notes,
                }
                for s in snapshots
            ]

    except Exception as e:
        logger.error(f"Error listing snapshots: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list snapshots: {str(e)}"
        )


@router.get("/{snapshot_id}")
async def get_snapshot_detail(
    snapshot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific snapshot, including its output data.
    """
    try:
        snapshot = db.query(Snapshot).filter(Snapshot.id == snapshot_id).first()

        if not snapshot:
            raise HTTPException(
                status_code=404,
                detail=f"Snapshot with id {snapshot_id} not found"
            )

        return {
            "id": snapshot.id,
            "device_id": snapshot.device_id,
            "device_name": snapshot.device_name,
            "command": snapshot.command,
            "type": snapshot.type.value,
            "version": snapshot.version,
            "created_at": snapshot.created_at.isoformat() if snapshot.created_at else None,
            "updated_at": snapshot.updated_at.isoformat() if snapshot.updated_at else None,
            "notes": snapshot.notes,
            "raw_output": snapshot.raw_output,
            "normalized_output": snapshot.normalized_output,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting snapshot detail: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get snapshot: {str(e)}"
        )


@router.delete("/{snapshot_id}")
async def delete_snapshot(
    snapshot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a specific snapshot by ID.
    """
    try:
        snapshot = db.query(Snapshot).filter(Snapshot.id == snapshot_id).first()

        if not snapshot:
            raise HTTPException(
                status_code=404,
                detail=f"Snapshot with id {snapshot_id} not found"
            )

        # Store info for response
        device_name = snapshot.device_name
        command = snapshot.command

        # Delete the snapshot
        db.delete(snapshot)
        db.commit()

        logger.info(f"Deleted snapshot {snapshot_id} for device {device_name}, command: {command}")

        return {
            "success": True,
            "message": f"Snapshot deleted successfully",
            "id": snapshot_id,
            "device_name": device_name,
            "command": command,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting snapshot: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete snapshot: {str(e)}"
        )


@router.delete("/group/{snapshot_group_id}")
async def delete_snapshot_group(
    snapshot_group_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete all snapshots in a group by snapshot_group_id.
    """
    try:
        # Find all snapshots in this group
        snapshots = db.query(Snapshot).filter(Snapshot.snapshot_group_id == snapshot_group_id).all()

        if not snapshots:
            raise HTTPException(
                status_code=404,
                detail=f"No snapshots found with group_id {snapshot_group_id}"
            )

        # Store info for response
        device_name = snapshots[0].device_name
        count = len(snapshots)

        # Delete all snapshots in the group
        db.query(Snapshot).filter(Snapshot.snapshot_group_id == snapshot_group_id).delete()
        db.commit()

        logger.info(f"Deleted snapshot group {snapshot_group_id} for device {device_name} ({count} commands)")

        return {
            "success": True,
            "message": f"Deleted {count} snapshots from group",
            "snapshot_group_id": snapshot_group_id,
            "device_name": device_name,
            "count": count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting snapshot group: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete snapshot group: {str(e)}"
        )


@router.post("/compare")
async def compare_snapshots(
    baseline_id: int = Query(..., description="Baseline snapshot ID"),
    snapshot_id: int = Query(..., description="Snapshot ID to compare"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Compare baseline and snapshot using structured comparison.

    Returns a structured comparison result if the command is supported,
    otherwise returns None.
    """
    try:
        # Fetch both snapshots
        baseline = db.query(Snapshot).filter(Snapshot.id == baseline_id).first()
        snapshot = db.query(Snapshot).filter(Snapshot.id == snapshot_id).first()

        if not baseline:
            raise HTTPException(
                status_code=404,
                detail=f"Baseline snapshot with id {baseline_id} not found"
            )

        if not snapshot:
            raise HTTPException(
                status_code=404,
                detail=f"Snapshot with id {snapshot_id} not found"
            )

        # Verify they are for the same command
        if baseline.command != snapshot.command:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot compare different commands: {baseline.command} vs {snapshot.command}"
            )

        # Try structured comparison
        comparison_result = StructuredComparator.compare(
            command=baseline.command,
            baseline_output=baseline.normalized_output,
            snapshot_output=snapshot.normalized_output
        )

        if comparison_result:
            # Add metadata
            comparison_result["baseline"] = {
                "id": baseline.id,
                "device_name": baseline.device_name,
                "created_at": baseline.created_at.isoformat() if baseline.created_at else None,
                "type": baseline.type.value
            }
            comparison_result["snapshot"] = {
                "id": snapshot.id,
                "device_name": snapshot.device_name,
                "created_at": snapshot.created_at.isoformat() if snapshot.created_at else None,
                "type": snapshot.type.value
            }

            return {
                "supported": True,
                "comparison": comparison_result
            }
        else:
            # Command not supported for structured comparison
            return {
                "supported": False,
                "message": f"Command '{baseline.command}' does not have structured comparison support"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing snapshots: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compare snapshots: {str(e)}"
        )
