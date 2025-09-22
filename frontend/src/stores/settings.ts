import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { makeAuthenticatedRequest } from '@/services/api'

export interface NautobotSettings {
  enabled: boolean
  url: string
  token: string
  verifyTls: boolean
  timeout: number
}

export interface CheckMKSettings {
  enabled: boolean
  url: string
  site: string
  username: string
  password: string
  verifyTls: boolean
}

export interface CanvasSettings {
  autoSaveInterval: number
  gridEnabled: boolean
}

export interface DatabaseSettings {
  host: string
  port: number
  database: string
  username: string
  password: string
  ssl: boolean
}

export interface Settings {
  nautobot: NautobotSettings
  checkmk: CheckMKSettings
  canvas: CanvasSettings
  database: DatabaseSettings
}

export const useSettingsStore = defineStore('settings', () => {
  const loading = ref(false)

  const settings = reactive<Settings>({
    nautobot: {
      enabled: false,
      url: '',
      token: '',
      verifyTls: true,
      timeout: 30,
    },
    checkmk: {
      enabled: false,
      url: '',
      site: 'cmk',
      username: '',
      password: '',
      verifyTls: true,
    },
    canvas: {
      autoSaveInterval: 60,
      gridEnabled: true,
    },
    database: {
      host: '',
      port: 5432,
      database: 'noc_canvas',
      username: '',
      password: '',
      ssl: false,
    },
  })

  // Load settings from API
  const loadSettings = async () => {
    loading.value = true
    try {
      const response = await makeAuthenticatedRequest('/api/settings/unified')

      if (response.ok) {
        const data = await response.json()
        Object.assign(settings, data)
      } else {
        // Fallback to localStorage
        const saved = localStorage.getItem('noc-canvas-settings')
        if (saved) {
          Object.assign(settings, JSON.parse(saved))
        }
      }
    } catch (error) {
      console.error('Failed to load settings:', error)
      // Fallback to localStorage
      const saved = localStorage.getItem('noc-canvas-settings')
      if (saved) {
        Object.assign(settings, JSON.parse(saved))
      }
    } finally {
      loading.value = false
    }
  }

  // Save settings to API
  const saveSettings = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/settings/unified', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token') || ''}`,
        },
        body: JSON.stringify(settings),
      })

      if (response.ok) {
        localStorage.setItem('noc-canvas-settings', JSON.stringify(settings))
        return { success: true }
      } else {
        throw new Error('Failed to save settings')
      }
    } catch (error) {
      console.error('Failed to save settings:', error)
      return { success: false, error }
    }
  }

  return {
    settings,
    loading,
    loadSettings,
    saveSettings,
  }
})
