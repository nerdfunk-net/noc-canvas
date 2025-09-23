#!/usr/bin/env python3
"""
Test script to verify command update functionality
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.settings import DeviceCommand, CommandPlatform, CommandParser

async def test_command_update():
    """Test updating a command with description"""

    # Get database session
    db_gen = get_db()
    db: Session = next(db_gen)

    try:
        # Find the first IOS command
        command = db.query(DeviceCommand).filter(
            DeviceCommand.platform == CommandPlatform.IOS
        ).first()

        if not command:
            print("❌ No IOS commands found in database")
            return

        print(f"📋 Found command: {command.command}")
        print(f"📋 Current description: {command.description}")

        # Update the description
        old_description = command.description
        command.description = "UPDATED: Display comprehensive device version information"

        db.commit()
        db.refresh(command)

        print(f"✅ Updated description from: {old_description}")
        print(f"✅ Updated description to: {command.description}")

        # Verify the update
        updated_command = db.query(DeviceCommand).filter(
            DeviceCommand.id == command.id
        ).first()

        if updated_command and updated_command.description == "UPDATED: Display comprehensive device version information":
            print("✅ Description update verified in database")
        else:
            print("❌ Description update failed to persist")

    except Exception as e:
        print(f"❌ Error testing command update: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_command_update())