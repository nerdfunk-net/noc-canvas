import { ref } from 'vue'
import type Konva from 'konva'
import { type Device } from '@/stores/devices'

export interface MousePosition {
  x: number
  y: number
}

export function useCanvasEvents() {
  // Mouse state tracking
  const isDragging = ref(false)
  const lastMousePos = ref<MousePosition>({ x: 0, y: 0 })
  const dragStartPos = ref<MousePosition>({ x: 0, y: 0 })
  const isSelectionBoxActive = ref(false)
  const selectionBoxStart = ref<MousePosition>({ x: 0, y: 0 })
  const selectionBoxEnd = ref<MousePosition>({ x: 0, y: 0 })

  // Connection mode state
  const isConnectionMode = ref(false)
  const connectionSourceDevice = ref<Device | null>(null)

  // Global mouse down handler
  const onGlobalMouseDown = (e: MouseEvent) => {
    console.log('🖱️ Global Mouse Down at:', e.clientX, e.clientY)

    // Store drag start position
    dragStartPos.value = { x: e.clientX, y: e.clientY }
    lastMousePos.value = { x: e.clientX, y: e.clientY }

    // Check if this is a canvas background click (not a device)
    const target = e.target as HTMLElement
    const isCanvasBackground = target.tagName === 'CANVAS' || target.classList.contains('konvajs-content')

    if (isCanvasBackground && !isConnectionMode.value) {
      console.log('📦 Starting selection box')
      isSelectionBoxActive.value = true
      selectionBoxStart.value = { x: e.clientX, y: e.clientY }
      selectionBoxEnd.value = { x: e.clientX, y: e.clientY }
    }
  }

  // Global mouse move handler
  const onGlobalMouseMove = (e: MouseEvent) => {
    const currentPos = { x: e.clientX, y: e.clientY }
    const deltaX = currentPos.x - dragStartPos.value.x
    const deltaY = currentPos.y - dragStartPos.value.y
    const dragThreshold = 5

    // Check if we've moved enough to start dragging
    if (!isDragging.value && (Math.abs(deltaX) > dragThreshold || Math.abs(deltaY) > dragThreshold)) {
      isDragging.value = true
      console.log('🚀 Drag started')
    }

    // Update selection box if active
    if (isSelectionBoxActive.value) {
      selectionBoxEnd.value = currentPos
    }

    lastMousePos.value = currentPos
  }

  // Global mouse up handler
  const onGlobalMouseUp = () => {
    console.log('🖱️ Global Mouse Up - isDragging:', isDragging.value, 'isSelectionBox:', isSelectionBoxActive.value)

    // Handle selection box completion
    if (isSelectionBoxActive.value) {
      console.log('📦 Selection box completed')
      // The actual device selection will be handled by the component
      // since it needs access to the canvas stage and device positions
      isSelectionBoxActive.value = false
    }

    // Reset drag state
    isDragging.value = false
    dragStartPos.value = { x: 0, y: 0 }
  }

  // Device-specific mouse handlers
  const onDeviceMouseDown = (device: Device, konvaEvent: Konva.KonvaEventObject<MouseEvent>) => {
    console.log('🖱️ Device Mouse Down:', device.name, 'Connection Mode:', isConnectionMode.value)

    if (isConnectionMode.value) {
      if (!connectionSourceDevice.value) {
        // First click - select source device
        connectionSourceDevice.value = device
        console.log('🔗 Connection source selected:', device.name)
        konvaEvent.cancelBubble = true
        return
      } else if (connectionSourceDevice.value.id !== device.id) {
        // Second click - create connection
        console.log('🔗 Creating connection:', connectionSourceDevice.value.name, '->', device.name)
        // The actual connection creation will be handled by the component
        // Reset connection mode
        connectionSourceDevice.value = null
        konvaEvent.cancelBubble = true
        return
      }
    }

    // Normal device selection behavior
    konvaEvent.cancelBubble = true
  }

  const onDeviceClick = (device: Device, konvaEvent: Konva.KonvaEventObject<MouseEvent>) => {
    console.log('🖱️ Device Click:', device.name)

    // Only process clicks if we weren't dragging
    if (isDragging.value) {
      console.log('🚫 Ignoring click - was dragging')
      return
    }

    const shiftPressed = konvaEvent.evt.shiftKey
    console.log('🔧 Shift pressed:', shiftPressed)

    // Device selection logic will be handled by the component
    // since it needs to interact with the device selection composable

    konvaEvent.cancelBubble = true
  }

  const onDeviceDoubleClick = (device: Device, konvaEvent: Konva.KonvaEventObject<MouseEvent>) => {
    console.log('🖱️ Device Double Click:', device.name)
    
    // Prevent event bubbling
    konvaEvent.cancelBubble = true
    
    // The actual edit modal showing will be handled by the component
    // since it needs to interact with the device operations composable
  }

  const onRightClick = (device: Device | null, konvaEvent: Konva.KonvaEventObject<MouseEvent>) => {
    console.log('🖱️ Right Click on:', device ? device.name : 'canvas background')

    // Prevent default context menu
    konvaEvent.evt.preventDefault()
    konvaEvent.cancelBubble = true

    // The actual context menu showing will be handled by the component
    // since it needs to interact with the context menu composable
  }

  // Connection mode controls
  const toggleConnectionMode = () => {
    isConnectionMode.value = !isConnectionMode.value
    connectionSourceDevice.value = null
    console.log('🔗 Connection mode:', isConnectionMode.value ? 'ENABLED' : 'DISABLED')
  }

  const exitConnectionMode = () => {
    isConnectionMode.value = false
    connectionSourceDevice.value = null
    console.log('🔗 Connection mode EXITED')
  }

  // Canvas keyboard handlers
  const onCanvasKeyDown = (e: KeyboardEvent) => {
    console.log('⌨️ Canvas Key Down:', e.key)

    // ESC key - exit connection mode
    if (e.key === 'Escape') {
      if (isConnectionMode.value) {
        exitConnectionMode()
        e.preventDefault()
      }
    }

    // Delete key - delete selected devices
    if (e.key === 'Delete' || e.key === 'Backspace') {
      // The actual deletion will be handled by the component
      // since it needs to interact with the device operations composable
      e.preventDefault()
    }
  }

  // Helper function to get relative mouse position on canvas
  const getRelativePointerPosition = (stage: Konva.Stage): MousePosition => {
    const pointer = stage.getPointerPosition()
    if (!pointer) return { x: 0, y: 0 }

    const transform = stage.getAbsoluteTransform().copy()
    transform.invert()
    const relativePos = transform.point(pointer)
    
    return {
      x: relativePos.x,
      y: relativePos.y
    }
  }

  // Helper function to calculate distance between two points
  const calculateDistance = (pos1: MousePosition, pos2: MousePosition): number => {
    const dx = pos2.x - pos1.x
    const dy = pos2.y - pos1.y
    return Math.sqrt(dx * dx + dy * dy)
  }

  // Selection box calculations
  const getSelectionBoxDimensions = () => {
    if (!isSelectionBoxActive.value) return null

    const startX = Math.min(selectionBoxStart.value.x, selectionBoxEnd.value.x)
    const startY = Math.min(selectionBoxStart.value.y, selectionBoxEnd.value.y)
    const width = Math.abs(selectionBoxEnd.value.x - selectionBoxStart.value.x)
    const height = Math.abs(selectionBoxEnd.value.y - selectionBoxStart.value.y)

    return { startX, startY, width, height }
  }

  return {
    // State
    isDragging,
    lastMousePos,
    dragStartPos,
    isSelectionBoxActive,
    selectionBoxStart,
    selectionBoxEnd,
    isConnectionMode,
    connectionSourceDevice,

    // Mouse event handlers
    onGlobalMouseDown,
    onGlobalMouseMove,
    onGlobalMouseUp,
    onDeviceMouseDown,
    onDeviceClick,
    onDeviceDoubleClick,
    onRightClick,

    // Connection mode controls
    toggleConnectionMode,
    exitConnectionMode,

    // Keyboard handlers
    onCanvasKeyDown,

    // Helper functions
    getRelativePointerPosition,
    calculateDistance,
    getSelectionBoxDimensions,
  }
}