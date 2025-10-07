# Fixed IP Address Caching in Sync Topology Discovery

## Problem Description

When using **Celery mode (sync discovery)** to discover interfaces, IP addresses were **NOT being cached** to the topology cache database, while the **async mode** had the same issue.

### Symptoms

**Celery Worker Log Output:**
```
[2025-10-07 20:43:26,366: INFO/ForkPoolWorker-4] ✅ Got 4 interfaces
[2025-10-07 20:43:26,376: INFO/ForkPoolWorker-4] ✅ Sync discovery completed for device 3ec64b79-aa33-46be-b9c2-6a5aa9ea6381
```

**Expected behavior:** IP addresses should be cached along with interfaces
**Actual behavior:** IP addresses were silently skipped

## Root Cause

Both `_cache_interfaces_sync()` and `_cache_interfaces_async()` methods were **skipping IP address caching** with debug logs:

```python
# Skipping IP address caching for now as bulk method doesn't exist
if ip_entries:
    logger.debug(
        f"Skipping {len(ip_entries)} IP addresses (bulk method not implemented)"
    )
```

**However**, the `bulk_upsert_ips()` method **DOES EXIST** in `device_cache_service.py` (line 278):

```python
@staticmethod
def bulk_upsert_ips(
    db: Session, device_id: str, ip_addresses: List[IPAddressCacheCreate]
) -> None:
    """Bulk insert/update IP addresses for a device."""
    # Delete existing IPs not in the new list
    new_ips = [(ip.interface_name, ip.ip_address) for ip in ip_addresses]
    existing = db.query(IPAddressCache).filter(
        IPAddressCache.device_id == device_id
    ).all()

    for existing_ip in existing:
        if (existing_ip.interface_name, existing_ip.ip_address) not in new_ips:
            db.delete(existing_ip)

    # Upsert each IP
    for ip_data in ip_addresses:
        DeviceCacheService.upsert_ip_address(db, ip_data)
```

The comment was **outdated** - the bulk method was implemented but never used!

## Solution

### Changed Files

1. **`backend/app/services/topology_discovery/sync_discovery.py`** (lines 897-909)
2. **`backend/app/services/topology_discovery/async_discovery.py`** (lines 917-929)

### Changes Made

Replaced the "skipping" logic with actual IP address caching:

**Before:**
```python
# Note: IP address caching would need upsert_ip_address method
# Skipping IP address caching for now as bulk method doesn't exist
if ip_entries:
    logger.debug(
        f"Skipping {len(ip_entries)} IP addresses (bulk method not implemented)"
    )
```

**After:**
```python
# Cache IP addresses using bulk upsert
if ip_entries:
    device_cache_service.bulk_upsert_ips(db, device_id, ip_entries)
    logger.debug(
        f"Cached {len(ip_entries)} IP addresses for device {device_id}"
    )
```

## Impact

### Before
- ❌ Interfaces cached, but **IP addresses silently skipped**
- ❌ No IP address data in topology cache
- ❌ Incomplete device network information
- ❌ Same issue in both sync (Celery) and async (API) modes

### After
- ✅ Interfaces cached with **complete IP address data**
- ✅ IP addresses stored in `ip_address_cache` table
- ✅ Full network topology information available
- ✅ Both sync and async modes cache IP addresses correctly

## Technical Details

### IP Address Parsing

IP addresses are extracted from interface data during discovery:

```python
# Create IP address entries if present
ip_address = iface.get("ip_address")
if ip_address and ip_address != "unassigned":
    # Parse IP and subnet mask if in CIDR format (e.g., "10.0.0.1/24")
    subnet_mask = None
    if "/" in ip_address:
        ip_addr, prefix = ip_address.split("/")
        ip_address = ip_addr
        subnet_mask = prefix  # Store as prefix length

    ip_entry = IPAddressCacheCreate(
        device_id=device_id,
        interface_id=None,  # Will be linked by interface_name
        interface_name=iface.get("name") or iface.get("interface", ""),
        ip_address=ip_address,
        subnet_mask=subnet_mask,
        ip_version=4 if "." in ip_address else 6,  # Auto-detect IPv4/IPv6
        is_primary=False,
    )
    ip_entries.append(ip_entry)
```

### Cache Operation

The `bulk_upsert_ips()` method:
1. **Deletes** IP addresses that are no longer present
2. **Updates** IP addresses that changed
3. **Inserts** new IP addresses discovered

This ensures the cache always reflects the current device state.

## Expected Log Output

**After fix, you should see:**
```
[2025-10-07 20:43:26,366: INFO/ForkPoolWorker-4] ✅ Got 4 interfaces
[2025-10-07 20:43:26,366: DEBUG/ForkPoolWorker-4] Cached 4 interfaces for device 3ec64b79-aa33-46be-b9c2-6a5aa9ea6381
[2025-10-07 20:43:26,367: DEBUG/ForkPoolWorker-4] Cached 2 IP addresses for device 3ec64b79-aa33-46be-b9c2-6a5aa9ea6381
[2025-10-07 20:43:26,376: INFO/ForkPoolWorker-4] ✅ Sync discovery completed for device 3ec64b79-aa33-46be-b9c2-6a5aa9ea6381
```

## Testing

To verify the fix:

1. **Clear existing cache:**
   ```bash
   # Delete IP address cache entries for testing
   sqlite3 backend/noc_canvas.db "DELETE FROM ip_address_cache;"
   ```

2. **Run topology discovery:**
   - Use Celery mode (sync) or API mode (async)
   - Select "Device Interfaces" checkbox
   - Start discovery

3. **Verify IP addresses cached:**
   ```bash
   # Check IP address cache table
   sqlite3 backend/noc_canvas.db "SELECT device_id, interface_name, ip_address, subnet_mask FROM ip_address_cache;"
   ```

4. **Expected result:**
   - Interface data in `interface_cache` table
   - IP address data in `ip_address_cache` table
   - Linked by `device_id` and `interface_name`

## Related Files

- **`backend/app/services/device_cache_service.py`**: Contains `bulk_upsert_ips()` method
- **`backend/app/models/device_cache.py`**: Defines `IPAddressCache` SQLAlchemy model
- **`backend/app/schemas/device_cache.py`**: Defines `IPAddressCacheCreate` Pydantic schema

## Notes

- Both **sync** and **async** discovery modes now cache IP addresses correctly
- The `bulk_upsert_ips()` method handles updates, inserts, and deletions
- IP addresses are linked to interfaces via `interface_name` (not foreign key)
- Supports both **IPv4** and **IPv6** addresses (auto-detected)
- CIDR notation is parsed into separate `ip_address` and `subnet_mask` fields

## Date

Fixed: October 7, 2025
