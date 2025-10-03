from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.shape import Shape

router = APIRouter()


class ShapeCreate(BaseModel):
    shape_type: str
    position_x: float
    position_y: float
    width: float
    height: float
    fill_color: str = "#93c5fd"
    stroke_color: str = "#3b82f6"
    stroke_width: float = 2
    layer: str = "devices"  # 'background' or 'devices'


class ShapeUpdate(BaseModel):
    shape_type: str | None = None
    position_x: float | None = None
    position_y: float | None = None
    width: float | None = None
    height: float | None = None
    fill_color: str | None = None
    stroke_color: str | None = None
    stroke_width: float | None = None
    layer: str | None = None


class ShapeResponse(BaseModel):
    id: int
    shape_type: str
    position_x: float
    position_y: float
    width: float
    height: float
    fill_color: str
    stroke_color: str
    stroke_width: float
    layer: str

    class Config:
        from_attributes = True


@router.get("/shapes", response_model=List[ShapeResponse])
def get_shapes(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all shapes"""
    shapes = db.query(Shape).all()
    return shapes


@router.post("/shapes", response_model=ShapeResponse)
def create_shape(
    shape: ShapeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new shape"""
    db_shape = Shape(**shape.model_dump())
    db.add(db_shape)
    db.commit()
    db.refresh(db_shape)
    return db_shape


@router.put("/shapes/{shape_id}", response_model=ShapeResponse)
def update_shape(
    shape_id: int,
    shape: ShapeUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a shape"""
    db_shape = db.query(Shape).filter(Shape.id == shape_id).first()
    if not db_shape:
        raise HTTPException(status_code=404, detail="Shape not found")

    update_data = shape.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_shape, key, value)

    db.commit()
    db.refresh(db_shape)
    return db_shape


@router.delete("/shapes/{shape_id}")
def delete_shape(
    shape_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a shape"""
    db_shape = db.query(Shape).filter(Shape.id == shape_id).first()
    if not db_shape:
        raise HTTPException(status_code=404, detail="Shape not found")

    db.delete(db_shape)
    db.commit()
    return {"message": "Shape deleted successfully"}
