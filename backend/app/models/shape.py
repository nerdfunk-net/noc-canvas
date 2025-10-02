from sqlalchemy import Column, Integer, String, Float
from app.core.database import Base


class Shape(Base):
    __tablename__ = "shapes"

    id = Column(Integer, primary_key=True, index=True)
    shape_type = Column(String, nullable=False)  # 'rectangle' or 'circle'
    position_x = Column(Float, nullable=False)
    position_y = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    fill_color = Column(String, default="#93c5fd")
    stroke_color = Column(String, default="#3b82f6")
    stroke_width = Column(Float, default=2)
