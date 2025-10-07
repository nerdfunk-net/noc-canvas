# SQLAlchemy 2.0 joinedload String Error Fix

## Problem Description

When using async topology discovery or device API endpoints, the following error occurred:

```
ERROR - Error getting <data type> for device <device_id>: Strings are not accepted for attribute names in loader options; please use class-bound attributes directly.
```

This affected multiple endpoints:
- `/api/devices/{device_id}/ip-arp`
- `/api/devices/{device_id}/ip-route/static`
- `/api/devices/{device_id}/ip-route/ospf`
- `/api/devices/{device_id}/mac-address-table`
- `/api/devices/{device_id}/cdp-neighbors`

## Root Cause

In `backend/app/services/device_cache_service.py`, line 43 used a **string** for relationship loading:

```python
joinedload(DeviceCache.interfaces).joinedload('ip_addresses'),  # ❌ STRING
```

**SQLAlchemy 2.0+ doesn't accept strings** for eager loading options. You must use class-bound attributes.

## The Fix

Changed from string to proper relationship attribute:

### Before (BROKEN ❌)
```python
.options(
    joinedload(DeviceCache.interfaces).joinedload('ip_addresses'),  # STRING!
    joinedload(DeviceCache.ip_addresses),
    ...
)
```

### After (FIXED ✅)
```python
.options(
    joinedload(DeviceCache.interfaces).joinedload(InterfaceCache.ip_addresses),  # CLASS ATTRIBUTE!
    joinedload(DeviceCache.ip_addresses),
    ...
)
```

## Files Modified

- **`backend/app/services/device_cache_service.py`** (line 43):
  - Changed `.joinedload('ip_addresses')` → `.joinedload(InterfaceCache.ip_addresses)`

## Impact

**Before:**
- ❌ Device API endpoints returned 500 errors
- ❌ Async topology discovery failed when trying to cache data
- ❌ No structured cache populated

**After:**
- ✅ All device API endpoints work correctly
- ✅ Async topology discovery caches properly
- ✅ Both JSON blob and structured topology caches populated

## SQLAlchemy 2.0 Migration Note

This is a **breaking change** in SQLAlchemy 2.0+. String-based relationship names in loader options are no longer supported.

**Always use class-bound attributes:**
```python
# ✅ CORRECT (SQLAlchemy 2.0+)
joinedload(Parent.children).joinedload(Child.grandchildren)

# ❌ WRONG (deprecated in SQLAlchemy 1.4, removed in 2.0)
joinedload(Parent.children).joinedload('grandchildren')
```

## Testing

After this fix:
1. ✅ Device API endpoints return 200 OK
2. ✅ ARP, routes, CDP, MAC table all cache properly
3. ✅ Async topology discovery completes successfully
4. ✅ Cache statistics show populated data

## Related Error Messages

If you see these errors, check for string-based relationship loading:
- "Strings are not accepted for attribute names in loader options"
- "please use class-bound attributes directly"

## Date

Fixed: October 7, 2025
