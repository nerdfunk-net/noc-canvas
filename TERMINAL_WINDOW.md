# SSH Terminal in Separate Window - Implementation

## Overview

This implementation allows users to open SSH terminal sessions in separate browser windows instead of modal dialogs. This enables multitasking: users can work in the main application while having one or more terminal sessions open simultaneously in separate windows.

## Architecture

### 1. **Standalone Terminal Page** - `/terminal` route

**File:** `frontend/src/views/TerminalWindow.vue`

A dedicated full-page terminal view that:
- Connects to the WebSocket SSH backend
- Uses xterm.js for terminal emulation  
- Receives device ID, name, and auth token via URL query parameters
- Renders a full-screen terminal with status indicators
- Auto-closes when SSH session disconnects

### 2. **Utility Functions** - Window Management

**File:** `frontend/src/utils/terminalWindow.ts`

Provides functions to:
- `openTerminalWindow()` - Open a terminal in a new browser window
- `canOpenPopup()` - Check if popups are allowed
- `openMultipleTerminals()` - Open several terminals at once
- `closeAllTerminals()` - Close terminal windows (limited by browser security)

### 3. **Updated Context Menu** - Two Terminal Options

**File:** `frontend/src/components/NOCCanvas.vue`

Right-click menu on devices now shows:
```
💻 SSH Terminal  →  🪟 Open in Modal
                   🚀 Open in New Window
```

### 4. **Router Configuration**

**File:** `frontend/src/router/index.ts`

Added new route:
```typescript
{
  path: '/terminal',
  name: 'terminal',
  component: TerminalWindow,
  meta: { requiresAuth: true }
}
```

## How It Works

### Opening a Terminal in New Window

```typescript
// 1. User right-clicks device → "SSH Terminal" → "Open in New Window"
const openSSHTerminalInWindow = (device: Device) => {
  const nautobotId = device.properties.nautobot_id
  
  // 2. Get auth token from localStorage
  const token = localStorage.getItem('auth_token')
  
  // 3. Build URL with query parameters
  const url = `/terminal?deviceId=${nautobotId}&deviceName=${device.name}&token=${token}`
  
  // 4. Open new window with specific dimensions and position
  window.open(url, `terminal_${nautobotId}`, 'width=1200,height=800,...')
}
```

### Terminal Window Lifecycle

```
1. New window opens → `/terminal` route loads
    ↓
2. TerminalWindow.vue reads URL query params
    ↓
3. Extracts: deviceId, deviceName, token
    ↓
4. Initializes xterm.js terminal
    ↓
5. Connects WebSocket: ws://host/api/ssh/terminal?device_id=X&token=Y
    ↓
6. Bidirectional communication established
    ↓
7. User interacts with terminal
    ↓
8. Session ends → Window auto-closes after 2 seconds
```

## Features

### Terminal Window Features

**Header Bar:**
- Device name display
- Connection status indicator (Connecting/Connected/Disconnected)
- Close button

**Terminal:**
- Full xterm.js terminal emulation
- Auto-resizing to fit window
- Standard terminal keyboard shortcuts
- Scrollback buffer (10,000 lines)
- Proper color support

**Auto-Close:**
- Window automatically closes 2 seconds after SSH session disconnects
- User can manually close via button or window controls

### Window Management

**Window Positioning:**
- Centers on screen
- Cascades when opening multiple terminals (50px offset)
- Customizable width/height

**Multiple Terminals:**
```typescript
// Open terminals to multiple devices
openMultipleTerminals([
  { deviceId: 'device1', deviceName: 'Router 1' },
  { deviceId: 'device2', deviceName: 'Router 2' },
])
```

**Popup Blocker Detection:**
```typescript
if (!canOpenPopup()) {
  alert('Please allow popups for this site')
}
```

## User Experience

### Benefits

1. **Multitasking**
   - Work in main app while terminal sessions are open
   - Switch between app and terminals using OS window management
   - No modal blocking the main interface

2. **Multiple Sessions**
   - Open terminals to multiple devices simultaneously
   - Each terminal in its own window
   - Easy to organize/tile windows

3. **Persistent Sessions**
   - Terminal windows stay open even if you navigate in main app
   - Can minimize/maximize terminal windows independently
   - Full OS window management (Alt+Tab, etc.)

4. **Familiar UX**
   - Behaves like traditional SSH clients
   - Each connection is a separate "application"
   - No confusion about which terminal belongs to which device

### Modal vs Window

| Feature | Modal | Separate Window |
|---------|-------|-----------------|
| Multitasking | ❌ Blocks main app | ✅ Independent |
| Multiple Sessions | ⚠️ One at a time | ✅ Unlimited |
| Window Management | ❌ Limited | ✅ Full OS support |
| Screen Real Estate | ⚠️ Shares with app | ✅ Can use full screen |
| Accidental Close | ⚠️ Easy (click outside) | ✅ Harder |

## Security

### Authentication

**Token Passing:**
- Auth token retrieved from localStorage
- Passed via URL query parameter
- WebSocket validates token on connect
- Token scoped to user's session

**Session Security:**
- Each window uses same auth token
- Backend validates permissions per device
- WebSocket connections authenticated
- Tokens expire (handled by backend)

### Privacy Considerations

**URL Parameters:**
- Token visible in browser history
- Solution: Use short-lived tokens or session-based auth
- Alternative: Use window.postMessage for token passing

## Browser Compatibility

**Supported:**
- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari

**Popup Blockers:**
- First-time users may need to allow popups
- Detection via `canOpenPopup()` function
- User-friendly error messages

**Window Features:**
- Modern browsers support all window features
- Resizable windows
- Independent of parent window

## Files Modified/Created

### Created:
- `frontend/src/views/TerminalWindow.vue` - Standalone terminal page
- `frontend/src/utils/terminalWindow.ts` - Window management utilities

### Modified:
- `frontend/src/router/index.ts` - Added `/terminal` route
- `frontend/src/components/NOCCanvas.vue` - Updated context menu, added `openSSHTerminalInWindow()`

## Usage Example

```typescript
import { openTerminalWindow } from '@/utils/terminalWindow'

// Open single terminal
const termWindow = openTerminalWindow({
  deviceId: 'abc-123',
  deviceName: 'router1.example.com',
  width: 1200,
  height: 800
})

// Check if opened successfully
if (!termWindow) {
  alert('Please allow popups')
}

// Open multiple terminals
const devices = [
  { deviceId: 'device1', deviceName: 'Router 1' },
  { deviceId: 'device2', deviceName: 'Switch 1' }
]
openMultipleTerminals(devices)
```

## Future Enhancements

1. **Session Management**
   - Track open terminal windows
   - "Restore all terminals" feature
   - Close all terminals with one click

2. **Window Persistence**
   - Remember window positions/sizes
   - Restore terminals on page reload
   - Save terminal session state

3. **Advanced Features**
   - Split terminal view (multiple panes in one window)
   - Terminal tabs (multiple devices in one window)
   - Screen recording/logging
   - Copy/paste improvements

4. **Security Improvements**
   - Token-less authentication via window.postMessage
   - Session-based auth instead of URL tokens
   - Auto-lock after inactivity

## Summary

This implementation provides a professional, user-friendly way to work with multiple SSH sessions simultaneously. Users can now:
- Keep terminals open while working in the main app
- Organize terminal windows using OS features
- Connect to multiple devices at once
- Enjoy a familiar, desktop-like SSH experience

The hybrid approach (modal + separate window options) gives users flexibility to choose their preferred workflow! 🚀
