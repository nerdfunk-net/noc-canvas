import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/services/api'
import secureStorage from '@/services/secureStorage'

export interface User {
  id: number
  username: string
  is_active: boolean
  is_admin?: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  // SECURITY: Only use secure storage for token retrieval
  const token = ref<string | null>(secureStorage.getToken())

  const isAuthenticated = computed(() => !!token.value && !!user.value)

  const login = async (username: string, password: string) => {
    try {
      console.log('🔍 Auth: Starting login process...')
      const response = await authApi.login(username, password)
      console.log('✅ Auth: Login API success, got token:', !!response.access_token)
      
      // Store token immediately so getMe() can use it
      token.value = response.access_token
      secureStorage.setToken(response.access_token)

      // Get user info
      console.log('🔍 Auth: Getting user info...')
      const userInfo = await authApi.getMe()
      console.log('✅ Auth: Got user info:', userInfo)
      user.value = userInfo

      // Update stored token with user information
      console.log('🔍 Auth: Updating stored token with user info...')
      secureStorage.setToken(response.access_token, {
        userId: userInfo.id,
        username: userInfo.username,
        isAdmin: userInfo.is_admin,
      })
      console.log('✅ Auth: Login complete!')

      return true
    } catch (error) {
      console.error('❌ Auth: Login failed:', error)
      throw error
    }
  }

  const logout = async () => {
    user.value = null
    token.value = null
    secureStorage.removeToken()
    // Clear autosave check flag so it will be asked again on next login
    sessionStorage.removeItem('noc_canvas_autosave_checked')
  }

  const register = async (username: string, password: string) => {
    try {
      const newUser = await authApi.register(username, password)
      return newUser
    } catch (error) {
      console.error('Registration failed:', error)
      throw error
    }
  }

  const initializeAuth = async () => {
    if (token.value) {
      try {
        const userInfo = await authApi.getMe()
        user.value = userInfo
        
        // Update secure storage with fresh user info
        secureStorage.updateSession({
          userId: userInfo.id,
          username: userInfo.username,
          isAdmin: userInfo.is_admin,
        })
      } catch (error) {
        // Token is invalid, clear it
        logout()
      }
    }
  }

  return {
    user,
    token,
    isAuthenticated,
    login,
    logout,
    register,
    initializeAuth,
  }
})
