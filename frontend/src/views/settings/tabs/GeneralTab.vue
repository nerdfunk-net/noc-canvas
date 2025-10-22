<template>
  <div class="space-y-6">
    <!-- Canvas Settings -->
    <div class="card p-6">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Canvas Settings</h2>
      <div class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 items-end">
          <div>
            <label class="flex items-center">
              <input
                v-model="canvasSettings.autoSaveEnabled"
                type="checkbox"
                class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span class="ml-2 text-sm text-gray-700">Enable Autosave</span>
            </label>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Auto-Save Interval (seconds)
            </label>
            <input
              v-model.number="canvasSettings.autoSaveInterval"
              type="number"
              min="30"
              step="10"
              :disabled="!canvasSettings.autoSaveEnabled"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Database Settings -->
    <div class="card p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-900">Database Configuration</h2>
        <div class="flex items-center space-x-3">
          <span class="text-sm text-gray-500">PostgreSQL Required</span>
          <button
            @click="testDatabaseConnection"
            :disabled="testingDatabase"
            class="px-3 py-1 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50"
          >
            {{ testingDatabase ? 'Testing...' : 'Test Connection' }}
          </button>
        </div>
      </div>
      <div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Host/IP Address <span class="text-red-500">*</span>
            </label>
            <input
              v-model="databaseSettings.host"
              type="text"
              placeholder="192.168.1.100 or db.example.com"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2"> Port </label>
            <input
              v-model.number="databaseSettings.port"
              type="number"
              min="1"
              max="65535"
              placeholder="5432"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Database Name <span class="text-red-500">*</span>
            </label>
            <input
              v-model="databaseSettings.database"
              type="text"
              placeholder="noc_canvas"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Username <span class="text-red-500">*</span>
            </label>
            <input
              v-model="databaseSettings.username"
              type="text"
              placeholder="database_user"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <div class="md:col-span-2">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Password <span class="text-red-500">*</span>
            </label>
            <input
              v-model="databaseSettings.password"
              type="password"
              placeholder="Enter database password"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <div class="md:col-span-2">
            <label class="flex items-center">
              <input
                v-model="databaseSettings.ssl"
                type="checkbox"
                class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span class="ml-2 text-sm text-gray-700">Use SSL Connection</span>
            </label>
          </div>
        </div>
        <div class="mt-4 flex space-x-3">
          <button
            @click="testDatabaseConnection"
            class="btn-secondary"
            :disabled="testingDatabase"
          >
            <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 7v10c0 2.21 1.79 4 4 4h8c0-2.21-1.79-4-4-4H4V7z"
              />
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 7c0-2.21 1.79-4 4-4h8c2.21 0 4 1.79 4 4v10c0 2.21-1.79 4-4 4"
              />
            </svg>
            {{ testingDatabase ? 'Testing...' : 'Test Connection' }}
          </button>
          <div v-if="databaseConnectionStatus" class="flex items-center">
            <i
              :class="
                databaseConnectionStatus.success
                  ? 'fas fa-check-circle text-green-500'
                  : 'fas fa-times-circle text-red-500'
              "
              class="mr-2"
            ></i>
            <span
              :class="databaseConnectionStatus.success ? 'text-green-700' : 'text-red-700'"
              class="text-sm"
            >
              {{ databaseConnectionStatus.message }}
            </span>
          </div>
        </div>
        <div class="mt-4 bg-amber-50 border border-amber-200 rounded-md p-4">
          <div class="flex">
            <svg
              class="w-5 h-5 text-amber-400 mt-0.5 mr-3"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 19.5c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
            <div class="text-sm text-amber-700">
              <p class="font-medium">Database Configuration</p>
              <p>
                Configure your external database connection for storing application data.
                Supports PostgreSQL, MySQL, and other SQL databases.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, toRefs } from 'vue'
import { useNotificationStore } from '@/stores/notification'
import { makeAuthenticatedRequest } from '@/services/api'

interface Props {
  canvasSettings: {
    autoSaveEnabled: boolean
    autoSaveInterval: number
  }
  databaseSettings: {
    host: string
    port: number
    database: string
    username: string
    password: string
    ssl: boolean
  }
}

const props = defineProps<Props>()
const notificationStore = useNotificationStore()

const testingDatabase = ref(false)
const databaseConnectionStatus = ref<{ success: boolean; message: string } | null>(null)

// Make props reactive for v-model
const { canvasSettings, databaseSettings } = toRefs(props)

const testDatabaseConnection = async () => {
  testingDatabase.value = true
  databaseConnectionStatus.value = null

  try {
    const response = await makeAuthenticatedRequest('/api/settings/test-connection/database', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        host: databaseSettings.value.host,
        port: databaseSettings.value.port,
        database: databaseSettings.value.database,
        username: databaseSettings.value.username,
        password: databaseSettings.value.password,
        ssl: databaseSettings.value.ssl,
      })
    })

    if (response.ok) {
      const data = await response.json()
      databaseConnectionStatus.value = {
        success: data.success,
        message: data.message || (data.success ? 'Connection successful!' : 'Connection failed')
      }

      notificationStore.addNotification({
        title: data.success ? 'Database Connection Successful' : 'Database Connection Failed',
        message: data.message,
        type: data.success ? 'success' : 'error',
      })
    } else {
      throw new Error('Failed to test connection')
    }
  } catch (error) {
    const message = 'Failed to test database connection. Please check your settings.'
    databaseConnectionStatus.value = {
      success: false,
      message
    }
    notificationStore.addNotification({
      title: 'Connection Test Error',
      message,
      type: 'error',
    })
    console.error('Failed to test database connection:', error)
  } finally {
    testingDatabase.value = false
  }
}
</script>
