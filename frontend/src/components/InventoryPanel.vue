<template>
  <div class="h-full flex flex-col" style="background-color: #fef3c7; border: 2px solid #f59e0b;">
    <!-- Plugin Sources -->
    <div class="p-4">
      <h3 class="text-sm font-medium text-gray-700 mb-3">Sources</h3>
      <div class="space-y-2">
        <div
          v-for="plugin in pluginSources"
          :key="plugin.name"
          class="flex items-center justify-between p-2 rounded border"
          :class="plugin.enabled ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'"
        >
          <div class="flex items-center space-x-2">
            <div
              class="w-2 h-2 rounded-full"
              :class="plugin.connected ? 'bg-green-500' : 'bg-red-500'"
            ></div>
            <span class="text-sm font-medium">{{ plugin.name }}</span>
          </div>
          <button
            @click="togglePlugin(plugin)"
            class="text-xs px-2 py-1 rounded"
            :class="plugin.enabled ? 'bg-green-600 text-white' : 'bg-gray-400 text-white'"
          >
            {{ plugin.enabled ? 'On' : 'Off' }}
          </button>
        </div>
      </div>
    </div>

    <div class="border-t border-gray-200"></div>

    <!-- Device Templates -->
    <div class="flex-1 p-4 overflow-y-auto">
      <h3 class="text-sm font-medium text-gray-700 mb-3">Device Types ({{ deviceStore.deviceTemplates.length }} available)</h3>
      <div class="space-y-2">
        <div
          v-for="template in deviceStore.deviceTemplates"
          :key="template.type"
          :draggable="true"
          @dragstart="startDrag($event, template)"
          class="device-template p-3 bg-white border border-gray-200 rounded-lg cursor-move hover:border-primary-300 hover:shadow-sm transition-all"
        >
          <div class="flex items-center space-x-3">
            <div class="text-2xl">{{ template.icon }}</div>
            <div>
              <div class="font-medium text-gray-900">{{ template.name }}</div>
              <div class="text-xs text-gray-500">{{ template.type }}</div>
            </div>
          </div>
          <div class="mt-2 text-xs text-gray-600">
            <div v-for="(value, key) in template.defaultProperties" :key="key">
              {{ key }}: {{ Array.isArray(value) ? value.join(', ') : value }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="border-t border-gray-200 p-4">
      <h3 class="text-sm font-medium text-gray-700 mb-3">Quick Actions</h3>
      <div class="space-y-2">
        <button
          @click="refreshInventory"
          class="w-full btn-secondary text-sm"
          :disabled="loading"
        >
          {{ loading ? 'Refreshing...' : 'Refresh Inventory' }}
        </button>
        <button
          @click="clearCanvas"
          class="w-full btn-secondary text-sm"
        >
          Clear Canvas
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useDevicesStore, type DeviceTemplate } from '@/stores/devices'

const deviceStore = useDevicesStore()

interface PluginSource {
  name: string
  enabled: boolean
  connected: boolean
  type: 'nautobot' | 'checkmk' | 'manual'
}

const loading = ref(false)

// Mock plugin sources
const pluginSources = ref<PluginSource[]>([
  {
    name: 'Nautobot',
    enabled: false,
    connected: false,
    type: 'nautobot'
  },
  {
    name: 'CheckMK',
    enabled: false,
    connected: false,
    type: 'checkmk'
  },
  {
    name: 'Manual Entry',
    enabled: true,
    connected: true,
    type: 'manual'
  }
])

const startDrag = (event: DragEvent, template: DeviceTemplate) => {
  console.log('🎯 Starting drag for template:', template.name)
  if (event.dataTransfer) {
    const dragData = {
      type: 'device-template',
      template
    }
    event.dataTransfer.setData('application/json', JSON.stringify(dragData))
    event.dataTransfer.effectAllowed = 'copy'
    console.log('✅ Drag data set:', dragData)
  }
}

const togglePlugin = (plugin: PluginSource) => {
  plugin.enabled = !plugin.enabled

  // Simulate connection status
  if (plugin.enabled && plugin.type === 'manual') {
    plugin.connected = true
  } else if (plugin.enabled) {
    // Mock connection attempt for external plugins
    setTimeout(() => {
      plugin.connected = Math.random() > 0.5 // 50% chance of connection
    }, 1000)
  } else {
    plugin.connected = false
  }
}

const refreshInventory = async () => {
  loading.value = true
  try {
    await deviceStore.fetchDevices()
    await deviceStore.fetchConnections()
  } finally {
    setTimeout(() => {
      loading.value = false
    }, 500)
  }
}

const clearCanvas = () => {
  // This will be implemented when we have the canvas component
  console.log('Clear canvas functionality will be implemented with the canvas component')
}
</script>

<style scoped>
.device-template {
  user-select: none;
}

.device-template:hover {
  transform: translateY(-1px);
}
</style>