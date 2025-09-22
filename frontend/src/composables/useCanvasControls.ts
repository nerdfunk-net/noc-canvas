import { ref, computed } from 'vue'
import { useDevicesStore } from '@/stores/devices'
import { useCanvasStore } from '@/stores/canvas'

export function useCanvasControls() {
  const deviceStore = useDevicesStore()
  const canvasStore = useCanvasStore()

  // State
  const showGrid = ref(true)
  const connectionMode = ref(false)
  const connectionStart = ref<{
    device: any
    point: { x: number; y: number }
  } | null>(null)

  // Computed
  const scale = computed(() => canvasStore.scale)
  const position = computed(() => canvasStore.position)

  // Methods
  const toggleGrid = () => {
    showGrid.value = !showGrid.value
  }

  const toggleConnectionMode = () => {
    connectionMode.value = !connectionMode.value
    connectionStart.value = null
  }

  const resetView = () => {
    canvasStore.resetView()
  }

  const fitToScreen = (canvasContainer: HTMLElement | null) => {
    if (!canvasContainer || deviceStore.devices.length === 0) return

    const padding = 100
    let minX = Infinity,
      minY = Infinity,
      maxX = -Infinity,
      maxY = -Infinity

    deviceStore.devices.forEach((device) => {
      minX = Math.min(minX, device.position_x)
      minY = Math.min(minY, device.position_y)
      maxX = Math.max(maxX, device.position_x + 80)
      maxY = Math.max(maxY, device.position_y + 80)
    })

    const width = maxX - minX + padding * 2
    const height = maxY - minY + padding * 2

    const containerRect = canvasContainer.getBoundingClientRect()

    const scaleX = containerRect.width / width
    const scaleY = containerRect.height / height
    const newScale = Math.min(scaleX, scaleY, 1)

    canvasStore.setZoom(newScale)
    canvasStore.setPosition({
      x: (containerRect.width - width * newScale) / 2 - (minX - padding) * newScale,
      y: (containerRect.height - height * newScale) / 2 - (minY - padding) * newScale,
    })
  }

  return {
    // State
    showGrid,
    connectionMode,
    connectionStart,
    
    // Computed
    scale,
    position,
    
    // Methods
    toggleGrid,
    toggleConnectionMode,
    resetView,
    fitToScreen,
  }
}