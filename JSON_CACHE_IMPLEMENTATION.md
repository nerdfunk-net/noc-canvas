# JSON Blob Cache Implementation

## Summary

Implemented a JSON blob caching system for storing parsed device command outputs. The cache stores TextFSM-parsed JSON data with device UUID, command string, timestamp, and raw JSON data.

**Implementation Date:** October 7, 2025

## Components Created/Modified

### 1. Database Model
**File:** `backend/app/models/device_cache.py`

Added `JSONBlobCache` model:
```python
class JSONBlobCache(Base):
    __tablename__ = "json_blob_cache"
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, nullable=False, index=True)
    command = Column(String, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    json_data = Column(String, nullable=False)
    __table_args__ = (Index('ix_json_blob_device_command', 'device_id', 'command'),)
```

**Features:**
- Auto-incrementing primary key
- Composite index on (device_id, command) for efficient lookups
- Automatic timestamp updates via `onupdate=func.now()`
- JSON data stored as string (TEXT field in PostgreSQL)

### 2. Pydantic Schemas
**File:** `backend/app/schemas/device_cache.py`

Added four schema classes:

```python
class JSONBlobCacheBase(BaseModel):
    device_id: str
    command: str
    json_data: str

class JSONBlobCacheCreate(JSONBlobCacheBase):
    pass

class JSONBlobCacheUpdate(BaseModel):
    json_data: str

class JSONBlobCacheResponse(JSONBlobCacheBase):
    id: int
    updated_at: datetime
    class Config:
        from_attributes = True
```

### 3. Service Layer
**File:** `backend/app/services/json_cache_service.py` (NEW)

Implemented `JSONCacheService` class with methods:

- **`set_cache(db, device_id, command, json_data)`**
  - Creates new cache entry or updates existing one
  - Returns the cache entry
  - Handles upsert logic automatically

- **`get_cache(db, device_id, command=None)`**
  - Returns single entry if command specified
  - Returns list of all entries for device if command omitted
  - Returns None if not found

- **`delete_cache(db, device_id, command=None)`**
  - Deletes specific command cache if command specified
  - Deletes all device cache entries if command omitted
  - Returns count of deleted entries

- **`get_all_cached_devices(db)`**
  - Returns list of all device IDs with cached data

- **`get_cached_commands(db, device_id)`**
  - Returns list of all commands cached for a device

### 4. API Endpoints
**File:** `backend/app/api/cache.py`

Added 5 new endpoints to existing cache router:

#### POST `/api/cache/json/{device_id}`
Create or update cache entry
- Request body: `device_id`, `command`, `json_data`
- Returns: `JSONBlobCacheResponse`
- Validates device_id matches URL parameter

#### GET `/api/cache/json/{device_id}`
Get cached data for device
- Query param: `command` (optional)
- If command provided: Returns single `JSONBlobCacheResponse`
- If command omitted: Returns list of `JSONBlobCacheResponse`
- Returns 404 if not found

#### DELETE `/api/cache/json/{device_id}`
Delete cached data
- Query param: `command` (optional)
- If command provided: Deletes specific cache
- If command omitted: Deletes all device cache
- Returns success message with deleted count
- Returns 404 if nothing to delete

#### GET `/api/cache/json/devices/list`
List all devices with cached data
- Returns: `{"devices": ["uuid1", "uuid2", ...]}`

#### GET `/api/cache/json/{device_id}/commands`
List all cached commands for device
- Returns: `{"commands": ["show interfaces", "show version", ...]}`
- Returns 404 if device has no cache

### 5. Integration with Interfaces Endpoint
**File:** `backend/app/api/devices.py`

Modified `get_interfaces()` endpoint to automatically cache JSON output:

```python
# Store the parsed JSON output in the JSON blob cache
try:
    import json
    from app.services.json_cache_service import JSONCacheService
    
    json_data = json.dumps(output)
    JSONCacheService.set_cache(
        db=db,
        device_id=device_id,
        command="show interfaces",
        json_data=json_data
    )
    logger.info(f"Successfully cached JSON output for device {device_id}, command: show interfaces")
except Exception as cache_error:
    logger.error(f"Failed to cache JSON output: {str(cache_error)}")
    # Continue processing even if JSON cache fails
```

**Behavior:**
- When `use_textfsm=True` parameter is used
- Automatically stores parsed JSON output in cache
- Fails gracefully if caching errors occur
- Logs all cache operations

## Database Schema

The `json_blob_cache` table is automatically created on application startup via SQLAlchemy's `Base.metadata.create_all()`.

```sql
CREATE TABLE json_blob_cache (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR NOT NULL,
    command VARCHAR NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    json_data TEXT NOT NULL
);

CREATE INDEX ix_json_blob_cache_device_id ON json_blob_cache (device_id);
CREATE INDEX ix_json_blob_device_command ON json_blob_cache (device_id, command);
```

## API Usage Examples

### Cache Command Output
```bash
curl -X POST "http://localhost:8000/api/cache/json/device-uuid" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-uuid",
    "command": "show interfaces",
    "json_data": "[{\"interface\": \"Gi0/0\", \"status\": \"up\"}]"
  }'
```

### Retrieve Cached Data
```bash
# Get specific command
curl -X GET "http://localhost:8000/api/cache/json/device-uuid?command=show%20interfaces" \
  -H "Authorization: Bearer TOKEN"

# Get all cached commands for device
curl -X GET "http://localhost:8000/api/cache/json/device-uuid" \
  -H "Authorization: Bearer TOKEN"
```

### Delete Cache
```bash
# Delete specific command cache
curl -X DELETE "http://localhost:8000/api/cache/json/device-uuid?command=show%20interfaces" \
  -H "Authorization: Bearer TOKEN"

# Delete all cache for device
curl -X DELETE "http://localhost:8000/api/cache/json/device-uuid" \
  -H "Authorization: Bearer TOKEN"
```

### Automatic Caching via Interfaces
```bash
# This will automatically cache the parsed JSON output
curl -X GET "http://localhost:8000/api/devices/device-uuid/interfaces?use_textfsm=true" \
  -H "Authorization: Bearer TOKEN"
```

## Key Features

1. **Automatic Upsert**: Setting cache with same device_id + command updates existing entry
2. **Timestamp Tracking**: `updated_at` automatically maintained by database
3. **Efficient Queries**: Composite index on (device_id, command) for fast lookups
4. **Flexible Retrieval**: Get single command or all commands for a device
5. **Bulk Delete**: Delete specific command or all commands for a device
6. **Integration**: Automatically populated when using TextFSM parsing
7. **Error Handling**: Graceful degradation if caching fails
8. **Logging**: All operations logged for debugging and monitoring

## Design Decisions

1. **String Storage**: JSON stored as string rather than JSONB
   - Simpler implementation
   - No PostgreSQL-specific features needed
   - Application handles JSON parsing

2. **Composite Index**: Index on (device_id, command)
   - Most queries filter by both fields
   - Efficient for common access patterns

3. **Service Layer Pattern**: Follows existing architecture
   - Separates business logic from API routes
   - Reusable across different endpoints
   - Easier to test and maintain

4. **Integrated with Existing Cache**: Added to existing cache.py router
   - Consistent API structure
   - Same authentication/authorization
   - Logical grouping with other cache endpoints

5. **Graceful Failure**: Cache errors don't break main functionality
   - Interfaces endpoint works even if cache fails
   - Errors logged for monitoring
   - User experience not affected

## Future Enhancements

Potential improvements for future iterations:

1. **Cache Expiration/TTL**
   - Add `expires_at` field
   - Automatic cleanup of old entries
   - Configurable TTL per command type

2. **Cache Statistics**
   - Track cache hit/miss rates
   - Monitor cache size and growth
   - Performance metrics endpoint

3. **Extended Command Support**
   - Cache other commands beyond "show interfaces"
   - Generalized caching for any TextFSM-parsed command
   - Command-specific cache strategies

4. **Cache Validation**
   - Verify JSON structure on storage
   - Schema validation for known command types
   - Data integrity checks

5. **Compression**
   - Compress large JSON blobs
   - Reduce storage requirements
   - Automatic decompression on retrieval

6. **Cache Warming**
   - Pre-populate cache for frequently accessed devices
   - Background refresh jobs
   - Configurable refresh intervals

## Testing

See `JSON_CACHE_TESTING.md` for comprehensive testing guide including:
- Manual API testing with cURL
- Integration testing scenarios
- Database verification queries
- Error case testing
- Performance considerations

## Files Modified

- ✅ `backend/app/models/device_cache.py` - Added JSONBlobCache model
- ✅ `backend/app/schemas/device_cache.py` - Added JSON cache schemas
- ✅ `backend/app/services/json_cache_service.py` - NEW service layer
- ✅ `backend/app/api/cache.py` - Added 5 new endpoints
- ✅ `backend/app/api/devices.py` - Integrated cache into interfaces endpoint
- ✅ `JSON_CACHE_TESTING.md` - NEW testing documentation
- ✅ `JSON_CACHE_IMPLEMENTATION.md` - This file

## Verification

All Python files compile successfully:
```bash
python -m py_compile app/models/device_cache.py app/schemas/device_cache.py \
  app/services/json_cache_service.py app/api/cache.py app/api/devices.py
```

No syntax errors detected.

## Deployment Notes

1. **Database Migration**: Table will be auto-created on next application start
2. **No Breaking Changes**: All modifications are additive
3. **Backward Compatible**: Existing endpoints unchanged
4. **Zero Downtime**: Can be deployed without service interruption
5. **Automatic Activation**: Cache automatically used when `use_textfsm=True`

## Conclusion

The JSON blob cache system is fully implemented and ready for testing. It provides a robust, efficient way to store and retrieve parsed device command outputs with minimal overhead and maximum flexibility.
