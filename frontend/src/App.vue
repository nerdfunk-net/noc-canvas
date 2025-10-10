<template>
  <router-view />

  <!-- Session Warning Dialog -->
  <SessionWarningDialog
    :show="sessionState.showWarning"
    :time-remaining="sessionState.timeRemaining"
    :total-warning-time="120"
    @continue="handleContinueSession"
    @cancel="handleLogoutFromWarning"
  />
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import SessionWarningDialog from '@/components/SessionWarningDialog.vue'
import sessionManager from '@/services/sessionManager'
import { tokenKeepAlive } from '@/services/tokenKeepAlive'
import { set401Handler } from '@/services/api'

const router = useRouter()
const authStore = useAuthStore()
const sessionState = sessionManager.state

// Handle session expiration
const handleSessionExpired = async () => {
  console.warn('⚠️ App: Session expired, redirecting to login')
  tokenKeepAlive.stop() // Stop token refresh when session expires
  await authStore.logout()
  router.push('/login')
}

// Handle user clicking "Continue" in warning dialog
const handleContinueSession = async () => {
  console.log('✅ App: User chose to continue session')
  await sessionManager.extendSession()
}

// Handle user clicking "Logout" in warning dialog
const handleLogoutFromWarning = async () => {
  console.log('🔐 App: User chose to logout from warning')
  sessionManager.dismissWarning()
  tokenKeepAlive.stop() // Stop token refresh on logout
  await authStore.logout()
  router.push('/login')
}

// Set up 401 handler for API requests
set401Handler(() => {
  console.warn('⚠️ App: 401 received, session expired')
  handleSessionExpired()
})

// Start/stop session manager based on authentication
onMounted(() => {
  // Register session expired callback
  sessionManager.onSessionExpired(handleSessionExpired)

  // Start session manager and token keep-alive if authenticated
  if (authStore.isAuthenticated) {
    console.log('🔐 App: User authenticated, starting session manager and token keep-alive')
    sessionManager.start()
    tokenKeepAlive.start()
  }

  // Watch for authentication changes
  const stopWatcher = router.afterEach((to) => {
    if (to.meta.requiresAuth && authStore.isAuthenticated) {
      // User logged in or navigated to protected route
      if (!sessionState.value.isActive) {
        console.log('🔐 App: Starting session manager on protected route')
        sessionManager.start()
      }
      // Start token keep-alive for authenticated users
      tokenKeepAlive.start()
    } else if (to.name === 'login') {
      // User navigated to login, stop session manager and token keep-alive
      if (sessionState.value.isActive) {
        console.log('🔐 App: Stopping session manager on login page')
        sessionManager.stop()
      }
      tokenKeepAlive.stop()
    }
  })

  onBeforeUnmount(() => {
    stopWatcher()
  })
})

onBeforeUnmount(() => {
  sessionManager.stop()
  tokenKeepAlive.stop()
})
</script>
