import { ref, computed } from 'vue'
import { useDevicesStore, type Device } from '@/stores/devices'
import { devicesApi } from '@/services/api'

export function useDeviceOperations() {
  const deviceStore = useDevicesStore()

  // Modal states
  const showAddModal = ref(false)
  const showEditModal = ref(false)
  const showDeleteConfirmDialog = ref(false)
  const showDiscoveryModal = ref(false)
  const showBulkDeleteDialog = ref(false)
  
  // Current device being edited/deleted
  const currentDevice = ref<Device | null>(null)
  
  // Discovery states - simplified for now (no API available)
  const discoveryTargets = ref<Array<{
    ip: string
    hostname: string
    type: string
    credentials: any
    device_id?: number
  }>>([])
  const discoveryProgress = ref(0)
  const discoveryResults = ref<any[]>([])

  // Delete device with confirmation
  const deleteDevice = (device: Device) => {
    console.log('Delete Device requested for:', device.name)
    currentDevice.value = device
    showDeleteConfirmDialog.value = true
  }

  const confirmDeleteDevice = async () => {
    if (!currentDevice.value) return

    console.log('Confirm Delete Device:', currentDevice.value.name)
    
    try {
      // Delete from API if it has a server ID
      if (currentDevice.value.id && currentDevice.value.id > 0) {
        await devicesApi.deleteDevice(currentDevice.value.id)
        console.log('✅ Device deleted from server')
      }

      // Remove from store
      deviceStore.deleteDevice(currentDevice.value.id)
      console.log('✅ Device removed from canvas')

      currentDevice.value = null
      showDeleteConfirmDialog.value = false
    } catch (error) {
      console.error('❌ Failed to delete device:', error)
    }
  }

  // Bulk delete selected devices - simplified without selection property
  const bulkDeleteSelectedDevices = () => {
    // For now, we'll implement this differently since devices don't have selection property
    console.log('Bulk delete not implemented - devices need selection property')
    return
  }

  const confirmBulkDeleteDevices = async () => {
    console.log('Bulk delete not implemented')
    showBulkDeleteDialog.value = false
  }

  // Edit device
  const editDevice = (device: Device) => {
    console.log('Edit Device:', device.name)
    currentDevice.value = device
    showEditModal.value = true
  }

  // Add device
  const addDevice = () => {
    console.log('Add Device')
    currentDevice.value = null
    showAddModal.value = true
  }

  // Device discovery operations - simplified without discovery API
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const runDiscovery = async (_config: {
    subnets: string[]
    snmp_community?: string
    snmp_version?: string
    ssh_username?: string
    ssh_password?: string
    ssh_key_path?: string
  }) => {
    console.log('🔍 Discovery not implemented - no discoveryApi available')
    discoveryProgress.value = 0
    discoveryResults.value = []
    return []
  }

  const addDiscoveredDevices = async (selectedTargets: typeof discoveryTargets.value) => {
    console.log('➕ Adding', selectedTargets.length, 'discovered devices to canvas')

    try {
      for (const target of selectedTargets) {
        // Create device data
        const deviceData = {
          name: target.hostname,
          device_type: target.type as Device['device_type'],
          ip_address: target.ip,
          position_x: Math.random() * 400 + 100, // Random position
          position_y: Math.random() * 300 + 100,
          properties: JSON.stringify(target.credentials),
        }

        // Add to store using correct method
        const newDevice = deviceStore.createDevice(deviceData)
        console.log('✅ Device added to canvas:', newDevice.name)
      }

      // Clear discovery state
      discoveryTargets.value = []
      showDiscoveryModal.value = false

      console.log('✅ All discovered devices added successfully')
    } catch (error) {
      console.error('❌ Failed to add discovered devices:', error)
    }
  }

  // Device property operations
  const updateDeviceProperty = async (deviceId: number, property: string, value: any) => {
    console.log(`Updating device ${deviceId} property ${property}:`, value)

    try {
      // Get current device
      const device = deviceStore.devices.find(d => d.id === deviceId)
      if (!device) {
        console.error('Device not found:', deviceId)
        return
      }

      // Update the device property
      const updatedDevice = {
        ...device,
        [property]: value,
      }

      deviceStore.updateDevice(deviceId, updatedDevice)
      console.log('✅ Device property updated successfully')
    } catch (error) {
      console.error('❌ Failed to update device property:', error)
    }
  }

  // Connection operations
  const createConnection = async (sourceId: number, targetId: number, connectionType = 'ethernet') => {
    console.log(`Creating ${connectionType} connection: ${sourceId} -> ${targetId}`)

    try {
      const connectionData = {
        source_device_id: sourceId,
        target_device_id: targetId,
        connection_type: connectionType,
        properties: '',
      }

      const connection = deviceStore.createConnection(connectionData)
      console.log('✅ Connection added to canvas')

      return connection
    } catch (error) {
      console.error('❌ Failed to create connection:', error)
    }
  }

  const deleteConnection = (connectionId: number) => {
    console.log('Deleting connection:', connectionId)
    
    try {
      // Find the connection and remove it
      deviceStore.connections = deviceStore.connections.filter(c => c.id !== connectionId)
      console.log('✅ Connection removed')
    } catch (error) {
      console.error('❌ Failed to delete connection:', error)
    }
  }

  // Computed values - simplified without selection property
  const selectedDevicesCount = computed(() => 0) // No selection implemented yet
  const hasSelectedDevices = computed(() => false)

  return {
    // State
    showAddModal,
    showEditModal,
    showDeleteConfirmDialog,
    showDiscoveryModal,
    showBulkDeleteDialog,
    currentDevice,
    discoveryTargets,
    discoveryProgress,
    discoveryResults,
    
    // Computed
    selectedDevicesCount,
    hasSelectedDevices,
    
    // Device operations
    deleteDevice,
    confirmDeleteDevice,
    bulkDeleteSelectedDevices,
    confirmBulkDeleteDevices,
    editDevice,
    addDevice,
    updateDeviceProperty,
    
    // Discovery operations
    runDiscovery,
    addDiscoveredDevices,
    
    // Connection operations
    createConnection,
    deleteConnection,
  }
}