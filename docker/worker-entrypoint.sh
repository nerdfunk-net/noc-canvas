#!/bin/bash
set -e

echo "Starting NOC Canvas Celery Worker..."

# Wait for Redis to be ready
echo "Waiting for Redis to be ready..."
while ! nc -z redis 6379; do
    echo "Waiting for Redis..."
    sleep 2
done
echo "Redis is ready!"

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."  
while ! nc -z postgres 5432; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done
echo "PostgreSQL is ready!"

# Wait a bit more for the backend to be fully initialized
echo "Waiting for backend to initialize..."
sleep 10

# Execute the command passed to the script
exec "$@"