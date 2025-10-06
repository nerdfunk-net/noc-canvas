# Bug Fix: Topology Discovery Cache Foreign Key Violation

## Date
October 6, 2025

## Issue Description

After fixing the `network_driver` KeyError, topology discovery successfully executed device commands but failed when trying to cache the results with a foreign key violation error:

```
(psycopg2.errors.ForeignKeyViolation) insert or update on table "static_route_cache" 
violates foreign key constraint "static_route_cache_device_id_fkey"
DETAIL:  Key (device_id)=(3ec64b79-aa33-46be-b9c2-6a5aa9ea6381) is not present in table "device_cache".
```

Additionally, after the first caching error, all subsequent cache operations failed with:

```
sqlalchemy.exc.PendingRollbackError: This Session's transaction has been rolled back 
due to a previous exception during flush.
```

## Root Cause Analysis

### Problem 1: Missing Device Cache Entry

The database schema has a parent-child relationship:

```
device_cache (parent)
├── static_route_cache (child)
├── ospf_route_cache (child)
├── bgp_route_cache (child)
├── mac_address_table_cache (child)
├── cdp_neighbor_cache (child)
├── arp_cache (child)
└── interface_cache (child)
```

All child tables have **foreign key constraints** referencing `device_cache.device_id`:

```python
device_id = Column(String, ForeignKey("device_cache.device_id", ondelete="CASCADE"), nullable=False)
```

**The topology discovery was attempting to insert child records WITHOUT first creating the parent `DeviceCache` record**, violating the foreign key constraint.

### Problem 2: Database Session Not Recovered After Error

When the first cache operation failed (static routes), the SQLAlchemy session entered an error state. All subsequent cache operations failed with `PendingRollbackError` because the session wasn't rolled back to recover from the error.

This caused a cascade of failures:
1. Static routes fail → session in error state
2. OSPF routes fail → can't use session
3. BGP routes fail → can't use session
4. CDP neighbors fail → can't use session
5. ARP entries fail → can't use session
6. Interfaces fail → can't use session
7. Final `db.commit()` fails → entire task fails

## The Fix

### Fix 1: Ensure Device Cache Entry Exists

Added logic to `discover_device_data_sync()` to create/update the `DeviceCache` entry **before** attempting to cache any child data:

```python
# Ensure device cache entry exists before caching any data
if cache_results:
    try:
        # Extract username from token
        username = TopologyDiscoveryService._get_username_from_token(auth_token)
        
        # Get device info from Nautobot
        async def get_device_info():
            return await nautobot_service.get_device(device_id, username)
        
        device_info = asyncio.run(get_device_info())
        
        if device_info:
            # Extract fields from nested GraphQL structure
            primary_ip4 = device_info.get("primary_ip4")
            primary_ip = primary_ip4["address"].split("/")[0] if primary_ip4 and primary_ip4.get("address") else None
            
            platform_info = device_info.get("platform")
            platform = platform_info.get("name") if platform_info else None
            
            # Create or update device cache entry
            device_cache_data = DeviceCacheCreate(
                device_id=device_id,
                device_name=device_info.get("name", ""),
                primary_ip=primary_ip,
                platform=platform
            )
            device_cache_service.get_or_create_device_cache(db, device_cache_data)
            logger.info(f"✅ Device cache entry ensured for {device_id}")
    except Exception as e:
        logger.error(f"❌ Failed to create device cache entry: {e}")
        # Continue anyway - data will still be returned
```

This ensures that:
1. The parent `DeviceCache` record exists before any child inserts
2. Uses `get_or_create_device_cache()` to handle both new and existing devices
3. Continues even if cache creation fails (data collection still works)

### Fix 2: Rollback Session After Each Cache Error

Added `db.rollback()` to all synchronous cache methods to recover the session after errors:

```python
@staticmethod
def _cache_static_routes_sync(db: Session, device_id: str, routes: List[Dict[str, Any]]):
    """Synchronous cache method for static routes."""
    try:
        cache_entries = []
        # ... build cache entries ...
        if cache_entries:
            device_cache_service.bulk_replace_static_routes(db, device_id, cache_entries)
    except Exception as e:
        logger.error(f"Failed to cache static routes for {device_id}: {e}")
        db.rollback()  # ← Added: Reset session to recover from error
```

Applied to all cache methods:
- `_cache_static_routes_sync()`
- `_cache_ospf_routes_sync()`
- `_cache_bgp_routes_sync()`
- `_cache_mac_table_sync()`
- `_cache_cdp_neighbors_sync()`
- `_cache_arp_entries_sync()`
- `_cache_interfaces_sync()`

This ensures:
1. Each cache operation is independent
2. If one cache operation fails, others can still succeed
3. The database session remains usable
4. Non-critical failures don't prevent data collection

## Files Modified

### `backend/app/services/topology_discovery_service.py`

1. **Added import**:
   ```python
   from ..schemas.device_cache import (
       DeviceCacheCreate,  # ← Added
       StaticRouteCacheCreate, OSPFRouteCacheCreate, ...
   )
   ```

2. **Modified `discover_device_data_sync()`**:
   - Added device cache initialization logic at the start
   - Creates parent `DeviceCache` record before child inserts

3. **Modified all `_cache_*_sync()` methods**:
   - Added `db.rollback()` in exception handlers
   - Ensures session recovery after errors

## Testing

After the fix, topology discovery should:
1. ✅ Create `DeviceCache` entry for each device
2. ✅ Successfully cache static routes
3. ✅ Successfully cache OSPF routes
4. ✅ Successfully cache BGP routes  
5. ✅ Successfully cache MAC address table
6. ✅ Successfully cache CDP neighbors
7. ✅ Successfully cache ARP entries
8. ✅ Successfully cache interfaces
9. ✅ Continue even if individual cache operations fail
10. ✅ Return discovery data even if caching fails

## Database Schema Relationships

```
device_cache
├── device_id (PK)
├── device_name
├── primary_ip
├── platform
└── ...

static_route_cache
├── id (PK)
├── device_id (FK → device_cache.device_id)  ← Foreign Key
├── network
└── ...

arp_cache
├── id (PK)
├── device_id (FK → device_cache.device_id)  ← Foreign Key
├── ip_address
└── ...

... (all other cache tables follow same pattern)
```

**Key Insight**: Parent must exist before children!

## Lessons Learned

1. **Database Integrity**: Always ensure parent records exist before inserting child records
2. **Transaction Management**: Use `db.rollback()` to recover from errors in non-critical operations
3. **Fail Gracefully**: Cache failures shouldn't prevent data collection
4. **Atomic Operations**: Make each cache operation independent and recoverable
5. **Order Matters**: Create parent records first, then children

## Related Issues

- Previous fix: `BUGFIX_TOPOLOGY_DISCOVERY_NETWORK_DRIVER.md`
- Database models: `backend/app/models/device_cache.py`
- Cache service: `backend/app/services/device_cache_service.py`

## Impact

- **Scope**: Only affects Celery worker background tasks with caching enabled
- **Risk**: Low - defensive programming with rollbacks ensures stability
- **Performance**: Minimal - one additional Nautobot query per device for cache initialization
- **Data Integrity**: High - proper foreign key relationships maintained
