# Frontend Update: Celery-Based Topology Discovery

## Overview

The Topology Discovery Modal has been updated to use the new Celery-based async discovery endpoints implemented in the backend.

## Changes Made

### File: `frontend/src/components/TopologyDiscoveryModal.vue`

#### 1. **Updated Execution Mode UI**

**Before:**
- "Foreground (Blocking)"
- "Background (Non-blocking)"

**After:**
- "Synchronous (Blocking)" - Uses `/api/topology/discover-sync`
- "Asynchronous (Background via Celery)" - Uses `/api/topology/discover-async`

#### 2. **New Celery Info Box**

Added an information box that appears when background mode is selected:
```
✨ Celery Worker Required
This mode requires a Celery worker to be running. Jobs are processed 
in parallel with real-time progress updates. You can cancel running 
jobs at any time.
```

#### 3. **Updated API Endpoints**

**Old Implementation:**
```javascript
// Single endpoint with flag
const response = await makeAuthenticatedRequest('/api/topology/discover', {
  method: 'POST',
  body: JSON.stringify({
    ...options,
    run_in_background: runInBackground.value  // ❌ Flag-based
  })
})
```

**New Implementation:**
```javascript
// Separate endpoints for clarity
const endpoint = runInBackground.value 
  ? '/api/topology/discover-async'  // ✅ Celery-based
  : '/api/topology/discover-sync'   // ✅ Synchronous

const response = await makeAuthenticatedRequest(endpoint, {
  method: 'POST',
  body: JSON.stringify({
    ...options
    // No run_in_background flag needed
  })
})
```

#### 4. **Enhanced Progress Tracking**

**Before:**
- Used deprecated in-memory job storage
- Polled every 1 second
- Called separate `/result` endpoint

**After:**
- Uses Celery state from Redis
- Polls every 2 seconds (more efficient)
- Gets results directly from progress endpoint

```javascript
const checkProgress = async () => {
  // Query Celery state
  const response = await makeAuthenticatedRequest(
    `/api/topology/discover/progress/${jobId.value}`
  )
  
  progress.value = await response.json()
  
  // Status comes from Celery: pending, in_progress, completed, failed, cancelled
  if (progress.value.status === 'completed' || progress.value.status === 'failed') {
    // Discovery complete
    discovering.value = false
  }
}
```

#### 5. **Job Cancellation Feature** ⭐ NEW

Added ability to cancel running background jobs:

**UI:**
- "Cancel Job" button appears during background discovery
- Red button with X icon
- Only shown for async/background jobs

**Functionality:**
```javascript
const cancelDiscovery = async () => {
  const response = await makeAuthenticatedRequest(
    `/api/topology/discover/${jobId.value}`, 
    { method: 'DELETE' }
  )
  
  if (response.ok) {
    // Stop polling and show cancellation message
    discovering.value = false
    discoveryResult.value = { status: 'cancelled', ... }
  }
}
```

#### 6. **Improved Error Handling**

- Better error messages
- Graceful handling of network issues
- Non-critical errors don't stop progress polling
- Clear distinction between job errors and network errors

## User Experience Changes

### Before

1. User selects "Background (Non-blocking)"
2. Discovery starts with `asyncio.create_task` (not real background)
3. Progress tracked in memory (lost on server restart)
4. No way to cancel
5. Unclear what "background" meant

### After

1. User selects "Asynchronous (Background via Celery)"
2. Info box explains Celery worker requirement
3. Discovery starts in Celery worker (true background)
4. Progress tracked in Redis (persists across restarts)
5. **Can cancel with "Cancel Job" button**
6. Clear understanding of execution mode

## API Endpoints Used

### Synchronous Mode
- `POST /api/topology/discover-sync` - Blocks until complete

### Asynchronous Mode (Celery)
- `POST /api/topology/discover-async` - Returns job_id immediately
- `GET /api/topology/discover/progress/{job_id}` - Real-time progress
- `DELETE /api/topology/discover/{job_id}` - Cancel running job

## Visual Changes

### Execution Mode Selection

```
┌─────────────────────────────────────────────────────┐
│ ○ Synchronous (Blocking)                           │
│   Best for small number of devices (1-3).          │
│   Waits for completion.                            │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ ● Asynchronous (Background via Celery)             │
│   ✨ Recommended for all workloads.                │
│   Runs in Celery worker with real-time progress.   │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ ℹ️  Celery Worker Required                         │
│                                                     │
│ This mode requires a Celery worker to be running.  │
│ Jobs are processed in parallel with real-time      │
│ progress updates. You can cancel running jobs at   │
│ any time.                                          │
└─────────────────────────────────────────────────────┘
```

### Discovery In Progress (Background Mode)

```
┌─────────────────────────────────────────────────────┐
│ Overall Progress                              45%  │
│ ████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░        │
│ 3 of 5 devices completed (1 failed)               │
│                                                     │
│ ✓ router-01        100%                           │
│ ✓ router-02        100%                           │
│ ⟳ router-03         45%  Discovering BGP routes   │
│ ○ router-04          0%                           │
│ ✗ router-05          0%  Connection timeout       │
│                                                     │
│ [Cancel]                          [❌ Cancel Job]  │
└─────────────────────────────────────────────────────┘
```

## Benefits

✅ **True Background Execution** - Jobs run in Celery workers  
✅ **Parallel Processing** - Multiple devices at once  
✅ **Real-time Progress** - Live updates from Celery state  
✅ **Cancellation Support** - Stop jobs mid-execution  
✅ **Persistent State** - Survives server restarts (Redis)  
✅ **Better UX** - Clear explanation of execution modes  
✅ **Clearer API** - Separate endpoints vs flag  

## Testing

### Prerequisites
1. Redis running: `redis-cli ping`
2. Celery worker: `cd backend && python start_worker.py`
3. FastAPI backend: `python start.py`
4. Frontend dev server: `cd frontend && npm run dev`

### Test Steps

**1. Test Synchronous Discovery**
- Select 1-2 devices
- Choose "Synchronous (Blocking)"
- Click "Start Discovery"
- Should block until complete
- Progress shown in modal

**2. Test Async Discovery**
- Select 3+ devices
- Choose "Asynchronous (Background via Celery)"
- Verify info box appears
- Click "Start Discovery"
- Should return immediately with job_id
- Progress updates every 2 seconds
- Verify "Cancel Job" button appears

**3. Test Job Cancellation**
- Start async discovery with 5+ devices
- Click "Cancel Job" button mid-execution
- Verify job stops
- Verify cancellation message shows

**4. Test Error Handling**
- Try with invalid device (unreachable)
- Verify partial success/failure handling
- Check error messages display correctly

## Migration Notes

### Backward Compatibility

The old `/api/topology/discover` endpoint still exists but is marked as **deprecated**. The frontend no longer uses it, but it remains functional for other clients.

### Breaking Changes

None - this is purely frontend UI/UX enhancement using the new backend endpoints.

### Rollback Plan

If issues arise:
1. Revert `TopologyDiscoveryModal.vue` to use old endpoint
2. Change endpoint back to `/api/topology/discover`
3. Add back `run_in_background` flag

## Future Enhancements

- [ ] Add estimated time remaining
- [ ] Show detailed per-device logs
- [ ] Add retry failed devices option
- [ ] Save discovery templates
- [ ] Schedule recurring discoveries
- [ ] Export discovery results
- [ ] Add discovery history view

---

**Status:** ✅ Complete  
**Date:** October 5, 2025  
**Version:** Frontend v2.0 (Celery Integration)
