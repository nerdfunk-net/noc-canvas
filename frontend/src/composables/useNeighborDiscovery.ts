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
   * Configuration interface for discovery protocols
   */
  interface DiscoveryConfig {
    endpoint: string  // API endpoint path (e.g., 'cdp-neighbors', 'ip-arp')
    displayName: string  // Protocol name for logging (e.g., 'CDP', 'ARP')
    extractIdentifier: (entry: any) => string | null  // Extract device identifier from parsed data
    searchByIp?: boolean  // If true, search Nautobot by IP when not in cache
    preprocessEntries?: (entries: any[]) => string[]  // Custom processing to extract unique identifiers from entries
  }

  /**
   * Generic neighbor discovery function
   * Handles common logic for all discovery protocols
   */
  const discoverNeighbors = async (
    device: Device,
    config: DiscoveryConfig
  ): Promise<NeighborDiscoveryResult | null> => {
    console.log(`➕ Adding ${config.displayName} neighbors to canvas for device:`, device.name)

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

      // Call the discovery endpoint with TextFSM parsing
      const response = await makeAuthenticatedRequest(
        `/api/devices/${nautobotId}/${config.endpoint}?use_textfsm=true`
      )

      if (!response.ok) {
        const errorData = await response.json()
        result.error = errorData.detail || `Failed to retrieve ${config.displayName} data`
        return result
      }

      const data = await response.json()

      if (!data.success) {
        result.error = data.error || `Failed to retrieve ${config.displayName} data`
        return result
      }

      // Check if output is an array (parsed data)
      if (!Array.isArray(data.output)) {
        result.error = `Expected parsed ${config.displayName} data but received raw output`
        return result
      }

      const entries = data.output
      console.log(`📋 Found ${config.displayName} entries:`, entries.length)

      if (entries.length === 0) {
        result.success = true
        return result
      }

      // Get all devices from Nautobot for matching
      const nautobotDevices = await nautobotApi.getAllDevices()
      console.log('📦 Inventory devices loaded:', nautobotDevices.devices.length)

      // Use preprocessor if provided, otherwise iterate through all entries
      const identifiers = config.preprocessEntries
        ? config.preprocessEntries(entries)
        : entries.map(entry => config.extractIdentifier(entry)).filter(id => id !== null) as string[]

      console.log(`🔍 Processing ${identifiers.length} unique identifiers`)

      let addedCount = 0

      for (const identifier of identifiers) {
        if (!identifier) {
          console.warn(`⚠️ ${config.displayName} entry has no identifier, skipping`)
          continue
        }

        console.log(`🔍 Searching for: ${identifier}`)

        let neighborDevice: any = null

        // Search by IP if configured
        if (config.searchByIp) {
          // First, try to find in cached inventory by IP
          neighborDevice = nautobotDevices.devices.find((d: any) => {
            const primaryIp = d.primary_ip4?.address || d.primary_ip6?.address
            if (!primaryIp) return false
            const deviceIp = primaryIp.split('/')[0]
            return deviceIp === identifier
          })

          // If not found, search Nautobot by IP
          if (!neighborDevice) {
            console.log(`🔎 Device not in cached inventory, searching Nautobot for IP: ${identifier}`)
            try {
              const searchResponse = await nautobotApi.searchDevices(identifier, 'ip_address')
              if (searchResponse.devices && searchResponse.devices.length > 0) {
                neighborDevice = searchResponse.devices[0]
                console.log(`✅ Found device in Nautobot: ${neighborDevice.name}`)
              }
            } catch (error) {
              console.warn(`⚠️ Failed to search Nautobot for IP ${identifier}:`, error)
            }
          }
        } else {
          // Search by name
          neighborDevice = findDeviceInInventory(identifier, nautobotDevices.devices)
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
          const position = calculateNeighborPosition(device, addedCount, identifiers.length)

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
          console.log(`❌ Device ${identifier} not found in inventory`)
          result.notFoundDevices.push(identifier)
        }
      }

      result.success = true
      return result

    } catch (error) {
      console.error(`❌ Error adding ${config.displayName} neighbors to canvas:`, error)
      result.error = error instanceof Error ? error.message : 'Unknown error occurred'
      return result
    }
  }

  /**
   * Add CDP (Cisco Discovery Protocol) neighbors to the canvas
   * Returns structured result data for display in modal
   */
  const addCdpNeighbors = async (device: Device): Promise<NeighborDiscoveryResult | null> => {
    return discoverNeighbors(device, {
      endpoint: 'cdp-neighbors',
      displayName: 'CDP',
      extractIdentifier: (entry) => entry.neighbor_name || entry.destination_host || entry.device_id,
      searchByIp: false
    })
  }

  /**
   * Add ARP table neighbors to the canvas
   * Returns structured result data for display in modal
   */
  const addArpNeighbors = async (device: Device): Promise<NeighborDiscoveryResult | null> => {
    return discoverNeighbors(device, {
      endpoint: 'ip-arp',
      displayName: 'ARP',
      extractIdentifier: (entry) => entry.ip_address,
      searchByIp: true
    })
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
    return discoverNeighbors(device, {
      endpoint: 'ip-route/static',
      displayName: 'Static Route',
      extractIdentifier: (entry) => entry.nexthop_ip,
      searchByIp: true,
      preprocessEntries: (entries) => {
        // Extract unique next-hop IPs, filtering out 0.0.0.0
        const nextHopIps = new Set<string>()
        entries.forEach((route: any) => {
          if (route.nexthop_ip && route.nexthop_ip !== '0.0.0.0') {
            const ip = route.nexthop_ip.split('/')[0]
            nextHopIps.add(ip)
          }
        })
        return Array.from(nextHopIps)
      }
    })
  }

  /**
   * Add OSPF neighbors to the canvas
   * Returns structured result data for display in modal
   */
  const addOspfNeighbors = async (device: Device): Promise<NeighborDiscoveryResult | null> => {
    return discoverNeighbors(device, {
      endpoint: 'ip-route/ospf',
      displayName: 'OSPF',
      extractIdentifier: (entry) => entry.nexthop_ip,
      searchByIp: true,
      preprocessEntries: (entries) => {
        // Extract unique next-hop IPs, filtering out 0.0.0.0
        const nextHopIps = new Set<string>()
        entries.forEach((route: any) => {
          if (route.nexthop_ip && route.nexthop_ip !== '0.0.0.0') {
            const ip = route.nexthop_ip.split('/')[0]
            nextHopIps.add(ip)
          }
        })
        return Array.from(nextHopIps)
      }
    })
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
