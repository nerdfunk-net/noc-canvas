"""
Inventory models for device inventory management.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..core.database import Base


def _get_utc_now():
    """Helper function to get current UTC time with timezone awareness."""
    return datetime.now(timezone.utc)


class Inventory(Base):
    """Database model for storing inventory definitions."""

    __tablename__ = "inventories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    operations_json = Column(
        Text, nullable=False
    )  # JSON string containing logical operations
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=_get_utc_now)
    updated_at = Column(DateTime, default=_get_utc_now, onupdate=_get_utc_now)

    # Relationships
    owner = relationship("User", back_populates="inventories")
