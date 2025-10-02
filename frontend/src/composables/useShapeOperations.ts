import { ref, computed } from 'vue'
import { useShapesStore } from '@/stores/shapes'

export function useShapeOperations() {
  const shapesStore = useShapesStore()

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
