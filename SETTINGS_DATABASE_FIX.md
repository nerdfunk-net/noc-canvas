# Settings Database Loading Fix

## Problem Identified

The application has a **dual configuration system** that's not properly integrated:

1. **Settings are SAVED to database** ✅ (via `/api/settings/unified` endpoint)
2. **Settings are READ from environment variables** ❌ (via `settings.nautobot_url`)

This causes:
- Settings saved in UI don't take effect
- Application always uses .env file values
- Database settings are ignored

## Root Cause

### Current Flow (BROKEN):
```
User saves settings → Database ✅
  ↓
Application uses settings → Environment variables only ❌
```

### Files Involved:

1. **`app/core/config.py`** - Loads from env vars only
   ```python
   settings = Settings()  # Only reads from .env
   ```

2. **`app/routers/nautobot_*.py`** - Uses static settings
   ```python
   if not settings.nautobot_url or not settings.nautobot_token:
       # Always checks .env, not database!
   ```

3. **`app/services/nautobot.py`** - Uses static settings
   ```python
   "url": settings.nautobot_url  # From .env only
   ```

## Solution Implemented

### Created Dynamic Settings Loader
**File:** `app/core/dynamic_settings.py`

```python
def get_nautobot_config(db: Session) -> dict:
    """
    Get Nautobot config with priority:
    1. Database (user saved values)
    2. Environment variables (.env)
    3. Defaults
    """
```

### Required Changes

#### 1. Update All Nautobot Routers
Files to update:
- `/Users/mp/programming/noc-canvas/backend/app/routers/nautobot_devices.py` ✅ (Started)
- `/Users/mp/programming/noc-canvas/backend/app/routers/nautobot_metadata.py`
- `/Users/mp/programming/noc-canvas/backend/app/routers/nautobot_jobs.py`
- `/Users/mp/programming/noc-canvas/backend/app/routers/nautobot_network.py`

**Change needed:**
```python
# OLD (broken):
if not settings.nautobot_url or not settings.nautobot_token:
    ...
url = f"{settings.nautobot_url}/api/..."

# NEW (fixed):
nautobot_config = get_nautobot_config(db)
if not nautobot_config["url"] or not nautobot_config["token"]:
    ...
url = f"{nautobot_config['url']}/api/..."
```

#### 2. Update Nautobot Service
**File:** `app/services/nautobot.py`

Change all references from:
```python
settings.nautobot_url → nautobot_config["url"]
settings.nautobot_token → nautobot_config["token"]
```

#### 3. Update Legacy Nautobot Router
**File:** `app/api/nautobot.py`

Same changes as above.

## Alternative: Global Settings Reload

Instead of passing `db` everywhere, we could reload the global settings object:

```python
# app/core/config.py
def reload_settings_from_db(db: Session):
    """Reload settings from database into global settings object"""
    settings.nautobot_url = get_dynamic_setting(db, "nautobot_url", settings.nautobot_url)
    settings.nautobot_token = get_dynamic_setting(db, "nautobot_token", settings.nautobot_token)
    # etc...
```

**Pros:** Minimal code changes
**Cons:** Global state mutation, threading issues

## Recommended Approach

**Use dependency injection** (pass db session to get dynamic config)

Benefits:
- ✅ No global state mutation
- ✅ Thread-safe
- ✅ Testable
- ✅ Clear data flow

## Testing

After fix:
1. Save Nautobot settings in UI
2. Check database: `SELECT * FROM app_settings WHERE key LIKE 'nautobot%';`
3. Test connection: `GET /api/nautobot/test`
4. Should use database values, not .env

## Status

🚧 **IN PROGRESS**
- Created dynamic_settings.py ✅
- Started updating nautobot_devices.py ✅
- Need to update 3 more routers
- Need to update nautobot service
- Need to update legacy nautobot router
