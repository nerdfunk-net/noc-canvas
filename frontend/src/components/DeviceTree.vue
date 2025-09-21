<template>
  <div class="device-tree w-full h-full bg-white border-r border-gray-200 flex flex-col">
    <!-- Tree Controls -->
    <div class="bg-white border-b border-gray-200 p-2 space-y-2 flex-shrink-0">
      <!-- Filter Input -->
      <div class="flex space-x-2">
        <select
          v-model="filterType"
          class="px-2 py-1 text-xs bg-white border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-400 disabled:bg-gray-50 disabled:cursor-not-allowed"
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
          placeholder="Search..."
          class="flex-1 px-2 py-1 text-xs bg-white border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-400 placeholder-gray-400"
        />
      </div>

      <!-- Group By Selection -->
      <div class="flex items-center space-x-2" :class="{ 'opacity-50': !isNautobotConfigured }">
        <span class="text-xs text-gray-600">Group:</span>
        <select
          v-model="groupBy"
          class="px-2 py-1 text-xs bg-white border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-400 disabled:bg-gray-50 disabled:cursor-not-allowed"
          :disabled="!isNautobotConfigured"
        >
          <option value="location">Location</option>
          <option value="role">Role</option>
          <option value="status">Status</option>
          <option value="device_type">Type</option>
        </select>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading && devices.length === 0" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <svg class="w-6 h-6 text-blue-500 animate-spin mx-auto mb-2" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <p class="text-xs text-gray-500">Loading...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex-1 flex items-center justify-center">
      <div class="text-center px-2">
        <svg class="w-6 h-6 text-red-500 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="text-xs font-medium text-red-600">Error</p>
        <p class="text-xs text-red-500 mt-1">{{ error }}</p>
      </div>
    </div>

    <!-- Not Configured State -->
    <div v-else-if="!isNautobotConfigured" class="flex-1 flex items-center justify-center">
      <div class="text-center px-2">
        <svg class="w-8 h-8 text-gray-400 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <p class="text-xs font-medium text-gray-600 mb-2">Not Configured</p>
        <router-link
          to="/settings"
          class="inline-flex items-center px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          Settings
        </router-link>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="filteredDevices.length === 0 && !loading" class="flex-1 flex items-center justify-center">
      <div class="text-center px-2">
        <svg class="w-6 h-6 text-gray-400 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <p class="text-xs font-medium text-gray-600">
          {{ devices.length === 0 ? 'No devices' : 'No matches' }}
        </p>
      </div>
    </div>

    <!-- Device Tree -->
    <div v-if="filteredDevices.length > 0 && !loading" class="flex-1 overflow-y-auto custom-scrollbar">
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
            <svg
              :class="expandedGroups.has(groupName) ? 'rotate-90' : 'rotate-0'"
              class="w-3 h-3 text-gray-400 transition-transform duration-150 flex-shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
            <span class="text-xs">{{ getGroupEmoji() }}</span>
            <span class="truncate">{{ groupName || 'Unknown' }}</span>
            <span class="px-1.5 py-0.5 text-xs bg-gray-200 text-gray-600 rounded-full flex-shrink-0">{{ group.length }}</span>
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
            class="device-item px-2 py-1.5 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-b-0 transition-colors group"
            :class="{ 'bg-blue-50 border-blue-200': selectedDevice?.id === device.id }"
          >
            <div class="flex items-center space-x-2 min-w-0">
              <!-- Device Status & Icon -->
              <div class="flex items-center space-x-1 flex-shrink-0">
                <div
                  class="w-2 h-2 rounded-full"
                  :class="getStatusColor(device.status?.name)"
                  :title="device.status?.name || 'Unknown'"
                ></div>
                <span class="text-sm">{{ getDeviceEmoji(device) }}</span>
              </div>

              <!-- Device Info -->
              <div class="flex-1 min-w-0">
                <div class="font-medium text-xs text-gray-900 truncate">
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
                  class="w-5 h-5 flex items-center justify-center text-gray-400 hover:text-blue-600 transition-colors rounded"
                  title="View"
                >
                  <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                </button>
                <button
                  @click.stop="addToCanvas(device)"
                  class="w-5 h-5 flex items-center justify-center text-gray-400 hover:text-green-600 transition-colors rounded"
                  title="Add"
                >
                  <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
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
import { useDevicesStore, type Device } from '@/stores/devices'
import { useCanvasStore } from '@/stores/canvas'

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
const deviceStore = useDevicesStore()
const canvasStore = useCanvasStore()

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
  console.log('👁️ Eye icon clicked - viewing device:', device.name)
  
  // Find the device on the canvas by Nautobot ID
  const canvasDevice = deviceStore.findDeviceByNautobotId(device.id)
  
  if (canvasDevice) {
    console.log('✅ Device found on canvas:', canvasDevice.name)
    
    // Use viewport dimensions to center the device
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight
    
    // Calculate center position for the device
    canvasStore.setPosition({
      x: viewportWidth / 2 - (canvasDevice.position_x + 40) * canvasStore.scale,
      y: viewportHeight / 2 - (canvasDevice.position_y + 40) * canvasStore.scale
    })
    
    // Also select the device on canvas
    deviceStore.setSelectedDevice(canvasDevice)
    
    console.log('✅ Device centered on canvas')
  } else {
    console.log('❌ Device not found on canvas:', device.name)
    // Optional: Show a notification that the device is not on the canvas
  }
}

const addToCanvas = async (device: NautobotDevice) => {
  console.log('➕ Plus icon clicked - adding device to canvas:', device.name)
  
  // Check for duplicate by name first (same logic as drag/drop)
  let existingDevice = deviceStore.findDeviceByName(device.name)
  
  // If not found by name, check by nautobot_id
  if (!existingDevice) {
    existingDevice = deviceStore.findDeviceByNautobotId(device.id)
  }

  if (existingDevice) {
    console.log('⚠️ Device already exists on canvas:', device.name)
    
    // Center on existing device instead (same as eye icon functionality)
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight

    canvasStore.setPosition({
      x: viewportWidth / 2 - (existingDevice.position_x + 40) * canvasStore.scale,
      y: viewportHeight / 2 - (existingDevice.position_y + 40) * canvasStore.scale
    })
    
    // Select the existing device on canvas
    deviceStore.setSelectedDevice(existingDevice)
    
    console.log('✅ Centered on existing device:', existingDevice.name)
    return
  }

  try {
    // Map Nautobot device type to canvas device type (same logic as drag/drop)
    const mapNautobotDeviceType = (nautobotDevice: NautobotDevice): 'router' | 'switch' | 'firewall' | 'vpn_gateway' => {
      const role = nautobotDevice.role?.name?.toLowerCase() || ''
      const deviceType = nautobotDevice.device_type?.model?.toLowerCase() || ''

      // Map based on role first, then device type
      if (role.includes('router') || deviceType.includes('router')) {
        return 'router'
      }
      if (role.includes('switch') || deviceType.includes('switch')) {
        return 'switch'
      }
      if (role.includes('firewall') || deviceType.includes('firewall')) {
        return 'firewall'
      }
      if (role.includes('vpn') || deviceType.includes('vpn')) {
        return 'vpn_gateway'
      }

      // Default to router for network devices
      return 'router'
    }

    // Place the device in center of current view
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight
    
    // Calculate center position in canvas coordinates
    const centerX = (viewportWidth / 2 - canvasStore.position.x) / canvasStore.scale
    const centerY = (viewportHeight / 2 - canvasStore.position.y) / canvasStore.scale

    // Create the device (same as drag/drop logic)
    const newDevice = await deviceStore.createDevice({
      name: device.name,
      device_type: mapNautobotDeviceType(device),
      ip_address: device.primary_ip4?.address?.split('/')[0], // Remove CIDR notation
      position_x: centerX - 40, // Center the device
      position_y: centerY - 40,
      properties: JSON.stringify({
        nautobot_id: device.id,
        location: device.location?.name,
        role: device.role?.name,
        status: device.status?.name,
        device_model: device.device_type?.model,
        last_backup: device.cf_last_backup
      })
    })
    
    console.log('✅ Device added to canvas successfully:', newDevice.name)
    
    // Also emit the event for backward compatibility
    emit('deviceAddedToCanvas', device)
    
  } catch (error) {
    console.error('❌ Failed to add device to canvas:', error)
  }
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

const getGroupEmoji = (): string => {
  // Return emoji based on current groupBy setting
  switch (groupBy.value) {
    case 'location':
      return '📍'
    case 'role':
      return '👤'
    case 'status':
      return '🔄'
    case 'device_type':
      return '🖥️'
    default:
      return '📁'
  }
}

const getDeviceEmoji = (device: any): string => {
  // Return emoji based on device type or role
  const deviceType = device.device_type?.model?.toLowerCase() || ''
  const role = device.role?.name?.toLowerCase() || ''

  if (deviceType.includes('router') || role.includes('router')) return '🔀'
  if (deviceType.includes('switch') || role.includes('switch')) return '🔁'
  if (deviceType.includes('firewall') || role.includes('firewall')) return '🛡️'
  if (deviceType.includes('server') || role.includes('server')) return '🖥️'
  if (deviceType.includes('access') || role.includes('access')) return '📡'
  if (deviceType.includes('wireless') || role.includes('wireless')) return '📶'
  if (deviceType.includes('phone') || role.includes('phone')) return '📞'

  return '📡' // Default network device
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
  background: white;
}

.group-header {
  font-weight: 500;
  line-height: 1.2;
}

.device-item {
  user-select: none;
  min-height: 28px;
}

/* Custom scrollbar */
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e0 transparent;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 2px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

/* Compact spacing */
.device-tree .mb-1 {
  margin-bottom: 1px;
}

/* Text overflow handling */
.truncate {
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
}

/* Smooth transitions */
.transition-colors {
  transition: background-color 0.15s ease;
}

.transition-opacity {
  transition: opacity 0.15s ease;
}

.transition-transform {
  transition: transform 0.15s ease;
}

/* Rotate utilities */
.rotate-0 {
  transform: rotate(0deg);
}

.rotate-90 {
  transform: rotate(90deg);
}

/* Focus states */
select:focus,
input:focus {
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

/* Remove any yellow or colored backgrounds */
.device-tree * {
  background-color: transparent;
}

.device-tree .bg-white {
  background-color: white !important;
}

.device-tree .bg-gray-50 {
  background-color: #f9fafb !important;
}

.device-tree .bg-gray-100 {
  background-color: #f3f4f6 !important;
}

.device-tree .bg-blue-50 {
  background-color: #eff6ff !important;
}

/* Ensure no yellow backgrounds anywhere */
.device-tree {
  background-color: white !important;
}
</style>