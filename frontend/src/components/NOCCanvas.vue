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
          @click="onDeviceClick(device)"
          @dblclick="onDeviceDoubleClick(device)"
          @mousedown="onDeviceMouseDown(device, $event)"
        >
          <!-- Device Background -->
          <v-rect
            :config="{
              width: 80,
              height: 80,
              fill: getDeviceColor(device.device_type),
              stroke: selectedDevice?.id === device.id ? '#1d4ed8' : '#6b7280',
              strokeWidth: selectedDevice?.id === device.id ? 3 : 1,
              cornerRadius: 8,
              shadowColor: 'black',
              shadowBlur: 4,
              shadowOpacity: 0.1,
              shadowOffsetY: 2
            }"
          />

          <!-- Device Icon -->
          <v-text
            :config="{
              x: 40,
              y: 25,
              text: getDeviceIcon(device.device_type),
              fontSize: 24,
              align: 'center',
              offsetX: 12,
              offsetY: 12
            }"
          />

          <!-- Device Name -->
          <v-text
            :config="{
              x: 40,
              y: 55,
              text: device.name,
              fontSize: 10,
              align: 'center',
              fill: '#374151',
              fontFamily: 'Arial',
              offsetX: device.name.length * 3,
              width: 80,
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
    <div
      v-if="contextMenu.show"
      :style="{
        position: 'absolute',
        left: contextMenu.x + 'px',
        top: contextMenu.y + 'px',
        zIndex: 1000
      }"
      class="bg-white border border-gray-200 rounded-lg shadow-lg py-2 min-w-48"
    >
      <div
        v-for="item in contextMenuItems"
        :key="item.label"
        class="relative group"
      >
        <button
          @click="item.submenu ? null : item.action()"
          class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center justify-between"
          :class="{ 'cursor-default': item.submenu }"
        >
          <div class="flex items-center space-x-2">
            <span>{{ item.icon }}</span>
            <span>{{ item.label }}</span>
          </div>
          <span v-if="item.submenu" class="text-gray-400">▶</span>
        </button>
        
        <!-- Submenu -->
        <div
          v-if="item.submenu"
          class="absolute left-full top-0 ml-1 bg-white border border-gray-200 rounded-lg shadow-lg py-2 min-w-40 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200"
        >
          <button
            v-for="subItem in item.submenu"
            :key="subItem.label"
            @click="subItem.action()"
            class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
          >
            <span>{{ subItem.icon }}</span>
            <span>{{ subItem.label }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Canvas Controls -->
    <div class="absolute bottom-4 right-4 flex flex-col space-y-2">
      <button
        @click="toggleGrid"
        class="p-2 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50"
        :class="{ 'bg-primary-50 border-primary-200': showGrid }"
      >
        📐
      </button>
      <button
        @click="toggleConnectionMode"
        class="p-2 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50"
        :class="{ 'bg-green-50 border-green-200': connectionMode }"
      >
        🔗
      </button>
      <button
        @click="fitToScreen"
        class="p-2 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50"
      >
        🔍
      </button>
      <button
        @click="resetView"
        class="p-2 bg-white border border-gray-200 rounded-lg shadow-sm hover:bg-gray-50"
      >
        🏠
      </button>
    </div>

    <!-- Controls Help -->
    <div class="absolute bottom-4 left-4 bg-white border border-gray-200 rounded-lg shadow-sm px-3 py-2 text-xs text-gray-600 max-w-64">
      <div class="font-medium mb-1">Canvas Controls</div>
      <div class="space-y-1">
        <div>• Left-click + drag: Pan canvas</div>
        <div>• Shift + drag: Selection box</div>
        <div>• Mouse wheel: Zoom in/out</div>
        <div>• Right-click: Context menu</div>
        <div>• Top menu: Zoom slider & presets</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useDevicesStore, type Device, type DeviceTemplate } from '@/stores/devices'
import { useCanvasStore } from '@/stores/canvas'

const deviceStore = useDevicesStore()
const canvasStore = useCanvasStore()

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
        sourceDevice.position_x + 40,
        sourceDevice.position_y + 40,
        targetDevice.position_x + 40,
        targetDevice.position_y + 40
      ]
    }
  }).filter(Boolean)
})

// Context menu items
const contextMenuItems = computed(() => {
  if (!contextMenu.target) {
    if (contextMenu.targetType === 'canvas') {
      return [
        { icon: '▫', label: 'Fit to Screen', action: fitToScreen },
        { icon: '↻', label: 'Reset View', action: resetView },
        { 
          icon: '■', 
          label: 'Canvas',
          submenu: [
            { icon: '↑', label: 'Load', action: loadCanvas },
            { icon: '↓', label: 'Save', action: saveCanvas },
            { icon: '×', label: 'Clear', action: clearCanvas }
          ]
        }
      ]
    }
    return []
  }

  // Device context menu
  return [
    { icon: '○', label: 'Overview', action: () => showDeviceOverview(contextMenu.target!) },
    {
      icon: '⚙',
      label: 'Config',
      submenu: [
        { icon: '□', label: 'Show', action: () => showDeviceConfig(contextMenu.target!) },
        { icon: '≡', label: 'Show Changes', action: () => showDeviceChanges(contextMenu.target!) }
      ]
    },
    { icon: '‣', label: 'Commands', action: () => showDeviceCommands(contextMenu.target!) },
    { icon: '◊', label: 'Neighbors', action: () => showDeviceNeighbors(contextMenu.target!) },
    { icon: '◉', label: 'Analyze', action: () => analyzeDevice(contextMenu.target!) }
  ]
})

// Device helpers
const getDeviceIcon = (type: string) => {
  const icons = {
    router: '🔀',
    switch: '🔁',
    firewall: '🛡️',
    vpn_gateway: '🔐'
  }
  return icons[type as keyof typeof icons] || '📡'
}

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
  console.log('Load Canvas')
}

const saveCanvas = () => {
  console.log('Save Canvas')  
}

const clearCanvas = () => {
  console.log('Clear Canvas')
  // deviceStore.clearDevices() // TODO: Implement clearDevices method in store
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
    { x: 0, y: 40 },    // Left
    { x: 80, y: 40 },   // Right
    { x: 40, y: 0 },    // Top
    { x: 40, y: 80 }    // Bottom
  ]
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
    const { type, template } = JSON.parse(data) as { type: string; template: DeviceTemplate }
    console.log('🔍 Parsed drop data:', { type, template })

    if (type === 'device-template') {
      const rect = canvasContainer.value?.getBoundingClientRect()
      if (!rect) {
        console.log('❌ No canvas container rect')
        return
      }

      const x = (event.clientX - rect.left - position.x) / scale.value
      const y = (event.clientY - rect.top - position.y) / scale.value

      console.log('📍 Drop position:', { x, y, clientX: event.clientX, clientY: event.clientY })

      const deviceName = `${template.name}-${Date.now()}`

      console.log('🏗️ Creating device:', deviceName)
      await deviceStore.createDevice({
        name: deviceName,
        device_type: template.type,
        position_x: x - 40, // Center the device
        position_y: y - 40,
        properties: JSON.stringify(template.defaultProperties)
      })
      console.log('✅ Device created successfully')
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

const onDeviceClick = (device: Device) => {
  console.log('🖱️ Device click detected for:', device.name, 'context menu showing:', contextMenu.show, 'target type:', contextMenu.targetType)

  selectedDevice.value = device
  deviceStore.setSelectedDevice(device)

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
  connectionStart.value = { device, point: { x: 40, y: 40 } }
  hideContextMenu()
}

const centerOnDevice = (device: Device) => {
  const containerRect = canvasContainer.value?.getBoundingClientRect()
  if (!containerRect) return

  canvasStore.setPosition({
    x: containerRect.width / 2 - (device.position_x + 40) * scale.value,
    y: containerRect.height / 2 - (device.position_y + 40) * scale.value
  })
  hideContextMenu()
}

const deleteDevice = async (device: Device) => {
  if (confirm(`Delete ${device.name}?`)) {
    try {
      await deviceStore.deleteDevice(device.id)
    } catch (error) {
      console.error('Failed to delete device:', error)
    }
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
</style>