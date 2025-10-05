<template>
  <Teleport to="body">
    <Transition name="dialog">
      <div
        v-if="show"
        class="fixed inset-0 z-[9999] flex items-center justify-center bg-black bg-opacity-50"
        @click.self="onCancel"
      >
        <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 overflow-hidden">
          <!-- Header -->
          <div class="bg-gradient-to-r from-orange-500 to-red-500 px-6 py-4">
            <div class="flex items-center gap-3 text-white">
              <i class="fas fa-exclamation-triangle text-2xl"></i>
              <h3 class="text-lg font-semibold">Session Expiring Soon</h3>
            </div>
          </div>

          <!-- Content -->
          <div class="px-6 py-6">
            <p class="text-gray-700 mb-4">
              Your session will expire in <strong class="text-red-600">{{ formattedTimeRemaining }}</strong> due to inactivity.
            </p>
            <p class="text-gray-600 text-sm">
              Would you like to continue working? Click "Continue" to extend your session.
            </p>

            <!-- Progress Bar -->
            <div class="mt-4 bg-gray-200 rounded-full h-2 overflow-hidden">
              <div
                class="bg-gradient-to-r from-orange-500 to-red-500 h-full transition-all duration-1000 ease-linear"
                :style="{ width: `${progressPercentage}%` }"
              ></div>
            </div>
          </div>

          <!-- Actions -->
          <div class="px-6 py-4 bg-gray-50 flex justify-end gap-3">
            <button
              @click="onCancel"
              class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
            >
              Logout
            </button>
            <button
              @click="onContinue"
              class="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-blue-700 rounded-md hover:from-blue-700 hover:to-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors shadow-sm"
            >
              <i class="fas fa-check mr-2"></i>
              Continue Working
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'

interface Props {
  show: boolean
  timeRemaining: number // in seconds
  totalWarningTime: number // in seconds
}

const props = defineProps<Props>()

const emit = defineEmits<{
  continue: []
  cancel: []
}>()

const localTimeRemaining = ref(props.timeRemaining)
let countdownInterval: number | null = null

// Format time remaining as MM:SS
const formattedTimeRemaining = computed(() => {
  const minutes = Math.floor(localTimeRemaining.value / 60)
  const seconds = localTimeRemaining.value % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
})

// Calculate progress percentage for visual countdown
const progressPercentage = computed(() => {
  return Math.max(0, (localTimeRemaining.value / props.totalWarningTime) * 100)
})

// Start countdown when dialog is shown
watch(() => props.show, (isShown) => {
  if (isShown) {
    localTimeRemaining.value = props.timeRemaining
    startCountdown()
  } else {
    stopCountdown()
  }
})

// Update local time when prop changes
watch(() => props.timeRemaining, (newTime) => {
  localTimeRemaining.value = newTime
})

const startCountdown = () => {
  stopCountdown() // Clear any existing interval
  countdownInterval = window.setInterval(() => {
    localTimeRemaining.value -= 1
    if (localTimeRemaining.value <= 0) {
      stopCountdown()
      // Auto-logout when time runs out
      emit('cancel')
    }
  }, 1000)
}

const stopCountdown = () => {
  if (countdownInterval !== null) {
    clearInterval(countdownInterval)
    countdownInterval = null
  }
}

const onContinue = () => {
  stopCountdown()
  emit('continue')
}

const onCancel = () => {
  stopCountdown()
  emit('cancel')
}

onUnmounted(() => {
  stopCountdown()
})
</script>

<style scoped>
.dialog-enter-active,
.dialog-leave-active {
  transition: opacity 0.3s ease;
}

.dialog-enter-from,
.dialog-leave-to {
  opacity: 0;
}

.dialog-enter-active .bg-white,
.dialog-leave-active .bg-white {
  transition: transform 0.3s ease;
}

.dialog-enter-from .bg-white {
  transform: scale(0.9);
}

.dialog-leave-to .bg-white {
  transform: scale(0.9);
}
</style>
