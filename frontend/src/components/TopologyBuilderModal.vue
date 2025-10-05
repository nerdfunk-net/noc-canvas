<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto">
    <!-- Backdrop -->
    <div class="fixed inset-0 bg-black bg-opacity-50 transition-opacity" @click="close"></div>

    <!-- Modal -->
    <div class="flex min-h-screen items-center justify-center p-4">
      <div class="relative bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <!-- Header -->
        <div class="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
          <div class="flex items-center justify-between">
            <h2 class="text-2xl font-bold text-white flex items-center gap-2">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Build Network Topology
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
          <!-- Loading State -->
          <div v-if="loading" class="flex items-center justify-center py-12">
            <div class="text-center">
              <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p class="mt-4 text-gray-600">Building topology...</p>
            </div>
          </div>

          <!-- Error State -->
          <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <div class="flex items-start gap-3">
              <svg class="w-5 h-5 text-red-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <h4 class="font-medium text-red-800">Error Building Topology</h4>
                <p class="text-sm text-red-700 mt-1">{{ error }}</p>
              </div>
            </div>
          </div>

          <!-- Configuration -->
          <div v-else>
            <!-- Device Selection -->
            <div class="mb-6">
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Devices
                <span class="text-gray-500 font-normal ml-1">(leave empty to use all cached devices)</span>
              </label>
              <select
                v-model="selectedDevices"
                multiple
                class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 h-32"
              >
                <option v-for="device in allDevices" :key="device.device_id" :value="device.device_id">
                  {{ device.device_name }} - {{ device.primary_ip || 'No IP' }} <span v-if="device.source === 'canvas'" class="text-xs text-gray-400">(canvas)</span>
                </option>
              </select>
              <p class="text-xs text-gray-500 mt-1">
                {{ selectedDevices.length === 0 ? 'All devices will be included' : `${selectedDevices.length} device(s) selected` }}
                <span v-if="allDevices.length > 0" class="ml-1">({{ allDevices.filter(d => d.source === 'cache').length }} cached, {{ allDevices.filter(d => d.source === 'canvas').length }} from canvas)</span>
              </p>
            </div>

            <!-- Topology Options -->
            <div class="mb-6">
              <h3 class="text-sm font-medium text-gray-700 mb-3">Topology Sources</h3>
              <div class="space-y-3">
                <!-- CDP Neighbors -->
                <label class="flex items-start gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition" :class="{ 'bg-blue-50 border-blue-300': includeCdp }">
                  <input type="checkbox" v-model="includeCdp" class="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
                  <div class="flex-1">
                    <div class="font-medium text-gray-900">CDP/LLDP Neighbors</div>
                    <div class="text-sm text-gray-500">Physical Layer 2/3 connectivity based on neighbor discovery</div>
                  </div>
                </label>

                <!-- Routing Tables -->
                <label class="flex items-start gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition" :class="{ 'bg-blue-50 border-blue-300': includeRouting }">
                  <input type="checkbox" v-model="includeRouting" class="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
                  <div class="flex-1">
                    <div class="font-medium text-gray-900">Routing Tables</div>
                    <div class="text-sm text-gray-500">Logical Layer 3 paths from routing protocols</div>

                    <!-- Route Types (shown when routing is enabled) -->
                    <div v-if="includeRouting" class="mt-3 ml-1 flex flex-wrap gap-3">
                      <label class="flex items-center gap-2">
                        <input type="checkbox" value="static" v-model="routeTypes" class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
                        <span class="text-sm text-gray-700">Static Routes</span>
                      </label>
                      <label class="flex items-center gap-2">
                        <input type="checkbox" value="ospf" v-model="routeTypes" class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
                        <span class="text-sm text-gray-700">OSPF</span>
                      </label>
                      <label class="flex items-center gap-2">
                        <input type="checkbox" value="bgp" v-model="routeTypes" class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
                        <span class="text-sm text-gray-700">BGP</span>
                      </label>
                    </div>
                  </div>
                </label>

                <!-- Layer 2 Discovery -->
                <label class="flex items-start gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition" :class="{ 'bg-blue-50 border-blue-300': includeLayer2 }">
                  <input type="checkbox" v-model="includeLayer2" class="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
                  <div class="flex-1">
                    <div class="font-medium text-gray-900">Layer 2 Discovery</div>
                    <div class="text-sm text-gray-500">MAC address table and ARP-based connections</div>
                  </div>
                </label>
              </div>
            </div>

            <!-- Layout Options -->
            <div class="mb-6">
              <h3 class="text-sm font-medium text-gray-700 mb-3">Layout Options</h3>
              <div class="space-y-3">
                <label class="flex items-center gap-3">
                  <input type="checkbox" v-model="autoLayout" class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
                  <span class="text-gray-700">Auto-calculate node positions</span>
                </label>

                <div v-if="autoLayout" class="ml-7">
                  <label class="block text-sm text-gray-600 mb-2">Layout Algorithm</label>
                  <select v-model="layoutAlgorithm" class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                    <option value="force_directed">Force-Directed (Spring Physics)</option>
                    <option value="hierarchical">Hierarchical (Layered)</option>
                    <option value="circular">Circular (Ring)</option>
                  </select>
                </div>
              </div>
            </div>

            <!-- Topology Preview -->
            <div v-if="topology" class="mb-6">
              <h3 class="text-sm font-medium text-gray-700 mb-3">Topology Preview</h3>
              <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <div class="grid grid-cols-3 gap-4 text-sm">
                  <div class="text-center">
                    <div class="text-2xl font-bold text-blue-600">{{ topology.nodes.length }}</div>
                    <div class="text-gray-600">Devices</div>
                  </div>
                  <div class="text-center">
                    <div class="text-2xl font-bold text-green-600">{{ topology.links.length }}</div>
                    <div class="text-gray-600">Links</div>
                  </div>
                  <div class="text-center">
                    <div class="text-2xl font-bold text-purple-600">{{ uniqueLinkTypes }}</div>
                    <div class="text-gray-600">Link Types</div>
                  </div>
                </div>

                <!-- Link Types Breakdown -->
                <div v-if="topology.links.length > 0" class="mt-4 pt-4 border-t border-gray-300">
                  <div class="text-xs font-medium text-gray-600 mb-2">Link Types:</div>
                  <div class="flex flex-wrap gap-2">
                    <span
                      v-for="(count, type) in linkTypesBreakdown"
                      :key="type"
                      class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                      :class="getLinkTypeClass(type as string)"
                    >
                      {{ formatLinkType(type as string) }}: {{ count }}
                    </span>
                  </div>
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
            Cancel
          </button>
          <div class="flex gap-3">
            <button
              @click="buildTopology"
              :disabled="loading || (!includeCdp && !includeRouting && !includeLayer2)"
              class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition font-medium"
            >
              {{ topology ? 'Rebuild' : 'Build' }} Topology
            </button>
            <button
              v-if="topology && topology.nodes.length > 0"
              @click="importToCanvas"
              class="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium"
            >
              Import to Canvas
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { topologyApi, type TopologyGraph, type LinkType } from '@/services/api'
import { makeAuthenticatedRequest } from '@/services/api'
import { useDevicesStore } from '@/stores/devices'

const props = defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  close: []
  import: [topology: TopologyGraph]
}>()

const deviceStore = useDevicesStore()

// State
const loading = ref(false)
const error = ref<string | null>(null)
const cachedDevices = ref<Array<{ device_id: string; device_name: string; primary_ip?: string }>>([])
const selectedDevices = ref<string[]>([])
const includeCdp = ref(true)
const includeRouting = ref(false)
const includeLayer2 = ref(false)
const routeTypes = ref<string[]>(['static', 'ospf', 'bgp'])
const autoLayout = ref(true)
const layoutAlgorithm = ref<'force_directed' | 'hierarchical' | 'circular'>('force_directed')
const topology = ref<TopologyGraph | null>(null)

// Computed
const allDevices = computed(() => {
  const devices = []

  // Add cached devices from API
  cachedDevices.value.forEach(d => {
    devices.push({
      device_id: d.device_id,
      device_name: d.device_name,
      primary_ip: d.primary_ip,
      source: 'cache'
    })
  })

  // Add canvas devices
  deviceStore.devices.forEach(d => {
    // Try to get device ID from various sources
    let deviceId = d.nautobot_id

    if (!deviceId && d.properties) {
      try {
        const props = JSON.parse(d.properties)
        deviceId = props.nautobot_id || props.device_id
      } catch (e) {
        // Ignore
      }
    }

    if (!deviceId) {
      deviceId = String(d.id)
    }

    // Only add if not already in cached devices
    if (!devices.find(existing => existing.device_id === deviceId)) {
      devices.push({
        device_id: deviceId,
        device_name: d.name,
        primary_ip: d.ip_address,
        source: 'canvas'
      })
    }
  })

  return devices
})

const uniqueLinkTypes = computed(() => {
  if (!topology.value) return 0
  const types = new Set(topology.value.links.map(link => link.link_type))
  return types.size
})

const linkTypesBreakdown = computed(() => {
  if (!topology.value) return {}
  const breakdown: Record<string, number> = {}
  topology.value.links.forEach(link => {
    breakdown[link.link_type] = (breakdown[link.link_type] || 0) + 1
  })
  return breakdown
})

// Methods
const close = () => {
  emit('close')
}

const fetchCachedDevices = async () => {
  try {
    const response = await makeAuthenticatedRequest('/api/cache/devices?limit=1000')
    if (response.ok) {
      cachedDevices.value = await response.json()
    }
  } catch (err) {
    console.error('Failed to fetch cached devices:', err)
  }
}

const buildTopology = async () => {
  loading.value = true
  error.value = null

  try {
    console.log('🔨 Building topology with params:', {
      device_ids: selectedDevices.value.length > 0 ? selectedDevices.value : undefined,
      include_cdp: includeCdp.value,
      include_routing: includeRouting.value,
      route_types: includeRouting.value ? routeTypes.value : [],
      include_layer2: includeLayer2.value,
      auto_layout: autoLayout.value,
      layout_algorithm: layoutAlgorithm.value
    })

    topology.value = await topologyApi.buildTopology({
      device_ids: selectedDevices.value.length > 0 ? selectedDevices.value : undefined,
      include_cdp: includeCdp.value,
      include_routing: includeRouting.value,
      route_types: includeRouting.value ? routeTypes.value : [],
      include_layer2: includeLayer2.value,
      auto_layout: autoLayout.value,
      layout_algorithm: layoutAlgorithm.value
    })

    console.log('✅ Topology built successfully:', topology.value)
    console.log('  - Nodes:', topology.value?.nodes?.length || 0)
    console.log('  - Links:', topology.value?.links?.length || 0)
  } catch (err: any) {
    error.value = err.message || 'Failed to build topology'
    console.error('❌ Topology build error:', err)
  } finally {
    loading.value = false
  }
}

const importToCanvas = () => {
  console.log('🔄 importToCanvas called, topology:', topology.value)
  if (topology.value) {
    console.log('✅ Emitting import event with topology')
    emit('import', topology.value)
  } else {
    console.error('❌ No topology available to import')
  }
}

const formatLinkType = (type: string): string => {
  const labels: Record<string, string> = {
    'cdp_neighbor': 'CDP',
    'lldp_neighbor': 'LLDP',
    'static_route': 'Static',
    'ospf_route': 'OSPF',
    'bgp_route': 'BGP',
    'arp_discovered': 'ARP',
    'mac_table': 'MAC'
  }
  return labels[type] || type
}

const getLinkTypeClass = (type: string): string => {
  const classes: Record<string, string> = {
    'cdp_neighbor': 'bg-blue-100 text-blue-800',
    'lldp_neighbor': 'bg-blue-100 text-blue-800',
    'static_route': 'bg-purple-100 text-purple-800',
    'ospf_route': 'bg-green-100 text-green-800',
    'bgp_route': 'bg-orange-100 text-orange-800',
    'arp_discovered': 'bg-yellow-100 text-yellow-800',
    'mac_table': 'bg-pink-100 text-pink-800'
  }
  return classes[type] || 'bg-gray-100 text-gray-800'
}

// Lifecycle
onMounted(() => {
  if (props.isOpen) {
    fetchCachedDevices()
  }
})
</script>
