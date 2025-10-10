import { makeAuthenticatedRequest } from './api'

/**
 * Token Keep-Alive Service
 * 
 * Automatically refreshes the authentication token before it expires
 * to maintain user session while they're actively using the app.
 * 
 * - Refreshes token every 20 minutes (before the 30-minute expiration)
 * - Only runs when user is active (detects mouse/keyboard activity)
 * - Automatically pauses during inactivity to save resources
 */

const REFRESH_INTERVAL = 20 * 60 * 1000 // 20 minutes in milliseconds
const ACTIVITY_TIMEOUT = 5 * 60 * 1000 // 5 minutes of inactivity before pausing

class TokenKeepAliveService {
  private refreshTimer: number | null = null
  private activityTimer: number | null = null
  private lastActivityTime: number = Date.now()
  private isActive: boolean = true
  private isRunning: boolean = false

  /**
   * Start the keep-alive service
   */
  start() {
    if (this.isRunning) {
      console.log('🔄 Token keep-alive already running')
      return
    }

    this.isRunning = true
    this.isActive = true
    this.lastActivityTime = Date.now()

    console.log('✅ Token keep-alive service started')

    // Start the refresh timer
    this.scheduleRefresh()

    // Listen for user activity
    this.setupActivityListeners()

    // Monitor for inactivity
    this.startActivityMonitor()
  }

  /**
   * Stop the keep-alive service
   */
  stop() {
    if (!this.isRunning) {
      return
    }

    console.log('🛑 Token keep-alive service stopped')

    this.isRunning = false
    this.clearRefreshTimer()
    this.clearActivityTimer()
    this.removeActivityListeners()
  }

  /**
   * Schedule the next token refresh
   */
  private scheduleRefresh() {
    this.clearRefreshTimer()

    this.refreshTimer = window.setTimeout(async () => {
      if (this.isActive && this.isRunning) {
        await this.refreshToken()
      }
      
      // Schedule next refresh if still running
      if (this.isRunning) {
        this.scheduleRefresh()
      }
    }, REFRESH_INTERVAL)
  }

  /**
   * Refresh the authentication token
   */
  private async refreshToken() {
    try {
      console.log('🔄 Auto-refreshing token...')
      
      const response = await makeAuthenticatedRequest('/api/auth/refresh', {
        method: 'POST',
      })

      if (response.ok) {
        await response.json() // Token is already stored by makeAuthenticatedRequest
        console.log('✅ Token refreshed successfully')
      } else {
        console.warn('⚠️ Token refresh failed:', response.status)
      }
    } catch (error) {
      console.error('❌ Error refreshing token:', error)
    }
  }

  /**
   * Record user activity
   */
  private recordActivity = () => {
    this.lastActivityTime = Date.now()
    
    if (!this.isActive) {
      console.log('👤 User activity detected - resuming token refresh')
      this.isActive = true
    }
  }

  /**
   * Setup event listeners for user activity
   */
  private setupActivityListeners() {
    window.addEventListener('mousemove', this.recordActivity)
    window.addEventListener('mousedown', this.recordActivity)
    window.addEventListener('keydown', this.recordActivity)
    window.addEventListener('scroll', this.recordActivity)
    window.addEventListener('touchstart', this.recordActivity)
  }

  /**
   * Remove activity event listeners
   */
  private removeActivityListeners() {
    window.removeEventListener('mousemove', this.recordActivity)
    window.removeEventListener('mousedown', this.recordActivity)
    window.removeEventListener('keydown', this.recordActivity)
    window.removeEventListener('scroll', this.recordActivity)
    window.removeEventListener('touchstart', this.recordActivity)
  }

  /**
   * Monitor for user inactivity
   */
  private startActivityMonitor() {
    this.clearActivityTimer()

    this.activityTimer = window.setInterval(() => {
      const timeSinceActivity = Date.now() - this.lastActivityTime

      if (timeSinceActivity > ACTIVITY_TIMEOUT && this.isActive) {
        console.log('💤 User inactive - pausing token refresh')
        this.isActive = false
      }
    }, 60 * 1000) // Check every minute
  }

  /**
   * Clear the refresh timer
   */
  private clearRefreshTimer() {
    if (this.refreshTimer !== null) {
      clearTimeout(this.refreshTimer)
      this.refreshTimer = null
    }
  }

  /**
   * Clear the activity timer
   */
  private clearActivityTimer() {
    if (this.activityTimer !== null) {
      clearInterval(this.activityTimer)
      this.activityTimer = null
    }
  }
}

// Export singleton instance
export const tokenKeepAlive = new TokenKeepAliveService()
