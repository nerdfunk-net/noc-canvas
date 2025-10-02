from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import json
from ..core.database import get_db
from ..models.canvas import Canvas
from ..api.auth import get_current_user
from ..models.user import User

router = APIRouter()


class CanvasDeviceData(BaseModel):
    id: int
    name: str
    device_type: str
    ip_address: Optional[str] = None
    position_x: float
    position_y: float
    properties: Optional[str] = None


class CanvasConnectionData(BaseModel):
    id: int
    source_device_id: int
    target_device_id: int
    connection_type: str
    properties: Optional[str] = None


class CanvasShapeData(BaseModel):
    id: int
    shape_type: str
    position_x: float
    position_y: float
    width: float
    height: float
    fill_color: Optional[str] = None
    stroke_color: Optional[str] = None
    stroke_width: Optional[float] = None


class CanvasData(BaseModel):
    devices: List[CanvasDeviceData]
    connections: List[CanvasConnectionData]
    shapes: Optional[List[CanvasShapeData]] = []


class CanvasCreate(BaseModel):
    name: str
    sharable: bool = False
    canvas_data: CanvasData


class CanvasUpdate(BaseModel):
    name: Optional[str] = None
    sharable: Optional[bool] = None
    canvas_data: Optional[CanvasData] = None


class CanvasResponse(BaseModel):
    id: int
    name: str
    owner_id: int
    sharable: bool
    canvas_data: CanvasData
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CanvasListItem(BaseModel):
    """Canvas list item with owner info for the load canvas modal"""

    id: int
    name: str
    owner_id: int
    owner_username: str
    sharable: bool
    is_own: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[CanvasResponse])
async def get_canvases(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Get all canvases accessible to the current user (owned by them or sharable)"""
    canvases = (
        db.query(Canvas)
        .filter((Canvas.owner_id == current_user.id) | Canvas.sharable)
        .all()
    )

    # Parse JSON canvas_data for each canvas
    result = []
    for canvas in canvases:
        canvas_dict = {
            "id": canvas.id,
            "name": canvas.name,
            "owner_id": canvas.owner_id,
            "sharable": canvas.sharable,
            "canvas_data": json.loads(canvas.canvas_data),
            "created_at": canvas.created_at,
            "updated_at": canvas.updated_at,
        }
        result.append(canvas_dict)

    return result


@router.get("/list", response_model=List[CanvasListItem])
async def get_canvas_list(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Get list of canvases for the load canvas modal"""
    from sqlalchemy.orm import joinedload

    canvases = (
        db.query(Canvas)
        .options(joinedload(Canvas.owner))
        .filter((Canvas.owner_id == current_user.id) | Canvas.sharable)
        .all()
    )

    result = []
    for canvas in canvases:
        canvas_item = CanvasListItem(
            id=canvas.id,
            name=canvas.name,
            owner_id=canvas.owner_id,
            owner_username=canvas.owner.username,
            sharable=canvas.sharable,
            is_own=(canvas.owner_id == current_user.id),
            created_at=canvas.created_at,
            updated_at=canvas.updated_at,
        )
        result.append(canvas_item)

    return result


@router.post("/", response_model=CanvasResponse)
async def save_canvas(
    canvas: CanvasCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save a new canvas"""
    canvas_data_json = json.dumps(canvas.canvas_data.dict())

    db_canvas = Canvas(
        name=canvas.name,
        owner_id=current_user.id,
        sharable=canvas.sharable,
        canvas_data=canvas_data_json,
    )

    db.add(db_canvas)
    db.commit()
    db.refresh(db_canvas)

    # Return with parsed canvas_data
    return CanvasResponse(
        id=db_canvas.id,
        name=db_canvas.name,
        owner_id=db_canvas.owner_id,
        sharable=db_canvas.sharable,
        canvas_data=json.loads(db_canvas.canvas_data),
        created_at=db_canvas.created_at,
        updated_at=db_canvas.updated_at,
    )


@router.get("/{canvas_id}", response_model=CanvasResponse)
async def get_canvas(
    canvas_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific canvas by ID"""
    canvas = db.query(Canvas).filter(Canvas.id == canvas_id).first()
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")

    # Check if user has access (owner or canvas is sharable)
    if canvas.owner_id != current_user.id and not canvas.sharable:
        raise HTTPException(status_code=403, detail="Access denied")

    return CanvasResponse(
        id=canvas.id,
        name=canvas.name,
        owner_id=canvas.owner_id,
        sharable=canvas.sharable,
        canvas_data=json.loads(canvas.canvas_data),
        created_at=canvas.created_at,
        updated_at=canvas.updated_at,
    )


@router.put("/{canvas_id}", response_model=CanvasResponse)
async def update_canvas(
    canvas_id: int,
    canvas_update: CanvasUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing canvas"""
    canvas = db.query(Canvas).filter(Canvas.id == canvas_id).first()
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")

    # Only owner can update
    if canvas.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only canvas owner can update")

    # Update fields
    update_data = canvas_update.dict(exclude_unset=True)
    if "canvas_data" in update_data:
        update_data["canvas_data"] = json.dumps(update_data["canvas_data"])

    for field, value in update_data.items():
        setattr(canvas, field, value)

    canvas.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(canvas)

    return CanvasResponse(
        id=canvas.id,
        name=canvas.name,
        owner_id=canvas.owner_id,
        sharable=canvas.sharable,
        canvas_data=json.loads(canvas.canvas_data),
        created_at=canvas.created_at,
        updated_at=canvas.updated_at,
    )


@router.delete("/{canvas_id}")
async def delete_canvas(
    canvas_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a canvas"""
    canvas = db.query(Canvas).filter(Canvas.id == canvas_id).first()
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")

    # Only owner can delete
    if canvas.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only canvas owner can delete")

    db.delete(canvas)
    db.commit()
    return {"message": "Canvas deleted successfully"}
