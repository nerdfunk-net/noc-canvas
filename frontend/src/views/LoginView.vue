<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          {{ isLogin ? 'Sign in to NOC Canvas' : 'Create your account' }}
        </h2>
      </div>
      <form class="mt-8 space-y-6" @submit.prevent="handleSubmit">
        <div class="rounded-md shadow-sm -space-y-px">
          <div>
            <label for="username" class="sr-only">Username</label>
            <input
              id="username"
              v-model="form.username"
              name="username"
              type="text"
              required
              class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
              placeholder="Username"
            />
          </div>
          <div>
            <label for="password" class="sr-only">Password</label>
            <input
              id="password"
              v-model="form.password"
              name="password"
              type="password"
              :autocomplete="isLogin ? 'current-password' : 'new-password'"
              required
              minlength="6"
              @input="checkPasswordStrength"
              class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
              placeholder="Password"
            />
          </div>
        </div>

        <!-- Password Strength Indicator (only for registration) -->
        <div v-if="!isLogin && form.password && passwordStrength" class="text-sm">
          <div class="flex items-center gap-2">
            <span class="font-medium">Password strength:</span>
            <span :class="{
              'text-red-600': passwordStrength.level === 'weak',
              'text-yellow-600': passwordStrength.level === 'medium',
              'text-green-600': passwordStrength.level === 'strong'
            }">
              {{ passwordStrength.level.toUpperCase() }}
            </span>
          </div>
          <ul class="mt-1 text-xs text-gray-600 space-y-1">
            <li v-for="(msg, idx) in passwordStrength.messages" :key="idx">
              {{ msg }}
            </li>
          </ul>
        </div>

        <!-- Weak Password Confirmation -->
        <div v-if="showWeakPasswordWarning" class="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <p class="text-sm text-yellow-800 mb-2">
            ⚠️ Your password is weak. Are you sure you want to continue?
          </p>
          <div class="flex gap-2">
            <button
              type="button"
              @click="proceedWithWeakPassword"
              class="px-3 py-1 bg-yellow-600 text-white text-sm rounded hover:bg-yellow-700"
            >
              Yes, continue
            </button>
            <button
              type="button"
              @click="showWeakPasswordWarning = false"
              class="px-3 py-1 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        </div>

        <div v-if="error" class="text-red-600 text-sm text-center">
          {{ error }}
        </div>

        <div>
          <button
            type="submit"
            :disabled="loading"
            class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
          >
            {{ loading ? 'Processing...' : isLogin ? 'Sign in' : 'Sign up' }}
          </button>
        </div>

        <div class="text-center">
          <button
            type="button"
            @click="toggleMode"
            class="text-primary-600 hover:text-primary-500 text-sm"
          >
            {{ isLogin ? "Don't have an account? Sign up" : 'Already have an account? Sign in' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const isLogin = ref(true)
const loading = ref(false)
const error = ref('')
const showWeakPasswordWarning = ref(false)
const weakPasswordConfirmed = ref(false)

interface PasswordStrength {
  level: 'weak' | 'medium' | 'strong'
  messages: string[]
}

const passwordStrength = ref<PasswordStrength | null>(null)

const form = reactive({
  username: '',
  password: '',
})

const toggleMode = () => {
  isLogin.value = !isLogin.value
  error.value = ''
  showWeakPasswordWarning.value = false
  weakPasswordConfirmed.value = false
  passwordStrength.value = null
}

const checkPasswordStrength = () => {
  const password = form.password
  const messages: string[] = []
  let score = 0

  // Length check
  if (password.length >= 12) {
    score += 2
  } else if (password.length >= 8) {
    score += 1
    messages.push('✓ At least 8 characters')
  } else {
    messages.push('✗ Should be at least 8 characters')
  }

  // Complexity checks
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) {
    score += 1
    messages.push('✓ Contains uppercase and lowercase')
  } else {
    messages.push('✗ Add uppercase and lowercase letters')
  }

  if (/\d/.test(password)) {
    score += 1
    messages.push('✓ Contains numbers')
  } else {
    messages.push('✗ Add numbers')
  }

  if (/[^A-Za-z0-9]/.test(password)) {
    score += 1
    messages.push('✓ Contains special characters')
  } else {
    messages.push('✗ Add special characters (!@#$%^&*)')
  }

  // Determine strength level
  let level: 'weak' | 'medium' | 'strong'
  if (score >= 4) {
    level = 'strong'
  } else if (score >= 2) {
    level = 'medium'
  } else {
    level = 'weak'
  }

  passwordStrength.value = { level, messages }
}

const proceedWithWeakPassword = () => {
  weakPasswordConfirmed.value = true
  showWeakPasswordWarning.value = false
  handleSubmit()
}

const handleSubmit = async () => {
  // For registration, check password strength
  if (!isLogin.value && !weakPasswordConfirmed.value) {
    checkPasswordStrength()

    if (passwordStrength.value?.level === 'weak') {
      showWeakPasswordWarning.value = true
      return
    }
  }

  loading.value = true
  error.value = ''

  try {
    if (isLogin.value) {
      await authStore.login(form.username, form.password)
      router.push('/dashboard')
    } else {
      await authStore.register(form.username, form.password)
      // After successful registration, auto-login
      await authStore.login(form.username, form.password)
      router.push('/dashboard')
    }
  } catch (err: any) {
    error.value = err.message || 'An error occurred'
  } finally {
    loading.value = false
    weakPasswordConfirmed.value = false
  }
}
</script>
