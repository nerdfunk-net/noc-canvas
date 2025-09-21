import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/services/api'

export interface User {
  id: number
  username: string
  is_active: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))

  const isAuthenticated = computed(() => !!token.value && !!user.value)

  const login = async (username: string, password: string) => {
    try {
      const response = await authApi.login(username, password)
      token.value = response.access_token
      localStorage.setItem('token', response.access_token)

      // Get user info
      const userInfo = await authApi.getMe()
      user.value = userInfo

      return true
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }

  const logout = async () => {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
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
