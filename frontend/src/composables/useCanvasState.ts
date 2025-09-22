import { ref, computed } from 'vue'
import { useDevicesStore, type Device } from '@/stores/devices'
import { canvasApi } from '@/services/api'

export function useCanvasState() {
  const deviceStore = useDevicesStore()

  // Canvas save state tracking
  const currentCanvasId = ref<number | null>(null)
  const lastSavedState = ref<{ devices: Device[]; connections: any[] }>({
    devices: [],
    connections: [],
  })

  // Modal states
  const showSaveModal = ref(false)
  const showLoadModal = ref(false)
  const showLoadConfirmDialog = ref(false)
  const showClearDialog = ref(false)
  const showUnsavedChangesDialog = ref(false)
  
  // Pending states
  const pendingCanvasId = ref<number | null>(null)
  const pendingAction = ref<(() => void) | null>(null)

  // Computed property to check if canvas has unsaved changes
  const hasUnsavedChanges = computed(() => {
    const currentDevices = deviceStore.devices
    const currentConnections = deviceStore.connections

    // If canvas is empty and was empty when last saved, no changes
    if (
      currentDevices.length === 0 &&
      currentConnections.length === 0 &&
      lastSavedState.value.devices.length === 0 &&
      lastSavedState.value.connections.length === 0
    ) {
      return false
    }

    // Check if devices have changed
    if (currentDevices.length !== lastSavedState.value.devices.length) {
      return true
    }

    // Check if connections have changed
    if (currentConnections.length !== lastSavedState.value.connections.length) {
      return true
    }

    // Deep comparison of devices (simplified - just check IDs, names, and positions)
    for (let i = 0; i < currentDevices.length; i++) {
      const current = currentDevices[i]
      const saved = lastSavedState.value.devices.find((d) => d.id === current.id)
      if (
        !saved ||
        saved.name !== current.name ||
        saved.position_x !== current.position_x ||
        saved.position_y !== current.position_y ||
        saved.device_type !== current.device_type ||
        saved.ip_address !== current.ip_address
      ) {
        return true
      }
    }

    // Deep comparison of connections
    for (let i = 0; i < currentConnections.length; i++) {
      const current = currentConnections[i]
      const saved = lastSavedState.value.connections.find((c) => c.id === current.id)
      if (
        !saved ||
        saved.source_device_id !== current.source_device_id ||
        saved.target_device_id !== current.target_device_id ||
        saved.connection_type !== current.connection_type
      ) {
        return true
      }
    }

    return false
  })

  // Function to update the saved state (called after successful save/load)
  const updateSavedState = () => {
    lastSavedState.value = {
      devices: [...deviceStore.devices],
      connections: [...deviceStore.connections],
    }
    console.log(
      '💾 Saved state updated with',
      lastSavedState.value.devices.length,
      'devices and',
      lastSavedState.value.connections.length,
      'connections'
    )
  }

  // Function to prompt user to save before certain actions
  const promptToSaveBeforeAction = (actionName: string, actionCallback: () => void) => {
    if (hasUnsavedChanges.value) {
      // Store the pending action and show dialog
      pendingAction.value = actionCallback
      showUnsavedChangesDialog.value = true
      return
    }

    // Continue with the action if no unsaved changes
    actionCallback()
  }

  const saveCanvasData = async (data: { name: string; sharable: boolean; canvasId?: number }) => {
    // Collect current canvas state
    const canvasData = {
      devices: deviceStore.devices.map((device) => ({
        id: device.id,
        name: device.name,
        device_type: device.device_type,
        ip_address: device.ip_address,
        position_x: device.position_x,
        position_y: device.position_y,
        properties: device.properties,
      })),
      connections: deviceStore.connections.map((connection) => ({
        id: connection.id,
        source_device_id: connection.source_device_id,
        target_device_id: connection.target_device_id,
        connection_type: connection.connection_type,
        properties: connection.properties,
      })),
    }

    let response
    if (data.canvasId) {
      // Update existing canvas
      response = await canvasApi.updateCanvas(data.canvasId, {
        name: data.name,
        sharable: data.sharable,
        canvas_data: canvasData,
      })
      console.log('✅ Canvas updated successfully:', response)
      currentCanvasId.value = data.canvasId
    } else {
      // Create new canvas
      response = await canvasApi.saveCanvas({
        name: data.name,
        sharable: data.sharable,
        canvas_data: canvasData,
      })
      console.log('✅ Canvas saved successfully:', response)
      currentCanvasId.value = response.id
    }

    // Update saved state after successful save
    updateSavedState()

    // Execute pending action if there was one (from unsaved changes dialog)
    if (pendingAction.value) {
      pendingAction.value()
      pendingAction.value = null
    }

    return response
  }

  const loadCanvasById = async (canvasId: number) => {
    console.log('🔄 Loading canvas from database...', canvasId)

    // Clear current canvas first if it has devices
    if (deviceStore.devices.length > 0) {
      deviceStore.clearDevices()
      console.log('✅ Current canvas cleared')
    }

    // Fetch canvas data
    const canvas = await canvasApi.getCanvas(canvasId)
    console.log('✅ Canvas data loaded:', canvas)

    // Load devices and connections directly from canvas data (pure frontend)
    // Convert CanvasDeviceData to Device with proper types
    const devicesWithCorrectTypes = canvas.canvas_data.devices.map((device) => ({
      ...device,
      device_type: device.device_type as Device['device_type'],
    }))

    deviceStore.loadDevicesFromCanvasData(devicesWithCorrectTypes, canvas.canvas_data.connections)

    // Update tracking state
    currentCanvasId.value = canvasId
    updateSavedState()

    console.log(
      '✅ Canvas loaded successfully with',
      canvas.canvas_data.devices.length,
      'devices and',
      canvas.canvas_data.connections.length,
      'connections'
    )

    return canvas
  }

  const quickSave = async () => {
    console.log('Quick Save Canvas')

    if (!currentCanvasId.value) {
      console.log('No canvas ID found, opening Save As dialog')
      showSaveModal.value = true
      return
    }

    try {
      // Get current canvas info to preserve name and sharable setting
      const currentCanvas = await canvasApi.getCanvas(currentCanvasId.value)

      // Update existing canvas
      await saveCanvasData({
        name: currentCanvas.name,
        sharable: currentCanvas.sharable,
        canvasId: currentCanvasId.value,
      })

      console.log('✅ Canvas quick saved successfully')
    } catch (error) {
      console.error('❌ Failed to quick save canvas:', error)
      // Fall back to Save As dialog on error
      showSaveModal.value = true
    }
  }

  const clearCanvas = () => {
    console.log('Clear Canvas - checking for unsaved changes')
    promptToSaveBeforeAction('clearing the canvas', () => {
      console.log('Clear Canvas - showing confirmation dialog')
      showClearDialog.value = true
    })
  }

  const executeClearCanvas = () => {
    try {
      deviceStore.clearDevices()
      // Reset tracking state
      currentCanvasId.value = null
      updateSavedState()
      console.log('✅ Canvas cleared successfully')
    } catch (error) {
      console.error('❌ Failed to clear canvas:', error)
    }
  }

  return {
    // State
    currentCanvasId,
    lastSavedState,
    showSaveModal,
    showLoadModal,
    showLoadConfirmDialog,
    showClearDialog,
    showUnsavedChangesDialog,
    pendingCanvasId,
    pendingAction,
    
    // Computed
    hasUnsavedChanges,
    
    // Methods
    updateSavedState,
    promptToSaveBeforeAction,
    saveCanvasData,
    loadCanvasById,
    quickSave,
    clearCanvas,
    executeClearCanvas,
  }
}