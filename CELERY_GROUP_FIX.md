# Celery Group Fix: Never Call `.get()` Within a Task

## Problem

The original implementation had a critical Celery anti-pattern that caused the worker to crash:

```python
# ❌ WRONG - Never do this!
def discover_topology_task(...):
    # Create group of parallel tasks
    job = group(discover_single_device_task.s(...) for device_id in device_ids)
    result = job.apply_async()
    
    # This blocks and causes RuntimeError!
    device_results = result.get()  # ❌ DEADLOCK
```

### Error Message
```
RuntimeError: Never call result.get() within a task!
See https://docs.celeryq.dev/en/latest/userguide/tasks.html#avoid-launching-synchronous-subtasks
```

### Why This Fails

Calling `.get()` inside a Celery task causes a **deadlock**:
1. The orchestrator task blocks waiting for subtasks
2. The subtasks are in the same worker pool
3. All workers are busy waiting
4. Nobody can execute the subtasks
5. 💥 Everything hangs or crashes

## Solution

Instead of blocking inside the task, the orchestrator now:
1. ✅ Dispatches the group of tasks
2. ✅ Returns immediately with group metadata
3. ✅ Lets the API endpoint track progress asynchronously

### Fixed Implementation

#### 1. Orchestrator Task (Non-Blocking)

```python
# ✅ CORRECT - Return immediately
@celery_app.task(bind=True, name='discover_topology')
def discover_topology_task(self, device_ids, ...):
    # Create group of parallel tasks
    job = group(
        discover_single_device_task.s(device_id, parent_job_id=self.request.id, ...)
        for device_id in device_ids
    )
    
    # Dispatch tasks - DO NOT call .get()!
    result = job.apply_async()
    
    # Return immediately with group info
    return {
        'status': 'in_progress',
        'job_id': self.request.id,
        'group_id': result.id,  # ← Store group ID for tracking
        'total_devices': len(device_ids),
        'device_ids': device_ids,
        'started_at': datetime.now().isoformat()
    }
```

#### 2. Progress Endpoint (Tracks Group)

```python
# ✅ Query group status from outside the task
@router.get("/discover/progress/{job_id}")
async def get_discovery_progress(job_id: str, ...):
    # Get orchestrator result
    result = background_job_service.get_job_status(job_id)
    meta = result.get('info', {}) or result.get('result', {})
    
    # Extract group_id from orchestrator metadata
    group_id = meta.get('group_id')
    device_ids = meta.get('device_ids', [])
    
    if group_id and device_ids:
        # Query individual child task statuses
        from celery.result import GroupResult
        group_result = GroupResult.restore(group_id, app=current_app)
        
        devices_progress = []
        completed = 0
        failed = 0
        
        for idx, child_result in enumerate(group_result.results):
            device_id = device_ids[idx]
            child_status = child_result.status
            child_meta = child_result.info if child_result.info else {}
            
            if child_status == 'SUCCESS':
                completed += 1
                device_progress = 100
            elif child_status == 'FAILURE':
                failed += 1
                device_progress = 0
            else:
                device_progress = child_meta.get('progress_percentage', 0)
            
            devices_progress.append({
                'device_id': device_id,
                'status': child_status,
                'progress_percentage': device_progress,
                'current_step': child_meta.get('current_step'),
                'error': child_meta.get('error')
            })
        
        # Calculate overall progress
        overall_progress = int((completed + failed) * 100 / len(device_ids))
        
        return {
            'job_id': job_id,
            'status': 'in_progress' if completed + failed < len(device_ids) else 'completed',
            'total_devices': len(device_ids),
            'completed_devices': completed,
            'failed_devices': failed,
            'progress_percentage': overall_progress,
            'devices': devices_progress,
            ...
        }
```

## Architecture Change

### Before (Blocking) ❌
```
API → Celery Task → group.apply_async()
                  ↓
                [BLOCKING .get()]  ← Deadlock!
                  ↓
                Wait for all subtasks
                  ↓
                Return aggregated results
```

### After (Non-Blocking) ✅
```
API → Celery Task → group.apply_async()
                  ↓
                Return immediately (group_id)
                
API → Progress Endpoint → GroupResult.restore(group_id)
                        ↓
                        Query individual child tasks
                        ↓
                        Aggregate & return progress
```

## Key Changes

### File: `backend/app/tasks/topology_tasks.py`

**Removed:**
```python
# Old blocking code
device_results = result.get()  # ❌

# Aggregate results
devices_data = {}
errors = {}
for device_result in device_results:
    # ... aggregation logic
```

**Added:**
```python
# New non-blocking code
return {
    'status': 'in_progress',
    'job_id': self.request.id,
    'group_id': result.id,  # ✅ Pass group ID
    'total_devices': total_devices,
    'device_ids': device_ids,
    'started_at': start_time.isoformat()
}
```

### File: `backend/app/api/topology.py`

**Enhanced Progress Tracking:**
```python
# Extract group_id from orchestrator result
group_id = meta.get('group_id')
device_ids = meta.get('device_ids', [])

if group_id and device_ids:
    # Restore group and query child tasks
    group_result = GroupResult.restore(group_id, app=current_app)
    
    # Track each device individually
    for idx, child_result in enumerate(group_result.results):
        # ... per-device progress tracking
```

## Benefits of This Approach

✅ **No Deadlock** - Tasks don't block waiting for subtasks  
✅ **True Parallelism** - All device tasks run concurrently  
✅ **Real-time Progress** - API can query status anytime  
✅ **Scalable** - Works with any number of devices  
✅ **Resilient** - Individual task failures don't block others  
✅ **Cancellable** - Can revoke group or individual tasks  

## Testing the Fix

### 1. Start Services
```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Backend
cd backend && python start.py

# Terminal 3: Celery Worker
cd backend && python start_worker.py

# Terminal 4: Frontend
cd frontend && npm run dev
```

### 2. Test Discovery
1. Navigate to Topology → Discover
2. Select multiple devices (3+)
3. Choose "Asynchronous (Background via Celery)"
4. Click "Start Discovery"

### 3. Expected Behavior
- ✅ Job starts immediately
- ✅ Returns job_id instantly
- ✅ Progress updates every 2 seconds
- ✅ Shows per-device progress
- ✅ No deadlock errors in worker logs
- ✅ Devices complete in parallel

### 4. Worker Logs Should Show
```
[INFO/MainProcess] 📦 Creating group of 3 parallel tasks
[INFO/MainProcess] 🔄 Executing parallel tasks...
[INFO/MainProcess] ✅ Group dispatched with result ID: abc123...
[INFO/ForkPoolWorker-1] 🚀 Starting discovery for device device-1
[INFO/ForkPoolWorker-2] 🚀 Starting discovery for device device-2
[INFO/ForkPoolWorker-3] 🚀 Starting discovery for device device-3
```

No more `RuntimeError` or crash!

## Celery Best Practices Applied

1. ✅ **Never call `.get()` in a task** - Use chords or callbacks instead
2. ✅ **Return quickly from tasks** - Don't block on I/O or subtasks
3. ✅ **Use groups for parallel work** - Let Celery manage concurrency
4. ✅ **Track progress via state** - Use `update_state()` and query from outside
5. ✅ **Store metadata in results** - Pass data via return values, not globals

## Related Documentation

- [Celery: Avoid Launching Synchronous Subtasks](https://docs.celeryq.dev/en/latest/userguide/tasks.html#avoid-launching-synchronous-subtasks)
- [Celery Groups](https://docs.celeryq.dev/en/stable/userguide/canvas.html#groups)
- [GroupResult API](https://docs.celeryq.dev/en/stable/reference/celery.result.html#celery.result.GroupResult)

## Status

✅ **Fixed** - Orchestrator no longer blocks on `.get()`  
✅ **Tested** - Worker starts without errors  
✅ **Documented** - This guide + code comments  

---

**Date:** October 5, 2025  
**Issue:** RuntimeError on `.get()` in Celery task  
**Fix:** Non-blocking orchestrator + group progress tracking
