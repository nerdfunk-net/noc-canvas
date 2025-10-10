"""
Model for tracking ownership of scheduled tasks.

This model provides an audit trail and security layer for scheduled tasks
by explicitly tracking which user created each task. This is separate from
the celery-sqlalchemy-scheduler's PeriodicTask table to avoid modifying
the external library's schema.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from ..core.database import Base


class ScheduledTaskOwner(Base):
    """
    Tracks ownership of scheduled (periodic) tasks.
    
    Each record associates a periodic task (from celery-sqlalchemy-scheduler)
    with the user who created it. This enables:
    - Proper credential lookup (task uses owner's credentials)
    - Security validation (prevent username spoofing)
    - Audit trail (who created which scheduled tasks)
    - User management (list/filter tasks by owner)
    """
    
    __tablename__ = "scheduled_task_owners"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to celery's periodic_tasks table
    # Note: We use Integer instead of ForeignKey since periodic_tasks is managed by external library
    periodic_task_id = Column(Integer, nullable=False, unique=True, index=True)
    
    # Owner's username (from User table)
    owner_username = Column(String, nullable=False, index=True)
    
    # Foreign key to User table for proper relationship
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationship to User
    owner = relationship("User", backref="scheduled_tasks")
    
    # Composite index for common queries
    __table_args__ = (
        Index('idx_owner_username', 'owner_username'),
        Index('idx_periodic_task_id', 'periodic_task_id'),
    )
    
    def __repr__(self):
        return f"<ScheduledTaskOwner(id={self.id}, periodic_task_id={self.periodic_task_id}, owner={self.owner_username})>"
