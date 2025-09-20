<template>
  <MainLayout>
    <div class="h-full bg-gray-100">
      <NOCCanvas />
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import MainLayout from '@/layouts/MainLayout.vue'
import NOCCanvas from '@/components/NOCCanvas.vue'
import { useDevicesStore } from '@/stores/devices'
import { useAuthStore } from '@/stores/auth'

const deviceStore = useDevicesStore()
const authStore = useAuthStore()

onMounted(async () => {
  // Initialize auth and fetch initial data
  await authStore.initializeAuth()
  await deviceStore.fetchDevices()
  await deviceStore.fetchConnections()
})
</script>