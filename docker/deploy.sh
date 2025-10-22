#!/bin/bash
set -e

# NOC Canvas Deployment Script
# This script can be used for both development and production deployments

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "=========================================="
echo "NOC Canvas Deployment"
echo "=========================================="
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running"
    exit 1
fi

# Check docker-compose
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed"
    exit 1
fi

print_success "Docker is ready"

# Determine deployment mode
MODE="${1:-development}"

case "$MODE" in
    dev|development)
        COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
        print_status "Deploying in DEVELOPMENT mode"
        ;;
    prod|production)
        COMPOSE_FILE="$PROJECT_ROOT/docker-compose.prod.yml"
        print_status "Deploying in PRODUCTION mode"
        ;;
    airgapped)
        COMPOSE_FILE="$PROJECT_ROOT/docker-compose.airgapped.yaml"
        print_status "Deploying in AIR-GAPPED mode"
        ;;
    *)
        print_error "Unknown mode: $MODE"
        echo "Usage: $0 [dev|prod|airgapped]"
        exit 1
        ;;
esac

# Check if compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    print_error "Compose file not found: $COMPOSE_FILE"
    exit 1
fi

# Create .env if it doesn't exist
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    print_warning "No .env file found"
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        print_status "Creating .env from .env.example"
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        print_warning "Please review and update .env file with your configuration"
    else
        print_warning "No .env.example found, using default values"
    fi
fi

# Pull/build images if needed
if [ "$MODE" != "airgapped" ]; then
    print_status "Pulling/building images..."
    docker-compose -f "$COMPOSE_FILE" pull || true
    docker-compose -f "$COMPOSE_FILE" build
fi

# Start services
print_status "Starting services..."
docker-compose -f "$COMPOSE_FILE" up -d

# Wait for services to be healthy
print_status "Waiting for services to be ready..."
sleep 5

# Check service status
print_status "Checking service status..."
docker-compose -f "$COMPOSE_FILE" ps

echo ""
print_success "Deployment complete!"
echo ""
echo "=========================================="
echo "Access Information"
echo "=========================================="
echo ""
echo "Frontend:  http://localhost:3000"
echo "Backend:   http://localhost:8000"
echo "API Docs:  http://localhost:8000/docs"
echo ""
echo "Default credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "⚠️  IMPORTANT: Change default passwords in production!"
echo ""
echo "=========================================="
echo "Useful Commands"
echo "=========================================="
echo ""
echo "View logs:     docker-compose -f $COMPOSE_FILE logs -f"
echo "Stop:          docker-compose -f $COMPOSE_FILE down"
echo "Restart:       docker-compose -f $COMPOSE_FILE restart"
echo "Status:        docker-compose -f $COMPOSE_FILE ps"
echo ""
