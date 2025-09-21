<template>
  <div class="device-tree">
    <!-- Tree Controls -->
    <div class="mb-4 space-y-2">
      <!-- Filter Input -->
      <div class="flex space-x-2">
        <select
          v-model="filterType"
          class="px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          :disabled="!isNautobotConfigured"
        >
          <option value="name">Name</option>
          <option value="ip">IP</option>
          <option value="location">Location</option>
          <option value="status">Status</option>
          <option value="role">Role</option>
        </select>
        <input
          v-model="filterValue"
          type="text"
          placeholder="Enter search value..."
          class="flex-1 px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
        />
      </div>

      <!-- Group By Selection -->
      <div class="flex items-center space-x-2" :class="{ 'opacity-50': !isNautobotConfigured }">
        <span class="text-xs text-gray-600">Group by:</span>
        <select
          v-model="groupBy"
          class="px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          :disabled="!isNautobotConfigured"
        >
          <option value="location">Location</option>
          <option value="role">Role</option>
          <option value="status">Status</option>
          <option value="device_type">Device Type</option>
        </select>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading && devices.length === 0" class="text-center py-4">
      <i class="fas fa-spinner fa-spin text-gray-400 mb-2"></i>
      <p class="text-xs text-gray-500">Loading devices...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-4">
      <i class="fas fa-exclamation-triangle text-red-400 mb-2"></i>
      <p class="text-xs text-red-600">{{ error }}</p>
    </div>

    <!-- Not Configured State -->
    <div v-else-if="!isNautobotConfigured" class="text-center py-6">
      <i class="fas fa-cog text-gray-400 text-2xl mb-3"></i>
      <p class="text-xs text-gray-500 mb-2">Nautobot not configured</p>
      <p class="text-xs text-gray-400 mb-3">Configure Nautobot settings to load devices</p>
      <router-link
        to="/settings"
        class="inline-flex items-center px-3 py-1.5 text-xs bg-primary-600 text-white rounded hover:bg-primary-700 transition-colors"
      >
        <i class="fas fa-cog mr-1"></i>
        Go to Settings
      </router-link>
    </div>

    <!-- Empty State -->
    <div v-else-if="filteredDevices.length === 0 && !loading" class="text-center py-4">
      <i class="fas fa-search text-gray-400 mb-2"></i>
      <p class="text-xs text-gray-500">
        {{ devices.length === 0 ? 'No devices found' : 'No devices match your search' }}
      </p>
      <div class="text-xs text-gray-400 mt-2">
        <div>Total devices: {{ devices.length }}</div>
        <div>Filtered devices: {{ filteredDevices.length }}</div>
        <div>Groups: {{ Object.keys(groupedDevices).length }}</div>
        <div>Expanded: {{ expandedGroups.size }}</div>
        <div>Filter: "{{ debouncedFilterValue }}"</div>
      </div>
    </div>

    <!-- Device Tree -->
    <div v-if="filteredDevices.length > 0 && !loading" class="overflow-y-auto" style="max-height: calc(100vh - 200px);">
      <div
        v-for="(group, groupName) in groupedDevices"
        :key="groupName"
        class="mb-1"
      >
        <!-- Group Header -->
        <div
          @click="toggleGroup(groupName)"
          class="group-header px-2 py-1.5 bg-gray-50 hover:bg-gray-100 cursor-pointer flex items-center justify-between text-xs font-medium text-gray-700 border-b border-gray-200 sticky top-0 z-10"
        >
          <div class="flex items-center space-x-1.5 min-w-0">
            <i
              :class="expandedGroups.has(groupName) ? 'fa-chevron-down' : 'fa-chevron-right'"
              class="fas text-gray-400 transition-transform text-xs w-2.5 flex-shrink-0"
            ></i>
            <i :class="getGroupIcon()" class="text-gray-500 text-xs flex-shrink-0"></i>
            <span class="truncate">{{ groupName || 'Unknown' }}</span>
            <span class="text-gray-400 flex-shrink-0">({{ group.length }})</span>
          </div>
        </div>

        <!-- Group Content -->
        <div
          v-if="expandedGroups.has(groupName)"
          class="group-content bg-white"
        >
          <div
            v-for="device in group"
            :key="device.id"
            @click="selectDevice(device)"
            @dragstart="startDeviceDrag($event, device)"
            draggable="true"
            class="device-item px-3 py-2 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-b-0 transition-colors group"
            :class="{ 'bg-primary-50 border-primary-200': selectedDevice?.id === device.id }"
          >
            <div class="flex items-center space-x-2 min-w-0">
              <!-- Device Status Indicator -->
              <div
                class="w-2 h-2 rounded-full flex-shrink-0"
                :class="getStatusColor(device.status?.name)"
                :title="device.status?.name || 'Unknown Status'"
              ></div>

              <!-- Device Info -->
              <div class="flex-1 min-w-0">
                <div class="font-medium text-sm text-gray-900 truncate">
                  {{ device.name }}
                </div>
                <div class="text-xs text-gray-500 truncate">
                  {{ device.primary_ip4?.address || 'No IP' }}
                </div>
              </div>

              <!-- Device Actions -->
              <div class="flex items-center space-x-0.5 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                <button
                  @click.stop="viewDevice(device)"
                  class="w-5 h-5 flex items-center justify-center text-gray-400 hover:text-primary-600 transition-colors rounded"
                  title="View details"
                >
                  <i class="fas fa-eye text-xs"></i>
                </button>
                <button
                  @click.stop="addToCanvas(device)"
                  class="w-5 h-5 flex items-center justify-center text-gray-400 hover:text-green-600 transition-colors rounded"
                  title="Add to canvas"
                >
                  <i class="fas fa-plus text-xs"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { nautobotApi, type NautobotDevice } from '@/services/api'
import { useSettingsStore } from '@/stores/settings'

// Debounce function for search
function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout>
  return (...args: Parameters<T>) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

const settingsStore = useSettingsStore()

// Props
interface Props {
  groupByProp?: string
}

const props = withDefaults(defineProps<Props>(), {
  groupByProp: 'location'
})

// Emits
const emit = defineEmits<{
  deviceSelected: [device: NautobotDevice]
  deviceAddedToCanvas: [device: NautobotDevice]
}>()

// Reactive state
const devices = ref<NautobotDevice[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const filterValue = ref('')
const filterType = ref('name')
const debouncedFilterValue = ref('')
const groupBy = ref(props.groupByProp)
const selectedDevice = ref<NautobotDevice | null>(null)
const expandedGroups = ref(new Set<string>())

// Debounced search to improve performance with large datasets
const debouncedUpdateFilter = debounce((value: string) => {
  debouncedFilterValue.value = value
}, 300)

// Watch for filter changes and debounce them
watch(filterValue, (newValue) => {
  console.log('🔍 Filter value changed:', newValue)
  debouncedUpdateFilter(newValue)
})

// Initialize debounced filter value
debouncedFilterValue.value = filterValue.value

// Computed property to check if Nautobot is properly configured
const isNautobotConfigured = computed(() => {
  const isConfigured = !!(settingsStore.settings.nautobot.enabled &&
                          settingsStore.settings.nautobot.url &&
                          settingsStore.settings.nautobot.token)
  console.log('🔧 isNautobotConfigured check:', {
    enabled: settingsStore.settings.nautobot.enabled,
    hasUrl: !!settingsStore.settings.nautobot.url,
    hasToken: !!settingsStore.settings.nautobot.token,
    result: isConfigured
  })
  return isConfigured
})

// Computed properties
const filteredDevices = computed(() => {
  console.log('🔍 Computing filtered devices...')
  console.log('Total devices:', devices.value.length)
  console.log('Filter type:', filterType.value)
  console.log('Filter value:', debouncedFilterValue.value)

  if (!debouncedFilterValue.value) {
    console.log('✅ No filter, returning all devices:', devices.value.length)
    return devices.value
  }

  const searchTerm = debouncedFilterValue.value.toLowerCase()
  const filtered = devices.value.filter(device => {
    switch (filterType.value) {
      case 'name':
        return device.name.toLowerCase().includes(searchTerm)
      case 'ip':
        return device.primary_ip4?.address.toLowerCase().includes(searchTerm)
      case 'location':
        return device.location?.name.toLowerCase().includes(searchTerm)
      case 'status':
        return device.status?.name.toLowerCase().includes(searchTerm)
      case 'role':
        return device.role?.name.toLowerCase().includes(searchTerm)
      default:
        return false
    }
  })

  console.log('🔍 Filtered devices:', filtered.length)
  return filtered
})

const groupedDevices = computed(() => {
  console.log('📁 Computing grouped devices...')
  console.log('Group by:', groupBy.value)
  console.log('Filtered devices for grouping:', filteredDevices.value.length)

  const groups: Record<string, NautobotDevice[]> = {}

  filteredDevices.value.forEach(device => {
    let groupValue: string

    switch (groupBy.value) {
      case 'location':
        groupValue = device.location?.name || 'Unknown Location'
        break
      case 'role':
        groupValue = device.role?.name || 'Unknown Role'
        break
      case 'status':
        groupValue = device.status?.name || 'Unknown Status'
        break
      case 'device_type':
        groupValue = device.device_type?.model || 'Unknown Type'
        break
      default:
        groupValue = 'Unknown'
    }

    if (!groups[groupValue]) {
      groups[groupValue] = []
    }
    groups[groupValue].push(device)
  })

  // Sort groups alphabetically and sort devices within each group
  const sortedGroups: Record<string, NautobotDevice[]> = {}
  Object.keys(groups)
    .sort()
    .forEach(key => {
      sortedGroups[key] = groups[key].sort((a, b) => a.name.localeCompare(b.name))
    })

  console.log('📊 Final groups:', Object.keys(sortedGroups))
  console.log('📊 Group details:', sortedGroups)

  return sortedGroups
})

// Methods
const loadDevices = async () => {
  // Check if Nautobot is properly configured before attempting to load
  if (!isNautobotConfigured.value) {
    devices.value = []
    error.value = null
    loading.value = false
    return
  }

  loading.value = true
  error.value = null

  try {
    console.log('🔍 Loading devices from API...')
    const response = await nautobotApi.getAllDevices()
    console.log('📡 API Response:', response)
    devices.value = response.devices || []
    console.log('📊 Devices loaded:', devices.value.length)
    console.log('🔍 First device sample:', devices.value[0])

    // Auto-expand first group only for large datasets
    setTimeout(() => {
      const groupNames = Object.keys(groupedDevices.value)
      console.log('📁 Groups created:', groupNames)
      console.log('🎯 Filtered devices count:', filteredDevices.value.length)

      if (devices.value.length < 50) {
        // Small dataset: expand first 3 groups
        groupNames.slice(0, 3).forEach(name => expandedGroups.value.add(name))
      } else if (devices.value.length < 200) {
        // Medium dataset: expand first 2 groups
        groupNames.slice(0, 2).forEach(name => expandedGroups.value.add(name))
      } else {
        // Large dataset: expand only first group
        if (groupNames.length > 0) {
          expandedGroups.value.add(groupNames[0])
        }
      }
      console.log('📂 Expanded groups:', Array.from(expandedGroups.value))
    }, 0)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load devices'
    console.error('Failed to load devices:', err)
  } finally {
    loading.value = false
  }
}

const refreshDevices = () => {
  loadDevices()
}

const toggleGroup = (groupName: string) => {
  if (expandedGroups.value.has(groupName)) {
    expandedGroups.value.delete(groupName)
  } else {
    expandedGroups.value.add(groupName)
  }
}

const selectDevice = (device: NautobotDevice) => {
  selectedDevice.value = device
  emit('deviceSelected', device)
}

const viewDevice = (device: NautobotDevice) => {
  // TODO: Implement device details view
  console.log('View device:', device)
}

const addToCanvas = (device: NautobotDevice) => {
  emit('deviceAddedToCanvas', device)
}

const startDeviceDrag = (event: DragEvent, device: NautobotDevice) => {
  if (event.dataTransfer) {
    const dragData = {
      type: 'nautobot-device',
      device
    }
    event.dataTransfer.setData('application/json', JSON.stringify(dragData))
    event.dataTransfer.effectAllowed = 'copy'
  }
}

const getGroupIcon = (): string => {
  // Return icon based on current groupBy setting
  switch (groupBy.value) {
    case 'location':
      return 'fas fa-map-marker-alt'
    case 'role':
      return 'fas fa-tag'
    case 'status':
      return 'fas fa-circle'
    case 'device_type':
      return 'fas fa-server'
    default:
      return 'fas fa-folder'
  }
}

const getStatusColor = (status?: string): string => {
  switch (status?.toLowerCase()) {
    case 'active':
      return 'bg-green-500'
    case 'offline':
      return 'bg-red-500'
    case 'planned':
      return 'bg-blue-500'
    case 'staging':
      return 'bg-yellow-500'
    case 'failed':
      return 'bg-red-600'
    case 'decommissioning':
      return 'bg-orange-500'
    default:
      return 'bg-gray-400'
  }
}

// Watch for group by changes to auto-expand some groups
watch(groupBy, () => {
  expandedGroups.value.clear()
  // Auto-expand groups when grouping changes based on dataset size
  setTimeout(() => {
    const groupNames = Object.keys(groupedDevices.value)
    if (devices.value.length < 50) {
      groupNames.slice(0, 3).forEach(name => expandedGroups.value.add(name))
    } else if (devices.value.length < 200) {
      groupNames.slice(0, 2).forEach(name => expandedGroups.value.add(name))
    } else {
      if (groupNames.length > 0) {
        expandedGroups.value.add(groupNames[0])
      }
    }
  }, 0)
})

// Watch for Nautobot configuration changes
watch(isNautobotConfigured, (newValue) => {
  if (newValue) {
    // Configuration became valid, load devices
    loadDevices()
  } else {
    // Configuration became invalid, clear devices
    devices.value = []
    error.value = null
  }
})

// Mount
onMounted(async () => {
  // Wait for settings to load before attempting to load devices
  if (!settingsStore.settings.nautobot.url && !settingsStore.loading) {
    await settingsStore.loadSettings()
  }
  loadDevices()
})

// Expose methods to parent component
defineExpose({
  refreshDevices,
  selectedDevice
})
</script>

<style scoped>
.device-tree {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.group-header:hover .fas.fa-chevron-right,
.group-header:hover .fas.fa-chevron-down {
  color: #6b7280;
}

.group-header {
  font-weight: 500;
  line-height: 1.2;
}

.device-item:hover .opacity-0 {
  opacity: 1;
}

.device-item {
  user-select: none;
  min-height: 40px;
}

/* Custom scrollbar */
.device-tree .overflow-y-auto {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e0 #f7fafc;
}

.device-tree .overflow-y-auto::-webkit-scrollbar {
  width: 4px;
}

.device-tree .overflow-y-auto::-webkit-scrollbar-track {
  background: #f7fafc;
  border-radius: 2px;
}

.device-tree .overflow-y-auto::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 2px;
}

.device-tree .overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}

/* Compact spacing for large datasets */
.device-tree .mb-1 {
  margin-bottom: 2px;
}

/* Sticky header optimization */
.sticky {
  backdrop-filter: blur(2px);
}

/* Text overflow handling */
.truncate {
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
}

/* Improve performance for hover effects */
.transition-colors {
  transition: background-color 0.1s ease-in-out;
}

.transition-opacity {
  transition: opacity 0.1s ease-in-out;
}

/* Loading state optimization */
.loading-skeleton {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
}

@keyframes loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>