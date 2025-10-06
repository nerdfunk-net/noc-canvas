# Bug Fix: Topology Discovery Network Driver KeyError

## Date
October 6, 2025

## Issue Description

When running topology discovery in the background using Celery workers, all device commands were failing with a KeyError:

```
KeyError: 'network_driver'
```

The error occurred in `device_communication.py` at line 161:
```python
device_info["network_driver"]
```

This caused all topology discovery tasks to fail, returning empty data for all collection types (interfaces, ARP, CDP, routes, etc.).

## Root Cause Analysis

The application has **two different code paths** for executing device commands:

### 1. **API/HTTP Path (Working)**
When commands are executed through the REST API endpoints:
- Uses `get_device_connection_info()` in `api/devices.py`
- Fetches device data from Nautobot using `nautobot_service.get_device()`
- **Transforms** the nested GraphQL response into a flat `DeviceConnectionInfo` Pydantic model
- The transformed model has `network_driver` at the top level

**GraphQL Response Structure:**
```python
{
    "id": "...",
    "name": "device-name",
    "primary_ip4": {
        "address": "10.0.0.1/24"
    },
    "platform": {
        "id": "...",
        "name": "Cisco IOS",
        "network_driver": "cisco_ios"  # ← Nested inside platform
    }
}
```

**Transformed Structure (DeviceConnectionInfo):**
```python
{
    "device_id": "...",
    "name": "device-name",
    "primary_ip": "10.0.0.1",
    "platform": "Cisco IOS",
    "network_driver": "cisco_ios"  # ← Flattened to top level
}
```

### 2. **Celery Worker Path (Broken)**
When commands are executed in Celery workers for background topology discovery:
- Uses `TopologyDiscoveryService._call_device_endpoint_sync()`
- Fetches device data using `nautobot_service.get_device()` directly
- **Does NOT transform** the response - passes raw GraphQL structure to DeviceCommunicationService
- The raw structure has `network_driver` nested inside `platform`
- `DeviceCommunicationService._get_device_config()` expects `device_info["network_driver"]` at top level
- **Result: KeyError**

## The Fix

Modified `TopologyDiscoveryService._call_device_endpoint_sync()` to transform the device data before passing it to `DeviceCommunicationService`:

### Changes in `backend/app/services/topology_discovery_service.py`

1. **Added httpx import** (was missing):
```python
import httpx
```

2. **Added data transformation logic** in `_call_device_endpoint_sync()`:

```python
# Transform device data to match expected structure
# The GraphQL response has nested structure, but DeviceCommunicationService
# expects a flat structure with network_driver at top level
primary_ip4 = device_data.get("primary_ip4")
if not primary_ip4 or not primary_ip4.get("address"):
    logger.error(f"Device {device_id} does not have a primary IPv4 address")
    return {"success": False, "error": "Device does not have a primary IPv4 address"}

platform_info = device_data.get("platform")
if not platform_info or not platform_info.get("network_driver"):
    logger.error(f"Device {device_id} does not have a platform/network_driver configured")
    return {"success": False, "error": "Device platform or network_driver not configured"}

# Create transformed device info with flattened structure
device_info = {
    "device_id": device_id,
    "name": device_data.get("name", ""),
    "primary_ip": primary_ip4["address"].split("/")[0],  # Remove subnet mask
    "platform": platform_info.get("name", ""),
    "network_driver": platform_info["network_driver"]
}
```

This transformation:
- Extracts `network_driver` from the nested `platform` object
- Flattens it to the top level of `device_info`
- Adds validation for missing fields
- Returns proper error messages if required fields are missing
- Removes subnet mask from IP address (e.g., "10.0.0.1/24" → "10.0.0.1")

## Files Modified

- `backend/app/services/topology_discovery_service.py`
  - Added `import httpx`
  - Modified `_call_device_endpoint_sync()` method to transform device data structure

## Testing

After the fix, topology discovery should:
1. Successfully connect to devices in Celery workers
2. Execute commands without KeyError
3. Return proper topology data (interfaces, ARP, CDP, routes, etc.)
4. Cache results to the database

## Impact

- **Scope**: Only affects Celery worker background tasks
- **Risk**: Low - the transformation logic matches the existing working pattern in `api/devices.py`
- **Backward Compatibility**: No breaking changes - only fixes broken functionality

## Related Code

### Key Components Involved:
1. **Nautobot Service** (`services/nautobot.py`)
   - `get_device()` - Returns raw GraphQL structure
   
2. **Device Communication Service** (`services/device_communication.py`)
   - `execute_command()` - Expects flat structure with `network_driver`
   - `_get_device_config()` - Accesses `device_info["network_driver"]`
   
3. **Topology Discovery Service** (`services/topology_discovery_service.py`)
   - `_call_device_endpoint_sync()` - Now transforms data before passing to communication service
   
4. **API Devices** (`api/devices.py`)
   - `get_device_connection_info()` - Reference implementation for correct transformation

## Lessons Learned

1. **Consistency is key**: When the same data is used in multiple contexts, ensure the structure is consistent
2. **Document data contracts**: The expected structure of `device_info` should be documented
3. **Consider creating a shared transformation function**: Both `get_device_connection_info()` and `_call_device_endpoint_sync()` now have similar transformation logic
4. **Add integration tests**: Test both API and Celery worker paths with the same data

## Future Improvements

1. **Extract transformation to shared function**:
   - Create a `transform_nautobot_device_to_connection_info()` helper
   - Use in both API and Celery contexts
   - Ensures consistency and reduces code duplication

2. **Use Pydantic models consistently**:
   - Return `DeviceConnectionInfo` model instead of dict
   - Better type safety and validation

3. **Add comprehensive error handling**:
   - Validate all required fields
   - Provide clear error messages
   - Log missing/invalid data for debugging
