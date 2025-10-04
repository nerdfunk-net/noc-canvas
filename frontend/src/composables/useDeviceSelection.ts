import { ref } from 'vue'
import { useDevicesStore, type Device } from '@/stores/devices'

export function useDeviceSelection() {
  const deviceStore = useDevicesStore()

  // State
  const selectedDevice = ref<Device | null>(null)
  const selectedDevices = ref<Set<number>>(new Set())

  // Selection box for multi-selection
  const selectionBox = ref<{
    startX: number
    startY: number
    endX: number
    endY: number
  } | null>(null)

  // Methods
  const selectDevicesInBox = (box: {
    startX: number
    startY: number
    endX: number
    endY: number
  }) => {
    const minX = Math.min(box.startX, box.endX)
    const maxX = Math.max(box.startX, box.endX)
    const minY = Math.min(box.startY, box.endY)
    const maxY = Math.max(box.startY, box.endY)

    console.log('🔍 Selecting devices in box:', { minX, minY, maxX, maxY })

    // Start with current selection (additive selection with Shift+drag)
    const newDeviceSelection = new Set(selectedDevices.value)
    const deviceSize = 80 // Device width/height

    // Select devices
    deviceStore.devices.forEach((device) => {
      // Check if device overlaps with selection box
      const deviceLeft = device.position_x
      const deviceRight = device.position_x + deviceSize
      const deviceTop = device.position_y
      const deviceBottom = device.position_y + deviceSize

      // Check if device overlaps with selection box
      const overlapsX = deviceLeft < maxX && deviceRight > minX
      const overlapsY = deviceTop < maxY && deviceBottom > minY

      if (overlapsX && overlapsY) {
        newDeviceSelection.add(device.id)
        console.log('✅ Selected device:', device.name, 'at', device.position_x, device.position_y)
      }
    })

    selectedDevices.value = newDeviceSelection

    // Update single selection based on multi-selection
    if (selectedDevices.value.size === 1) {
      const singleDeviceId = Array.from(selectedDevices.value)[0]
      const device = deviceStore.devices.find((d) => d.id === singleDeviceId)
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

  const selectDevice = (device: Device, isShiftClick = false) => {
    if (isShiftClick) {
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
  }

  const clearSelection = () => {
    selectedDevices.value.clear()
    selectedDevice.value = null
    deviceStore.setSelectedDevice(null)
  }

  const getSelectedDevicesArray = (): Device[] => {
    return Array.from(selectedDevices.value)
      .map(id => deviceStore.devices.find(d => d.id === id))
      .filter((device): device is Device => device !== undefined)
  }

  return {
    // State
    selectedDevice,
    selectedDevices,
    selectionBox,
    
    // Methods
    selectDevicesInBox,
    selectDevice,
    clearSelection,
    getSelectedDevicesArray,
  }
}