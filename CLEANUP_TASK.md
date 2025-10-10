# Cleanup Task Documentation

## Overview

The `cleanup_old_data` task is an automated maintenance task designed to clean up stale and expired data from the NOC Canvas system. This helps maintain database performance and prevents unnecessary storage usage.

## Task Details

- **Task Name**: `cleanup_old_data`
- **Task Path**: `app.services.background_jobs.cleanup_old_data`
- **Default Schedule**: Not scheduled by default (manual or configure as needed)

## What Gets Cleaned Up

The cleanup task performs the following operations:

### 1. **Expired Scheduled Tasks**
- Removes periodic tasks that have passed their expiration date
- Only affects tasks with an `expires` field set
- Example: One-time scheduled tasks that have completed

### 2. **Completed One-Off Tasks**
- Removes one-off tasks that have already executed and are disabled
- Only deletes tasks older than the retention period (default: 7 days)
- Preserves recent task history for auditing

### 3. **Celery Task Results**
- Delegates to Celery's built-in `celery.backend_cleanup` task
- Cleans up old task result metadata from Redis/backend

## Configuration

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days_to_keep` | int | 7 | Number of days to retain historical data |

### Example Usage

#### Via Scheduler UI
1. Navigate to **Scheduled Jobs**
2. Click **Create Schedule**
3. Select task: `cleanup_old_data`
4. Configure schedule (e.g., daily at 4 AM)
5. Optional: Set `days_to_keep` in kwargs (e.g., `{"days_to_keep": 14}`)

#### Via API

```bash
# Create a scheduled cleanup task (daily at 4 AM)
curl -X POST http://localhost:8000/api/scheduler/tasks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "daily_cleanup",
    "task": "app.services.background_jobs.cleanup_old_data",
    "description": "Daily cleanup of old data",
    "schedule_type": "crontab",
    "crontab": {
      "minute": "0",
      "hour": "4",
      "day_of_week": "*",
      "day_of_month": "*",
      "month_of_year": "*"
    },
    "kwargs": {
      "days_to_keep": 7
    },
    "enabled": true
  }'
```

#### Manual Execution

```python
from app.services.background_jobs import celery_app

# Run cleanup with default settings (7 days)
result = celery_app.send_task('app.services.background_jobs.cleanup_old_data')

# Run cleanup with custom retention period
result = celery_app.send_task(
    'app.services.background_jobs.cleanup_old_data',
    kwargs={'days_to_keep': 14}
)
```

## Task Execution Flow

1. **Initialization**: Task starts and logs cleanup parameters
2. **Progress Updates**: Task reports progress through 4 main steps
3. **Celery Results Cleanup**: Delegates to built-in cleanup mechanism
4. **Expired Tasks Removal**: Queries and deletes expired scheduled tasks
5. **One-Off Tasks Removal**: Removes completed one-off tasks older than retention period
6. **Completion**: Returns statistics about deleted items

## Return Value

The task returns a dictionary with cleanup statistics:

```json
{
  "status": "SUCCESS",
  "message": "Cleanup completed successfully. Deleted 15 items.",
  "stats": {
    "celery_results_deleted": 0,
    "expired_tasks_deleted": 8,
    "one_off_tasks_deleted": 7,
    "errors": []
  },
  "cutoff_date": "2025-10-03T12:00:00",
  "days_kept": 7
}
```

## Recommended Schedule

For typical installations:

- **Frequency**: Daily
- **Time**: 4:00 AM (low-traffic period)
- **Retention**: 7-14 days

### Crontab Configuration
```
0 4 * * *  # Every day at 4:00 AM
```

### Interval Configuration
```
every: 1
period: days
```

## Safety Features

1. **Non-Destructive**: Only removes explicitly expired or old completed tasks
2. **Rollback on Error**: Database operations are wrapped in transactions
3. **Error Logging**: All errors are logged and included in results
4. **Configurable Retention**: Retention period can be adjusted per execution
5. **Progress Tracking**: Real-time progress updates during execution

## Monitoring

### Via Logs

```bash
# Check cleanup task logs
grep "cleanup_old_data" backend/logs/celery.log
```

### Via Job Status API

```bash
# Get task status
curl -X GET http://localhost:8000/api/jobs/{task_id}/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Troubleshooting

### Task Not Running

1. Check if Celery Beat is running: `ps aux | grep celery`
2. Verify task is enabled in scheduler
3. Check Celery worker logs for errors

### Incomplete Cleanup

- Review the `errors` array in task results
- Check database permissions
- Verify Celery backend configuration

### Performance Issues

- Reduce `days_to_keep` value
- Run cleanup more frequently
- Monitor database query performance

## Related Tasks

- `celery.backend_cleanup`: Built-in Celery cleanup task
- This task complements (not replaces) the built-in Celery cleanup

## Best Practices

1. **Run During Off-Peak Hours**: Schedule for low-traffic periods
2. **Monitor First Runs**: Watch logs on initial executions
3. **Adjust Retention**: Balance between history and performance
4. **Regular Execution**: Daily or weekly depending on load
5. **Keep Logs**: Maintain cleanup task logs for troubleshooting

## Future Enhancements

Potential additions to the cleanup task:

- Clean up old canvas snapshots/versions
- Archive deleted shapes and canvases
- Compress old logs
- Clean up orphaned cache entries
- Database vacuum/optimization after cleanup
