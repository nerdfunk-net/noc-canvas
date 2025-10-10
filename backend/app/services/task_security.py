"""
Security utilities for validating background task execution.

This module provides security checks to ensure that background tasks
cannot be spoofed or executed with incorrect credentials.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session

from ..models.scheduled_task_owner import ScheduledTaskOwner

logger = logging.getLogger(__name__)


def validate_task_username(
    db: Session,
    periodic_task_id: Optional[int],
    username_from_kwargs: str
) -> tuple[bool, str]:
    """
    Validate that the username in task kwargs matches the task owner.
    
    This prevents credential spoofing where a malicious user could modify
    task kwargs to use another user's credentials.
    
    Args:
        db: Database session
        periodic_task_id: ID of the periodic task (None for ad-hoc tasks)
        username_from_kwargs: Username extracted from task kwargs
        
    Returns:
        Tuple of (is_valid, resolved_username):
        - is_valid: True if validation passed or not applicable
        - resolved_username: The username to use for credential lookup
    """
    # If no periodic_task_id, this is an ad-hoc task (not scheduled)
    # Trust the username from kwargs (it was set by the API at execution time)
    if periodic_task_id is None:
        logger.debug(f"Ad-hoc task, using username from kwargs: {username_from_kwargs}")
        return True, username_from_kwargs
    
    try:
        # Look up the task owner
        owner = db.query(ScheduledTaskOwner).filter(
            ScheduledTaskOwner.periodic_task_id == periodic_task_id
        ).first()
        
        if not owner:
            # No owner record found - this is an old task created before ownership tracking
            # Log a warning but allow execution with provided username
            logger.warning(
                f"No owner record found for periodic task {periodic_task_id}. "
                f"Using username from kwargs: {username_from_kwargs}"
            )
            return True, username_from_kwargs
        
        # Validate that kwargs username matches the owner
        if username_from_kwargs != owner.owner_username:
            logger.error(
                f"Security validation failed for task {periodic_task_id}! "
                f"Kwargs username '{username_from_kwargs}' does not match "
                f"task owner '{owner.owner_username}'. Using owner's username."
            )
            # Return owner's username to prevent credential spoofing
            return False, owner.owner_username
        
        # Validation passed
        logger.debug(
            f"Security validation passed for task {periodic_task_id}: "
            f"username '{username_from_kwargs}' matches owner"
        )
        return True, username_from_kwargs
        
    except Exception as e:
        logger.error(f"Error during task username validation: {e}")
        # On error, fall back to provided username but log the issue
        return True, username_from_kwargs


def get_task_owner_username(db: Session, periodic_task_id: int) -> Optional[str]:
    """
    Get the owner username for a periodic task.
    
    Args:
        db: Database session
        periodic_task_id: ID of the periodic task
        
    Returns:
        Owner username or None if not found
    """
    try:
        owner = db.query(ScheduledTaskOwner).filter(
            ScheduledTaskOwner.periodic_task_id == periodic_task_id
        ).first()
        return owner.owner_username if owner else None
    except Exception as e:
        logger.error(f"Error retrieving task owner: {e}")
        return None
