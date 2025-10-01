<template>
  <div class="flex flex-col h-screen bg-gray-50">
    <!-- Top Navigation - Full Width -->
    <nav class="bg-white border-b border-gray-200 px-6 py-3 z-10 h-16">
      <div class="flex items-center justify-between h-full">
        <div class="flex items-center space-x-6">
          <h1 class="text-xl font-bold text-gray-900">NOC Canvas</h1>

          <div class="flex space-x-2">
            <router-link
              to="/dashboard"
              class="px-3 py-2 rounded-md text-sm font-medium"
              :class="
                $route.name === 'dashboard'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 hover:text-gray-900'
              "
            >
              Dashboard
            </router-link>
            <router-link
              to="/inventory"
              class="px-3 py-2 rounded-md text-sm font-medium"
              :class="
                $route.name === 'inventory'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 hover:text-gray-900'
              "
            >
              Inventory
            </router-link>
            <router-link
              to="/settings"
              class="px-3 py-2 rounded-md text-sm font-medium"
              :class="
                $route.name === 'settings'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 hover:text-gray-900'
              "
            >
              Settings
            </router-link>
          </div>
        </div>

        <div class="flex items-center space-x-4">
          <!-- Zoom Controls -->
          <div
            v-if="$route.name === 'dashboard'"
            class="flex items-center space-x-2 px-3 py-1.5 bg-gray-50 rounded-lg border"
          >
            <span class="text-sm font-medium text-gray-700">Zoom:</span>

            <!-- Zoom Dropdown with Text Input -->
            <div class="relative">
              <select
                :value="Math.round((currentZoom || 1) * 100)"
                @change="handleDropdownChange($event)"
                class="appearance-none bg-white border border-gray-300 rounded px-2 py-1 text-xs font-mono pr-6 min-w-16"
              >
                <option value="20">20%</option>
                <option value="40">40%</option>
                <option value="50">50%</option>
                <option value="60">60%</option>
                <option value="80">80%</option>
                <option value="100">100%</option>
                <option value="120">120%</option>
                <option value="150">150%</option>
              </select>
              <div class="absolute inset-y-0 right-0 flex items-center pr-1 pointer-events-none">
                <svg
                  class="w-3 h-3 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M19 9l-7 7-7-7"
                  ></path>
                </svg>
              </div>
            </div>

            <!-- Custom Zoom Input -->
            <input
              type="number"
              :value="Math.round((currentZoom || 1) * 100)"
              @input="handleCustomZoom($event)"
              @blur="validateCustomZoom($event)"
              min="10"
              max="300"
              class="w-16 px-2 py-1 text-xs font-mono border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
              placeholder="100"
            />
            <span class="text-xs text-gray-500">%</span>

            <!-- Zoom Slider -->
            <input
              type="range"
              :value="currentZoom"
              @input="handleZoomSlider($event)"
              min="0.1"
              max="3"
              step="0.1"
              class="zoom-slider w-20"
            />
          </div>

          <span class="text-sm text-gray-600">{{ authStore.user?.username }}</span>
          <button @click="logout" class="btn-secondary text-sm">Logout</button>
        </div>
      </div>
    </nav>

    <!-- Content Area with Sidebar -->
    <div class="flex flex-1 min-h-0">
      <!-- Left Panel - Only show on Dashboard -->
      <div
        v-if="$route.name === 'dashboard'"
        class="panel relative flex flex-col"
        :style="`width: ${inventoryPanelWidth}px; min-width: 250px; max-width: 600px; background-color: #f9fafb; border-right: 2px solid #e5e7eb;`"
      >
        <!-- Panel Toggle Headers -->
        <div class="flex border-b border-gray-300 bg-white">
          <button
            @click="activePanel = 'inventory'"
            class="flex-1 px-4 py-3 text-sm font-medium transition-all duration-200 flex items-center justify-center space-x-2"
            :class="activePanel === 'inventory'
              ? 'bg-gray-50 text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'"
          >
            <svg
              class="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"
              />
            </svg>
            <span>Inventory</span>
          </button>
          <button
            @click="activePanel = 'symbols'"
            class="flex-1 px-4 py-3 text-sm font-medium transition-all duration-200 flex items-center justify-center space-x-2"
            :class="activePanel === 'symbols'
              ? 'bg-gray-50 text-purple-600 border-b-2 border-purple-600'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'"
          >
            <svg
              class="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"
              />
            </svg>
            <span>Symbols</span>
          </button>
        </div>

        <!-- Panel Content -->
        <div class="flex-1 min-h-0">
          <InventoryPanel v-if="activePanel === 'inventory'" />
          <SymbolsPanel v-else-if="activePanel === 'symbols'" />
        </div>

        <!-- Resize Handle -->
        <div
          class="absolute top-0 right-0 w-3 h-full cursor-col-resize bg-transparent hover:bg-blue-100 transition-all duration-200 group flex items-center justify-center z-50"
          :class="{ 'bg-blue-200': isResizing }"
          @mousedown="startResize"
          title="Drag to resize panel"
          style="right: -1px"
        >
          <!-- Visual indicator dots for the drag handle -->
          <div
            class="flex flex-col space-y-1 opacity-60 group-hover:opacity-100 transition-opacity duration-200"
          >
            <div class="w-1 h-1 bg-gray-400 rounded-full group-hover:bg-blue-600"></div>
            <div class="w-1 h-1 bg-gray-400 rounded-full group-hover:bg-blue-600"></div>
            <div class="w-1 h-1 bg-gray-400 rounded-full group-hover:bg-blue-600"></div>
            <div class="w-1 h-1 bg-gray-400 rounded-full group-hover:bg-blue-600"></div>
            <div class="w-1 h-1 bg-gray-400 rounded-full group-hover:bg-blue-600"></div>
          </div>
        </div>
      </div>

      <!-- Main Content Area -->
      <div class="flex-1 overflow-auto">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useCanvasStore } from '@/stores/canvas'
import { useRouter } from 'vue-router'
import InventoryPanel from '@/components/InventoryPanel.vue'
import SymbolsPanel from '@/components/SymbolsPanel.vue'

const authStore = useAuthStore()
const canvasStore = useCanvasStore()
const router = useRouter()

// Active panel state (inventory or symbols)
const activePanel = ref<'inventory' | 'symbols'>('inventory')

// Inventory panel resize state
const PANEL_WIDTH_KEY = 'noc-canvas-inventory-panel-width'
const inventoryPanelWidth = ref(320) // Default width (80 * 4 = 320px, equivalent to w-80)
const isResizing = ref(false)
const resizeStartX = ref(0)
const resizeStartWidth = ref(0)

// Load saved panel width from localStorage
const loadSavedPanelWidth = () => {
  const saved = localStorage.getItem(PANEL_WIDTH_KEY)
  if (saved) {
    const width = parseInt(saved)
    if (width >= 250 && width <= 600) {
      inventoryPanelWidth.value = width
      console.log('📐 Loaded saved panel width:', width)
    }
  }
}

// Save panel width to localStorage
const savePanelWidth = (width: number) => {
  localStorage.setItem(PANEL_WIDTH_KEY, width.toString())
  console.log('💾 Saved panel width:', width)
}

// Computed property for current zoom level
const currentZoom = computed(() => {
  console.log('🔍 Current zoom from store:', canvasStore.scale)
  return canvasStore.scale
})

const setZoom = (zoomLevel: number) => {
  console.log('🎯 Setting zoom to:', zoomLevel)
  canvasStore.setZoom(zoomLevel)
}

const handleDropdownChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  const zoomPercent = parseInt(target.value)
  setZoom(zoomPercent / 100)
}

const handleCustomZoom = (event: Event) => {
  const target = event.target as HTMLInputElement
  const zoomPercent = parseInt(target.value)
  if (!isNaN(zoomPercent) && zoomPercent >= 10 && zoomPercent <= 300) {
    setZoom(zoomPercent / 100)
  }
}

const handleZoomSlider = (event: Event) => {
  const target = event.target as HTMLInputElement
  setZoom(parseFloat(target.value))
}

const validateCustomZoom = (event: Event) => {
  const target = event.target as HTMLInputElement
  let zoomPercent = parseInt(target.value)

  // Clamp values to valid range
  if (isNaN(zoomPercent) || zoomPercent < 10) {
    zoomPercent = 10
  } else if (zoomPercent > 300) {
    zoomPercent = 300
  }

  // Update the input value and set zoom
  target.value = zoomPercent.toString()
  setZoom(zoomPercent / 100)
}

// Panel resize functions
const startResize = (event: MouseEvent) => {
  event.preventDefault()
  event.stopPropagation()

  isResizing.value = true
  resizeStartX.value = event.clientX
  resizeStartWidth.value = inventoryPanelWidth.value

  console.log('🔄 Starting panel resize', {
    startX: event.clientX,
    startWidth: inventoryPanelWidth.value,
    isResizing: isResizing.value,
  })

  // Prevent text selection during resize
  document.body.style.userSelect = 'none'
  document.body.style.cursor = 'col-resize'
}

const handleResize = (event: MouseEvent) => {
  if (!isResizing.value) {
    return
  }

  const deltaX = event.clientX - resizeStartX.value
  const newWidth = resizeStartWidth.value + deltaX

  // Apply constraints: min 250px, max 600px
  const constrainedWidth = Math.max(250, Math.min(600, newWidth))
  inventoryPanelWidth.value = constrainedWidth

  console.log('🔄 Resizing panel', {
    isResizing: isResizing.value,
    clientX: event.clientX,
    startX: resizeStartX.value,
    deltaX,
    newWidth,
    constrainedWidth,
  })
}

const stopResize = () => {
  console.log('🛑 Stop resize called, isResizing:', isResizing.value)

  if (!isResizing.value) return

  isResizing.value = false
  console.log('✅ Panel resize stopped, final width:', inventoryPanelWidth.value)

  // Save the new width to localStorage
  savePanelWidth(inventoryPanelWidth.value)

  // Restore default cursor and text selection
  document.body.style.userSelect = ''
  document.body.style.cursor = ''
}

// Event listeners for resize
onMounted(() => {
  // Load saved panel width on component mount
  loadSavedPanelWidth()

  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
})

const logout = async () => {
  await authStore.logout()
  router.push('/login')
}
</script>
