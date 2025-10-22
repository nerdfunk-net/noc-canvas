# NOC Canvas Deployment Guide

## Overview

NOC Canvas supports multiple deployment methods:

1. **Development** - Local development with hot-reload
2. **Production** - Optimized production deployment
3. **Air-gapped** - Complete offline deployment (no internet required)

## Quick Reference

| Method | Script | Use Case |
|--------|--------|----------|
| Development | `./docker/deploy.sh dev` | Local development |
| Production | `./docker/deploy.sh prod` | Production with internet |
| **Air-gapped** | `./docker/build-airgapped-images.sh` | **Offline/secure environments** |

---

## Air-Gapped Deployment

### Overview

The `build-airgapped-images.sh` script creates a complete, self-contained deployment package that can run in environments with **no internet access**.

**Key Features:**
- ✅ All dependencies bundled (including Font Awesome)
- ✅ Pre-built Docker images - no compilation on target system
- ✅ Only requires Docker on target system
- ✅ True "build once, deploy anywhere" approach
- ✅ Perfect for secure, isolated, or offline environments

---

### Step 1: Build Package (Internet-Connected System)

On a system **with internet access**, run:

```bash
cd /path/to/noc-canvas
./docker/build-airgapped-images.sh
```

**What this does:**
1. Installs frontend dependencies (including Font Awesome locally)
2. Builds production frontend bundle
3. Creates 3 Docker images:
   - `noc-canvas-backend` - Python/FastAPI backend
   - `noc-canvas-worker` - Celery worker
   - `noc-canvas-frontend` - Nginx + Vue.js app
4. Pulls base images (PostgreSQL 16, Redis 7)
5. Saves everything as compressed tar files
6. Creates deployment scripts and documentation

**Build time:** ~5-10 minutes (depending on system)

**Output:** `airgapped-images/` directory (~2-3 GB) containing:

```
airgapped-images/
├── images/
│   ├── noc-backend.tar.gz       (~500 MB)
│   ├── noc-worker.tar.gz        (~500 MB)
│   ├── noc-frontend.tar.gz      (~200 MB)
│   ├── postgres.tar.gz          (~150 MB)
│   ├── redis.tar.gz             (~50 MB)
│   └── checksums.sha256         (verification)
├── docker-compose.yaml          (orchestration config)
├── deploy.sh                    (deployment script)
├── stop.sh                      (stop script)
├── config/
│   └── .env.example            (configuration template)
└── README.md                    (deployment instructions)
```

---

### Step 2: Transfer to Air-Gapped System

Transfer the entire `airgapped-images/` directory to your air-gapped system using your preferred method:

**Option A: USB Drive**
```bash
cp -r airgapped-images /media/usb/
```

**Option B: Compressed Archive**
```bash
# Create archive
tar czf noc-canvas-airgapped.tar.gz airgapped-images/

# On target system, extract:
tar xzf noc-canvas-airgapped.tar.gz
```

**Option C: SCP (before air-gap)**
```bash
scp -r airgapped-images user@target:/opt/
```

**Option D: Network Share**
```bash
cp -r airgapped-images /mnt/network-share/
```

---

### Step 3: Verify Transfer (Optional but Recommended)

On the air-gapped system, verify file integrity:

```bash
cd airgapped-images/images
sha256sum -c checksums.sha256
```

You should see:
```
noc-backend.tar.gz: OK
noc-worker.tar.gz: OK
noc-frontend.tar.gz: OK
postgres.tar.gz: OK
redis.tar.gz: OK
```

---

### Step 4: Configure (Optional)

Before deployment, you can customize the configuration:

```bash
cd airgapped-images

# Copy template and edit
cp config/.env.example .env
nano .env
```

**Important settings to change:**

```bash
# Security (REQUIRED for production!)
SECRET_KEY=your-long-random-secret-key-here
ADMIN_PASSWORD=your-secure-password

# Database
POSTGRES_PASSWORD=your-database-password
POSTGRES_USER=noc_user
POSTGRES_DB=noc

# Redis
REDIS_PASSWORD=your-redis-password

# Network (optional)
FRONTEND_PORT=3000
```

**If you skip this step**, the deployment will use secure defaults, but you should change passwords after first login.

---

### Step 5: Deploy

On the air-gapped system:

```bash
cd airgapped-images
./deploy.sh
```

**What deploy.sh does:**
1. Loads all Docker images from tar files (~3-5 minutes)
2. Creates necessary Docker networks and volumes
3. Starts all services with docker-compose
4. Shows access information

**Expected output:**
```
==========================================
NOC Canvas Air-gapped Deployment
==========================================

Loading Docker images...
This may take several minutes...

Loaded image: postgres:16-alpine
Loaded image: redis:7-alpine
Loaded image: noc-canvas-backend:latest
Loaded image: noc-canvas-worker:latest
Loaded image: noc-canvas-frontend:latest

All images loaded successfully!

Starting NOC Canvas services...
Creating network "noc-network"
Creating volume "postgres_data"
Creating volume "redis_data"
Creating volume "app_data"
Creating noc-postgres ... done
Creating noc-redis ... done
Creating noc-backend ... done
Creating noc-worker ... done
Creating noc-frontend ... done

==========================================
Deployment Complete!
==========================================

Access the application:
  Frontend: http://localhost:3000
  Backend API: http://localhost:8000
  API Docs: http://localhost:8000/docs

Default credentials:
  Username: admin
  Password: admin123

IMPORTANT: Change default passwords in production!
```

---

### Step 6: Access Application

Open your web browser and navigate to:

- **Frontend UI:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

⚠️ **IMPORTANT:** Change the default password immediately in production!

---

## Management & Operations

### Check Service Status

```bash
cd airgapped-images
docker-compose ps
```

**Expected output:**
```
NAME            SERVICE    STATUS      PORTS
noc-backend     backend    Up (healthy)  0.0.0.0:8000->8000/tcp
noc-frontend    frontend   Up (healthy)  0.0.0.0:3000->80/tcp
noc-postgres    postgres   Up (healthy)  0.0.0.0:5432->5432/tcp
noc-redis       redis      Up (healthy)  0.0.0.0:6379->6379/tcp
noc-worker      worker     Up
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f worker
docker-compose logs -f postgres
docker-compose logs -f redis

# Last 100 lines
docker-compose logs --tail=100

# Since 10 minutes ago
docker-compose logs --since 10m
```

### Restart Services

```bash
# All services
docker-compose restart

# Specific service
docker-compose restart backend
docker-compose restart worker

# Hard restart (recreate containers)
docker-compose down
docker-compose up -d
```

### Stop Services

```bash
# Using stop script
./stop.sh

# Or using docker-compose
docker-compose down

# Stop and remove volumes (⚠️ deletes all data!)
docker-compose down -v
```

### Update Configuration

1. Edit `.env` file:
   ```bash
   nano .env
   ```

2. Apply changes:
   ```bash
   docker-compose up -d
   ```

Docker Compose will automatically recreate only the services that need changes.

---

## Data Management

### Data Persistence

All data is stored in Docker volumes:

| Volume | Purpose | Size (typical) |
|--------|---------|----------------|
| `postgres_data` | Database | ~100 MB - 10 GB |
| `redis_data` | Cache and job queue | ~10 MB - 1 GB |
| `app_data` | Application settings, backups | ~10 MB - 1 GB |

**Location:** Docker volumes are managed by Docker and stored in:
- Linux: `/var/lib/docker/volumes/`
- macOS: Docker Desktop VM
- Windows: Docker Desktop VM

### Backup Database

```bash
# Create backup directory
mkdir -p backups

# Backup database (SQL dump)
docker-compose exec postgres pg_dump -U noc_user noc > backups/backup-$(date +%Y%m%d-%H%M%S).sql

# Compress backup
gzip backups/backup-$(date +%Y%m%d-%H%M%S).sql
```

### Backup Application Data

```bash
# Backup app data volume
docker run --rm \
  -v noc-canvas_app_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/app-data-$(date +%Y%m%d-%H%M%S).tar.gz -C /data .
```

### Backup All Volumes

```bash
#!/bin/bash
# backup-all.sh

BACKUP_DIR="backups/full-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Database
docker-compose exec -T postgres pg_dump -U noc_user noc | gzip > "$BACKUP_DIR/database.sql.gz"

# App data
docker run --rm \
  -v noc-canvas_app_data:/data \
  -v $(pwd)/$BACKUP_DIR:/backup \
  alpine tar czf /backup/app-data.tar.gz -C /data .

# Redis (optional)
docker run --rm \
  -v noc-canvas_redis_data:/data \
  -v $(pwd)/$BACKUP_DIR:/backup \
  alpine tar czf /backup/redis-data.tar.gz -C /data .

echo "Backup completed: $BACKUP_DIR"
```

### Restore Database

```bash
# Stop backend and worker
docker-compose stop backend worker

# Restore database
gunzip -c backups/backup-20240101-120000.sql.gz | \
  docker-compose exec -T postgres psql -U noc_user noc

# Restart services
docker-compose start backend worker
```

### Restore Application Data

```bash
# Stop backend
docker-compose stop backend worker

# Restore app data
docker run --rm \
  -v noc-canvas_app_data:/data \
  -v $(pwd)/backups:/backup \
  alpine sh -c "cd /data && tar xzf /backup/app-data-20240101-120000.tar.gz"

# Restart services
docker-compose start backend worker
```

---

## Security Hardening

### Pre-Deployment Checklist

Before deploying to production:

- [ ] Change `SECRET_KEY` to a strong random value (min 32 characters)
- [ ] Change `ADMIN_PASSWORD` from default
- [ ] Change `POSTGRES_PASSWORD` to a strong password
- [ ] Change `REDIS_PASSWORD` to a strong password
- [ ] Review `.env` file - no sensitive data exposed
- [ ] Limit network access (firewall rules)
- [ ] Enable HTTPS (requires reverse proxy)
- [ ] Set up regular backups (automated)
- [ ] Configure log rotation
- [ ] Review Docker security settings
- [ ] Document access procedures

### Change Admin Password

**Method 1: Via UI**
1. Login as admin
2. Go to Settings → Profile
3. Change password

**Method 2: Via Environment**
1. Edit `.env`:
   ```bash
   ADMIN_PASSWORD=new-secure-password
   ```
2. Restart backend:
   ```bash
   docker-compose restart backend
   ```

### Generate Secure SECRET_KEY

```bash
# Python method
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL method
openssl rand -base64 32

# /dev/urandom method
tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 32 && echo
```

### Network Security

**Firewall Configuration (example for ufw):**

```bash
# Allow SSH (if needed)
sudo ufw allow 22/tcp

# Allow frontend
sudo ufw allow 3000/tcp

# Allow backend API
sudo ufw allow 8000/tcp

# Deny all other incoming
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Enable firewall
sudo ufw enable
```

**Or restrict to specific IPs:**

```bash
# Allow only from specific subnet
sudo ufw allow from 192.168.1.0/24 to any port 3000
sudo ufw allow from 192.168.1.0/24 to any port 8000
```

### HTTPS Setup (Reverse Proxy)

For production, use a reverse proxy like Nginx:

```nginx
# /etc/nginx/sites-available/noc-canvas
server {
    listen 443 ssl http2;
    server_name noc.example.com;

    ssl_certificate /etc/ssl/certs/noc.crt;
    ssl_certificate_key /etc/ssl/private/noc.key;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Troubleshooting

### Services Won't Start

**Symptom:** `docker-compose up -d` fails

**Solutions:**

1. **Check logs:**
   ```bash
   docker-compose logs
   ```

2. **Check individual service:**
   ```bash
   docker-compose ps
   docker-compose logs backend
   ```

3. **Check port conflicts:**
   ```bash
   # Check if ports are already in use
   netstat -tulpn | grep -E ':(3000|8000|5432|6379)'
   # or on macOS:
   lsof -i :3000
   lsof -i :8000
   ```

4. **Check Docker daemon:**
   ```bash
   docker info
   systemctl status docker  # on Linux
   ```

5. **Check disk space:**
   ```bash
   df -h
   docker system df
   ```

### Database Connection Errors

**Symptom:** Backend shows "could not connect to database"

**Solutions:**

1. **Verify PostgreSQL is healthy:**
   ```bash
   docker-compose ps postgres
   docker-compose logs postgres
   ```

2. **Check connection from backend:**
   ```bash
   docker-compose exec backend env | grep NOC_
   ```

3. **Test connection manually:**
   ```bash
   docker-compose exec postgres psql -U noc_user -d noc -c "SELECT 1;"
   ```

4. **Check if database exists:**
   ```bash
   docker-compose exec postgres psql -U noc_user -l
   ```

5. **Recreate database (⚠️ deletes data):**
   ```bash
   docker-compose down
   docker volume rm noc-canvas_postgres_data
   docker-compose up -d
   ```

### Frontend Not Loading

**Symptom:** Browser shows "connection refused" or blank page

**Solutions:**

1. **Check if frontend is running:**
   ```bash
   docker-compose ps frontend
   docker-compose logs frontend
   ```

2. **Check if port is accessible:**
   ```bash
   curl http://localhost:3000
   ```

3. **Check firewall:**
   ```bash
   sudo ufw status  # Linux
   sudo iptables -L  # Linux
   ```

4. **Check browser console:**
   - Open browser DevTools (F12)
   - Check Console tab for errors
   - Check Network tab for failed requests

5. **Verify API connection:**
   ```bash
   curl http://localhost:8000/health
   ```

### Worker Not Processing Jobs

**Symptom:** Background tasks don't run

**Solutions:**

1. **Check worker logs:**
   ```bash
   docker-compose logs worker
   ```

2. **Check Redis connection:**
   ```bash
   docker-compose exec redis redis-cli -a $(grep REDIS_PASSWORD .env | cut -d'=' -f2) ping
   ```

3. **Check active tasks:**
   ```bash
   docker-compose exec worker python -c "
   from app.services.background_jobs import celery_app
   print(celery_app.control.inspect().active())
   "
   ```

4. **Check registered tasks:**
   ```bash
   docker-compose exec worker python -c "
   from app.services.background_jobs import celery_app
   print(list(celery_app.tasks.keys()))
   "
   ```

5. **Restart worker:**
   ```bash
   docker-compose restart worker
   ```

### High Memory Usage

**Symptom:** System running out of memory

**Solutions:**

1. **Check memory usage:**
   ```bash
   docker stats
   ```

2. **Limit container memory:**
   Edit `docker-compose.yaml`:
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             memory: 1G
     worker:
       deploy:
         resources:
           limits:
             memory: 1G
   ```

3. **Reduce worker concurrency:**
   Edit `docker-compose.yaml`:
   ```yaml
   worker:
     command: python -m celery -A app.services.background_jobs worker --loglevel=info --concurrency=1
   ```

### Complete Reset

**⚠️ WARNING: This will delete ALL data!**

```bash
# Stop and remove everything
docker-compose down -v

# Remove all NOC Canvas images (optional)
docker images | grep noc-canvas | awk '{print $3}' | xargs docker rmi

# Redeploy
./deploy.sh
```

---

## System Requirements

### Minimum:
- **CPU:** 2 cores
- **RAM:** 4 GB
- **Disk:** 10 GB free space
- **Docker:** Engine 20.10+
- **Docker Compose:** 2.0+
- **OS:** Linux, macOS, Windows (with Docker Desktop)

### Recommended:
- **CPU:** 4 cores
- **RAM:** 8 GB
- **Disk:** 20 GB SSD
- **OS:** Linux (Ubuntu 20.04+, Rocky Linux 8+)

### For Production:
- **CPU:** 8+ cores
- **RAM:** 16 GB+
- **Disk:** 50 GB+ SSD with backup storage
- **Network:** 1 Gbps+
- **OS:** Enterprise Linux (RHEL, Rocky, Ubuntu LTS)

---

## Port Reference

| Service | Port | Internal/External | Purpose |
|---------|------|-------------------|---------|
| Frontend | 3000 | External | Web UI |
| Backend | 8000 | External | REST API |
| PostgreSQL | 5432 | Internal* | Database |
| Redis | 6379 | Internal* | Cache/Queue |

**Internal ports** are only accessible from within the Docker network by default. They can be exposed if needed by editing `docker-compose.yaml`.

---

## Environment Variables

See `config/.env.example` for all available options.

### Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `noc` | Database name |
| `POSTGRES_USER` | `noc_user` | Database user |
| `POSTGRES_PASSWORD` | `changeme123` | Database password ⚠️ Change! |
| `POSTGRES_PORT` | `5432` | Database port |

### Redis Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_PASSWORD` | `changeme456` | Redis password ⚠️ Change! |
| `REDIS_PORT` | `6379` | Redis port |

### Application Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `change-this...` | JWT secret ⚠️ Change! |
| `ADMIN_USERNAME` | `admin` | Default admin username |
| `ADMIN_PASSWORD` | `admin123` | Default admin password ⚠️ Change! |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token lifetime |

### Network Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `FRONTEND_PORT` | `3000` | Frontend port |

---

## Monitoring & Maintenance

### Health Checks

All services have built-in health checks:

```bash
# Check all services
docker-compose ps

# Check specific health
docker inspect noc-backend --format='{{.State.Health.Status}}'
docker inspect noc-frontend --format='{{.State.Health.Status}}'
docker inspect noc-postgres --format='{{.State.Health.Status}}'
```

### Log Rotation

Configure Docker log rotation to prevent disk space issues:

**/etc/docker/daemon.json:**
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Then restart Docker:
```bash
sudo systemctl restart docker
docker-compose up -d
```

### Automated Backups

Create a cron job for daily backups:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /opt/noc-canvas/airgapped-images && /opt/noc-canvas/backup-all.sh
```

---

## Upgrading

### Update to New Version

1. **Build new airgapped package** on internet-connected system
2. **Transfer to air-gapped system**
3. **Backup current data** (see Data Management section)
4. **Stop current services:**
   ```bash
   cd airgapped-images
   docker-compose down
   ```
5. **Load new images:**
   ```bash
   cd /path/to/new/airgapped-images
   ./deploy.sh
   ```
6. **Verify upgrade:**
   ```bash
   docker-compose logs -f
   ```

---

## Support & Resources

### Getting Help

1. **Check logs first:**
   ```bash
   docker-compose logs -f
   ```

2. **Review this guide** - especially Troubleshooting section

3. **Check application logs:**
   - Backend: `docker-compose logs backend`
   - Worker: `docker-compose logs worker`
   - Database: `docker-compose logs postgres`

4. **Contact your system administrator**

### Useful Commands Reference

```bash
# Status
docker-compose ps
docker stats

# Logs
docker-compose logs -f
docker-compose logs --tail=100 backend

# Restart
docker-compose restart
docker-compose restart backend

# Stop
docker-compose down

# Complete reset (⚠️ deletes data!)
docker-compose down -v

# Backup database
docker-compose exec postgres pg_dump -U noc_user noc > backup.sql

# Shell access
docker-compose exec backend bash
docker-compose exec postgres psql -U noc_user noc

# Resource usage
docker stats
df -h
```

---

## Appendix

### Font Awesome

✅ **Font Awesome 7.1.0 is bundled locally**

The application includes Font Awesome as a local npm dependency. **No external CDN requests are made**, ensuring the app works completely offline in air-gapped environments.

**Bundled in all production builds:**
- `fa-solid-900.woff2` - Solid icons
- `fa-regular-400.woff2` - Regular icons
- `fa-brands-400.woff2` - Brand icons

**Verification:** Check frontend image for bundled fonts:
```bash
docker run --rm noc-canvas-frontend:latest ls -lh /usr/share/nginx/html/assets/ | grep woff2
```

### Architecture

```
┌─────────────────────────────────────────────┐
│         Air-Gapped System                   │
│                                              │
│  ┌──────────┐      ┌──────────┐            │
│  │ Frontend │      │ Backend  │            │
│  │  :3000   │◄────►│  :8000   │            │
│  └──────────┘      └──────────┘            │
│       │                 │                   │
│       │                 ├──────────┐        │
│       │                 │          │        │
│  ┌────▼─────┐   ┌──────▼──┐  ┌───▼────┐  │
│  │PostgreSQL│   │  Redis  │  │ Worker │  │
│  │  :5432   │   │  :6379  │  │        │  │
│  └──────────┘   └─────────┘  └────────┘  │
│                                              │
└─────────────────────────────────────────────┘
```

### License

See project LICENSE file for details.

### Version

This guide is for NOC Canvas air-gapped deployment v1.0

Last updated: 2024
