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
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

onMounted(async () => {
  // Initialize auth
  await authStore.initializeAuth()
  // Note: Devices are loaded from canvas data, not fetched from backend initially
})
</script>
