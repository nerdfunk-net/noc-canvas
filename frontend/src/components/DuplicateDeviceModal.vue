<template>
  <div 
    v-if="show" 
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    @click.self="cancel"
  >
    <div class="bg-white rounded-lg shadow-xl p-6 w-96 max-w-md">
      <!-- Header -->
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-900">
          Device Already Exists
        </h3>
        <button
          @click="cancel"
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
              Duplicate Device
            </h3>
          </div>
        </div>
        
        <p class="text-gray-700 text-sm leading-relaxed">
          The device <strong>"{{ deviceName }}"</strong> is already on the canvas.
        </p>
        
        <p class="text-gray-600 text-sm mt-2">
          Would you like to locate the existing device or add a duplicate?
        </p>
      </div>

      <!-- Actions -->
      <div class="flex justify-end space-x-3">
        <button
          @click="cancel"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
          type="button"
        >
          Cancel
        </button>
        <button
          @click="showExisting"
          class="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
          type="button"
        >
          Show Existing
        </button>
        <button
          @click="addDuplicate"
          class="px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-colors"
          type="button"
        >
          Add Duplicate
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  show: boolean
  deviceName: string
}

interface Emits {
  (e: 'cancel'): void
  (e: 'show'): void
  (e: 'add'): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()

const cancel = () => {
  emit('cancel')
}

const showExisting = () => {
  emit('show')
}

const addDuplicate = () => {
  emit('add')
}
</script>