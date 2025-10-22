<template>
  <div class="space-y-6">
    <!-- Canvas Management -->
    <div class="card p-6">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-lg font-semibold text-gray-900">Canvas Management</h2>
        <div class="flex items-center space-x-3">
          <!-- Selection Info -->
          <span v-if="selectedCanvases.size > 0" class="text-sm text-gray-600">
            {{ selectedCanvases.size }} selected
          </span>

          <!-- Action Buttons -->
          <button
            v-if="selectedCanvases.size === 1"
            @click="$emit('show-rename')"
            class="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
            title="Rename selected canvas"
          >
            <i class="fas fa-edit mr-1"></i>
            Rename
          </button>

          <button
            v-if="selectedCanvases.size === 1"
            @click="$emit('load-canvas')"
            class="px-3 py-1 text-xs bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors"
            title="Load selected canvas"
          >
            <i class="fas fa-folder-open mr-1"></i>
            Load
          </button>

          <button
            v-if="selectedCanvases.size > 0"
            @click="$emit('show-delete')"
            class="px-3 py-1 text-xs bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
            title="Delete selected canvases"
          >
            <i class="fas fa-trash mr-1"></i>
            Delete ({{ selectedCanvases.size }})
          </button>

          <button
            @click="$emit('refresh')"
            :disabled="loading"
            class="px-3 py-1 text-xs bg-gray-600 hover:bg-gray-700 disabled:bg-gray-400 text-white rounded-md transition-colors"
            title="Refresh canvas list"
          >
            <i
              :class="loading ? 'fas fa-spinner fa-spin' : 'fas fa-sync-alt'"
              class="mr-1"
            ></i>
            Refresh
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex items-center justify-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span class="ml-3 text-gray-600">Loading canvases...</span>
      </div>

      <!-- Error State -->
      <div
        v-else-if="error"
        class="bg-red-50 border border-red-200 rounded-md p-4 mb-6"
      >
        <div class="flex">
          <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path
              fill-rule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clip-rule="evenodd"
            />
          </svg>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-red-800">Error Loading Canvases</h3>
            <p class="mt-1 text-sm text-red-700">{{ error }}</p>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="canvases.length === 0" class="text-center py-12 text-gray-500">
        <div
          class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4"
        >
          <svg
            class="w-8 h-8 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
            ></path>
          </svg>
        </div>
        <p class="text-base font-medium text-gray-900 mb-1">No saved canvases</p>
        <p class="text-sm text-gray-500">Create your first canvas to get started</p>
      </div>

      <!-- Canvas Grid -->
      <div v-else>
        <!-- Search Bar -->
        <div class="mb-6">
          <div class="relative">
            <input
              :value="searchQuery"
              @input="$emit('update:search-query', ($event.target as HTMLInputElement).value)"
              type="text"
              placeholder="Search canvases..."
              class="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <div
              class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none"
            >
              <svg
                class="h-5 w-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                ></path>
              </svg>
            </div>
          </div>
        </div>

        <!-- Canvas Tiles -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <div
            v-for="canvas in filteredCanvases"
            :key="canvas.id"
            class="relative border border-gray-200 rounded-lg p-4 hover:bg-gray-50 hover:border-gray-300 cursor-pointer transition-all duration-200"
            :class="{
              'ring-2 ring-blue-500 bg-blue-50 border-blue-200': selectedCanvases.has(
                canvas.id
              ),
              'hover:shadow-md': !selectedCanvases.has(canvas.id),
            }"
            @click="$emit('toggle-selection', canvas.id)"
          >
            <!-- Selection Checkbox -->
            <div class="absolute top-3 right-3">
              <div
                class="w-5 h-5 border-2 rounded"
                :class="
                  selectedCanvases.has(canvas.id)
                    ? 'bg-blue-600 border-blue-600'
                    : 'border-gray-300'
                "
              >
                <svg
                  v-if="selectedCanvases.has(canvas.id)"
                  class="w-3 h-3 text-white ml-0.5 mt-0.5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fill-rule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clip-rule="evenodd"
                  ></path>
                </svg>
              </div>
            </div>

            <!-- Canvas Content -->
            <div class="pr-8">
              <!-- Canvas Icon -->
              <div
                class="w-12 h-12 bg-gradient-to-br rounded-lg flex items-center justify-center mb-3"
                :class="getCanvasIconGradient(canvas)"
              >
                <svg
                  class="w-6 h-6 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                  ></path>
                </svg>
              </div>

              <!-- Canvas Name -->
              <h3
                class="font-medium text-gray-900 text-sm mb-1 truncate"
                :title="canvas.name"
              >
                {{ canvas.name }}
              </h3>

              <!-- Canvas Info -->
              <div class="text-xs text-gray-500 mb-2">
                <span v-if="canvas.is_own" class="text-blue-600 font-medium"
                  >Your canvas</span
                >
                <span v-else>
                  <svg
                    class="w-3 h-3 inline mr-1 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                    ></path>
                  </svg>
                  {{ canvas.owner_username }}
                </span>
                <span v-if="canvas.sharable" class="ml-2 text-green-600">• Shared</span>
              </div>

              <!-- Date -->
              <p class="text-xs text-gray-400">
                {{ formatCanvasDate(canvas.updated_at) }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Canvas {
  id: number
  name: string
  owner_username: string
  is_own: boolean
  sharable: boolean
  updated_at: string
}

interface Props {
  canvases: Canvas[]
  selectedCanvases: Set<number>
  searchQuery: string
  loading: boolean
  error: string | null
}

const props = defineProps<Props>()

defineEmits<{
  'show-rename': []
  'load-canvas': []
  'show-delete': []
  'refresh': []
  'toggle-selection': [id: number]
  'update:search-query': [query: string]
}>()

const filteredCanvases = computed(() => {
  if (!props.searchQuery) return props.canvases
  const query = props.searchQuery.toLowerCase()
  return props.canvases.filter(canvas =>
    canvas.name.toLowerCase().includes(query)
  )
})

const getCanvasIconGradient = (canvas: Canvas) => {
  const gradients = [
    'from-blue-400 to-blue-600',
    'from-green-400 to-green-600',
    'from-purple-400 to-purple-600',
    'from-pink-400 to-pink-600',
    'from-indigo-400 to-indigo-600',
    'from-red-400 to-red-600',
  ]
  return gradients[canvas.id % gradients.length]
}

const formatCanvasDate = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diffInMs = now.getTime() - date.getTime()
  const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24))

  if (diffInDays === 0) return 'Today'
  if (diffInDays === 1) return 'Yesterday'
  if (diffInDays < 7) return `${diffInDays} days ago`
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
</script>
