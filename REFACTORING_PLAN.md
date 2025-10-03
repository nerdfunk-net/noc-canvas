# Backend Refactoring Plan - Nautobot API

## ✅ Completed

1. **Extracted GraphQL Queries** → `/backend/app/queries/nautobot_queries.py`
   - COMPLETE_DEVICE_DATA_QUERY
   - DEVICE_DETAILS_QUERY
   - NAMESPACES_QUERY
   - SECRET_GROUPS_QUERY

2. **Created Devices Router** → `/backend/app/routers/nautobot_devices.py`
   - GET `/devices` - List devices with filters
   - GET `/devices/{id}` - Get device
   - GET `/devices/{id}/nautobot-data` - GraphQL complete data
   - GET `/devices/{id}/details` - GraphQL detailed info
   - POST `/devices/search` - Search by name
   - GET `/device-types` - List device types

## 🚧 Remaining Work

### 3. Create Metadata Router (`/backend/app/routers/nautobot_metadata.py`)
Extract from main nautobot.py:
- GET `/locations` (line ~760)
- GET `/roles` (line ~815)
- GET `/roles/devices` (line ~835)
- GET `/platforms` (line ~855)
- GET `/statuses` (line ~890)
- GET `/statuses/device` (line ~910)
- GET `/namespaces` (line ~794)
- GET `/secret-groups` (line ~934)
- GET `/stats` (line ~777)

### 4. Create Jobs Router (`/backend/app/routers/nautobot_jobs.py`)
Extract from main nautobot.py:
- POST `/devices/onboard` (line ~645)
- POST `/sync-network-data` (line ~705)
- Helper: `execute_nautobot_job()` (line ~290)

### 5. Create Network Router (`/backend/app/routers/nautobot_network.py`)
Extract from main nautobot.py:
- POST `/check-ip` (line ~625)
- GET `/test` (line ~415) - Connection test

### 6. Update Main Router
Update `/backend/app/api/nautobot.py`:
```python
from ..queries.nautobot_queries import *
from ..routers import nautobot_devices, nautobot_metadata, nautobot_jobs, nautobot_network

# Keep only debug endpoints in main file (or remove them)
# Keep helper functions like get_username()
```

### 7. Update Main App
Update `/backend/app/main.py`:
```python
from .routers import (
    nautobot_devices,
    nautobot_metadata,
    nautobot_jobs,
    nautobot_network,
)

app.include_router(nautobot_devices.router, prefix="/api/nautobot", tags=["nautobot-devices"])
app.include_router(nautobot_metadata.router, prefix="/api/nautobot", tags=["nautobot-metadata"])
app.include_router(nautobot_jobs.router, prefix="/api/nautobot", tags=["nautobot-jobs"])
app.include_router(nautobot_network.router, prefix="/api/nautobot", tags=["nautobot-network"])
```

## Expected Results

### Before:
- 1 file: 1009 lines

### After:
- `queries/nautobot_queries.py`: ~200 lines (queries)
- `routers/nautobot_devices.py`: ~250 lines ✅ DONE
- `routers/nautobot_metadata.py`: ~200 lines
- `routers/nautobot_jobs.py`: ~150 lines
- `routers/nautobot_network.py`: ~100 lines
- `api/nautobot.py`: ~100 lines (debug + helpers)

**Total: Same functionality, better organization!**

## Benefits
✅ Single Responsibility - Each router has clear purpose
✅ Easier to Navigate - Find endpoints by domain
✅ Better Testing - Test routers independently
✅ Cleaner Imports - Only import what you need
✅ Team Scalability - Multiple devs can work on different routers

## Next Steps
Run the remaining creation steps (3-7) to complete the refactoring.
