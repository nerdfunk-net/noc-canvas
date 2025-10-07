# Netmiko Integration Settings Implementation

## Overview
Added a new "Netmiko Integration" settings panel to the Settings/Plugins view that allows users to configure Netmiko timeout settings for SSH connections to network devices. Both Nautobot and Netmiko integrations are always enabled and do not have an enable/disable toggle.

## Changes Made

### Backend Changes

#### 1. **backend/app/models/settings.py**
- Added `NetmikoSettings` Pydantic model with all timeout fields (no enabled field)
- Updated `UnifiedSettings` model to include a `netmiko` dictionary with default values
- Removed `enabled` field from `nautobot` dictionary (always enabled)

**Fields Added:**
- `readTimeout`: Read timeout in seconds (default: 10)
- `lastRead`: Last read timeout in seconds (default: None/optional)
- `connTimeout`: Connection timeout in seconds (default: 10)
- `authTimeout`: Authentication timeout in seconds (default: None/optional)
- `bannerTimeout`: Banner timeout in seconds (default: 15)
- `blockingTimeout`: Blocking timeout in seconds (default: 20)
- `timeout`: General timeout in seconds (default: 100)
- `sessionTimeout`: Session timeout in seconds (default: 60)

#### 2. **backend/app/api/settings.py**
- Added `build_netmiko_settings()` function to load Netmiko settings from database with defaults
- Updated `build_nautobot_settings()` to not return `enabled` field (always enabled)
- Updated `get_unified_settings()` endpoint to include Netmiko settings in the response
- Updated `save_unified_settings()` endpoint to save Netmiko settings to database
- Removed saving of `nautobot_enabled` and `netmiko_enabled` keys

**Database Keys:**
- `netmiko_read_timeout`
- `netmiko_last_read`
- `netmiko_conn_timeout`
- `netmiko_auth_timeout`
- `netmiko_banner_timeout`
- `netmiko_blocking_timeout`
- `netmiko_timeout`
- `netmiko_session_timeout`

### Frontend Changes

#### 3. **frontend/src/views/SettingsView.vue**

**Updated Reactive State:**
```typescript
nautobot: {
  url: '',
  token: '',
  verifyTls: true,
  timeout: 30,
},
netmiko: {
  readTimeout: 10,
  lastRead: null as number | null,
  connTimeout: 10,
  authTimeout: null as number | null,
  bannerTimeout: 15,
  blockingTimeout: 20,
  timeout: 100,
  sessionTimeout: 60,
}
```

**Updated UI Panels:**
- Removed "Enable Plugin" toggle from **Nautobot Integration** panel
- Removed "Enable Plugin" toggle from **Netmiko Integration** panel
- Added descriptive subtitle text to both panels
- **CheckMK Integration** still has the enable/disable toggle
- All timeout input fields with labels and descriptions for Netmiko
- Help text explaining the purpose of each timeout
- Info box with description of Netmiko connection settings

**Updated Functions:**
- `loadSettings()`: Automatically loads Netmiko settings via Object.assign
- `saveSettings()`: Now includes `netmiko` in the settings payload sent to backend

## Usage

1. Navigate to **Settings → Plugins**
2. Both **Nautobot Integration** and **Netmiko Integration** are always active
3. Configure Netmiko timeout values as needed:
   - **Read Timeout**: How long to wait for data when reading from device
   - **Last Read**: Optional timeout for the final read operation
   - **Connection Timeout**: How long to wait when establishing connection
   - **Auth Timeout**: Optional timeout for authentication operations
   - **Banner Timeout**: How long to wait for login banner
   - **Blocking Timeout**: Timeout for blocking operations
   - **Timeout**: General operation timeout
   - **Session Timeout**: How long a session can remain active
4. Click the "Save" button at the bottom of the page

## Data Flow

1. **Loading Settings:**
   - Frontend calls `GET /api/settings/unified`
   - Backend calls `build_netmiko_settings(db)` and `build_nautobot_settings(db)` to retrieve from database
   - Settings are returned with default values if not configured
   - Frontend updates reactive state via `Object.assign()`

2. **Saving Settings:**
   - User modifies values in UI
   - Frontend calls `POST /api/settings/unified` with nautobot and netmiko objects
   - Backend extracts settings and saves to database as individual key-value pairs
   - Success notification shown to user

## Database Storage

All Netmiko settings are stored in the `app_settings` table with the following structure:
- `key`: Setting name (e.g., "netmiko_read_timeout")
- `value`: Setting value as string
- `description`: Optional description (can be NULL)
- `created_at`: Timestamp when setting was created
- `updated_at`: Timestamp when setting was last updated

## Notes

- **Nautobot and Netmiko integrations are always enabled** - no toggle needed
- Optional fields (`lastRead` and `authTimeout`) can be left empty and will be stored as empty strings in the database
- All timeout values are validated to be between 1 and 300/600 seconds in the UI
- CheckMK integration still has an enable/disable toggle
- Settings are persisted to both the database (backend) and localStorage (frontend fallback)
