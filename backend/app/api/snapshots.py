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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List snapshots/baselines.

    Can filter by device_id and/or type.
    """
    try:
        query = db.query(Snapshot)

        if device_id:
            query = query.filter(Snapshot.device_id == device_id)

        if type:
            snapshot_type = SnapshotType.BASELINE if type.lower() == "baseline" else SnapshotType.SNAPSHOT
            query = query.filter(Snapshot.type == snapshot_type)

        snapshots = query.order_by(desc(Snapshot.updated_at)).all()

        return [
            {
                "id": s.id,
                "device_id": s.device_id,
                "device_name": s.device_name,
                "command": s.command,
                "type": s.type.value,
                "version": s.version,
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
