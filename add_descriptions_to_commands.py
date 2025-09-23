#!/usr/bin/env python3
"""
Script to add descriptions to existing device commands and add description column
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

async def add_descriptions_to_commands():
    """Add descriptions to existing commands and ensure column exists"""

    # Command descriptions mapping
    command_descriptions = {
        "show version": "Display device version information",
        "show interfaces": "Show interface status and configuration",
        "show ip route": "Display IP routing table",
        "show ip int brief": "Show brief interface IP information",
        "show ip int brief summary": "Show summarized interface IP information",
        "show interface": "Display interface details",
        "string": "Generic string command (test)"
    }

    # Get database session
    db_gen = get_db()
    db: Session = next(db_gen)

    try:
        # First, try to add the description column if it doesn't exist
        # This is safe - if column exists, it will be ignored
        try:
            db.execute(text("ALTER TABLE device_commands ADD COLUMN description TEXT"))
            db.commit()
            print("✅ Added description column to device_commands table")
        except Exception as e:
            if "already exists" in str(e) or "duplicate column" in str(e).lower():
                print("ℹ️ Description column already exists")
                db.rollback()
            else:
                print(f"⚠️ Note: {e}")
                db.rollback()

        # Update existing commands with descriptions
        commands = db.query(DeviceCommand).all()
        updated_count = 0

        for command in commands:
            if command.command in command_descriptions:
                command.description = command_descriptions[command.command]
                updated_count += 1
                print(f"✅ Updated: {command.command} -> {command.description}")

        db.commit()
        print(f"\n🎉 Updated {updated_count} commands with descriptions!")

        # Show all commands with descriptions
        all_commands = db.query(DeviceCommand).all()
        print(f"\n📋 All commands with descriptions:")
        for cmd in all_commands:
            desc = cmd.description or "(no description)"
            print(f"  - {cmd.command} ({cmd.platform.value}) -> {desc}")

    except Exception as e:
        print(f"❌ Error updating commands: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(add_descriptions_to_commands())