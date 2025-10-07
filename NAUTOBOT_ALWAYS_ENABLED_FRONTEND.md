# Nautobot Always-Enabled Frontend Updates

## Overview
Updated frontend components to reflect that Nautobot integration is always enabled and removed all references to the `enabled` field.

## Changes Made

### 1. **frontend/src/stores/settings.ts**

**Updated Interface:**
```typescript
export interface NautobotSettings {
  // Removed: enabled: boolean
  url: string
  token: string
  verifyTls: boolean
  timeout: number
}
```

**Updated Reactive State:**
```typescript
nautobot: {
  // Removed: enabled: false,
  url: '',
  token: '',
  verifyTls: true,
  timeout: 30,
}
```

### 2. **frontend/src/components/InventoryPanel.vue**

**Before:**
- Checked `settingsStore.settings.nautobot.enabled` to show inventory
- Showed "Plugin Disabled" message when URL was configured but plugin was disabled
- Had separate conditions for enabled, disabled, and not configured states

**After:**
- Simplified to check only `settingsStore.settings.nautobot.url`
- Removed "Plugin Disabled" message and condition entirely
- Now only shows:
  - **Device Tree**: When Nautobot URL is configured (always enabled)
  - **Not Configured**: When Nautobot URL is empty

**Updated Template Logic:**
```vue
<!-- Before -->
<div v-if="settingsStore.settings.nautobot.enabled" class="flex-1 flex flex-col">
<div v-else-if="!settingsStore.settings.nautobot.enabled && settingsStore.settings.nautobot.url">
  <!-- Plugin Disabled message -->
</div>
<div v-else-if="!settingsStore.settings.nautobot.url">
  <!-- Not Configured message -->
</div>

<!-- After -->
<div v-if="settingsStore.settings.nautobot.url" class="flex-1 flex flex-col">
  <!-- Device Tree -->
</div>
<div v-else>
  <!-- Not Configured message -->
</div>
```

### 3. **frontend/src/components/DeviceTree.vue**

**Updated Configuration Check:**
```typescript
// Before
const isNautobotConfigured = computed(() => {
  const isConfigured = !!(
    settingsStore.settings.nautobot.enabled &&
    settingsStore.settings.nautobot.url &&
    settingsStore.settings.nautobot.token
  )
  console.log('🔧 isNautobotConfigured check:', {
    enabled: settingsStore.settings.nautobot.enabled,
    hasUrl: !!settingsStore.settings.nautobot.url,
    hasToken: !!settingsStore.settings.nautobot.token,
    result: isConfigured,
  })
  return isConfigured
})

// After
const isNautobotConfigured = computed(() => {
  const isConfigured = !!(
    settingsStore.settings.nautobot.url &&
    settingsStore.settings.nautobot.token
  )
  console.log('🔧 isNautobotConfigured check:', {
    hasUrl: !!settingsStore.settings.nautobot.url,
    hasToken: !!settingsStore.settings.nautobot.token,
    result: isConfigured,
  })
  return isConfigured
})
```

## Impact

### User Experience Changes

**Before:**
1. User had to configure Nautobot URL and token
2. User had to enable the plugin in Settings
3. Device inventory would show "Plugin Disabled" if not enabled

**After:**
1. User only needs to configure Nautobot URL and token
2. No enable/disable toggle (always enabled)
3. Device inventory shows immediately when URL/token are configured
4. Cleaner, simpler UX with fewer steps

### State Conditions

**Device Tree/Inventory Display Logic:**
- **Shows Device Tree**: When `nautobot.url` is present (plugin is always active)
- **Shows "Not Configured"**: When `nautobot.url` is empty
- **No longer shows**: "Plugin Disabled" message

## Benefits

1. **Simplified User Experience**: One less step to get Nautobot working
2. **Consistent Behavior**: Nautobot is always ready when configured
3. **Cleaner Code**: Removed unnecessary conditional checks for `enabled` field
4. **Reduced Confusion**: Users no longer need to understand the difference between "configured" and "enabled"

## Testing Checklist

- [x] Settings store interface updated to remove `enabled` field
- [x] InventoryPanel no longer shows "Plugin Disabled" message
- [x] DeviceTree configuration check no longer references `enabled`
- [x] All TypeScript errors resolved
- [ ] Test UI: Navigate to inventory panel
- [ ] Test UI: Should show "Not Configured" when no URL set
- [ ] Test UI: Should show device tree when URL is configured
- [ ] Test: Settings page should not show Nautobot enable toggle
