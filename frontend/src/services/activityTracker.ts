/**
 * Activity Tracker Service
 *
 * Monitors user activity (mouse movements, keyboard input, API calls)
 * and manages session timeout based on inactivity.
 */

type ActivityCallback = () => void

class ActivityTracker {
  private lastActivityTime: number = Date.now()
  private activityListeners: ActivityCallback[] = []
  private checkIntervalId: number | null = null
  private warningShown: boolean = false

  // Configuration (in milliseconds)
  private readonly INACTIVITY_TIMEOUT = 30 * 60 * 1000 // 30 minutes of inactivity
  private readonly WARNING_BEFORE_TIMEOUT = 2 * 60 * 1000 // Warn 2 minutes before timeout
  private readonly CHECK_INTERVAL = 30 * 1000 // Check every 30 seconds

  constructor() {
    this.resetActivity = this.resetActivity.bind(this)
  }

  /**
   * Start monitoring user activity
   */
  start(): void {
    if (this.checkIntervalId !== null) {
      console.warn('ActivityTracker already started')
      return
    }

    console.log('🔍 ActivityTracker: Starting activity monitoring')
    this.lastActivityTime = Date.now()

    // Listen for user interactions
    window.addEventListener('mousedown', this.resetActivity)
    window.addEventListener('keydown', this.resetActivity)
    window.addEventListener('scroll', this.resetActivity)
    window.addEventListener('touchstart', this.resetActivity)

    // Start periodic inactivity check
    this.checkIntervalId = window.setInterval(() => {
      this.checkInactivity()
    }, this.CHECK_INTERVAL)

    console.log(`✅ ActivityTracker: Monitoring started (timeout: ${this.INACTIVITY_TIMEOUT / 60000} minutes)`)
  }

  /**
   * Stop monitoring user activity
   */
  stop(): void {
    console.log('🛑 ActivityTracker: Stopping activity monitoring')

    window.removeEventListener('mousedown', this.resetActivity)
    window.removeEventListener('keydown', this.resetActivity)
    window.removeEventListener('scroll', this.resetActivity)
    window.removeEventListener('touchstart', this.resetActivity)

    if (this.checkIntervalId !== null) {
      clearInterval(this.checkIntervalId)
      this.checkIntervalId = null
    }
  }

  /**
   * Reset activity timer (called on user interaction)
   */
  resetActivity(): void {
    const now = Date.now()
    const wasInactive = this.getInactivityDuration() > this.INACTIVITY_TIMEOUT

    this.lastActivityTime = now
    this.warningShown = false

    if (wasInactive) {
      console.log('✅ ActivityTracker: User active again after timeout period')
    }

    // Notify listeners about activity
    this.notifyActivityListeners()
  }

  /**
   * Get duration of inactivity in milliseconds
   */
  getInactivityDuration(): number {
    return Date.now() - this.lastActivityTime
  }

  /**
   * Get time until timeout in milliseconds
   */
  getTimeUntilTimeout(): number {
    return Math.max(0, this.INACTIVITY_TIMEOUT - this.getInactivityDuration())
  }

  /**
   * Get time until warning in milliseconds
   */
  getTimeUntilWarning(): number {
    const timeUntilTimeout = this.getTimeUntilTimeout()
    return Math.max(0, timeUntilTimeout - this.WARNING_BEFORE_TIMEOUT)
  }

  /**
   * Check if user should be warned about inactivity
   */
  shouldShowWarning(): boolean {
    const timeUntilTimeout = this.getTimeUntilTimeout()
    return timeUntilTimeout > 0 &&
           timeUntilTimeout <= this.WARNING_BEFORE_TIMEOUT &&
           !this.warningShown
  }

  /**
   * Check if session has timed out due to inactivity
   */
  isTimedOut(): boolean {
    return this.getTimeUntilTimeout() === 0
  }

  /**
   * Mark warning as shown
   */
  markWarningShown(): void {
    this.warningShown = true
  }

  /**
   * Register callback for activity events
   */
  onActivity(callback: ActivityCallback): void {
    this.activityListeners.push(callback)
  }

  /**
   * Unregister activity callback
   */
  offActivity(callback: ActivityCallback): void {
    const index = this.activityListeners.indexOf(callback)
    if (index > -1) {
      this.activityListeners.splice(index, 1)
    }
  }

  /**
   * Notify all activity listeners
   */
  private notifyActivityListeners(): void {
    this.activityListeners.forEach(callback => {
      try {
        callback()
      } catch (error) {
        console.error('Error in activity callback:', error)
      }
    })
  }

  /**
   * Check for inactivity and trigger warning/timeout
   */
  private checkInactivity(): void {
    const inactivityDuration = this.getInactivityDuration()
    const timeUntilTimeout = this.getTimeUntilTimeout()

    if (this.isTimedOut()) {
      console.warn('⚠️ ActivityTracker: Session timed out due to inactivity')
      // Timeout will be handled by the session manager
    } else if (this.shouldShowWarning()) {
      console.warn(`⚠️ ActivityTracker: Warning - session expires in ${Math.ceil(timeUntilTimeout / 1000)} seconds`)
      // Warning will be handled by the session manager
    }
  }

  /**
   * Get configuration values
   */
  getConfig() {
    return {
      inactivityTimeout: this.INACTIVITY_TIMEOUT,
      warningBeforeTimeout: this.WARNING_BEFORE_TIMEOUT,
      checkInterval: this.CHECK_INTERVAL,
    }
  }
}

// Create singleton instance
const activityTracker = new ActivityTracker()

export default activityTracker
export { ActivityTracker }
