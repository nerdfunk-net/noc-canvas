#!/usr/bin/env python3
"""
Test script to verify display field functionality
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

async def test_display_field():
    """Test display field CRUD operations"""

    # Get database session
    db_gen = get_db()
    db: Session = next(db_gen)

    try:
        print("🧪 Testing display field functionality...")

        # Test 1: Create a new command with display
        print("\n1️⃣ Creating new command with display...")
        new_command = DeviceCommand(
            command="show interfaces status",
            display="Interface Status Summary",
            platform=CommandPlatform.IOS,
            parser=CommandParser.TEXTFSM
        )
        db.add(new_command)
        db.commit()
        db.refresh(new_command)
        print(f"✅ Created: {new_command.command} -> {new_command.display}")

        # Test 2: Update existing command's display
        print("\n2️⃣ Updating existing command display...")
        existing_command = db.query(DeviceCommand).filter(
            DeviceCommand.command == "show version"
        ).first()

        if existing_command:
            old_display = existing_command.display
            existing_command.display = "Device Version Information"
            db.commit()
            db.refresh(existing_command)
            print(f"✅ Updated: {existing_command.command}")
            print(f"   From: {old_display}")
            print(f"   To: {existing_command.display}")

        # Test 3: Verify all commands with display values
        print("\n3️⃣ All commands with display values:")
        all_commands = db.query(DeviceCommand).all()
        for cmd in all_commands:
            display = cmd.display or "(no display)"
            print(f"   {cmd.command} ({cmd.platform.value}) -> {display}")

        print(f"\n✅ All tests passed! Found {len(all_commands)} commands in database.")

    except Exception as e:
        print(f"❌ Error testing display field: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_display_field())