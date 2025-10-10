<template>
  <div
    v-if="show"
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    @click.self="close"
    data-modal="true"
  >
    <div class="bg-white rounded-lg shadow-2xl w-[90vw] max-w-5xl max-h-[90vh] flex flex-col" data-modal="true">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-600 to-blue-700">
        <h3 class="text-xl font-semibold text-white flex items-center gap-2">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Device Overview
        </h3>
        <button
          @click.stop="close"
          class="text-white hover:text-gray-200 transition-colors p-2 rounded-lg hover:bg-blue-800"
          type="button"
          aria-label="Close overview"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex-1 flex items-center justify-center p-8">
        <div class="text-center">
          <div class="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
          <p class="text-gray-600 text-lg">Loading device information...</p>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="flex-1 flex items-center justify-center p-8">
        <div class="bg-red-50 border-2 border-red-200 rounded-xl p-8 max-w-md">
          <div class="flex items-start gap-4">
            <svg class="w-8 h-8 text-red-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <h4 class="font-semibold text-red-900 text-lg mb-2">Error Loading Device</h4>
              <p class="text-red-700">{{ error }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Content -->
      <div v-else-if="device" class="flex-1 overflow-y-auto p-6">
        <!-- Device Name Header -->
        <div class="mb-6 pb-6 border-b border-gray-200">
          <h2 class="text-3xl font-bold text-gray-900 mb-2">{{ device.name }}</h2>
          <div class="flex items-center gap-4 text-sm">
            <span v-if="device.status" class="px-3 py-1 rounded-full font-medium"
                  :class="getStatusColor(device.status?.name)">
              {{ device.status.name }}
            </span>
            <span v-if="device.role" class="text-gray-600">
              <span class="font-medium">Role:</span> {{ device.role.name }}
            </span>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Basic Information -->
          <div class="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-6 border border-blue-200">
            <h3 class="text-lg font-semibold text-blue-900 mb-4 flex items-center gap-2">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Basic Information
            </h3>
            <dl class="space-y-3">
              <div v-if="device.primary_ip4">
                <dt class="text-sm font-medium text-blue-700">Primary IPv4</dt>
                <dd class="text-base text-blue-900 font-mono">{{ device.primary_ip4.address }}</dd>
              </div>
              <div v-if="device.serial">
                <dt class="text-sm font-medium text-blue-700">Serial Number</dt>
                <dd class="text-base text-blue-900">{{ device.serial }}</dd>
              </div>
              <div v-if="device.asset_tag">
                <dt class="text-sm font-medium text-blue-700">Asset Tag</dt>
                <dd class="text-base text-blue-900">{{ device.asset_tag }}</dd>
              </div>
            </dl>
          </div>

          <!-- Hardware Information -->
          <div class="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-6 border border-purple-200">
            <h3 class="text-lg font-semibold text-purple-900 mb-4 flex items-center gap-2">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
              </svg>
              Hardware
            </h3>
            <dl class="space-y-3">
              <div v-if="device.device_type">
                <dt class="text-sm font-medium text-purple-700">Model</dt>
                <dd class="text-base text-purple-900">{{ device.device_type.model }}</dd>
              </div>
              <div v-if="device.device_type?.manufacturer">
                <dt class="text-sm font-medium text-purple-700">Manufacturer</dt>
                <dd class="text-base text-purple-900">{{ device.device_type.manufacturer.name }}</dd>
              </div>
              <div v-if="device.platform">
                <dt class="text-sm font-medium text-purple-700">Platform</dt>
                <dd class="text-base text-purple-900">{{ device.platform.name }}</dd>
              </div>
              <div v-if="device.platform?.network_driver">
                <dt class="text-sm font-medium text-purple-700">Network Driver</dt>
                <dd class="text-base text-purple-900 font-mono">{{ device.platform.network_driver }}</dd>
              </div>
            </dl>
          </div>

          <!-- Location Information -->
          <div class="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-6 border border-green-200">
            <h3 class="text-lg font-semibold text-green-900 mb-4 flex items-center gap-2">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Location
            </h3>
            <dl class="space-y-3">
              <div v-if="device.location">
                <dt class="text-sm font-medium text-green-700">Location</dt>
                <dd class="text-base text-green-900">{{ device.location.name }}</dd>
              </div>
              <div v-if="device.rack">
                <dt class="text-sm font-medium text-green-700">Rack</dt>
                <dd class="text-base text-green-900">{{ device.rack.name }}</dd>
              </div>
              <div v-if="device.position">
                <dt class="text-sm font-medium text-green-700">Position</dt>
                <dd class="text-base text-green-900">U{{ device.position }}</dd>
              </div>
              <div v-if="device.tenant">
                <dt class="text-sm font-medium text-green-700">Tenant</dt>
                <dd class="text-base text-green-900">{{ device.tenant.name }}</dd>
              </div>
            </dl>
          </div>

          <!-- Tags and Metadata -->
          <div class="bg-gradient-to-br from-amber-50 to-amber-100 rounded-xl p-6 border border-amber-200">
            <h3 class="text-lg font-semibold text-amber-900 mb-4 flex items-center gap-2">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
              </svg>
              Tags & Metadata
            </h3>
            <div class="space-y-3">
              <div v-if="device.tags && device.tags.length > 0">
                <dt class="text-sm font-medium text-amber-700 mb-2">Tags</dt>
                <dd class="flex flex-wrap gap-2">
                  <span v-for="tag in device.tags" :key="tag.id"
                        class="px-3 py-1 bg-amber-200 text-amber-900 rounded-full text-sm font-medium">
                    {{ tag.name }}
                  </span>
                </dd>
              </div>
              <div v-if="device.comments">
                <dt class="text-sm font-medium text-amber-700">Comments</dt>
                <dd class="text-base text-amber-900 whitespace-pre-wrap">{{ device.comments }}</dd>
              </div>
            </div>
          </div>
        </div>

        <!-- Interfaces -->
        <div v-if="device.interfaces && device.interfaces.length > 0"
             class="mt-6 bg-gradient-to-br from-indigo-50 to-indigo-100 rounded-xl p-6 border border-indigo-200">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-indigo-900 flex items-center gap-2">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              Interfaces ({{ displayedInterfaces.length }})
              <span v-if="syncedInterfaces" class="text-xs font-normal text-indigo-700 ml-2">
                (Live from device)
              </span>
            </h3>
            <button
              @click="syncInterfaces"
              :disabled="syncingInterfaces"
              class="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white rounded-lg text-sm font-medium transition-colors"
            >
              <svg v-if="!syncingInterfaces" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <svg v-else class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ syncingInterfaces ? 'Syncing...' : 'Sync' }}
            </button>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="bg-indigo-200 bg-opacity-50">
                <tr>
                  <th class="px-3 py-2 text-left font-semibold text-indigo-900">Name</th>
                  <th class="px-3 py-2 text-left font-semibold text-indigo-900">Type</th>
                  <th class="px-3 py-2 text-left font-semibold text-indigo-900">Description</th>
                  <th class="px-3 py-2 text-left font-semibold text-indigo-900">Status</th>
                  <th class="px-3 py-2 text-left font-semibold text-indigo-900">Enabled</th>
                  <th class="px-3 py-2 text-left font-semibold text-indigo-900">MAC</th>
                  <th class="px-3 py-2 text-left font-semibold text-indigo-900">MTU</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-indigo-200">
                <tr v-for="iface in displayedInterfaces" :key="iface.id || iface.interface" class="hover:bg-indigo-100 transition-colors">
                  <td class="px-3 py-2 font-mono text-indigo-900 font-medium">{{ iface.name || iface.interface }}</td>
                  <td class="px-3 py-2 text-indigo-800">{{ iface.type || iface.hardware_type || '-' }}</td>
                  <td class="px-3 py-2 text-indigo-800 max-w-xs truncate" :title="iface.description">
                    {{ iface.description || '-' }}
                  </td>
                  <td class="px-3 py-2">
                    <span v-if="iface.status?.name" class="px-2 py-1 rounded-full text-xs font-medium"
                          :class="getInterfaceStatusColor(iface.status.name)">
                      {{ iface.status.name }}
                    </span>
                    <span v-else-if="iface.link_status" class="px-2 py-1 rounded-full text-xs font-medium"
                          :class="getLinkStatusColor(iface.link_status)">
                      {{ iface.link_status }}
                    </span>
                    <span v-else class="text-gray-500">-</span>
                  </td>
                  <td class="px-3 py-2">
                    <span v-if="iface.enabled !== undefined ? iface.enabled : (iface.line_protocol === 'up')" class="text-green-600 font-semibold">✓</span>
                    <span v-else class="text-red-600 font-semibold">✗</span>
                  </td>
                  <td class="px-3 py-2 font-mono text-xs text-indigo-800">{{ iface.mac_address || '-' }}</td>
                  <td class="px-3 py-2 text-indigo-800">{{ iface.mtu || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Custom Fields (if any) -->
        <div v-if="device._custom_field_data && Object.keys(device._custom_field_data).length > 0"
             class="mt-6 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-6 border border-gray-200">
          <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
            </svg>
            Custom Fields
          </h3>
          <dl class="grid grid-cols-2 gap-4">
            <div v-for="(value, key) in device._custom_field_data" :key="key">
              <dt class="text-sm font-medium text-gray-600">{{ formatFieldName(key) }}</dt>
              <dd class="text-base text-gray-900">{{ value || '-' }}</dd>
            </div>
          </dl>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
        <div class="text-sm text-gray-500">
          <span v-if="device?.id">Device ID: {{ device.id }}</span>
        </div>
        <button
          @click="close"
          class="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
        >
          Close
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { makeAuthenticatedRequest } from '@/services/api'
import { devicesApi } from '@/services/api'

interface Props {
  show: boolean
  deviceId: string
}

const props = defineProps<Props>()
const emit = defineEmits(['close'])

const device = ref<any>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const syncedInterfaces = ref<any[]>(null)
const syncingInterfaces = ref(false)

// Computed property to determine which interfaces to display
const displayedInterfaces = computed(() => {
  if (syncedInterfaces.value) {
    return syncedInterfaces.value
  }
  return device.value?.interfaces || []
})

// Sync interfaces from live device
const syncInterfaces = async () => {
  if (!props.deviceId || syncingInterfaces.value) return

  syncingInterfaces.value = true

  try {
    console.log('🔄 Syncing interfaces from device:', props.deviceId)
    const response = await devicesApi.getInterfaces(props.deviceId, true, true) // use TextFSM, bypass cache

    if (response.success && Array.isArray(response.output)) {
      syncedInterfaces.value = response.output
      console.log('✅ Synced', syncedInterfaces.value.length, 'interfaces from device')
    } else {
      console.error('❌ Failed to sync interfaces:', response.error)
      error.value = response.error || 'Failed to sync interfaces'
    }
  } catch (err: any) {
    console.error('❌ Error syncing interfaces:', err)
    error.value = err.message || 'Failed to sync interfaces from device'
  } finally {
    syncingInterfaces.value = false
  }
}

// Fetch device details
const fetchDeviceDetails = async () => {
  if (!props.deviceId) return

  loading.value = true
  error.value = null
  device.value = null

  try {
    console.log('📡 Fetching device details for:', props.deviceId)
    const response = await makeAuthenticatedRequest(`/api/nautobot/devices/${props.deviceId}/details`)
    console.log('📦 Raw response:', response)

    // Parse the JSON response
    const data = await response.json()
    console.log('📦 Parsed data:', data)
    console.log('📦 Data keys:', data ? Object.keys(data) : 'null')

    device.value = data
    console.log('✅ Device details loaded:', device.value)
    console.log('✅ Device name:', device.value?.name)
    console.log('✅ Device status:', device.value?.status)
    console.log('✅ Device role:', device.value?.role)
  } catch (err: any) {
    console.error('❌ Error fetching device details:', err)
    console.error('❌ Error response:', err.response)
    console.error('❌ Error data:', err.response?.data)
    error.value = err.response?.data?.detail || err.message || 'Failed to load device information'
  } finally {
    loading.value = false
  }
}

// Watch for show prop changes
watch(() => props.show, (newValue) => {
  if (newValue) {
    fetchDeviceDetails()
  } else {
    // Reset state when closing
    device.value = null
    error.value = null
    syncedInterfaces.value = null
    syncingInterfaces.value = false
  }
})

// Helper functions
const getStatusColor = (status: string) => {
  const statusColors: Record<string, string> = {
    'Active': 'bg-green-200 text-green-800',
    'Offline': 'bg-red-200 text-red-800',
    'Planned': 'bg-blue-200 text-blue-800',
    'Staged': 'bg-yellow-200 text-yellow-800',
    'Failed': 'bg-red-200 text-red-800',
    'Inventory': 'bg-gray-200 text-gray-800',
    'Decommissioning': 'bg-orange-200 text-orange-800',
  }
  return statusColors[status] || 'bg-gray-200 text-gray-800'
}

const getInterfaceStatusColor = (status: string) => {
  const statusColors: Record<string, string> = {
    'Active': 'bg-green-200 text-green-800',
    'Connected': 'bg-green-200 text-green-800',
    'Planned': 'bg-blue-200 text-blue-800',
    'Maintenance': 'bg-yellow-200 text-yellow-800',
    'Failed': 'bg-red-200 text-red-800',
    'Decommissioning': 'bg-orange-200 text-orange-800',
  }
  return statusColors[status] || 'bg-gray-200 text-gray-800'
}

const getLinkStatusColor = (status: string) => {
  const statusColors: Record<string, string> = {
    'up': 'bg-green-200 text-green-800',
    'down': 'bg-red-200 text-red-800',
    'admin down': 'bg-gray-200 text-gray-800',
  }
  return statusColors[status.toLowerCase()] || 'bg-gray-200 text-gray-800'
}

const formatFieldName = (key: string): string => {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

const close = () => {
  emit('close')
}
</script>

<style scoped>
/* Custom scrollbar for the content area */
.overflow-y-auto::-webkit-scrollbar {
  width: 8px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #555;
}
</style>
