<template>
  <div class="h-full flex flex-col bg-white border-r border-gray-200">
    <!-- Nautobot Section (shown when nautobot plugin is enabled) -->
    <div v-if="settingsStore.settings.nautobot.enabled" class="flex-1 flex flex-col">
      <div class="p-3 border-b border-gray-200 bg-gray-50">
        <h3 class="text-sm font-medium text-gray-700 flex items-center">
          <svg
            class="w-4 h-4 mr-2 text-blue-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"
            />
          </svg>
          Inventory
        </h3>
      </div>

      <!-- Device Tree Component -->
      <div class="flex-1 min-h-0">
        <DeviceTree
          ref="deviceTreeRef"
          @device-selected="onDeviceSelected"
          @device-added-to-canvas="onDeviceAddedToCanvas"
        />
      </div>
    </div>

    <!-- Nautobot Not Enabled Message -->
    <div
      v-else-if="!settingsStore.settings.nautobot.enabled && settingsStore.settings.nautobot.url"
      class="flex-1 flex items-center justify-center"
    >
      <div class="text-center px-4">
        <svg
          class="w-8 h-8 mx-auto mb-3 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"
          />
        </svg>
        <p class="text-sm font-medium text-gray-600 mb-2">Plugin Disabled</p>
        <router-link to="/settings" class="text-xs text-blue-600 hover:text-blue-800">
          Enable in Settings
        </router-link>
      </div>
    </div>

    <!-- Nautobot Not Configured Message -->
    <div
      v-else-if="!settingsStore.settings.nautobot.url"
      class="flex-1 flex items-center justify-center"
    >
      <div class="text-center px-4">
        <svg
          class="w-8 h-8 mx-auto mb-3 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
          />
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
        <p class="text-sm font-medium text-gray-600 mb-2">Not Configured</p>
        <router-link to="/settings" class="text-xs text-blue-600 hover:text-blue-800">
          Configure Settings
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { type NautobotDevice } from '@/services/api'
import DeviceTree from './DeviceTree.vue'

const settingsStore = useSettingsStore()

const deviceTreeRef = ref<InstanceType<typeof DeviceTree> | null>(null)

// Event handlers for DeviceTree
const onDeviceSelected = (device: NautobotDevice) => {
  console.log('Selected nautobot device:', device)
  // TODO: Implement device selection logic (e.g., show device details)
}

const onDeviceAddedToCanvas = (device: NautobotDevice) => {
  console.log('Adding device to canvas:', device)
  // TODO: Implement adding device to canvas
  // This could emit an event to the parent component or use a canvas store
}

// Load stores when component mounts
onMounted(async () => {
  await settingsStore.loadSettings()
})
</script>
