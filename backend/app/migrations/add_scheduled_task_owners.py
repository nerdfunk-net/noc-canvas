"""
Database migration: Add scheduled_task_owners table

This migration creates the scheduled_task_owners table to track ownership
of periodic (scheduled) tasks for proper credential lookup and security.

Run this script once to initialize the table:
    python -m app.migrations.add_scheduled_task_owners
"""

import logging
from sqlalchemy import create_engine, inspect
from app.core.database import Base, engine
from app.models.scheduled_task_owner import ScheduledTaskOwner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Create the scheduled_task_owners table if it doesn't exist."""
    try:
        # Check if table already exists
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if 'scheduled_task_owners' in existing_tables:
            logger.info("Table 'scheduled_task_owners' already exists. Skipping migration.")
            return
        
        logger.info("Creating 'scheduled_task_owners' table...")
        
        # Create only the ScheduledTaskOwner table
        ScheduledTaskOwner.__table__.create(engine, checkfirst=True)
        
        logger.info("✅ Successfully created 'scheduled_task_owners' table")
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    print("=" * 60)
    print("Running migration: Add scheduled_task_owners table")
    print("=" * 60)
    run_migration()
    print("=" * 60)
