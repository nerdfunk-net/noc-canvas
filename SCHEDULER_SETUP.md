# NOC Canvas Dynamic Scheduler Setup

## Overview

The NOC Canvas application now includes a fully dynamic scheduler system that allows users to create, manage, and schedule periodic tasks (cron jobs) through the web interface. This system is built on:

- **Celery Beat**: Periodic task scheduler
- **celery-sqlalchemy-scheduler**: Database-backed scheduler for dynamic task management
- **PostgreSQL**: Stores schedule configurations

## Features

✅ **Fully Dynamic Scheduling** - Create and modify schedules without restarting services
✅ **Two Schedule Types**:
  - **Interval-based**: Run tasks every X seconds/minutes/hours/days
  - **Cron-based**: Use cron expressions for complex schedules
✅ **Web UI Management** - Full CRUD interface in Settings → Scheduler
✅ **Enable/Disable** - Toggle schedules on/off without deleting
✅ **One-off Tasks** - Run tasks once at a scheduled time
✅ **Expiry Dates** - Automatically disable tasks after a certain date
✅ **Available Tasks**:
  - Sync Nautobot Devices
  - Sync CheckMK Hosts
  - Cache Warm-up
  - Network Topology Discovery
  - Test Background Jobs

## Prerequisites

1. **Celery Worker running** - For executing background tasks
2. **Celery Beat running** - For scheduling periodic tasks
3. **Redis running** - Message broker
4. **PostgreSQL running** - Database for storing schedules

## Setup Instructions

### 1. Install Dependencies

The required packages are already in `requirements.txt`:

```bash
cd backend
pip install -r requirements.txt
```

This includes:
- `celery>=5.3.0`
- `celery-sqlalchemy-scheduler>=0.3.0`
- `redis>=4.5.0`

### 2. Start Required Services

#### A. Start Redis (if not already running)

```bash
# macOS with Homebrew
brew services start redis

# or manually
redis-server
```

#### B. Start Celery Worker

**Option 1: Using the helper script (Recommended)**

Open a new terminal and run:

```bash
cd backend
python start_worker.py
```

The script will:
- Check all dependencies
- Verify Redis connection
- List registered tasks
- Start the worker with optimal settings

**Option 2: Using celery command directly**

```bash
cd backend
celery -A app.services.background_jobs worker -l info
```

You should see output like:
```
celery@hostname ready.
```

#### C. Start Celery Beat Scheduler

**Option 1: Using the helper script (Recommended)**

Open another new terminal and run:

```bash
cd backend
python start_beat.py
```

The script will:
- Check all dependencies
- Verify Redis and database connections
- Start Celery Beat with database scheduler
- Show helpful status messages

**Option 2: Using celery command directly**

```bash
cd backend
celery -A app.services.background_jobs beat -l info --scheduler celery_sqlalchemy_scheduler.schedulers:DatabaseScheduler
```

You should see output like:
```
celery beat v5.3.x is starting.
DatabaseScheduler: Using scheduler database...
```

**Note**: Celery Beat will automatically create the necessary database tables on first run.

### 3. Start the Backend API

In another terminal:

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 4. Start the Frontend

In another terminal:

```bash
cd frontend
npm run dev
```

## Using the Scheduler

### Creating a Scheduled Job

1. Navigate to **Settings → Scheduler** in the web interface
2. Click **"Create Schedule"**
3. Fill in the form:
   - **Job Name**: Descriptive name (e.g., "Daily Nautobot Sync")
   - **Description**: Optional details
   - **Task**: Select from available tasks
   - **Schedule Type**:
     - **Interval**: Run every X seconds/minutes/hours/days
     - **Cron**: Use cron expression (minute hour day month day_of_week)
   - **Task Arguments**: JSON object with task-specific parameters
   - **Options**:
     - Enable immediately
     - Run only once (one-off)
     - Set expiry date
4. Click **"Create Schedule"**

### Example Schedules

#### 1. Sync Nautobot Devices Every Hour

```
Name: Hourly Nautobot Sync
Task: sync_nautobot_devices
Schedule Type: Interval
  Every: 1
  Period: hours
Arguments: {}
```

#### 2. Daily Cache Warm-up at 2 AM

```
Name: Daily Cache Warm-up
Task: cache_warm_up
Schedule Type: Cron
  Minute: 0
  Hour: 2
  Day: *
  Month: *
  Day of Week: *
Arguments: {}
```

#### 3. Weekly Topology Discovery (Every Monday at 3 AM)

```
Name: Weekly Topology Discovery
Task: discover_topology_task
Schedule Type: Cron
  Minute: 0
  Hour: 3
  Day: *
  Month: *
  Day of Week: 1
Arguments: {
  "seed_devices": [1, 2, 3],
  "max_depth": 3
}
```

### Cron Expression Quick Reference

| Expression | Meaning |
|------------|---------|
| `*` | Every (any value) |
| `*/5` | Every 5 units |
| `0-23` | Range (0 through 23) |
| `1,3,5` | Specific values |
| `0 0 * * *` | Daily at midnight |
| `0 */4 * * *` | Every 4 hours |
| `0 9 * * 1-5` | Weekdays at 9 AM |
| `0 0 1 * *` | First day of month |

### Managing Scheduled Jobs

- **Edit**: Click the edit (pencil) icon
- **Enable/Disable**: Click the play/pause icon
- **Delete**: Click the trash icon
- **View Status**: See last run time and total run count

## Database Schema

The `celery-sqlalchemy-scheduler` creates these tables:

- `celerybeat.celery_periodic_task` - Periodic task definitions
- `celerybeat.celery_interval_schedule` - Interval schedules
- `celerybeat.celery_crontab_schedule` - Cron schedules
- `celerybeat.celery_periodic_task_changed` - Change tracking

## Monitoring

### Check Celery Beat Status

In the Celery Beat terminal, you'll see:
```
Scheduler: Sending due task daily-sync (app.services.background_jobs.sync_nautobot_devices)
```

### Check Worker Status

In the Settings → Jobs tab, you can see:
- Active workers
- Queue size
- Running jobs
- Recent job results

## Troubleshooting

### Beat not picking up new schedules

**Solution**: Celery Beat checks the database every few seconds. If changes aren't appearing, check:

1. Celery Beat is running
2. Database connection is correct
3. Check Celery Beat logs for errors

### Tasks not executing

**Solution**: Check that:

1. Celery Worker is running
2. Redis is accessible
3. Task name in schedule matches actual task name
4. Schedule is enabled
5. Check worker logs for errors

### "Celery not available" error

**Solution**:
```bash
pip install celery celery-sqlalchemy-scheduler redis
```

### Database connection errors

**Solution**: Verify database URL in Celery config matches your PostgreSQL settings

## Production Deployment

### Using Supervisor (Linux)

Create `/etc/supervisor/conf.d/noc-canvas-celery.conf`:

```ini
[program:noc-canvas-worker]
command=/path/to/venv/bin/celery -A app.services.background_jobs worker -l info
directory=/path/to/noc-canvas/backend
user=www-data
autostart=true
autorestart=true
stdout_logfile=/var/log/noc-canvas/worker.log
stderr_logfile=/var/log/noc-canvas/worker.err.log

[program:noc-canvas-beat]
command=/path/to/venv/bin/celery -A app.services.background_jobs beat -l info --scheduler celery_sqlalchemy_scheduler.schedulers:DatabaseScheduler
directory=/path/to/noc-canvas/backend
user=www-data
autostart=true
autorestart=true
stdout_logfile=/var/log/noc-canvas/beat.log
stderr_logfile=/var/log/noc-canvas/beat.err.log
```

Then:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start noc-canvas-worker
sudo supervisorctl start noc-canvas-beat
```

### Using systemd (Linux)

Create `/etc/systemd/system/noc-canvas-worker.service`:

```ini
[Unit]
Description=NOC Canvas Celery Worker
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/noc-canvas/backend
ExecStart=/path/to/venv/bin/celery -A app.services.background_jobs worker -l info
Restart=always

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/noc-canvas-beat.service`:

```ini
[Unit]
Description=NOC Canvas Celery Beat
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/noc-canvas/backend
ExecStart=/path/to/venv/bin/celery -A app.services.background_jobs beat -l info --scheduler celery_sqlalchemy_scheduler.schedulers:DatabaseScheduler
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable noc-canvas-worker noc-canvas-beat
sudo systemctl start noc-canvas-worker noc-canvas-beat
```

## API Endpoints

For programmatic access:

- `GET /api/scheduler/tasks` - List all scheduled tasks
- `POST /api/scheduler/tasks` - Create new scheduled task
- `GET /api/scheduler/tasks/{id}` - Get specific task
- `PUT /api/scheduler/tasks/{id}` - Update task
- `DELETE /api/scheduler/tasks/{id}` - Delete task
- `GET /api/scheduler/available-tasks` - List available tasks

## Security Considerations

1. **Authentication Required**: All scheduler endpoints require authentication
2. **Admin Only**: Consider restricting scheduler access to admin users only
3. **Input Validation**: Task arguments are validated as JSON
4. **SQL Injection**: Uses SQLAlchemy ORM (protected)

## Additional Resources

- [Celery Documentation](https://docs.celeryproject.org/)
- [Celery Beat Documentation](https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html)
- [Crontab Guru](https://crontab.guru/) - Cron expression helper
