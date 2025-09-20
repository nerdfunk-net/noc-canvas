#!/usr/bin/env python3
"""
Test script to verify settings storage and retrieval.
"""
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.models.local_settings import store_setting, get_user_settings, get_setting

def test_settings():
    """Test settings storage and retrieval."""
    print("Testing settings storage and retrieval...")
    
    # Test user
    username = "testuser"
    
    # Test storing boolean settings
    print("\n1. Storing boolean settings:")
    store_setting(username, "nautobot", "enabled", "true")
    store_setting(username, "checkmk", "enabled", "false")
    
    # Test storing string settings
    print("2. Storing string settings:")
    store_setting(username, "nautobot", "url", "https://nautobot.example.com")
    store_setting(username, "checkmk", "site", "cmk")
    
    # Test storing numeric settings
    print("3. Storing numeric settings:")
    store_setting(username, "nautobot", "timeout", "30")
    store_setting(username, "canvas", "autoSaveInterval", "60")
    
    # Test retrieving settings
    print("\n4. Retrieving all settings:")
    all_settings = get_user_settings(username)
    print(f"All settings: {all_settings}")
    
    # Test retrieving individual settings
    print("\n5. Retrieving individual settings:")
    nautobot_enabled = get_setting(username, "nautobot", "enabled")
    checkmk_enabled = get_setting(username, "checkmk", "enabled")
    nautobot_url = get_setting(username, "nautobot", "url")
    
    print(f"Nautobot enabled: {nautobot_enabled} (type: {type(nautobot_enabled)})")
    print(f"CheckMK enabled: {checkmk_enabled} (type: {type(checkmk_enabled)})")
    print(f"Nautobot URL: {nautobot_url} (type: {type(nautobot_url)})")
    
    # Test boolean conversion
    print("\n6. Testing boolean conversion:")
    def convert_to_bool(value):
        if value is None or value == "":
            return False
        return str(value).lower() == "true"
    
    print(f"Nautobot enabled as bool: {convert_to_bool(nautobot_enabled)}")
    print(f"CheckMK enabled as bool: {convert_to_bool(checkmk_enabled)}")
    
    print("\n✅ Settings test completed successfully!")

if __name__ == "__main__":
    test_settings()