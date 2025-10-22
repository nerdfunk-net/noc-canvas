<template>
  <div class="space-y-6">
    <!-- Nautobot Plugin -->
    <div class="card p-6">
      <div class="mb-4">
        <h2 class="text-lg font-semibold text-gray-900">Nautobot Integration</h2>
        <p class="text-sm text-gray-600 mt-1">Configure connection to your Nautobot instance</p>
      </div>
      <div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              URL <span class="text-red-500">*</span>
            </label>
            <input
              v-model="nautobotSettings.url"
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
              v-model="nautobotSettings.token"
              type="password"
              placeholder="Enter API Token"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <div>
            <label class="flex items-center">
              <input
                v-model="nautobotSettings.verifyTls"
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
              v-model.number="nautobotSettings.timeout"
              type="number"
              min="5"
              max="300"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        </div>
        <div class="mt-4 flex space-x-3">
          <button
            @click="$emit('test-connection', 'nautobot')"
            class="btn-secondary"
            :disabled="testingConnection.nautobot"
          >
            <i class="fas fa-plug mr-2"></i>
            {{ testingConnection.nautobot ? 'Testing...' : 'Test Connection' }}
          </button>
          <div v-if="connectionStatus.nautobot" class="flex items-center">
            <i
              :class="
                connectionStatus.nautobot.success
                  ? 'fas fa-check-circle text-green-500'
                  : 'fas fa-times-circle text-red-500'
              "
              class="mr-2"
            ></i>
            <span
              :class="connectionStatus.nautobot.success ? 'text-green-700' : 'text-red-700'"
              class="text-sm"
            >
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
          <input v-model="checkmkSettings.enabled" type="checkbox" class="sr-only peer" />
          <div
            class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"
          ></div>
          <span class="ml-3 text-sm font-medium text-gray-700">Enable Plugin</span>
        </label>
      </div>
      <div :class="{ 'opacity-50 pointer-events-none': !checkmkSettings.enabled }">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              URL <span class="text-red-500">*</span>
            </label>
            <input
              v-model="checkmkSettings.url"
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
              v-model="checkmkSettings.site"
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
              v-model="checkmkSettings.username"
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
              v-model="checkmkSettings.password"
              type="password"
              placeholder="Password"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <div class="md:col-span-2">
            <label class="flex items-center">
              <input
                v-model="checkmkSettings.verifyTls"
                type="checkbox"
                class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span class="ml-2 text-sm text-gray-700">Verify TLS Certificate</span>
            </label>
          </div>
        </div>
        <div class="mt-4 flex space-x-3">
          <button
            @click="$emit('test-connection', 'checkmk')"
            class="btn-secondary"
            :disabled="testingConnection.checkmk"
          >
            <i class="fas fa-plug mr-2"></i>
            {{ testingConnection.checkmk ? 'Testing...' : 'Test Connection' }}
          </button>
          <div v-if="connectionStatus.checkmk" class="flex items-center">
            <i
              :class="
                connectionStatus.checkmk.success
                  ? 'fas fa-check-circle text-green-500'
                  : 'fas fa-times-circle text-red-500'
              "
              class="mr-2"
            ></i>
            <span
              :class="connectionStatus.checkmk.success ? 'text-green-700' : 'text-red-700'"
              class="text-sm"
            >
              {{ connectionStatus.checkmk.message }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Netmiko Plugin -->
    <div class="card p-6">
      <div class="mb-4">
        <h2 class="text-lg font-semibold text-gray-900">Netmiko Integration</h2>
        <p class="text-sm text-gray-600 mt-1">Configure SSH connection timeout settings for network devices</p>
      </div>
      <div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Read Timeout (seconds)
            </label>
            <input
              v-model.number="netmikoSettings.readTimeout"
              type="number"
              min="1"
              max="300"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
            <p class="mt-1 text-xs text-gray-500">Default: 10 seconds</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Last Read (seconds)
            </label>
            <input
              v-model.number="netmikoSettings.lastRead"
              type="number"
              min="1"
              max="300"
              placeholder="None (optional)"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
            <p class="mt-1 text-xs text-gray-500">Optional timeout for last read</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Connection Timeout (seconds)
            </label>
            <input
              v-model.number="netmikoSettings.connTimeout"
              type="number"
              min="1"
              max="300"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
            <p class="mt-1 text-xs text-gray-500">Default: 10 seconds</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Auth Timeout (seconds)
            </label>
            <input
              v-model.number="netmikoSettings.authTimeout"
              type="number"
              min="1"
              max="300"
              placeholder="None (optional)"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
            <p class="mt-1 text-xs text-gray-500">Optional timeout for authentication</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Banner Timeout (seconds)
            </label>
            <input
              v-model.number="netmikoSettings.bannerTimeout"
              type="number"
              min="1"
              max="300"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
            <p class="mt-1 text-xs text-gray-500">Default: 15 seconds</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Blocking Timeout (seconds)
            </label>
            <input
              v-model.number="netmikoSettings.blockingTimeout"
              type="number"
              min="1"
              max="300"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
            <p class="mt-1 text-xs text-gray-500">Default: 20 seconds</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Timeout (seconds)
            </label>
            <input
              v-model.number="netmikoSettings.timeout"
              type="number"
              min="1"
              max="600"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
            <p class="mt-1 text-xs text-gray-500">Default: 100 seconds</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Session Timeout (seconds)
            </label>
            <input
              v-model.number="netmikoSettings.sessionTimeout"
              type="number"
              min="1"
              max="600"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
            <p class="mt-1 text-xs text-gray-500">Default: 60 seconds</p>
          </div>
        </div>
        <div class="mt-4 bg-blue-50 border border-blue-200 rounded-md p-4">
          <div class="flex">
            <i class="fas fa-info-circle text-blue-400 mt-0.5 mr-3"></i>
            <div class="text-sm text-blue-700">
              <p class="font-medium">Netmiko Connection Settings</p>
              <p>
                Configure timeout settings for SSH connections to network devices. These settings affect how long Netmiko waits for various operations before timing out.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { toRefs } from 'vue'

interface NautobotSettings {
  url: string
  token: string
  verifyTls: boolean
  timeout: number
}

interface CheckmkSettings {
  enabled: boolean
  url: string
  site: string
  username: string
  password: string
  verifyTls: boolean
}

interface NetmikoSettings {
  readTimeout: number
  lastRead: number | null
  connTimeout: number
  authTimeout: number | null
  bannerTimeout: number
  blockingTimeout: number
  timeout: number
  sessionTimeout: number
}

interface Props {
  nautobotSettings: NautobotSettings
  checkmkSettings: CheckmkSettings
  netmikoSettings: NetmikoSettings
  testingConnection: {
    nautobot: boolean
    checkmk: boolean
  }
  connectionStatus: {
    nautobot: { success: boolean; message: string } | null
    checkmk: { success: boolean; message: string } | null
  }
}

const props = defineProps<Props>()
const { nautobotSettings, checkmkSettings, netmikoSettings } = toRefs(props)

defineEmits<{
  'test-connection': [service: 'nautobot' | 'checkmk']
}>()
</script>
