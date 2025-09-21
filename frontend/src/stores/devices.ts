import { defineStore } from 'pinia'
import { ref } from 'vue'
import { devicesApi } from '@/services/api'

export interface Device {
  id: number
  name: string
  device_type: 'router' | 'switch' | 'firewall' | 'vpn_gateway'
  ip_address?: string
  position_x: number
  position_y: number
  properties?: string
}

export interface Connection {
  id: number
  source_device_id: number
  target_device_id: number
  connection_type: string
  properties?: string
}

export const useDevicesStore = defineStore('devices', () => {
  const devices = ref<Device[]>([])
  const connections = ref<Connection[]>([])
  const selectedDevice = ref<Device | null>(null)
  const loading = ref(false)

  const fetchDevices = async () => {
    loading.value = true
    try {
      devices.value = await devicesApi.getDevices()
    } catch (error) {
      console.error('Failed to fetch devices:', error)
    } finally {
      loading.value = false
    }
  }

  const createDevice = async (deviceData: Omit<Device, 'id'>) => {
    try {
      const newDevice = await devicesApi.createDevice(deviceData)
      devices.value.push(newDevice)
      return newDevice
    } catch (error) {
      console.error('Failed to create device:', error)
      throw error
    }
  }

  const updateDevice = async (deviceId: number, updates: Partial<Device>) => {
    try {
      const updatedDevice = await devicesApi.updateDevice(deviceId, updates)
      const index = devices.value.findIndex(d => d.id === deviceId)
      if (index !== -1) {
        devices.value[index] = updatedDevice
      }
      return updatedDevice
    } catch (error) {
      console.error('Failed to update device:', error)
      throw error
    }
  }

  const deleteDevice = async (deviceId: number) => {
    try {
      await devicesApi.deleteDevice(deviceId)
      devices.value = devices.value.filter(d => d.id !== deviceId)
    } catch (error) {
      console.error('Failed to delete device:', error)
      throw error
    }
  }

  const findDeviceByName = (name: string): Device | null => {
    return devices.value.find(device => device.name === name) || null
  }

  const findDeviceByNautobotId = (nautobotId: string): Device | null => {
    return devices.value.find(device => {
      if (!device.properties) return false
      try {
        const props = JSON.parse(device.properties)
        return props.nautobot_id === nautobotId
      } catch {
        return false
      }
    }) || null
  }

  const fetchConnections = async () => {
    try {
      connections.value = await devicesApi.getConnections()
    } catch (error) {
      console.error('Failed to fetch connections:', error)
    }
  }

  const createConnection = async (connectionData: Omit<Connection, 'id'>) => {
    try {
      const newConnection = await devicesApi.createConnection(connectionData)
      connections.value.push(newConnection)
      return newConnection
    } catch (error) {
      console.error('Failed to create connection:', error)
      throw error
    }
  }

  const setSelectedDevice = (device: Device | null) => {
    selectedDevice.value = device
  }

  const clearDevices = async () => {
    // Clear all devices from the canvas
    try {
      // Delete all devices via API
      for (const device of devices.value) {
        await devicesApi.deleteDevice(device.id)
      }
      // Clear the local store
      devices.value = []
      connections.value = []
      selectedDevice.value = null
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
    fetchDevices,
    createDevice,
    updateDevice,
    deleteDevice,
    findDeviceByName,
    findDeviceByNautobotId,
    fetchConnections,
    createConnection,
    setSelectedDevice,
    clearDevices
  }
})