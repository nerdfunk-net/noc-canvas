import { ref, reactive } from 'vue'
import type { Device } from '@/stores/devices'

export type ContextMenuTargetType = 'canvas' | 'device' | 'multi-device'

export interface ContextMenuItem {
  icon: string
  label: string
  action?: () => void
  submenu?: ContextMenuItem[]
}

export function useContextMenu() {
  // State
  const contextMenu = reactive({
    show: false,
    x: 0,
    y: 0,
    target: null as Device | null,
    targetType: 'canvas' as ContextMenuTargetType,
  })

  // Context menu just shown timestamp to prevent immediate hiding
  const contextMenuShownAt = ref(0)

  // Methods
  const showContextMenu = (
    x: number,
    y: number,
    target: Device | null = null,
    targetType: ContextMenuTargetType = 'canvas'
  ) => {
    contextMenu.show = true
    contextMenu.x = x
    contextMenu.y = y
    contextMenu.target = target
    contextMenu.targetType = targetType
    contextMenuShownAt.value = Date.now()

    console.log('✅ Context menu shown:', {
      x,
      y,
      targetType,
      target: target?.name,
      timestamp: contextMenuShownAt.value
    })
  }

  const hideContextMenu = () => {
    console.log('🚫 hideContextMenu() called - HIDING CONTEXT MENU')
    console.trace('🔍 hideContextMenu called from:')
    console.log('📊 Context menu state before hiding:', {
      show: contextMenu.show,
      targetType: contextMenu.targetType,
      target: contextMenu.target?.name,
      timeSinceShown: Date.now() - contextMenuShownAt.value
    })
    contextMenu.show = false
  }

  const calculateMenuPosition = (
    event: MouseEvent,
    containerElement: HTMLElement,
    menuWidth = 200,
    menuHeight = 200
  ): { x: number; y: number } => {
    const rect = containerElement.getBoundingClientRect()
    
    let menuX = event.clientX - rect.left
    let menuY = event.clientY - rect.top

    // Ensure menu doesn't go outside the container bounds
    if (menuX + menuWidth > rect.width) {
      menuX = rect.width - menuWidth
    }
    if (menuY + menuHeight > rect.height) {
      menuY = rect.height - menuHeight
    }

    // Ensure menu doesn't go negative
    menuX = Math.max(0, menuX)
    menuY = Math.max(0, menuY)

    return { x: menuX, y: menuY }
  }

  const isRecentlyShown = (threshold = 100): boolean => {
    return Date.now() - contextMenuShownAt.value < threshold
  }

  return {
    // State
    contextMenu,
    contextMenuShownAt,
    
    // Methods
    showContextMenu,
    hideContextMenu,
    calculateMenuPosition,
    isRecentlyShown,
  }
}