#!/bin/bash
set -e

# NOC Canvas Docker Image Preparation Script
# This script prepares all necessary files and dependencies for air-gapped deployment

echo "=========================================="
echo "NOC Canvas Docker Preparation Script"
echo "=========================================="

# Set variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$SCRIPT_DIR"
BUILD_DIR="$PROJECT_ROOT/build"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect proxy environment variables and build proxy arguments
PROXY_ARGS=""
if [ -n "${HTTP_PROXY}" ]; then
    PROXY_ARGS="${PROXY_ARGS} --build-arg HTTP_PROXY=${HTTP_PROXY}"
    print_status "🌐 HTTP Proxy detected: ${HTTP_PROXY}"
fi

if [ -n "${HTTPS_PROXY}" ]; then
    PROXY_ARGS="${PROXY_ARGS} --build-arg HTTPS_PROXY=${HTTPS_PROXY}"
    print_status "🔒 HTTPS Proxy detected: ${HTTPS_PROXY}"
fi

if [ -n "${NO_PROXY}" ]; then
    PROXY_ARGS="${PROXY_ARGS} --build-arg NO_PROXY=${NO_PROXY}"
    print_status "🚫 No Proxy list detected: ${NO_PROXY}"
fi

if [ -n "${PROXY_ARGS}" ]; then
    print_status "📡 Using proxy configuration for Docker builds"
else
    print_status "🌍 No proxy configuration detected - using direct internet access"
fi

# Check required tools
print_status "Checking required tools..."

required_tools=("docker" "docker-compose" "node" "npm" "python3" "pip")
missing_tools=()

for tool in "${required_tools[@]}"; do
    if ! command_exists "$tool"; then
        missing_tools+=("$tool")
    fi
done

if [ ${#missing_tools[@]} -ne 0 ]; then
    print_error "Missing required tools: ${missing_tools[*]}"
    print_error "Please install the missing tools and run this script again."
    exit 1
fi

print_success "All required tools are available"

# Create build directory
print_status "Creating build directory..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Check Docker daemon
print_status "Checking Docker daemon..."
if ! docker info >/dev/null 2>&1; then
    print_error "Docker daemon is not running. Please start Docker and try again."
    exit 1
fi

print_success "Docker daemon is running"

# Build frontend dependencies and check for external resources
print_status "Preparing frontend dependencies..."
cd "$FRONTEND_DIR"

# Clean previous builds
rm -rf node_modules dist

# Install dependencies
print_status "Installing frontend dependencies..."
if [ -n "${HTTP_PROXY}" ] || [ -n "${HTTPS_PROXY}" ]; then
    print_status "Configuring npm for proxy usage..."
    npm config set proxy "${HTTP_PROXY}" || true
    npm config set https-proxy "${HTTPS_PROXY}" || true
fi
npm ci

# Check for any external CDN or font dependencies
print_status "Checking for external dependencies in frontend..."
external_deps=$(grep -r "fonts\.googleapis\|cdnjs\|unpkg\|jsdelivr\|fontawesome" src/ public/ index.html || true)
if [ -n "$external_deps" ]; then
    print_warning "Found potential external dependencies:"
    echo "$external_deps"
    print_warning "Please ensure these are downloaded locally for air-gapped deployment"
fi

# Build frontend
print_status "Building frontend..."
npm run build

# Copy built frontend to build directory
cp -r dist "$BUILD_DIR/frontend-dist"
print_success "Frontend built and copied to build directory"

# Prepare backend dependencies
print_status "Preparing backend dependencies..."
cd "$BACKEND_DIR"

# Create requirements list with exact versions
print_status "Generating requirements with exact versions..."
python3 -m pip freeze > "$BUILD_DIR/requirements-frozen.txt"

# Download all Python dependencies for offline installation
print_status "Downloading Python dependencies for offline installation..."
if [ -n "${HTTP_PROXY}" ] || [ -n "${HTTPS_PROXY}" ]; then
    print_status "Using proxy for Python package downloads..."
    # Pip will automatically use HTTP_PROXY/HTTPS_PROXY environment variables
fi
pip download -r requirements.txt -d "$BUILD_DIR/python-packages"

print_success "Python dependencies downloaded"

# Copy backend source
print_status "Copying backend source..."
cp -r "$BACKEND_DIR" "$BUILD_DIR/backend-source"

# Remove unnecessary files from backend copy
rm -rf "$BUILD_DIR/backend-source/__pycache__"
find "$BUILD_DIR/backend-source" -name "*.pyc" -delete
find "$BUILD_DIR/backend-source" -name "__pycache__" -type d -exec rm -rf {} +

# Create offline installation script
print_status "Creating offline installation script..."
cat > "$BUILD_DIR/install-python-deps.sh" << 'EOF'
#!/bin/bash
# Offline Python dependencies installation script
echo "Installing Python dependencies from local packages..."
pip install --no-index --find-links ./python-packages -r requirements.txt
echo "Python dependencies installed successfully"
EOF
chmod +x "$BUILD_DIR/install-python-deps.sh"

# Copy Docker configuration
print_status "Copying Docker configuration..."
cp -r "$DOCKER_DIR" "$BUILD_DIR/docker"

# Copy .env file template and create default .env if it doesn't exist
print_status "Setting up environment configuration..."
if [ -f "$DOCKER_DIR/.env" ]; then
    cp "$DOCKER_DIR/.env" "$BUILD_DIR/.env"
else
    cp "$DOCKER_DIR/.env.template" "$BUILD_DIR/.env"
    print_warning "No .env file found, created from template. Please review and update the values."
fi

# Create enhanced Dockerfile that uses local dependencies
print_status "Creating air-gapped Dockerfile..."
cat > "$BUILD_DIR/docker/Dockerfile.backend.airgapped" << 'EOF'
# Air-gapped Backend Dockerfile for NOC Canvas
FROM python:3.12-slim

# Install system dependencies including netcat for wait scripts
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy local Python packages and installation script
COPY build/python-packages ./python-packages/
COPY build/install-python-deps.sh ./
COPY backend/requirements.txt ./

# Install Python dependencies from local packages
RUN ./install-python-deps.sh && rm -rf python-packages install-python-deps.sh

# Copy backend source code
COPY backend/ .

# Create necessary directories
RUN mkdir -p /app/data/settings /app/data/backups

# Copy docker-specific configuration
COPY docker/backend-entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Create air-gapped worker Dockerfile
cat > "$BUILD_DIR/docker/Dockerfile.worker.airgapped" << 'EOF'
# Air-gapped Worker Dockerfile for NOC Canvas Celery Worker
FROM python:3.12-slim

# Install system dependencies including netcat for wait scripts
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy local Python packages and installation script
COPY build/python-packages ./python-packages/
COPY build/install-python-deps.sh ./
COPY backend/requirements.txt ./

# Install Python dependencies from local packages
RUN ./install-python-deps.sh && rm -rf python-packages install-python-deps.sh

# Copy backend source code
COPY backend/ .

# Create necessary directories
RUN mkdir -p /app/data/settings /app/data/backups

# Copy docker-specific configuration
COPY docker/worker-entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command - start celery worker
CMD ["python", "-m", "celery", "-A", "app.services.background_jobs", "worker", "--loglevel=info", "--concurrency=2"]
EOF

# Create air-gapped frontend Dockerfile
cat > "$BUILD_DIR/docker/Dockerfile.frontend.airgapped" << 'EOF'
# Air-gapped Frontend Dockerfile for NOC Canvas
FROM nginx:alpine

# Copy pre-built frontend assets
COPY build/frontend-dist /usr/share/nginx/html

# Copy nginx configuration
COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/default.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
EOF

# Create air-gapped docker-compose.yaml
print_status "Creating air-gapped docker-compose.yaml..."
cat > "$BUILD_DIR/docker-compose.airgapped.yaml" << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:latest
    container_name: noc-postgres
    environment:
      POSTGRES_DB: ${NOC_DATABASE_NAME:-noc}
      POSTGRES_USER: ${NOC_USERNAME:-postgres}
      POSTGRES_PASSWORD: ${NOC_PASSWORD:-postgres}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    ports:
      - "${NOC_DATABASE_PORT:-5432}:5432"
    networks:
      - noc-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${NOC_USERNAME:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:8-alpine
    container_name: noc-redis
    command: redis-server --requirepass ${NOC_REDIS_PASSWORD:-changeme}
    ports:
      - "${NOC_REDIS_PORT:-6379}:6379"
    volumes:
      - redis_data:/data
    networks:
      - noc-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "--no-auth-warning", "-a", "${NOC_REDIS_PASSWORD:-changeme}", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  noc-backend:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend.airgapped
    container_name: noc-backend
    environment:
      # Database settings
      NOC_DATABASE: postgres
      NOC_USERNAME: ${NOC_USERNAME:-postgres}
      NOC_PASSWORD: ${NOC_PASSWORD:-postgres}
      NOC_DATABASE_PORT: 5432
      NOC_DATABASE_NAME: ${NOC_DATABASE_NAME:-noc}
      NOC_DATABASE_SSL: "false"
      
      # Redis settings
      NOC_REDIS_HOST: redis
      NOC_REDIS_PORT: 6379
      NOC_REDIS_PASSWORD: ${NOC_REDIS_PASSWORD:-changeme}
      NOC_REDIS_SSL: "false"
      
      # App settings
      SECRET_KEY: ${SECRET_KEY:-your-production-secret-key-change-this}
      DEFAULT_ADMIN_USERNAME: ${DEFAULT_ADMIN_USERNAME:-admin}
      DEFAULT_ADMIN_PASSWORD: ${DEFAULT_ADMIN_PASSWORD:-admin123}
      ALGORITHM: ${ALGORITHM:-HS256}
      ACCESS_TOKEN_EXPIRE_MINUTES: ${ACCESS_TOKEN_EXPIRE_MINUTES:-30}
    ports:
      - "8000:8000"
    volumes:
      - app_data:/app/data
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - noc-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  noc-worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.worker.airgapped
    container_name: noc-worker
    environment:
      # Database settings
      NOC_DATABASE: postgres
      NOC_USERNAME: ${NOC_USERNAME:-postgres}
      NOC_PASSWORD: ${NOC_PASSWORD:-postgres}
      NOC_DATABASE_PORT: 5432
      NOC_DATABASE_NAME: ${NOC_DATABASE_NAME:-noc}
      NOC_DATABASE_SSL: "false"
      
      # Redis settings
      NOC_REDIS_HOST: redis
      NOC_REDIS_PORT: 6379
      NOC_REDIS_PASSWORD: ${NOC_REDIS_PASSWORD:-changeme}
      NOC_REDIS_SSL: "false"
      
      # App settings
      SECRET_KEY: ${SECRET_KEY:-your-production-secret-key-change-this}
      ALGORITHM: ${ALGORITHM:-HS256}
    volumes:
      - app_data:/app/data
    depends_on:
      - redis
      - postgres
      - noc-backend
    networks:
      - noc-network
    restart: unless-stopped

  noc-frontend:
    build:
      context: .
      dockerfile: docker/Dockerfile.frontend.airgapped
    container_name: noc-frontend
    ports:
      - "3000:80"
    depends_on:
      - noc-backend
    networks:
      - noc-network
    restart: unless-stopped

networks:
  noc-network:
    driver: bridge

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  app_data:
    driver: local
EOF

# Pull required Docker base images
print_status "Pulling required Docker base images..."

# Configure Docker daemon proxy if proxy settings are detected
if [ ! -z "$HTTP_PROXY" ] || [ ! -z "$HTTPS_PROXY" ]; then
    echo "Proxy detected - Docker daemon should be configured for proxy access"
    echo "HTTP_PROXY: ${HTTP_PROXY:-not set}"
    echo "HTTPS_PROXY: ${HTTPS_PROXY:-not set}"
    echo "NO_PROXY: ${NO_PROXY:-not set}"
fi

docker pull python:3.12-slim
docker pull postgres:latest
docker pull redis:8-alpine
docker pull nginx:alpine
docker pull node:18-alpine

print_success "Docker base images pulled"

# Save Docker images for air-gapped deployment
print_status "Saving Docker base images..."
mkdir -p "$BUILD_DIR/docker-images"
docker save python:3.12-slim | gzip > "$BUILD_DIR/docker-images/python-3.12-slim.tar.gz"
docker save postgres:latest | gzip > "$BUILD_DIR/docker-images/postgres-latest.tar.gz"
docker save redis:8-alpine | gzip > "$BUILD_DIR/docker-images/redis-8-alpine.tar.gz"
docker save nginx:alpine | gzip > "$BUILD_DIR/docker-images/nginx-alpine.tar.gz"
docker save node:18-alpine | gzip > "$BUILD_DIR/docker-images/node-18-alpine.tar.gz"

print_success "Docker images saved"

# Create deployment script for air-gapped environment
print_status "Creating deployment script..."
cat > "$BUILD_DIR/deploy-airgapped.sh" << 'EOF'
#!/bin/bash
set -e

echo "=========================================="
echo "NOC Canvas Air-gapped Deployment"
echo "=========================================="

# Load Docker images
echo "Loading Docker base images..."
docker load < docker-images/python-3.12-slim.tar.gz
docker load < docker-images/postgres-latest.tar.gz
docker load < docker-images/redis-7-alpine.tar.gz
docker load < docker-images/nginx-alpine.tar.gz
docker load < docker-images/node-18-alpine.tar.gz
echo "Docker base images loaded successfully"

# Build and start services
echo "Building and starting NOC Canvas services..."
docker-compose -f docker-compose.airgapped.yaml up --build -d

echo "NOC Canvas is starting up..."
echo "Frontend will be available at: http://localhost:3000"
echo "Backend API will be available at: http://localhost:8000"
echo ""
echo "Default admin credentials:"
echo "Username: admin"
echo "Password: admin123"
echo ""
echo "To check status: docker-compose -f docker-compose.airgapped.yaml ps"
echo "To view logs: docker-compose -f docker-compose.airgapped.yaml logs -f"
echo "To stop: docker-compose -f docker-compose.airgapped.yaml down"
EOF
chmod +x "$BUILD_DIR/deploy-airgapped.sh"

# Create backup script
cat > "$BUILD_DIR/backup-data.sh" << 'EOF'
#!/bin/bash
set -e

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Creating backup in $BACKUP_DIR..."

# Backup database
docker-compose -f docker-compose.airgapped.yaml exec -T postgres pg_dump -U postgres noc > "$BACKUP_DIR/database.sql"

# Backup app data volume
docker run --rm -v "$(pwd)_app_data:/data" -v "$(pwd)/$BACKUP_DIR:/backup" alpine tar czf /backup/app_data.tar.gz -C /data .

echo "Backup completed in $BACKUP_DIR"
EOF
chmod +x "$BUILD_DIR/backup-data.sh"

# Create README for deployment
print_status "Creating deployment documentation..."
cat > "$BUILD_DIR/README.md" << 'EOF'
# NOC Canvas Air-gapped Deployment

This package contains all necessary files for deploying NOC Canvas in an air-gapped environment.

## Contents

- `docker-compose.airgapped.yaml` - Air-gapped Docker Compose configuration
- `docker/` - Docker configuration files and scripts
- `backend/` - Backend application source code
- `build/` - Build artifacts and dependencies
- `docker-images/` - Pre-downloaded Docker base images
- `deploy-airgapped.sh` - Deployment script
- `backup-data.sh` - Data backup script

## Prerequisites

- Docker Engine 20.x or later
- Docker Compose 2.x or later
- At least 4GB of available RAM
- At least 10GB of available disk space

## Quick Start

1. Extract this package to your target system
2. Run the deployment script:
   ```bash
   ./deploy-airgapped.sh
   ```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## Default Credentials

- Username: `admin`
- Password: `admin123`

**Important**: Change the default password after first login!

## Configuration

### Environment Variables

Edit the `docker-compose.airgapped.yaml` file to modify:

- Database credentials
- Redis password
- Application secrets
- Port mappings

### Persistent Data

The following Docker volumes store persistent data:
- `postgres_data` - Database data
- `redis_data` - Redis data
- `app_data` - Application data and settings

### Backup and Restore

Create a backup:
```bash
./backup-data.sh
```

## Troubleshooting

### Check service status
```bash
docker-compose -f docker-compose.airgapped.yaml ps
```

### View logs
```bash
docker-compose -f docker-compose.airgapped.yaml logs -f
```

### Restart services
```bash
docker-compose -f docker-compose.airgapped.yaml restart
```

### Stop all services
```bash
docker-compose -f docker-compose.airgapped.yaml down
```

## Security Considerations

1. Change default passwords before production use
2. Configure proper firewall rules
3. Use HTTPS in production (requires additional configuration)
4. Regularly backup your data
5. Keep Docker and base images updated

## Support

For support and documentation, contact your system administrator.
EOF

# Create final summary
print_success "Build preparation completed!"
echo ""
echo "=========================================="
echo "DEPLOYMENT PACKAGE SUMMARY"
echo "=========================================="
echo "Build directory: $BUILD_DIR"
echo ""
echo "Package contents:"
echo "├── docker-compose.airgapped.yaml   # Air-gapped Docker Compose config"
echo "├── deploy-airgapped.sh             # Deployment script"
echo "├── backup-data.sh                  # Backup script"
echo "├── README.md                       # Deployment documentation"
echo "├── docker/                         # Docker configuration"
echo "├── backend/                        # Backend source code"
echo "├── build/                          # Build artifacts"
echo "│   ├── frontend-dist/              # Built frontend assets"
echo "│   ├── python-packages/            # Python dependencies"
echo "│   └── requirements-frozen.txt     # Exact Python versions"
echo "└── docker-images/                  # Pre-downloaded Docker images"
echo ""
echo "Total size: $(du -sh "$BUILD_DIR" | cut -f1)"
echo ""
echo "To deploy in air-gapped environment:"
echo "1. Copy the entire '$BUILD_DIR' directory to target system"
echo "2. Run: cd $(basename "$BUILD_DIR") && ./deploy-airgapped.sh"
echo ""
print_success "Ready for air-gapped deployment!"

# Calculate and display total package size
total_size=$(du -sh "$BUILD_DIR" | cut -f1)
print_success "Total package size: $total_size"