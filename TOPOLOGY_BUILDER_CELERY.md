# Celery-Based Topology Discovery Implementation Plan

**Created:** October 5, 2025  
**Status:** Planning Phase  
**Target:** Implement asynchronous topology discovery using Celery workers

---

## 📋 Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Recommended Architecture](#recommended-architecture)
3. [Implementation Plan](#implementation-plan)
4. [File Structure](#file-structure)
5. [Migration Steps](#migration-steps)
6. [Testing Strategy](#testing-strategy)
7. [Important Considerations](#important-considerations)

---

## Current State Analysis

### ✅ What We Have

- **Celery infrastructure** already set up in `background_jobs.py`
- **Redis configured** as broker/backend
- **Worker startup script** (`start_worker.py`)
- **Existing task patterns** (sync_nautobot_devices, etc.)
- In-memory job storage (`_discovery_jobs` dict) - **needs replacement**
- Async discovery service with API endpoint calls
- Topology API endpoint (`/topology/discover`) with placeholder background execution

### ⚠️ What Needs Work

- Replace in-memory job storage with Redis
- Convert async discovery methods to Celery tasks
- Handle async operations in Celery worker context
- Implement proper progress tracking via Celery state updates
- Fix database session management for worker context

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      ARCHITECTURE                           │
└─────────────────────────────────────────────────────────────┘

 FastAPI Endpoint                 Celery Worker
 ───────────────                 ──────────────
      │                                │
      ├── POST /topology/discover      │
      │   └─> Create Celery task ─────┼─> discover_topology_task
      │       (returns job_id)         │    ├─> Parallel device tasks
      │                                │    │   ├─> discover_single_device_task
      │                                │    │   ├─> discover_single_device_task
      │                                │    │   └─> discover_single_device_task
      │                                │    └─> Aggregate results
      │                                │
      ├── GET /topology/discover/      │
      │   progress/{job_id}            │
      │   └─> Query Celery state ─────┼─> AsyncResult(job_id)
      │       (via Redis)              │    └─> Returns progress
      │                                │
      └── DELETE /topology/discover/   │
          {job_id}                     │
          └─> Revoke task ─────────────┼─> celery.control.revoke()
                                       │

                    Redis
                    ─────
              ┌─────────────┐
              │ Job State   │
              │ Progress    │
              │ Results     │
              └─────────────┘
```

### Data Flow

```
User → FastAPI → Celery Task → Device API Calls → Cache Results
                     ↓
                  Redis (Job State)
                     ↓
User ← FastAPI ← Query Progress
```

---

## Implementation Plan

### Phase 1: Create Celery Tasks (New File)

**File:** `backend/app/tasks/topology_tasks.py` (new file)

**Why separate file?**
- Better organization (tasks vs services)
- Follows existing pattern (services contain business logic, tasks are Celery wrappers)
- Easier to test independently
- Clear separation of concerns

**Task Structure:**

```python
# Structure (not full implementation):

from celery import group, chord
from typing import List, Dict, Any
from app.services.background_jobs import celery_app
from app.services.topology_discovery_service import TopologyDiscoveryService
from app.core.database import SessionLocal
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def discover_topology_task(
    self,
    device_ids: List[str],
    include_static_routes: bool = True,
    include_ospf_routes: bool = True,
    include_bgp_routes: bool = True,
    include_mac_table: bool = True,
    include_cdp_neighbors: bool = True,
    cache_results: bool = True,
    auth_token: str = ""
):
    """
    Main orchestrator task - spawns sub-tasks for each device
    and aggregates results.
    
    This task:
    1. Initializes job state in Redis (via Celery)
    2. Creates a group of parallel device discovery tasks
    3. Monitors overall progress
    4. Aggregates results from all devices
    5. Updates final state
    
    Args:
        device_ids: List of device IDs to discover
        include_*: Flags for what data to collect
        cache_results: Whether to cache results to database
        auth_token: Authentication token for device API calls
        
    Returns:
        Dictionary with discovery results and statistics
    """
    total_devices = len(device_ids)
    
    # Initialize state
    self.update_state(
        state='PROGRESS',
        meta={
            'job_id': self.request.id,
            'status': 'in_progress',
            'total_devices': total_devices,
            'completed_devices': 0,
            'failed_devices': 0,
            'progress_percentage': 0,
            'devices': [
                {
                    'device_id': did,
                    'status': 'pending',
                    'progress_percentage': 0,
                    'current_task': None,
                    'error': None
                }
                for did in device_ids
            ],
            'started_at': datetime.now(timezone.utc).isoformat()
        }
    )
    
    # Options dict for sub-tasks
    options = {
        'include_static_routes': include_static_routes,
        'include_ospf_routes': include_ospf_routes,
        'include_bgp_routes': include_bgp_routes,
        'include_mac_table': include_mac_table,
        'include_cdp_neighbors': include_cdp_neighbors,
        'cache_results': cache_results
    }
    
    # Create parallel device discovery tasks
    job = group(
        discover_single_device_task.s(
            device_id=device_id,
            parent_job_id=self.request.id,
            options=options,
            auth_token=auth_token
        )
        for device_id in device_ids
    )
    
    # Execute and wait for results
    result = job.apply_async()
    device_results = result.get()  # Blocks until all complete
    
    # Aggregate results
    devices_data = {}
    errors = {}
    successful = 0
    failed = 0
    
    for device_result in device_results:
        device_id = device_result['device_id']
        if device_result['success']:
            devices_data[device_id] = device_result['data']
            successful += 1
        else:
            errors[device_id] = device_result['error']
            failed += 1
    
    # Final state update
    final_status = 'completed' if failed < total_devices else 'failed'
    
    return {
        'job_id': self.request.id,
        'status': final_status,
        'total_devices': total_devices,
        'successful_devices': successful,
        'failed_devices': failed,
        'devices_data': devices_data,
        'errors': errors,
        'completed_at': datetime.now(timezone.utc).isoformat()
    }


@celery_app.task(bind=True)
def discover_single_device_task(
    self,
    device_id: str,
    parent_job_id: str,
    options: Dict[str, Any],
    auth_token: str
):
    """
    Discover data for a single device.
    Can be called individually or as part of group.
    
    This task:
    1. Updates device progress in parent task state
    2. Calls device endpoints sequentially
    3. Caches results if requested
    4. Returns device data
    5. Handles errors gracefully
    
    Args:
        device_id: Device ID to discover
        parent_job_id: Parent task ID for progress updates
        options: Discovery options dict
        auth_token: Authentication token
        
    Returns:
        Dictionary with device data or error
    """
    logger.info(f"Starting discovery for device {device_id}")
    
    # Update device state
    self.update_state(
        state='PROGRESS',
        meta={
            'device_id': device_id,
            'status': 'in_progress',
            'progress': 0,
            'current_task': 'Initializing'
        }
    )
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Call synchronous discovery service
        device_data = TopologyDiscoveryService.discover_device_data_sync(
            db=db,
            device_id=device_id,
            task=self,  # Pass task for progress updates
            **options,
            auth_token=auth_token
        )
        
        db.commit()
        
        return {
            'device_id': device_id,
            'success': True,
            'data': device_data,
            'error': None
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Discovery failed for device {device_id}: {e}")
        
        return {
            'device_id': device_id,
            'success': False,
            'data': None,
            'error': str(e)
        }
        
    finally:
        db.close()
```

---

### Phase 2: Modify Discovery Service

**File:** `backend/app/services/topology_discovery_service.py`

**Changes needed:**

#### 1. Remove in-memory storage
```python
# DELETE THIS:
_discovery_jobs: Dict[str, Dict[str, Any]] = {}

# All state should go to Redis via Celery
```

#### 2. Convert async methods to sync

```python
# Current (async):
@staticmethod
async def _call_device_endpoint(device_id: str, endpoint: str, auth_token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(...)
        return response.json()

# New (sync):
@staticmethod
def _call_device_endpoint_sync(device_id: str, endpoint: str, auth_token: str):
    """
    Synchronous version for Celery worker.
    
    Args:
        device_id: Device ID
        endpoint: API endpoint (e.g., 'cdp-neighbors')
        auth_token: Authentication token
        
    Returns:
        API response as dict
    """
    base_url = "http://localhost:8000"
    url = f"{base_url}/api/devices/{device_id}/{endpoint}?use_textfsm=true"
    
    with httpx.Client() as client:
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=30.0
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API call failed: {response.status_code}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
```

#### 3. Create sync version of discover_device_data

```python
@staticmethod
def discover_device_data_sync(
    db: Session,
    device_id: str,
    task: Any,  # Celery task for progress updates
    include_static_routes: bool = True,
    include_ospf_routes: bool = True,
    include_bgp_routes: bool = True,
    include_mac_table: bool = True,
    include_cdp_neighbors: bool = True,
    cache_results: bool = True,
    auth_token: str = ""
) -> Dict[str, Any]:
    """
    Synchronous version of discover_device_data for Celery worker.
    
    This method is called from discover_single_device_task and runs
    in the Celery worker context.
    """
    logger.info(f"🔍 Starting sync discovery for device {device_id}")
    
    device_data = {
        "device_id": device_id,
        "static_routes": [],
        "ospf_routes": [],
        "bgp_routes": [],
        "mac_table": [],
        "cdp_neighbors": []
    }
    
    total_tasks = sum([
        include_static_routes,
        include_ospf_routes,
        include_bgp_routes,
        include_mac_table,
        include_cdp_neighbors
    ])
    completed_tasks = 0
    
    # Static Routes
    if include_static_routes:
        task.update_state(
            state='PROGRESS',
            meta={
                'progress': int(completed_tasks / total_tasks * 100),
                'current_task': 'Discovering static routes'
            }
        )
        
        try:
            result = TopologyDiscoveryService._call_device_endpoint_sync(
                device_id=device_id,
                endpoint="ip-route/static",
                auth_token=auth_token
            )
            
            if result.get("success") and isinstance(result.get("output"), list):
                device_data["static_routes"] = result["output"]
                
                if cache_results:
                    TopologyDiscoveryService._cache_static_routes_sync(
                        db, device_id, result["output"]
                    )
        except Exception as e:
            logger.error(f"Failed to get static routes: {e}")
        
        completed_tasks += 1
    
    # ... Similar for OSPF, BGP, MAC, CDP ...
    
    task.update_state(
        state='PROGRESS',
        meta={
            'progress': 100,
            'current_task': 'Discovery completed'
        }
    )
    
    return device_data
```

#### 4. Make cache methods synchronous

```python
@staticmethod
def _cache_static_routes_sync(db: Session, device_id: str, routes: List[Dict[str, Any]]):
    """Synchronous cache method for Celery worker."""
    from ..schemas.device_cache import StaticRouteCacheCreate
    
    try:
        for route in routes:
            cache_entry = StaticRouteCacheCreate(
                device_id=device_id,
                network=route.get("network"),
                next_hop=route.get("next_hop"),
                # ... other fields
            )
            device_cache_service.cache_static_route(db, cache_entry)
    except Exception as e:
        logger.error(f"Failed to cache static routes: {e}")
        raise
```

#### 5. Keep async version for backward compatibility (optional)

```python
# Keep the async version for direct API calls (non-Celery)
@staticmethod
async def discover_device_data(
    # ... existing async implementation
):
    """
    Async version - kept for backward compatibility.
    Use discover_device_data_sync() for Celery tasks.
    """
    pass
```

---

### Phase 3: Update API Endpoints

**File:** `backend/app/api/topology.py`

#### New Endpoint Structure

```python
from app.tasks.topology_tasks import discover_topology_task
from app.services.background_jobs import background_job_service


@router.post("/topology/discover-async", response_model=TopologyDiscoveryResult)
async def discover_topology_async(
    request: TopologyDiscoveryRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
):
    """
    Start asynchronous topology discovery using Celery workers.
    
    Returns immediately with a job_id that can be used to track progress.
    Use GET /topology/discover/progress/{job_id} to check status.
    
    This endpoint:
    - Creates a Celery task for topology discovery
    - Returns job_id immediately (non-blocking)
    - Allows parallel processing of multiple devices
    - Supports cancellation via DELETE /topology/discover/{job_id}
    
    Args:
        request: Discovery request with device IDs and options
        
    Returns:
        Job ID and initial status
    """
    try:
        logger.info(f"📡 Starting async topology discovery for {len(request.device_ids)} devices")
        
        # Submit task to Celery
        task = discover_topology_task.apply_async(
            kwargs={
                "device_ids": request.device_ids,
                "include_static_routes": request.include_static_routes,
                "include_ospf_routes": request.include_ospf_routes,
                "include_bgp_routes": request.include_bgp_routes,
                "include_mac_table": request.include_mac_table,
                "include_cdp_neighbors": request.include_cdp_neighbors,
                "cache_results": request.cache_results,
                "auth_token": credentials.credentials
            }
        )
        
        logger.info(f"✅ Task submitted with job_id: {task.id}")
        
        return {
            "job_id": task.id,
            "status": "pending",
            "total_devices": len(request.device_ids),
            "successful_devices": 0,
            "failed_devices": 0,
            "devices_data": {},
            "errors": {},
            "duration_seconds": 0
        }
        
    except Exception as e:
        logger.error(f"Failed to start discovery: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start topology discovery: {str(e)}"
        )


@router.post("/topology/discover-sync", response_model=TopologyDiscoveryResult)
async def discover_topology_sync(
    request: TopologyDiscoveryRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
):
    """
    Synchronous topology discovery (blocks until complete).
    
    Use this for small numbers of devices or when immediate results are needed.
    For large-scale discovery, use /topology/discover-async instead.
    
    This endpoint:
    - Blocks until discovery completes
    - Returns full results immediately
    - Not recommended for > 5 devices
    
    Args:
        request: Discovery request with device IDs and options
        
    Returns:
        Complete discovery results
    """
    try:
        logger.info(f"📡 Starting sync topology discovery for {len(request.device_ids)} devices")
        
        # Run discovery directly (async version)
        result = await TopologyDiscoveryService.discover_topology(
            device_ids=request.device_ids,
            include_static_routes=request.include_static_routes,
            include_ospf_routes=request.include_ospf_routes,
            include_bgp_routes=request.include_bgp_routes,
            include_mac_table=request.include_mac_table,
            include_cdp_neighbors=request.include_cdp_neighbors,
            cache_results=request.cache_results,
            auth_token=credentials.credentials,
            db=db
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Sync discovery failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to discover topology: {str(e)}"
        )


@router.get("/topology/discover/progress/{job_id}", response_model=TopologyDiscoveryProgress)
async def get_discovery_progress(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get progress for a topology discovery job.
    
    Query this endpoint periodically to track progress of an async discovery job.
    
    Job Status Values:
    - PENDING: Task is waiting to be executed
    - STARTED: Task has been started
    - PROGRESS: Task is in progress (check meta for details)
    - SUCCESS: Task completed successfully
    - FAILURE: Task failed
    - REVOKED: Task was cancelled
    
    Args:
        job_id: Job ID returned from /topology/discover-async
        
    Returns:
        Current job status and progress information
    """
    try:
        # Query Celery for job status
        result = background_job_service.get_job_status(job_id)
        
        status_mapping = {
            'PENDING': 'pending',
            'STARTED': 'in_progress',
            'PROGRESS': 'in_progress',
            'SUCCESS': 'completed',
            'FAILURE': 'failed',
            'REVOKED': 'cancelled'
        }
        
        celery_status = result.get('status', 'PENDING')
        our_status = status_mapping.get(celery_status, 'unknown')
        
        # Extract progress from metadata
        meta = result.get('info', {})
        
        if celery_status == 'SUCCESS':
            # Task completed, result contains final data
            return {
                "job_id": job_id,
                "status": "completed",
                "total_devices": meta.get('total_devices', 0),
                "completed_devices": meta.get('successful_devices', 0),
                "failed_devices": meta.get('failed_devices', 0),
                "progress_percentage": 100,
                "devices": [],
                "started_at": meta.get('started_at'),
                "completed_at": meta.get('completed_at'),
                "error": None
            }
        elif celery_status == 'FAILURE':
            # Task failed
            return {
                "job_id": job_id,
                "status": "failed",
                "total_devices": meta.get('total_devices', 0),
                "completed_devices": meta.get('completed_devices', 0),
                "failed_devices": meta.get('failed_devices', 0),
                "progress_percentage": meta.get('progress_percentage', 0),
                "devices": meta.get('devices', []),
                "started_at": meta.get('started_at'),
                "completed_at": meta.get('completed_at'),
                "error": result.get('traceback')
            }
        else:
            # Task in progress
            return {
                "job_id": job_id,
                "status": our_status,
                "total_devices": meta.get('total_devices', 0),
                "completed_devices": meta.get('completed_devices', 0),
                "failed_devices": meta.get('failed_devices', 0),
                "progress_percentage": meta.get('progress_percentage', 0),
                "devices": meta.get('devices', []),
                "started_at": meta.get('started_at'),
                "completed_at": None,
                "error": None
            }
            
    except Exception as e:
        logger.error(f"Failed to get progress: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job progress: {str(e)}"
        )


@router.delete("/topology/discover/{job_id}")
async def cancel_discovery(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Cancel a running topology discovery job.
    
    Attempts to terminate the Celery task and any child tasks.
    
    Args:
        job_id: Job ID to cancel
        
    Returns:
        Cancellation status
    """
    try:
        success = background_job_service.cancel_job(job_id)
        
        if success:
            return {
                "job_id": job_id,
                "status": "cancelled",
                "message": "Discovery job cancelled successfully"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to cancel job"
            )
            
    except Exception as e:
        logger.error(f"Failed to cancel job: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel job: {str(e)}"
        )
```

#### Deprecate old endpoint (optional)

```python
@router.post("/topology/discover", deprecated=True)
async def discover_topology_legacy(...):
    """
    DEPRECATED: Use /topology/discover-async or /topology/discover-sync instead.
    """
    pass
```

---

### Phase 4: Handle Async in Celery

**Challenge:** Current code uses `async def` and `httpx.AsyncClient`, but Celery workers run sync tasks.

#### Option A: Convert to Sync (✅ Recommended)

```python
import httpx

def _call_device_endpoint_sync(device_id: str, endpoint: str, auth_token: str):
    """Synchronous version for Celery worker."""
    url = f"http://localhost:8000/api/devices/{device_id}/{endpoint}"
    
    with httpx.Client() as client:
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=30.0
        )
        return response.json()
```

**Advantages:**
- Simpler code
- More reliable in Celery context
- No event loop issues
- Better performance (no async overhead)

#### Option B: Use asyncio in task (More complex)

```python
import asyncio

@celery_app.task(bind=True)
def discover_device_task(self, ...):
    """Run async code in sync Celery task."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            TopologyDiscoveryService.discover_device_data(...)
        )
        return result
    finally:
        loop.close()
```

**Disadvantages:**
- More complex
- Potential event loop conflicts
- Harder to debug

**Recommendation:** Use Option A (sync) for simplicity and reliability.

---

### Phase 5: Database Session Management

**Challenge:** SQLAlchemy sessions in Celery tasks need special handling.

#### Proper Session Handling

```python
from app.core.database import SessionLocal

@celery_app.task(bind=True)
def discover_single_device_task(self, device_id, ...):
    """Each task gets its own database session."""
    
    # Create new session for this task
    db = SessionLocal()
    
    try:
        # Use db for all database operations
        result = TopologyDiscoveryService.discover_device_data_sync(
            db=db,
            device_id=device_id,
            ...
        )
        
        # Commit all changes
        db.commit()
        
        return {
            'success': True,
            'device_id': device_id,
            'data': result
        }
        
    except Exception as e:
        # Rollback on error
        db.rollback()
        logger.error(f"Task failed for {device_id}: {e}")
        
        return {
            'success': False,
            'device_id': device_id,
            'error': str(e)
        }
        
    finally:
        # Always close the session
        db.close()
```

#### Session Best Practices

1. **One session per task** - Don't share sessions across tasks
2. **Always close** - Use try/finally to ensure cleanup
3. **Commit/rollback explicitly** - Don't rely on autocommit
4. **Don't pass sessions** - Create new sessions in tasks
5. **Handle connection pooling** - Configure pool size in config

---

### Phase 6: Parallel Execution

**Use Celery groups/chords for parallel device discovery:**

#### Celery Group (Parallel Execution)

```python
from celery import group

@celery_app.task(bind=True)
def discover_topology_task(self, device_ids, options, auth_token):
    """Orchestrate parallel device discovery using groups."""
    
    # Create group of parallel tasks
    job = group(
        discover_single_device_task.s(
            device_id=device_id,
            parent_job_id=self.request.id,
            options=options,
            auth_token=auth_token
        )
        for device_id in device_ids
    )
    
    # Execute all tasks in parallel
    result = job.apply_async()
    
    # Wait for all to complete (blocks)
    device_results = result.get()
    
    # Aggregate results
    return aggregate_results(device_results)
```

#### Celery Chord (Parallel + Callback)

```python
from celery import chord

@celery_app.task(bind=True)
def discover_topology_task(self, device_ids, options, auth_token):
    """Parallel execution with callback for aggregation."""
    
    # Create chord: parallel tasks + callback
    job = chord(
        discover_single_device_task.s(
            device_id=device_id,
            parent_job_id=self.request.id,
            options=options,
            auth_token=auth_token
        )
        for device_id in device_ids
    )(aggregate_results_task.s())
    
    # Returns immediately, callback will aggregate when done
    return job.id


@celery_app.task
def aggregate_results_task(device_results):
    """Callback to aggregate results from all devices."""
    devices_data = {}
    errors = {}
    
    for result in device_results:
        if result['success']:
            devices_data[result['device_id']] = result['data']
        else:
            errors[result['device_id']] = result['error']
    
    return {
        'devices_data': devices_data,
        'errors': errors,
        'total': len(device_results)
    }
```

#### Concurrency Configuration

**File:** `backend/app/services/background_jobs.py`

```python
celery_app.conf.update(
    # Worker concurrency (number of parallel tasks)
    worker_concurrency=4,  # Adjust based on system resources
    
    # Task routing
    task_routes={
        'app.tasks.topology_tasks.discover_single_device_task': {
            'queue': 'discovery',
            'routing_key': 'discovery.device'
        }
    },
    
    # Rate limiting (optional)
    task_annotations={
        'app.tasks.topology_tasks.discover_single_device_task': {
            'rate_limit': '10/m'  # Max 10 devices per minute
        }
    }
)
```

---

### Phase 7: Progress Tracking

**How to track progress of parent + child tasks:**

#### Parent Task Progress Updates

```python
@celery_app.task(bind=True)
def discover_topology_task(self, device_ids, ...):
    """Main task with progress tracking."""
    total_devices = len(device_ids)
    completed = 0
    failed = 0
    
    # Initialize state
    self.update_state(
        state='PROGRESS',
        meta={
            'job_id': self.request.id,
            'status': 'in_progress',
            'total_devices': total_devices,
            'completed_devices': 0,
            'failed_devices': 0,
            'progress_percentage': 0,
            'devices': [
                {
                    'device_id': did,
                    'status': 'pending',
                    'progress_percentage': 0
                }
                for did in device_ids
            ],
            'started_at': datetime.now(timezone.utc).isoformat()
        }
    )
    
    # Create parallel tasks
    job = group(...)
    result = job.apply_async()
    
    # Monitor progress (if not using chord)
    while not result.ready():
        # Update overall progress
        completed_count = result.completed_count()
        progress_pct = int(completed_count / total_devices * 100)
        
        self.update_state(
            state='PROGRESS',
            meta={
                'completed_devices': completed_count,
                'progress_percentage': progress_pct,
                'status': f'Processing {completed_count}/{total_devices} devices'
            }
        )
        
        time.sleep(2)  # Poll every 2 seconds
    
    # Get final results
    device_results = result.get()
    
    # Final update
    return {
        'status': 'completed',
        'total_devices': total_devices,
        'completed_at': datetime.now(timezone.utc).isoformat()
    }
```

#### Child Task Progress Updates

```python
@celery_app.task(bind=True)
def discover_single_device_task(self, device_id, ...):
    """Device task with granular progress."""
    
    tasks = [
        ('static_routes', 20),
        ('ospf_routes', 20),
        ('bgp_routes', 20),
        ('mac_table', 20),
        ('cdp_neighbors', 20)
    ]
    
    current_progress = 0
    
    for task_name, task_weight in tasks:
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={
                'device_id': device_id,
                'current_task': f'Discovering {task_name}',
                'progress': current_progress
            }
        )
        
        # Perform task
        # ...
        
        current_progress += task_weight
    
    # Final update
    self.update_state(
        state='PROGRESS',
        meta={
            'device_id': device_id,
            'current_task': 'Completed',
            'progress': 100
        }
    )
```

---

## File Structure

### Proposed Directory Layout

```
backend/app/
├── api/
│   └── topology.py                    # MODIFIED: New async/sync endpoints
│
├── services/
│   ├── topology_discovery_service.py  # MODIFIED: Add sync methods
│   ├── device_cache_service.py        # Existing
│   └── background_jobs.py             # MODIFIED: Register new tasks
│
├── tasks/                             # NEW DIRECTORY
│   ├── __init__.py                    # NEW: Export tasks
│   └── topology_tasks.py              # NEW: Celery tasks
│
├── schemas/
│   ├── topology.py                    # MODIFIED: New response models
│   └── device_cache.py                # Existing
│
├── core/
│   ├── config.py                      # Existing: Celery config
│   └── database.py                    # Existing: SessionLocal
│
└── models/
    └── device_cache.py                # Existing
```

### New Files to Create

1. **`backend/app/tasks/__init__.py`**
```python
"""
Celery tasks for background processing.
"""
from .topology_tasks import (
    discover_topology_task,
    discover_single_device_task
)

__all__ = [
    'discover_topology_task',
    'discover_single_device_task'
]
```

2. **`backend/app/tasks/topology_tasks.py`**
   - Main Celery tasks (see Phase 1)

### Files to Modify

1. **`backend/app/services/topology_discovery_service.py`**
   - Add sync versions of methods
   - Remove in-memory job storage
   - Add sync caching methods

2. **`backend/app/api/topology.py`**
   - Add `/topology/discover-async` endpoint
   - Add `/topology/discover-sync` endpoint
   - Update `/topology/discover/progress/{job_id}`
   - Add `/topology/discover/{job_id}` DELETE endpoint

3. **`backend/app/services/background_jobs.py`**
   - Register topology tasks in include list
   - Update task routing (optional)

4. **`backend/app/schemas/topology.py`**
   - Update response models if needed

---

## Migration Steps

### Step-by-Step Implementation

#### ✅ Step 1: Prepare Environment
```bash
# Ensure Redis is running
redis-cli ping  # Should return PONG

# Ensure Celery dependencies are installed
pip install celery redis

# Test worker connection
cd backend
python start_worker.py  # Should start without errors
```

#### ✅ Step 2: Create Tasks Directory
```bash
cd backend/app
mkdir tasks
touch tasks/__init__.py
touch tasks/topology_tasks.py
```

#### ✅ Step 3: Implement Basic Task Structure

**File:** `tasks/topology_tasks.py`

Start with a simple test task:
```python
from app.services.background_jobs import celery_app

@celery_app.task(bind=True)
def test_topology_task(self, device_id):
    """Test task to verify Celery setup."""
    self.update_state(
        state='PROGRESS',
        meta={'device_id': device_id, 'status': 'testing'}
    )
    return {'device_id': device_id, 'success': True}
```

Test it:
```python
# In Python shell or test script
from app.tasks.topology_tasks import test_topology_task
task = test_topology_task.apply_async(kwargs={'device_id': 'test-device'})
print(task.id)
print(task.status)
print(task.result)
```

#### ✅ Step 4: Implement Single Device Task

Add `discover_single_device_task` (see Phase 1 for full code).

Test with one device:
```python
task = discover_single_device_task.apply_async(
    kwargs={
        'device_id': 'device-001',
        'parent_job_id': 'test-job',
        'options': {...},
        'auth_token': 'your-token'
    }
)
```

#### ✅ Step 5: Add Sync Methods to Discovery Service

**File:** `services/topology_discovery_service.py`

1. Add `_call_device_endpoint_sync()`
2. Add `discover_device_data_sync()`
3. Add sync cache methods

Test sync methods directly before integrating with Celery.

#### ✅ Step 6: Implement Orchestrator Task

Add `discover_topology_task` with parallel execution (see Phase 1).

Test with multiple devices:
```python
task = discover_topology_task.apply_async(
    kwargs={
        'device_ids': ['device-001', 'device-002'],
        'include_static_routes': True,
        # ... options
    }
)
```

#### ✅ Step 7: Update API Endpoints

**File:** `api/topology.py`

1. Add `/topology/discover-async` endpoint
2. Update `/topology/discover/progress/{job_id}`
3. Test via API:
```bash
curl -X POST http://localhost:8000/api/topology/discover-async \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_ids": ["device-001"],
    "include_static_routes": true
  }'
```

#### ✅ Step 8: Remove In-Memory Storage

**File:** `services/topology_discovery_service.py`

Remove:
- `_discovery_jobs` dict
- `create_job()` method
- `get_job_progress()` method (moved to endpoint)
- `update_job_status()` method
- `update_device_progress()` method

All state is now in Redis via Celery.

#### ✅ Step 9: Add Error Handling & Retries

```python
@celery_app.task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_kwargs={'max_retries': 3, 'countdown': 5},
    retry_backoff=True
)
def discover_single_device_task(self, device_id, ...):
    """Task with automatic retry logic."""
    try:
        # Discovery logic
        pass
    except Exception as e:
        logger.error(f"Device {device_id} failed: {e}")
        raise
```

#### ✅ Step 10: Integration Testing

Test scenarios:
1. Single device discovery
2. Multiple devices (parallel)
3. Progress tracking
4. Error handling (device unreachable)
5. Partial failures
6. Task cancellation
7. Worker restart during discovery

#### ✅ Step 11: Update Documentation

Update:
- API documentation
- README with Celery setup instructions
- Architecture diagrams
- Deployment guides

#### ✅ Step 12: Deploy

1. Deploy code changes
2. Restart FastAPI backend
3. Restart Celery workers
4. Monitor logs for issues

---

## Testing Strategy

### Unit Tests

**File:** `tests/test_topology_tasks.py`

```python
import pytest
from app.tasks.topology_tasks import (
    discover_single_device_task,
    discover_topology_task
)

def test_single_device_task():
    """Test single device discovery task."""
    result = discover_single_device_task.apply(
        kwargs={
            'device_id': 'test-device',
            'parent_job_id': 'test-job',
            'options': {...},
            'auth_token': 'test-token'
        }
    )
    
    assert result.successful()
    assert result.result['device_id'] == 'test-device'
    assert result.result['success'] is True

def test_parallel_discovery():
    """Test parallel device discovery."""
    result = discover_topology_task.apply(
        kwargs={
            'device_ids': ['device-1', 'device-2'],
            'include_static_routes': True,
            'auth_token': 'test-token'
        }
    )
    
    assert result.successful()
    assert len(result.result['devices_data']) == 2
```

### Integration Tests

**File:** `tests/test_topology_api.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_discover_async_endpoint():
    """Test async discovery endpoint."""
    response = client.post(
        '/api/topology/discover-async',
        json={
            'device_ids': ['device-001'],
            'include_static_routes': True
        },
        headers={'Authorization': 'Bearer test-token'}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert 'job_id' in data
    assert data['status'] == 'pending'

def test_progress_endpoint():
    """Test progress tracking endpoint."""
    # Start discovery
    start_response = client.post(...)
    job_id = start_response.json()['job_id']
    
    # Check progress
    progress_response = client.get(
        f'/api/topology/discover/progress/{job_id}',
        headers={'Authorization': 'Bearer test-token'}
    )
    
    assert progress_response.status_code == 200
    data = progress_response.json()
    assert data['job_id'] == job_id
    assert 'progress_percentage' in data
```

### Load Tests

```python
def test_parallel_devices():
    """Test discovery of 50 devices in parallel."""
    device_ids = [f'device-{i:03d}' for i in range(50)]
    
    response = client.post(
        '/api/topology/discover-async',
        json={'device_ids': device_ids}
    )
    
    job_id = response.json()['job_id']
    
    # Poll until complete
    while True:
        progress = client.get(f'/api/topology/discover/progress/{job_id}')
        if progress.json()['status'] in ['completed', 'failed']:
            break
        time.sleep(2)
    
    # Verify results
    assert progress.json()['status'] == 'completed'
```

### Error Scenarios

```python
def test_device_unreachable():
    """Test handling of unreachable device."""
    response = client.post(
        '/api/topology/discover-async',
        json={'device_ids': ['unreachable-device']}
    )
    
    job_id = response.json()['job_id']
    
    # Wait for completion
    time.sleep(10)
    
    # Check errors
    progress = client.get(f'/api/topology/discover/progress/{job_id}')
    data = progress.json()
    
    assert data['failed_devices'] == 1
    assert 'unreachable-device' in data.get('errors', {})

def test_task_cancellation():
    """Test cancelling a running task."""
    # Start long-running discovery
    response = client.post(
        '/api/topology/discover-async',
        json={'device_ids': [f'device-{i}' for i in range(100)]}
    )
    
    job_id = response.json()['job_id']
    
    # Cancel immediately
    cancel_response = client.delete(
        f'/api/topology/discover/{job_id}'
    )
    
    assert cancel_response.status_code == 200
    
    # Verify cancellation
    progress = client.get(f'/api/topology/discover/progress/{job_id}')
    assert progress.json()['status'] == 'cancelled'
```

---

## Important Considerations

### 🔐 Security

#### 1. Auth Token Handling
```python
# ❌ BAD: Logging auth tokens
logger.info(f"Using token: {auth_token}")

# ✅ GOOD: Mask sensitive data
logger.info(f"Using token: {auth_token[:10]}***")

# ✅ GOOD: Don't include in task metadata
self.update_state(
    meta={'device_id': device_id}  # No auth_token here
)
```

#### 2. Rate Limiting
```python
# Limit concurrent device API calls
celery_app.conf.task_annotations = {
    'app.tasks.topology_tasks.discover_single_device_task': {
        'rate_limit': '10/m'  # Max 10 devices per minute
    }
}
```

#### 3. Input Validation
```python
@celery_app.task(bind=True)
def discover_topology_task(self, device_ids, ...):
    # Validate inputs
    if not device_ids or len(device_ids) > 100:
        raise ValueError("device_ids must be 1-100 items")
    
    # Sanitize device IDs
    device_ids = [did.strip() for did in device_ids if did.strip()]
```

### ⏱️ Performance

#### 1. Task Timeouts
```python
celery_app.conf.update(
    task_time_limit=30 * 60,       # Hard limit: 30 minutes
    task_soft_time_limit=25 * 60,  # Soft limit: 25 minutes
)

@celery_app.task(
    bind=True,
    time_limit=300,        # 5 minutes per device
    soft_time_limit=240    # Warning at 4 minutes
)
def discover_single_device_task(self, ...):
    pass
```

#### 2. Worker Concurrency
```bash
# Start worker with more concurrency
celery -A app.services.background_jobs worker \
    --loglevel=info \
    --concurrency=8 \
    --pool=prefork
```

#### 3. Connection Pooling
```python
# Configure httpx client pool
client = httpx.Client(
    limits=httpx.Limits(
        max_connections=100,
        max_keepalive_connections=20
    )
)
```

### 💾 Resource Management

#### 1. Result Expiry
```python
celery_app.conf.update(
    result_expires=3600,  # Results expire after 1 hour
)
```

#### 2. Database Connection Pooling
```python
# backend/app/core/database.py
engine = create_engine(
    settings.database_url,
    pool_size=10,        # Connection pool size
    max_overflow=20,     # Max overflow connections
    pool_pre_ping=True,  # Verify connections
    pool_recycle=3600    # Recycle after 1 hour
)
```

#### 3. Memory Limits
```python
# Limit result size
@celery_app.task(bind=True)
def discover_topology_task(self, ...):
    # If results too large, store in database instead
    if len(str(results)) > 1_000_000:  # 1MB limit
        # Store in DB, return reference
        pass
```

### 🔄 Reliability

#### 1. Automatic Retries
```python
@celery_app.task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
    retry_backoff_max=600,  # Max 10 minutes
    retry_jitter=True
)
def discover_single_device_task(self, ...):
    pass
```

#### 2. Dead Letter Queue
```python
# Configure DLQ for failed tasks
celery_app.conf.task_reject_on_worker_lost = True
celery_app.conf.task_acks_late = True
```

#### 3. Idempotency
```python
@celery_app.task(bind=True)
def discover_single_device_task(self, device_id, ...):
    # Make task idempotent - safe to retry
    # Check if already processed
    if already_cached(device_id):
        logger.info(f"Device {device_id} already processed, skipping")
        return cached_result(device_id)
    
    # Proceed with discovery
    # ...
```

### 📊 Monitoring

#### 1. Celery Flower
```bash
# Install Flower
pip install flower

# Start Flower
celery -A app.services.background_jobs flower \
    --port=5555 \
    --broker=redis://localhost:6379/1
```

Access at: http://localhost:5555

#### 2. Task Events
```python
# Enable task events
celery_app.conf.worker_send_task_events = True
celery_app.conf.task_send_sent_event = True
```

#### 3. Logging
```python
# Configure task logging
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@celery_app.task(bind=True)
def discover_topology_task(self, device_ids, ...):
    logger.info(f"Starting discovery for {len(device_ids)} devices")
    logger.info(f"Job ID: {self.request.id}")
    logger.info(f"Task name: {self.name}")
```

### 🚨 Error Handling

#### 1. Graceful Degradation
```python
@celery_app.task(bind=True)
def discover_single_device_task(self, device_id, ...):
    errors = []
    partial_data = {}
    
    # Try each endpoint independently
    for endpoint in ['static', 'ospf', 'bgp', 'mac', 'cdp']:
        try:
            data = call_endpoint(endpoint)
            partial_data[endpoint] = data
        except Exception as e:
            errors.append(f"{endpoint}: {str(e)}")
            # Continue with other endpoints
    
    # Return partial results
    return {
        'device_id': device_id,
        'success': len(errors) < 5,  # Success if at least one worked
        'data': partial_data,
        'errors': errors
    }
```

#### 2. Error Notifications
```python
from celery.signals import task_failure

@task_failure.connect
def task_failure_handler(sender, task_id, exception, **kwargs):
    """Send notification on task failure."""
    logger.error(
        f"Task {sender.name}[{task_id}] failed: {exception}",
        exc_info=exception
    )
    # Send email, Slack, etc.
```

### 🔧 Configuration Management

#### Environment Variables
```bash
# .env file
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
CELERY_WORKER_CONCURRENCY=4
CELERY_TASK_TIME_LIMIT=1800
CELERY_TASK_SOFT_TIME_LIMIT=1500
```

#### Dynamic Configuration
```python
from app.core.config import settings

celery_app.conf.update(
    worker_concurrency=settings.celery_worker_concurrency,
    task_time_limit=settings.celery_task_time_limit,
    # ... etc
)
```

---

## Endpoint Behavior Comparison

### Before (Current Implementation)

```
POST /topology/discover
├─ Request: {"device_ids": [...], "run_in_background": false}
├─ Blocks for: 5-30 minutes
├─ Returns: Complete discovery results
└─ Issues:
   ├─ Request timeout
   ├─ No progress visibility
   ├─ Sequential processing
   └─ Memory usage in FastAPI process

POST /topology/discover?run_in_background=true
├─ Request: {"device_ids": [...]}
├─ Uses: asyncio.create_task (not real background)
├─ Returns: job_id immediately
└─ Issues:
   ├─ Lost on server restart
   ├─ No persistence
   ├─ In-memory state only
   └─ No parallel processing
```

### After (Celery Implementation)

```
POST /topology/discover-async
├─ Request: {"device_ids": [...]}
├─ Creates: Celery task
├─ Returns: job_id (< 1 second)
└─ Benefits:
   ├─ Non-blocking
   ├─ Persistent in Redis
   ├─ Parallel processing
   └─ Survives restarts

GET /topology/discover/progress/{job_id}
├─ Queries: Celery state from Redis
├─ Returns: Real-time progress
└─ Features:
   ├─ Per-device status
   ├─ Overall progress %
   ├─ Current task info
   └─ Error details

POST /topology/discover-sync
├─ Request: {"device_ids": [...]}
├─ Blocks until complete
├─ Returns: Full results
└─ Use cases:
   ├─ Small device count (< 5)
   ├─ Interactive testing
   └─ Single device queries

DELETE /topology/discover/{job_id}
├─ Cancels: Running Celery task
├─ Terminates: All child tasks
└─ Returns: Cancellation status
```

---

## Alternative Architectures Considered

### Option A: Single endpoint with mode flag (Current)
```python
POST /topology/discover?run_in_background=true
```
**Pros:**
- Single API endpoint
- Simple routing

**Cons:**
- Inconsistent response schemas
- Unclear semantics
- Hard to version separately

### Option B: Separate endpoints (✅ Recommended)
```python
POST /topology/discover-async   # Non-blocking, returns job_id
POST /topology/discover-sync    # Blocking, returns results
GET  /topology/jobs/{job_id}    # Get status/result
```
**Pros:**
- Clear intent
- Consistent response schemas
- Easy to document
- Independent versioning

**Cons:**
- More endpoints to maintain

### Option C: WebSocket for real-time updates
```python
POST /topology/discover         # Start job
WS   /topology/discover/{job_id} # Stream progress
```
**Pros:**
- Real-time streaming updates
- Efficient for long-running tasks

**Cons:**
- More complex infrastructure
- Requires WebSocket support
- Harder to scale

**Recommendation:** Use Option B (separate endpoints) for simplicity and clarity.

---

## Summary

### ✨ Best Approach

1. **Create separate `tasks/topology_tasks.py`** with Celery tasks
2. **Keep business logic in `topology_discovery_service.py`** (add sync versions)
3. **Update API to submit Celery tasks** instead of running inline
4. **Use Celery groups** for parallel device discovery
5. **Use Celery state updates** for progress tracking (replaces in-memory dict)
6. **Create separate async/sync endpoints** for clarity
7. **Handle database sessions** properly in tasks (SessionLocal)
8. **Convert async to sync** for device API calls in worker

### Benefits

- ✅ True background execution
- ✅ Parallel processing of multiple devices
- ✅ Real-time progress tracking
- ✅ Fault tolerance (survives worker restarts)
- ✅ Scalability (add more workers)
- ✅ Consistent with existing background job patterns
- ✅ Persistent job state in Redis
- ✅ Task cancellation support
- ✅ Automatic retries
- ✅ Better resource management

### Next Steps

1. Review this plan with the team
2. Set up development environment (Redis, Celery worker)
3. Create tasks directory and skeleton code
4. Implement and test single device task
5. Add parallel execution
6. Update API endpoints
7. Integration testing
8. Documentation updates
9. Deploy to production

---

## References

- **Celery Documentation:** https://docs.celeryq.dev/
- **FastAPI Background Tasks:** https://fastapi.tiangolo.com/tutorial/background-tasks/
- **Redis Documentation:** https://redis.io/docs/
- **Celery Flower:** https://flower.readthedocs.io/
- **Best Practices:** https://docs.celeryq.dev/en/stable/userguide/tasks.html#best-practices

---

**Document Version:** 1.0  
**Last Updated:** October 5, 2025  
**Status:** Ready for Implementation
