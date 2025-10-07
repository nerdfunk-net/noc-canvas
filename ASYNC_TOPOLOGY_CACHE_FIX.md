# Async Topology Discovery Cache Bug Fix

## Problem Description

When using the asynchronous topology discovery mechanism (`async_discovery.py`), the JSON blob cache was being populated correctly, but the structured topology cache tables (interfaces, ARP, routes, CDP neighbors, etc.) remained empty.

## Root Cause

In `async_discovery.py`, all topology cache population methods were **commented out** with `pass` statements:

```python
# Cache if requested (async cache methods would go here)
if cache_results and db:
    # await AsyncTopologyDiscoveryService._cache_interfaces(
    #     db, device_id, result["output"]
    # )
    pass  # Cache methods not yet implemented
```

This was left as a TODO, while the synchronous discovery (`sync_discovery.py`) properly implemented all caching methods.

## Comparison: Sync vs Async

### Sync Discovery (WORKING ✅)
```python
if cache_results:
    SyncTopologyDiscoveryService._cache_interfaces_sync(
        db, device_id, result["output"]
    )
    SyncTopologyDiscoveryService._cache_arp_entries_sync(
        db, device_id, result["output"]
    )
    # ... etc for all data types
```

### Async Discovery (BROKEN ❌)
```python
if cache_results and db:
    pass  # Cache methods not yet implemented
```

## The Fix

### 1. Added Missing Imports

Added imports for all cache schemas and services:

```python
from ...schemas.device_cache import (
    ARPCacheCreate,
    BGPRouteCacheCreate,
    CDPNeighborCacheCreate,
    InterfaceCacheCreate,
    IPAddressCacheCreate,
    MACAddressTableCacheCreate,
    OSPFRouteCacheCreate,
    StaticRouteCacheCreate,
    DeviceCacheCreate,
)
from ...services.device_cache_service import device_cache_service
```

### 2. Ensured Device Cache Entry Exists

Added device cache initialization at the start of discovery (required for foreign key constraints):

```python
# Ensure device cache entry exists before caching any data
if cache_results and db:
    # Get device info from Nautobot
    device_info = await nautobot_service.get_device(device_id, username)
    
    # Create or update device cache entry
    device_cache_data = DeviceCacheCreate(
        device_id=device_id,
        device_name=device_info.get("name", ""),
        primary_ip=primary_ip,
        platform=platform,
    )
    device_cache_service.get_or_create_device_cache(db, device_cache_data)
```

### 3. Added Cache Calls for All Data Types

Replaced all `pass` statements with proper cache method calls:

#### Interfaces
```python
if cache_results and db:
    AsyncTopologyDiscoveryService._cache_interfaces_async(
        db, device_id, result["output"]
    )
```

#### Static Routes
```python
if cache_results and db:
    AsyncTopologyDiscoveryService._cache_static_routes_async(
        db, device_id, result["output"]
    )
```

#### OSPF Routes
```python
if cache_results and db:
    AsyncTopologyDiscoveryService._cache_ospf_routes_async(
        db, device_id, result["output"]
    )
```

#### BGP Routes
```python
if cache_results and db:
    AsyncTopologyDiscoveryService._cache_bgp_routes_async(
        db, device_id, result["output"]
    )
```

#### MAC Address Table
```python
if cache_results and db:
    AsyncTopologyDiscoveryService._cache_mac_table_async(
        db, device_id, result["output"]
    )
```

#### CDP Neighbors
```python
if cache_results and db:
    AsyncTopologyDiscoveryService._cache_cdp_neighbors_async(
        db, device_id, result["output"]
    )
```

#### ARP Entries
```python
if cache_results and db:
    AsyncTopologyDiscoveryService._cache_arp_entries_async(
        db, device_id, result["output"]
    )
```

### 4. Implemented All Cache Methods

Added complete implementations at the end of the file:

- `_cache_static_routes_async()`
- `_cache_ospf_routes_async()`
- `_cache_bgp_routes_async()`
- `_cache_mac_table_async()`
- `_cache_cdp_neighbors_async()`
- `_cache_arp_entries_async()`
- `_cache_interfaces_async()`

These methods are identical to the sync versions but named with `_async` suffix for clarity.

## Cache Flow

### Two-Layer Cache System

1. **JSON Blob Cache** (already working):
   - Stores raw parsed command output
   - Used by both `_call_device_endpoint()` in async and `_call_device_endpoint_sync()` in sync
   - Checked BEFORE making device calls (HTTP or SSH)
   - 30-minute TTL by default

2. **Structured Topology Cache** (now fixed):
   - Stores normalized data in relational tables
   - Tables: `device_cache`, `interface_cache`, `arp_cache`, `static_route_cache`, etc.
   - Used for building topology visualizations
   - Updated AFTER successful discovery
   - **Was broken in async path, now fixed**

## Files Modified

- `backend/app/services/topology_discovery/async_discovery.py`:
  - Added imports for cache schemas and services
  - Added device cache initialization
  - Added cache method calls for all 7 data types
  - Implemented 7 cache methods (`_cache_*_async`)

## Testing

After this fix:
1. ✅ JSON blob cache still works (already did)
2. ✅ Structured topology cache now populated correctly
3. ✅ Both async (API) and sync (Celery) paths now cache properly
4. ✅ Topology builder can use cached data from both execution paths

## Impact

- **Before**: Async discovery only cached JSON blobs, topology cache stayed empty
- **After**: Async discovery caches both JSON blobs AND structured topology data
- **Compatibility**: No breaking changes, only adds missing functionality
- **Performance**: No impact, caching is optional via `cache_results` flag

## Related Components

- **Sync Discovery**: `backend/app/services/topology_discovery/sync_discovery.py`
- **Base Class**: `backend/app/services/topology_discovery/base.py`
- **Cache Service**: `backend/app/services/device_cache_service.py`
- **JSON Cache**: `backend/app/services/json_cache_service.py`
- **Cache Tables**: `backend/app/models/device_cache.py`

## Date

Fixed: October 7, 2025
