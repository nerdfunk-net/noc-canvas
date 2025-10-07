<template>
  <div
    v-if="show"
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    @click.self="close"
  >
    <div class="bg-white rounded-lg shadow-xl w-[90vw] h-[85vh] max-w-7xl flex flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-600 to-blue-700">
        <h3 class="text-xl font-semibold text-white flex items-center gap-2">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          {{ deviceName }} - Interfaces
          <span v-if="isCached" class="ml-2 px-3 py-1 text-sm font-medium bg-amber-400 text-amber-900 rounded-full flex items-center gap-1">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Cached
          </span>
        </h3>
        <button
          @click="close"
          class="text-white hover:text-gray-200 transition-colors"
          type="button"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex-1 flex items-center justify-center">
        <div class="text-center">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p class="text-gray-600">Loading interfaces...</p>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="flex-1 flex items-center justify-center p-6">
        <div class="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <div class="flex items-start gap-3">
            <svg class="w-6 h-6 text-red-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <h4 class="font-medium text-red-800">Error Loading Interfaces</h4>
              <p class="text-sm text-red-700 mt-1">{{ error }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Content -->
      <div v-else-if="interfaces.length > 0" class="flex-1 flex gap-4 p-6 overflow-hidden">
        <!-- Left Panel: Interface List -->
        <div class="w-80 flex flex-col border border-gray-200 rounded-lg bg-gray-50 overflow-hidden">
          <div class="px-4 py-3 border-b border-gray-300 bg-white">
            <h4 class="font-medium text-gray-900">Interfaces ({{ interfaces.length }})</h4>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search interfaces..."
              class="mt-2 w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div class="flex-1 overflow-y-auto">
            <div
              v-for="iface in filteredInterfaces"
              :key="iface.interface"
              class="px-4 py-3 cursor-pointer transition-colors border-b border-gray-200"
              :class="{
                'bg-blue-100 border-l-4 border-l-blue-600': selectedInterface?.interface === iface.interface,
                'hover:bg-gray-100': selectedInterface?.interface !== iface.interface
              }"
              @click="selectInterface(iface)"
            >
              <div class="flex items-center justify-between">
                <span class="font-mono text-sm font-medium text-gray-900">{{ iface.interface }}</span>
                <span 
                  class="px-2 py-0.5 text-xs rounded-full"
                  :class="getStatusBadgeClass(iface.status)"
                >
                  {{ iface.status }}
                </span>
              </div>
              <div class="mt-1 text-xs text-gray-600" v-if="iface.description">
                {{ iface.description }}
              </div>
            </div>
          </div>
        </div>

        <!-- Right Panel: Interface Details -->
        <div class="flex-1 flex flex-col border border-gray-200 rounded-lg bg-white overflow-hidden">
          <div v-if="selectedInterface" class="flex flex-col h-full">
            <!-- Header -->
            <div class="px-6 py-4 border-b border-gray-200 bg-gray-50">
              <div class="flex items-center justify-between">
                <h4 class="text-lg font-semibold text-gray-900">{{ selectedInterface.interface }}</h4>
                <span 
                  class="px-3 py-1 text-sm font-medium rounded-full"
                  :class="getStatusBadgeClass(selectedInterface.status)"
                >
                  {{ selectedInterface.status }}
                </span>
              </div>
            </div>

            <!-- Details Content -->
            <div class="flex-1 overflow-y-auto p-6">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Status Section -->
                <div class="space-y-4">
                  <h5 class="text-sm font-semibold text-gray-700 uppercase tracking-wide border-b pb-2">Status</h5>
                  <dl class="space-y-3">
                    <div v-for="(value, key) in getStatusFields(selectedInterface)" :key="key">
                      <dt class="text-sm font-medium text-gray-600">{{ formatFieldName(key) }}</dt>
                      <dd class="mt-1 text-sm text-gray-900 font-mono">{{ value || 'N/A' }}</dd>
                    </div>
                  </dl>
                </div>

                <!-- Configuration Section -->
                <div class="space-y-4">
                  <h5 class="text-sm font-semibold text-gray-700 uppercase tracking-wide border-b pb-2">Configuration</h5>
                  <dl class="space-y-3">
                    <div v-for="(value, key) in getConfigFields(selectedInterface)" :key="key">
                      <dt class="text-sm font-medium text-gray-600">{{ formatFieldName(key) }}</dt>
                      <dd class="mt-1 text-sm text-gray-900 font-mono">{{ value || 'N/A' }}</dd>
                    </div>
                  </dl>
                </div>

                <!-- Traffic Section (if available) -->
                <div v-if="hasTrafficFields(selectedInterface)" class="space-y-4 md:col-span-2">
                  <h5 class="text-sm font-semibold text-gray-700 uppercase tracking-wide border-b pb-2">Traffic & Errors</h5>
                  <dl class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div v-for="(value, key) in getTrafficFields(selectedInterface)" :key="key">
                      <dt class="text-sm font-medium text-gray-600">{{ formatFieldName(key) }}</dt>
                      <dd class="mt-1 text-sm text-gray-900 font-mono">{{ value || '0' }}</dd>
                    </div>
                  </dl>
                </div>

                <!-- Additional Fields Section -->
                <div v-if="hasAdditionalFields(selectedInterface)" class="space-y-4 md:col-span-2">
                  <h5 class="text-sm font-semibold text-gray-700 uppercase tracking-wide border-b pb-2">Additional Information</h5>
                  <dl class="grid grid-cols-2 gap-4">
                    <div v-for="(value, key) in getAdditionalFields(selectedInterface)" :key="key">
                      <dt class="text-sm font-medium text-gray-600">{{ formatFieldName(key) }}</dt>
                      <dd class="mt-1 text-sm text-gray-900 font-mono break-all">{{ value || 'N/A' }}</dd>
                    </div>
                  </dl>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="flex-1 flex items-center justify-center text-gray-500">
            <div class="text-center">
              <svg class="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <p class="text-lg font-medium">Select an interface</p>
              <p class="text-sm text-gray-400 mt-1">Choose an interface from the list to view details</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="flex-1 flex items-center justify-center text-gray-500">
        <div class="text-center">
          <svg class="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
          <p class="text-lg font-medium">No interfaces found</p>
          <p class="text-sm text-gray-400 mt-1">This device has no interface data</p>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 border-t border-gray-200 bg-gray-50 flex justify-between items-center">
        <div>
          <button
            v-if="isCached && !loading"
            @click="reloadData"
            class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors flex items-center gap-2"
            type="button"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Reload Data
          </button>
        </div>
        <button
          @click="close"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
          type="button"
        >
          Close
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { devicesApi } from '@/services/api'

interface Props {
  show: boolean
  deviceId: string
  deviceName: string
}

interface InterfaceData {
  interface: string
  status: string
  protocol?: string
  description?: string
  ip_address?: string
  mtu?: string
  speed?: string
  duplex?: string
  vlan?: string
  bandwidth?: string
  [key: string]: any
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
}>()

const loading = ref(false)
const error = ref<string | null>(null)
const interfaces = ref<InterfaceData[]>([])
const selectedInterface = ref<InterfaceData | null>(null)
const searchQuery = ref('')
const isCached = ref(false)

const filteredInterfaces = computed(() => {
  if (!searchQuery.value.trim()) {
    return interfaces.value
  }
  const query = searchQuery.value.toLowerCase()
  return interfaces.value.filter(iface =>
    iface.interface.toLowerCase().includes(query) ||
    (iface.description && iface.description.toLowerCase().includes(query))
  )
})

const getStatusBadgeClass = (status: string) => {
  const statusLower = status?.toLowerCase() || ''
  if (statusLower.includes('up')) {
    return 'bg-green-100 text-green-800'
  } else if (statusLower.includes('down')) {
    return 'bg-red-100 text-red-800'
  } else if (statusLower.includes('admin')) {
    return 'bg-yellow-100 text-yellow-800'
  }
  return 'bg-gray-100 text-gray-800'
}

const formatFieldName = (key: string): string => {
  return key
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

// Define field categories
const STATUS_FIELDS = ['status', 'protocol', 'link_status', 'line_protocol']
const CONFIG_FIELDS = ['description', 'ip_address', 'mtu', 'speed', 'duplex', 'vlan', 'bandwidth', 'encapsulation', 'hardware_type']
const TRAFFIC_FIELDS = ['input_packets', 'output_packets', 'input_errors', 'output_errors', 'input_rate', 'output_rate', 'crc', 'collisions']

const getStatusFields = (iface: InterfaceData) => {
  const fields: Record<string, any> = {}
  STATUS_FIELDS.forEach(field => {
    if (iface[field] !== undefined && iface[field] !== null) {
      fields[field] = iface[field]
    }
  })
  return fields
}

const getConfigFields = (iface: InterfaceData) => {
  const fields: Record<string, any> = {}
  CONFIG_FIELDS.forEach(field => {
    if (iface[field] !== undefined && iface[field] !== null) {
      fields[field] = iface[field]
    }
  })
  return fields
}

const getTrafficFields = (iface: InterfaceData) => {
  const fields: Record<string, any> = {}
  TRAFFIC_FIELDS.forEach(field => {
    if (iface[field] !== undefined && iface[field] !== null) {
      fields[field] = iface[field]
    }
  })
  return fields
}

const getAdditionalFields = (iface: InterfaceData) => {
  const fields: Record<string, any> = {}
  const excludeFields = new Set([
    'interface',
    ...STATUS_FIELDS,
    ...CONFIG_FIELDS,
    ...TRAFFIC_FIELDS
  ])
  
  Object.keys(iface).forEach(key => {
    if (!excludeFields.has(key) && iface[key] !== undefined && iface[key] !== null && iface[key] !== '') {
      fields[key] = iface[key]
    }
  })
  
  return fields
}

const hasTrafficFields = (iface: InterfaceData) => {
  return Object.keys(getTrafficFields(iface)).length > 0
}

const hasAdditionalFields = (iface: InterfaceData) => {
  return Object.keys(getAdditionalFields(iface)).length > 0
}

const selectInterface = (iface: InterfaceData) => {
  selectedInterface.value = iface
}

const loadInterfaces = async (disableCache: boolean = false) => {
  if (!props.deviceId) return

  loading.value = true
  error.value = null
  interfaces.value = []
  selectedInterface.value = null
  isCached.value = false

  try {
    console.log('🔄 Loading interfaces for device:', props.deviceId, disableCache ? '(bypassing cache)' : '')
    const response = await devicesApi.getInterfaces(props.deviceId, true, disableCache) // true = use TextFSM, disableCache parameter

    if (response.success && Array.isArray(response.output)) {
      interfaces.value = response.output
      isCached.value = response.cached === true
      console.log('✅ Loaded', interfaces.value.length, 'interfaces', isCached.value ? '(from cache)' : '(fresh data)')
      
      // Auto-select first interface
      if (interfaces.value.length > 0) {
        selectedInterface.value = interfaces.value[0]
      }
    } else {
      error.value = response.error || 'Failed to parse interface data'
    }
  } catch (err: any) {
    console.error('❌ Failed to load interfaces:', err)
    error.value = err.response?.data?.detail || err.message || 'Failed to load interfaces'
  } finally {
    loading.value = false
  }
}

const reloadData = () => {
  loadInterfaces(true) // Pass true to disable cache
}

const close = () => {
  emit('close')
}

// Load interfaces when modal is shown
watch(
  () => props.show,
  (newShow) => {
    if (newShow) {
      loadInterfaces()
    } else {
      // Reset state when closing
      searchQuery.value = ''
      selectedInterface.value = null
    }
  },
  { immediate: false }
)
</script>
