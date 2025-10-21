import { computed, type ComputedRef, type Ref } from 'vue'
import type { Device } from '@/stores/devices'
import type { ContextMenuItem, ContextMenuTargetType } from './useContextMenu'

interface ContextMenuItemsOptions {
  contextMenu: {
    show: boolean
    x: number
    y: number
    target: Device | null
    targetType: ContextMenuTargetType
  }
  hideContextMenu: () => void
  selectedDevices: Ref<Set<number>>
  selectedShapes: Ref<Set<string>>
  layerVisibility: Ref<{
    devices: boolean
    layer2: boolean
    layer3: boolean
    background: boolean
  }>
  deviceStore: any
  // Shape operations
  openShapeColorModal: (shape: any) => void
  alignShapesHorizontally: () => void
  alignShapesVertically: () => void
  deleteShape: (shape: any) => void
  deleteMultiShapes: () => void
  // Connection operations
  showConnectionInfo: (connectionId: any) => void
  showConnectionStatus: (connectionId: any) => void
  showConnectionStats: (connectionId: any) => void
  toggleConnectionRoutingStyle: (connectionId: any) => void
  clearConnectionWaypoints: (connectionId: any) => void
  deleteConnection: (connectionId: any) => void
  // Canvas operations
  fitToScreen: (container: HTMLElement | null) => void
  resetView: () => void
  openTopologyDiscovery: () => void
  openTopologyBuilder: () => void
  loadCanvas: () => void
  saveCanvas: () => void
  saveCanvasAs: () => void
  clearCanvas: () => void
  // Multi-device operations
  showMultiDeviceConfig: () => void
  showMultiDeviceChanges: () => void
  showMultiDeviceNeighbors: () => void
  addMultiDeviceNeighborsToCanvas: () => void
  connectTwoDevices: () => void
  analyzeMultiDevices: () => void
  alignDevicesHorizontally: () => void
  alignDevicesVertically: () => void
  deleteMultiDevices: () => void
  // Single device operations
  showDeviceOverview: (device: Device) => void
  showSSHTerminal: (device: Device) => void
  openSSHTerminalInWindow: (device: Device) => void
  showDeviceRunningConfig: (device: Device) => void
  showDeviceStartupConfig: (device: Device) => void
  showDeviceChanges: (device: Device) => void
  showDeviceInterfaces: (device: Device, type: string) => void
  executeCommand: (device: Device, command: any) => void
  reloadCommands: () => Promise<void>
  showNeighbors: (device: Device) => void
  addCdpNeighbors: (device: Device) => void
  addMacNeighbors: (device: Device) => void
  addArpNeighbors: (device: Device) => void
  addStaticNeighbors: (device: Device) => void
  addOspfNeighbors: (device: Device) => void
  addBgpNeighbors: (device: Device) => void
  createBaseline: (device: Device) => void
  createSnapshot: (device: Device) => void
  manageSnapshots: (device: Device) => void
  compareSnapshotToBaseline: (device: Device) => void
  manageConnectionPorts: (device: Device) => void
  deleteDevice: (device: Device) => void
  getDevicePlatform: (properties: any) => string
  getCommandsForPlatform: (platform: string) => any[]
  canvasContainer: Ref<HTMLElement | null>
}

export function useContextMenuItems(options: ContextMenuItemsOptions): ComputedRef<ContextMenuItem[]> {
  const {
    contextMenu,
    hideContextMenu,
    selectedDevices,
    selectedShapes,
    layerVisibility,
    deviceStore,
    canvasContainer,
  } = options

  // Helper for neighbor discovery actions
  const handleNeighborDiscovery = (device: Device, discoveryFn: (device: Device) => void) => {
    hideContextMenu()
    discoveryFn(device)
  }

  return computed(() => {
    console.log('🔵 DEBUG: contextMenuItems computed, targetType:', contextMenu.targetType, 'target:', contextMenu.target)

    // Shape context menu
    if (contextMenu.targetType === 'shape') {
      console.log('🔵 DEBUG: Building shape context menu')
      const items = [
        { icon: '🎨', label: 'Color', action: () => { hideContextMenu(); options.openShapeColorModal(contextMenu.target as any) } },
        {
          icon: '📐',
          label: 'Alignment',
          submenu: [
            { icon: '↔️', label: 'Horizontal', action: () => { hideContextMenu(); options.alignShapesHorizontally() } },
            { icon: '↕️', label: 'Vertical', action: () => { hideContextMenu(); options.alignShapesVertically() } },
          ],
        },
        { icon: '─', label: '─────────', action: () => {}, separator: true } as ContextMenuItem,
        { icon: '🗑️', label: 'Remove', action: () => { hideContextMenu(); options.deleteShape(contextMenu.target as any) } },
      ]
      console.log('🔵 DEBUG: Shape context menu items:', items)
      return items
    }

    // Multi-shape context menu
    if (contextMenu.targetType === 'multi-shape') {
      console.log('🔵 DEBUG: Building multi-shape context menu')
      const selectedCount = selectedShapes.value.size
      const items = [
        {
          icon: '📐',
          label: 'Alignment',
          submenu: [
            { icon: '↔️', label: 'Horizontal', action: () => { hideContextMenu(); options.alignShapesHorizontally() } },
            { icon: '↕️', label: 'Vertical', action: () => { hideContextMenu(); options.alignShapesVertically() } },
          ],
        },
        { icon: '─', label: '─────────', action: () => {}, separator: true } as ContextMenuItem,
        { icon: '🗑️', label: `Remove ${selectedCount} shapes`, action: () => { hideContextMenu(); options.deleteMultiShapes() } },
      ]
      console.log('🔵 DEBUG: Multi-shape context menu items:', items)
      return items
    }

    // Connection context menu
    if (contextMenu.targetType === 'connection') {
      const connection = deviceStore.connections.find((c: any) => c.id === contextMenu.target)
      const currentStyle = connection?.routing_style || 'straight'
      const styleLabel = currentStyle === 'straight' ? 'Orthogonal' : 'Straight'
      const hasWaypoints = connection?.waypoints && connection.waypoints.length > 0

      const items = [
        { icon: '👁️', label: 'Show', action: () => { hideContextMenu(); options.showConnectionInfo(contextMenu.target as any) } },
        { icon: '📊', label: 'Status', action: () => { hideContextMenu(); options.showConnectionStatus(contextMenu.target as any) } },
        { icon: '📈', label: 'Stats', action: () => { hideContextMenu(); options.showConnectionStats(contextMenu.target as any) } },
        {
          icon: '✏️',
          label: 'Edit',
          submenu: [
            { icon: '↔️', label: `Route: ${styleLabel}`, action: () => { hideContextMenu(); options.toggleConnectionRoutingStyle(contextMenu.target as any) } },
            { icon: '🎯', label: 'Add Waypoint (Alt+Click)', action: () => { hideContextMenu() }, disabled: true } as ContextMenuItem,
            ...(hasWaypoints ? [{ icon: '🧹', label: 'Clear Waypoints', action: () => { hideContextMenu(); options.clearConnectionWaypoints(contextMenu.target as any) } }] : []),
            { icon: '🗑️', label: 'Delete', action: () => { hideContextMenu(); options.deleteConnection(contextMenu.target as any) } },
          ],
        },
      ]
      return items
    }

    // Canvas context menu
    if (!contextMenu.target && contextMenu.targetType === 'canvas') {
      const items = [
        {
          icon: '👁️',
          label: 'View',
          submenu: [
            {
              icon: '📊',
              label: 'Layers',
              submenu: [
                {
                  icon: layerVisibility.value.devices ? '✅' : '☐',
                  label: 'Devices',
                  action: () => {
                    layerVisibility.value.devices = !layerVisibility.value.devices
                    hideContextMenu()
                  }
                },
                {
                  icon: layerVisibility.value.layer2 ? '✅' : '☐',
                  label: 'Layer2',
                  action: () => {
                    layerVisibility.value.layer2 = !layerVisibility.value.layer2
                    hideContextMenu()
                  }
                },
                {
                  icon: layerVisibility.value.layer3 ? '✅' : '☐',
                  label: 'Layer3',
                  action: () => {
                    layerVisibility.value.layer3 = !layerVisibility.value.layer3
                    hideContextMenu()
                  }
                },
                {
                  icon: layerVisibility.value.background ? '✅' : '☐',
                  label: 'Background',
                  action: () => {
                    layerVisibility.value.background = !layerVisibility.value.background
                    hideContextMenu()
                  }
                },
              ],
            },
            { icon: '🖼️', label: 'Fit to Screen', action: () => { hideContextMenu(); options.fitToScreen(canvasContainer.value || null) } },
            { icon: '🏠', label: 'Reset View', action: () => { hideContextMenu(); options.resetView() } },
          ],
        },
        {
          icon: '🔗',
          label: 'Topology',
          submenu: [
            { icon: '🔍', label: 'Discover', action: () => { hideContextMenu(); options.openTopologyDiscovery() } },
            { icon: '🔨', label: 'Build', action: () => { hideContextMenu(); options.openTopologyBuilder() } },
          ],
        },
        {
          icon: '🎨',
          label: 'Canvas',
          submenu: [
            { icon: '📂', label: 'Load', action: () => { hideContextMenu(); options.loadCanvas() } },
            { icon: '💾', label: 'Save', action: () => { hideContextMenu(); options.saveCanvas() } },
            { icon: '📋', label: 'Save As', action: () => { hideContextMenu(); options.saveCanvasAs() } },
            { icon: '🗑️', label: 'Clear', action: () => { hideContextMenu(); options.clearCanvas() } },
          ],
        },
      ]
      return items
    }

    // Multi-device context menu
    if (contextMenu.targetType === 'multi-device') {
      const selectedCount = selectedDevices.value.size
      const items = [
        {
          icon: '⚙️',
          label: 'Config',
          submenu: [
            { icon: '👁️', label: 'Show All', action: () => { hideContextMenu(); options.showMultiDeviceConfig() } },
            { icon: '📝', label: 'Show All Changes', action: () => { hideContextMenu(); options.showMultiDeviceChanges() } },
          ],
        },
        {
          icon: '🔗',
          label: 'Neighbors',
          submenu: [
            { icon: '👁️', label: 'Show All', action: () => { hideContextMenu(); options.showMultiDeviceNeighbors() } },
            { icon: '➕', label: 'Add', action: () => { hideContextMenu(); options.addMultiDeviceNeighborsToCanvas() } },
            {
              icon: '🔗',
              label: 'Connect to',
              action: selectedCount === 2
                ? () => { hideContextMenu(); options.connectTwoDevices() }
                : () => {},
              disabled: selectedCount !== 2
            } as ContextMenuItem,
          ],
        },
        { icon: '🔍', label: 'Analyze All', action: () => { hideContextMenu(); options.analyzeMultiDevices() } },
        {
          icon: '✏️',
          label: 'Edit',
          submenu: [
            {
              icon: '📐',
              label: 'Alignment',
              submenu: [
                { icon: '↔️', label: 'Horizontal', action: () => { hideContextMenu(); options.alignDevicesHorizontally() } },
                { icon: '↕️', label: 'Vertical', action: () => { hideContextMenu(); options.alignDevicesVertically() } },
              ],
            },
            { icon: '🗑️', label: `Remove ${selectedCount} devices`, action: () => { hideContextMenu(); options.deleteMultiDevices() } },
          ],
        },
      ]
      return items
    }

    // Single device context menu
    if (!contextMenu.target) return []

    const device = contextMenu.target!
    const devicePlatform = options.getDevicePlatform(device.properties)
    const platformCommands = options.getCommandsForPlatform(devicePlatform)

    // Build Commands submenu with Send and Reload
    const sendSubmenu = platformCommands.length > 0
      ? platformCommands.map(command => ({
          icon: '⚡',
          label: command.display || command.command,
          action: () => { hideContextMenu(); options.executeCommand(device, command) }
        }))
      : [{
          icon: '❌',
          label: devicePlatform ? `No commands for ${devicePlatform}` : 'No platform detected',
          action: () => {
            hideContextMenu()
            console.log(`No commands configured for platform: ${devicePlatform || 'unknown'}`)
          }
        }]

    const commandsSubmenu = [
      {
        icon: '📤',
        label: 'Send',
        submenu: sendSubmenu
      },
      {
        icon: '🔄',
        label: 'Reload',
        action: async () => {
          console.log('🔄 Reloading commands...')
          await options.reloadCommands()
          console.log('✅ Commands reloaded successfully - menu will update automatically')
          // Don't hide menu - it will update automatically with new commands
        }
      }
    ]

    const items = [
      { icon: '📊', label: 'Overview', action: () => { hideContextMenu(); options.showDeviceOverview(contextMenu.target!) } },
      {
        icon: '💻',
        label: 'SSH Terminal',
        submenu: [
          { icon: '🪟', label: 'Open in Modal', action: () => { hideContextMenu(); options.showSSHTerminal(contextMenu.target!) } },
          { icon: '🚀', label: 'Open in New Window', action: () => { hideContextMenu(); options.openSSHTerminalInWindow(contextMenu.target!) } },
        ]
      },
      {
        icon: '⚙️',
        label: 'Config',
        submenu: [
          {
            icon: '👁️',
            label: 'Show',
            submenu: [
              { icon: '🔧', label: 'Running', action: () => { hideContextMenu(); options.showDeviceRunningConfig(contextMenu.target!) } },
              { icon: '💾', label: 'Startup', action: () => { hideContextMenu(); options.showDeviceStartupConfig(contextMenu.target!) } },
            ]
          },
          { icon: '📝', label: 'Show Changes', action: () => { hideContextMenu(); options.showDeviceChanges(contextMenu.target!) } },
        ],
      },
      {
        icon: '🔌',
        label: 'Interfaces',
        submenu: [
          { icon: '📋', label: 'Brief', action: () => { hideContextMenu(); options.showDeviceInterfaces(contextMenu.target!, 'brief') } },
          { icon: '📄', label: 'Full', action: () => { hideContextMenu(); options.showDeviceInterfaces(contextMenu.target!, 'full') } },
          { icon: '⚠️', label: 'Errors', action: () => { hideContextMenu(); options.showDeviceInterfaces(contextMenu.target!, 'errors') } },
        ],
      },
      {
        icon: '💻',
        label: 'Commands',
        submenu: commandsSubmenu
      },
      {
        icon: '🔗',
        label: 'Neighbors',
        submenu: [
          { icon: '👁️', label: 'Show', action: () => { hideContextMenu(); options.showNeighbors(contextMenu.target!) } },
          {
            icon: '➕',
            label: 'Add',
            submenu: [
              {
                icon: '🔗',
                label: 'Layer2',
                submenu: [
                  { icon: '📡', label: 'CDP', action: () => handleNeighborDiscovery(contextMenu.target!, options.addCdpNeighbors) },
                  { icon: '🔗', label: 'MAC', action: () => { hideContextMenu(); options.addMacNeighbors(contextMenu.target!) } },
                ]
              },
              {
                icon: '🌐',
                label: 'Layer3',
                submenu: [
                  { icon: '🔍', label: 'IP ARP', action: () => handleNeighborDiscovery(contextMenu.target!, options.addArpNeighbors) },
                  { icon: '📌', label: 'Static', action: () => handleNeighborDiscovery(contextMenu.target!, options.addStaticNeighbors) },
                  { icon: '🔀', label: 'OSPF', action: () => handleNeighborDiscovery(contextMenu.target!, options.addOspfNeighbors) },
                  { icon: '🌍', label: 'BGP', action: () => { hideContextMenu(); options.addBgpNeighbors(contextMenu.target!) } },
                ]
              },
            ]
          },
          {
            icon: '🔗',
            label: 'Connect',
            action: selectedDevices.value.size === 2
              ? () => { hideContextMenu(); options.connectTwoDevices() }
              : () => {},
            disabled: selectedDevices.value.size !== 2
          } as ContextMenuItem,
        ],
      },
      {
        icon: '🔍',
        label: 'Analyze',
        submenu: [
          {
            icon: '📊',
            label: 'Baseline',
            submenu: [
              { icon: '➕', label: 'Create', action: () => { hideContextMenu(); options.createBaseline(contextMenu.target!) } },
            ]
          },
          {
            icon: '📸',
            label: 'Snapshot',
            submenu: [
              { icon: '➕', label: 'Create', action: () => { hideContextMenu(); options.createSnapshot(contextMenu.target!) } },
              { icon: '📋', label: 'Manage', action: () => { hideContextMenu(); options.manageSnapshots(contextMenu.target!) } },
            ]
          },
          {
            icon: '⚖️',
            label: 'Compare',
            action: () => { hideContextMenu(); options.compareSnapshotToBaseline(contextMenu.target!) }
          },
        ],
      },
      {
        icon: '✏️',
        label: 'Edit',
        submenu: [
          {
            icon: '📐',
            label: 'Alignment',
            submenu: [
              { icon: '↔️', label: 'Horizontal', action: () => { options.alignDevicesHorizontally() } },
              { icon: '↕️', label: 'Vertical', action: () => { options.alignDevicesVertically() } },
            ],
          },
          { icon: '🔌', label: 'Connection Ports', action: () => { hideContextMenu(); options.manageConnectionPorts(contextMenu.target!) } },
          { icon: '🗑️', label: 'Remove', action: () => { hideContextMenu(); options.deleteDevice(contextMenu.target!) } },
        ],
      },
    ]
    return items
  })
}
