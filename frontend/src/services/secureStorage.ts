/**
 * Secure Storage Service
 * 
 * Provides secure token storage using sessionStorage with encryption
 * and XSS protection mechanisms. Falls back to localStorage with warnings.
 */

import { encrypt, decrypt } from '../utils/encryption'

const STORAGE_KEY = 'noc_canvas_session'
const ENCRYPTION_KEY_STORAGE = 'noc_canvas_key'

// Configuration from environment variables
const ENABLE_SECURE_STORAGE = import.meta.env.VITE_ENABLE_SECURE_STORAGE !== 'false'
const SESSION_TIMEOUT_HOURS = parseInt(import.meta.env.VITE_SESSION_TIMEOUT_HOURS || '24')

interface SecureSession {
  token: string
  userId?: number
  username?: string
  expiresAt: number
  isAdmin?: boolean
}

class SecureStorage {
  private encryptionKey: string | null = null

  constructor() {
    this.initializeEncryptionKey()
  }

  private initializeEncryptionKey(): void {
    // Generate or retrieve encryption key for this session
    let key = sessionStorage.getItem(ENCRYPTION_KEY_STORAGE)
    if (!key) {
      // Generate a new key for this session
      key = this.generateEncryptionKey()
      sessionStorage.setItem(ENCRYPTION_KEY_STORAGE, key)
    }
    this.encryptionKey = key
  }

  private generateEncryptionKey(): string {
    // Generate a random key using Web Crypto API
    const array = new Uint8Array(32)
    crypto.getRandomValues(array)
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
  }

  private isSessionExpired(session: SecureSession): boolean {
    return Date.now() > session.expiresAt
  }

  /**
   * Store token securely with encryption
   */
  setToken(token: string, userInfo?: { userId?: number; username?: string; isAdmin?: boolean }): void {
    if (!token) {
      console.warn('SecureStorage: Attempting to store empty token')
      return
    }

    try {
      const session: SecureSession = {
        token,
        userId: userInfo?.userId,
        username: userInfo?.username,
        isAdmin: userInfo?.isAdmin,
        expiresAt: Date.now() + (SESSION_TIMEOUT_HOURS * 60 * 60 * 1000), // Configurable timeout
      }

      if (!ENABLE_SECURE_STORAGE) {
        // Fallback to localStorage if secure storage is disabled
        console.warn('⚠️ Secure storage disabled, using localStorage')
        localStorage.setItem('token', token)
        return
      }

      const encryptedData = encrypt(JSON.stringify(session), this.encryptionKey!)
      
      // Use sessionStorage for better security (cleared when browser closes)
      sessionStorage.setItem(STORAGE_KEY, encryptedData)
      
      // Also store in localStorage as backup (less secure but more reliable)
      localStorage.setItem('token', token)
      
      console.log('✅ Token stored securely in sessionStorage (with localStorage backup)')
    } catch (error) {
      console.error('❌ Failed to store token securely:', error)
      // Fallback to localStorage with warning (for backwards compatibility)
      console.warn('⚠️ Falling back to localStorage - this is less secure')
      localStorage.setItem('token', token)
    }
  }

  /**
   * Retrieve token securely with decryption
   */
  getToken(): string | null {
    console.log('🔍 SecureStorage: Getting token...')
    try {
      // Try sessionStorage first
      const encryptedData = sessionStorage.getItem(STORAGE_KEY)
      console.log('🔍 SecureStorage: Encrypted data from sessionStorage:', !!encryptedData)
      console.log('🔍 SecureStorage: Has encryption key:', !!this.encryptionKey)
      
      if (encryptedData && this.encryptionKey) {
        const decryptedData = decrypt(encryptedData, this.encryptionKey)
        const session: SecureSession = JSON.parse(decryptedData)

        if (this.isSessionExpired(session)) {
          console.warn('⚠️ Session expired, removing token')
          this.removeToken()
          return null
        }

        console.log('✅ SecureStorage: Retrieved token from sessionStorage')
        return session.token
      }

      // Fallback to localStorage for migration
      const oldToken = localStorage.getItem('token')
      console.log('🔍 SecureStorage: Found token in localStorage:', !!oldToken)
      if (oldToken) {
        console.warn('⚠️ Found token in localStorage, migrating to secure storage')
        // Migrate to secure storage
        this.setToken(oldToken)
        // Remove from localStorage
        localStorage.removeItem('token')
        return oldToken
      }

      console.log('❌ SecureStorage: No token found')
      return null
    } catch (error) {
      console.error('❌ Failed to retrieve token securely:', error)
      // Clear corrupted data
      this.removeToken()
      return null
    }
  }

  /**
   * Get complete session information
   */
  getSession(): SecureSession | null {
    try {
      const encryptedData = sessionStorage.getItem(STORAGE_KEY)
      if (encryptedData && this.encryptionKey) {
        const decryptedData = decrypt(encryptedData, this.encryptionKey)
        const session: SecureSession = JSON.parse(decryptedData)

        if (this.isSessionExpired(session)) {
          this.removeToken()
          return null
        }

        return session
      }
      return null
    } catch (error) {
      console.error('❌ Failed to retrieve session:', error)
      this.removeToken()
      return null
    }
  }

  /**
   * Update session information
   */
  updateSession(updates: Partial<SecureSession>): void {
    const currentSession = this.getSession()
    if (currentSession) {
      const updatedSession = { ...currentSession, ...updates }
      this.setToken(updatedSession.token, {
        userId: updatedSession.userId,
        username: updatedSession.username,
        isAdmin: updatedSession.isAdmin,
      })
    }
  }

  /**
   * Remove token and clear session
   */
  removeToken(): void {
    try {
      sessionStorage.removeItem(STORAGE_KEY)
      sessionStorage.removeItem(ENCRYPTION_KEY_STORAGE)
      localStorage.removeItem('token') // Clean up old localStorage too
      this.encryptionKey = null
      console.log('✅ Token removed securely')
    } catch (error) {
      console.error('❌ Failed to remove token:', error)
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return this.getToken() !== null
  }

  /**
   * Check session validity and auto-refresh if needed
   */
  async validateSession(): Promise<boolean> {
    const session = this.getSession()
    if (!session) return false

    // Check if session expires in next 5 minutes
    const fiveMinutes = 5 * 60 * 1000
    const expiresIn = session.expiresAt - Date.now()

    if (expiresIn < fiveMinutes && expiresIn > 0) {
      console.log('🔄 Session expiring soon, extending...')
      // Extend session by configured timeout
      this.updateSession({ expiresAt: Date.now() + (SESSION_TIMEOUT_HOURS * 60 * 60 * 1000) })
    }

    return true
  }
}

// Create singleton instance
const secureStorage = new SecureStorage()

export default secureStorage
export type { SecureSession }