# Celery Worker and Beat Quick Start

This directory contains helper scripts to easily start Celery Worker and Beat scheduler.

## Quick Start

### 1. Start Celery Worker (processes background tasks)

```bash
python start_worker.py
```

### 2. Start Celery Beat (schedules periodic tasks)

```bash
python start_beat.py
```

## What These Scripts Do

### `start_worker.py`

The worker script:
- ✅ Checks if Celery is installed
- ✅ Verifies Redis is running and accessible
- ✅ Lists all registered tasks
- ✅ Starts the Celery worker to process tasks

### `start_beat.py`

The beat script:
- ✅ Checks if Celery and celery-sqlalchemy-scheduler are installed
- ✅ Verifies Redis is running and accessible
- ✅ Verifies PostgreSQL database is accessible
- ✅ Starts Celery Beat with database scheduler
- ✅ Creates necessary database tables automatically

## Prerequisites

1. **Redis must be running**:
   ```bash
   # macOS
   brew services start redis

   # Linux
   sudo systemctl start redis
   ```

2. **PostgreSQL must be running** with database configured

3. **Dependencies installed**:
   ```bash
   pip install -r requirements.txt
   ```

## Custom Options

You can pass Celery options to the scripts:

### Worker with debug logging
```bash
python start_worker.py --loglevel=debug
```

### Worker with specific concurrency
```bash
python start_worker.py --concurrency=4
```

### Beat with debug logging
```bash
python start_beat.py --loglevel=debug
```

## Alternative: Direct Celery Commands

If you prefer to use Celery commands directly:

### Start Worker
```bash
celery -A app.services.background_jobs worker -l info
```

### Start Beat
```bash
celery -A app.services.background_jobs beat -l info --scheduler celery_sqlalchemy_scheduler.schedulers:DatabaseScheduler
```

## Monitoring

- **Worker Status**: Check Settings → Jobs in the web interface
- **Scheduled Tasks**: Check Settings → Scheduler in the web interface
- **Logs**: Both scripts output detailed logs to the console

## Troubleshooting

### "Cannot connect to Redis"
- Make sure Redis is running: `redis-cli ping` should return `PONG`
- Check Redis URL in your environment/config

### "Cannot connect to database"
- Verify PostgreSQL is running
- Check database configuration in your `.env` or YAML config

### "Celery is not available"
- Install Celery: `pip install celery celery-sqlalchemy-scheduler redis`

## Production Deployment

For production, use a process manager like:
- **systemd** (Linux)
- **supervisor** (Linux)
- **launchd** (macOS)

See [SCHEDULER_SETUP.md](../SCHEDULER_SETUP.md) for production deployment examples.
