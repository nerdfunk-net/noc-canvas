#!/bin/bash
set -e

echo "Starting NOC Canvas Backend..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
while ! nc -z postgres 5432; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done
echo "PostgreSQL is ready!"

# Wait for Redis to be ready  
echo "Waiting for Redis to be ready..."
while ! nc -z redis 6379; do
    echo "Waiting for Redis..."
    sleep 2
done
echo "Redis is ready!"

# Initialize database if needed
echo "Initializing database..."
python -c "
import sys
sys.path.append('/app')
import logging
logging.basicConfig(level=logging.INFO)

try:
    from app.core.db_init import create_database_if_not_exists, initialize_tables, create_default_admin_user
    
    print('Step 1: Creating database if needed...')
    if create_database_if_not_exists():
        print('✅ Database creation successful')
    else:
        print('❌ Database creation failed')
        sys.exit(1)
    
    print('Step 2: Creating tables...')
    if initialize_tables():
        print('✅ Tables created successfully')
    else:
        print('❌ Table creation failed')
        sys.exit(1)
    
    print('Step 3: Creating default admin user...')
    if create_default_admin_user():
        print('✅ Admin user created successfully')
    else:
        print('⚠️ Admin user creation failed (might already exist)')
    
    print('✅ Database initialization completed successfully')

except Exception as e:
    print(f'❌ Database initialization error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

# Execute the command passed to the script
exec "$@"