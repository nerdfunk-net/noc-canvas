import { computed, ref, type Ref, type ComputedRef } from 'vue'
import type { Device } from '@/stores/devices'

const DEVICE_SIZE = 60
const DEVICE_HALF_SIZE = DEVICE_SIZE / 2

interface Connection {
  id: number
  source_device_id: number
  target_device_id: number
  source_port_id?: number
  target_port_id?: number
  routing_style?: 'straight' | 'orthogonal'
  waypoints?: { x: number; y: number }[]
  layer?: 'layer2' | 'layer3'
}

interface RenderedConnection {
  id: number
  points: number[]
  routingStyle: string
  waypoints: { x: number; y: number }[]
}

interface ConnectionRenderingOptions {
  connections: Connection[]
  devices: Device[]
  dragPositions: Ref<Map<number, { x: number; y: number }>>
}

export function useConnectionRendering(options: ConnectionRenderingOptions) {
  const { connections, devices, dragPositions } = options

  // Waypoint dragging state
  const draggingWaypoint = ref<{
    connectionId: number
    waypointIndex: number
  } | null>(null)

  /**
   * Calculate the best edge connection point between two devices
   */
  const getEdgeConnectionPoint = (
    sourcePos: { x: number; y: number },
    targetPos: { x: number; y: number }
  ): { sourcePoint: { x: number; y: number }; targetPoint: { x: number; y: number } } => {
    // Calculate center points
    const sourceCenterX = sourcePos.x + DEVICE_HALF_SIZE
    const sourceCenterY = sourcePos.y + DEVICE_HALF_SIZE
    const targetCenterX = targetPos.x + DEVICE_HALF_SIZE
    const targetCenterY = targetPos.y + DEVICE_HALF_SIZE

    // Calculate direction from source to target
    const dx = targetCenterX - sourceCenterX
    const dy = targetCenterY - sourceCenterY

    // Determine which edge of source device to use
    let sourcePoint: { x: number; y: number }
    if (Math.abs(dx) > Math.abs(dy)) {
      // Horizontal connection dominates
      if (dx > 0) {
        // Target is to the right - use right edge
        sourcePoint = { x: sourcePos.x + DEVICE_SIZE, y: sourceCenterY }
      } else {
        // Target is to the left - use left edge
        sourcePoint = { x: sourcePos.x, y: sourceCenterY }
      }
    } else {
      // Vertical connection dominates
      if (dy > 0) {
        // Target is below - use bottom edge
        sourcePoint = { x: sourceCenterX, y: sourcePos.y + DEVICE_SIZE }
      } else {
        // Target is above - use top edge
        sourcePoint = { x: sourceCenterX, y: sourcePos.y }
      }
    }

    // Determine which edge of target device to use (opposite direction)
    let targetPoint: { x: number; y: number }
    if (Math.abs(dx) > Math.abs(dy)) {
      // Horizontal connection dominates
      if (dx > 0) {
        // Source is to the left - use left edge
        targetPoint = { x: targetPos.x, y: targetCenterY }
      } else {
        // Source is to the right - use right edge
        targetPoint = { x: targetPos.x + DEVICE_SIZE, y: targetCenterY }
      }
    } else {
      // Vertical connection dominates
      if (dy > 0) {
        // Source is above - use top edge
        targetPoint = { x: targetCenterX, y: targetPos.y }
      } else {
        // Source is below - use bottom edge
        targetPoint = { x: targetCenterX, y: targetPos.y + DEVICE_SIZE }
      }
    }

    return { sourcePoint, targetPoint }
  }

  /**
   * Calculate orthogonal (right-angle) path points for connections
   */
  const calculateOrthogonalPath = (
    x1: number,
    y1: number,
    x2: number,
    y2: number,
    waypoints?: { x: number; y: number }[]
  ): number[] => {
    // If custom waypoints are provided, use them
    if (waypoints && waypoints.length > 0) {
      const points: number[] = [x1, y1]
      waypoints.forEach(wp => {
        points.push(wp.x, wp.y)
      })
      points.push(x2, y2)
      return points
    }

    // Default orthogonal path (automatic routing)
    // Create a path with right-angle corners
    // Route: start -> vertical to midpoint -> horizontal -> vertical to end
    return [
      x1, y1,      // Start point
      x1, y1 + (y2 - y1) / 2,  // Vertical segment to middle height
      x2, y1 + (y2 - y1) / 2,  // Horizontal segment to target x
      x2, y2       // Vertical segment to end point
    ]
  }

  /**
   * Render all connections with proper routing
   */
  const renderConnections: ComputedRef<RenderedConnection[]> = computed(() => {
    return connections
      .map((connection) => {
        const sourceDevice = devices.find((d) => d.id === connection.source_device_id)
        const targetDevice = devices.find((d) => d.id === connection.target_device_id)

        if (!sourceDevice || !targetDevice) return null

        // Use drag positions if device is being dragged, otherwise use stored positions
        const sourcePos = dragPositions.value.get(sourceDevice.id) || {
          x: sourceDevice.position_x,
          y: sourceDevice.position_y
        }
        const targetPos = dragPositions.value.get(targetDevice.id) || {
          x: targetDevice.position_x,
          y: targetDevice.position_y
        }

        // Check if connection uses specific ports
        let x1: number, y1: number, x2: number, y2: number

        if (connection.source_port_id && sourceDevice.connectionPorts) {
          // Use specific source port
          const sourcePort = sourceDevice.connectionPorts.find(p => p.id === connection.source_port_id)
          if (sourcePort) {
            x1 = sourcePos.x + sourcePort.x
            y1 = sourcePos.y + sourcePort.y
          } else {
            // Fallback to edge point if port not found
            const { sourcePoint } = getEdgeConnectionPoint(sourcePos, targetPos)
            x1 = sourcePoint.x
            y1 = sourcePoint.y
          }
        } else {
          // Use automatic edge connection point
          const { sourcePoint } = getEdgeConnectionPoint(sourcePos, targetPos)
          x1 = sourcePoint.x
          y1 = sourcePoint.y
        }

        if (connection.target_port_id && targetDevice.connectionPorts) {
          // Use specific target port
          const targetPort = targetDevice.connectionPorts.find(p => p.id === connection.target_port_id)
          if (targetPort) {
            x2 = targetPos.x + targetPort.x
            y2 = targetPos.y + targetPort.y
          } else {
            // Fallback to edge point if port not found
            const { targetPoint } = getEdgeConnectionPoint(sourcePos, targetPos)
            x2 = targetPoint.x
            y2 = targetPoint.y
          }
        } else {
          // Use automatic edge connection point
          const { targetPoint } = getEdgeConnectionPoint(sourcePos, targetPos)
          x2 = targetPoint.x
          y2 = targetPoint.y
        }

        // Determine points based on routing style (default to straight)
        const routingStyle = connection.routing_style || 'straight'
        const points = routingStyle === 'orthogonal'
          ? calculateOrthogonalPath(x1, y1, x2, y2, connection.waypoints)
          : connection.waypoints && connection.waypoints.length > 0
            ? [x1, y1, ...connection.waypoints.flatMap(wp => [wp.x, wp.y]), x2, y2]
            : [x1, y1, x2, y2]

        return {
          id: connection.id,
          points,
          routingStyle,
          waypoints: connection.waypoints || [],
        }
      })
      .filter((connection): connection is NonNullable<typeof connection> => connection !== null)
  })

  /**
   * Filter connections by layer
   */
  const layer2Connections = computed(() => {
    return renderConnections.value.filter(conn => {
      const connection = connections.find(c => c.id === conn.id)
      return connection?.layer === 'layer2'
    })
  })

  const layer3Connections = computed(() => {
    return renderConnections.value.filter(conn => {
      const connection = connections.find(c => c.id === conn.id)
      return connection?.layer === 'layer3' || !connection?.layer // Default to layer3 if not specified
    })
  })

  /**
   * Helper functions to check connection layers
   */
  const isLayer2Connection = (connectionId: number): boolean => {
    const connection = connections.find(c => c.id === connectionId)
    return connection?.layer === 'layer2'
  }

  const isLayer3Connection = (connectionId: number): boolean => {
    const connection = connections.find(c => c.id === connectionId)
    return connection?.layer === 'layer3' || !connection?.layer // Default to layer3
  }

  /**
   * Waypoint management functions
   */
  const getConnectionWaypoints = (connectionId: number) => {
    const connection = connections.find(c => c.id === connectionId)
    return connection?.waypoints || []
  }

  const onWaypointDragStart = (connectionId: number, waypointIndex: number) => {
    draggingWaypoint.value = { connectionId, waypointIndex }
    console.log('🎯 Waypoint drag start:', connectionId, waypointIndex)
  }

  const onWaypointDragMove = (connectionId: number, waypointIndex: number, event: any) => {
    const connection = connections.find(c => c.id === connectionId)
    if (!connection || !connection.waypoints) return

    // Get the dragged node's position (already in world coordinates by Konva)
    const node = event.target
    const nodeX = node.x()
    const nodeY = node.y()

    // Update waypoint position with the node's position
    connection.waypoints[waypointIndex] = {
      x: nodeX,
      y: nodeY
    }
  }

  const onWaypointDragEnd = () => {
    draggingWaypoint.value = null
    console.log('🎯 Waypoint drag end')
  }

  const onWaypointRightClick = (connectionId: number, waypointIndex: number, event: any) => {
    event.evt.preventDefault()
    event.evt.stopPropagation()
    event.cancelBubble = true

    // Show simple confirmation to delete waypoint
    if (confirm('Delete this waypoint?')) {
      deleteWaypoint(connectionId, waypointIndex)
    }
  }

  const deleteWaypoint = (connectionId: number, waypointIndex: number) => {
    const connection = connections.find(c => c.id === connectionId)
    if (!connection || !connection.waypoints) return

    connection.waypoints.splice(waypointIndex, 1)
    console.log('✅ Waypoint deleted:', waypointIndex)
  }

  return {
    // State
    draggingWaypoint,

    // Computed
    renderConnections,
    layer2Connections,
    layer3Connections,

    // Helper functions
    isLayer2Connection,
    isLayer3Connection,
    getEdgeConnectionPoint,
    calculateOrthogonalPath,

    // Waypoint functions
    getConnectionWaypoints,
    onWaypointDragStart,
    onWaypointDragMove,
    onWaypointDragEnd,
    onWaypointRightClick,
    deleteWaypoint,
  }
}
