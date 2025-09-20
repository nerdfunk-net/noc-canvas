import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useCanvasStore = defineStore('canvas', () => {
  const scale = ref(1)
  const position = ref({ x: 0, y: 0 })

  const setZoom = (newScale: number) => {
    // Clamp zoom level between 0.1 and 3
    scale.value = Math.max(0.1, Math.min(3, newScale))
  }

  const setPosition = (newPosition: { x: number; y: number }) => {
    position.value = newPosition
  }

  const resetView = () => {
    scale.value = 1
    position.value = { x: 0, y: 0 }
  }

  const zoomIn = () => {
    const newScale = Math.min(3, scale.value * 1.2)
    setZoom(newScale)
  }

  const zoomOut = () => {
    const newScale = Math.max(0.1, scale.value / 1.2)
    setZoom(newScale)
  }

  return {
    scale,
    position,
    setZoom,
    setPosition,
    resetView,
    zoomIn,
    zoomOut
  }
})