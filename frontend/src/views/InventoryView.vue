<template>
  <MainLayout>
    <div class="p-6">
      <div class="max-w-6xl mx-auto">
        <div class="mb-6">
          <h1 class="text-2xl font-bold text-gray-900">Device Inventory</h1>
          <p class="text-gray-600 mt-1">Manage devices currently placed on the canvas</p>
        </div>

        <!-- Inventory Grid -->
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-3">
          <div
            v-for="device in deviceStore.devices"
            :key="device.id"
            class="bg-white rounded-xl border border-gray-200 p-3 hover:shadow-md hover:border-primary-300 transition-all duration-200 cursor-pointer group"
            @click="selectDevice(device)"
            :class="{ 'ring-2 ring-primary-500 border-primary-500': deviceStore.selectedDevice?.id === device.id }"
          >
            <!-- Header with icon and name -->
            <div class="flex items-start justify-between mb-3">
              <div class="flex items-center space-x-2">
                <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
                  <img
                    :src="getDeviceIconUrl(device.device_type)"
                    :alt="`${device.device_type} icon`"
                    class="w-5 h-5 object-contain"
                  />
                </div>
                <div class="min-w-0 flex-1">
                  <h3 class="font-semibold text-gray-900 text-sm truncate">{{ device.name }}</h3>
                  <p class="text-xs text-gray-500 truncate">{{ device.device_type }}</p>
                </div>
              </div>
              <div class="flex space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  @click.stop="viewDevice(device)"
                  class="w-6 h-6 rounded-md bg-gray-100 hover:bg-blue-100 text-gray-500 hover:text-blue-600 transition-colors flex items-center justify-center"
                  title="View device details"
                >
                  <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                  </svg>
                </button>
                <button
                  @click.stop="deleteDevice(device)"
                  class="w-6 h-6 rounded-md bg-gray-100 hover:bg-red-100 text-gray-500 hover:text-red-600 transition-colors flex items-center justify-center"
                  title="Delete device"
                >
                  <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                  </svg>
                </button>
              </div>
            </div>

            <!-- Device info -->
            <div class="space-y-2">
              <div v-if="device.ip_address" class="flex items-center text-xs text-gray-600">
                <svg class="w-3 h-3 mr-1.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9-9a9 9 0 00-9 9m9-9v18"></path>
                </svg>
                {{ device.ip_address }}
              </div>

              <div v-if="getDevicePlatform(device.properties)" class="flex items-center text-xs text-gray-600">
                <svg class="w-3 h-3 mr-1.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"></path>
                </svg>
                {{ getDevicePlatform(device.properties) }}
              </div>

              <div class="flex items-center text-xs text-gray-600">
                <svg class="w-3 h-3 mr-1.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                </svg>
                {{ Math.round(device.position_x) }}, {{ Math.round(device.position_y) }}
              </div>
            </div>

            <!-- Device properties (modern display) -->
            <div v-if="device.properties" class="mt-3 pt-3 border-t border-gray-100">
              <div class="space-y-1">
                <template v-for="[key, value] in getFormattedProperties(device.properties)" :key="key">
                  <div class="flex justify-between items-center text-xs">
                    <span class="text-gray-500 font-medium capitalize">{{ key.replace(/_/g, ' ') }}:</span>
                    <span class="text-gray-700 truncate ml-2 max-w-24" :title="String(value)">{{ String(value) }}</span>
                  </div>
                </template>
              </div>
            </div>
          </div>

          <!-- Empty State -->
          <div
            v-if="deviceStore.devices.length === 0 && !deviceStore.loading"
            class="col-span-full text-center py-12"
          >
            <div class="text-4xl mb-4">📡</div>
            <h3 class="text-lg font-medium text-gray-900 mb-2">No devices found</h3>
            <p class="text-gray-500 mb-4">
              Start by dragging device templates from the inventory panel to the canvas.
            </p>
            <router-link to="/dashboard" class="btn-primary"> Go to Canvas </router-link>
          </div>
        </div>

        <!-- Device Details Modal -->
        <div
          v-if="showDeviceModal"
          class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          @click="closeModal"
        >
          <div class="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto" @click.stop>
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-lg font-semibold text-gray-900">Device Details</h2>
              <button
                @click="closeModal"
                class="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </button>
            </div>

            <div v-if="deviceStore.selectedDevice">
              <!-- Basic Device Info -->
              <div class="bg-gray-50 rounded-lg p-4 mb-6">
                <div class="flex items-center space-x-3 mb-3">
                  <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
                    <img
                      :src="getDeviceIconUrl(deviceStore.selectedDevice.device_type)"
                      :alt="`${deviceStore.selectedDevice.device_type} icon`"
                      class="w-6 h-6 object-contain"
                    />
                  </div>
                  <div>
                    <h3 class="text-lg font-semibold text-gray-900">{{ deviceStore.selectedDevice.name }}</h3>
                    <p class="text-sm text-gray-600">{{ deviceStore.selectedDevice.device_type }}</p>
                  </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div v-if="deviceStore.selectedDevice.ip_address">
                    <span class="text-gray-500 font-medium">IP Address:</span>
                    <span class="text-gray-900 ml-1">{{ deviceStore.selectedDevice.ip_address }}</span>
                  </div>
                  <div v-if="getDevicePlatform(deviceStore.selectedDevice.properties)">
                    <span class="text-gray-500 font-medium">Platform:</span>
                    <span class="text-gray-900 ml-1">{{ getDevicePlatform(deviceStore.selectedDevice.properties) }}</span>
                  </div>
                  <div>
                    <span class="text-gray-500 font-medium">Position:</span>
                    <span class="text-gray-900 ml-1">
                      {{ Math.round(deviceStore.selectedDevice.position_x) }}, {{ Math.round(deviceStore.selectedDevice.position_y) }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Loading state for Nautobot data -->
              <div v-if="loadingNautobotData" class="text-center py-8">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p class="text-gray-600">Loading device data from Nautobot...</p>
              </div>

              <!-- Error state -->
              <div v-else-if="nautobotDataError" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                <div class="flex items-center">
                  <svg class="w-5 h-5 text-red-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                  <p class="text-red-700 text-sm">{{ nautobotDataError }}</p>
                </div>
              </div>

              <!-- Full Nautobot Data -->
              <div v-else-if="nautobotData" class="space-y-6">
                <h4 class="text-md font-semibold text-gray-900 mb-3">Complete Device Information</h4>

                <!-- Basic Device Information -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div class="bg-white border border-gray-200 rounded-lg p-4">
                    <h5 class="font-medium text-gray-900 mb-3">Device Details</h5>
                    <div class="space-y-2 text-sm">
                      <div v-if="nautobotData.hostname"><strong>Hostname:</strong> {{ nautobotData.hostname }}</div>
                      <div v-if="nautobotData.serial"><strong>Serial:</strong> {{ nautobotData.serial }}</div>
                      <div v-if="nautobotData.asset_tag"><strong>Asset Tag:</strong> {{ nautobotData.asset_tag }}</div>
                      <div v-if="nautobotData.position"><strong>Position:</strong> {{ nautobotData.position }}</div>
                      <div v-if="nautobotData.face"><strong>Face:</strong> {{ nautobotData.face }}</div>
                    </div>
                  </div>

                  <div class="bg-white border border-gray-200 rounded-lg p-4">
                    <h5 class="font-medium text-gray-900 mb-3">Network Information</h5>
                    <div class="space-y-2 text-sm">
                      <div v-if="nautobotData.primary_ip4">
                        <strong>Primary IPv4:</strong> {{ nautobotData.primary_ip4.address }}
                        <div v-if="nautobotData.primary_ip4.dns_name" class="text-gray-600 ml-4">
                          DNS: {{ nautobotData.primary_ip4.dns_name }}
                        </div>
                      </div>
                      <div v-if="nautobotData.platform">
                        <strong>Platform:</strong> {{ nautobotData.platform.name }}
                        <div v-if="nautobotData.platform.network_driver" class="text-gray-600 ml-4">
                          Driver: {{ nautobotData.platform.network_driver }}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Interfaces Section -->
                <div v-if="nautobotData.interfaces && nautobotData.interfaces.length > 0" class="bg-white border border-gray-200 rounded-lg">
                  <div class="p-4 border-b border-gray-200">
                    <h5 class="font-medium text-gray-900">Interfaces ({{ nautobotData.interfaces.length }})</h5>
                  </div>
                  <div class="max-h-64 overflow-y-auto">
                    <table class="min-w-full divide-y divide-gray-200 text-sm">
                      <thead class="bg-gray-50">
                        <tr>
                          <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                          <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                          <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                          <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">IP Addresses</th>
                        </tr>
                      </thead>
                      <tbody class="bg-white divide-y divide-gray-200">
                        <tr v-for="iface in nautobotData.interfaces" :key="iface.id" class="hover:bg-gray-50">
                          <td class="px-4 py-2 font-medium text-gray-900">{{ iface.name }}</td>
                          <td class="px-4 py-2 text-gray-600">{{ iface.type || '-' }}</td>
                          <td class="px-4 py-2">
                            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                                  :class="iface.enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'">
                              {{ iface.enabled ? 'Enabled' : 'Disabled' }}
                            </span>
                          </td>
                          <td class="px-4 py-2">
                            <div v-if="iface.ip_addresses && iface.ip_addresses.length > 0" class="space-y-1">
                              <div v-for="ip in iface.ip_addresses" :key="ip.address" class="text-xs">
                                {{ ip.address }}
                              </div>
                            </div>
                            <span v-else class="text-gray-400">-</span>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                <!-- VRFs Section -->
                <div v-if="nautobotData.vrfs && nautobotData.vrfs.length > 0" class="bg-white border border-gray-200 rounded-lg p-4">
                  <h5 class="font-medium text-gray-900 mb-3">VRFs ({{ nautobotData.vrfs.length }})</h5>
                  <div class="space-y-2">
                    <div v-for="vrf in nautobotData.vrfs" :key="vrf.id" class="flex justify-between items-center text-sm border-b border-gray-100 pb-2">
                      <div>
                        <strong>{{ vrf.name }}</strong>
                        <div v-if="vrf.description" class="text-gray-600">{{ vrf.description }}</div>
                      </div>
                      <div class="text-right">
                        <div v-if="vrf.rd" class="font-mono text-xs">RD: {{ vrf.rd }}</div>
                        <div v-if="vrf.namespace" class="text-gray-600 text-xs">{{ vrf.namespace.name }}</div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Configuration Context -->
                <div v-if="nautobotData.config_context || nautobotData.local_config_context_data" class="bg-white border border-gray-200 rounded-lg p-4">
                  <h5 class="font-medium text-gray-900 mb-3">Configuration Context</h5>
                  <div class="space-y-4">
                    <div v-if="nautobotData.config_context">
                      <h6 class="text-sm font-medium text-gray-700 mb-2">Global Context</h6>
                      <pre class="bg-gray-50 p-3 rounded text-xs overflow-x-auto">{{ formatValue(nautobotData.config_context) }}</pre>
                    </div>
                    <div v-if="nautobotData.local_config_context_data">
                      <h6 class="text-sm font-medium text-gray-700 mb-2">Local Context</h6>
                      <pre class="bg-gray-50 p-3 rounded text-xs overflow-x-auto">{{ formatValue(nautobotData.local_config_context_data) }}</pre>
                    </div>
                  </div>
                </div>

                <!-- Custom Fields -->
                <div v-if="nautobotData.custom_field_data" class="bg-white border border-gray-200 rounded-lg p-4">
                  <h5 class="font-medium text-gray-900 mb-3">Custom Fields</h5>
                  <div class="space-y-2 text-sm">
                    <template v-for="[key, value] in Object.entries(nautobotData.custom_field_data)" :key="key">
                      <div class="flex justify-between items-start border-b border-gray-100 pb-2">
                        <span class="font-medium text-gray-600 capitalize">{{ formatKey(key) }}:</span>
                        <span class="text-gray-900 text-right max-w-md">{{ formatValue(value) }}</span>
                      </div>
                    </template>
                  </div>
                </div>
              </div>

              <!-- Local Properties Fallback -->
              <div v-else-if="deviceStore.selectedDevice.properties" class="space-y-4">
                <h4 class="text-md font-semibold text-gray-900 mb-3">Local Device Properties</h4>
                <div class="bg-white border border-gray-200 rounded-lg p-4">
                  <div class="space-y-2">
                    <template v-for="[key, value] in getFormattedProperties(deviceStore.selectedDevice.properties)" :key="key">
                      <div class="flex justify-between items-start">
                        <span class="text-sm font-medium text-gray-600 capitalize">{{ key.replace(/_/g, ' ') }}:</span>
                        <span class="text-sm text-gray-900 ml-4 text-right max-w-md">{{ String(value) }}</span>
                      </div>
                    </template>
                  </div>
                </div>
              </div>

              <div class="flex justify-between mt-6">
                <button
                  @click="refreshNautobotData"
                  :disabled="loadingNautobotData"
                  class="btn-secondary"
                >
                  {{ loadingNautobotData ? 'Refreshing...' : 'Refresh Data' }}
                </button>
                <button @click="closeModal" class="btn-primary">Close</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import MainLayout from '@/layouts/MainLayout.vue'
import { useDevicesStore, type Device } from '@/stores/devices'
import { useDeviceIcons } from '@/composables/useDeviceIcons'

const deviceStore = useDevicesStore()
const { getDeviceIconUrl } = useDeviceIcons()

const showDeviceModal = ref(false)
const loadingNautobotData = ref(false)
const nautobotDataError = ref<string | null>(null)
const nautobotData = ref<any>(null)

const getFormattedProperties = (properties: string | null): [string, any][] => {
  if (!properties) return []
  try {
    const parsed = JSON.parse(properties)
    if (typeof parsed === 'object' && parsed !== null) {
      return Object.entries(parsed).slice(0, 4) // Limit to first 4 properties for compact display
    }
    return [['value', parsed]]
  } catch {
    return [['raw', properties]]
  }
}

const getDevicePlatform = (properties: string | null): string | null => {
  if (!properties) return null
  try {
    const parsed = JSON.parse(properties)
    return parsed.platform || null
  } catch {
    return null
  }
}


const formatKey = (key: string): string => {
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const formatValue = (value: any): string => {
  if (typeof value === 'object' && value !== null) {
    return JSON.stringify(value, null, 2)
  }
  return String(value)
}

const selectDevice = (device: Device) => {
  deviceStore.setSelectedDevice(device)
  showDeviceModal.value = true
  loadNautobotData(device)
}

const viewDevice = (device: Device) => {
  deviceStore.setSelectedDevice(device)
  showDeviceModal.value = true
  loadNautobotData(device)
}



const deleteDevice = async (device: Device) => {
  if (confirm(`Are you sure you want to delete ${device.name}?`)) {
    try {
      await deviceStore.deleteDevice(device.id)
    } catch (error) {
      console.error('Failed to delete device:', error)
    }
  }
}

const loadNautobotData = async (device: Device) => {
  if (!device.properties) return

  try {
    const properties = JSON.parse(device.properties)
    if (!properties.nautobot_id) return

    loadingNautobotData.value = true
    nautobotDataError.value = null

    const response = await fetch(`/api/nautobot/devices/${properties.nautobot_id}/details`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch device data: ${response.statusText}`)
    }

    nautobotData.value = await response.json()
  } catch (error) {
    console.error('Failed to load Nautobot data:', error)
    nautobotDataError.value = error instanceof Error ? error.message : 'Failed to load device data'
  } finally {
    loadingNautobotData.value = false
  }
}

const refreshNautobotData = () => {
  if (deviceStore.selectedDevice) {
    loadNautobotData(deviceStore.selectedDevice)
  }
}

const closeModal = () => {
  showDeviceModal.value = false
  deviceStore.setSelectedDevice(null)
  nautobotData.value = null
  nautobotDataError.value = null
  loadingNautobotData.value = false
}

// Devices are loaded from the canvas state automatically
</script>
