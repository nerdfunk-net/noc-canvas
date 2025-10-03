<template>
  <div
    v-if="show"
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    @click.self="close"
  >
    <div class="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] flex flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b border-gray-200">
        <div class="flex items-center space-x-3">
          <div class="p-2 bg-blue-100 rounded-lg">
            <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
              ></path>
            </svg>
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900">
              {{ title }}
            </h3>
            <p class="text-sm text-gray-500">{{ subtitle }}</p>
          </div>
        </div>
        <button
          @click="close"
          class="text-gray-400 hover:text-gray-600 transition-colors"
          type="button"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            ></path>
          </svg>
        </button>
      </div>

      <!-- Summary Stats -->
      <div class="grid grid-cols-3 gap-4 p-6 bg-gray-50 border-b border-gray-200">
        <div class="text-center">
          <div class="text-3xl font-bold text-green-600">{{ addedDevices.length }}</div>
          <div class="text-sm text-gray-600 mt-1">Added</div>
        </div>
        <div class="text-center">
          <div class="text-3xl font-bold text-yellow-600">{{ skippedDevices.length }}</div>
          <div class="text-sm text-gray-600 mt-1">Skipped</div>
        </div>
        <div class="text-center">
          <div class="text-3xl font-bold text-red-600">{{ notFoundDevices.length }}</div>
          <div class="text-sm text-gray-600 mt-1">Not Found</div>
        </div>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto p-6">
        <!-- Added Devices -->
        <div v-if="addedDevices.length > 0" class="mb-6">
          <h4 class="text-sm font-semibold text-gray-900 mb-3 flex items-center">
            <span class="inline-flex items-center justify-center w-6 h-6 bg-green-100 text-green-600 rounded-full text-xs font-bold mr-2">
              ✓
            </span>
            Successfully Added ({{ addedDevices.length }})
          </h4>
          <div class="space-y-2">
            <div
              v-for="device in addedDevices"
              :key="device.name"
              class="bg-green-50 border border-green-200 rounded-lg p-3 hover:bg-green-100 transition-colors"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="font-medium text-gray-900">{{ device.name }}</div>
                  <div class="text-sm text-gray-600 mt-1 space-y-1">
                    <div v-if="device.ipAddress" class="flex items-center">
                      <svg class="w-4 h-4 mr-1.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"
                        ></path>
                      </svg>
                      <span>{{ device.ipAddress }}</span>
                    </div>
                    <div v-if="device.role" class="flex items-center">
                      <svg class="w-4 h-4 mr-1.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                        ></path>
                      </svg>
                      <span>{{ device.role }}</span>
                    </div>
                    <div v-if="device.location" class="flex items-center">
                      <svg class="w-4 h-4 mr-1.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                        ></path>
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                        ></path>
                      </svg>
                      <span>{{ device.location }}</span>
                    </div>
                  </div>
                </div>
                <span class="ml-3 px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded">
                  Added
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Skipped Devices -->
        <div v-if="skippedDevices.length > 0" class="mb-6">
          <h4 class="text-sm font-semibold text-gray-900 mb-3 flex items-center">
            <span class="inline-flex items-center justify-center w-6 h-6 bg-yellow-100 text-yellow-600 rounded-full text-xs font-bold mr-2">
              ⚠
            </span>
            Already on Canvas ({{ skippedDevices.length }})
          </h4>
          <div class="space-y-2">
            <div
              v-for="device in skippedDevices"
              :key="device.name"
              class="bg-yellow-50 border border-yellow-200 rounded-lg p-3"
            >
              <div class="flex items-center justify-between">
                <div class="flex-1">
                  <div class="font-medium text-gray-900">{{ device.name }}</div>
                  <div v-if="device.ipAddress" class="text-sm text-gray-600 mt-1">
                    {{ device.ipAddress }}
                  </div>
                </div>
                <button
                  v-if="!device.hasConnection && device.deviceId"
                  @click="addConnection(device.deviceId!)"
                  class="ml-3 px-3 py-1 text-xs font-medium bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                >
                  Add Connection
                </button>
                <span
                  v-else
                  class="ml-3 px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded"
                >
                  {{ device.hasConnection ? 'Connected' : 'Exists' }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Not Found Devices -->
        <div v-if="notFoundDevices.length > 0">
          <h4 class="text-sm font-semibold text-gray-900 mb-3 flex items-center">
            <span class="inline-flex items-center justify-center w-6 h-6 bg-red-100 text-red-600 rounded-full text-xs font-bold mr-2">
              ✕
            </span>
            Not Found in Inventory ({{ notFoundDevices.length }})
          </h4>
          <div class="space-y-2">
            <div
              v-for="device in notFoundDevices"
              :key="device"
              class="bg-red-50 border border-red-200 rounded-lg p-3"
            >
              <div class="flex items-center justify-between">
                <div class="font-medium text-gray-900">{{ device }}</div>
                <span class="ml-3 px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded">
                  Missing
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="addedDevices.length === 0 && skippedDevices.length === 0 && notFoundDevices.length === 0" class="text-center py-12">
          <svg class="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
            ></path>
          </svg>
          <p class="text-gray-500">No neighbors discovered</p>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex justify-end items-center gap-3 p-6 border-t border-gray-200 bg-gray-50">
        <button
          @click="close"
          class="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
          type="button"
        >
          Close
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useDevicesStore } from '@/stores/devices'

interface NeighborDevice {
  name: string
  ipAddress?: string
  role?: string
  location?: string
  status?: string
  deviceId?: number
  hasConnection?: boolean
}

interface NeighborDiscoveryResult {
  success: boolean
  error?: string
  addedDevices: NeighborDevice[]
  skippedDevices: NeighborDevice[]
  notFoundDevices: string[]
  sourceDeviceId?: number
}

interface Props {
  show: boolean
  result: NeighborDiscoveryResult | null
  title?: string
  subtitle?: string
}

interface Emits {
  (e: 'close'): void
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Neighbor Discovery Results',
  subtitle: 'CDP neighbor discovery completed',
})

const emit = defineEmits<Emits>()

const deviceStore = useDevicesStore()

// Computed properties to safely access result data
const addedDevices = computed(() => props.result?.addedDevices || [])
const skippedDevices = computed(() => props.result?.skippedDevices || [])
const notFoundDevices = computed(() => props.result?.notFoundDevices || [])

const close = () => {
  emit('close')
}

const addConnection = (targetDeviceId: number) => {
  if (!props.result?.sourceDeviceId) {
    console.error('❌ No source device ID available')
    return
  }

  try {
    deviceStore.createConnection({
      source_device_id: props.result.sourceDeviceId,
      target_device_id: targetDeviceId,
      connection_type: 'ethernet',
    })
    console.log(`🔗 Created connection between devices ${props.result.sourceDeviceId} and ${targetDeviceId}`)

    // Update the hasConnection flag for this device in skipped list
    const device = skippedDevices.value.find(d => d.deviceId === targetDeviceId)
    if (device) {
      device.hasConnection = true
    }
  } catch (error) {
    console.error('❌ Failed to create connection:', error)
  }
}
</script>
