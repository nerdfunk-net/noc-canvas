#!/usr/bin/env python3
"""
Script to add test device commands to the database
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

async def add_test_commands():
    """Add test commands for different platforms"""
    
    # Test commands for different platforms
    test_commands = [
        {
            "command": "show version",
            "platform": CommandPlatform.IOS,
            "parser": CommandParser.TEXTFSM
        },
        {
            "command": "show interfaces",
            "platform": CommandPlatform.IOS,
            "parser": CommandParser.TEXTFSM
        },
        {
            "command": "show ip route",
            "platform": CommandPlatform.IOS,
            "parser": CommandParser.TEXTFSM
        },
        {
            "command": "show version",
            "platform": CommandPlatform.IOS_XE,
            "parser": CommandParser.TEXTFSM
        },
        {
            "command": "show interfaces",
            "platform": CommandPlatform.IOS_XE,
            "parser": CommandParser.TEXTFSM
        },
        {
            "command": "show version",
            "platform": CommandPlatform.NEXUS,
            "parser": CommandParser.TEXTFSM
        },
        {
            "command": "show interface",
            "platform": CommandPlatform.NEXUS,
            "parser": CommandParser.TEXTFSM
        }
    ]
    
    # Get database session
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        # Add commands to database
        for cmd_data in test_commands:
            # Check if command already exists
            existing = db.query(DeviceCommand).filter(
                DeviceCommand.command == cmd_data["command"],
                DeviceCommand.platform == cmd_data["platform"]
            ).first()
            
            if not existing:
                command = DeviceCommand(**cmd_data)
                db.add(command)
                print(f"✅ Added command: {cmd_data['command']} for {cmd_data['platform'].value}")
            else:
                print(f"⏭️ Command already exists: {cmd_data['command']} for {cmd_data['platform'].value}")
        
        db.commit()
        print(f"\n🎉 Test commands added successfully!")
        
        # Show all commands
        all_commands = db.query(DeviceCommand).all()
        print(f"\n📋 Total commands in database: {len(all_commands)}")
        for cmd in all_commands:
            print(f"  - {cmd.command} ({cmd.platform.value})")
            
    except Exception as e:
        print(f"❌ Error adding commands: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(add_test_commands())