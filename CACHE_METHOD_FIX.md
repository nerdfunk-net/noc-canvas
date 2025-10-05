# Cache Method Fix: Sync Discovery Caching

## Problem

The synchronous cache methods in `topology_discovery_service.py` were calling **non-existent singular methods** on `DeviceCacheService`:

```python
# ❌ WRONG - These methods don't exist!
device_cache_service.cache_static_route(db, cache_entry)
device_cache_service.cache_ospf_route(db, cache_entry)
device_cache_service.cache_bgp_route(db, cache_entry)
device_cache_service.cache_mac_address(db, cache_entry)
device_cache_service.cache_cdp_neighbor(db, cache_entry)
```

### Errors Observed
```
Failed to cache CDP neighbors for 8cea4a0f-b1d7-4ebd-aaa6-01ae7b3f38a5: 
  'DeviceCacheService' object has no attribute 'cache_cdp_neighbor'

Failed to cache static routes for 3ec64b79-aa33-46be-b9c2-6a5aa9ea6381: 
  'DeviceCacheService' object has no attribute 'cache_static_route'

Failed to cache OSPF routes for 3ec64b79-aa33-46be-b9c2-6a5aa9ea6381: 
  'DeviceCacheService' object has no attribute 'cache_ospf_route'

Failed to cache MAC table for c2029692-5e8d-4447-9f1e-c7fc90ba396f: 
  'DeviceCacheService' object has no attribute 'cache_mac_address'
```

## Root Cause

`DeviceCacheService` **only has bulk methods**, not singular methods:

```python
# ✅ These exist
device_cache_service.bulk_replace_static_routes(db, device_id, routes)
device_cache_service.bulk_replace_ospf_routes(db, device_id, routes)
device_cache_service.bulk_replace_bgp_routes(db, device_id, routes)
device_cache_service.bulk_replace_mac_table(db, device_id, entries)
device_cache_service.bulk_replace_cdp_neighbors(db, device_id, neighbors)
```

The sync methods were iterating and calling singular methods (which don't exist), instead of collecting all entries and calling the bulk method once.

## Solution

Changed all sync cache methods to:
1. Collect all entries into a list
2. Call the bulk_replace method once at the end

### Fixed Methods

#### 1. Static Routes ✅

**Before:**
```python
def _cache_static_routes_sync(db: Session, device_id: str, routes: List[Dict[str, Any]]):
    for route in routes:
        cache_entry = StaticRouteCacheCreate(...)
        device_cache_service.cache_static_route(db, cache_entry)  # ❌ Doesn't exist
```

**After:**
```python
def _cache_static_routes_sync(db: Session, device_id: str, routes: List[Dict[str, Any]]):
    cache_entries = []
    for route in routes:
        cache_entry = StaticRouteCacheCreate(
            device_id=device_id,
            network=route.get("network", ""),
            nexthop_ip=route.get("nexthop_ip"),
            interface_name=route.get("nexthop_if"),
            distance=route.get("distance"),
            metric=route.get("metric")
        )
        cache_entries.append(cache_entry)
    
    if cache_entries:
        device_cache_service.bulk_replace_static_routes(db, device_id, cache_entries)  # ✅
```

#### 2. OSPF Routes ✅

**Before:**
```python
device_cache_service.cache_ospf_route(db, cache_entry)  # ❌
```

**After:**
```python
cache_entries = []
for route in routes:
    cache_entry = OSPFRouteCacheCreate(
        device_id=device_id,
        network=route.get("network", ""),
        nexthop_ip=route.get("nexthop_ip"),
        interface_name=route.get("nexthop_if"),
        distance=route.get("distance"),
        metric=route.get("metric"),
        area=route.get("area"),
        route_type=route.get("route_type")
    )
    cache_entries.append(cache_entry)

if cache_entries:
    device_cache_service.bulk_replace_ospf_routes(db, device_id, cache_entries)  # ✅
```

#### 3. BGP Routes ✅

**Before:**
```python
device_cache_service.cache_bgp_route(db, cache_entry)  # ❌
```

**After:**
```python
cache_entries = []
for route in routes:
    cache_entry = BGPRouteCacheCreate(
        device_id=device_id,
        network=route.get("network", ""),
        nexthop_ip=route.get("nexthop_ip"),
        as_path=route.get("as_path"),
        local_pref=route.get("local_pref"),
        metric=route.get("metric"),
        weight=route.get("weight")
    )
    cache_entries.append(cache_entry)

if cache_entries:
    device_cache_service.bulk_replace_bgp_routes(db, device_id, cache_entries)  # ✅
```

#### 4. MAC Address Table ✅

**Before:**
```python
device_cache_service.cache_mac_address(db, cache_entry)  # ❌
```

**After:**
```python
cache_entries = []
for entry in mac_entries:
    cache_entry = MACAddressTableCacheCreate(
        device_id=device_id,
        vlan=entry.get("vlan", ""),
        mac_address=entry.get("destination_address", ""),
        interface=entry.get("destination_port", ""),
        type=entry.get("type", "")
    )
    cache_entries.append(cache_entry)

if cache_entries:
    device_cache_service.bulk_replace_mac_table(db, device_id, cache_entries)  # ✅
```

#### 5. CDP Neighbors ✅

**Before:**
```python
device_cache_service.cache_cdp_neighbor(db, cache_entry)  # ❌
```

**After:**
```python
cache_entries = []
for neighbor in neighbors:
    cache_entry = CDPNeighborCacheCreate(
        device_id=device_id,
        local_interface=neighbor.get("local_interface", ""),
        neighbor_name=neighbor.get("neighbor", ""),
        neighbor_interface=neighbor.get("neighbor_interface", ""),
        neighbor_ip=neighbor.get("management_ip", ""),
        platform=neighbor.get("platform", ""),
        capabilities=neighbor.get("capabilities", "")
    )
    cache_entries.append(cache_entry)

if cache_entries:
    device_cache_service.bulk_replace_cdp_neighbors(db, device_id, cache_entries)  # ✅
```

## Benefits of Bulk Methods

✅ **More Efficient** - Single database transaction instead of N transactions  
✅ **Atomic Operations** - All-or-nothing, ensures data consistency  
✅ **Better Performance** - Reduces database round trips  
✅ **Existing Pattern** - Matches how async methods and API endpoints cache data  

## Impact Assessment

### Before Fix
- ❌ Data was **not cached** to database
- ❌ Every topology query hit devices again
- ❌ No persistent storage
- ❌ Slower performance
- ✅ Discovery still **worked** (data returned to API)

### After Fix
- ✅ Data **cached to database**
- ✅ Subsequent queries use cache
- ✅ Persistent topology history
- ✅ Faster performance
- ✅ Discovery works **and** caches

## Testing

### 1. Restart Worker
```bash
cd backend && python3 start_worker.py
```

### 2. Run Discovery
- Select 3+ devices in UI
- Choose "Asynchronous (Background via Celery)"
- Click "Start Discovery"

### 3. Expected Worker Logs
```
✅ Cached 1 static routes for device 3ec64b79-aa33-46be-b9c2-6a5aa9ea6381
✅ Cached 1 OSPF routes for device 3ec64b79-aa33-46be-b9c2-6a5aa9ea6381
✅ Cached 17 MAC entries for device c2029692-5e8d-4447-9f1e-c7fc90ba396f
✅ Cached 2 CDP neighbors for device c2029692-5e8d-4447-9f1e-c7fc90ba396f
```

No more `'DeviceCacheService' object has no attribute...` errors!

### 4. Verify Database
```sql
-- Check cached data
SELECT COUNT(*) FROM static_route_cache;
SELECT COUNT(*) FROM ospf_route_cache;
SELECT COUNT(*) FROM bgp_route_cache;
SELECT COUNT(*) FROM mac_address_table_cache;
SELECT COUNT(*) FROM cdp_neighbor_cache;

-- View sample cached CDP neighbors
SELECT device_id, neighbor_name, neighbor_ip, local_interface 
FROM cdp_neighbor_cache 
ORDER BY last_updated DESC 
LIMIT 10;
```

## File Changed

- `backend/app/services/topology_discovery_service.py`
  - `_cache_static_routes_sync()` - Fixed to use `bulk_replace_static_routes`
  - `_cache_ospf_routes_sync()` - Fixed to use `bulk_replace_ospf_routes`
  - `_cache_bgp_routes_sync()` - Fixed to use `bulk_replace_bgp_routes`
  - `_cache_mac_table_sync()` - Fixed to use `bulk_replace_mac_table`
  - `_cache_cdp_neighbors_sync()` - Fixed to use `bulk_replace_cdp_neighbors`

## Related Issues

This was discovered after fixing the Celery deadlock issue. The errors became visible once tasks started executing successfully.

## Answer to "Should We Fix It?"

**YES!** These errors were non-critical for Celery functionality but **critical for the cache system**:

1. **Data Persistence** - Without caching, topology data is lost after each query
2. **Performance** - Every view hits devices, causing slow response times
3. **Topology Builder** - Needs cached data to build topology graphs
4. **Historical Analysis** - Can't compare topologies over time without cache
5. **Offline Mode** - Can't show topology when devices are unreachable

The fix ensures discovered data is **properly cached**, enabling all downstream features that depend on cached topology data.

---

**Status:** ✅ Fixed  
**Date:** October 5, 2025  
**Related:** CELERY_GROUP_FIX.md
