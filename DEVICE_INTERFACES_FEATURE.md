# Device Interfaces Feature Implementation

## Overview

Added a comprehensive "Interfaces" menu item to the device context menu with three submenu options (Brief, Full, Errors). Implemented a full interface viewer modal that displays interface data in a modern, user-friendly way with TextFSM parsing.

## Changes Made

### 1. Backend API (Already Exists)
**File**: `backend/app/api/devices.py`

The endpoint already exists:
- **Endpoint**: `GET /api/devices/{device_id}/interfaces?use_textfsm=true`
- **Parser**: Uses TextFSM for structured data parsing
- **Response**: Returns DeviceCommandResponse with parsed interface data as an array

### 2. Frontend API Service
**File**: `frontend/src/services/api.ts`

Added `devicesApi` export with `getInterfaces()` method:

```typescript
export const devicesApi = {
  async getInterfaces(deviceId: string, useTextfsm: boolean = true): Promise<{
    success: boolean
    output?: any
    error?: string
    parsed?: boolean
    parser_used?: string
  }> {
    const queryParams = new URLSearchParams()
    if (useTextfsm) {
      queryParams.append('use_textfsm', 'true')
    }
    const endpoint = `/api/devices/${deviceId}/interfaces${queryParams.toString() ? '?' + queryParams.toString() : ''}`
    return apiClient.get(endpoint)
  }
}
```

### 3. Device Interfaces Modal Component
**File**: `frontend/src/components/DeviceInterfacesModal.vue`

Created a new modal component with:

#### Features
- **Two-panel layout**:
  - Left panel: Searchable list of all interfaces with status badges
  - Right panel: Detailed information for selected interface
  
- **Status badges**: Color-coded status indicators (up=green, down=red, admin=yellow)

- **Organized data display**:
  - Status section: status, protocol, link_status, line_protocol
  - Configuration section: description, IP address, MTU, speed, duplex, VLAN, bandwidth
  - Traffic & Errors section: packet counts, error counts, CRC, collisions
  - Additional Information: Any other fields returned by TextFSM

#### Props
```typescript
interface Props {
  show: boolean          // Show/hide modal
  deviceId: string       // Nautobot device ID
  deviceName: string     // Device name for display
}
```

#### Key Functions
- `loadInterfaces()`: Fetches interface data from API with TextFSM parsing
- `selectInterface()`: Handles interface selection from list
- `formatFieldName()`: Converts snake_case to Title Case
- `getStatusBadgeClass()`: Returns CSS classes based on interface status
- `getStatusFields()`, `getConfigFields()`, `getTrafficFields()`, `getAdditionalFields()`: Categorize interface data for organized display

#### UI Components
- Search input for filtering interfaces by name or description
- Scrollable interface list with selectable items
- Responsive grid layout for interface details
- Loading and error states
- Empty state handling

### 4. NOCCanvas Integration
**File**: `frontend/src/components/NOCCanvas.vue`

#### Imports
```typescript
import DeviceInterfacesModal from './DeviceInterfacesModal.vue'
```

#### State Variables
```typescript
const showInterfacesModal = ref(false)
const interfacesDeviceId = ref('')
const interfacesDeviceName = ref('')
```

#### Template Addition
```vue
<DeviceInterfacesModal
  :show="showInterfacesModal"
  :device-id="interfacesDeviceId"
  :device-name="interfacesDeviceName"
  @close="closeInterfacesModal"
/>
```

#### Context Menu Addition
Added "Interfaces" menu item between "Config" and "Commands":

```typescript
{
  icon: '🔌',
  label: 'Interfaces',
  submenu: [
    { icon: '📋', label: 'Brief', action: () => { hideContextMenu(); showDeviceInterfaces(contextMenu.target!, 'brief') } },
    { icon: '📄', label: 'Full', action: () => { hideContextMenu(); showDeviceInterfaces(contextMenu.target!, 'full') } },
    { icon: '⚠️', label: 'Errors', action: () => { hideContextMenu(); showDeviceInterfaces(contextMenu.target!, 'errors') } },
  ],
}
```

#### Functions
```typescript
const showDeviceInterfaces = (device: Device, _mode: 'brief' | 'full' | 'errors') => {
  const props = device.properties ? JSON.parse(device.properties) : {}
  const nautobotId = props.nautobot_id
  
  if (!nautobotId) {
    console.error('Device does not have a Nautobot ID')
    return
  }
  
  interfacesDeviceId.value = nautobotId
  interfacesDeviceName.value = device.name
  showInterfacesModal.value = true
}

const closeInterfacesModal = () => {
  showInterfacesModal.value = false
  interfacesDeviceId.value = ''
  interfacesDeviceName.value = ''
}
```

## Usage

### How to Use
1. Right-click on any device on the canvas
2. Navigate to **Interfaces** → **Full** in the context menu
3. The modal will open showing all interfaces for the device
4. Select an interface from the left panel to view detailed information
5. Use the search box to filter interfaces by name or description

### Menu Options (Currently All Use "Full" Mode)
- **Brief**: Designed for summary view (to be implemented with different command)
- **Full**: Shows all interface details with TextFSM parsing ✅ **Implemented**
- **Errors**: Designed to filter only interfaces with errors (to be implemented)

## Data Display

### Field Categories

**Status Fields**:
- status, protocol, link_status, line_protocol

**Configuration Fields**:
- description, ip_address, mtu, speed, duplex, vlan, bandwidth, encapsulation, hardware_type

**Traffic & Error Fields**:
- input_packets, output_packets, input_errors, output_errors, input_rate, output_rate, crc, collisions

**Additional Fields**:
- Any other fields returned by TextFSM that don't fit above categories

### TextFSM Output Structure

The backend uses TextFSM to parse `show interfaces` command output into structured data. Example fields:

```json
[
  {
    "interface": "GigabitEthernet0/0",
    "status": "up",
    "protocol": "up",
    "description": "WAN Link",
    "ip_address": "192.168.1.1",
    "mtu": "1500",
    "speed": "1000Mbps",
    "duplex": "Full",
    "input_packets": "123456",
    "output_packets": "234567",
    "input_errors": "0",
    "output_errors": "0"
  }
]
```

## Future Enhancements

### 1. Brief Mode
- Implement with different command or filter output
- Show only interface name, status, IP address
- More compact view for quick overview

### 2. Errors Mode
- Filter to show only interfaces with non-zero error counts
- Highlight error-prone interfaces
- Sort by error count

### 3. Interface Statistics Visualization
- Add charts for traffic rates
- Historical data if available
- Error rate trends

### 4. Bulk Operations
- Select multiple interfaces
- Compare interface configurations
- Export interface data to CSV/JSON

### 5. Real-time Updates
- Auto-refresh interface status
- Live traffic counters
- Alert on status changes

### 6. Additional Commands
- Support `show ip interface brief`
- Support `show interfaces status`
- Support `show interfaces description`

## Technical Notes

### TextFSM Parser
- The backend uses TextFSM templates to parse CLI output
- Templates are device/platform-specific
- Parsed output is more reliable than regex parsing
- Returns structured data (list of dictionaries)

### Error Handling
- API errors displayed in modal
- Device without Nautobot ID shows console error
- Empty interface list shows "No interfaces found" message
- Network timeouts handled gracefully

### Performance
- Interface data loaded on-demand when modal opens
- Search filtering happens client-side (instant)
- Auto-selects first interface for better UX
- Modal state reset on close

## Testing

### Test Scenarios

1. **Happy Path**:
   - Right-click device → Interfaces → Full
   - Modal opens with interface list
   - Select interface → Details appear
   - Search for interface → Filters correctly
   - Close modal → State resets

2. **Error Cases**:
   - Device without Nautobot ID → Error logged to console
   - API failure → Error message displayed in modal
   - No interfaces → Empty state shown
   - Network timeout → Error message with details

3. **Edge Cases**:
   - Device with 100+ interfaces → Scrollable list
   - Interface with minimal data → Only available fields shown
   - Interface with extensive data → All fields categorized and displayed

## Files Modified

1. ✅ `frontend/src/services/api.ts` - Added `devicesApi.getInterfaces()`
2. ✅ `frontend/src/components/DeviceInterfacesModal.vue` - Created new modal component
3. ✅ `frontend/src/components/NOCCanvas.vue` - Added menu item and modal integration

## Date
October 7, 2025
