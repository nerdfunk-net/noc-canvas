"""
Database migration script to create the baseline_cache table.

This script creates the baseline_cache table for storing device configuration
snapshots used for configuration drift detection and change management.

Run this script to add the baseline feature to an existing database:
    python backend/app/migrations/add_baseline_table.py
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.database import engine
from app.models.device_cache import BaselineCache
from sqlalchemy import inspect


def check_table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def create_baseline_table():
    """Create the baseline_cache table if it doesn't exist."""

    print("=" * 60)
    print("Baseline Table Migration")
    print("=" * 60)

    # Check if table already exists
    if check_table_exists("baseline_cache"):
        print("\n✅ Table 'baseline_cache' already exists. No migration needed.")
        return

    print("\n📊 Creating 'baseline_cache' table...")

    try:
        # Create only the BaselineCache table
        BaselineCache.__table__.create(engine, checkfirst=True)

        print("✅ Successfully created 'baseline_cache' table")

        # Verify table was created
        inspector = inspect(engine)
        columns = inspector.get_columns("baseline_cache")
        indexes = inspector.get_indexes("baseline_cache")

        print("\n📋 Table structure:")
        print(f"   Columns: {len(columns)}")
        for col in columns:
            print(f"      - {col['name']}: {col['type']}")

        print(f"\n🔍 Indexes: {len(indexes)}")
        for idx in indexes:
            print(f"      - {idx['name']}: {idx['column_names']}")

        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error creating table: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        create_baseline_table()
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        sys.exit(1)
