# NOC Canvas Backend

A comprehensive FastAPI backend for NOC Canvas with Nautobot and CheckMK integration.

## Features

- **FastAPI** - Modern, fast web framework for building APIs
- **Authentication & Authorization** - JWT-based authentication with role-based access control
- **Nautobot Integration** - Complete GraphQL and REST API integration
- **CheckMK Integration** - Full host management and monitoring capabilities
- **Caching** - Redis-based caching for improved performance
- **Background Jobs** - Celery-based task queue for long-running operations
- **Database Support** - SQLAlchemy ORM with SQLite/PostgreSQL support
- **API Documentation** - Automatic OpenAPI/Swagger documentation

## Architecture

```
backend/
├── app/
│   ├── api/              # API routers
│   │   ├── auth.py       # Authentication endpoints
│   │   ├── devices.py    # Device management
│   │   ├── nautobot.py   # Nautobot integration
│   │   ├── checkmk.py    # CheckMK integration
│   │   ├── settings.py   # Configuration management
│   │   └── jobs.py       # Background job management
│   ├── core/             # Core application modules
│   │   ├── config.py     # Configuration settings
│   │   ├── database.py   # Database setup
│   │   ├── security.py   # Authentication & security
│   │   └── cache.py      # Redis cache service
│   ├── models/           # Pydantic models
│   │   ├── user.py       # User models
│   │   ├── device.py     # Device models
│   │   ├── nautobot.py   # Nautobot data models
│   │   ├── checkmk.py    # CheckMK data models
│   │   └── settings.py   # Settings models
│   ├── services/         # Business logic services
│   │   ├── nautobot.py   # Nautobot service
│   │   ├── checkmk.py    # CheckMK service
│   │   ├── checkmk_client.py  # CheckMK API client
│   │   └── background_jobs.py # Celery tasks
│   └── main.py           # FastAPI application
├── requirements.txt      # Python dependencies
├── start.py             # Development server startup
├── start_worker.py      # Celery worker startup
└── .env.example         # Environment configuration template
```

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start Redis (for caching and background jobs):**
   ```bash
   # Using Docker
   docker run -d -p 6379:6379 redis:alpine

   # Or install locally on macOS
   brew install redis
   brew services start redis
   ```

## Configuration

Copy `.env.example` to `.env` and configure the following:

### Required Settings

- `SECRET_KEY` - JWT signing secret (use a strong random key)
- `NAUTOBOT_URL` - Your Nautobot instance URL
- `NAUTOBOT_TOKEN` - Nautobot API token
- `CHECKMK_URL` - Your CheckMK instance URL
- `CHECKMK_SITE` - CheckMK site name
- `CHECKMK_USERNAME` - CheckMK username
- `CHECKMK_PASSWORD` - CheckMK password

### Optional Settings

- `DATABASE_URL` - Database connection string (defaults to SQLite)
- `REDIS_URL` - Redis connection string
- `CACHE_TTL_SECONDS` - Cache expiration time
- `CORS_ORIGINS` - Allowed frontend origins

## Running the Application

### Development Mode

1. **Start the main application:**
   ```bash
   python start.py
   ```

2. **Start Celery worker (in separate terminal):**
   ```bash
   celery -A app.services.background_jobs.celery_app worker --loglevel=info
   ```

3. **Start Celery flower (optional, for monitoring):**
   ```bash
   celery -A app.services.background_jobs.celery_app flower
   ```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## API Endpoints

### Core Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /api/auth/login` - User authentication
- `GET /api/auth/me` - Current user info

### Nautobot Integration

- `GET /api/nautobot/devices` - List devices
- `GET /api/nautobot/devices/{device_id}` - Get device details
- `POST /api/nautobot/devices/onboard` - Onboard new device
- `POST /api/nautobot/check-ip` - Check IP availability
- `GET /api/nautobot/locations` - List locations
- `GET /api/nautobot/stats` - Nautobot statistics
- `GET /api/nautobot/test` - Test connection

### CheckMK Integration

- `GET /api/checkmk/hosts` - List hosts
- `POST /api/checkmk/hosts` - Create host
- `GET /api/checkmk/hosts/{hostname}` - Get host details
- `PUT /api/checkmk/hosts/{hostname}` - Update host
- `DELETE /api/checkmk/hosts/{hostname}` - Delete host
- `GET /api/checkmk/monitoring/hosts` - Get monitoring status
- `POST /api/checkmk/changes/activate` - Activate changes
- `GET /api/checkmk/stats` - CheckMK statistics
- `GET /api/checkmk/test` - Test connection

### Background Jobs

- `POST /api/jobs/submit` - Submit generic job
- `GET /api/jobs/{job_id}/status` - Get job status
- `POST /api/jobs/{job_id}/cancel` - Cancel job
- `POST /api/jobs/sync/nautobot-devices` - Sync devices from Nautobot
- `POST /api/jobs/sync/checkmk-hosts` - Sync hosts from CheckMK
- `POST /api/jobs/bulk/host-operations` - Bulk host operations
- `POST /api/jobs/cache/warm-up` - Warm up caches

### Settings Management

- `GET /api/settings/` - List all settings
- `POST /api/settings/` - Create/update setting
- `GET /api/settings/nautobot/current` - Get Nautobot settings
- `POST /api/settings/nautobot/test` - Test Nautobot connection
- `GET /api/settings/checkmk/current` - Get CheckMK settings
- `POST /api/settings/checkmk/test` - Test CheckMK connection
- `POST /api/settings/cache/clear` - Clear cache

## Authentication

The API uses JWT (JSON Web Tokens) for authentication:

1. **Login** with username/password to get a token
2. **Include token** in Authorization header: `Bearer <token>`
3. **Admin routes** require admin privileges

## Caching

The application uses Redis for caching:

- **Device lists** - Cached for 10 minutes
- **Statistics** - Cached for 5 minutes
- **Configuration data** - Cached for 30 minutes

Cache keys follow the pattern: `service:endpoint:params`

## Background Jobs

Long-running tasks are handled by Celery:

- **Device synchronization** from Nautobot/CheckMK
- **Bulk operations** on hosts
- **Cache warm-up** tasks
- **Data imports/exports**

Job status can be monitored via the jobs API.

## Error Handling

The API provides consistent error responses:

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

## Security Features

- **JWT Authentication** with configurable expiration
- **Role-based Access Control** (admin/user)
- **Input Validation** using Pydantic models
- **SQL Injection Protection** via SQLAlchemy ORM
- **CORS Configuration** for frontend integration

## Performance Features

- **Redis Caching** for frequently accessed data
- **Async/Await** for non-blocking operations
- **Connection Pooling** for external APIs
- **Background Jobs** for long-running tasks
- **Pagination** for large datasets

## Monitoring

- **Health Check** endpoint for uptime monitoring
- **Structured Logging** with configurable levels
- **Job Monitoring** via Celery Flower
- **Cache Statistics** via Redis monitoring

## Testing

```bash
# Run tests (if test suite is available)
pytest

# Test specific endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/nautobot/test
curl http://localhost:8000/api/checkmk/test
```

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   - Ensure Redis is running on localhost:6379
   - Check `REDIS_URL` in `.env`

2. **Nautobot/CheckMK Connection Failed**
   - Verify URLs and credentials in `.env`
   - Check network connectivity
   - Validate SSL certificates

3. **Database Errors**
   - Check `DATABASE_URL` configuration
   - Ensure database file permissions (SQLite)

4. **Import Errors**
   - Verify all dependencies are installed
   - Check Python path configuration

### Debug Mode

Set log level to DEBUG in the startup script:

```python
uvicorn.run("app.main:app", log_level="debug")
```

## Development

### Adding New Endpoints

1. Create route in appropriate `api/` module
2. Add business logic to `services/` module
3. Define data models in `models/` module
4. Update main.py to include router

### Adding New Background Tasks

1. Define task in `services/background_jobs.py`
2. Add task endpoint in `api/jobs.py`
3. Update task documentation

## Production Deployment

### Environment Variables

Set production values for:
- `SECRET_KEY` - Use a strong random key
- `DATABASE_URL` - PostgreSQL recommended
- `REDIS_URL` - Production Redis instance
- Service URLs and credentials

### Scaling

- Use multiple uvicorn workers
- Deploy Celery workers on separate machines
- Use Redis Cluster for high availability
- Implement load balancing

### Security

- Use HTTPS in production
- Implement rate limiting
- Monitor for security issues
- Regular dependency updates

## License

[Your License Here]