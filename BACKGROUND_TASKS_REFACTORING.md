# Background Tasks Refactoring

## Overview
The background tasks have been refactored from a monolithic `background_jobs.py` file into a modular structure with separate files for each task type. This improves code maintainability, organization, and makes it easier to locate and test individual tasks.

## Changes Made

### New Task Module Structure

All background tasks are now organized in the `./backend/app/tasks/` directory:

```
backend/app/tasks/
├── __init__.py              # Package initialization
├── nautobot_tasks.py        # Nautobot device synchronization tasks
├── checkmk_tasks.py         # CheckMK host management and bulk operations
├── cache_tasks.py           # Cache warming tasks
├── cleanup_tasks.py         # Data cleanup and maintenance tasks
├── test_tasks.py            # Testing and verification tasks
└── topology_tasks.py        # Network topology discovery tasks (pre-existing)
```

### Task Registration Pattern

Each task module follows a consistent `register_tasks()` pattern:

```python
def register_tasks(celery_app):
    """Register tasks with the Celery app."""
    
    @celery_app.task(bind=True, name='app.tasks.module_name.task_name')
    def task_function(self, ...):
        # Task implementation
        pass
    
    return {
        'task_name': task_function,
    }
```

### Updated Task Names

Task paths have been updated from `app.services.background_jobs.*` to `app.tasks.*`:

| Old Task Path | New Task Path |
|--------------|---------------|
| `app.services.background_jobs.sync_nautobot_devices` | `app.tasks.nautobot_tasks.sync_nautobot_devices` |
| `app.services.background_jobs.sync_checkmk_hosts` | `app.tasks.checkmk_tasks.sync_checkmk_hosts` |
| `app.services.background_jobs.bulk_host_operations` | `app.tasks.checkmk_tasks.bulk_host_operations` |
| `app.services.background_jobs.cache_warm_up` | `app.tasks.cache_tasks.cache_warm_up` |
| `app.services.background_jobs.cleanup_old_data` | `app.tasks.cleanup_tasks.cleanup_old_data` |
| `app.services.background_jobs.test_background_task` | `app.tasks.test_tasks.test_background_task` |

### Updated Files

1. **`backend/app/services/background_jobs.py`**
   - Removed inline task definitions (~500 lines)
   - Added imports from task modules
   - Calls `register_tasks()` for each module
   - Updated Celery `include` configuration
   - Now serves as an orchestrator rather than containing task logic

2. **`backend/app/api/scheduler.py`**
   - Updated task paths in `get_available_tasks()` endpoint
   - Updated example in Pydantic model docstring

3. **`backend/app/api/settings.py`**
   - Updated `submit_test_job()` to use new task path
   - Updated comment examples

## Task Modules

### 1. nautobot_tasks.py
**Purpose:** Nautobot device synchronization

**Tasks:**
- `sync_nautobot_devices`: Sync devices from Nautobot with filters support

### 2. checkmk_tasks.py
**Purpose:** CheckMK host management and bulk operations

**Tasks:**
- `sync_checkmk_hosts`: Sync hosts from CheckMK
- `bulk_host_operations`: Perform bulk create/update/delete operations on hosts

### 3. cache_tasks.py
**Purpose:** Cache warming for improved performance

**Tasks:**
- `cache_warm_up`: Pre-load commonly accessed data into cache

### 4. cleanup_tasks.py
**Purpose:** Database maintenance and cleanup

**Tasks:**
- `cleanup_old_data`: Comprehensive 4-stage cleanup:
  1. Expired periodic tasks
  2. Old task execution records (>30 days)
  3. Old Celery results (>7 days)
  4. Orphaned task changes

### 5. test_tasks.py
**Purpose:** Testing and verification

**Tasks:**
- `test_background_task`: Test task for verifying Celery worker functionality

### 6. topology_tasks.py
**Purpose:** Network topology discovery (pre-existing)

**Tasks:**
- `discover_topology_task`: Discover network topology from seed devices
- `discover_single_device_task`: Discover topology for a single device

## Benefits

1. **Better Organization**: Each task type has its own dedicated file
2. **Easier Navigation**: Developers can quickly find specific tasks
3. **Improved Maintainability**: Changes to one task type don't affect others
4. **Clearer Dependencies**: Import statements show what each task requires
5. **Independent Testing**: Each module can be tested in isolation
6. **Consistent Pattern**: All modules follow the same `register_tasks()` pattern
7. **Scalability**: Easy to add new task types by creating new module files

## Migration Guide

If you have any scheduled tasks in the database using the old task paths, they will continue to work because the task names in the `@celery_app.task()` decorator specify the full path. However, you may want to update them:

1. Go to the Scheduler tab in the application
2. For each task, click Edit
3. Update the task path from `app.services.background_jobs.*` to `app.tasks.*`
4. Click Save

Alternatively, tasks will automatically use the new paths when created through the UI after this update.

## Testing

To verify the refactoring:

1. **Start Celery Worker:**
   ```bash
   cd backend
   python start_worker.py
   ```

2. **Start Celery Beat:**
   ```bash
   cd backend
   python start_beat.py
   ```

3. **Test Task Submission:**
   - Navigate to Settings → Jobs tab
   - Click "Test Background Job"
   - Verify the task runs successfully

4. **Test Scheduled Tasks:**
   - Navigate to the Scheduler tab
   - Create a new scheduled task
   - Verify it uses the new task paths
   - Verify it executes correctly

## Notes

- All task functionality remains unchanged - only the organization has been improved
- The `BackgroundJobService` class in `background_jobs.py` still handles job submission and status checking
- Celery configuration remains in `background_jobs.py`
- Task names registered with Celery use the full module path (e.g., `app.tasks.nautobot_tasks.sync_nautobot_devices`)
