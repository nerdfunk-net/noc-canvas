# JSON Blob Cache Testing Guide

## Overview
This guide provides steps to test the JSON blob cache implementation for storing parsed device command outputs.

## Prerequisites
1. Backend server must be running
2. Database must be initialized with `json_blob_cache` table
3. User must be authenticated with valid token
4. At least one network device must be configured with credentials

## Database Setup

The `json_blob_cache` table will be automatically created when the backend starts. It has the following structure:

```sql
CREATE TABLE json_blob_cache (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR NOT NULL,
    command VARCHAR NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    json_data TEXT NOT NULL
);

CREATE INDEX ix_json_blob_device_command ON json_blob_cache (device_id, command);
```

## API Endpoints

### 1. Set/Update Cache Entry (POST)
**Endpoint:** `POST /api/cache/json/{device_id}`

**Request Body:**
```json
{
  "device_id": "uuid-of-device",
  "command": "show interfaces",
  "json_data": "[{\"interface\": \"GigabitEthernet0/0\", \"status\": \"up\"}]"
}
```

**Example cURL:**
```bash
curl -X POST "http://localhost:8000/api/cache/json/your-device-uuid" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "your-device-uuid",
    "command": "show interfaces",
    "json_data": "[{\"interface\": \"GigabitEthernet0/0\"}]"
  }'
```

**Response:**
```json
{
  "id": 1,
  "device_id": "your-device-uuid",
  "command": "show interfaces",
  "updated_at": "2024-01-15T10:30:00Z",
  "json_data": "[{\"interface\": \"GigabitEthernet0/0\"}]"
}
```

### 2. Get Cache Entry (GET)
**Endpoint:** `GET /api/cache/json/{device_id}?command=show%20interfaces`

**Example cURL:**
```bash
# Get specific command cache
curl -X GET "http://localhost:8000/api/cache/json/your-device-uuid?command=show%20interfaces" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get all cached commands for a device
curl -X GET "http://localhost:8000/api/cache/json/your-device-uuid" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response (single command):**
```json
{
  "id": 1,
  "device_id": "your-device-uuid",
  "command": "show interfaces",
  "updated_at": "2024-01-15T10:30:00Z",
  "json_data": "[{\"interface\": \"GigabitEthernet0/0\"}]"
}
```

**Response (all commands):**
```json
[
  {
    "id": 1,
    "device_id": "your-device-uuid",
    "command": "show interfaces",
    "updated_at": "2024-01-15T10:30:00Z",
    "json_data": "[{\"interface\": \"GigabitEthernet0/0\"}]"
  },
  {
    "id": 2,
    "device_id": "your-device-uuid",
    "command": "show version",
    "updated_at": "2024-01-15T10:35:00Z",
    "json_data": "[{\"version\": \"15.1\"}]"
  }
]
```

### 3. Delete Cache Entry (DELETE)
**Endpoint:** `DELETE /api/cache/json/{device_id}?command=show%20interfaces`

**Example cURL:**
```bash
# Delete specific command cache
curl -X DELETE "http://localhost:8000/api/cache/json/your-device-uuid?command=show%20interfaces" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Delete all cached commands for a device
curl -X DELETE "http://localhost:8000/api/cache/json/your-device-uuid" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "message": "Deleted 1 cache entry(ies)",
  "deleted_count": 1
}
```

### 4. List All Cached Devices (GET)
**Endpoint:** `GET /api/cache/json/devices/list`

**Example cURL:**
```bash
curl -X GET "http://localhost:8000/api/cache/json/devices/list" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "devices": [
    "device-uuid-1",
    "device-uuid-2"
  ]
}
```

### 5. List Cached Commands for Device (GET)
**Endpoint:** `GET /api/cache/json/{device_id}/commands`

**Example cURL:**
```bash
curl -X GET "http://localhost:8000/api/cache/json/your-device-uuid/commands" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "commands": [
    "show interfaces",
    "show version"
  ]
}
```

## Integration Testing

### Test 1: Automatic Caching via Interfaces Endpoint

The JSON cache is automatically populated when you fetch interfaces with TextFSM parsing enabled:

**Request:**
```bash
curl -X GET "http://localhost:8000/api/devices/your-device-uuid/interfaces?use_textfsm=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

This will:
1. Execute "show interfaces" on the device
2. Parse output using TextFSM
3. Store the parsed JSON in the cache
4. Store interfaces in the interface cache (as before)
5. Return the parsed data

**Verify Cache was Created:**
```bash
curl -X GET "http://localhost:8000/api/cache/json/your-device-uuid?command=show%20interfaces" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test 2: Cache Update Behavior

Run the interfaces command twice to verify cache updates:

```bash
# First run - creates cache entry
curl -X GET "http://localhost:8000/api/devices/your-device-uuid/interfaces?use_textfsm=true" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check timestamp
curl -X GET "http://localhost:8000/api/cache/json/your-device-uuid?command=show%20interfaces" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Wait a few seconds, then run again
sleep 5

# Second run - updates existing cache entry
curl -X GET "http://localhost:8000/api/devices/your-device-uuid/interfaces?use_textfsm=true" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Verify timestamp updated
curl -X GET "http://localhost:8000/api/cache/json/your-device-uuid?command=show%20interfaces" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

The `updated_at` timestamp should change on the second run.

### Test 3: Manual Cache Operations

Test direct cache manipulation:

```bash
# 1. Create a cache entry manually
curl -X POST "http://localhost:8000/api/cache/json/test-device-uuid" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "test-device-uuid",
    "command": "show version",
    "json_data": "{\"version\": \"15.1\", \"model\": \"C9300\"}"
  }'

# 2. Retrieve it
curl -X GET "http://localhost:8000/api/cache/json/test-device-uuid?command=show%20version" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 3. Update it
curl -X POST "http://localhost:8000/api/cache/json/test-device-uuid" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "test-device-uuid",
    "command": "show version",
    "json_data": "{\"version\": \"15.2\", \"model\": \"C9300\"}"
  }'

# 4. Verify update
curl -X GET "http://localhost:8000/api/cache/json/test-device-uuid?command=show%20version" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 5. Delete it
curl -X DELETE "http://localhost:8000/api/cache/json/test-device-uuid?command=show%20version" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 6. Verify deletion (should return 404)
curl -X GET "http://localhost:8000/api/cache/json/test-device-uuid?command=show%20version" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Database Verification

Connect to PostgreSQL to verify the cache:

```sql
-- View all cache entries
SELECT * FROM json_blob_cache;

-- View cache for specific device
SELECT * FROM json_blob_cache WHERE device_id = 'your-device-uuid';

-- View cache for specific command
SELECT * FROM json_blob_cache WHERE command = 'show interfaces';

-- Count cache entries per device
SELECT device_id, COUNT(*) as cache_count
FROM json_blob_cache
GROUP BY device_id;

-- View recent cache updates
SELECT device_id, command, updated_at
FROM json_blob_cache
ORDER BY updated_at DESC
LIMIT 10;
```

## Expected Behavior

1. **First cache write**: Creates new entry with current timestamp
2. **Subsequent writes (same device + command)**: Updates existing entry and timestamp
3. **Get with command**: Returns single cache entry
4. **Get without command**: Returns array of all cache entries for device
5. **Delete with command**: Deletes specific cache entry
6. **Delete without command**: Deletes all cache entries for device
7. **Invalid device/command**: Returns 404 error

## Error Cases to Test

1. **Mismatched device_id**: POST with URL device_id != body device_id
   - Expected: 400 Bad Request

2. **Non-existent cache**: GET for cache that doesn't exist
   - Expected: 404 Not Found

3. **Delete non-existent**: DELETE for cache that doesn't exist
   - Expected: 404 Not Found

4. **Invalid JSON**: POST with malformed JSON data
   - Expected: Should still store (cache stores string, doesn't validate JSON)

## Performance Considerations

- Composite index on (device_id, command) ensures fast lookups
- Large JSON blobs stored as TEXT field
- updated_at automatically maintained by database
- Consider cache cleanup strategy for old entries

## Logs to Monitor

Check backend logs for:
```
Successfully cached JSON output for device {device_id}, command: show interfaces
Created JSON cache for device {device_id}, command: {command}
Updated JSON cache for device {device_id}, command: {command}
Deleted JSON cache for device {device_id}, command: {command}
```

## Next Steps

After testing the basic cache operations, consider:
1. Adding cache expiration/TTL
2. Implementing cache cleanup jobs
3. Adding metrics for cache hit/miss rates
4. Extending to other commands beyond "show interfaces"
5. Adding cache statistics endpoint
