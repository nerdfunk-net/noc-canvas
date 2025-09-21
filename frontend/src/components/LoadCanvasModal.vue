<template>
  <div 
    v-if="show" 
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    @click.self="close"
  >
    <div class="bg-white rounded-lg shadow-xl p-6 w-[600px] max-w-[90vw] max-h-[80vh] flex flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-900">
          Load Canvas
        </h3>
        <button
          @click="close"
          class="text-gray-400 hover:text-gray-600 transition-colors"
          type="button"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex items-center justify-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span class="ml-3 text-gray-600">Loading canvases...</span>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
        <div class="flex">
          <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-red-800">Error Loading Canvases</h3>
            <p class="mt-1 text-sm text-red-700">{{ error }}</p>
          </div>
        </div>
      </div>

      <!-- Canvas List -->
      <div v-else-if="canvases.length === 0" class="text-center py-8 text-gray-500">
        <svg class="mx-auto h-12 w-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path>
        </svg>
        <p class="mt-2 text-sm">No saved canvases found</p>
      </div>

      <div v-else class="flex-1 overflow-hidden flex flex-col">
        <!-- Search Bar -->
        <div class="mb-4">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search canvases..."
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
        </div>

        <!-- Canvas Items -->
        <div class="flex-1 overflow-y-auto space-y-2">
          <div
            v-for="canvas in filteredCanvases"
            :key="canvas.id"
            class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors"
            :class="{ 'ring-2 ring-blue-500 bg-blue-50': selectedCanvas?.id === canvas.id }"
            @click="selectCanvas(canvas)"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <!-- Canvas Name -->
                <h4 class="font-medium text-gray-900">{{ canvas.name }}</h4>
                
                <!-- Owner Info -->
                <div class="flex items-center mt-1 text-sm text-gray-600">
                  <span v-if="canvas.is_own" class="text-blue-600 font-medium">Your canvas</span>
                  <span v-else>
                    Created by <span class="font-medium">{{ canvas.owner_username }}</span>
                  </span>
                  
                  <!-- Sharable indicator -->
                  <span v-if="canvas.sharable && !canvas.is_own" class="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                    <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z"></path>
                    </svg>
                    Shared
                  </span>
                  <span v-else-if="canvas.sharable && canvas.is_own" class="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                    <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z"></path>
                    </svg>
                    Sharable
                  </span>
                </div>

                <!-- Date -->
                <p class="mt-1 text-xs text-gray-500">
                  Updated {{ formatDate(canvas.updated_at) }}
                </p>
              </div>

              <!-- Selection indicator -->
              <div v-if="selectedCanvas?.id === canvas.id" class="flex-shrink-0 ml-3">
                <svg class="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div v-if="!loading && !error" class="flex justify-end space-x-3 mt-4 pt-4 border-t border-gray-200">
        <button
          @click="close"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
          type="button"
        >
          Cancel
        </button>
        <button
          @click="loadCanvas"
          :disabled="!selectedCanvas"
          class="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          type="button"
        >
          Load Canvas
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { canvasApi, type CanvasListItem } from '@/services/api'

interface Props {
  show: boolean
}

interface Emits {
  (e: 'close'): void
  (e: 'load', canvasId: number): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const canvases = ref<CanvasListItem[]>([])
const selectedCanvas = ref<CanvasListItem | null>(null)
const searchQuery = ref('')
const loading = ref(false)
const error = ref<string | null>(null)

const filteredCanvases = computed(() => {
  if (!searchQuery.value.trim()) {
    return canvases.value
  }
  
  const query = searchQuery.value.toLowerCase()
  return canvases.value.filter(canvas => 
    canvas.name.toLowerCase().includes(query) ||
    canvas.owner_username.toLowerCase().includes(query)
  )
})

const selectCanvas = (canvas: CanvasListItem) => {
  selectedCanvas.value = canvas
}

const loadCanvas = () => {
  if (selectedCanvas.value) {
    emit('load', selectedCanvas.value.id)
  }
}

const close = () => {
  emit('close')
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)
  
  if (diffInHours < 24) {
    return `${Math.floor(diffInHours)} hours ago`
  } else if (diffInHours < 24 * 7) {
    return `${Math.floor(diffInHours / 24)} days ago`
  } else {
    return date.toLocaleDateString()
  }
}

const loadCanvases = async () => {
  loading.value = true
  error.value = null
  
  try {
    console.log('🔄 Loading canvases...')
    const response = await canvasApi.getCanvasList()
    canvases.value = response
    console.log('✅ Loaded canvases:', response)
  } catch (err) {
    console.error('❌ Failed to load canvases:', err)
    error.value = err instanceof Error ? err.message : 'Failed to load canvases'
  } finally {
    loading.value = false
  }
}

// Load canvases when modal is shown
watch(() => props.show, (newShow) => {
  if (newShow) {
    selectedCanvas.value = null
    searchQuery.value = ''
    loadCanvases()
  }
}, { immediate: false })
</script>