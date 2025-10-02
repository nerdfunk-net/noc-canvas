import { type Device, useDevicesStore } from '@/stores/devices'
import { makeAuthenticatedRequest } from '@/services/api'

const DEVICE_SIZE = 60
const DEVICE_HALF_SIZE = 30

export function useNeighborOperations() {
  const deviceStore = useDevicesStore()

  // Show CDP neighbors for a device
  const showNeighbors = async (
    device: Device,
    setModalState: (title: string, content: string, loading: boolean, show: boolean) => void
  ) => {
    try {
      setModalState(`CDP Neighbors - ${device.name}`, '', true, true)

      const deviceProps = device.properties ? JSON.parse(device.properties) : {}
      const nautobotId = deviceProps.nautobot_id

      if (!nautobotId) {
        setModalState(`CDP Neighbors - ${device.name}`, 'Error: Device does not have a Nautobot ID', false, true)
        return
      }

      const response = await makeAuthenticatedRequest(`/api/devices/${nautobotId}/cdp-neighbors`)

      if (response.ok) {
        const data = await response.json()

        if (data.success) {
          setModalState(`CDP Neighbors - ${device.name}`, data.output || 'No neighbors found', false, true)
        } else {
          setModalState(`CDP Neighbors - ${device.name}`, `Error: ${data.error || 'Failed to retrieve CDP neighbors'}`, false, true)
        }
      } else {
        const errorData = await response.json()
        setModalState(`CDP Neighbors - ${device.name}`, `Error: ${errorData.detail || 'Failed to retrieve CDP neighbors'}`, false, true)
      }
    } catch (error) {
      console.error('Error fetching CDP neighbors:', error)
      setModalState(`CDP Neighbors - ${device.name}`, `Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`, false, true)
    }
  }

  // Add CDP neighbors to canvas
  const addNeighborsToCanvas = async (
    device: Device,
    setModalState: (title: string, content: string, loading: boolean, show: boolean) => void
  ) => {
    try {
      setModalState('Adding Neighbors...', 'Fetching CDP neighbors...', true, true)

      const deviceProps = device.properties ? JSON.parse(device.properties) : {}
      const nautobotId = deviceProps.nautobot_id

      if (!nautobotId) {
        setModalState('Error', 'Device does not have a Nautobot ID', false, true)
        return
      }

      const response = await makeAuthenticatedRequest(`/api/devices/${nautobotId}/cdp-neighbors-parsed`)

      if (!response.ok) {
        const errorData = await response.json()
        setModalState('Error', errorData.detail || 'Failed to retrieve neighbors', false, true)
        return
      }

      const data = await response.json()

      if (!data.success) {
        setModalState('Error', data.error || 'Failed to parse neighbors', false, true)
        return
      }

      const neighbors = data.output
      const notFoundNeighbors: string[] = []
      const existingNeighbors: string[] = []
      let addedCount = 0
      const spacing = 200
      const neighborsPerRow = Math.ceil(Math.sqrt(neighbors.length))

      for (let i = 0; i < neighbors.length; i++) {
        const neighbor = neighbors[i]

        // Check if device already exists on canvas
        const existingDevice = deviceStore.devices.find(
          (d) => d.name.toLowerCase() === neighbor.neighbor.toLowerCase()
        )

        if (existingDevice) {
          existingNeighbors.push(neighbor.neighbor)
          continue
        }

        try {
          // Search for the device in Nautobot by name
          const searchResponse = await makeAuthenticatedRequest(
            `/api/nautobot/devices/search?name=${encodeURIComponent(neighbor.neighbor)}`
          )

          if (!searchResponse.ok) {
            notFoundNeighbors.push(neighbor.neighbor)
            continue
          }

          const searchData = await searchResponse.json()

          if (!searchData || searchData.count === 0) {
            notFoundNeighbors.push(neighbor.neighbor)
            continue
          }

          const nautobotDevice = searchData.devices[0]
          const row = Math.floor(addedCount / neighborsPerRow)
          const col = addedCount % neighborsPerRow
          const offsetX = (col - (neighborsPerRow - 1) / 2) * spacing
          const offsetY = row * spacing + 150

          await deviceStore.createDevice({
            name: nautobotDevice.name,
            device_type: mapNautobotDeviceType(nautobotDevice),
            ip_address: nautobotDevice.primary_ip4?.address?.split('/')[0],
            position_x: device.position_x + offsetX - DEVICE_HALF_SIZE,
            position_y: device.position_y + offsetY,
            properties: JSON.stringify({
              nautobot_id: nautobotDevice.id,
              location: nautobotDevice.location?.name,
              role: nautobotDevice.role?.name,
              status: nautobotDevice.status?.name,
              device_model: nautobotDevice.device_type?.model,
              platform: nautobotDevice.platform?.network_driver,
              platform_id: nautobotDevice.platform?.id,
              device_type_model: nautobotDevice.device_type?.model,
            }),
          })

          addedCount++
        } catch (error) {
          console.error(`Error adding neighbor ${neighbor.neighbor}:`, error)
          notFoundNeighbors.push(neighbor.neighbor)
        }
      }

      let message = `Successfully added ${addedCount} neighbors to canvas.`
      if (existingNeighbors.length > 0) {
        message += `\n\nAlready on canvas (${existingNeighbors.length}): ${existingNeighbors.join(', ')}`
      }
      if (notFoundNeighbors.length > 0) {
        message += `\n\nNot found in Nautobot (${notFoundNeighbors.length}): ${notFoundNeighbors.join(', ')}`
      }

      setModalState('Neighbors Added', message, false, true)
    } catch (error) {
      console.error('Error adding neighbors to canvas:', error)
      setModalState('Error', `Failed to add neighbors: ${error instanceof Error ? error.message : 'Unknown error'}`, false, true)
    }
  }

  // Map Nautobot device type
  const mapNautobotDeviceType = (device: any): Device['device_type'] => {
    const deviceType = device.device_type?.model?.toLowerCase() || ''
    const role = device.role?.name?.toLowerCase() || ''

    if (deviceType.includes('firewall') || role.includes('firewall')) return 'firewall'
    if (deviceType.includes('router') || role.includes('router')) return 'router'
    if (deviceType.includes('switch') || role.includes('switch')) return 'switch'
    if (deviceType.includes('vpn') || role.includes('vpn')) return 'vpn_gateway'

    return 'router'
  }

  // Connect two selected devices
  const connectTwoDevices = async (selectedDevices: Set<number>) => {
    const devices = Array.from(selectedDevices)
      .map((id) => deviceStore.devices.find((d) => d.id === id))
      .filter((d) => d !== undefined) as Device[]

    if (devices.length !== 2) {
      console.error('Exactly 2 devices must be selected to connect')
      return
    }

    const [device1, device2] = devices

    // Check if connection already exists
    const existingConnection = deviceStore.connections.find(
      (c) =>
        (c.source_device_id === device1.id && c.target_device_id === device2.id) ||
        (c.source_device_id === device2.id && c.target_device_id === device1.id)
    )

    if (existingConnection) {
      console.log('Connection already exists between these devices')
      return
    }

    // Create connection
    await deviceStore.createConnection({
      source_device_id: device1.id,
      target_device_id: device2.id,
      connection_type: 'ethernet',
      properties: JSON.stringify({}),
    })

    console.log(`✅ Connected ${device1.name} to ${device2.name}`)
  }

  return {
    showNeighbors,
    addNeighborsToCanvas,
    connectTwoDevices,
  }
}
