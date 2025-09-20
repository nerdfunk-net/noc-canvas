<template>
  <MainLayout>
    <div class="p-6">
      <div class="max-w-6xl mx-auto">
        <h1 class="text-2xl font-bold text-gray-900 mb-6">Settings</h1>

        <!-- Tab Navigation -->
        <div class="border-b border-gray-200 mb-6">
          <nav class="-mb-px flex space-x-8">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="[
                'py-2 px-1 border-b-2 font-medium text-sm transition-colors',
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              ]"
            >
              <i :class="tab.icon" class="mr-2"></i>
              {{ tab.name }}
            </button>
          </nav>
        </div>

        <!-- Tab Content -->
        <div class="space-y-6">
          <!-- General Tab -->
          <div v-if="activeTab === 'general'" class="space-y-6">
            <!-- Canvas Settings -->
            <div class="card p-6">
              <h2 class="text-lg font-semibold text-gray-900 mb-4">Canvas Settings</h2>
              <div class="space-y-4">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label class="flex items-center mb-4">
                      <input
                        v-model="settings.canvas.gridEnabled"
                        type="checkbox"
                        class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                      />
                      <span class="ml-2 text-sm text-gray-700">Enable Grid Snap</span>
                    </label>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                      Auto-Save Interval (seconds)
                    </label>
                    <input
                      v-model.number="settings.canvas.autoSaveInterval"
                      type="number"
                      min="30"
                      step="10"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                </div>
                <div class="bg-blue-50 border border-blue-200 rounded-md p-4">
                  <div class="flex">
                    <i class="fas fa-info-circle text-blue-400 mt-0.5 mr-3"></i>
                    <div class="text-sm text-blue-700">
                      <p class="font-medium">Canvas Size</p>
                      <p>The canvas size is unlimited and will automatically adjust based on your content.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Plugins Tab -->
          <div v-if="activeTab === 'plugins'" class="space-y-6">
            <!-- Nautobot Plugin -->
            <div class="card p-6">
              <div class="flex items-center justify-between mb-4">
                <h2 class="text-lg font-semibold text-gray-900">Nautobot Integration</h2>
                <label class="relative inline-flex items-center cursor-pointer">
                  <input
                    v-model="settings.nautobot.enabled"
                    type="checkbox"
                    class="sr-only peer"
                  />
                  <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                  <span class="ml-3 text-sm font-medium text-gray-700">Enable Plugin</span>
                </label>
              </div>
              <div :class="{ 'opacity-50 pointer-events-none': !settings.nautobot.enabled }">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                      URL <span class="text-red-500">*</span>
                    </label>
                    <input
                      v-model="settings.nautobot.url"
                      type="url"
                      placeholder="https://nautobot.example.com"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                      API Token <span class="text-red-500">*</span>
                    </label>
                    <input
                      v-model="settings.nautobot.token"
                      type="password"
                      placeholder="Enter API Token"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div>
                    <label class="flex items-center">
                      <input
                        v-model="settings.nautobot.verifyTls"
                        type="checkbox"
                        class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                      />
                      <span class="ml-2 text-sm text-gray-700">Verify TLS Certificate</span>
                    </label>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                      Timeout (seconds)
                    </label>
                    <input
                      v-model.number="settings.nautobot.timeout"
                      type="number"
                      min="5"
                      max="300"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                </div>
                <div class="mt-4 flex space-x-3">
                  <button
                    @click="testConnection('nautobot')"
                    class="btn-secondary"
                    :disabled="testingConnection.nautobot"
                  >
                    <i class="fas fa-plug mr-2"></i>
                    {{ testingConnection.nautobot ? 'Testing...' : 'Test Connection' }}
                  </button>
                  <div v-if="connectionStatus.nautobot" class="flex items-center">
                    <i :class="connectionStatus.nautobot.success ? 'fas fa-check-circle text-green-500' : 'fas fa-times-circle text-red-500'" class="mr-2"></i>
                    <span :class="connectionStatus.nautobot.success ? 'text-green-700' : 'text-red-700'" class="text-sm">
                      {{ connectionStatus.nautobot.message }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- CheckMK Plugin -->
            <div class="card p-6">
              <div class="flex items-center justify-between mb-4">
                <h2 class="text-lg font-semibold text-gray-900">CheckMK Integration</h2>
                <label class="relative inline-flex items-center cursor-pointer">
                  <input
                    v-model="settings.checkmk.enabled"
                    type="checkbox"
                    class="sr-only peer"
                  />
                  <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                  <span class="ml-3 text-sm font-medium text-gray-700">Enable Plugin</span>
                </label>
              </div>
              <div :class="{ 'opacity-50 pointer-events-none': !settings.checkmk.enabled }">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                      URL <span class="text-red-500">*</span>
                    </label>
                    <input
                      v-model="settings.checkmk.url"
                      type="url"
                      placeholder="https://checkmk.example.com"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                      Site <span class="text-red-500">*</span>
                    </label>
                    <input
                      v-model="settings.checkmk.site"
                      type="text"
                      placeholder="cmk"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                      Username <span class="text-red-500">*</span>
                    </label>
                    <input
                      v-model="settings.checkmk.username"
                      type="text"
                      placeholder="Username"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                      Password <span class="text-red-500">*</span>
                    </label>
                    <input
                      v-model="settings.checkmk.password"
                      type="password"
                      placeholder="Password"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div class="md:col-span-2">
                    <label class="flex items-center">
                      <input
                        v-model="settings.checkmk.verifyTls"
                        type="checkbox"
                        class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                      />
                      <span class="ml-2 text-sm text-gray-700">Verify TLS Certificate</span>
                    </label>
                  </div>
                </div>
                <div class="mt-4 flex space-x-3">
                  <button
                    @click="testConnection('checkmk')"
                    class="btn-secondary"
                    :disabled="testingConnection.checkmk"
                  >
                    <i class="fas fa-plug mr-2"></i>
                    {{ testingConnection.checkmk ? 'Testing...' : 'Test Connection' }}
                  </button>
                  <div v-if="connectionStatus.checkmk" class="flex items-center">
                    <i :class="connectionStatus.checkmk.success ? 'fas fa-check-circle text-green-500' : 'fas fa-times-circle text-red-500'" class="mr-2"></i>
                    <span :class="connectionStatus.checkmk.success ? 'text-green-700' : 'text-red-700'" class="text-sm">
                      {{ connectionStatus.checkmk.message }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Profile Tab -->
          <div v-if="activeTab === 'profile'" class="space-y-6">
            <!-- Personal Credentials -->
            <div class="card p-6">
              <div class="flex items-center justify-between mb-4">
                <h2 class="text-lg font-semibold text-gray-900">Personal Credentials</h2>
                <div class="flex items-center space-x-2">
                  <button
                    @click="addCredential"
                    class="w-8 h-8 bg-green-600 hover:bg-green-700 text-white rounded-full flex items-center justify-center transition-colors font-bold text-lg"
                    title="Add credential"
                  >
                    +
                  </button>
                  <button
                    @click="removeLastCredential"
                    :disabled="settings.credentials.length === 0"
                    class="w-8 h-8 bg-red-600 hover:bg-red-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-full flex items-center justify-center transition-colors font-bold text-lg"
                    title="Remove last credential"
                  >
                    −
                  </button>
                </div>
              </div>
              <div class="space-y-3">
                <div
                  v-for="(credential, index) in settings.credentials"
                  :key="index"
                  class="border border-gray-200 rounded-lg p-3 bg-gray-50"
                >
                  <div class="flex items-center justify-between mb-3">
                    <span class="text-sm font-medium text-gray-600">Credential {{ index + 1 }}</span>
                    <button
                      @click="removeCredential(index)"
                      class="w-6 h-6 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center transition-colors font-bold text-sm"
                      title="Remove this credential"
                    >
                      ×
                    </button>
                  </div>
                  <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div>
                      <label class="block text-xs font-medium text-gray-700 mb-1">
                        Name
                      </label>
                      <input
                        v-model="credential.name"
                        type="text"
                        placeholder="Credential name"
                        class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                    <div>
                      <label class="block text-xs font-medium text-gray-700 mb-1">
                        Username
                      </label>
                      <input
                        v-model="credential.username"
                        type="text"
                        placeholder="Username"
                        class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                    <div>
                      <label class="block text-xs font-medium text-gray-700 mb-1">
                        Password
                      </label>
                      <input
                        v-model="credential.password"
                        type="password"
                        placeholder="Password"
                        class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                  </div>
                </div>
                <div v-if="settings.credentials.length === 0" class="text-center py-6 text-gray-500">
                  <i class="fas fa-key text-3xl mb-3 opacity-50"></i>
                  <p class="text-sm">No credentials added yet. Click the "+" button to add one.</p>
                </div>
              </div>
            </div>

            <!-- Change Password -->
            <div class="card p-6">
              <h2 class="text-lg font-semibold text-gray-900 mb-4">Change Login Password</h2>
              <div class="max-w-md space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Current Password
                  </label>
                  <input
                    v-model="passwordChange.currentPassword"
                    type="password"
                    placeholder="Enter current password"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    New Password
                  </label>
                  <input
                    v-model="passwordChange.newPassword"
                    type="password"
                    placeholder="Enter new password"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Confirm New Password
                  </label>
                  <input
                    v-model="passwordChange.confirmPassword"
                    type="password"
                    placeholder="Confirm new password"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
                <button
                  @click="changePassword"
                  class="btn-primary"
                  :disabled="changingPassword || !isPasswordChangeValid"
                >
                  {{ changingPassword ? 'Changing...' : 'Change Password' }}
                </button>
              </div>
            </div>
          </div>

          <!-- Save Button (for General and Plugins tabs) -->
          <div v-if="activeTab !== 'profile'" class="flex justify-end">
            <button
              @click="saveSettings"
              class="btn-primary"
              :disabled="saving"
            >
              <i class="fas fa-save mr-2"></i>
              {{ saving ? 'Saving...' : 'Save Settings' }}
            </button>
          </div>

          <!-- Save Button (for Profile tab) -->
          <div v-if="activeTab === 'profile'" class="flex justify-end">
            <button
              @click="saveProfile"
              class="btn-primary"
              :disabled="savingProfile"
            >
              <i class="fas fa-save mr-2"></i>
              {{ savingProfile ? 'Saving...' : 'Save Credentials' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import MainLayout from '@/layouts/MainLayout.vue'
import { useNotificationStore } from '@/stores/notification'

const notificationStore = useNotificationStore()

const activeTab = ref('general')
const saving = ref(false)
const savingProfile = ref(false)
const changingPassword = ref(false)
const testingConnection = reactive({
  nautobot: false,
  checkmk: false
})
const connectionStatus = reactive({
  nautobot: null as { success: boolean; message: string } | null,
  checkmk: null as { success: boolean; message: string } | null
})

const tabs = [
  { id: 'general', name: 'General', icon: 'fas fa-cog' },
  { id: 'plugins', name: 'Plugins', icon: 'fas fa-plug' },
  { id: 'profile', name: 'Profile', icon: 'fas fa-user' }
]

const settings = reactive({
  nautobot: {
    enabled: false,
    url: '',
    token: '',
    verifyTls: true,
    timeout: 30
  },
  checkmk: {
    enabled: false,
    url: '',
    site: 'cmk',
    username: '',
    password: '',
    verifyTls: true
  },
  canvas: {
    autoSaveInterval: 60,
    gridEnabled: true
  },
  credentials: [] as Array<{
    name: string
    username: string
    password: string
  }>
})

const passwordChange = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const isPasswordChangeValid = computed(() => {
  return passwordChange.currentPassword &&
         passwordChange.newPassword &&
         passwordChange.confirmPassword &&
         passwordChange.newPassword === passwordChange.confirmPassword &&
         passwordChange.newPassword.length >= 6
})

const addCredential = () => {
  settings.credentials.push({
    name: '',
    username: '',
    password: ''
  })
}

const removeCredential = (index: number) => {
  settings.credentials.splice(index, 1)
}

const removeLastCredential = () => {
  if (settings.credentials.length > 0) {
    settings.credentials.pop()
  }
}

const testConnection = async (service: 'nautobot' | 'checkmk') => {
  testingConnection[service] = true
  connectionStatus[service] = null

  try {
    const endpoint = service === 'nautobot' ? '/api/settings/test-nautobot' : '/api/settings/test-checkmk'
    const payload = service === 'nautobot'
      ? {
          url: settings.nautobot.url,
          token: settings.nautobot.token,
          verify_ssl: settings.nautobot.verifyTls,
          timeout: settings.nautobot.timeout
        }
      : {
          url: settings.checkmk.url,
          site: settings.checkmk.site,
          username: settings.checkmk.username,
          password: settings.checkmk.password,
          verify_ssl: settings.checkmk.verifyTls
        }

    const response = await fetch(`http://localhost:8000${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
      },
      body: JSON.stringify(payload)
    })

    const result = await response.json()

    if (response.ok && result.success) {
      connectionStatus[service] = {
        success: true,
        message: result.message || 'Connection successful!'
      }
    } else {
      connectionStatus[service] = {
        success: false,
        message: result.message || result.detail || 'Connection failed'
      }
    }
  } catch (error) {
    connectionStatus[service] = {
      success: false,
      message: `Connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`
    }
  } finally {
    testingConnection[service] = false
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    const response = await fetch('http://localhost:8000/api/settings/unified', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
      },
      body: JSON.stringify({
        nautobot: settings.nautobot,
        checkmk: settings.checkmk,
        canvas: settings.canvas
      })
    })

    if (response.ok) {
      notificationStore.addNotification({
        title: 'Settings Saved',
        message: 'Your settings have been saved successfully.',
        type: 'success'
      })
      localStorage.setItem('noc-canvas-settings', JSON.stringify(settings))
    } else {
      throw new Error('Failed to save settings')
    }
  } catch (error) {
    notificationStore.addNotification({
      title: 'Save Failed',
      message: 'Failed to save settings. Please try again.',
      type: 'error'
    })
    console.error('Failed to save settings:', error)
  } finally {
    saving.value = false
  }
}

const saveProfile = async () => {
  savingProfile.value = true
  try {
    const response = await fetch('http://localhost:8000/api/settings/credentials', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
      },
      body: JSON.stringify({ credentials: settings.credentials })
    })

    if (response.ok) {
      notificationStore.addNotification({
        title: 'Credentials Saved',
        message: 'Your credentials have been saved successfully.',
        type: 'success'
      })
      localStorage.setItem('noc-canvas-credentials', JSON.stringify(settings.credentials))
    } else {
      throw new Error('Failed to save credentials')
    }
  } catch (error) {
    notificationStore.addNotification({
      title: 'Save Failed',
      message: 'Failed to save credentials. Please try again.',
      type: 'error'
    })
    console.error('Failed to save credentials:', error)
  } finally {
    savingProfile.value = false
  }
}

const changePassword = async () => {
  if (!isPasswordChangeValid.value) return

  changingPassword.value = true
  try {
    const response = await fetch('http://localhost:8000/api/auth/change-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
      },
      body: JSON.stringify({
        current_password: passwordChange.currentPassword,
        new_password: passwordChange.newPassword
      })
    })

    if (response.ok) {
      notificationStore.addNotification({
        title: 'Password Changed',
        message: 'Your password has been changed successfully.',
        type: 'success'
      })
      passwordChange.currentPassword = ''
      passwordChange.newPassword = ''
      passwordChange.confirmPassword = ''
    } else {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to change password')
    }
  } catch (error) {
    notificationStore.addNotification({
      title: 'Password Change Failed',
      message: error instanceof Error ? error.message : 'Failed to change password. Please try again.',
      type: 'error'
    })
  } finally {
    changingPassword.value = false
  }
}

// Load settings on component mount
const loadSettings = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/settings/unified', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
      }
    })

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
  }

  // Load credentials
  try {
    const credentialsResponse = await fetch('http://localhost:8000/api/settings/credentials', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
      }
    })

    if (credentialsResponse.ok) {
      const credentialsData = await credentialsResponse.json()
      settings.credentials = credentialsData.credentials || []
    } else {
      // Fallback to localStorage
      const savedCredentials = localStorage.getItem('noc-canvas-credentials')
      if (savedCredentials) {
        settings.credentials = JSON.parse(savedCredentials)
      }
    }
  } catch (error) {
    console.error('Failed to load credentials:', error)
    // Fallback to localStorage
    const savedCredentials = localStorage.getItem('noc-canvas-credentials')
    if (savedCredentials) {
      settings.credentials = JSON.parse(savedCredentials)
    }
  }
}

loadSettings()
</script>