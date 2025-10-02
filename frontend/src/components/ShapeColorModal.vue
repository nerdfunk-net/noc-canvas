<template>
  <div
    v-if="show"
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    @click.self="close"
  >
    <div class="bg-white rounded-lg shadow-xl p-6 w-96">
      <h2 class="text-xl font-semibold mb-4">Shape Color</h2>

      <div class="space-y-4">
        <!-- Fill Color -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Fill Color</label>
          <div class="flex items-center gap-3">
            <input
              v-model="fillColor"
              type="color"
              class="w-20 h-10 rounded cursor-pointer"
            />
            <input
              v-model="fillColor"
              type="text"
              class="flex-1 px-3 py-2 border border-gray-300 rounded-md"
              placeholder="#93c5fd"
            />
          </div>
        </div>

        <!-- Stroke Color -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Stroke Color</label>
          <div class="flex items-center gap-3">
            <input
              v-model="strokeColor"
              type="color"
              class="w-20 h-10 rounded cursor-pointer"
            />
            <input
              v-model="strokeColor"
              type="text"
              class="flex-1 px-3 py-2 border border-gray-300 rounded-md"
              placeholder="#3b82f6"
            />
          </div>
        </div>

        <!-- Stroke Width -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Stroke Width: {{ strokeWidth }}px
          </label>
          <input
            v-model.number="strokeWidth"
            type="range"
            min="1"
            max="10"
            class="w-full"
          />
        </div>
      </div>

      <div class="flex justify-end gap-3 mt-6">
        <button
          @click="close"
          class="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          @click="save"
          class="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
        >
          Save
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface Props {
  show: boolean
  shapeId: number | null
  initialFillColor?: string
  initialStrokeColor?: string
  initialStrokeWidth?: number
}

const props = withDefaults(defineProps<Props>(), {
  initialFillColor: '#93c5fd',
  initialStrokeColor: '#3b82f6',
  initialStrokeWidth: 2,
})

const emit = defineEmits<{
  close: []
  save: [{ fillColor: string; strokeColor: string; strokeWidth: number }]
}>()

const fillColor = ref(props.initialFillColor)
const strokeColor = ref(props.initialStrokeColor)
const strokeWidth = ref(props.initialStrokeWidth)

watch(() => props.show, (newShow) => {
  if (newShow) {
    fillColor.value = props.initialFillColor
    strokeColor.value = props.initialStrokeColor
    strokeWidth.value = props.initialStrokeWidth
  }
})

const close = () => {
  emit('close')
}

const save = () => {
  emit('save', {
    fillColor: fillColor.value,
    strokeColor: strokeColor.value,
    strokeWidth: strokeWidth.value,
  })
}
</script>
