#!/usr/bin/env python3
"""
Initialize local databases for credentials and settings.
This script creates the database files and tables if they don't exist.
"""

import os
import sys

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from app.models.credential import create_credentials_tables, get_credentials_db_path
    from app.models.local_settings import create_settings_tables, get_settings_db_path
    
    def init_databases():
        """Initialize the local databases."""
        print("Initializing local databases...")
        
        # Create credentials database
        credentials_db_path = get_credentials_db_path()
        print(f"Creating credentials database at: {credentials_db_path}")
        create_credentials_tables()
        print("✅ Credentials database created successfully")
        
        # Create settings database
        settings_db_path = get_settings_db_path()
        print(f"Creating settings database at: {settings_db_path}")
        create_settings_tables()
        print("✅ Settings database created successfully")
        
        print(f"\n🎉 Database initialization completed!")
        print(f"📁 Database files location: {os.path.dirname(credentials_db_path)}")
        print(f"   - credentials.db: User credentials with encrypted passwords")
        print(f"   - settings.db: Application settings and configurations")
        
    if __name__ == "__main__":
        init_databases()

except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure you're running this from the project root directory")
    print("and that all dependencies are installed: pip install -r backend/requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error initializing databases: {e}")
    sys.exit(1)