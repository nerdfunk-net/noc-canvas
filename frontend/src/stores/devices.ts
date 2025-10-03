import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Device {
  id: number
  name: string
  device_type: 'router' | 'switch' | 'firewall' | 'vpn_gateway'
  ip_address?: string
  position_x: number
  position_y: number
  properties?: string
  layer?: string // 'background' or 'devices'
}

export interface Connection {
  id: number
  source_device_id: number
  target_device_id: number
  connection_type: string
  properties?: string
  routing_style?: 'straight' | 'orthogonal' // Line routing: straight or with right-angle corners
  waypoints?: { x: number; y: number }[] // Custom waypoints for manual route adjustment
}

export const useDevicesStore = defineStore('devices', () => {
  const devices = ref<Device[]>([])
  const connections = ref<Connection[]>([])
  const selectedDevice = ref<Device | null>(null)
  const loading = ref(false)

  // Generate unique local IDs for devices and connections
  let nextDeviceId = 1
  let nextConnectionId = 1

  const generateDeviceId = () => {
    // Use timestamp + counter to ensure uniqueness across sessions
    return Date.now() * 1000 + nextDeviceId++
  }

  const generateConnectionId = () => {
    return Date.now() * 1000 + nextConnectionId++
  }

  const loadDevicesFromCanvasData = (canvasDevices: Device[], canvasConnections: Connection[]) => {
    loading.value = true
    try {
      // Load devices and connections from canvas data (pure frontend)
      devices.value = [...canvasDevices]
      connections.value = [...canvasConnections]

      // Update ID counters to avoid conflicts
      if (devices.value.length > 0) {
        const maxDeviceId = Math.max(...devices.value.map((d) => d.id))
        nextDeviceId = Math.max(nextDeviceId, maxDeviceId + 1)
      }
      if (connections.value.length > 0) {
        const maxConnectionId = Math.max(...connections.value.map((c) => c.id))
        nextConnectionId = Math.max(nextConnectionId, maxConnectionId + 1)
      }

      console.log('✅ Devices loaded from canvas data:', devices.value.length)
    } catch (error) {
      console.error('Failed to load devices from canvas data:', error)
    } finally {
      loading.value = false
    }
  }

  const createDevice = (deviceData: Omit<Device, 'id'>): Device => {
    try {
      const newDevice: Device = {
        id: generateDeviceId(),
        ...deviceData,
      }
      devices.value.push(newDevice)
      console.log('✅ Device created locally:', newDevice.name, 'ID:', newDevice.id)
      return newDevice
    } catch (error) {
      console.error('Failed to create device:', error)
      throw error
    }
  }

  const updateDevice = (deviceId: number, updates: Partial<Device>): Device | null => {
    try {
      const index = devices.value.findIndex((d) => d.id === deviceId)
      if (index !== -1) {
        const updatedDevice = { ...devices.value[index], ...updates }
        devices.value[index] = updatedDevice
        console.log('✅ Device updated locally:', updatedDevice.name, 'ID:', deviceId)
        return updatedDevice
      }
      console.warn('Device not found for update:', deviceId)
      return null
    } catch (error) {
      console.error('Failed to update device:', error)
      throw error
    }
  }

  const deleteDevice = (deviceId: number): boolean => {
    try {
      const deviceToDelete = devices.value.find((d) => d.id === deviceId)
      if (deviceToDelete) {
        devices.value = devices.value.filter((d) => d.id !== deviceId)
        // Also remove any connections involving this device
        connections.value = connections.value.filter(
          (c) => c.source_device_id !== deviceId && c.target_device_id !== deviceId
        )
        console.log('✅ Device deleted locally:', deviceToDelete.name, 'ID:', deviceId)
        return true
      }
      console.warn('Device not found for deletion:', deviceId)
      return false
    } catch (error) {
      console.error('Failed to delete device:', error)
      throw error
    }
  }

  const findDeviceByName = (name: string): Device | null => {
    return devices.value.find((device) => device.name === name) || null
  }

  const findDeviceByNautobotId = (nautobotId: string): Device | null => {
    return (
      devices.value.find((device) => {
        if (!device.properties) return false
        try {
          const props = JSON.parse(device.properties)
          return props.nautobot_id === nautobotId
        } catch {
          return false
        }
      }) || null
    )
  }

  const getConnectionsData = (): Connection[] => {
    return [...connections.value]
  }

  const createConnection = (connectionData: Omit<Connection, 'id'>): Connection => {
    try {
      const newConnection: Connection = {
        id: generateConnectionId(),
        ...connectionData,
      }
      connections.value.push(newConnection)
      console.log('✅ Connection created locally:', newConnection.id)
      return newConnection
    } catch (error) {
      console.error('Failed to create connection:', error)
      throw error
    }
  }

  const setSelectedDevice = (device: Device | null) => {
    selectedDevice.value = device
  }

  const clearDevices = (): void => {
    // Clear all devices from the canvas (pure frontend)
    try {
      devices.value = []
      connections.value = []
      selectedDevice.value = null
      console.log('✅ Canvas cleared locally')
    } catch (error) {
      console.error('Failed to clear devices:', error)
      throw error
    }
  }

  return {
    devices,
    connections,
    selectedDevice,
    loading,
    loadDevicesFromCanvasData,
    createDevice,
    updateDevice,
    deleteDevice,
    findDeviceByName,
    findDeviceByNautobotId,
    getConnectionsData,
    createConnection,
    setSelectedDevice,
    clearDevices,
  }
})
