from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..core.database import Base


def _get_utc_now():
    """Helper function to get current UTC time with timezone awareness."""
    return datetime.now(timezone.utc)


class Canvas(Base):
    __tablename__ = "canvases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sharable = Column(Boolean, default=False)
    canvas_data = Column(
        Text, nullable=False
    )  # JSON string containing devices and positions
    created_at = Column(DateTime, default=_get_utc_now)
    updated_at = Column(DateTime, default=_get_utc_now, onupdate=_get_utc_now)

    # Relationships
    owner = relationship("User", back_populates="canvases")
