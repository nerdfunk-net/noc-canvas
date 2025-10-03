import { useDevicesStore, type Device } from '@/stores/devices'
import { type NautobotDevice, nautobotApi, makeAuthenticatedRequest } from '@/services/api'

// Type definitions for neighbor discovery results
export interface NeighborDevice {
  name: string
  ipAddress?: string
  role?: string
  location?: string
  status?: string
  deviceId?: number // Canvas device ID for connection creation
  hasConnection?: boolean // Whether a connection already exists
}

export interface NeighborDiscoveryResult {
  success: boolean
  error?: string
  addedDevices: NeighborDevice[]
  skippedDevices: NeighborDevice[]
  notFoundDevices: string[]
  sourceDeviceId?: number // ID of the source device for connection creation
}

/**
 * Composable for discovering and adding network neighbors to the canvas
 * Supports multiple discovery protocols: CDP, MAC, Static routes, OSPF, BGP
 */
export function useNeighborDiscovery() {
  const deviceStore = useDevicesStore()

  /**
   * Helper: Get Nautobot ID from device properties
   */
  const getNautobotId = (device: Device): string | null => {
    try {
      const deviceProps = device.properties ? JSON.parse(device.properties) : {}
      return deviceProps.nautobot_id || null
    } catch (error) {
      console.error('Error parsing device properties:', error)
      return null
    }
  }

  /**
   * Helper: Map Nautobot device type to canvas device type
   */
  const mapNautobotDeviceType = (nautobotDevice: NautobotDevice): Device['device_type'] => {
    const role = nautobotDevice.role?.name?.toLowerCase() || ''
    const deviceType = nautobotDevice.device_type?.model?.toLowerCase() || ''

    if (role.includes('router') || deviceType.includes('router')) return 'router'
    if (role.includes('switch') || deviceType.includes('switch')) return 'switch'
    if (role.includes('firewall') || deviceType.includes('firewall')) return 'firewall'
    if (role.includes('vpn') || deviceType.includes('vpn')) return 'vpn_gateway'
    return 'router'
  }

  /**
   * Helper: Find a device in inventory by name (case-insensitive, partial match)
   */
  const findDeviceInInventory = (neighborName: string, inventory: any[]): any | null => {
    return inventory.find((d: any) =>
      d.name.toLowerCase() === neighborName.toLowerCase() ||
      d.name.toLowerCase().startsWith(neighborName.toLowerCase()) ||
      neighborName.toLowerCase().startsWith(d.name.toLowerCase())
    )
  }

  /**
   * Helper: Check if device already exists on canvas
   */
  const isDeviceOnCanvas = (nautobotDevice: any): boolean => {
    let existingDevice = deviceStore.findDeviceByName(nautobotDevice.name)
    if (!existingDevice) {
      existingDevice = deviceStore.findDeviceByNautobotId(nautobotDevice.id)
    }
    return !!existingDevice
  }

  /**
   * Helper: Calculate position for neighbor in a grid layout around source device
   */
  const calculateNeighborPosition = (
    sourceDevice: Device,
    index: number,
    totalNeighbors: number
  ): { x: number; y: number } => {
    const spacing = 150
    const neighborsPerRow = Math.ceil(Math.sqrt(totalNeighbors))
    const row = Math.floor(index / neighborsPerRow)
    const col = index % neighborsPerRow
    const offsetX = (col - (neighborsPerRow - 1) / 2) * spacing
    const offsetY = (row + 1) * spacing // Place below the source device

    return {
      x: sourceDevice.position_x + offsetX,
      y: sourceDevice.position_y + offsetY,
    }
  }

  /**
   * Helper: Add a device from Nautobot inventory to the canvas
   */
  const addDeviceToCanvas = async (
    nautobotDevice: NautobotDevice,
    position: { x: number; y: number }
  ): Promise<Device> => {
    return await deviceStore.createDevice({
      name: nautobotDevice.name,
      device_type: mapNautobotDeviceType(nautobotDevice),
      ip_address: nautobotDevice.primary_ip4?.address?.split('/')[0],
      position_x: position.x,
      position_y: position.y,
      properties: JSON.stringify({
        nautobot_id: nautobotDevice.id,
        location: nautobotDevice.location?.name,
        role: nautobotDevice.role?.name,
        status: nautobotDevice.status?.name,
        device_model: nautobotDevice.device_type?.model,
        platform: nautobotDevice.platform?.network_driver,
        device_type_model: nautobotDevice.device_type?.model,
      }),
    })
  }

  /**
   * Helper: Check if a connection exists between two devices
   */
  const connectionExists = (device1Id: number, device2Id: number): boolean => {
    return deviceStore.connections.some(conn =>
      (conn.source_device_id === device1Id && conn.target_device_id === device2Id) ||
      (conn.source_device_id === device2Id && conn.target_device_id === device1Id)
    )
  }

  /**
   * Helper: Create a connection between two devices
   */
  const createConnection = (sourceDevice: Device, targetDevice: Device): void => {
    try {
      deviceStore.createConnection({
        source_device_id: sourceDevice.id,
        target_device_id: targetDevice.id,
        connection_type: 'ethernet',
      })
      console.log(`🔗 Created connection: ${sourceDevice.name} <-> ${targetDevice.name}`)
    } catch (error) {
      console.error(`❌ Failed to create connection to ${targetDevice.name}:`, error)
    }
  }

  /**
   * Add CDP (Cisco Discovery Protocol) neighbors to the canvas
   * Returns structured result data for display in modal
   */
  const addCdpNeighbors = async (device: Device): Promise<NeighborDiscoveryResult | null> => {
    console.log('➕ Adding CDP neighbors to canvas for device:', device.name)

    const result: NeighborDiscoveryResult = {
      success: false,
      addedDevices: [],
      skippedDevices: [],
      notFoundDevices: [],
      sourceDeviceId: device.id
    }

    try {
      const nautobotId = getNautobotId(device)
      if (!nautobotId) {
        result.error = 'Device does not have a Nautobot ID'
        return result
      }

      // Call the CDP neighbors endpoint with TextFSM parsing
      const response = await makeAuthenticatedRequest(
        `/api/devices/${nautobotId}/cdp-neighbors?use_textfsm=true`
      )

      if (!response.ok) {
        const errorData = await response.json()
        result.error = errorData.detail || 'Failed to retrieve CDP neighbors'
        return result
      }

      const data = await response.json()

      if (!data.success) {
        result.error = data.error || 'Failed to retrieve CDP neighbors'
        return result
      }

      // Check if output is an array (parsed data)
      if (!Array.isArray(data.output)) {
        result.error = 'Expected parsed neighbor data but received raw output'
        return result
      }

      const neighbors = data.output
      console.log('📋 Found CDP neighbors:', neighbors)

      if (neighbors.length === 0) {
        result.success = true
        return result
      }

      // Get all devices from Nautobot for matching
      const nautobotDevices = await nautobotApi.getAllDevices()
      console.log('📦 Inventory devices loaded:', nautobotDevices.devices.length)

      let addedCount = 0

      for (let i = 0; i < neighbors.length; i++) {
        const neighbor = neighbors[i]
        const neighborName = neighbor.neighbor_name || neighbor.destination_host || neighbor.device_id

        if (!neighborName) {
          console.warn('⚠️ Neighbor has no name, skipping:', neighbor)
          continue
        }

        console.log(`🔍 Searching for neighbor: ${neighborName}`)

        // Try to find the neighbor in the inventory
        const neighborDevice = findDeviceInInventory(neighborName, nautobotDevices.devices)

        if (neighborDevice) {
          console.log(`✅ Found neighbor in inventory: ${neighborDevice.name}`)

          // Check if device already exists on canvas
          if (isDeviceOnCanvas(neighborDevice)) {
            console.log(`⚠️ Neighbor already on canvas: ${neighborDevice.name}`)

            // Find the canvas device to check for connection
            let canvasDevice = deviceStore.findDeviceByName(neighborDevice.name)
            if (!canvasDevice) {
              canvasDevice = deviceStore.findDeviceByNautobotId(neighborDevice.id)
            }

            const hasConnection = canvasDevice ? connectionExists(device.id, canvasDevice.id) : false

            result.skippedDevices.push({
              name: neighborDevice.name,
              ipAddress: neighborDevice.primary_ip4?.address || neighborDevice.primary_ip6?.address,
              status: 'Already on canvas',
              deviceId: canvasDevice?.id,
              hasConnection
            })
            continue
          }

          // Calculate position in grid around the source device
          const position = calculateNeighborPosition(device, addedCount, neighbors.length)

          // Add neighbor to canvas
          const newDevice = await addDeviceToCanvas(neighborDevice, position)

          // Create connection between source device and neighbor
          createConnection(device, newDevice)

          addedCount++
          console.log(`✅ Added neighbor to canvas: ${neighborDevice.name}`)

          result.addedDevices.push({
            name: neighborDevice.name,
            ipAddress: neighborDevice.primary_ip4?.address || neighborDevice.primary_ip6?.address,
            role: neighborDevice.device_role?.display || neighborDevice.device_role?.name,
            location: neighborDevice.site?.display || neighborDevice.site?.name
          })
        } else {
          console.log(`❌ Neighbor not found in inventory: ${neighborName}`)
          result.notFoundDevices.push(neighborName)
        }
      }

      result.success = true
      return result

    } catch (error) {
      console.error('❌ Error adding CDP neighbors to canvas:', error)
      result.error = error instanceof Error ? error.message : 'Unknown error occurred'
      return result
    }
  }

  /**
   * Add ARP table neighbors to the canvas
   * Returns structured result data for display in modal
   */
  const addArpNeighbors = async (device: Device): Promise<NeighborDiscoveryResult | null> => {
    console.log('➕ Adding ARP neighbors to canvas for device:', device.name)

    const result: NeighborDiscoveryResult = {
      success: false,
      addedDevices: [],
      skippedDevices: [],
      notFoundDevices: [],
      sourceDeviceId: device.id
    }

    try {
      const nautobotId = getNautobotId(device)
      if (!nautobotId) {
        result.error = 'Device does not have a Nautobot ID'
        return result
      }

      // Call the ARP table endpoint with TextFSM parsing
      const response = await makeAuthenticatedRequest(
        `/api/devices/${nautobotId}/ip-arp?use_textfsm=true`
      )

      if (!response.ok) {
        const errorData = await response.json()
        result.error = errorData.detail || 'Failed to retrieve ARP table'
        return result
      }

      const data = await response.json()

      if (!data.success) {
        result.error = data.error || 'Failed to retrieve ARP table'
        return result
      }

      // Check if output is an array (parsed data)
      if (!Array.isArray(data.output)) {
        result.error = 'Expected parsed ARP data but received raw output'
        return result
      }

      const arpEntries = data.output
      console.log('📋 Found ARP entries:', arpEntries)

      if (arpEntries.length === 0) {
        result.success = true
        return result
      }

      // Get all devices from Nautobot for matching
      const nautobotDevices = await nautobotApi.getAllDevices()
      console.log('📦 Inventory devices loaded:', nautobotDevices.devices.length)

      let addedCount = 0

      for (let i = 0; i < arpEntries.length; i++) {
        const arpEntry = arpEntries[i]
        const ipAddress = arpEntry.ip_address

        if (!ipAddress) {
          console.warn('⚠️ ARP entry has no IP address, skipping:', arpEntry)
          continue
        }

        console.log(`🔍 Searching for device with IP: ${ipAddress}`)

        // First, try to find the device in loaded inventory by IP
        let neighborDevice = nautobotDevices.devices.find((d: any) => {
          const primaryIp = d.primary_ip4?.address || d.primary_ip6?.address
          if (!primaryIp) return false

          // Extract IP without CIDR notation
          const deviceIp = primaryIp.split('/')[0]
          return deviceIp === ipAddress
        })

        // If not found in inventory, try to fetch from Nautobot by IP
        if (!neighborDevice) {
          console.log(`🔎 Device not in cached inventory, searching Nautobot for IP: ${ipAddress}`)

          try {
            const searchResponse = await nautobotApi.searchDevices(ipAddress, 'ip_address')

            if (searchResponse.devices && searchResponse.devices.length > 0) {
              neighborDevice = searchResponse.devices[0]
              console.log(`✅ Found device in Nautobot: ${neighborDevice.name}`)
            }
          } catch (error) {
            console.warn(`⚠️ Failed to search Nautobot for IP ${ipAddress}:`, error)
          }
        }

        if (neighborDevice) {
          console.log(`✅ Found neighbor in inventory: ${neighborDevice.name}`)

          // Check if device already exists on canvas
          if (isDeviceOnCanvas(neighborDevice)) {
            console.log(`⚠️ Neighbor already on canvas: ${neighborDevice.name}`)

            // Find the canvas device to check for connection
            let canvasDevice = deviceStore.findDeviceByName(neighborDevice.name)
            if (!canvasDevice) {
              canvasDevice = deviceStore.findDeviceByNautobotId(neighborDevice.id)
            }

            const hasConnection = canvasDevice ? connectionExists(device.id, canvasDevice.id) : false

            result.skippedDevices.push({
              name: neighborDevice.name,
              ipAddress: neighborDevice.primary_ip4?.address || neighborDevice.primary_ip6?.address,
              status: 'Already on canvas',
              deviceId: canvasDevice?.id,
              hasConnection
            })
            continue
          }

          // Calculate position in grid around the source device
          const position = calculateNeighborPosition(device, addedCount, arpEntries.length)

          // Add neighbor to canvas
          const newDevice = await addDeviceToCanvas(neighborDevice, position)

          // Create connection between source device and neighbor
          createConnection(device, newDevice)

          addedCount++
          console.log(`✅ Added neighbor to canvas: ${neighborDevice.name}`)

          result.addedDevices.push({
            name: neighborDevice.name,
            ipAddress: neighborDevice.primary_ip4?.address || neighborDevice.primary_ip6?.address,
            role: neighborDevice.device_role?.display || neighborDevice.device_role?.name,
            location: neighborDevice.site?.display || neighborDevice.site?.name
          })
        } else {
          console.log(`❌ Device with IP ${ipAddress} not found in inventory`)
          result.notFoundDevices.push(ipAddress)
        }
      }

      result.success = true
      return result

    } catch (error) {
      console.error('❌ Error adding ARP neighbors to canvas:', error)
      result.error = error instanceof Error ? error.message : 'Unknown error occurred'
      return result
    }
  }

  /**
   * Add MAC address table neighbors to the canvas
   * TODO: Implement when MAC table API endpoint is available
   */
  const addMacNeighbors = async (device: Device): Promise<void> => {
    console.log('➕ Adding MAC neighbors to canvas for device:', device.name)
    alert('MAC neighbor discovery is not yet implemented. Coming soon!')
  }

  /**
   * Add static route neighbors to the canvas
   * Returns structured result data for display in modal
   */
  const addStaticNeighbors = async (device: Device): Promise<NeighborDiscoveryResult | null> => {
    console.log('➕ Adding static route neighbors to canvas for device:', device.name)

    const result: NeighborDiscoveryResult = {
      success: false,
      addedDevices: [],
      skippedDevices: [],
      notFoundDevices: [],
      sourceDeviceId: device.id
    }

    try {
      const nautobotId = getNautobotId(device)
      if (!nautobotId) {
        result.error = 'Device does not have a Nautobot ID'
        return result
      }

      // Call the static routes endpoint with TextFSM parsing
      const response = await makeAuthenticatedRequest(
        `/api/devices/${nautobotId}/ip-route/static?use_textfsm=true`
      )

      if (!response.ok) {
        const errorData = await response.json()
        result.error = errorData.detail || 'Failed to retrieve static routes'
        return result
      }

      const data = await response.json()

      if (!data.success) {
        result.error = data.error || 'Failed to retrieve static routes'
        return result
      }

      // Check if output is an array (parsed data)
      if (!Array.isArray(data.output)) {
        result.error = 'Expected parsed route data but received raw output'
        return result
      }

      const routes = data.output
      console.log('📋 Found static routes:', routes)

      if (routes.length === 0) {
        result.success = true
        return result
      }

      // Get all devices from Nautobot for matching
      const nautobotDevices = await nautobotApi.getAllDevices()
      console.log('📦 Inventory devices loaded:', nautobotDevices.devices.length)

      // Extract unique next-hop IPs from static routes
      const nextHopIps = new Set<string>()
      routes.forEach((route: any) => {
        if (route.nexthop_ip && route.nexthop_ip !== '0.0.0.0') {
          // Remove subnet mask if present
          const ip = route.nexthop_ip.split('/')[0]
          nextHopIps.add(ip)
        }
      })

      console.log('🔍 Unique static route next-hop IPs:', Array.from(nextHopIps))

      let addedCount = 0

      for (const nextHopIp of nextHopIps) {
        console.log(`🔍 Searching for device with IP: ${nextHopIp}`)

        // Find device by IP address in inventory
        const neighborDevice = nautobotDevices.devices.find((d: any) => {
          const primaryIp = d.primary_ip4?.address || d.primary_ip6?.address
          if (!primaryIp) return false
          
          // Remove subnet mask from inventory IP for comparison
          const inventoryIp = primaryIp.split('/')[0]
          return inventoryIp === nextHopIp
        })

        if (neighborDevice) {
          console.log(`✅ Found neighbor in inventory: ${neighborDevice.name}`)

          // Check if device already exists on canvas
          if (isDeviceOnCanvas(neighborDevice)) {
            console.log(`⚠️ Neighbor already on canvas: ${neighborDevice.name}`)

            // Find the canvas device to check for connection
            let canvasDevice = deviceStore.findDeviceByName(neighborDevice.name)
            if (!canvasDevice) {
              canvasDevice = deviceStore.findDeviceByNautobotId(neighborDevice.id)
            }

            const hasConnection = canvasDevice ? connectionExists(device.id, canvasDevice.id) : false

            result.skippedDevices.push({
              name: neighborDevice.name,
              ipAddress: neighborDevice.primary_ip4?.address,
              status: 'Already on canvas',
              deviceId: canvasDevice?.id,
              hasConnection
            })
            continue
          }

          // Calculate position in grid around the source device
          const position = calculateNeighborPosition(device, addedCount, Array.from(nextHopIps).length)

          // Add neighbor to canvas
          const newDevice = await addDeviceToCanvas(neighborDevice, position)

          // Create connection between source device and neighbor
          createConnection(device, newDevice)

          addedCount++
          console.log(`✅ Added static route neighbor to canvas: ${neighborDevice.name}`)

          result.addedDevices.push({
            name: neighborDevice.name,
            ipAddress: neighborDevice.primary_ip4?.address,
            role: neighborDevice.role?.name,
            location: neighborDevice.location?.name
          })
        } else {
          console.log(`❌ Neighbor not found in inventory for IP: ${nextHopIp}`)
          
          // Try to search for the IP address in Nautobot
          console.log(`🔍 Searching Nautobot for IP: ${nextHopIp}`)
          try {
            const nautobotSearchResponse = await nautobotApi.getDevices({
              filter_type: 'ip_address',
              filter_value: nextHopIp,
              disable_cache: true
            })

            if (nautobotSearchResponse.devices.length > 0) {
              const foundDevice = nautobotSearchResponse.devices[0]
              console.log(`✅ Found device in Nautobot: ${foundDevice.name}`)
              
              // Check if this device is in our inventory (by name)
              const deviceInInventory = nautobotDevices.devices.find((d: any) => 
                d.id === foundDevice.id || d.name === foundDevice.name
              )
              
              if (!deviceInInventory) {
                console.log(`⚠️ Device ${foundDevice.name} found in Nautobot but not in inventory`)
                result.notFoundDevices.push(
                  `${nextHopIp} - Found device "${foundDevice.name}" in Nautobot but not in inventory`
                )
              } else {
                console.log(`✅ Device ${foundDevice.name} is in inventory, attempting to add to canvas`)
                
                // Check if device already exists on canvas
                if (isDeviceOnCanvas(foundDevice)) {
                  console.log(`⚠️ Device already on canvas: ${foundDevice.name}`)
                  result.skippedDevices.push({
                    name: foundDevice.name,
                    ipAddress: foundDevice.primary_ip4?.address,
                    status: 'Already on canvas'
                  })
                  continue
                }

                // Calculate position in grid around the source device
                const position = calculateNeighborPosition(device, addedCount, Array.from(nextHopIps).length)

                // Add device to canvas
                const newDevice = await addDeviceToCanvas(foundDevice, position)

                // Create connection between source device and neighbor
                createConnection(device, newDevice)

                addedCount++
                console.log(`✅ Added static route neighbor to canvas: ${foundDevice.name}`)

                result.addedDevices.push({
                  name: foundDevice.name,
                  ipAddress: foundDevice.primary_ip4?.address,
                  role: foundDevice.role?.name,
                  location: foundDevice.location?.name
                })
              }
            } else {
              console.log(`❌ IP address ${nextHopIp} not found in Nautobot`)
              result.notFoundDevices.push(`${nextHopIp} - Not found in Nautobot`)
            }
          } catch (error) {
            console.error(`❌ Error searching Nautobot for IP ${nextHopIp}:`, error)
            result.notFoundDevices.push(`${nextHopIp} - Error searching Nautobot: ${error}`)
          }
        }
      }

      result.success = true
      return result

    } catch (error) {
      console.error('❌ Error adding static route neighbors to canvas:', error)
      result.error = error instanceof Error ? error.message : 'Unknown error occurred'
      return result
    }
  }

  /**
   * Add OSPF neighbors to the canvas
   * Returns structured result data for display in modal
   */
  const addOspfNeighbors = async (device: Device): Promise<NeighborDiscoveryResult | null> => {
    console.log('➕ Adding OSPF neighbors to canvas for device:', device.name)

    const result: NeighborDiscoveryResult = {
      success: false,
      addedDevices: [],
      skippedDevices: [],
      notFoundDevices: [],
      sourceDeviceId: device.id
    }

    try {
      const nautobotId = getNautobotId(device)
      if (!nautobotId) {
        result.error = 'Device does not have a Nautobot ID'
        return result
      }

      // Call the OSPF routes endpoint with TextFSM parsing
      const response = await makeAuthenticatedRequest(
        `/api/devices/${nautobotId}/ip-route/ospf?use_textfsm=true`
      )

      if (!response.ok) {
        const errorData = await response.json()
        result.error = errorData.detail || 'Failed to retrieve OSPF routes'
        return result
      }

      const data = await response.json()

      if (!data.success) {
        result.error = data.error || 'Failed to retrieve OSPF routes'
        return result
      }

      // Check if output is an array (parsed data)
      if (!Array.isArray(data.output)) {
        result.error = 'Expected parsed route data but received raw output'
        return result
      }

      const routes = data.output
      console.log('📋 Found OSPF routes:', routes)

      if (routes.length === 0) {
        result.success = true
        return result
      }

      // Get all devices from Nautobot for matching
      const nautobotDevices = await nautobotApi.getAllDevices()
      console.log('📦 Inventory devices loaded:', nautobotDevices.devices.length)

      // Extract unique next-hop IPs from OSPF routes
      const nextHopIps = new Set<string>()
      routes.forEach((route: any) => {
        if (route.nexthop_ip && route.nexthop_ip !== '0.0.0.0') {
          // Remove subnet mask if present
          const ip = route.nexthop_ip.split('/')[0]
          nextHopIps.add(ip)
        }
      })

      console.log('🔍 Unique OSPF next-hop IPs:', Array.from(nextHopIps))

      let addedCount = 0

      for (const nextHopIp of nextHopIps) {
        console.log(`🔍 Searching for device with IP: ${nextHopIp}`)

        // Find device by IP address in inventory
        const neighborDevice = nautobotDevices.devices.find((d: any) => {
          const primaryIp = d.primary_ip4?.address || d.primary_ip6?.address
          if (!primaryIp) return false
          
          // Remove subnet mask from inventory IP for comparison
          const inventoryIp = primaryIp.split('/')[0]
          return inventoryIp === nextHopIp
        })

        if (neighborDevice) {
          console.log(`✅ Found neighbor in inventory: ${neighborDevice.name}`)

          // Check if device already exists on canvas
          if (isDeviceOnCanvas(neighborDevice)) {
            console.log(`⚠️ Neighbor already on canvas: ${neighborDevice.name}`)

            // Find the canvas device to check for connection
            let canvasDevice = deviceStore.findDeviceByName(neighborDevice.name)
            if (!canvasDevice) {
              canvasDevice = deviceStore.findDeviceByNautobotId(neighborDevice.id)
            }

            const hasConnection = canvasDevice ? connectionExists(device.id, canvasDevice.id) : false

            result.skippedDevices.push({
              name: neighborDevice.name,
              ipAddress: neighborDevice.primary_ip4?.address,
              status: 'Already on canvas',
              deviceId: canvasDevice?.id,
              hasConnection
            })
            continue
          }

          // Calculate position in grid around the source device
          const position = calculateNeighborPosition(device, addedCount, Array.from(nextHopIps).length)

          // Add neighbor to canvas
          const newDevice = await addDeviceToCanvas(neighborDevice, position)

          // Create connection between source device and neighbor
          createConnection(device, newDevice)

          addedCount++
          console.log(`✅ Added OSPF neighbor to canvas: ${neighborDevice.name}`)

          result.addedDevices.push({
            name: neighborDevice.name,
            ipAddress: neighborDevice.primary_ip4?.address,
            role: neighborDevice.role?.name,
            location: neighborDevice.location?.name
          })
        } else {
          console.log(`❌ Neighbor not found in inventory for IP: ${nextHopIp}`)
          
          // Try to search for the IP address in Nautobot
          console.log(`🔍 Searching Nautobot for IP: ${nextHopIp}`)
          try {
            const nautobotSearchResponse = await nautobotApi.getDevices({
              filter_type: 'ip_address',
              filter_value: nextHopIp,
              disable_cache: true
            })

            if (nautobotSearchResponse.devices.length > 0) {
              const foundDevice = nautobotSearchResponse.devices[0]
              console.log(`✅ Found device in Nautobot: ${foundDevice.name}`)
              
              // Check if this device is in our inventory (by name)
              const deviceInInventory = nautobotDevices.devices.find((d: any) => 
                d.id === foundDevice.id || d.name === foundDevice.name
              )
              
              if (!deviceInInventory) {
                console.log(`⚠️ Device ${foundDevice.name} found in Nautobot but not in inventory`)
                result.notFoundDevices.push(
                  `${nextHopIp} - Found device "${foundDevice.name}" in Nautobot but not in inventory`
                )
              } else {
                console.log(`✅ Device ${foundDevice.name} is in inventory, attempting to add to canvas`)
                
                // Check if device already exists on canvas
                if (isDeviceOnCanvas(foundDevice)) {
                  console.log(`⚠️ Device already on canvas: ${foundDevice.name}`)
                  result.skippedDevices.push({
                    name: foundDevice.name,
                    ipAddress: foundDevice.primary_ip4?.address,
                    status: 'Already on canvas'
                  })
                  continue
                }

                // Calculate position in grid around the source device
                const position = calculateNeighborPosition(device, addedCount, Array.from(nextHopIps).length)

                // Add device to canvas
                const newDevice = await addDeviceToCanvas(foundDevice, position)

                // Create connection between source device and neighbor
                createConnection(device, newDevice)

                addedCount++
                console.log(`✅ Added OSPF neighbor to canvas: ${foundDevice.name}`)

                result.addedDevices.push({
                  name: foundDevice.name,
                  ipAddress: foundDevice.primary_ip4?.address,
                  role: foundDevice.role?.name,
                  location: foundDevice.location?.name
                })
              }
            } else {
              console.log(`❌ IP address ${nextHopIp} not found in Nautobot`)
              result.notFoundDevices.push(`${nextHopIp} - Not found in Nautobot`)
            }
          } catch (error) {
            console.error(`❌ Error searching Nautobot for IP ${nextHopIp}:`, error)
            result.notFoundDevices.push(`${nextHopIp} - Error searching Nautobot: ${error}`)
          }
        }
      }

      result.success = true
      return result

    } catch (error) {
      console.error('❌ Error adding OSPF neighbors to canvas:', error)
      result.error = error instanceof Error ? error.message : 'Unknown error occurred'
      return result
    }
  }

  /**
   * Add BGP neighbors to the canvas
   * TODO: Implement when BGP API endpoint is available
   */
  const addBgpNeighbors = async (device: Device): Promise<void> => {
    console.log('➕ Adding BGP neighbors to canvas for device:', device.name)
    alert('BGP neighbor discovery is not yet implemented. Coming soon!')
  }

  return {
    addCdpNeighbors,
    addArpNeighbors,
    addMacNeighbors,
    addStaticNeighbors,
    addOspfNeighbors,
    addBgpNeighbors,
  }
}
