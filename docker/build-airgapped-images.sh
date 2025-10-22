#!/bin/bash
set -e

# NOC Canvas Air-gapped Docker Image Builder
# This script builds complete, self-contained Docker images with all dependencies
# for deployment in air-gapped environments

echo "=========================================="
echo "NOC Canvas Air-gapped Image Builder"
echo "=========================================="

# Set variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_DIR="$PROJECT_ROOT/backend"
OUTPUT_DIR="$PROJECT_ROOT/airgapped-images"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Image names and tags
IMAGE_PREFIX="${IMAGE_PREFIX:-noc-canvas}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
BACKEND_IMAGE="${IMAGE_PREFIX}-backend:${IMAGE_TAG}"
WORKER_IMAGE="${IMAGE_PREFIX}-worker:${IMAGE_TAG}"
FRONTEND_IMAGE="${IMAGE_PREFIX}-frontend:${IMAGE_TAG}"

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

# Check required tools
print_status "Checking required tools..."
required_tools=("docker" "docker-compose" "node" "npm")
missing_tools=()

for tool in "${required_tools[@]}"; do
    if ! command_exists "$tool"; then
        missing_tools+=("$tool")
    fi
done

if [ ${#missing_tools[@]} -ne 0 ]; then
    print_error "Missing required tools: ${missing_tools[*]}"
    exit 1
fi

print_success "All required tools are available"

# Check Docker daemon
print_status "Checking Docker daemon..."
if ! docker info >/dev/null 2>&1; then
    print_error "Docker daemon is not running. Please start Docker and try again."
    exit 1
fi
print_success "Docker daemon is running"

# Create output directory
print_status "Creating output directory..."
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR/images"
mkdir -p "$OUTPUT_DIR/config"

# Step 1: Build Frontend
print_status "Building frontend application..."
cd "$FRONTEND_DIR"

# Install dependencies and build
print_status "Installing frontend dependencies..."
npm ci

print_status "Building frontend for production..."
npm run build

print_success "Frontend built successfully"

# Step 2: Create Frontend Docker Image
print_status "Building frontend Docker image..."
cat > "$OUTPUT_DIR/Dockerfile.frontend" << 'EOF'
FROM nginx:alpine

# Copy built frontend assets
COPY frontend/dist /usr/share/nginx/html

# Copy nginx configuration
COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/default.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
EOF

cd "$PROJECT_ROOT"
docker build -f "$OUTPUT_DIR/Dockerfile.frontend" -t "$FRONTEND_IMAGE" .

print_success "Frontend image built: $FRONTEND_IMAGE"

# Step 3: Create Backend Docker Image
print_status "Building backend Docker image..."
cat > "$OUTPUT_DIR/Dockerfile.backend" << 'EOF'
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ .

# Create necessary directories
RUN mkdir -p /app/data/settings /app/data/backups

# Copy entrypoint script
COPY docker/backend-entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

docker build -f "$OUTPUT_DIR/Dockerfile.backend" -t "$BACKEND_IMAGE" .

print_success "Backend image built: $BACKEND_IMAGE"

# Step 4: Create Worker Docker Image
print_status "Building worker Docker image..."
cat > "$OUTPUT_DIR/Dockerfile.worker" << 'EOF'
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ .

# Create necessary directories
RUN mkdir -p /app/data/settings /app/data/backups

# Copy entrypoint script
COPY docker/worker-entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "-m", "celery", "-A", "app.services.background_jobs", "worker", "--loglevel=info", "--concurrency=2"]
EOF

docker build -f "$OUTPUT_DIR/Dockerfile.worker" -t "$WORKER_IMAGE" .

print_success "Worker image built: $WORKER_IMAGE"

# Step 5: Pull base images
print_status "Pulling required base images..."
docker pull postgres:16-alpine
docker pull redis:7-alpine

print_success "Base images pulled"

# Step 6: Save all images
print_status "Saving Docker images for air-gapped deployment..."

print_status "Saving backend image..."
docker save "$BACKEND_IMAGE" | gzip > "$OUTPUT_DIR/images/noc-backend.tar.gz"

print_status "Saving worker image..."
docker save "$WORKER_IMAGE" | gzip > "$OUTPUT_DIR/images/noc-worker.tar.gz"

print_status "Saving frontend image..."
docker save "$FRONTEND_IMAGE" | gzip > "$OUTPUT_DIR/images/noc-frontend.tar.gz"

print_status "Saving PostgreSQL image..."
docker save postgres:16-alpine | gzip > "$OUTPUT_DIR/images/postgres.tar.gz"

print_status "Saving Redis image..."
docker save redis:7-alpine | gzip > "$OUTPUT_DIR/images/redis.tar.gz"

print_success "All images saved"

# Step 7: Create docker-compose file for air-gapped deployment
print_status "Creating docker-compose configuration..."
cat > "$OUTPUT_DIR/docker-compose.yaml" << EOF
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: noc-postgres
    environment:
      POSTGRES_DB: \${POSTGRES_DB:-noc}
      POSTGRES_USER: \${POSTGRES_USER:-noc_user}
      POSTGRES_PASSWORD: \${POSTGRES_PASSWORD:-changeme123}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "\${POSTGRES_PORT:-5432}:5432"
    networks:
      - noc-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U \${POSTGRES_USER:-noc_user}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: noc-redis
    command: redis-server --requirepass \${REDIS_PASSWORD:-changeme456}
    ports:
      - "\${REDIS_PORT:-6379}:6379"
    volumes:
      - redis_data:/data
    networks:
      - noc-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "--no-auth-warning", "-a", "\${REDIS_PASSWORD:-changeme456}", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  backend:
    image: ${BACKEND_IMAGE}
    container_name: noc-backend
    environment:
      # Database settings
      NOC_DATABASE: postgres
      NOC_USERNAME: \${POSTGRES_USER:-noc_user}
      NOC_PASSWORD: \${POSTGRES_PASSWORD:-changeme123}
      NOC_DATABASE_PORT: 5432
      NOC_DATABASE_NAME: \${POSTGRES_DB:-noc}
      NOC_DATABASE_SSL: "false"

      # Redis settings
      NOC_REDIS_HOST: redis
      NOC_REDIS_PORT: 6379
      NOC_REDIS_PASSWORD: \${REDIS_PASSWORD:-changeme456}
      NOC_REDIS_SSL: "false"

      # App settings
      SECRET_KEY: \${SECRET_KEY:-change-this-secret-key-in-production}
      DEFAULT_ADMIN_USERNAME: \${ADMIN_USERNAME:-admin}
      DEFAULT_ADMIN_PASSWORD: \${ADMIN_PASSWORD:-admin123}
      ALGORITHM: HS256
      ACCESS_TOKEN_EXPIRE_MINUTES: 30
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

  worker:
    image: ${WORKER_IMAGE}
    container_name: noc-worker
    environment:
      # Database settings
      NOC_DATABASE: postgres
      NOC_USERNAME: \${POSTGRES_USER:-noc_user}
      NOC_PASSWORD: \${POSTGRES_PASSWORD:-changeme123}
      NOC_DATABASE_PORT: 5432
      NOC_DATABASE_NAME: \${POSTGRES_DB:-noc}
      NOC_DATABASE_SSL: "false"

      # Redis settings
      NOC_REDIS_HOST: redis
      NOC_REDIS_PORT: 6379
      NOC_REDIS_PASSWORD: \${REDIS_PASSWORD:-changeme456}
      NOC_REDIS_SSL: "false"

      # App settings
      SECRET_KEY: \${SECRET_KEY:-change-this-secret-key-in-production}
      ALGORITHM: HS256
    volumes:
      - app_data:/app/data
    depends_on:
      - redis
      - postgres
      - backend
    networks:
      - noc-network
    restart: unless-stopped

  frontend:
    image: ${FRONTEND_IMAGE}
    container_name: noc-frontend
    ports:
      - "\${FRONTEND_PORT:-3000}:80"
    depends_on:
      - backend
    networks:
      - noc-network
    restart: unless-stopped

networks:
  noc-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  app_data:
EOF

# Step 8: Create .env template
cat > "$OUTPUT_DIR/config/.env.example" << 'EOF'
# Database Configuration
POSTGRES_DB=noc
POSTGRES_USER=noc_user
POSTGRES_PASSWORD=changeme123
POSTGRES_PORT=5432

# Redis Configuration
REDIS_PASSWORD=changeme456
REDIS_PORT=6379

# Application Configuration
SECRET_KEY=change-this-secret-key-in-production
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# Frontend Port
FRONTEND_PORT=3000
EOF

# Step 9: Create deployment script
print_status "Creating deployment script..."
cat > "$OUTPUT_DIR/deploy.sh" << 'EOF'
#!/bin/bash
set -e

echo "=========================================="
echo "NOC Canvas Air-gapped Deployment"
echo "=========================================="

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed or not in PATH"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "ERROR: Docker daemon is not running"
    exit 1
fi

# Load images
echo "Loading Docker images..."
echo "This may take several minutes..."

docker load < images/postgres.tar.gz
docker load < images/redis.tar.gz
docker load < images/noc-backend.tar.gz
docker load < images/noc-worker.tar.gz
docker load < images/noc-frontend.tar.gz

echo "All images loaded successfully!"

# Check for .env file
if [ ! -f .env ]; then
    echo "No .env file found. Creating from template..."
    cp config/.env.example .env
    echo ""
    echo "WARNING: Using default configuration!"
    echo "Please edit .env file and change default passwords before production use."
    echo ""
fi

# Start services
echo "Starting NOC Canvas services..."
docker-compose up -d

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Services are starting up..."
echo ""
echo "Access the application:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Default credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "IMPORTANT: Change default passwords in production!"
echo ""
echo "Useful commands:"
echo "  Check status: docker-compose ps"
echo "  View logs: docker-compose logs -f"
echo "  Stop services: docker-compose down"
echo "  Restart services: docker-compose restart"
echo ""
EOF

chmod +x "$OUTPUT_DIR/deploy.sh"

# Step 10: Create stop script
cat > "$OUTPUT_DIR/stop.sh" << 'EOF'
#!/bin/bash
echo "Stopping NOC Canvas services..."
docker-compose down
echo "Services stopped."
EOF

chmod +x "$OUTPUT_DIR/stop.sh"

# Step 11: Create README
cat > "$OUTPUT_DIR/README.md" << 'EOF'
# NOC Canvas - Air-gapped Deployment Package

This package contains everything needed to deploy NOC Canvas in an air-gapped environment.

## Contents

- `images/` - Pre-built Docker images (compressed)
- `docker-compose.yaml` - Service orchestration configuration
- `config/.env.example` - Environment configuration template
- `deploy.sh` - Deployment script
- `stop.sh` - Stop script
- `README.md` - This file

## Requirements

- Docker Engine 20.x or newer
- Docker Compose 2.x or newer
- 4GB+ RAM available
- 10GB+ disk space

## Quick Start

1. **Copy this entire directory** to your air-gapped system

2. **Configure environment** (optional but recommended):
   ```bash
   cp config/.env.example .env
   nano .env  # Edit passwords and secrets
   ```

3. **Deploy**:
   ```bash
   ./deploy.sh
   ```

4. **Access the application**:
   - Frontend: http://localhost:3000
   - API: http://localhost:8000

## Default Credentials

- **Username**: admin
- **Password**: admin123

**⚠️ CHANGE THESE IN PRODUCTION!**

## Management Commands

### Check status
```bash
docker-compose ps
```

### View logs
```bash
docker-compose logs -f
```

### View specific service logs
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f worker
```

### Restart services
```bash
docker-compose restart
```

### Stop services
```bash
./stop.sh
# or
docker-compose down
```

### Update configuration
1. Edit `.env` file
2. Restart services: `docker-compose up -d`

## Data Persistence

Data is stored in Docker volumes:
- `postgres_data` - Database
- `redis_data` - Cache and queue data
- `app_data` - Application data and settings

### Backup Data

```bash
# Backup database
docker-compose exec postgres pg_dump -U noc_user noc > backup-$(date +%Y%m%d).sql

# Backup volumes
docker run --rm -v noc-canvas_app_data:/data -v $(pwd):/backup alpine tar czf /backup/app-data-$(date +%Y%m%d).tar.gz -C /data .
```

### Restore Database

```bash
docker-compose exec -T postgres psql -U noc_user noc < backup-20240101.sql
```

## Security Checklist

- [ ] Change default admin password
- [ ] Update SECRET_KEY in .env
- [ ] Change database password
- [ ] Change Redis password
- [ ] Configure firewall rules
- [ ] Enable HTTPS (requires additional configuration)
- [ ] Regular backups configured

## Troubleshooting

### Services won't start

Check logs:
```bash
docker-compose logs
```

### Database connection errors

Ensure PostgreSQL is healthy:
```bash
docker-compose ps postgres
docker-compose logs postgres
```

### Cannot access frontend

Check if port 3000 is available:
```bash
netstat -tulpn | grep 3000
```

### Reset everything

⚠️ This will delete all data!
```bash
docker-compose down -v
./deploy.sh
```

## Support

For issues and documentation, contact your system administrator.
EOF

# Create checksums
print_status "Creating checksums..."
cd "$OUTPUT_DIR/images"
sha256sum *.tar.gz > checksums.sha256
cd "$PROJECT_ROOT"

# Final summary
print_success "Build completed successfully!"
echo ""
echo "=========================================="
echo "AIR-GAPPED DEPLOYMENT PACKAGE READY"
echo "=========================================="
echo ""
echo "Location: $OUTPUT_DIR"
echo ""
echo "Package contents:"
echo "  ├── images/                    # Docker images (~2-3 GB)"
echo "  │   ├── noc-backend.tar.gz"
echo "  │   ├── noc-worker.tar.gz"
echo "  │   ├── noc-frontend.tar.gz"
echo "  │   ├── postgres.tar.gz"
echo "  │   ├── redis.tar.gz"
echo "  │   └── checksums.sha256"
echo "  ├── config/"
echo "  │   └── .env.example          # Configuration template"
echo "  ├── docker-compose.yaml       # Service configuration"
echo "  ├── deploy.sh                 # Deployment script"
echo "  ├── stop.sh                   # Stop script"
echo "  └── README.md                 # Documentation"
echo ""
TOTAL_SIZE=$(du -sh "$OUTPUT_DIR" | cut -f1)
echo "Total package size: $TOTAL_SIZE"
echo ""
echo "To deploy on air-gapped system:"
echo "  1. Copy entire directory to target system"
echo "  2. cd $(basename "$OUTPUT_DIR")"
echo "  3. ./deploy.sh"
echo ""
print_success "Ready for air-gapped deployment!"
