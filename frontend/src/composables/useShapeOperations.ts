import { ref, computed } from 'vue'
import { useShapesStore } from '@/stores/shapes'
import { useDevicesStore, type Device } from '@/stores/devices'

export function useShapeOperations(selectedDevices?: any, deviceStore?: any) {
  const shapesStore = useShapesStore()
  const devicesStoreInstance = deviceStore || useDevicesStore()

  // Selected shape state
  const selectedShape = ref<number | null>(null)
  const selectedShapes = ref<Set<number>>(new Set())
  const transformer = ref<any>(null)
  const showShapeColorModal = ref(false)
  const shapeColorToEdit = ref<number | null>(null)

  // Current shape colors for modal
  const currentShapeColors = computed(() => {
    if (!shapeColorToEdit.value) {
      return { fill: '#93c5fd', stroke: '#3b82f6', strokeWidth: 2 }
    }
    const shape = shapesStore.shapes.find(s => s.id === shapeColorToEdit.value)
    return {
      fill: shape?.fill_color || '#93c5fd',
      stroke: shape?.stroke_color || '#3b82f6',
      strokeWidth: shape?.stroke_width || 2,
    }
  })

  // Track drag state for shapes
  const shapeDragState = ref<{
    draggedShape: any | null
    initialPositions: Map<number, { x: number; y: number }>
    initialDevicePositions?: Map<number, { x: number; y: number }>
  } | null>(null)

  // Shape drag start handler
  const onShapeDragStart = (shape: any) => {
    // Initialize drag state
    shapeDragState.value = {
      draggedShape: shape,
      initialPositions: new Map(),
      initialDevicePositions: new Map()
    }

    // Store initial positions of all selected shapes
    const selectedShapesList = Array.from(selectedShapes.value)
      .map(id => shapesStore.shapes.find(s => s.id === id))
      .filter((s): s is any => s !== undefined)

    selectedShapesList.forEach(selectedShape => {
      shapeDragState.value!.initialPositions.set(selectedShape.id, {
        x: selectedShape.position_x,
        y: selectedShape.position_y
      })
    })

    // Store initial positions of all selected devices (if any)
    if (selectedDevices && selectedDevices.value) {
      const selectedDevicesList = Array.from(selectedDevices.value)
        .map((id: number) => devicesStoreInstance.devices.find((d: Device) => d.id === id))
        .filter((d): d is Device => d !== undefined)

      selectedDevicesList.forEach((selectedDevice: Device) => {
        shapeDragState.value!.initialDevicePositions!.set(selectedDevice.id, {
          x: selectedDevice.position_x,
          y: selectedDevice.position_y
        })
      })
    }
  }

  // Shape drag move handler
  const onShapeDragMove = (shape: any, event: any) => {
    const currentX = event.target.x()
    const currentY = event.target.y()

    // Handle multi-selection dragging (shapes and devices)
    if (shapeDragState.value) {
      // Calculate the delta from the shape's initial position
      const initialPos = shapeDragState.value.initialPositions.get(shape.id)
      if (!initialPos) return

      const deltaX = currentX - initialPos.x
      const deltaY = currentY - initialPos.y

      // Update positions of other selected shapes in real-time
      if (selectedShapes.value.size > 1 && selectedShapes.value.has(shape.id)) {
        const otherSelectedShapes = Array.from(selectedShapes.value)
          .map(id => shapesStore.shapes.find(s => s.id === id))
          .filter((s): s is any => s !== undefined && s.id !== shape.id)

        otherSelectedShapes.forEach(selectedShape => {
          const initialShapePos = shapeDragState.value!.initialPositions.get(selectedShape.id)
          if (!initialShapePos) return

          const newX = initialShapePos.x + deltaX
          const newY = initialShapePos.y + deltaY

          // Update the shape position in the store in real-time
          shapesStore.updateShape(selectedShape.id, {
            position_x: newX,
            position_y: newY,
          })
        })
      }

      // Update positions of selected devices in real-time
      if (selectedDevices && selectedDevices.value && selectedDevices.value.size > 0 && shapeDragState.value.initialDevicePositions) {
        const selectedDevicesList = Array.from(selectedDevices.value)
          .map((id: number) => devicesStoreInstance.devices.find((d: Device) => d.id === id))
          .filter((d): d is Device => d !== undefined)

        selectedDevicesList.forEach((selectedDevice: Device) => {
          const initialDevicePos = shapeDragState.value!.initialDevicePositions!.get(selectedDevice.id)
          if (!initialDevicePos) return

          const newX = initialDevicePos.x + deltaX
          const newY = initialDevicePos.y + deltaY

          // Update the device position in the store in real-time
          devicesStoreInstance.updateDevice(selectedDevice.id, {
            position_x: newX,
            position_y: newY,
          })
        })
      }
    }
  }

  // Shape click handler
  const onShapeClick = (shape: any, event: any) => {
    // Ignore right-clicks (they're handled by onShapeRightClick)
    if (event.evt.button === 2) {
      console.log('🔴 DEBUG: onShapeClick - ignoring right-click')
      return
    }

    event.cancelBubble = true

    // Multi-selection with Shift key
    if (event.evt.shiftKey) {
      if (selectedShapes.value.has(shape.id)) {
        selectedShapes.value.delete(shape.id)
        if (selectedShape.value === shape.id) {
          selectedShape.value = selectedShapes.value.size > 0 ? Array.from(selectedShapes.value)[0] : null
        }
      } else {
        selectedShapes.value.add(shape.id)
        selectedShape.value = shape.id
      }
    } else {
      selectedShapes.value.clear()
      selectedShapes.value.add(shape.id)
      selectedShape.value = shape.id
    }

    // Attach transformer to the clicked shape (only for single selection)
    if (transformer.value && selectedShapes.value.size === 1) {
      const stage = event.target.getStage()
      const shapeNode = event.target.getParent()
      transformer.value.getNode().nodes([shapeNode])
      transformer.value.getNode().getLayer().batchDraw()
    } else if (transformer.value) {
      // Clear transformer for multi-selection
      transformer.value.getNode().nodes([])
    }
  }

  // Shape drag end handler
  const onShapeDragEnd = (shape: any, event: any) => {
    const node = event.target
    shapesStore.updateShape(shape.id, {
      position_x: node.x(),
      position_y: node.y(),
    })

    // Clean up drag state
    shapeDragState.value = null
  }

  // Shape right-click handler
  const onShapeRightClick = (shape: any, event: any, showContextMenu: Function) => {
    console.log('🔴 DEBUG: onShapeRightClick called', { shape, event })
    event.evt.preventDefault()
    event.evt.stopPropagation()
    event.cancelBubble = true

    // If the clicked shape is not in selection, select only it
    if (!selectedShapes.value.has(shape.id)) {
      console.log('🔴 DEBUG: Shape not in selection, adding to selection', shape.id)
      selectedShapes.value.clear()
      selectedShapes.value.add(shape.id)
      selectedShape.value = shape.id
    } else {
      console.log('🔴 DEBUG: Shape already in selection', shape.id, 'Selected shapes:', Array.from(selectedShapes.value))
    }

    // Show context menu
    const stage = event.target.getStage()
    const pointerPosition = stage.getPointerPosition()

    console.log('🔴 DEBUG: Pointer position:', pointerPosition)
    console.log('🔴 DEBUG: Selected shapes count:', selectedShapes.value.size)

    if (selectedShapes.value.size > 1) {
      console.log('🔴 DEBUG: Showing multi-shape context menu')
      showContextMenu(pointerPosition.x, pointerPosition.y, Array.from(selectedShapes.value) as any, 'multi-shape')
    } else {
      console.log('🔴 DEBUG: Showing single shape context menu')
      showContextMenu(pointerPosition.x, pointerPosition.y, shape, 'shape')
    }
  }

  // Open shape color modal
  const openShapeColorModal = (shape: any) => {
    shapeColorToEdit.value = shape.id
    showShapeColorModal.value = true
  }

  // Handle shape color save
  const handleShapeColorSave = (colors: { fillColor: string; strokeColor: string; strokeWidth: number }) => {
    if (shapeColorToEdit.value) {
      shapesStore.updateShape(shapeColorToEdit.value, {
        fill_color: colors.fillColor,
        stroke_color: colors.strokeColor,
        stroke_width: colors.strokeWidth,
      })
    }
    showShapeColorModal.value = false
  }

  // Delete single shape
  const deleteShape = (shape: any) => {
    shapesStore.deleteShape(shape.id)
    selectedShape.value = null
    selectedShapes.value.delete(shape.id)
  }

  // Delete multiple shapes
  const deleteMultiShapes = () => {
    const shapesToDelete = Array.from(selectedShapes.value)
    for (const shapeId of shapesToDelete) {
      shapesStore.deleteShape(shapeId)
    }
    selectedShape.value = null
    selectedShapes.value.clear()
  }

  // Align shapes horizontally
  const alignShapesHorizontally = () => {
    const shapes = Array.from(selectedShapes.value)
      .map(id => shapesStore.shapes.find(s => s.id === id))
      .filter(s => s !== undefined)

    if (shapes.length < 2) return

    // Calculate average Y position
    const avgY = shapes.reduce((sum, s) => sum + s!.position_y, 0) / shapes.length

    // Update all shapes to align horizontally
    shapes.forEach(shape => {
      if (shape) {
        shapesStore.updateShape(shape.id, { position_y: avgY })
      }
    })
  }

  // Align shapes vertically
  const alignShapesVertically = () => {
    const shapes = Array.from(selectedShapes.value)
      .map(id => shapesStore.shapes.find(s => s.id === id))
      .filter(s => s !== undefined)

    if (shapes.length < 2) return

    // Calculate average X position
    const avgX = shapes.reduce((sum, s) => sum + s!.position_x, 0) / shapes.length

    // Update all shapes to align vertically
    shapes.forEach(shape => {
      if (shape) {
        shapesStore.updateShape(shape.id, { position_x: avgX })
      }
    })
  }

  // Clear shape selection
  const clearShapeSelection = () => {
    selectedShape.value = null
    selectedShapes.value.clear()
    if (transformer.value) {
      transformer.value.getNode().nodes([])
    }
  }

  return {
    // State
    selectedShape,
    selectedShapes,
    transformer,
    showShapeColorModal,
    shapeColorToEdit,
    currentShapeColors,

    // Methods
    onShapeClick,
    onShapeDragStart,
    onShapeDragMove,
    onShapeDragEnd,
    onShapeRightClick,
    openShapeColorModal,
    handleShapeColorSave,
    deleteShape,
    deleteMultiShapes,
    alignShapesHorizontally,
    alignShapesVertically,
    clearShapeSelection,
  }
}
