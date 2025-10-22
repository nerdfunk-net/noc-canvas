# Settings View Refactoring

## Overview
SettingsView.vue was a monolithic 5,504-line component managing 11 different settings tabs. This refactoring breaks it down into smaller, maintainable components.

## Progress

### ✅ Completed - 9 Tabs Extracted!

#### 1. Jobs Tab (Lines saved: 392)
- **Component**: `tabs/JobsTab.vue` (248 lines)
- **Composable**: `composables/useJobMonitoring.ts` (216 lines)
- **Features**: Worker status, job history with error detection, auto-refresh

#### 2. General Tab (Lines saved: 176)
- **Component**: `tabs/GeneralTab.vue` (234 lines)
- **Features**: Canvas settings, database configuration with connection testing

#### 3. Templates Tab (Lines saved: 157)
- **Component**: `tabs/TemplatesTab.vue` (187 lines)
- **Features**: Device shape template management with platform/type assignment

#### 4. Commands Tab (Lines saved: 118)
- **Component**: `tabs/CommandsTab.vue` (165 lines)
- **Features**: Device command management with parser configuration

#### 5. Inventory Tab (Lines saved: 100)
- **Component**: `tabs/InventoryTab.vue` (155 lines)
- **Features**: Device inventory list with slots for editor/preview sections

#### 6. Profile Tab (Lines saved: 120)
- **Component**: `tabs/ProfileTab.vue` (168 lines)
- **Features**: Personal credentials management with slot for password change

#### 7. Canvas Tab (Lines saved: 225)
- **Component**: `tabs/CanvasTab.vue` (311 lines)
- **Features**: Canvas management with search, selection, and batch operations

#### 8. Plugins Tab (Lines saved: 85)
- **Component**: `tabs/PluginsTab.vue` (364 lines)
- **Composable**: `composables/usePluginConnection.ts` (91 lines)
- **Features**: Nautobot, CheckMK, and Netmiko integration with connection testing

#### 9. Cache Tab (Lines saved: 1,016)
- **Component**: `tabs/CacheTab.vue` (897 lines)
- **Composable**: `composables/useCacheManagement.ts` (486 lines)
- **Features**: Cache settings, statistics display, cache browser with multiple views (devices, routes, MAC table, CDP, JSON blobs), clear cache operations

**Final Stats**:
- **Original**: 5,504 lines
- **Current**: 2,805 lines
- **Total Reduction**: 2,699 lines (49.0% smaller!)

### 📋 Remaining Tabs

#### Priority Order for Refactoring:

1. **Scheduler Tab** (Already uses sub-component)
   - Just needs wrapper component
   - Uses `SchedulerManagement` component

## Directory Structure

```
frontend/src/views/settings/
├── tabs/
│   ├── JobsTab.vue ✅
│   ├── GeneralTab.vue ✅
│   ├── PluginsTab.vue ✅
│   ├── SchedulerTab.vue (TODO)
│   ├── TemplatesTab.vue ✅
│   ├── CommandsTab.vue ✅
│   ├── InventoryTab.vue ✅
│   ├── CacheTab.vue ✅
│   ├── ProfileTab.vue ✅
│   └── CanvasTab.vue ✅
├── components/
│   └── (Reusable components)
└── composables/
    ├── useJobMonitoring.ts ✅
    ├── usePluginConnection.ts ✅
    ├── useCacheManagement.ts ✅
    ├── useSettings.ts (TODO)
    └── useNotifications.ts (TODO)
```

## Benefits Achieved

1. **Modularity**: Each tab is self-contained and independently testable
2. **Reusability**: Composables can be reused across tabs
3. **Maintainability**: Smaller files are easier to understand and modify
4. **Performance**: Potential for lazy-loading tabs
5. **Collaboration**: Reduced merge conflicts

## Refactoring Guidelines

### Creating a New Tab Component

1. **Extract template section** from SettingsView.vue
2. **Identify required reactive state** and methods
3. **Create composable** for complex logic
4. **Update imports** in main SettingsView.vue
5. **Replace template** with component reference
6. **Remove unused code** from main file
7. **Test functionality**

### Example Pattern

```vue
<!-- tabs/ExampleTab.vue -->
<template>
  <div class="space-y-6">
    <!-- Tab content -->
  </div>
</template>

<script setup lang="ts">
import { useExample } from '../composables/useExample'

const {
  state,
  methods
} = useExample()
</script>
```

### Composable Pattern

```typescript
// composables/useExample.ts
import { ref, reactive } from 'vue'
import { useNotificationStore } from '@/stores/notificationStore'
import { makeAuthenticatedRequest } from '@/utils/api'

export function useExample() {
  const notificationStore = useNotificationStore()

  // State
  const loading = ref(false)
  const data = reactive({})

  // Methods
  const loadData = async () => {
    loading.value = true
    try {
      // Implementation
    } catch (error) {
      notificationStore.addNotification({
        title: 'Error',
        message: 'Failed to load data',
        type: 'error'
      })
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    data,
    loadData
  }
}
```

## Next Steps

1. Continue extracting remaining tabs in priority order
2. Extract shared functionality into composables
3. Consider creating reusable UI components
4. Add unit tests for composables
5. Document component APIs

## Estimated Final Size

**Target**: ~2,500-3,000 lines (from 5,504)
- Main SettingsView: ~500-700 lines (navigation + tab switching)
- 10 Tab components: ~200-400 lines each
- 5-10 Composables: ~100-300 lines each
- Reusable components: ~50-200 lines each

**Expected reduction**: ~45-50% smaller main file
