# NOC Canvas Docker Setup

This directory contains all the necessary Docker configuration files for deploying NOC Canvas in containerized environments, including air-gapped deployments.

## Files Overview

### Core Docker Files
- `docker-compose.yaml` - Main Docker Compose configuration for development/testing
- `Dockerfile.backend` - Backend application container
- `Dockerfile.worker` - Celery worker container  
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
│   (nginx:alpine)│────│  (python:3.11)  │
│   Port: 3000    │    │   Port: 8000    │
└─────────────────┘    └─────────────────┘
                              │
                       ┌─────────────────┐
                       │   noc-worker    │
                       │  (python:3.11)  │
                       │  (Celery)       │
                       └─────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌─────────────────┐    ┌─────────────────┐  ┌─────────────────┐
│     postgres    │    │      redis      │  │   noc-network   │
│ (postgres:15)   │    │  (redis:7-alpine)│  │   (bridge)      │
│  Port: 5432     │    │   Port: 6379    │  │                 │
└─────────────────┘    └─────────────────┘  └─────────────────┘
```

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

## Support

- Check logs first: `docker-compose logs -f`
- Verify service health: `docker-compose ps`
- Test connectivity: `curl http://localhost:8000/health`
- For application-specific issues, check the main project documentation