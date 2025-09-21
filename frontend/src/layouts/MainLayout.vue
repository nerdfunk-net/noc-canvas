<template>
  <div class="flex h-screen bg-gray-50">
    <!-- Left Panel - Only show on Dashboard -->
    <div 
      v-if="$route.name === 'dashboard'"
      class="w-80 panel" 
      style="min-width: 320px; background-color: #f9fafb; border-right: 2px solid #e5e7eb;"
    >
      <div class="p-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-800">Device Inventory</h2>
      </div>
      <InventoryPanel />
    </div>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col">
      <!-- Top Navigation -->
      <nav class="bg-white border-b border-gray-200 px-6 py-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-6">
            <h1 class="text-xl font-bold text-gray-900">NOC Canvas</h1>

            <div class="flex space-x-2">
              <router-link
                to="/dashboard"
                class="px-3 py-2 rounded-md text-sm font-medium"
                :class="$route.name === 'dashboard' ? 'bg-primary-600 text-white' : 'text-gray-600 hover:text-gray-900'"
              >
                Dashboard
              </router-link>
              <router-link
                to="/inventory"
                class="px-3 py-2 rounded-md text-sm font-medium"
                :class="$route.name === 'inventory' ? 'bg-primary-600 text-white' : 'text-gray-600 hover:text-gray-900'"
              >
                Inventory
              </router-link>
              <router-link
                to="/settings"
                class="px-3 py-2 rounded-md text-sm font-medium"
                :class="$route.name === 'settings' ? 'bg-primary-600 text-white' : 'text-gray-600 hover:text-gray-900'"
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
                  <svg class="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
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
            <button
              @click="logout"
              class="btn-secondary text-sm"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      <!-- Main Canvas Area -->
      <div class="flex-1 overflow-auto">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useCanvasStore } from '@/stores/canvas'
import { useRouter } from 'vue-router'
import InventoryPanel from '@/components/InventoryPanel.vue'

const authStore = useAuthStore()
const canvasStore = useCanvasStore()
const router = useRouter()

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

const logout = async () => {
  await authStore.logout()
  router.push('/login')
}
</script>