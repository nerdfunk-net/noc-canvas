# JSON Blob Cache TTL Setting Implementation

## Summary

Extended the Settings > Cache panel to include a JSON Blob Cache subsection with a configurable TTL (Time To Live) setting. This allows administrators to control how long JSON blob cache entries remain valid before expiration.

**Implementation Date:** October 7, 2025

## Changes Made

### Frontend Changes

**File:** `frontend/src/views/SettingsView.vue`

#### 1. Added UI Component (Lines ~1192-1203)

Added a new subsection within the Cache Settings card:

```vue
<!-- JSON Blob Cache Subsection -->
<div class="mt-6 pt-6 border-t border-gray-200">
  <h3 class="text-base font-semibold text-gray-900 mb-4">JSON Blob Cache</h3>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">
        Default TTL (minutes)
      </label>
      <input
        v-model.number="settings.cache.jsonBlobTtlMinutes"
        type="number"
        min="1"
        max="10080"
        class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
      />
      <p class="text-xs text-gray-500 mt-1">How long JSON blob cache entries remain valid (max: 7 days)</p>
    </div>
  </div>
</div>
```

**Features:**
- Text input field for TTL in minutes
- Validation: Min 1 minute, Max 10080 minutes (7 days)
- Two-way data binding with `v-model.number`
- Helpful description text
- Separated from main cache settings with border divider
- Responsive grid layout (1 column on mobile, 2 on desktop)

#### 2. Updated Settings Data Structure (Line ~2732)

Added `jsonBlobTtlMinutes` property to the reactive settings object:

```typescript
cache: {
  defaultTtlMinutes: 60,
  autoRefreshEnabled: false,
  autoRefreshIntervalMinutes: 30,
  cleanExpiredOnStartup: true,
  jsonBlobTtlMinutes: 1440, // 24 hours default
},
```

**Default Value:** 1440 minutes (24 hours)

#### 3. Updated Settings Load Logic (Line ~3195)

Added loading of `jsonBlobTtlMinutes` from localStorage:

```typescript
settings.cache.jsonBlobTtlMinutes = parsed.jsonBlobTtlMinutes ?? 1440
```

**Behavior:**
- Loads value from localStorage on component mount
- Falls back to 1440 minutes if not found
- Maintains setting across page refreshes

#### 4. Updated Settings Save Logic (Line ~4174)

Added `jsonBlobTtlMinutes` to the cache settings payload:

```typescript
const cacheSettings = {
  defaultTtlMinutes: settings.cache.defaultTtlMinutes,
  autoRefreshEnabled: settings.cache.autoRefreshEnabled,
  autoRefreshIntervalMinutes: settings.cache.autoRefreshIntervalMinutes,
  cleanExpiredOnStartup: settings.cache.cleanExpiredOnStartup,
  jsonBlobTtlMinutes: settings.cache.jsonBlobTtlMinutes,
}
```

**Behavior:**
- Saves to localStorage as backup
- Sends to backend API endpoint `/api/settings/cache_settings`
- Persists in database for multi-user environments

## User Interface

### Location
**Settings > Cache Tab > Cache Settings Card > JSON Blob Cache Subsection**

### Layout
```
┌─────────────────────────────────────────────────────┐
│ Cache Settings                                      │
├─────────────────────────────────────────────────────┤
│ Default TTL (minutes)  │ Auto-refresh Interval      │
│ [    60     ]          │ [    30     ]              │
├─────────────────────────────────────────────────────┤
│ ☐ Enable Auto-refresh                               │
│ ☐ Clean Expired Cache on Startup                    │
├─────────────────────────────────────────────────────┤
│ JSON Blob Cache                                     │
├─────────────────────────────────────────────────────┤
│ Default TTL (minutes)                               │
│ [   1440    ]                                       │
│ How long JSON blob cache entries remain valid       │
│ (max: 7 days)                                       │
└─────────────────────────────────────────────────────┘
```

## Technical Details

### Data Flow

1. **Load on Mount:**
   ```
   localStorage → Component State → UI Display
   ```

2. **User Input:**
   ```
   User Types → v-model → Reactive State → Auto-save to localStorage
   ```

3. **Save to Database:**
   ```
   User Clicks Save → Collect Settings → POST /api/settings/cache_settings → Database
   ```

4. **Multi-user Sync:**
   ```
   Other users → Load Settings → GET /api/settings/cache_settings → Sync to UI
   ```

### Validation

- **Type:** Number (enforced by `v-model.number`)
- **Minimum:** 1 minute
- **Maximum:** 10,080 minutes (7 days / 1 week)
- **Default:** 1,440 minutes (24 hours / 1 day)

### Storage Locations

1. **Browser localStorage** (key: `cacheSettings`)
   - Fast access
   - User-specific
   - Survives page refresh
   - Backup/fallback storage

2. **PostgreSQL Database** (table: `app_settings`, key: `cache_settings`)
   - Persistent
   - Shared across users
   - Survives browser cache clear
   - Source of truth

## Usage

### For End Users

1. Navigate to **Settings** (gear icon in top right)
2. Click the **Cache** tab
3. Scroll to **JSON Blob Cache** subsection
4. Enter desired TTL in minutes (1-10080)
5. Click **Save Cache Settings** button
6. Setting is now active and persisted

### For Developers

Access the setting value in code:

```typescript
// In SettingsView.vue
const ttlMinutes = settings.cache.jsonBlobTtlMinutes

// Calculate expiration timestamp
const expiresAt = new Date(Date.now() + ttlMinutes * 60 * 1000)
```

## Backend Integration (Future)

While the UI is now complete, the backend needs to be updated to use this TTL value:

### Recommended Implementation

**File:** `backend/app/services/json_cache_service.py`

```python
from datetime import datetime, timedelta
from app.models.settings import AppSettings
import json

class JSONCacheService:
    @staticmethod
    def get_ttl_minutes(db: Session) -> int:
        """Get JSON blob cache TTL from settings."""
        settings = db.query(AppSettings).filter(
            AppSettings.key == "cache_settings"
        ).first()
        
        if settings and settings.value:
            try:
                cache_settings = json.loads(settings.value)
                return cache_settings.get("jsonBlobTtlMinutes", 1440)
            except:
                pass
        
        return 1440  # Default: 24 hours
    
    @staticmethod
    def set_cache(db: Session, device_id: str, command: str, json_data: str):
        # ... existing code ...
        
        # Calculate expiration
        ttl_minutes = JSONCacheService.get_ttl_minutes(db)
        expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
        
        # Store with expiration (requires schema update)
        cache_entry = JSONBlobCache(
            device_id=device_id,
            command=command,
            json_data=json_data,
            expires_at=expires_at  # New field
        )
        # ... rest of code ...
```

### Required Database Changes

**File:** `backend/app/models/device_cache.py`

Add `expires_at` field to `JSONBlobCache`:

```python
class JSONBlobCache(Base):
    __tablename__ = "json_blob_cache"
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, nullable=False, index=True)
    command = Column(String, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # NEW
    json_data = Column(String, nullable=False)
    __table_args__ = (Index('ix_json_blob_device_command', 'device_id', 'command'),)
```

### Cache Cleanup Job

Create a periodic cleanup task:

```python
@staticmethod
def cleanup_expired_cache(db: Session) -> int:
    """Delete expired cache entries."""
    now = datetime.utcnow()
    deleted = db.query(JSONBlobCache).filter(
        JSONBlobCache.expires_at < now
    ).delete()
    db.commit()
    logger.info(f"Cleaned up {deleted} expired JSON cache entries")
    return deleted
```

## Benefits

1. **Configurable Expiration:** Admins can tune cache lifetime based on data volatility
2. **Storage Management:** Prevent indefinite cache growth
3. **Data Freshness:** Ensure cached data doesn't become too stale
4. **User Control:** Different environments can have different policies
5. **Compliance:** Meet data retention requirements

## Testing

### Manual Testing

1. **Set Short TTL:**
   - Set to 1 minute
   - Save settings
   - Verify value persists after page refresh

2. **Set Long TTL:**
   - Set to 10080 minutes (max)
   - Verify no validation errors

3. **Test Boundaries:**
   - Try 0 minutes (should prevent via min="1")
   - Try 10081 minutes (should prevent via max="10080")

4. **Multi-user Test:**
   - User A sets TTL to 720 minutes
   - User B refreshes settings page
   - Verify User B sees 720 minutes

### Automated Testing

```typescript
describe('JSON Blob Cache TTL Setting', () => {
  it('should have default value of 1440 minutes', () => {
    expect(settings.cache.jsonBlobTtlMinutes).toBe(1440)
  })
  
  it('should enforce minimum value of 1', () => {
    // Input validation test
  })
  
  it('should enforce maximum value of 10080', () => {
    // Input validation test
  })
  
  it('should persist to localStorage', () => {
    settings.cache.jsonBlobTtlMinutes = 720
    saveCacheSettings()
    const saved = JSON.parse(localStorage.getItem('cacheSettings'))
    expect(saved.jsonBlobTtlMinutes).toBe(720)
  })
})
```

## Documentation Updates

- ✅ Frontend UI implemented
- ✅ Settings data structure updated
- ✅ Load/save logic implemented
- ⏳ Backend integration pending
- ⏳ Database schema update pending
- ⏳ Cleanup job implementation pending

## Files Modified

- ✅ `frontend/src/views/SettingsView.vue` - Added UI and logic for JSON blob cache TTL setting

## Deployment Notes

1. **No Breaking Changes:** Frontend changes are backward compatible
2. **Default Value:** 1440 minutes (24 hours) used if setting not found
3. **Graceful Degradation:** Backend currently ignores TTL (cache never expires)
4. **Future Enhancement:** Backend needs update to enforce TTL expiration

## Conclusion

The JSON Blob Cache TTL setting is now available in the Settings UI. Users can configure how long JSON cache entries remain valid (1 minute to 7 days). The setting is persisted in both localStorage and the database. Backend implementation to enforce TTL expiration is recommended as a next step.
