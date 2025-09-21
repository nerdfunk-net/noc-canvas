<template>
  <!-- Save Canvas Modal -->
  <div
    v-if="show"
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    @click="closeModal"
  >
    <div
      class="bg-white rounded-lg p-6 max-w-md w-full mx-4"
      @click.stop
    >
      <h2 class="text-lg font-semibold mb-4">Save Canvas</h2>

      <form @submit.prevent="saveCanvas">
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Canvas Name
            </label>
            <input
              v-model="canvasForm.name"
              type="text"
              placeholder="Enter canvas name"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
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

          <!-- Canvas Summary -->
          <div class="bg-gray-50 p-3 rounded-md">
            <p class="text-sm text-gray-700 mb-2">Canvas Summary:</p>
            <ul class="text-xs text-gray-600 space-y-1">
              <li>• {{ deviceCount }} devices</li>
              <li>• {{ connectionCount }} connections</li>
              <li v-if="canvasForm.sharable">• Will be visible to other users</li>
              <li v-else>• Private to you only</li>
            </ul>
          </div>

          <!-- Error Message -->
          <div v-if="error" class="bg-red-50 border border-red-200 rounded-md p-3">
            <p class="text-sm text-red-600">{{ error }}</p>
          </div>

          <div class="flex justify-end space-x-2">
            <button
              type="button"
              @click="closeModal"
              class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              :disabled="saving"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              :disabled="saving || !canvasForm.name.trim()"
            >
              {{ saving ? 'Saving...' : 'Save Canvas' }}
            </button>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  show: boolean
  deviceCount: number
  connectionCount: number
}

const props = defineProps<Props>()

interface Emits {
  (e: 'close'): void
  (e: 'save', data: { name: string; sharable: boolean }): void
}

const emit = defineEmits<Emits>()

// Form state
const canvasForm = ref({
  name: '',
  sharable: false
})

const saving = ref(false)
const error = ref<string | null>(null)

// Methods
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
  error.value = null
  saving.value = false
}

const saveCanvas = async () => {
  if (!canvasForm.value.name.trim()) {
    error.value = 'Canvas name is required'
    return
  }

  saving.value = true
  error.value = null

  try {
    emit('save', {
      name: canvasForm.value.name.trim(),
      sharable: canvasForm.value.sharable
    })
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'An error occurred while saving'
    saving.value = false
  }
}

// Reset form when modal is shown
const resetOnShow = () => {
  if (props.show) {
    resetForm()
  }
}

// Watch for show prop changes to reset form
import { watch } from 'vue'
watch(() => props.show, resetOnShow)

// Expose methods for parent component
defineExpose({
  resetForm,
  setSaving: (value: boolean) => { saving.value = value },
  setError: (message: string | null) => { error.value = message }
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