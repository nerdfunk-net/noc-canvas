# Added Device Interfaces and ARP Entries Checkboxes to Topology Discovery UI

## Problem Description

The "Discover Topology" modal was missing checkboxes for two data types that were already supported by the backend:
1. **Device Interfaces** - Always discovered (hardcoded to `true`)
2. **ARP Entries** - Always discovered (hardcoded to `true`)

Users had no way to disable discovery of these data types from the UI.

## Changes Made

### Frontend: `frontend/src/components/TopologyDiscoveryModal.vue`

**1. Added Two New Checkboxes to UI (Lines 57-82)**

Added checkboxes at the **top** of the "Data to Discover" section:
- ✅ **Device Interfaces** - checkbox for `includeInterfaces`
- ✅ **ARP Entries** - checkbox for `includeArp`

**Layout Now (7 checkboxes in 2 columns):**
```
┌─────────────────────────┬─────────────────────────┐
│ ☑ Device Interfaces     │ ☑ ARP Entries          │
│ ☑ Static Routes         │ ☑ OSPF Routes          │
│ ☑ BGP Routes            │ ☑ MAC Address Table    │
│ ☑ CDP Neighbors         │                         │
└─────────────────────────┴─────────────────────────┘
```

**2. Updated Validation Logic (Lines 348-351)**

Updated `hasDataSelected` computed property to include the new checkboxes:

**Before:**
```typescript
const hasDataSelected = computed(() => {
  return includeStaticRoutes.value || includeOspfRoutes.value || 
         includeBgpRoutes.value || includeMacTable.value || 
         includeCdpNeighbors.value
})
```

**After:**
```typescript
const hasDataSelected = computed(() => {
  return includeInterfaces.value || includeArp.value || 
         includeStaticRoutes.value || includeOspfRoutes.value || 
         includeBgpRoutes.value || includeMacTable.value || 
         includeCdpNeighbors.value
})
```

### Backend: No Changes Needed ✅

The backend already supports these parameters:
- **`async_discovery.py`**: `include_interfaces` and `include_arp` parameters exist with default `True`
- **`sync_discovery.py`**: Same parameters with default `True`
- **API endpoints**: Already accept these parameters in POST body

**Frontend was already sending these values** (lines 396-397):
```typescript
include_arp: includeArp.value,
include_interfaces: includeInterfaces.value,
```

## Impact

### Before
- ❌ "Device Interfaces" not visible in UI
- ❌ "ARP Entries" not visible in UI  
- ❌ Both always discovered (couldn't be disabled)
- ❌ Only 5 checkboxes visible

### After
- ✅ "Device Interfaces" checkbox visible and functional
- ✅ "ARP Entries" checkbox visible and functional
- ✅ Users can enable/disable both data types
- ✅ 7 checkboxes total (complete control)
- ✅ "Start Discovery" button disabled if no data types selected

## User Experience

Users can now:
1. **Selectively discover data** - Uncheck "Device Interfaces" if only interested in routing data
2. **Faster discovery** - Skip interfaces/ARP for quick topology checks
3. **Reduce cache usage** - Don't cache interface data if not needed
4. **Better control** - Choose exactly what data to discover

## Default Behavior

All checkboxes are **checked by default** (`ref(true)`), maintaining backward compatibility:
- ✅ Device Interfaces: `true`
- ✅ ARP Entries: `true`
- ✅ Static Routes: `true`
- ✅ OSPF Routes: `true`
- ✅ BGP Routes: `true`
- ✅ MAC Address Table: `true`
- ✅ CDP Neighbors: `true`

## Testing

To test the new functionality:
1. Open Topology Discovery modal
2. Verify all 7 checkboxes are visible
3. Uncheck "Device Interfaces" and "ARP Entries"
4. Start discovery
5. Verify only selected data types are discovered
6. Check backend logs to confirm parameters are received correctly

## Technical Details

**Frontend Variables (already existed, just exposed in UI):**
```typescript
const includeInterfaces = ref(true)  // Line 317
const includeArp = ref(true)          // Line 316
```

**Backend Parameters (already existed):**
```python
# async_discovery.py, line 117-118
include_arp: bool = True,
include_interfaces: bool = True,

# sync_discovery.py, similar parameters exist
```

**API Request Body:**
```json
{
  "device_ids": ["uuid1", "uuid2"],
  "include_interfaces": true,
  "include_arp": true,
  "include_static_routes": true,
  "include_ospf_routes": true,
  "include_bgp_routes": true,
  "include_mac_table": true,
  "include_cdp_neighbors": true,
  "cache_results": true
}
```

## Files Modified

- **`frontend/src/components/TopologyDiscoveryModal.vue`**:
  - Added 2 new checkboxes to UI (lines 57-82)
  - Updated `hasDataSelected` validation (lines 348-351)

## Date

Implemented: October 7, 2025
