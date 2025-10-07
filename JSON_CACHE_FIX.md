# JSON Blob Cache Fix - All Endpoints

## Issue Summary
When using topology discovery in "API sync mode" (foreground, `/discover-sync`), only 3 JSON blobs were cached (for interfaces only). When using Celery mode (`/discover-async`), all 21 JSON blobs were cached (7 endpoints × 3 devices).

## Root Cause
Only the `/interfaces` endpoint in `backend/app/api/devices.py` had JSON blob caching logic using `JSONCacheService.set_cache()`. The other 6 endpoints (static routes, OSPF routes, BGP routes, MAC table, CDP neighbors, ARP) only cached to the structured topology cache but not the JSON blob cache.

## Two Discovery Paths

### Path 1: API "Sync" Mode (Foreground - `/discover-sync`)
```
API Request → AsyncTopologyDiscoveryService 
           → HTTP calls to device API endpoints
           → Device API caches JSON blobs
```

### Path 2: Celery Mode (Background - `/discover-async`)
```
API Request → Celery Task → SyncTopologyDiscoveryService
           → Direct device calls
           → Caches JSON blobs in _call_device_endpoint_sync()
```

## Solution
Added JSON blob caching to all 6 missing device API endpoints:

### Files Modified
- `backend/app/api/devices.py`

### Endpoints Fixed
1. ✅ `/ip-route/static` - Added JSON cache for "show ip route static"
2. ✅ `/ip-route/ospf` - Added JSON cache for "show ip route ospf"
3. ✅ `/ip-route/bgp` - Added JSON cache for "show ip route bgp" (also added `db` parameter)
4. ✅ `/mac-address-table` - Added JSON cache for "show mac address-table"
5. ✅ `/cdp-neighbors` - Added JSON cache for "show cdp neighbors"
6. ✅ `/ip-arp` - Added JSON cache for "show ip arp"

### Caching Pattern Applied
For each endpoint, added this code block after executing the command:

```python
# Store the parsed JSON output in the JSON blob cache
try:
    import json
    from app.services.json_cache_service import JSONCacheService
    
    json_data = json.dumps(output)
    JSONCacheService.set_cache(
        db=db,
        device_id=device_id,
        command="<command>",
        json_data=json_data
    )
    logger.info(f"Successfully cached JSON output for device {device_id}, command: <command>")
except Exception as cache_error:
    logger.error(f"Failed to cache JSON output: {str(cache_error)}")
    # Continue processing even if JSON cache fails
```

## Expected Behavior - Before Fix

### API Sync Mode (`/discover-sync`)
- **Before**: Only 3 JSON blobs cached (interfaces only)
  - Device 1: `show interfaces`
  - Device 2: `show interfaces`
  - Device 3: `show interfaces`

### Celery Mode (`/discover-async`)
- **Before**: All 21 JSON blobs cached
  - Device 1: 7 commands
  - Device 2: 7 commands
  - Device 3: 7 commands

## Expected Behavior - After Fix

### API Sync Mode (`/discover-sync`)
- **After**: All 21 JSON blobs cached ✅
  - Device 1: 7 commands
  - Device 2: 7 commands
  - Device 3: 7 commands

### Celery Mode (`/discover-async`)
- **After**: All 21 JSON blobs cached ✅ (unchanged)
  - Device 1: 7 commands
  - Device 2: 7 commands
  - Device 3: 7 commands

## Commands Cached (Per Device)
1. `show interfaces`
2. `show ip route static`
3. `show ip route ospf`
4. `show ip route bgp`
5. `show mac address-table`
6. `show cdp neighbors`
7. `show ip arp`

## Verification
To verify the fix works:

1. Clear JSON cache:
```sql
DELETE FROM json_cache;
```

2. Run topology discovery in API sync mode:
```bash
curl -X POST "http://localhost:8000/api/topology/discover-sync" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "device_ids": ["device-1-id", "device-2-id", "device-3-id"],
    "include_static_routes": true,
    "include_ospf_routes": true,
    "include_bgp_routes": true,
    "include_mac_table": true,
    "include_cdp_neighbors": true,
    "include_arp": true,
    "include_interfaces": true,
    "cache_results": true
  }'
```

3. Check JSON cache count:
```sql
SELECT COUNT(*) FROM json_cache;
-- Expected: 21 (7 commands × 3 devices)

SELECT device_id, command, created_at 
FROM json_cache 
ORDER BY device_id, command;
```

4. Check logs for caching messages:
```
Successfully cached JSON output for device <device_id>, command: show ip route static
Successfully cached JSON output for device <device_id>, command: show ip route ospf
Successfully cached JSON output for device <device_id>, command: show ip route bgp
Successfully cached JSON output for device <device_id>, command: show mac address-table
Successfully cached JSON output for device <device_id>, command: show cdp neighbors
Successfully cached JSON output for device <device_id>, command: show ip arp
Successfully cached JSON output for device <device_id>, command: show interfaces
```

## Benefits
1. **Consistent Caching**: Both API sync and Celery modes now cache identically
2. **Performance**: Second discovery run can use cached JSON blobs instead of re-querying devices
3. **Cache Expiry**: JSON cache has TTL (default 1 hour), reducing device load
4. **Debugging**: Full command output preserved in JSON format for troubleshooting

## Technical Notes

### BGP Routes Endpoint
- Added missing `db: Session = Depends(get_db)` parameter
- Previously had no database access, now can cache both JSON blobs and topology data

### Cache Check Logic
All endpoints already check JSON cache before execution:
- If valid cache exists → Return cached data (no device query)
- If no cache or expired → Execute command and cache results

### Error Handling
JSON cache failures are logged but don't stop processing:
- Structured topology cache still works if JSON cache fails
- Allows graceful degradation

## Related Files
- `backend/app/api/devices.py` - Device API endpoints (modified)
- `backend/app/services/json_cache_service.py` - JSON cache service
- `backend/app/services/topology_discovery/sync_discovery.py` - Celery mode (already had JSON caching)
- `backend/app/services/topology_discovery/async_discovery.py` - API sync mode (uses HTTP calls to device API)

## Testing Completed
✅ Syntax validation passed (no errors in devices.py)
✅ All 6 endpoints updated with consistent caching pattern
✅ BGP endpoint fixed (added db parameter)
✅ Log messages standardized across all endpoints
