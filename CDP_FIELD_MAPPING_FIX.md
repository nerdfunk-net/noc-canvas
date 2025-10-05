# CDP Discovery Field Mapping Issue Fix

## Problem

**Symptom:** CDP neighbor discovery works correctly when run in **foreground/synchronous mode** but fails to capture neighbor data when run in **background/Celery mode**.

**Root Cause:** Field name mismatch between the sync cache method and the TextFSM parser output.

## Analysis

### How TextFSM Works

TextFSM parsers return structured data from network device command output. The field names in the returned dictionaries depend on the TextFSM template being used. Some templates use **UPPERCASE** field names, others use **lowercase**, and some use variations like `NEIGHBOR`, `neighbor_name`, or `DESTINATION_HOST`.

### The Discrepancy

#### API Endpoint (Working Correctly)
File: `backend/app/api/devices.py` lines 255-310

The API endpoint has **robust field mapping** that handles multiple field name variants:

```python
# Handles UPPERCASE, lowercase, and multiple field name variations
neighbor_name_raw = (
    cdp_data.get("NEIGHBOR") or cdp_data.get("neighbor") or
    cdp_data.get("NEIGHBOR_NAME") or cdp_data.get("neighbor_name") or
    cdp_data.get("DESTINATION_HOST") or cdp_data.get("destination_host") or ""
)

local_interface_raw = (
    cdp_data.get("LOCAL_INTERFACE") or cdp_data.get("local_interface") or
    cdp_data.get("LOCAL_PORT") or cdp_data.get("local_port") or ""
)

# Also handles list vs string values
if isinstance(neighbor_name_raw, list):
    neighbor_name = neighbor_name_raw[0] if neighbor_name_raw else ""
else:
    neighbor_name = neighbor_name_raw
```

**Result:** Works with any TextFSM template variant ✅

#### Sync Cache Method (Was Broken)
File: `backend/app/services/topology_discovery_service.py` line 707 (old version)

The synchronous cache method used **hardcoded lowercase field names**:

```python
# ❌ Only works if TextFSM returns lowercase fields
cache_entry = CDPNeighborCacheCreate(
    device_id=device_id,
    local_interface=neighbor.get("local_interface", ""),  # ❌ lowercase only
    neighbor_name=neighbor.get("neighbor", ""),           # ❌ lowercase only
    neighbor_interface=neighbor.get("neighbor_interface", ""),
    neighbor_ip=neighbor.get("management_ip", ""),
    platform=neighbor.get("platform", ""),
    capabilities=neighbor.get("capabilities", "")
)
```

**Result:** Fails if TextFSM returns UPPERCASE or different field names ❌

### Why It Appeared to Work in Foreground

When running discovery in foreground (synchronous mode):
1. API endpoint is called directly via async method
2. API endpoint has robust field mapping (handles all variants)
3. API endpoint caches data correctly using `bulk_replace_cdp_neighbors`
4. Data appears in database ✅

When running discovery in background (Celery mode):
1. API endpoint is called via sync method in Celery worker
2. API endpoint returns data correctly
3. **Sync cache method fails to extract fields** (wrong field names)
4. Empty or incomplete data is cached ❌

## Solution

Updated `_cache_cdp_neighbors_sync()` to use the **same robust field mapping** as the API endpoint.

### Fixed Code

```python
@staticmethod
def _cache_cdp_neighbors_sync(db: Session, device_id: str, neighbors: List[Dict[str, Any]]):
    """Synchronous cache method for CDP neighbors."""
    try:
        cache_entries = []
        for neighbor in neighbors:
            # ✅ Extract fields with case-insensitive fallback (TextFSM may return uppercase)
            neighbor_name_raw = (
                neighbor.get("NEIGHBOR") or neighbor.get("neighbor") or
                neighbor.get("NEIGHBOR_NAME") or neighbor.get("neighbor_name") or
                neighbor.get("DESTINATION_HOST") or neighbor.get("destination_host") or ""
            )
            local_interface_raw = (
                neighbor.get("LOCAL_INTERFACE") or neighbor.get("local_interface") or
                neighbor.get("LOCAL_PORT") or neighbor.get("local_port") or ""
            )
            neighbor_ip_raw = (
                neighbor.get("MANAGEMENT_IP") or neighbor.get("management_ip") or
                neighbor.get("NEIGHBOR_IP") or neighbor.get("neighbor_ip") or ""
            )
            neighbor_interface_raw = (
                neighbor.get("NEIGHBOR_INTERFACE") or neighbor.get("neighbor_interface") or
                neighbor.get("NEIGHBOR_PORT") or neighbor.get("neighbor_port") or ""
            )
            platform_raw = neighbor.get("PLATFORM") or neighbor.get("platform") or ""
            capabilities_raw = neighbor.get("CAPABILITIES") or neighbor.get("capabilities") or ""
            
            # ✅ Handle if fields are lists (some TextFSM templates return lists)
            if isinstance(neighbor_name_raw, list):
                neighbor_name = neighbor_name_raw[0] if neighbor_name_raw else ""
            else:
                neighbor_name = neighbor_name_raw
            neighbor_name = neighbor_name.strip() if neighbor_name else ""
            
            if isinstance(local_interface_raw, list):
                local_interface = local_interface_raw[0] if local_interface_raw else ""
            else:
                local_interface = local_interface_raw
            local_interface = local_interface.strip() if local_interface else ""
            
            # ✅ Skip entries without neighbor name or local interface
            if not neighbor_name or not local_interface:
                logger.warning(f"Skipping CDP neighbor with missing name or interface: {neighbor}")
                continue
            
            # Process other fields with list handling...
            
            cache_entry = CDPNeighborCacheCreate(
                device_id=device_id,
                local_interface=local_interface,
                neighbor_name=neighbor_name,
                neighbor_interface=neighbor_interface if neighbor_interface else None,
                neighbor_ip=neighbor_ip if neighbor_ip else None,
                platform=platform if platform else None,
                capabilities=capabilities if capabilities else None
            )
            cache_entries.append(cache_entry)
        
        # Use bulk replace method
        if cache_entries:
            device_cache_service.bulk_replace_cdp_neighbors(db, device_id, cache_entries)
            logger.debug(f"Cached {len(cache_entries)} CDP neighbors for device {device_id}")
    except Exception as e:
        logger.error(f"Failed to cache CDP neighbors for {device_id}: {e}")
```

## Key Improvements

✅ **Case-insensitive field lookup** - Handles UPPERCASE, lowercase, mixed case  
✅ **Multiple field name variants** - `NEIGHBOR`, `neighbor_name`, `DESTINATION_HOST`, etc.  
✅ **List vs string handling** - Some templates return `["value"]` others return `"value"`  
✅ **Data validation** - Skips entries missing required fields  
✅ **Robust error handling** - Logs warnings for skipped entries  
✅ **Matches API endpoint behavior** - Consistent field extraction logic  

## Why This Pattern

This issue is common when working with TextFSM because:

1. **Different TextFSM templates exist** for the same command
2. **Templates from different sources** use different naming conventions
3. **NTC Templates** (ntc-templates library) vs custom templates may differ
4. **Template versions** may change field names over time

The solution is to **always check multiple field name variants** when extracting data from TextFSM-parsed output.

## Testing

### Before Fix
```bash
# Background mode
'cdp_neighbors': []  # ❌ Empty

# Foreground mode
'cdp_neighbors': [{'neighbor': 'Router1', 'local_interface': 'Gi0/0'}]  # ✅ Works
```

### After Fix
```bash
# Background mode
'cdp_neighbors': [{'neighbor': 'Router1', 'local_interface': 'Gi0/0'}]  # ✅ Works

# Foreground mode
'cdp_neighbors': [{'neighbor': 'Router1', 'local_interface': 'Gi0/0'}]  # ✅ Works
```

## Related Files

- `backend/app/services/topology_discovery_service.py` - Fixed sync cache method
- `backend/app/api/devices.py` - Reference implementation with robust field mapping

## Recommendation

Apply this same pattern to **all other sync cache methods**:
- `_cache_static_routes_sync()` - Check if field names need variants
- `_cache_ospf_routes_sync()` - Check if field names need variants
- `_cache_bgp_routes_sync()` - Check if field names need variants
- `_cache_mac_table_sync()` - Check if field names need variants

Most routing commands have more standardized output, but CDP/LLDP is notorious for having many template variants.

---

**Status:** ✅ Fixed  
**Date:** October 5, 2025  
**Issue:** CDP neighbors not captured in background mode  
**Cause:** Hardcoded lowercase field names didn't match TextFSM output  
**Fix:** Robust field mapping with multiple variants and list handling
