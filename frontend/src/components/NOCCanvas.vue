<template>
  <div
    ref="canvasContainer"
    class="w-full h-full relative overflow-hidden"
    :class="{
      'ring-4 ring-blue-400 ring-opacity-50': isDragOver,
      'cursor-grab': !mouseState.isDragging,
      'cursor-grabbing': mouseState.isDragging && !selectionBox
    }"
    @drop="onDrop"
    @dragover.prevent="onDragOver"
    @dragenter.prevent="onDragEnter"
    @dragleave="onDragLeave"
    @contextmenu.prevent="onRightClick"
    @mouseup="onCanvasMouseUp"
  >
    <!-- Loading state while canvas initializes -->
    <div 
      v-if="canvasSize.width === 0 || canvasSize.height === 0" 
      class="absolute inset-0 flex items-center justify-center bg-gray-50"
    >
      <div class="text-gray-500">
        <svg class="animate-spin h-8 w-8 mx-auto mb-2" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <p class="text-sm">Initializing canvas...</p>
      </div>
    </div>

    <v-stage
      v-if="canvasSize.width > 0 && canvasSize.height > 0"
      ref="stage"
      :config="{
        width: canvasSize.width,
        height: canvasSize.height,
        draggable: false,
        scaleX: scale,
        scaleY: scale,
        x: position.x,
        y: position.y
      }"
      @wheel="onWheel"
      @mousedown="onStageMouseDown"
      @mousemove="onStageMouseMove"
      @mouseup="onStageMouseUp"
    >
      <!-- Background Grid -->
      <v-layer ref="gridLayer">
        <v-group v-if="showGrid">
          <v-line
            v-for="(line, index) in gridLines.vertical"
            :key="`v-${index}`"
            :config="{
              points: line,
              stroke: '#e5e7eb',
              strokeWidth: 1,
              opacity: 0.5
            }"
          />
          <v-line
            v-for="(line, index) in gridLines.horizontal"
            :key="`h-${index}`"
            :config="{
              points: line,
              stroke: '#e5e7eb',
              strokeWidth: 1,
              opacity: 0.5
            }"
          />
        </v-group>
      </v-layer>

      <!-- Connections Layer -->
      <v-layer ref="connectionsLayer">
        <v-line
          v-for="connection in renderConnections"
          :key="`connection-${connection.id}`"
          :config="{
            points: connection.points,
            stroke: '#3b82f6',
            strokeWidth: 2,
            opacity: 0.8
          }"
        />
      </v-layer>

      <!-- Devices Layer -->
      <v-layer ref="devicesLayer">
        <v-group
          v-for="device in deviceStore.devices"
          :key="`device-${device.id}`"
          :config="{
            x: device.position_x,
            y: device.position_y,
            draggable: true
          }"
          @dragend="onDeviceDragEnd(device, $event)"
          @click="onDeviceClick(device, $event)"
          @dblclick="onDeviceDoubleClick(device)"
          @mousedown="onDeviceMouseDown(device, $event)"
          @mouseenter="onDeviceMouseEnter"
          @mouseleave="onDeviceMouseLeave"
        >
          <!-- Device Background -->
          <v-rect
            :config="{
              width: 60,
              height: 60,
              fill: getDeviceColor(device.device_type),
              stroke: selectedDevice?.id === device.id || selectedDevices.has(device.id) ? '#1d4ed8' : '#6b7280',
              strokeWidth: selectedDevice?.id === device.id || selectedDevices.has(device.id) ? 3 : 1,
              cornerRadius: 8,
              shadowColor: 'black',
              shadowBlur: 4,
              shadowOpacity: 0.1,
              shadowOffsetY: 2
            }"
          />

          <!-- Device Icon -->
          <v-image
            v-if="getDeviceIcon(device.device_type)"
            :config="{
              x: 16,
              y: 16,
              width: 28,
              height: 28,
              image: getDeviceIcon(device.device_type)
            }"
          />

          <!-- Device Name -->
          <v-text
            :config="{
              x: 30,
              y: 50,
              text: device.name,
              fontSize: 9,
              align: 'center',
              fill: '#374151',
              fontFamily: 'Arial',
              offsetX: device.name.length * 5.5,
              offsetY: 10,
              width: 60,
              ellipsis: true
            }"
          />

          <!-- Connection Points -->
          <v-circle
            v-for="(point, index) in getConnectionPoints(device)"
            :key="`point-${device.id}-${index}`"
            :config="{
              x: point.x,
              y: point.y,
              radius: 4,
              fill: '#10b981',
              stroke: '#065f46',
              strokeWidth: 1,
              opacity: connectionMode ? 1 : 0
            }"
            @click="onConnectionPointClick(device, point, $event)"
          />
        </v-group>
      </v-layer>

      <!-- Selection Layer -->
      <v-layer ref="selectionLayer">
        <v-rect
          v-if="selectionBox"
          :config="{
            x: Math.min(selectionBox.startX, selectionBox.endX),
            y: Math.min(selectionBox.startY, selectionBox.endY),
            width: Math.abs(selectionBox.endX - selectionBox.startX),
            height: Math.abs(selectionBox.endY - selectionBox.startY),
            fill: 'rgba(59, 130, 246, 0.1)',
            stroke: '#3b82f6',
            strokeWidth: 1,
            dash: [5, 5]
          }"
        />
      </v-layer>
    </v-stage>

    <!-- Context Menu -->
    <Transition
      enter-active-class="transition-all duration-200 ease-out"
      enter-from-class="opacity-0 scale-95 translate-y-1"
      enter-to-class="opacity-100 scale-100 translate-y-0"
      leave-active-class="transition-all duration-150 ease-in"
      leave-from-class="opacity-100 scale-100 translate-y-0"
      leave-to-class="opacity-0 scale-95 translate-y-1"
    >
      <div
        v-if="contextMenu.show"
        :style="{
          position: 'absolute',
          left: contextMenu.x + 'px',
          top: contextMenu.y + 'px',
          zIndex: 1000
        }"
        class="bg-white/95 backdrop-blur-md border border-gray-200/60 rounded-lg shadow-2xl shadow-black/10 py-1 min-w-44"
      >
        <div
          v-for="item in contextMenuItems"
          :key="item.label"
          class="relative context-menu-item"
        >
          <button
            @click="item.submenu ? null : item.action()"
            class="w-full text-left px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50/80 hover:text-blue-900 flex items-center justify-between transition-all duration-150 ease-out"
            :class="{
              'cursor-default': item.submenu,
              'hover:bg-gradient-to-r hover:from-blue-50/80 hover:to-indigo-50/80': !item.submenu
            }"
          >
            <div class="flex items-center space-x-2">
              <span class="text-sm opacity-70 transition-opacity">{{ item.icon }}</span>
              <span class="font-medium">{{ item.label }}</span>
            </div>
            <span v-if="item.submenu" class="text-gray-400 transition-colors">
              <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
              </svg>
            </span>
          </button>

          <!-- Submenu -->
          <div
            v-if="item.submenu"
            class="submenu absolute left-full top-0 bg-white/95 backdrop-blur-md border border-gray-200/60 rounded-lg shadow-2xl shadow-black/10 py-1 min-w-36 z-10"
          >
            <button
              v-for="subItem in item.submenu"
              :key="subItem.label"
              @click="subItem.action()"
              class="w-full text-left px-3 py-1.5 text-xs text-gray-700 hover:bg-gradient-to-r hover:from-blue-50/80 hover:to-indigo-50/80 hover:text-blue-900 flex items-center space-x-2 transition-all duration-150 ease-out"
            >
              <span class="text-xs opacity-70">{{ subItem.icon }}</span>
              <span class="font-medium">{{ subItem.label }}</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Device Search Input -->
    <div 
      v-if="showDeviceSearch" 
      class="absolute bottom-4 right-16 z-10"
    >
      <div class="relative">
        <input
          ref="deviceSearchInput"
          v-model="deviceSearchQuery"
          type="text"
          placeholder="Search device..."
          class="w-48 px-3 py-2 pr-8 text-sm bg-white border border-gray-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          @keydown.enter="searchAndCenterDevice"
          @keydown.escape="closeDeviceSearch"
          @blur="closeDeviceSearch"
        />
        <button
          @click="closeDeviceSearch"
          class="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>
    </div>

    <!-- Canvas Controls -->
    <div class="absolute bottom-4 right-4 flex flex-col space-y-2">
      <button
        @click="toggleGrid"
        class="p-2 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50 flex-shrink-0"
        :class="{ 'bg-primary-50 border-primary-200': showGrid }"
      >
        📐
      </button>
      <button
        @click="toggleConnectionMode"
        class="p-2 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50 flex-shrink-0"
        :class="{ 'bg-green-50 border-green-200': connectionMode }"
      >
        🔗
      </button>
      <button
        @click="toggleDeviceSearch"
        class="p-2 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50 flex-shrink-0"
        :class="{ 'bg-blue-50 border-blue-200': showDeviceSearch }"
        title="Search devices"
      >
        🔍
      </button>
      <button
        @click="resetView"
        class="p-2 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50 flex-shrink-0"
      >
        🏠
      </button>
    </div>

    <!-- Save Canvas Modal -->
    <SaveCanvasModal
      ref="saveModalRef"
      :show="showSaveModal"
      :device-count="deviceStore.devices.length"
      :connection-count="deviceStore.connections.length"
      @close="closeSaveModal"
      @save="handleCanvasSave"
    />

    <!-- Clear Canvas Confirmation Dialog -->
    <ConfirmDialog
      :show="showClearDialog"
      title="Clear Canvas"
      message="Are you sure you want to clear the canvas? This will permanently remove all devices and connections from the current view."
      confirm-text="Clear Canvas"
      cancel-text="Cancel"
      @confirm="handleClearConfirm"
      @cancel="handleClearCancel"
    />

    <!-- Load Canvas Modal -->
    <LoadCanvasModal
      :show="showLoadModal"
      @close="closeLoadModal"
      @load="handleCanvasLoad"
    />

    <!-- Load Canvas Confirmation Dialog -->
    <ConfirmDialog
      :show="showLoadConfirmDialog"
      title="Load Canvas"
      message="The current canvas is not empty. Loading a new canvas will replace all current devices and connections. Do you want to continue?"
      confirm-text="Load Canvas"
      cancel-text="Cancel"
      @confirm="handleLoadConfirm"
      @cancel="handleLoadCancel"
    />

    <!-- Duplicate Device Modal -->
    <DuplicateDeviceModal
      :show="showDuplicateDialog"
      :device-name="duplicateDeviceName"
      @cancel="handleDuplicateCancel"
      @show="handleDuplicateShow"
      @add="handleDuplicateAdd"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useDevicesStore, type Device } from '@/stores/devices'
import { useCanvasStore } from '@/stores/canvas'
import { type NautobotDevice, canvasApi } from '@/services/api'
import { useDeviceIcons } from '@/composables/useDeviceIcons'
import SaveCanvasModal from './SaveCanvasModal.vue'
import ConfirmDialog from './ConfirmDialog.vue'
import LoadCanvasModal from './LoadCanvasModal.vue'
import DuplicateDeviceModal from './DuplicateDeviceModal.vue'

const deviceStore = useDevicesStore()
const canvasStore = useCanvasStore()
const { loadDeviceIcons, getDeviceIcon } = useDeviceIcons()

const canvasContainer = ref<HTMLElement>()
const stage = ref()

// Canvas state
const canvasSize = reactive({ width: 0, height: 0 })
// Use canvas store for scale and position
const scale = computed(() => canvasStore.scale)
const position = computed(() => canvasStore.position)
const showGrid = ref(true)
const connectionMode = ref(false)
const selectedDevice = ref<Device | null>(null)
const isDragOver = ref(false)

// Selection state
const selectionBox = ref<{
  startX: number
  startY: number
  endX: number
  endY: number
} | null>(null)

// Selected devices for multi-selection
const selectedDevices = ref<Set<number>>(new Set())

// Function to select devices within a selection box
const selectDevicesInBox = (box: { startX: number; startY: number; endX: number; endY: number }) => {
  const minX = Math.min(box.startX, box.endX)
  const maxX = Math.max(box.startX, box.endX)
  const minY = Math.min(box.startY, box.endY)
  const maxY = Math.max(box.startY, box.endY)
  
  console.log('🔍 Selecting devices in box:', { minX, minY, maxX, maxY })
  
  // Start with current selection (additive selection with Shift+drag)
  const newSelection = new Set(selectedDevices.value)
  const deviceSize = 80 // Device width/height
  
  deviceStore.devices.forEach(device => {
    // Check if device overlaps with selection box
    const deviceLeft = device.position_x
    const deviceRight = device.position_x + deviceSize
    const deviceTop = device.position_y
    const deviceBottom = device.position_y + deviceSize
    
    // Check if device overlaps with selection box
    const overlapsX = deviceLeft < maxX && deviceRight > minX
    const overlapsY = deviceTop < maxY && deviceBottom > minY
    
    if (overlapsX && overlapsY) {
      newSelection.add(device.id)
      console.log('✅ Selected device:', device.name, 'at', device.position_x, device.position_y)
    }
  })
  
  selectedDevices.value = newSelection
  
  // Update single selection based on multi-selection
  if (selectedDevices.value.size === 1) {
    const singleDeviceId = Array.from(selectedDevices.value)[0]
    const device = deviceStore.devices.find(d => d.id === singleDeviceId)
    if (device) {
      selectedDevice.value = device
      deviceStore.setSelectedDevice(device)
    }
  } else {
    selectedDevice.value = null
    deviceStore.setSelectedDevice(null)
  }
  
  console.log(`🎯 Total devices selected: ${selectedDevices.value.size}`)
}

// Context menu state
const contextMenu = reactive({
  show: false,
  x: 0,
  y: 0,
  target: null as Device | null,
  targetType: 'canvas' as 'canvas' | 'device'
})

// Connection state
const connectionStart = ref<{
  device: Device
  point: { x: number; y: number }
} | null>(null)

// Save Canvas Modal state
const showSaveModal = ref(false)
const saveModalRef = ref()

// Clear Canvas Confirmation Dialog state
const showClearDialog = ref(false)

// Load Canvas Modal state
const showLoadModal = ref(false)

// Load Canvas Confirmation state
const showLoadConfirmDialog = ref(false)
const pendingCanvasId = ref<number | null>(null)

// Duplicate Device Modal state
const showDuplicateDialog = ref(false)
const duplicateDeviceName = ref('')
const pendingDeviceData = ref<any>(null)
const duplicateExistingDevice = ref<Device | null>(null)

// Device Search state
const showDeviceSearch = ref(false)
const deviceSearchQuery = ref('')
const deviceSearchInput = ref<HTMLInputElement>()

// Mouse state
const mouseState = reactive({
  isDown: false,
  startX: 0,
  startY: 0,
  isDragging: false
})

// Grid lines computation
const gridLines = computed(() => {
  const gridSize = 50
  const lines = { vertical: [], horizontal: [] } as any

  // Vertical lines
  for (let i = 0; i <= canvasSize.width; i += gridSize) {
    lines.vertical.push([i, 0, i, canvasSize.height])
  }

  // Horizontal lines
  for (let i = 0; i <= canvasSize.height; i += gridSize) {
    lines.horizontal.push([0, i, canvasSize.width, i])
  }

  return lines
})

// Render connections
const renderConnections = computed(() => {
  return deviceStore.connections.map(connection => {
    const sourceDevice = deviceStore.devices.find(d => d.id === connection.source_device_id)
    const targetDevice = deviceStore.devices.find(d => d.id === connection.target_device_id)

    if (!sourceDevice || !targetDevice) return null

    return {
      id: connection.id,
      points: [
        sourceDevice.position_x + 30,
        sourceDevice.position_y + 30,
        targetDevice.position_x + 30,
        targetDevice.position_y + 30
      ]
    }
  }).filter(Boolean)
})

// Context menu items
const contextMenuItems = computed(() => {
  if (!contextMenu.target) {
    if (contextMenu.targetType === 'canvas') {
      const items = [
        { icon: '🖼️', label: 'Fit to Screen', action: fitToScreen },
        { icon: '🏠', label: 'Reset View', action: resetView },
        {
          icon: '🎨',
          label: 'Canvas',
          submenu: [
            { icon: '📂', label: 'Load', action: loadCanvas },
            { icon: '💾', label: 'Save', action: saveCanvas },
            { icon: '🗑️', label: 'Clear', action: clearCanvas }
          ]
        }
      ]
      console.log('🐛 Canvas context menu items:', items)
      console.log('🐛 Canvas item with submenu:', items.find(item => item.submenu))
      return items
    }
    return []
  }

  // Device context menu
  const items = [
    { icon: '📊', label: 'Overview', action: () => showDeviceOverview(contextMenu.target!) },
    {
      icon: '⚙️',
      label: 'Config',
      submenu: [
        { icon: '👁️', label: 'Show', action: () => showDeviceConfig(contextMenu.target!) },
        { icon: '📝', label: 'Show Changes', action: () => showDeviceChanges(contextMenu.target!) }
      ]
    },
    { icon: '💻', label: 'Commands', action: () => showDeviceCommands(contextMenu.target!) },
    { icon: '🔗', label: 'Neighbors', action: () => showDeviceNeighbors(contextMenu.target!) },
    { icon: '🔍', label: 'Analyze', action: () => analyzeDevice(contextMenu.target!) },
    { icon: '🗑️', label: 'Remove', action: () => deleteDevice(contextMenu.target!) }
  ]
  console.log('🐛 Device context menu items:', items)
  console.log('🐛 Device item with submenu:', items.find(item => item.submenu))
  return items
})

// Device helpers

const getDeviceColor = (type: string) => {
  const colors = {
    router: '#dbeafe',
    switch: '#dcfce7',
    firewall: '#fef3c7',
    vpn_gateway: '#e0e7ff'
  }
  return colors[type as keyof typeof colors] || '#f3f4f6'
}

// Context menu functions
const loadCanvas = () => {
  console.log('Load Canvas - showing modal')
  showLoadModal.value = true
}

// Load Canvas Modal functions
const closeLoadModal = () => {
  showLoadModal.value = false
}

const handleCanvasLoad = (canvasId: number) => {
  console.log('🔄 Canvas load requested for ID:', canvasId)
  
  // Check if current canvas has devices
  if (deviceStore.devices.length > 0) {
    // Show confirmation dialog
    pendingCanvasId.value = canvasId
    showLoadModal.value = false
    showLoadConfirmDialog.value = true
  } else {
    // Load directly if canvas is empty
    loadCanvasById(canvasId)
  }
}

const handleLoadConfirm = () => {
  console.log('✅ User confirmed canvas load')
  showLoadConfirmDialog.value = false
  if (pendingCanvasId.value) {
    loadCanvasById(pendingCanvasId.value)
    pendingCanvasId.value = null
  }
}

const handleLoadCancel = () => {
  console.log('❌ User cancelled canvas load')
  showLoadConfirmDialog.value = false
  pendingCanvasId.value = null
  // Reopen the load modal
  showLoadModal.value = true
}

const loadCanvasById = async (canvasId: number) => {
  try {
    console.log('🔄 Loading canvas from database...', canvasId)
    
    // Clear current canvas first if it has devices
    if (deviceStore.devices.length > 0) {
      await deviceStore.clearDevices()
      console.log('✅ Current canvas cleared')
    }
    
    // Fetch canvas data
    const canvas = await canvasApi.getCanvas(canvasId)
    console.log('✅ Canvas data loaded:', canvas)
    
    // Load devices from canvas data
    for (const deviceData of canvas.canvas_data.devices) {
      const device = await deviceStore.createDevice({
        name: deviceData.name,
        device_type: deviceData.device_type as Device['device_type'],
        ip_address: deviceData.ip_address,
        position_x: deviceData.position_x,
        position_y: deviceData.position_y,
        properties: deviceData.properties
      })
      console.log('✅ Device created:', device)
    }
    
    // Load connections from canvas data
    for (const connectionData of canvas.canvas_data.connections) {
      const connection = await deviceStore.createConnection({
        source_device_id: connectionData.source_device_id,
        target_device_id: connectionData.target_device_id,
        connection_type: connectionData.connection_type,
        properties: connectionData.properties
      })
      console.log('✅ Connection created:', connection)
    }
    
    console.log('✅ Canvas loaded successfully')
    // notificationStore.showSuccess(`Canvas "${canvas.name}" loaded successfully`)
    
    // Close the load modal after successful loading
    showLoadModal.value = false
    
  } catch (error) {
    console.error('❌ Failed to load canvas:', error)
    // notificationStore.showError('Failed to load canvas')
  }
}

const saveCanvas = () => {
  console.log('Save Canvas')
  showSaveModal.value = true
}

const clearCanvas = () => {
  console.log('Clear Canvas - showing confirmation dialog')
  showClearDialog.value = true
}

// Clear Canvas Confirmation Dialog functions
const handleClearConfirm = async () => {
  console.log('✅ User confirmed canvas clear')
  showClearDialog.value = false
  
  try {
    await deviceStore.clearDevices()
    console.log('✅ Canvas cleared successfully')
    // notificationStore.showSuccess('Canvas cleared successfully')
  } catch (error) {
    console.error('❌ Failed to clear canvas:', error)
    // notificationStore.showError('Failed to clear canvas')
  }
}

const handleClearCancel = () => {
  console.log('❌ User cancelled canvas clear')
  showClearDialog.value = false
}

// Save Canvas Modal functions
const closeSaveModal = () => {
  showSaveModal.value = false
}

const handleCanvasSave = async (data: { name: string; sharable: boolean; canvasId?: number }) => {
  try {
    // Import the canvas API
    const { canvasApi } = await import('@/services/api')
    
    // Collect current canvas state
    const canvasData = {
      devices: deviceStore.devices.map(device => ({
        id: device.id,
        name: device.name,
        device_type: device.device_type,
        ip_address: device.ip_address,
        position_x: device.position_x,
        position_y: device.position_y,
        properties: device.properties
      })),
      connections: deviceStore.connections.map(connection => ({
        id: connection.id,
        source_device_id: connection.source_device_id,
        target_device_id: connection.target_device_id,
        connection_type: connection.connection_type,
        properties: connection.properties
      }))
    }

    let response
    if (data.canvasId) {
      // Update existing canvas
      response = await canvasApi.updateCanvas(data.canvasId, {
        name: data.name,
        sharable: data.sharable,
        canvas_data: canvasData
      })
      console.log('✅ Canvas updated successfully:', response)
    } else {
      // Create new canvas
      response = await canvasApi.saveCanvas({
        name: data.name,
        sharable: data.sharable,
        canvas_data: canvasData
      })
      console.log('✅ Canvas saved successfully:', response)
    }

    showSaveModal.value = false

    // TODO: Show success notification
    // notificationStore.showSuccess(`Canvas "${data.name}" ${data.canvasId ? 'updated' : 'saved'} successfully`)
    
  } catch (error) {
    console.error('❌ Failed to save canvas:', error)
    
    // Show error to user via modal
    if (saveModalRef.value) {
      saveModalRef.value.setError(error instanceof Error ? error.message : 'Failed to save canvas')
      saveModalRef.value.setSaving(false)
    }
  }
}

// Duplicate Device Modal functions
const handleDuplicateCancel = () => {
  showDuplicateDialog.value = false
  pendingDeviceData.value = null
  duplicateExistingDevice.value = null
  duplicateDeviceName.value = ''
}

const handleDuplicateShow = () => {
  if (duplicateExistingDevice.value) {
    // Center and highlight the existing device
    centerOnDevice(duplicateExistingDevice.value)
    // Clear selection and select the existing device
    selectedDevices.value.clear()
    selectedDevice.value = duplicateExistingDevice.value
  }
  handleDuplicateCancel()
}

const handleDuplicateAdd = async () => {
  if (pendingDeviceData.value) {
    try {
      await deviceStore.createDevice(pendingDeviceData.value)
      console.log('✅ Duplicate device added successfully')
    } catch (error) {
      console.error('❌ Failed to create duplicate device:', error)
    }
  }
  handleDuplicateCancel()
}

const showDeviceOverview = (device: Device) => {
  console.log('Show Device Overview:', device.name)
}

const showDeviceConfig = (device: Device) => {
  console.log('Show Device Config:', device.name)
}

const showDeviceChanges = (device: Device) => {
  console.log('Show Device Changes:', device.name)
}

const showDeviceCommands = (device: Device) => {
  console.log('Show Device Commands:', device.name)
}

const showDeviceNeighbors = (device: Device) => {
  console.log('Show Device Neighbors:', device.name)
}

const analyzeDevice = (device: Device) => {
  console.log('Analyze Device:', device.name)
}

const getConnectionPoints = (device: Device) => {
  return [
    { x: 0, y: 30 },    // Left (middle of 60px height)
    { x: 60, y: 30 },   // Right (middle of 60px height)
    { x: 30, y: 0 },    // Top (middle of 60px width)
    { x: 30, y: 60 }    // Bottom (middle of 60px width)
  ]
}

// Helper function to map Nautobot device types to canvas device types
const mapNautobotDeviceType = (nautobotDevice: NautobotDevice): Device['device_type'] => {
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

// Event handlers
const onDragEnter = (event: DragEvent) => {
  console.log('🎯 Drag enter canvas')
  isDragOver.value = true
}

const onDragOver = (event: DragEvent) => {
  // This is called continuously while dragging over the element
  event.preventDefault()
}

const onDragLeave = (event: DragEvent) => {
  console.log('🏃 Drag leave canvas')
  isDragOver.value = false
}

const onDrop = async (event: DragEvent) => {
  console.log('📍 Drop event triggered')
  event.preventDefault()
  isDragOver.value = false

  const data = event.dataTransfer?.getData('application/json')
  console.log('📦 Drop data received:', data)
  if (!data) {
    console.log('❌ No data in drop event')
    return
  }

  try {
    const parsedData = JSON.parse(data)
    const { type } = parsedData
    console.log('🔍 Parsed drop data:', parsedData)

    const rect = canvasContainer.value?.getBoundingClientRect()
    if (!rect) {
      console.log('❌ No canvas container rect')
      return
    }

    const x = (event.clientX - rect.left - position.value.x) / scale.value
    const y = (event.clientY - rect.top - position.value.y) / scale.value

    console.log('📍 Drop position:', { x, y, clientX: event.clientX, clientY: event.clientY })

    if (type === 'nautobot-device') {
      const { device } = parsedData as { type: string; device: NautobotDevice }
      console.log('🏗️ Creating device from Nautobot:', device.name)

      // Check for duplicate by name first
      let existingDevice = deviceStore.findDeviceByName(device.name)
      
      // If not found by name, check by nautobot_id
      if (!existingDevice) {
        existingDevice = deviceStore.findDeviceByNautobotId(device.id)
      }

      if (existingDevice) {
        // Show duplicate dialog
        duplicateDeviceName.value = device.name
        duplicateExistingDevice.value = existingDevice
        pendingDeviceData.value = {
          name: device.name,
          device_type: mapNautobotDeviceType(device),
          ip_address: device.primary_ip4?.address?.split('/')[0],
          position_x: x - 30,
          position_y: y - 30,
          properties: JSON.stringify({
            nautobot_id: device.id,
            location: device.location?.name,
            role: device.role?.name,
            status: device.status?.name,
            device_model: device.device_type?.model,
            last_backup: device.cf_last_backup
          })
        }
        showDuplicateDialog.value = true
        return
      }
      
      await deviceStore.createDevice({
        name: device.name,
        device_type: mapNautobotDeviceType(device),
        ip_address: device.primary_ip4?.address?.split('/')[0], // Remove CIDR notation
        position_x: x - 30, // Center the device
        position_y: y - 30,
        properties: JSON.stringify({
          nautobot_id: device.id,
          location: device.location?.name,
          role: device.role?.name,
          status: device.status?.name,
          device_model: device.device_type?.model,
          last_backup: device.cf_last_backup
        })
      })
      console.log('✅ Device from Nautobot created successfully')
    } else {
      console.log('❌ Unknown drop data type:', type)
    }
  } catch (error) {
    console.error('❌ Failed to create device:', error)
  }
}

const onWheel = (event: any) => {
  event.evt.preventDefault()

  const scaleBy = 1.1
  const stage = event.target.getStage()
  const pointer = stage.getPointerPosition()
  const mousePointTo = {
    x: (pointer.x - stage.x()) / stage.scaleX(),
    y: (pointer.y - stage.y()) / stage.scaleY()
  }

  const newScale = event.evt.deltaY > 0 ? scale.value / scaleBy : scale.value * scaleBy

  // Limit zoom
  if (newScale < 0.1 || newScale > 3) return

  canvasStore.setZoom(newScale)

  canvasStore.setPosition({
    x: pointer.x - mousePointTo.x * newScale,
    y: pointer.y - mousePointTo.y * newScale
  })
}

const onStageMouseDown = (event: any) => {
  console.log('🎭 Stage mouse down:', {
    button: event.evt.button,
    target: event.target?.constructor?.name,
    isStage: event.target === event.target.getStage()
  })

  // Don't handle right-clicks here - they are handled by onRightClick and onDeviceMouseDown
  if (event.evt.button === 2) {
    console.log('🔴 Stage right-click detected, skipping stage handler')
    return
  }

  // Check if clicking on a device - don't handle canvas operations if so
  if (event.target !== event.target.getStage()) {
    console.log('🎯 Clicking on non-stage element:', event.target?.constructor?.name)
    // Clicking on a device or device element, let device handlers take care of it
    return
  }

  if (event.target === event.target.getStage()) {
    console.log('📍 Clicking on stage background')
    mouseState.isDown = true
    const pos = event.target.getStage().getPointerPosition()
    mouseState.startX = pos.x
    mouseState.startY = pos.y

    selectedDevice.value = null
    hideContextMenu()

    // Only create selection box if Shift key is held down
    // Otherwise, default to canvas panning
    if (event.evt.shiftKey) {
      selectionBox.value = {
        startX: (pos.x - position.value.x) / scale.value,
        startY: (pos.y - position.value.y) / scale.value,
        endX: (pos.x - position.value.x) / scale.value,
        endY: (pos.y - position.value.y) / scale.value
      }
    } else {
      selectionBox.value = null
      // Clear multi-selection when not holding shift
      selectedDevices.value.clear()
    }

    // Debug: console.log('🖱️ Mouse down - Mode:', event.evt.shiftKey ? 'Selection' : 'Panning')
  }
}

const onStageMouseMove = (event: any) => {
  if (!mouseState.isDown) return

  const pos = event.target.getStage().getPointerPosition()

  if (!mouseState.isDragging) {
    const dx = pos.x - mouseState.startX
    const dy = pos.y - mouseState.startY
    if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
      mouseState.isDragging = true
      // Debug: console.log('🔄 Start dragging:', selectionBox.value ? 'Selection box' : 'Canvas panning')
    }
  }

  if (mouseState.isDragging) {
    if (selectionBox.value) {
      // Update selection box (when Shift is held)
      selectionBox.value.endX = (pos.x - position.value.x) / scale.value
      selectionBox.value.endY = (pos.y - position.value.y) / scale.value
    } else {
      // Pan the canvas (default behavior)
      const deltaX = pos.x - mouseState.startX
      const deltaY = pos.y - mouseState.startY

      canvasStore.setPosition({
        x: position.value.x + deltaX,
        y: position.value.y + deltaY
      })

      mouseState.startX = pos.x
      mouseState.startY = pos.y

      // Optional: Add some visual feedback
      // console.log('🔄 Panning canvas:', { deltaX, deltaY, newPos: { x: position.x, y: position.y } })
    }
  }
}

const onStageMouseUp = () => {
  // If we had a selection box, select devices within it
  if (selectionBox.value) {
    selectDevicesInBox(selectionBox.value)
  }
  
  mouseState.isDown = false
  mouseState.isDragging = false
  selectionBox.value = null
}

const onCanvasMouseUp = (event: MouseEvent) => {
  console.log('🖱️ Canvas mouse up, button:', event.button)

  // Don't hide context menu on right-click release
  if (event.button === 2) {
    console.log('🔴 Canvas right-click mouseup, keeping context menu visible')
    return
  }

  // Only handle other mouse button releases normally
}

const onRightClick = (event: MouseEvent) => {
  console.log('🎭 Canvas right-click handler triggered', {
    target: (event.target as Element)?.tagName,
    currentTarget: (event.currentTarget as Element)?.tagName,
    contextMenuAlreadyShowing: contextMenu.show,
    contextMenuTargetType: contextMenu.targetType
  })

  event.preventDefault()

  // If we already have a device context menu showing, don't override it
  if (contextMenu.show && contextMenu.targetType === 'device') {
    console.log('🚫 Device context menu already showing, ignoring canvas right-click')
    return
  }

  // Get the canvas container's bounding rect to calculate relative position
  const rect = canvasContainer.value?.getBoundingClientRect()
  if (!rect) return

  // Calculate position relative to the canvas container
  let menuX = event.clientX - rect.left
  let menuY = event.clientY - rect.top

  // Menu dimensions (approximate)
  const menuWidth = 200
  const menuHeight = 200

  // Ensure menu doesn't go outside the canvas bounds
  if (menuX + menuWidth > rect.width) {
    menuX = rect.width - menuWidth
  }
  if (menuY + menuHeight > rect.height) {
    menuY = rect.height - menuHeight
  }

  // Ensure menu doesn't go negative
  menuX = Math.max(0, menuX)
  menuY = Math.max(0, menuY)

  contextMenu.show = true
  contextMenu.x = menuX
  contextMenu.y = menuY
  contextMenu.target = null
  contextMenu.targetType = 'canvas'

  console.log('✅ Canvas context menu shown at:', { x: menuX, y: menuY })
}

const onDeviceClick = (device: Device, event: any) => {
  console.log('🖱️ Device click detected for:', device.name, 'shift key:', event.evt?.shiftKey, 'context menu showing:', contextMenu.show, 'target type:', contextMenu.targetType)

  // Handle Shift+Click for multi-selection
  if (event.evt?.shiftKey) {
    // Toggle device in multi-selection
    if (selectedDevices.value.has(device.id)) {
      selectedDevices.value.delete(device.id)
      console.log('➖ Removed device from selection:', device.name)
    } else {
      selectedDevices.value.add(device.id)
      console.log('➕ Added device to selection:', device.name)
    }
    console.log(`🎯 Total devices in multi-selection: ${selectedDevices.value.size}`)
    
    // Also add to single selection if it's the only one, otherwise clear it
    if (selectedDevices.value.size === 1 && selectedDevices.value.has(device.id)) {
      selectedDevice.value = device
      deviceStore.setSelectedDevice(device)
    } else {
      selectedDevice.value = null
      deviceStore.setSelectedDevice(null)
    }
  } else {
    // Normal click - replace selection
    selectedDevice.value = device
    deviceStore.setSelectedDevice(device)
    
    // Clear multi-selection and set only this device
    selectedDevices.value.clear()
    selectedDevices.value.add(device.id)
    console.log('🎯 Single device selected:', device.name)
  }

  // Don't hide context menu if it's showing a device context menu for this device
  if (contextMenu.show && contextMenu.targetType === 'device' && contextMenu.target?.id === device.id) {
    console.log('🔒 Keeping device context menu visible for:', device.name)
    return
  }

  // Hide context menu for other cases (canvas menu, or clicking different device)
  hideContextMenu()
}

const onDeviceDoubleClick = (device: Device) => {
  editDevice(device)
}

const onDeviceMouseDown = (device: Device, event: any) => {
  console.log('🖱️ Device mouse down event:', {
    deviceName: device.name,
    button: event.evt.button,
    eventType: event.type,
    target: event.target?.constructor?.name
  })

  // Check if it's a right-click (button 2)
  if (event.evt.button === 2) {
    console.log('🎯 Right-click detected on device:', device.name)

    // Prevent all event propagation
    event.evt.preventDefault()
    event.evt.stopPropagation()
    event.cancelBubble = true

    // Also stop immediate propagation to prevent other handlers
    if (event.evt.stopImmediatePropagation) {
      event.evt.stopImmediatePropagation()
    }

    // Get the canvas container's bounding rect to calculate relative position
    const rect = canvasContainer.value?.getBoundingClientRect()
    if (!rect) {
      console.log('❌ No canvas container rect found')
      return
    }

    // Calculate position relative to the canvas container
    let menuX = event.evt.clientX - rect.left
    let menuY = event.evt.clientY - rect.top

    // Menu dimensions (approximate)
    const menuWidth = 200
    const menuHeight = 200

    // Ensure menu doesn't go outside the canvas bounds
    if (menuX + menuWidth > rect.width) {
      menuX = rect.width - menuWidth
    }
    if (menuY + menuHeight > rect.height) {
      menuY = rect.height - menuHeight
    }

    // Ensure menu doesn't go negative
    menuX = Math.max(0, menuX)
    menuY = Math.max(0, menuY)

    contextMenu.show = true
    contextMenu.x = menuX
    contextMenu.y = menuY
    contextMenu.target = device
    contextMenu.targetType = 'device'

    console.log('✅ Device context menu shown for:', device.name, {
      x: menuX,
      y: menuY,
      contextMenuState: contextMenu
    })
  } else {
    console.log('🔘 Non-right-click on device:', device.name, 'button:', event.evt.button)
  }
}

const onDeviceDragEnd = async (device: Device, event: any) => {
  const newX = event.target.x()
  const newY = event.target.y()

  try {
    await deviceStore.updateDevice(device.id, {
      position_x: newX,
      position_y: newY
    })
  } catch (error) {
    console.error('Failed to update device position:', error)
  }
}

const onDeviceMouseEnter = () => {
  // Change cursor to pointer when hovering over devices
  if (canvasContainer.value) {
    canvasContainer.value.style.cursor = 'pointer'
  }
}

const onDeviceMouseLeave = () => {
  // Restore default canvas cursor when leaving device
  if (canvasContainer.value) {
    canvasContainer.value.style.cursor = mouseState.isDragging ? 'grabbing' : 'grab'
  }
}

const onConnectionPointClick = async (device: Device, point: { x: number; y: number }, event: any) => {
  event.cancelBubble = true

  if (!connectionMode.value) return

  if (!connectionStart.value) {
    connectionStart.value = { device, point }
  } else {
    if (connectionStart.value.device.id !== device.id) {
      try {
        await deviceStore.createConnection({
          source_device_id: connectionStart.value.device.id,
          target_device_id: device.id,
          connection_type: 'ethernet'
        })
      } catch (error) {
        console.error('Failed to create connection:', error)
      }
    }
    connectionStart.value = null
    connectionMode.value = false
  }
}

// Canvas controls
const toggleGrid = () => {
  showGrid.value = !showGrid.value
}

const toggleConnectionMode = () => {
  connectionMode.value = !connectionMode.value
  connectionStart.value = null
}

const fitToScreen = () => {
  if (deviceStore.devices.length === 0) return

  const padding = 100
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity

  deviceStore.devices.forEach(device => {
    minX = Math.min(minX, device.position_x)
    minY = Math.min(minY, device.position_y)
    maxX = Math.max(maxX, device.position_x + 80)
    maxY = Math.max(maxY, device.position_y + 80)
  })

  const width = maxX - minX + padding * 2
  const height = maxY - minY + padding * 2

  const containerRect = canvasContainer.value?.getBoundingClientRect()
  if (!containerRect) return

  const scaleX = containerRect.width / width
  const scaleY = containerRect.height / height
  const newScale = Math.min(scaleX, scaleY, 1)

  canvasStore.setZoom(newScale)
  canvasStore.setPosition({
    x: (containerRect.width - width * newScale) / 2 - (minX - padding) * newScale,
    y: (containerRect.height - height * newScale) / 2 - (minY - padding) * newScale
  })
}

const resetView = () => {
  canvasStore.resetView()
}

// Device search functions
const toggleDeviceSearch = () => {
  showDeviceSearch.value = !showDeviceSearch.value
  if (showDeviceSearch.value) {
    deviceSearchQuery.value = ''
    // Focus the input after DOM updates
    nextTick(() => {
      deviceSearchInput.value?.focus()
    })
  }
}

const closeDeviceSearch = () => {
  showDeviceSearch.value = false
  deviceSearchQuery.value = ''
}

const searchAndCenterDevice = () => {
  const query = deviceSearchQuery.value.trim().toLowerCase()
  if (!query) return

  // Find device by name (case-insensitive)
  const foundDevice = deviceStore.devices.find(device => 
    device.name.toLowerCase().includes(query)
  )

  if (foundDevice) {
    // Center the device on screen
    const containerRect = canvasContainer.value?.getBoundingClientRect()
    if (containerRect) {
      canvasStore.setPosition({
        x: containerRect.width / 2 - (foundDevice.position_x + 30) * scale.value,
        y: containerRect.height / 2 - (foundDevice.position_y + 30) * scale.value
      })
      
      // Select the device
      deviceStore.setSelectedDevice(foundDevice)
      
      // Close search
      closeDeviceSearch()
      
      console.log(`✅ Found and centered device: ${foundDevice.name}`)
    }
  } else {
    console.log(`❌ Device not found: ${query}`)
    // Optionally show a notification that device was not found
  }
}

const hideContextMenu = () => {
  console.log('🚫 Hiding context menu')
  console.trace('🔍 hideContextMenu called from:')
  contextMenu.show = false
}

// Context menu actions
const editDevice = (device: Device) => {
  console.log('Edit device:', device)
  hideContextMenu()
}

const showProperties = (device: Device) => {
  console.log('Show properties:', device)
  hideContextMenu()
}

const startConnection = (device: Device) => {
  connectionMode.value = true
  connectionStart.value = { device, point: { x: 30, y: 30 } }
  hideContextMenu()
}

const centerOnDevice = (device: Device) => {
  const containerRect = canvasContainer.value?.getBoundingClientRect()
  if (!containerRect) return

  canvasStore.setPosition({
    x: containerRect.width / 2 - (device.position_x + 30) * scale.value,
    y: containerRect.height / 2 - (device.position_y + 30) * scale.value
  })
  hideContextMenu()
}

const deleteDevice = async (device: Device) => {
  console.log('🗑️ Remove device requested:', device.name)
  
  if (confirm(`Are you sure you want to remove "${device.name}" from the canvas?`)) {
    try {
      await deviceStore.deleteDevice(device.id)
      
      // Remove from selections if it was selected
      if (selectedDevice.value?.id === device.id) {
        selectedDevice.value = null
        deviceStore.setSelectedDevice(null)
      }
      selectedDevices.value.delete(device.id)
      
      console.log('✅ Device removed successfully:', device.name)
    } catch (error) {
      console.error('❌ Failed to delete device:', error)
    }
  } else {
    console.log('❌ Device removal cancelled by user')
  }
  
  hideContextMenu()
}

// Resize handler
const handleResize = () => {
  if (canvasContainer.value) {
    const newWidth = canvasContainer.value.clientWidth
    const newHeight = canvasContainer.value.clientHeight
    console.log('🔄 Resizing canvas to:', { newWidth, newHeight })
    
    // Only update if dimensions are valid, with minimum fallback
    if (newWidth > 0 && newHeight > 0) {
      canvasSize.width = newWidth
      canvasSize.height = newHeight
    } else if (canvasContainer.value.parentElement) {
      // Fallback to parent element dimensions
      const parentWidth = canvasContainer.value.parentElement.clientWidth
      const parentHeight = canvasContainer.value.parentElement.clientHeight
      if (parentWidth > 0 && parentHeight > 0) {
        canvasSize.width = parentWidth
        canvasSize.height = parentHeight
        console.log('🔄 Using parent dimensions:', { width: parentWidth, height: parentHeight })
      }
    }
  }
}

// Global click handler to hide context menu
const handleGlobalClick = (event: MouseEvent) => {
  // Don't handle right-clicks - they should show context menus, not hide them
  if (event.button === 2) {
    console.log('🔴 Global click handler ignoring right-click')
    return
  }

  console.log('🖱️ Global click detected, context menu visible:', contextMenu.show)
  if (contextMenu.show) {
    // Find the context menu element
    const contextMenuElement = document.querySelector('.bg-white.border.border-gray-200.rounded-lg.shadow-lg')
    const clickedInsideMenu = contextMenuElement?.contains(event.target as Node)

    console.log('📍 Click details:', {
      clickedInsideMenu,
      targetElement: (event.target as Element)?.tagName
    })

    if (!clickedInsideMenu) {
      hideContextMenu()
    }
  }
}

// Global mouseup handler to hide context menu on left-click release only
const handleGlobalMouseUp = (event: MouseEvent) => {
  console.log('🖱️ Global mouseup detected, button:', event.button, 'context menu visible:', contextMenu.show)

  // Only hide context menu on left-click mouseup, never on right-click
  if (event.button === 0 && contextMenu.show) {
    // Find the context menu element
    const contextMenuElement = document.querySelector('.bg-white.border.border-gray-200.rounded-lg.shadow-lg')
    const clickedInsideMenu = contextMenuElement?.contains(event.target as Node)

    console.log('📍 Left MouseUp details:', {
      clickedInsideMenu,
      targetElement: (event.target as Element)?.tagName
    })

    if (!clickedInsideMenu) {
      hideContextMenu()
    }
  } else if (event.button === 2) {
    console.log('🔴 Right-click mouseup detected, keeping context menu visible')
  }
}

onMounted(async () => {
  await nextTick()

  // Load device icons first
  await loadDeviceIcons()

  // Debug: Check device count
  console.log('🎯 Devices loaded:', deviceStore.devices.length)

  // Ensure canvas container is available before initializing
  if (canvasContainer.value) {
    // Wait a bit more for the DOM to be fully rendered
    setTimeout(() => {
      handleResize()

      // If still no dimensions after first resize, try again
      if (canvasSize.width === 0 || canvasSize.height === 0) {
        setTimeout(() => {
          handleResize()
        }, 200)
      }
    }, 100)
  }

  window.addEventListener('resize', handleResize)
  document.addEventListener('click', handleGlobalClick)
  document.addEventListener('mouseup', handleGlobalMouseUp)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  document.removeEventListener('click', handleGlobalClick)
  document.removeEventListener('mouseup', handleGlobalMouseUp)
})
</script>

<style scoped>
.canvas-container {
  cursor: grab;
}

.canvas-container:active {
  cursor: grabbing;
}

/* Context Menu Submenu Hover Effects */
.context-menu-item {
  position: relative;
}

.context-menu-item .submenu {
  opacity: 0;
  visibility: hidden;
  transform: translateX(-10px);
  transition: opacity 0.2s ease-out, visibility 0.2s ease-out, transform 0.2s ease-out;
}

.context-menu-item:hover .submenu {
  opacity: 1;
  visibility: visible;
  transform: translateX(0);
}

/* Keep submenu visible when hovering over it */
.context-menu-item:hover .submenu,
.submenu:hover {
  opacity: 1;
  visibility: visible;
}

/* Extend hover area slightly to prevent flickering */
.context-menu-item:hover::after {
  content: '';
  position: absolute;
  top: 0;
  right: -5px;
  width: 5px;
  height: 100%;
  z-index: 1;
}
</style>