<template>
  <!-- Save Canvas Modal -->
  <div
    v-if="show"
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    @click="closeModal"
  >
    <div
      class="bg-white rounded-lg shadow-xl p-6 w-[700px] max-w-[90vw] max-h-[85vh] flex flex-col"
      @click.stop
    >
      <!-- Header -->
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-900">
          Save Canvas
        </h3>
        <button
          @click="closeModal"
          class="text-gray-400 hover:text-gray-600 transition-colors"
          type="button"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>

      <!-- Canvas Summary -->
      <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <div class="flex items-center space-x-2 text-blue-800">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path>
          </svg>
          <span class="font-medium">Current Canvas: {{ deviceCount }} devices, {{ connectionCount }} connections</span>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex items-center justify-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span class="ml-3 text-gray-600">Loading your canvases...</span>
      </div>

      <!-- Error State -->
      <div v-else-if="loadError" class="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
        <div class="flex">
          <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-red-800">Error Loading Canvases</h3>
            <p class="mt-1 text-sm text-red-700">{{ loadError }}</p>
          </div>
        </div>
      </div>

      <div v-else class="flex-1 overflow-hidden flex flex-col">
        <!-- Action Tabs -->
        <div class="flex space-x-1 mb-4 bg-gray-100 rounded-lg p-1">
          <button
            @click="activeTab = 'new'"
            :class="[
              'flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors',
              activeTab === 'new' 
                ? 'bg-white text-gray-900 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            ]"
          >
            Create New
          </button>
          <button
            @click="activeTab = 'existing'"
            :class="[
              'flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors',
              activeTab === 'existing' 
                ? 'bg-white text-gray-900 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            ]"
          >
            Overwrite Existing ({{ userCanvases.length }})
          </button>
        </div>

        <!-- Create New Tab -->
        <div v-if="activeTab === 'new'" class="flex-1 flex flex-col">
          <form @submit.prevent="handleSave" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Canvas Name
              </label>
              <input
                ref="nameInput"
                v-model="canvasForm.name"
                type="text"
                placeholder="Enter canvas name"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
                :disabled="saving"
              />
            </div>

            <div class="flex items-start space-x-2">
              <input
                id="sharable"
                v-model="canvasForm.sharable"
                type="checkbox"
                class="mt-1 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                :disabled="saving"
              />
              <div>
                <label for="sharable" class="block text-sm font-medium text-gray-700">
                  Make sharable
                </label>
                <p class="text-xs text-gray-500 mt-1">
                  Allow other users to view and load this canvas
                </p>
              </div>
            </div>
          </form>
        </div>

        <!-- Existing Canvases Tab -->
        <div v-else class="flex-1 overflow-hidden flex flex-col">
          <!-- Search Bar -->
          <div class="mb-4">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search your canvases..."
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
          </div>

          <!-- Empty State -->
          <div v-if="userCanvases.length === 0" class="text-center py-12 text-gray-500">
            <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path>
              </svg>
            </div>
            <p class="text-base font-medium text-gray-900 mb-1">No saved canvases</p>
            <p class="text-sm text-gray-500">Switch to "Create New" to save your first canvas</p>
          </div>

          <!-- Canvas Grid -->
          <div v-else class="flex-1 overflow-y-auto">
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              <div
                v-for="canvas in filteredUserCanvases"
                :key="canvas.id"
                class="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 hover:border-gray-300 cursor-pointer transition-all duration-200 relative group"
                :class="{ 
                  'ring-2 ring-blue-500 bg-blue-50 border-blue-200': selectedCanvas?.id === canvas.id,
                  'hover:shadow-md': selectedCanvas?.id !== canvas.id
                }"
                @click="selectCanvas(canvas)"
              >
                <!-- Canvas Icon and Info -->
                <div class="flex items-start space-x-3">
                  <!-- Canvas Icon -->
                  <div class="flex-shrink-0">
                    <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
                      <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path>
                      </svg>
                    </div>
                  </div>

                  <!-- Content -->
                  <div class="flex-1 min-w-0">
                    <!-- Canvas Name -->
                    <h4 class="font-medium text-gray-900 text-sm truncate">{{ canvas.name }}</h4>
                    
                    <!-- Canvas Info -->
                    <div class="mt-1 text-xs text-gray-500">
                      <span class="text-blue-600 font-medium">Your canvas</span>
                      <span v-if="canvas.sharable" class="ml-2">• Sharable</span>
                    </div>

                    <!-- Date -->
                    <p class="mt-1 text-xs text-gray-400">
                      {{ formatDate(canvas.updated_at) }}
                    </p>
                  </div>
                </div>

                <!-- Status Badges -->
                <div class="absolute top-2 right-2 flex flex-col space-y-1">
                  <!-- Selection indicator -->
                  <div v-if="selectedCanvas?.id === canvas.id" class="w-4 h-4 bg-blue-600 rounded-full flex items-center justify-center">
                    <svg class="w-2.5 h-2.5 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                    </svg>
                  </div>
                  
                  <!-- Sharing indicator -->
                  <div v-if="canvas.sharable" class="w-4 h-4 bg-green-500 rounded-full flex items-center justify-center" title="Shared canvas">
                    <svg class="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z"></path>
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="saveError" class="bg-red-50 border border-red-200 rounded-md p-3 mt-4">
          <p class="text-sm text-red-600">{{ saveError }}</p>
        </div>
      </div>

      <!-- Actions -->
      <div v-if="!loading && !loadError" class="flex justify-end space-x-3 mt-4 pt-4 border-t border-gray-200">
        <button
          @click="closeModal"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
          type="button"
          :disabled="saving"
        >
          Cancel
        </button>
        <button
          @click="handleSave"
          :disabled="saving || !canSave"
          class="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          type="button"
        >
          {{ getSaveButtonText() }}
        </button>
      </div>
    </div>

    <!-- Overwrite Confirmation Dialog -->
    <div 
      v-if="showOverwriteDialog" 
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-60"
      @click.self="cancelOverwrite"
    >
      <div class="bg-white rounded-lg shadow-xl p-6 w-96 max-w-md">
        <!-- Header -->
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900">
            Confirm Overwrite
          </h3>
          <button
            @click="cancelOverwrite"
            class="text-gray-400 hover:text-gray-600 transition-colors"
            type="button"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>

        <!-- Message -->
        <div class="mb-6">
          <div class="flex items-center mb-3">
            <div class="flex-shrink-0">
              <svg class="h-8 w-8 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 14.5c-.77.833.192 2.5 1.732 2.5z"></path>
              </svg>
            </div>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-gray-900">
                Canvas Already Exists
              </h3>
            </div>
          </div>
          
          <p class="text-gray-700 text-sm leading-relaxed mb-2">
            A canvas named <strong>"{{ overwriteCanvasName }}"</strong> already exists.
          </p>
          
          <p class="text-gray-600 text-sm">
            Do you want to overwrite it with the current canvas?
          </p>
        </div>

        <!-- Actions -->
        <div class="flex justify-end space-x-3">
          <button
            @click="cancelOverwrite"
            class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
            type="button"
          >
            Cancel
          </button>
          <button
            @click="confirmOverwrite"
            class="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-colors"
            type="button"
          >
            Overwrite
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { canvasApi, type CanvasListItem } from '@/services/api'

interface Props {
  show: boolean
  deviceCount: number
  connectionCount: number
}

const props = defineProps<Props>()

interface Emits {
  (e: 'close'): void
  (e: 'save', data: { name: string; sharable: boolean; canvasId?: number }): void
}

const emit = defineEmits<Emits>()

// Form state
const canvasForm = ref({
  name: '',
  sharable: false
})

// UI state
const activeTab = ref<'new' | 'existing'>('new')
const saving = ref(false)
const loading = ref(false)
const saveError = ref<string | null>(null)
const loadError = ref<string | null>(null)
const searchQuery = ref('')
const nameInput = ref<HTMLInputElement>()

// Canvas state
const userCanvases = ref<CanvasListItem[]>([])
const selectedCanvas = ref<CanvasListItem | null>(null)

// Overwrite confirmation
const showOverwriteDialog = ref(false)
const overwriteCanvasName = ref('')
const pendingOverwriteData = ref<{ name: string; sharable: boolean; canvasId?: number } | null>(null)

// Computed properties
const filteredUserCanvases = computed(() => {
  if (!searchQuery.value.trim()) {
    return userCanvases.value
  }
  
  const query = searchQuery.value.toLowerCase()
  return userCanvases.value.filter(canvas => 
    canvas.name.toLowerCase().includes(query)
  )
})

const canSave = computed(() => {
  if (activeTab.value === 'new') {
    return canvasForm.value.name.trim() !== ''
  } else {
    return selectedCanvas.value !== null
  }
})

// Methods
const loadUserCanvases = async () => {
  loading.value = true
  loadError.value = null
  
  try {
    console.log('🔄 Loading user canvases...')
    const response = await canvasApi.getCanvasList()
    // Filter to only show user's own canvases
    userCanvases.value = response.filter(canvas => canvas.is_own)
    console.log('✅ Loaded user canvases:', userCanvases.value)
  } catch (err) {
    console.error('❌ Failed to load user canvases:', err)
    loadError.value = err instanceof Error ? err.message : 'Failed to load canvases'
  } finally {
    loading.value = false
  }
}

const selectCanvas = (canvas: CanvasListItem) => {
  selectedCanvas.value = selectedCanvas.value?.id === canvas.id ? null : canvas
  if (selectedCanvas.value) {
    // Pre-fill the form with selected canvas data
    canvasForm.value.name = canvas.name
    canvasForm.value.sharable = canvas.sharable
  }
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

const getSaveButtonText = () => {
  if (saving.value) return 'Saving...'
  if (activeTab.value === 'new') return 'Save Canvas'
  return 'Overwrite Canvas'
}

const checkNameExists = (name: string): CanvasListItem | null => {
  return userCanvases.value.find(canvas => 
    canvas.name.toLowerCase() === name.toLowerCase()
  ) || null
}

const handleSave = async () => {
  if (!canSave.value) return

  const saveData = {
    name: canvasForm.value.name.trim(),
    sharable: canvasForm.value.sharable,
    canvasId: activeTab.value === 'existing' ? selectedCanvas.value?.id : undefined
  }

  // Check for name conflicts when creating new canvas
  if (activeTab.value === 'new') {
    const existingCanvas = checkNameExists(saveData.name)
    if (existingCanvas) {
      // Show overwrite confirmation
      overwriteCanvasName.value = saveData.name
      pendingOverwriteData.value = saveData
      showOverwriteDialog.value = true
      return
    }
  }

  await performSave(saveData)
}

const performSave = async (saveData: { name: string; sharable: boolean; canvasId?: number }) => {
  saving.value = true
  saveError.value = null

  try {
    emit('save', saveData)
  } catch (err) {
    saveError.value = err instanceof Error ? err.message : 'An error occurred while saving'
    saving.value = false
  }
}

const confirmOverwrite = async () => {
  if (pendingOverwriteData.value) {
    const existingCanvas = checkNameExists(pendingOverwriteData.value.name)
    if (existingCanvas) {
      // Add the canvas ID to overwrite the existing one
      pendingOverwriteData.value.canvasId = existingCanvas.id
    }
    await performSave(pendingOverwriteData.value)
  }
  cancelOverwrite()
}

const cancelOverwrite = () => {
  showOverwriteDialog.value = false
  overwriteCanvasName.value = ''
  pendingOverwriteData.value = null
}

const closeModal = () => {
  if (!saving.value) {
    resetForm()
    emit('close')
  }
}

const resetForm = () => {
  canvasForm.value = {
    name: '',
    sharable: false
  }
  activeTab.value = 'new'
  selectedCanvas.value = null
  saveError.value = null
  loadError.value = null
  saving.value = false
  searchQuery.value = ''
  cancelOverwrite()
}

// Focus name input when switching to new tab
watch(activeTab, async (newTab) => {
  if (newTab === 'new') {
    await nextTick()
    nameInput.value?.focus()
  }
})

// Watch for show prop changes to reset form and load data
watch(() => props.show, async (show) => {
  if (show) {
    resetForm()
    await loadUserCanvases()
    // Focus name input when modal opens
    await nextTick()
    if (activeTab.value === 'new') {
      nameInput.value?.focus()
    }
  }
})

// Expose methods for parent component
defineExpose({
  resetForm,
  setSaving: (value: boolean) => { saving.value = value },
  setError: (message: string | null) => { saveError.value = message }
})
</script>

<style scoped>
/* Modal backdrop animation */
.fixed {
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Modal content animation */
.bg-white {
  animation: slideIn 0.2s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
</style>