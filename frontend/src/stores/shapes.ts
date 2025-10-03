import { defineStore } from 'pinia'
import { ref } from 'vue'
import { makeAuthenticatedRequest } from '@/services/api'

export interface Shape {
  id: number
  shape_type: 'rectangle' | 'circle'
  position_x: number
  position_y: number
  width: number
  height: number
  fill_color?: string
  stroke_color?: string
  stroke_width?: number
  layer?: string // 'background' or 'devices'
}

export const useShapesStore = defineStore('shapes', () => {
  const shapes = ref<Shape[]>([])
  const isLoading = ref(false)
  let nextTempId = -1 // Use negative IDs for temporary shapes

  const fetchShapes = async () => {
    isLoading.value = true
    try {
      const response = await makeAuthenticatedRequest('/api/shapes', { method: 'GET' })
      if (response.ok) {
        shapes.value = await response.json()
      }
    } catch (error) {
      console.error('Failed to fetch shapes:', error)
    } finally {
      isLoading.value = false
    }
  }

  const createShape = (shapeData: Omit<Shape, 'id'>) => {
    // Create shape in memory only (not saved to DB)
    const newShape = {
      ...shapeData,
      id: nextTempId--,
    }
    shapes.value.push(newShape)
    console.log('🔷 Shape created, shapes.value now has:', shapes.value.length, 'shapes')
    return newShape
  }

  const updateShape = (id: number, shapeData: Partial<Shape>) => {
    const index = shapes.value.findIndex((s) => s.id === id)
    if (index !== -1) {
      shapes.value[index] = { ...shapes.value[index], ...shapeData }
      return shapes.value[index]
    }
    return null
  }

  const deleteShape = (id: number) => {
    shapes.value = shapes.value.filter((s) => s.id !== id)
  }

  const clearShapes = () => {
    shapes.value = []
    nextTempId = -1
  }

  const loadShapesFromCanvasData = (canvasShapes: any[]) => {
    console.log('🔷 loadShapesFromCanvasData called with:', canvasShapes)
    // Clear existing shapes first
    shapes.value = []
    // Load shapes from canvas data (use negative IDs to indicate they're temporary)
    shapes.value = canvasShapes.map((shape, index) => ({
      ...shape,
      id: -(index + 1),
    }))
    nextTempId = -(canvasShapes.length + 1)
    console.log('🔷 Shapes loaded, shapes.value now has:', shapes.value.length, 'shapes')
  }

  return {
    shapes,
    isLoading,
    fetchShapes,
    createShape,
    updateShape,
    deleteShape,
    clearShapes,
    loadShapesFromCanvasData,
  }
})
