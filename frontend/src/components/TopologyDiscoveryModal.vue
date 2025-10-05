<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto">
    <!-- Backdrop -->
    <div class="fixed inset-0 bg-black bg-opacity-50 transition-opacity" @click="close"></div>

    <!-- Modal -->
    <div class="flex min-h-screen items-center justify-center p-4">
      <div class="relative bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <!-- Header -->
        <div class="bg-gradient-to-r from-indigo-600 to-indigo-700 px-6 py-4">
          <div class="flex items-center justify-between">
            <h2 class="text-2xl font-bold text-white flex items-center gap-2">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Discover Topology
            </h2>
            <button @click="close" class="text-white hover:text-gray-200 transition">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Content -->
        <div class="p-6 overflow-y-auto" style="max-height: calc(90vh - 180px)">
          <!-- Discovery Not Started -->
          <div v-if="!discovering && !discoveryResult">
            <!-- Device Selection -->
            <div class="mb-6">
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Select Devices to Discover
              </label>
              <div class="mb-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p class="text-sm text-blue-800">
                  <strong>Note:</strong> Discovery requires devices with Nautobot IDs. Devices added manually may not have network connectivity configured.
                  For best results, use devices from the Inventory panel.
                </p>
              </div>
              <select
                v-model="selectedDevices"
                multiple
                class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 h-48"
              >
                <option v-for="device in canvasDevices" :key="device.id" :value="device.deviceId">
                  {{ device.name }} ({{ device.ip_address || 'No IP' }})
                </option>
              </select>
              <p class="text-xs text-gray-500 mt-1">
                {{ selectedDevices.length === 0 ? 'Select devices to discover' : `${selectedDevices.length} device(s) selected` }}
              </p>
            </div>

            <!-- Discovery Options -->
            <div class="mb-6">
              <h3 class="text-sm font-medium text-gray-700 mb-3">Data to Discover</h3>
              <div class="grid grid-cols-2 gap-3">
                <label class="flex items-center gap-2 p-2 border rounded cursor-pointer hover:bg-gray-50" :class="{ 'bg-indigo-50 border-indigo-300': includeStaticRoutes }">
                  <input type="checkbox" v-model="includeStaticRoutes" class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded" />
                  <span class="text-sm text-gray-700">Static Routes</span>
                </label>
                <label class="flex items-center gap-2 p-2 border rounded cursor-pointer hover:bg-gray-50" :class="{ 'bg-indigo-50 border-indigo-300': includeOspfRoutes }">
                  <input type="checkbox" v-model="includeOspfRoutes" class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded" />
                  <span class="text-sm text-gray-700">OSPF Routes</span>
                </label>
                <label class="flex items-center gap-2 p-2 border rounded cursor-pointer hover:bg-gray-50" :class="{ 'bg-indigo-50 border-indigo-300': includeBgpRoutes }">
                  <input type="checkbox" v-model="includeBgpRoutes" class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded" />
                  <span class="text-sm text-gray-700">BGP Routes</span>
                </label>
                <label class="flex items-center gap-2 p-2 border rounded cursor-pointer hover:bg-gray-50" :class="{ 'bg-indigo-50 border-indigo-300': includeMacTable }">
                  <input type="checkbox" v-model="includeMacTable" class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded" />
                  <span class="text-sm text-gray-700">MAC Address Table</span>
                </label>
                <label class="flex items-center gap-2 p-2 border rounded cursor-pointer hover:bg-gray-50" :class="{ 'bg-indigo-50 border-indigo-300': includeCdpNeighbors }">
                  <input type="checkbox" v-model="includeCdpNeighbors" class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded" />
                  <span class="text-sm text-gray-700">CDP Neighbors</span>
                </label>
              </div>
            </div>

            <!-- Execution Mode -->
            <div class="mb-6">
              <h3 class="text-sm font-medium text-gray-700 mb-3">Execution Mode</h3>
              <div class="space-y-2">
                <label class="flex items-start gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50" :class="{ 'bg-indigo-50 border-indigo-300': !runInBackground }">
                  <input type="radio" :value="false" v-model="runInBackground" class="mt-1 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300" />
                  <div>
                    <div class="font-medium text-gray-900">Synchronous (Blocking)</div>
                    <div class="text-sm text-gray-500">Best for small number of devices (1-3). Waits for completion.</div>
                  </div>
                </label>
                <label class="flex items-start gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50" :class="{ 'bg-indigo-50 border-indigo-300': runInBackground }">
                  <input type="radio" :value="true" v-model="runInBackground" class="mt-1 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300" />
                  <div>
                    <div class="font-medium text-gray-900">Asynchronous (Background via Celery)</div>
                    <div class="text-sm text-gray-500">✨ Recommended for all workloads. Runs in Celery worker with real-time progress tracking.</div>
                  </div>
                </label>
              </div>
              
              <!-- Celery Info Box (shown when background mode selected) -->
              <div v-if="runInBackground" class="mt-3 p-3 bg-indigo-50 border border-indigo-200 rounded-lg">
                <div class="flex items-start gap-2">
                  <svg class="w-5 h-5 text-indigo-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div class="text-sm text-indigo-800">
                    <p class="font-medium mb-1">Celery Worker Required</p>
                    <p>This mode requires a Celery worker to be running. Jobs are processed in parallel with real-time progress updates. You can cancel running jobs at any time.</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Cache Option -->
            <div class="mb-4">
              <label class="flex items-center gap-2">
                <input type="checkbox" v-model="cacheResults" class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded" />
                <span class="text-sm text-gray-700">Cache results to database</span>
              </label>
            </div>
          </div>

          <!-- Discovery In Progress -->
          <div v-else-if="discovering && !jobScheduled">
            <div class="space-y-4">
              <!-- Overall Progress -->
              <div>
                <div class="flex items-center justify-between mb-2">
                  <h3 class="text-sm font-medium text-gray-700">Overall Progress</h3>
                  <span class="text-sm font-medium text-indigo-600">{{ progress?.progress_percentage || 0 }}%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2.5">
                  <div class="bg-indigo-600 h-2.5 rounded-full transition-all duration-300" :style="{ width: `${progress?.progress_percentage || 0}%` }"></div>
                </div>
                <p class="text-xs text-gray-500 mt-1">
                  {{ progress?.completed_devices || 0 }} of {{ progress?.total_devices || 0 }} devices completed
                  <span v-if="progress?.failed_devices > 0" class="text-red-600">({{ progress.failed_devices }} failed)</span>
                </p>
              </div>

              <!-- Device Progress List -->
              <div v-if="progress?.devices" class="border rounded-lg divide-y max-h-64 overflow-y-auto">
                <div v-for="device in progress.devices" :key="device.device_id" class="p-3">
                  <div class="flex items-center justify-between mb-1">
                    <div class="flex items-center gap-2">
                      <span v-if="device.status === 'completed'" class="text-green-600">✓</span>
                      <span v-else-if="device.status === 'failed'" class="text-red-600">✗</span>
                      <span v-else-if="device.status === 'in_progress'" class="animate-spin">⟳</span>
                      <span v-else class="text-gray-400">○</span>
                      <span class="text-sm font-medium text-gray-900">{{ device.device_name }}</span>
                    </div>
                    <span class="text-xs font-medium" :class="{
                      'text-green-600': device.status === 'completed',
                      'text-red-600': device.status === 'failed',
                      'text-indigo-600': device.status === 'in_progress',
                      'text-gray-400': device.status === 'pending'
                    }">
                      {{ device.progress_percentage }}%
                    </span>
                  </div>
                  <p v-if="device.current_task" class="text-xs text-gray-500 ml-6">{{ device.current_task }}</p>
                  <p v-if="device.error" class="text-xs text-red-600 ml-6">{{ device.error }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Job Scheduled (Background Mode) -->
          <div v-else-if="jobScheduled">
            <div class="bg-indigo-50 border border-indigo-200 rounded-lg p-6 mb-4">
              <div class="flex items-start gap-3">
                <svg class="w-6 h-6 text-indigo-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <div class="flex-1">
                  <h4 class="font-semibold text-indigo-900 text-lg">Job Scheduled in Background</h4>
                  <p class="text-sm text-indigo-700 mt-2">
                    Your topology discovery job has been scheduled and will be processed by a Celery worker.
                  </p>
                  <div class="mt-3 space-y-2">
                    <div class="flex items-center gap-2 text-sm text-indigo-800">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                      </svg>
                      <span><strong>Job ID:</strong> <code class="bg-white px-2 py-0.5 rounded">{{ jobId }}</code></span>
                    </div>
                    <div class="flex items-center gap-2 text-sm text-indigo-800">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span><strong>Devices:</strong> {{ selectedDevices.length }}</span>
                    </div>
                  </div>
                  <div class="mt-4 p-3 bg-white rounded border border-indigo-200">
                    <p class="text-xs text-indigo-700">
                      <strong>💡 Tip:</strong> You can monitor the job progress in Settings → Background Jobs. The job will process your devices in parallel and cache the results when complete.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Discovery Complete -->
          <div v-else-if="discoveryResult">
            <div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
              <div class="flex items-start gap-3">
                <svg class="w-5 h-5 text-green-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <h4 class="font-medium text-green-800">Discovery Complete!</h4>
                  <p class="text-sm text-green-700 mt-1">
                    Successfully discovered {{ discoveryResult.successful_devices }} of {{ discoveryResult.total_devices }} devices
                    in {{ discoveryResult.duration_seconds.toFixed(1) }} seconds
                  </p>
                </div>
              </div>
            </div>

            <!-- Summary -->
            <div class="grid grid-cols-3 gap-4 mb-4">
              <div class="bg-blue-50 rounded-lg p-4 text-center">
                <div class="text-2xl font-bold text-blue-600">{{ discoveryResult.total_devices }}</div>
                <div class="text-sm text-gray-600">Total Devices</div>
              </div>
              <div class="bg-green-50 rounded-lg p-4 text-center">
                <div class="text-2xl font-bold text-green-600">{{ discoveryResult.successful_devices }}</div>
                <div class="text-sm text-gray-600">Successful</div>
              </div>
              <div class="bg-red-50 rounded-lg p-4 text-center">
                <div class="text-2xl font-bold text-red-600">{{ discoveryResult.failed_devices }}</div>
                <div class="text-sm text-gray-600">Failed</div>
              </div>
            </div>

            <!-- Errors (if any) -->
            <div v-if="discoveryResult.failed_devices > 0" class="bg-red-50 border border-red-200 rounded-lg p-4">
              <h4 class="font-medium text-red-800 mb-2">Errors</h4>
              <div class="space-y-1">
                <div v-for="(error, deviceId) in discoveryResult.errors" :key="deviceId" class="text-sm text-red-700">
                  <span class="font-medium">{{ deviceId }}:</span> {{ error }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="bg-gray-50 px-6 py-4 flex items-center justify-between border-t">
          <button
            @click="close"
            class="px-4 py-2 text-gray-700 hover:text-gray-900 font-medium transition"
          >
            {{ discoveryResult || jobScheduled ? 'Close' : 'Cancel' }}
          </button>
          <div class="flex gap-3">
            <!-- Show Jobs Button (when job scheduled) -->
            <button
              v-if="jobScheduled"
              @click="navigateToJobs"
              class="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition font-medium flex items-center gap-2"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              Show Jobs
            </button>
            <button
              v-if="!discovering && !discoveryResult && !jobScheduled"
              @click="startDiscovery"
              :disabled="selectedDevices.length === 0 || !hasDataSelected"
              class="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition font-medium"
            >
              Start Discovery
            </button>
            <button
              v-if="discoveryResult"
              @click="openTopologyBuilder"
              class="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium"
            >
              Build Topology
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { makeAuthenticatedRequest } from '@/services/api'
import { useDevicesStore } from '@/stores/devices'

const props = defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  close: []
  openBuilder: []
}>()

const router = useRouter()
const deviceStore = useDevicesStore()

// State
const selectedDevices = ref<string[]>([])
const includeStaticRoutes = ref(true)
const includeOspfRoutes = ref(true)
const includeBgpRoutes = ref(true)
const includeMacTable = ref(true)
const includeCdpNeighbors = ref(true)
const runInBackground = ref(false)
const cacheResults = ref(true)
const discovering = ref(false)
const jobId = ref<string | null>(null)
const progress = ref<any>(null)
const discoveryResult = ref<any>(null)
const jobScheduled = ref(false) // Track if async job was just scheduled
let progressInterval: any = null

// Computed
const canvasDevices = computed(() => {
  // Show all devices, but prefer those with nautobot_id or device IDs from properties
  return deviceStore.devices.map(d => {
    // Try to get device ID from various sources
    let deviceId: string | undefined = (d as any).nautobot_id

    if (!deviceId && d.properties) {
      try {
        const props = JSON.parse(d.properties)
        deviceId = props.nautobot_id || props.device_id
      } catch (e) {
        // Ignore parsing errors
      }
    }

    // Fallback to using internal ID as string
    if (!deviceId) {
      deviceId = String(d.id)
    }

    return {
      ...d,
      deviceId
    }
  }).filter(d => d.deviceId) // Only show devices with some ID
})

const hasDataSelected = computed(() => {
  return includeStaticRoutes.value || includeOspfRoutes.value || includeBgpRoutes.value ||
         includeMacTable.value || includeCdpNeighbors.value
})

// Methods
const close = () => {
  if (progressInterval) {
    clearInterval(progressInterval)
    progressInterval = null
  }
  discovering.value = false
  discoveryResult.value = null
  progress.value = null
  jobId.value = null
  jobScheduled.value = false
  emit('close')
}

const navigateToJobs = () => {
  // Navigate to Settings -> Background Jobs with tab query parameter
  close()
  // Use Vue Router to navigate with query parameter for the jobs tab
  router.push({ path: '/settings', query: { tab: 'jobs' } })
}

const startDiscovery = async () => {
  discovering.value = true
  discoveryResult.value = null
  jobScheduled.value = false

  try {
    // Choose endpoint based on execution mode
    const endpoint = runInBackground.value 
      ? '/api/topology/discover-async'  // Use new Celery-based endpoint
      : '/api/topology/discover-sync'   // Use synchronous endpoint

    const response = await makeAuthenticatedRequest(endpoint, {
      method: 'POST',
      body: JSON.stringify({
        device_ids: selectedDevices.value,
        include_static_routes: includeStaticRoutes.value,
        include_ospf_routes: includeOspfRoutes.value,
        include_bgp_routes: includeBgpRoutes.value,
        include_mac_table: includeMacTable.value,
        include_cdp_neighbors: includeCdpNeighbors.value,
        cache_results: cacheResults.value
      })
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`Discovery failed: ${response.status} ${response.statusText} - ${errorText}`)
    }

    const result = await response.json()
    jobId.value = result.job_id

    if (runInBackground.value) {
      // Show "Job scheduled" message instead of polling immediately
      jobScheduled.value = true
      discovering.value = false
    } else {
      // Synchronous - result is complete
      discoveryResult.value = result
      discovering.value = false
    }
  } catch (error: any) {
    console.error('Discovery failed:', error)
    discovering.value = false
    jobScheduled.value = false

    // Show error in UI instead of alert
    discoveryResult.value = {
      job_id: 'error',
      status: 'failed',
      total_devices: selectedDevices.value.length,
      successful_devices: 0,
      failed_devices: selectedDevices.value.length,
      devices_data: {},
      errors: { 'all': error.message || 'Unknown error' },
      duration_seconds: 0
    }
  }
}

const openTopologyBuilder = () => {
  emit('openBuilder')
  close()
}

// Watch for modal close
watch(() => props.isOpen, (newVal) => {
  if (!newVal) {
    if (progressInterval) {
      clearInterval(progressInterval)
      progressInterval = null
    }
  }
})
</script>
