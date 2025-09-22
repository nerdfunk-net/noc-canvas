#!/bin/bash
set -e

# NOC Canvas Docker Test Script
# This script tests the Docker setup locally before air-gapped deployment

echo "=========================================="
echo "NOC Canvas Docker Test"
echo "=========================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
print_status "Checking Docker daemon..."
if ! docker info >/dev/null 2>&1; then
    print_error "Docker daemon is not running. Please start Docker and try again."
    exit 1
fi

print_success "Docker daemon is running"

# Detect proxy settings from environment
PROXY_ARGS=""
if [ ! -z "$HTTP_PROXY" ]; then
    PROXY_ARGS="$PROXY_ARGS --build-arg HTTP_PROXY=$HTTP_PROXY"
fi
if [ ! -z "$HTTPS_PROXY" ]; then
    PROXY_ARGS="$PROXY_ARGS --build-arg HTTPS_PROXY=$HTTPS_PROXY"
fi
if [ ! -z "$NO_PROXY" ]; then
    PROXY_ARGS="$PROXY_ARGS --build-arg NO_PROXY=$NO_PROXY"
fi

if [ ! -z "$PROXY_ARGS" ]; then
    print_status "Proxy settings detected, will use for Docker builds:"
    echo "  HTTP_PROXY: ${HTTP_PROXY:-not set}"
    echo "  HTTPS_PROXY: ${HTTPS_PROXY:-not set}"
    echo "  NO_PROXY: ${NO_PROXY:-not set}"
fi

# Check if .env file exists
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    print_warning ".env file not found, creating from template..."
    cp "$SCRIPT_DIR/.env.template" "$SCRIPT_DIR/.env"
    print_warning "Please review and update the .env file with appropriate values"
fi

# Clean up any existing containers
print_status "Cleaning up existing containers..."
cd "$PROJECT_ROOT"
if [ ! -z "$PROXY_ARGS" ]; then
    docker-compose -f docker/docker-compose.yaml down -v 2>/dev/null || true
else
    docker-compose -f docker/docker-compose.yaml down -v 2>/dev/null || true
fi

# Build and start services
print_status "Building and starting services..."
if [ ! -z "$PROXY_ARGS" ]; then
    print_status "Using proxy settings for build..."
    docker-compose -f docker/docker-compose.yaml build $PROXY_ARGS
    docker-compose -f docker/docker-compose.yaml up -d
else
    docker-compose -f docker/docker-compose.yaml up --build -d
fi

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Check service health
print_status "Checking service health..."

# Check if all containers are running
containers=$(docker-compose -f docker/docker-compose.yaml ps --services)
failed_services=()

for service in $containers; do
    if ! docker-compose -f docker/docker-compose.yaml ps "$service" | grep -q "Up"; then
        failed_services+=("$service")
    fi
done

if [ ${#failed_services[@]} -ne 0 ]; then
    print_error "Some services failed to start: ${failed_services[*]}"
    print_status "Showing logs for failed services..."
    for service in "${failed_services[@]}"; do
        echo "=== Logs for $service ==="
        docker-compose -f docker/docker-compose.yaml logs "$service"
        echo ""
    done
    exit 1
fi

# Test backend health endpoint
print_status "Testing backend health endpoint..."
for i in {1..10}; do
    if curl -f -s http://localhost:8000/health >/dev/null; then
        print_success "Backend health check passed"
        break
    else
        print_status "Attempt $i/10: Backend not ready yet, waiting..."
        sleep 10
    fi
    
    if [ $i -eq 10 ]; then
        print_error "Backend health check failed after 10 attempts"
        print_status "Backend logs:"
        docker-compose -f docker/docker-compose.yaml logs noc-backend
        exit 1
    fi
done

# Test frontend availability
print_status "Testing frontend availability..."
for i in {1..5}; do
    if curl -f -s http://localhost:3000 >/dev/null; then
        print_success "Frontend is accessible"
        break
    else
        print_status "Attempt $i/5: Frontend not ready yet, waiting..."
        sleep 5
    fi
    
    if [ $i -eq 5 ]; then
        print_error "Frontend accessibility check failed"
        print_status "Frontend logs:"
        docker-compose -f docker/docker-compose.yaml logs noc-frontend
        exit 1
    fi
done

# Show service status
print_status "Service status:"
docker-compose -f docker/docker-compose.yaml ps

print_success "All services are running successfully!"
echo ""
echo "=========================================="
echo "TEST COMPLETED SUCCESSFULLY"
echo "=========================================="
echo "You can access the application at:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Default admin credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "To stop the test environment:"
echo "  docker-compose -f docker/docker-compose.yaml down -v"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker/docker-compose.yaml logs -f"
echo ""
print_success "Docker setup is working correctly and ready for air-gapped deployment!"