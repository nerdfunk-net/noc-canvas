<template>
  <div class="h-full flex flex-col" style="background-color: #fef3c7; border: 2px solid #f59e0b;">
    <!-- Nautobot Section (shown when nautobot plugin is enabled) -->
    <div v-if="settingsStore.settings.nautobot.enabled" class="p-4 flex-1 flex flex-col">
      <h3 class="text-sm font-medium text-gray-700 mb-3 flex items-center">
        <i class="fas fa-network-wired mr-2 text-primary-600"></i>
        Nautobot Devices
      </h3>

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
    <div v-else-if="!settingsStore.settings.nautobot.enabled && settingsStore.settings.nautobot.url" class="p-4 border-b border-gray-200">
      <div class="text-center py-4 text-gray-500">
        <i class="fas fa-network-wired text-2xl mb-2 opacity-50"></i>
        <p class="text-xs">Nautobot plugin is disabled</p>
        <router-link to="/settings" class="text-xs text-primary-600 hover:text-primary-800">
          Enable in Settings
        </router-link>
      </div>
    </div>

    <!-- Nautobot Not Configured Message -->
    <div v-else-if="!settingsStore.settings.nautobot.url" class="p-4 border-b border-gray-200">
      <div class="text-center py-4 text-gray-500">
        <i class="fas fa-cog text-2xl mb-2 opacity-50"></i>
        <p class="text-xs">Nautobot not configured</p>
        <router-link to="/settings" class="text-xs text-primary-600 hover:text-primary-800">
          Configure in Settings
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

<style scoped>
.device-template {
  user-select: none;
}

.device-template:hover {
  transform: translateY(-1px);
}
</style>