<template>
  <MainLayout>
    <div class="p-6">
      <div class="max-w-6xl mx-auto">
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-900">Device Inventory</h1>
          <button
            @click="refreshInventory"
            class="btn-primary"
            :disabled="deviceStore.loading"
          >
            {{ deviceStore.loading ? 'Refreshing...' : 'Refresh' }}
          </button>
        </div>

        <!-- Inventory Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <div
            v-for="device in deviceStore.devices"
            :key="device.id"
            class="card p-4 hover:shadow-lg transition-shadow cursor-pointer"
            @click="selectDevice(device)"
            :class="{ 'ring-2 ring-primary-500': deviceStore.selectedDevice?.id === device.id }"
          >
            <div class="flex items-start justify-between">
              <div class="flex items-center space-x-3">
                <div class="text-2xl">
                  {{ getDeviceIcon(device.device_type) }}
                </div>
                <div>
                  <h3 class="font-medium text-gray-900">{{ device.name }}</h3>
                  <p class="text-sm text-gray-500">{{ device.device_type }}</p>
                  <p v-if="device.ip_address" class="text-xs text-gray-400">
                    {{ device.ip_address }}
                  </p>
                </div>
              </div>
              <div class="flex space-x-1">
                <button
                  @click.stop="editDevice(device)"
                  class="text-gray-400 hover:text-primary-600"
                >
                  ✏️
                </button>
                <button
                  @click.stop="deleteDevice(device)"
                  class="text-gray-400 hover:text-red-600"
                >
                  🗑️
                </button>
              </div>
            </div>

            <div v-if="device.properties" class="mt-3 text-xs text-gray-600">
              <div class="font-medium mb-1">Properties:</div>
              <pre class="whitespace-pre-wrap">{{ formatProperties(device.properties) }}</pre>
            </div>

            <div class="mt-3 text-xs text-gray-500">
              Position: {{ Math.round(device.position_x) }}, {{ Math.round(device.position_y) }}
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
            <router-link to="/dashboard" class="btn-primary">
              Go to Canvas
            </router-link>
          </div>
        </div>

        <!-- Device Details Modal -->
        <div
          v-if="showDeviceModal"
          class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          @click="closeModal"
        >
          <div
            class="bg-white rounded-lg p-6 max-w-md w-full mx-4"
            @click.stop
          >
            <h2 class="text-lg font-semibold mb-4">
              {{ editingDevice ? 'Edit Device' : 'Device Details' }}
            </h2>

            <form v-if="editingDevice" @submit.prevent="saveDevice">
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Name
                  </label>
                  <input
                    v-model="deviceForm.name"
                    type="text"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    IP Address
                  </label>
                  <input
                    v-model="deviceForm.ip_address"
                    type="text"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>

                <div class="flex justify-end space-x-2">
                  <button
                    type="button"
                    @click="closeModal"
                    class="btn-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    class="btn-primary"
                    :disabled="saving"
                  >
                    {{ saving ? 'Saving...' : 'Save' }}
                  </button>
                </div>
              </div>
            </form>

            <div v-else>
              <div class="space-y-2 text-sm">
                <div><strong>Type:</strong> {{ deviceStore.selectedDevice?.device_type }}</div>
                <div v-if="deviceStore.selectedDevice?.ip_address">
                  <strong>IP:</strong> {{ deviceStore.selectedDevice.ip_address }}
                </div>
                <div>
                  <strong>Position:</strong>
                  {{ Math.round(deviceStore.selectedDevice?.position_x || 0) }},
                  {{ Math.round(deviceStore.selectedDevice?.position_y || 0) }}
                </div>
              </div>

              <div class="flex justify-end space-x-2 mt-4">
                <button
                  @click="closeModal"
                  class="btn-secondary"
                >
                  Close
                </button>
                <button
                  @click="editDevice(deviceStore.selectedDevice!)"
                  class="btn-primary"
                >
                  Edit
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import MainLayout from '@/layouts/MainLayout.vue'
import { useDevicesStore, type Device } from '@/stores/devices'

const deviceStore = useDevicesStore()

const showDeviceModal = ref(false)
const editingDevice = ref(false)
const saving = ref(false)

const deviceForm = reactive({
  name: '',
  ip_address: ''
})

const getDeviceIcon = (type: string) => {
  const icons = {
    router: '🔀',
    switch: '🔁',
    firewall: '🛡️',
    vpn_gateway: '🔐'
  }
  return icons[type as keyof typeof icons] || '📡'
}

const formatProperties = (properties: string | null) => {
  if (!properties) return 'None'
  try {
    return JSON.stringify(JSON.parse(properties), null, 2)
  } catch {
    return properties
  }
}

const selectDevice = (device: Device) => {
  deviceStore.setSelectedDevice(device)
  showDeviceModal.value = true
  editingDevice.value = false
}

const editDevice = (device: Device) => {
  deviceStore.setSelectedDevice(device)
  deviceForm.name = device.name
  deviceForm.ip_address = device.ip_address || ''
  editingDevice.value = true
  showDeviceModal.value = true
}

const saveDevice = async () => {
  if (!deviceStore.selectedDevice) return

  saving.value = true
  try {
    await deviceStore.updateDevice(deviceStore.selectedDevice.id, {
      name: deviceForm.name,
      ip_address: deviceForm.ip_address || undefined
    })
    closeModal()
  } catch (error) {
    console.error('Failed to save device:', error)
  } finally {
    saving.value = false
  }
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

const closeModal = () => {
  showDeviceModal.value = false
  editingDevice.value = false
  deviceStore.setSelectedDevice(null)
}

const refreshInventory = async () => {
  await deviceStore.fetchDevices()
}

// Load initial data
refreshInventory()
</script>