<template>
  <div class="h-full flex flex-col bg-white border-r border-gray-200">
    <!-- Symbols Content -->
    <div class="flex-1 overflow-y-auto p-4">
      <!-- Shapes Section -->
      <div class="mb-6">
        <h4 class="text-xs font-semibold text-gray-600 uppercase mb-3">Shapes</h4>
        <div class="grid grid-cols-2 gap-3">
          <div
            v-for="shape in shapes"
            :key="shape.id"
            :draggable="true"
            @dragstart="onDragStart($event, shape)"
            class="bg-gray-50 border-2 border-gray-200 rounded-lg p-3 cursor-move hover:border-purple-400 hover:bg-purple-50 transition-all duration-200 flex flex-col items-center justify-center"
          >
            <div class="w-12 h-12 rounded mb-2 flex items-center justify-center">
              <span class="text-4xl">{{ shape.icon }}</span>
            </div>
            <span class="text-xs text-gray-700 text-center">{{ shape.name }}</span>
          </div>
        </div>
      </div>

      <!-- Cloud Symbols Section -->
      <div class="mb-6">
        <h4 class="text-xs font-semibold text-gray-600 uppercase mb-3">Cloud Services</h4>
        <div class="grid grid-cols-2 gap-3">
          <div
            v-for="cloud in cloudSymbols"
            :key="cloud.id"
            :draggable="true"
            @dragstart="onDragStart($event, cloud)"
            class="bg-gray-50 border-2 border-gray-200 rounded-lg p-3 cursor-move hover:border-purple-400 hover:bg-purple-50 transition-all duration-200 flex flex-col items-center justify-center"
          >
            <div class="w-12 h-12 rounded mb-2 flex items-center justify-center">
              <span class="text-3xl">{{ cloud.icon }}</span>
            </div>
            <span class="text-xs text-gray-700 text-center">{{ cloud.name }}</span>
          </div>
        </div>
      </div>

      <!-- Network Symbols Section -->
      <div class="mb-6">
        <h4 class="text-xs font-semibold text-gray-600 uppercase mb-3">Network</h4>
        <div class="grid grid-cols-2 gap-3">
          <div
            v-for="network in networkSymbols"
            :key="network.id"
            :draggable="true"
            @dragstart="onDragStart($event, network)"
            class="bg-gray-50 border-2 border-gray-200 rounded-lg p-3 cursor-move hover:border-purple-400 hover:bg-purple-50 transition-all duration-200 flex flex-col items-center justify-center"
          >
            <div class="w-12 h-12 rounded mb-2 flex items-center justify-center">
              <span class="text-3xl">{{ network.icon }}</span>
            </div>
            <span class="text-xs text-gray-700 text-center">{{ network.name }}</span>
          </div>
        </div>
      </div>

      <!-- Other Symbols Section -->
      <div class="mb-6">
        <h4 class="text-xs font-semibold text-gray-600 uppercase mb-3">Other</h4>
        <div class="grid grid-cols-2 gap-3">
          <div
            v-for="other in otherSymbols"
            :key="other.id"
            :draggable="true"
            @dragstart="onDragStart($event, other)"
            class="bg-gray-50 border-2 border-gray-200 rounded-lg p-3 cursor-move hover:border-purple-400 hover:bg-purple-50 transition-all duration-200 flex flex-col items-center justify-center"
          >
            <div class="w-12 h-12 rounded mb-2 flex items-center justify-center">
              <span class="text-3xl">{{ other.icon }}</span>
            </div>
            <span class="text-xs text-gray-700 text-center">{{ other.name }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Symbol {
  id: string
  name: string
  icon: string
  type: 'shape' | 'cloud' | 'network' | 'other'
  shapeType?: 'rectangle' | 'circle'
  color?: string
}

// Shape symbols
const shapes = ref<Symbol[]>([
  { id: 'shape-rectangle', name: 'Rectangle', icon: '▭', type: 'shape', shapeType: 'rectangle' },
  { id: 'shape-circle', name: 'Circle', icon: '●', type: 'shape', shapeType: 'circle' },
])

// Cloud service symbols
const cloudSymbols = ref<Symbol[]>([
  { id: 'cloud-generic', name: 'Cloud', icon: '☁️', type: 'cloud' },
  { id: 'cloud-aws', name: 'AWS', icon: '🟧', type: 'cloud' },
  { id: 'cloud-azure', name: 'Azure', icon: '🔷', type: 'cloud' },
  { id: 'cloud-gcp', name: 'GCP', icon: '🔶', type: 'cloud' },
])

// Network symbols
const networkSymbols = ref<Symbol[]>([
  { id: 'net-internet', name: 'Internet', icon: '🌐', type: 'network' },
  { id: 'net-firewall', name: 'Firewall', icon: '🔥', type: 'network' },
  { id: 'net-vpn', name: 'VPN', icon: '🔐', type: 'network' },
  { id: 'net-wifi', name: 'WiFi', icon: '📶', type: 'network' },
])

// Other symbols
const otherSymbols = ref<Symbol[]>([
  { id: 'other-user', name: 'User', icon: '👤', type: 'other' },
  { id: 'other-group', name: 'Group', icon: '👥', type: 'other' },
  { id: 'other-building', name: 'Building', icon: '🏢', type: 'other' },
  { id: 'other-location', name: 'Location', icon: '📍', type: 'other' },
])

// Handle drag start - set the symbol data
const onDragStart = (event: DragEvent, symbol: Symbol) => {
  if (!event.dataTransfer) return

  // Set the data that will be transferred
  event.dataTransfer.effectAllowed = 'copy'
  event.dataTransfer.setData('application/json', JSON.stringify({
    type: 'symbol',
    symbol: symbol
  }))

  console.log('🎨 Dragging symbol:', symbol)
}
</script>
