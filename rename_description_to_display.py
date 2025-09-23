#!/usr/bin/env python3
"""
Script to rename description column to display column in device_commands table
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.models.settings import DeviceCommand

async def rename_column():
    """Rename description column to display"""

    # Get database session
    db_gen = get_db()
    db: Session = next(db_gen)

    try:
        # First, try to rename the column from description to display
        try:
            db.execute(text("ALTER TABLE device_commands RENAME COLUMN description TO display"))
            db.commit()
            print("✅ Renamed column 'description' to 'display' successfully")
        except Exception as e:
            if "does not exist" in str(e).lower():
                print("ℹ️ Column 'description' does not exist, checking if 'display' exists...")
                # Check if display column already exists
                try:
                    db.execute(text("SELECT display FROM device_commands LIMIT 1"))
                    print("ℹ️ Column 'display' already exists")
                except Exception:
                    # If neither exists, create the display column
                    print("➕ Creating 'display' column...")
                    db.execute(text("ALTER TABLE device_commands ADD COLUMN display TEXT"))
                    db.commit()
                    print("✅ Created 'display' column successfully")
            else:
                print(f"⚠️ Note: {e}")
                db.rollback()

        # Show all commands with their display values
        commands = db.query(DeviceCommand).all()
        print(f"\n📋 Commands with display values:")
        for cmd in commands:
            display = cmd.display or "(no display value)"
            print(f"  - {cmd.command} ({cmd.platform.value}) -> {display}")

    except Exception as e:
        print(f"❌ Error renaming column: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(rename_column())