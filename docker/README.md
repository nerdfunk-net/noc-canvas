# NOC Canvas Docker Setup

This directory contains all the necessary Docker configuration files for deploying NOC Canvas in containerized environments, including air-gapped deployments.

## Files Overview

### Core Docker Files
- `docker-compose.yaml` - Main Docker Compose configuration for development/testing
- `Dockerfile.backend` - Backend application container
- `Dockerfile.worker` - Celery worker and beat container (shared)
- `Dockerfile.frontend` - Frontend application container
- `nginx.conf` - Nginx web server configuration
- `default.conf` - Nginx site configuration

### Scripts
- `prepare-airgapped.sh` - Comprehensive script to prepare air-gapped deployment package
- `test-docker.sh` - Script to test Docker setup locally
- `backend-entrypoint.sh` - Backend container startup script
- `worker-entrypoint.sh` - Worker container startup script

### Configuration
- `.env.template` - Environment configuration template
- `init-db.sql` - PostgreSQL initialization script

## Quick Start (Development/Testing)

1. **Set up environment variables:**
   ```bash
   cp .env.template .env
   # Edit .env file with your desired configuration
   ```

2. **Test the Docker setup locally:**
   ```bash
   ./test-docker.sh
   ```

3. **Manual startup:**
   ```bash
   docker-compose up --build -d
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

5. **Default credentials:**
   - Username: Set by `DEFAULT_ADMIN_USERNAME` in .env (default: `username`)
   - Password: Set by `DEFAULT_ADMIN_PASSWORD` in .env (default: `password`)

## Air-gapped Deployment

For deployment in air-gapped environments where internet access is not available:

1. **Prepare the deployment package:**
   ```bash
   ./prepare-airgapped.sh
   ```

2. **This creates a complete deployment package including:**
   - All Docker base images
   - All Python dependencies (offline installation)
   - Built frontend assets
   - Configuration files
   - Deployment scripts

3. **Transfer the generated `build/` directory to your air-gapped environment**

4. **Deploy in the air-gapped environment:**
   ```bash
   cd build
   ./deploy-airgapped.sh
   ```

## Architecture

The Docker setup consists of 5 containers:

```
┌─────────────────┐    ┌─────────────────┐
│   noc-frontend  │    │   noc-backend   │
│   (nginx:alpine)│────│  (FastAPI)      │
│   Port: 3000    │    │   Port: 8000    │
└─────────────────┘    └─────────────────┘
                              │
                              │ HTTP (internal)
                              ▼
                       ┌─────────────────┐
                       │   noc-worker    │
                       │  (Celery)       │──┐
                       │                 │  │ Device
                       └─────────────────┘  │ Commands
                              │              │ (SSH/Netmiko)
        ┌─────────────────────┼──────────────┼────────┐
        │                     │              │        │
┌─────────────────┐    ┌─────────────────┐  │  ┌───────────────┐
│     postgres    │    │      redis      │  │  │ Network       │
│ (postgres:15)   │    │  (redis:8-alpine)│  │  │ Devices       │
│  Port: 5432     │    │   Port: 6379    │  │  └───────────────┘
└─────────────────┘    └─────────────────┘  │
                                             │
                              ┌──────────────┘
                              ▼
                       noc-network (bridge)
```

### Container Communication

- **Frontend → Backend**: HTTP requests to `noc-backend:8000`
- **Worker → Backend**: HTTP requests to `noc-backend:8000` (for device command execution)
- **Worker → Devices**: Direct SSH connections via Netmiko
- **Backend/Worker → Database**: PostgreSQL connection to `postgres:5432`
- **Backend/Worker → Redis**: Redis connection to `redis:6379` (job queue & cache)

### Background Job Architecture

The Celery worker runs topology discovery and other background jobs:

1. **User triggers job** via Frontend → Backend
2. **Backend submits task** to Celery via Redis queue
3. **Worker picks up task** and executes it asynchronously
4. **Worker calls Backend API** to execute device commands (via HTTP to `noc-backend:8000`)
5. **Backend connects to devices** via SSH/Netmiko and returns data
6. **Worker caches results** to PostgreSQL database
7. **User sees progress** and results via Frontend

## Configuration

### Environment Variables

**Important**: All configuration is now done via environment variables loaded from a `.env` file.

1. **Create your .env file:**
   ```bash
   cp .env.template .env
   ```

2. **Edit .env file** with your configuration:
   ```bash
   # Example .env file
   SECRET_KEY=your-secret-key-change-this-in-production
   DEFAULT_ADMIN_USERNAME=admin
   DEFAULT_ADMIN_PASSWORD=secure-password-123
   NOC_USERNAME=postgres
   NOC_PASSWORD=your-db-password
   NOC_REDIS_PASSWORD=your-redis-password
   ```

### Key Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Application secret key | `your-secret-key-change-this-in-production` |
| `DEFAULT_ADMIN_USERNAME` | Default admin username | `username` |
| `DEFAULT_ADMIN_PASSWORD` | Default admin password | `password` |
| `NOC_USERNAME` | PostgreSQL username | `postgres` |
| `NOC_PASSWORD` | PostgreSQL password | `postgres` |
| `NOC_DATABASE_NAME` | Database name | `noc` |
| `NOC_DATABASE_PORT` | Database port | `5432` |
| `NOC_REDIS_PASSWORD` | Redis password | `changeme` |
| `NOC_REDIS_PORT` | Redis port | `6379` |
| `INTERNAL_API_URL` | Internal API URL for worker | `http://noc-backend:8000` |

**Worker-Specific Variables:**
- `INTERNAL_API_URL`: The URL the Celery worker uses to call the FastAPI backend for device operations. In Docker, this is `http://noc-backend:8000` (using the container service name). For local development outside Docker, use `http://localhost:8000`.

**Important for Production:**
- Change `SECRET_KEY` to a secure 64+ character random string
- Change all default passwords
- Use strong passwords for database and Redis

### Persistent Data

The following Docker volumes store persistent data:
- `postgres_data` - PostgreSQL database
- `redis_data` - Redis cache and job queue data  
- `app_data` - Application files and settings

### Port Configuration

Default ports can be changed in the environment file:
- Frontend: 3000
- Backend API: 8000  
- PostgreSQL: 5432
- Redis: 6379

## Health Checks

All containers include health checks:
- **Backend**: HTTP GET to `/health` endpoint
- **Frontend**: Basic HTTP connectivity check
- **PostgreSQL**: `pg_isready` command
- **Redis**: Redis PING command

## Logging

View logs for all services:
```bash
docker-compose logs -f
```

View logs for a specific service:
```bash
docker-compose logs -f noc-backend
docker-compose logs -f noc-worker
docker-compose logs -f noc-frontend
```

## Backup and Maintenance

### Create Backup
```bash
# Database backup
docker-compose exec postgres pg_dump -U postgres noc > backup.sql

# Volume backup  
docker run --rm -v noc-canvas_app_data:/data -v $(pwd):/backup alpine tar czf /backup/app_data_backup.tar.gz -C /data .
```

### Restore Backup
```bash
# Database restore
docker-compose exec -T postgres psql -U postgres noc < backup.sql

# Volume restore
docker run --rm -v noc-canvas_app_data:/data -v $(pwd):/backup alpine tar xzf /backup/app_data_backup.tar.gz -C /data
```

### Update Application
```bash
# Pull latest code and rebuild
docker-compose down
git pull  # or update source code
docker-compose up --build -d
```

## Troubleshooting

### Common Issues

1. **Services fail to start:**
   - Check Docker daemon is running: `docker info`
   - Check port availability: `netstat -ln | grep :3000`
   - Review logs: `docker-compose logs [service-name]`

2. **Database connection errors:**
   - Verify PostgreSQL is running: `docker-compose ps postgres`
   - Check database logs: `docker-compose logs postgres`
   - Verify environment variables in docker-compose.yaml

3. **Redis connection errors:**
   - Verify Redis is running: `docker-compose ps redis`  
   - Check Redis logs: `docker-compose logs redis`
   - Test Redis connectivity: `docker-compose exec redis redis-cli ping`

4. **Frontend not loading:**
   - Check nginx logs: `docker-compose logs noc-frontend`
   - Verify backend API is accessible: `curl http://localhost:8000/health`
   - Check browser network tab for API call failures

### Reset Environment
```bash
# Stop all services and remove volumes (DELETES ALL DATA!)
docker-compose down -v

# Remove all images to force rebuild
docker-compose down --rmi all

# Start fresh
docker-compose up --build -d
```

## Security Considerations

1. **Change default passwords** before production deployment
2. **Use strong SECRET_KEY** (64+ character random string)
3. **Configure firewall rules** to limit external access
4. **Use HTTPS** in production (requires additional reverse proxy configuration)
5. **Regularly update** base Docker images
6. **Monitor logs** for security events
7. **Backup data regularly** and test restore procedures

## Production Deployment

For production environments:

1. Use a reverse proxy (nginx, Traefik) with SSL termination
2. Configure proper logging and monitoring
3. Set up automated backups
4. Use Docker secrets for sensitive data
5. Consider using Docker Swarm or Kubernetes for high availability
6. Implement proper network segmentation
7. Set up centralized log collection

## Services Architecture

The Docker Compose deployment includes 6 services:

### 1. PostgreSQL (`noc-postgres`)
- **Purpose**: Primary database for persistent storage
- **Port**: 5432 (configurable via `NOC_DATABASE_PORT`)
- **Volume**: `postgres_data` for data persistence
- **Health Check**: `pg_isready` command

### 2. Redis (`noc-redis`)
- **Purpose**: Message broker for Celery and caching
- **Port**: 6379 (configurable via `NOC_REDIS_PORT`)
- **Volume**: `redis_data` for persistence
- **Health Check**: `redis-cli ping`
- **Authentication**: Password-protected (set via `NOC_REDIS_PASSWORD`)

### 3. Backend (`noc-backend`)
- **Purpose**: FastAPI REST API server
- **Port**: 8000
- **Volume**: `app_data` shared with workers
- **Health Check**: HTTP GET to `/health`
- **Dependencies**: PostgreSQL (healthy), Redis (healthy)

### 4. Celery Worker (`noc-worker`)
- **Purpose**: Executes background tasks
  - Device discovery (CDP, LLDP, ARP)
  - SSH command execution
  - Data collection and processing
  - Topology building
  - Baseline comparisons
- **Command**: `python start_worker.py`
- **Volume**: Shared `app_data` with backend
- **Health Check**: Celery inspect active workers
- **Dependencies**: PostgreSQL, Redis, Backend (all healthy)
- **Scaling**: Can run multiple instances (`docker-compose up -d --scale noc-worker=3`)

### 5. Celery Beat (`noc-beat`)
- **Purpose**: Schedules periodic tasks
  - Auto-refresh cache
  - Cleanup expired data
  - Baseline checks
  - Scheduled discoveries
- **Command**: `python start_beat.py`
- **Volume**: Shared `app_data` with backend
- **Health Check**: Process check for celery beat
- **Dependencies**: PostgreSQL, Redis, Backend (all healthy)
- **⚠️ IMPORTANT**: Only ONE beat instance should run (do NOT scale)

### 6. Frontend (`noc-frontend`)
- **Purpose**: Vue.js SPA served via Nginx
- **Port**: 3000
- **Dependencies**: Backend (for API calls)

## Celery Management

### Monitor Worker Tasks

```bash
# Check active tasks
docker exec noc-worker celery -A app.services.background_jobs inspect active

# Check registered tasks
docker exec noc-worker celery -A app.services.background_jobs inspect registered

# Worker statistics
docker exec noc-worker celery -A app.services.background_jobs inspect stats

# Check worker queues
docker exec noc-worker celery -A app.services.background_jobs inspect active_queues
```

### Monitor Beat Schedule

```bash
# View scheduled tasks from database
docker exec noc-postgres psql -U postgres -d noc -c \
  "SELECT name, task, enabled, crontab_id FROM celery_periodic_task;"

# Check beat logs
docker-compose logs -f noc-beat

# Verify beat is running
docker exec noc-beat ps aux | grep celery
```

### Scaling Workers

```bash
# Scale to 3 worker instances
docker-compose up -d --scale noc-worker=3

# Verify all workers are registered
docker exec noc-worker celery -A app.services.background_jobs inspect ping
```

### Restart Workers/Beat

```bash
# Restart worker (graceful shutdown)
docker-compose restart noc-worker

# Restart beat (only one instance)
docker-compose restart noc-beat

# Force restart (immediate)
docker-compose stop noc-worker noc-beat
docker-compose start noc-worker noc-beat
```

## Troubleshooting Celery

### Worker Not Processing Tasks

1. **Check worker is running:**
   ```bash
   docker-compose ps noc-worker
   docker-compose logs noc-worker
   ```

2. **Verify Redis connection:**
   ```bash
   docker exec noc-worker python -c \
     "from app.core.celery_app import celery_app; print(celery_app.connection().connect())"
   ```

3. **Check registered tasks:**
   ```bash
   docker exec noc-worker celery -A app.services.background_jobs inspect registered
   ```

4. **Monitor task execution:**
   ```bash
   docker exec noc-worker celery -A app.services.background_jobs events
   ```

### Beat Not Scheduling Tasks

1. **Ensure only ONE beat instance:**
   ```bash
   docker-compose ps noc-beat
   # Should show exactly 1 running instance
   ```

2. **Check beat logs for errors:**
   ```bash
   docker-compose logs -f noc-beat | grep -i error
   ```

3. **Verify scheduler table exists:**
   ```bash
   docker exec noc-postgres psql -U postgres -d noc -c "\dt celery*"
   ```

4. **Check beat process:**
   ```bash
   docker exec noc-beat ps aux | grep celery.*beat
   ```

### Tasks Failing

1. **Check worker logs:**
   ```bash
   docker-compose logs --tail=100 noc-worker | grep -i error
   ```

2. **Check task results in database:**
   ```bash
   docker exec noc-postgres psql -U postgres -d noc -c \
     "SELECT task_id, status, result FROM celery_taskmeta ORDER BY date_done DESC LIMIT 10;"
   ```

3. **Verify environment variables:**
   ```bash
   docker exec noc-worker env | grep NOC_
   ```

## Support

- Check logs first: `docker-compose logs -f`
- Verify service health: `docker-compose ps`
- Test connectivity: `curl http://localhost:8000/health`
- Check Celery workers: `docker exec noc-worker celery -A app.services.background_jobs inspect ping`
- For application-specific issues, check the main project documentation