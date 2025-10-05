/**
 * Session Manager Service
 *
 * Manages user session lifecycle with activity tracking, token refresh,
 * and inactivity timeout handling.
 */

import { ref } from 'vue'
import activityTracker from './activityTracker'
import secureStorage from './secureStorage'
import { authApi } from './api'

export interface SessionState {
  showWarning: boolean
  timeRemaining: number
  isActive: boolean
}

class SessionManager {
  private checkIntervalId: number | null = null
  private readonly CHECK_INTERVAL = 10 * 1000 // Check every 10 seconds

  // Reactive state
  public state = ref<SessionState>({
    showWarning: false,
    timeRemaining: 0,
    isActive: false,
  })

  // Callbacks
  private onSessionExpiredCallback: (() => void) | null = null

  /**
   * Start session management
   */
  start(): void {
    if (this.checkIntervalId !== null) {
      console.warn('SessionManager already started')
      return
    }

    console.log('🔐 SessionManager: Starting session management')
    this.state.value.isActive = true

    // Start activity tracking
    activityTracker.start()

    // Listen for activity to refresh token
    activityTracker.onActivity(() => {
      this.handleActivity()
    })

    // Start periodic session checks
    this.checkIntervalId = window.setInterval(() => {
      this.checkSession()
    }, this.CHECK_INTERVAL)

    console.log('✅ SessionManager: Session management started')
  }

  /**
   * Stop session management
   */
  stop(): void {
    console.log('🛑 SessionManager: Stopping session management')

    this.state.value.isActive = false
    this.state.value.showWarning = false

    activityTracker.stop()

    if (this.checkIntervalId !== null) {
      clearInterval(this.checkIntervalId)
      this.checkIntervalId = null
    }
  }

  /**
   * Handle user activity
   */
  private async handleActivity(): Promise<void> {
    // If warning is shown and user is active, refresh the token
    if (this.state.value.showWarning) {
      await this.extendSession()
    }
  }

  /**
   * Check session status and handle warnings/timeouts
   */
  private async checkSession(): Promise<void> {
    if (!this.state.value.isActive) {
      return
    }

    // Check if session timed out
    if (activityTracker.isTimedOut()) {
      console.warn('⚠️ SessionManager: Session timed out due to inactivity')
      this.handleSessionExpired()
      return
    }

    // Check if warning should be shown
    if (activityTracker.shouldShowWarning()) {
      const timeUntilTimeout = Math.ceil(activityTracker.getTimeUntilTimeout() / 1000)
      console.warn(`⚠️ SessionManager: Showing session warning (${timeUntilTimeout}s remaining)`)

      this.state.value.showWarning = true
      this.state.value.timeRemaining = timeUntilTimeout
      activityTracker.markWarningShown()
    }

    // Update time remaining if warning is shown
    if (this.state.value.showWarning) {
      this.state.value.timeRemaining = Math.ceil(activityTracker.getTimeUntilTimeout() / 1000)
    }
  }

  /**
   * Extend the session (called when user clicks "Continue")
   */
  async extendSession(): Promise<void> {
    console.log('🔄 SessionManager: Extending session...')

    try {
      // Refresh the token on backend
      const response = await authApi.refreshToken()
      secureStorage.setToken(response.access_token)

      // Reset activity tracker
      activityTracker.resetActivity()

      // Hide warning
      this.state.value.showWarning = false
      this.state.value.timeRemaining = 0

      console.log('✅ SessionManager: Session extended successfully')
    } catch (error) {
      console.error('❌ SessionManager: Failed to extend session:', error)
      // If refresh fails, trigger session expired
      this.handleSessionExpired()
    }
  }

  /**
   * Handle session expiration
   */
  private handleSessionExpired(): void {
    console.warn('⚠️ SessionManager: Session expired')

    this.stop()
    this.state.value.showWarning = false

    // Call the expiration callback
    if (this.onSessionExpiredCallback) {
      this.onSessionExpiredCallback()
    }
  }

  /**
   * Register callback for session expiration
   */
  onSessionExpired(callback: () => void): void {
    this.onSessionExpiredCallback = callback
  }

  /**
   * Dismiss the warning (user clicked "Logout")
   */
  dismissWarning(): void {
    console.log('🔐 SessionManager: User dismissed warning, logging out')
    this.handleSessionExpired()
  }

  /**
   * Get current session config
   */
  getConfig() {
    return {
      ...activityTracker.getConfig(),
      checkInterval: this.CHECK_INTERVAL,
    }
  }
}

// Create singleton instance
const sessionManager = new SessionManager()

export default sessionManager
export { SessionManager }
