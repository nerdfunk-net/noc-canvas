<template>
  <div class="space-y-6">
    <!-- Saved Inventories List -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div class="bg-gradient-to-r from-primary-50 to-primary-100 px-6 py-4 border-b border-primary-200">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 bg-primary-500 rounded-lg flex items-center justify-center">
              <i class="fas fa-list text-white"></i>
            </div>
            <div>
              <h2 class="text-lg font-bold text-gray-900">Device Inventories</h2>
              <p class="text-sm text-gray-600">Manage and organize your device collections</p>
            </div>
          </div>
          <button
            @click="$emit('start-new')"
            class="inline-flex items-center px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg shadow-sm transition-all duration-200 hover:shadow-md transform hover:-translate-y-0.5"
          >
            <i class="fas fa-plus mr-2"></i>
            New Inventory
          </button>
        </div>
      </div>

      <div class="p-6">
        <div v-if="loading" class="text-center py-12">
          <div class="inline-block">
            <div class="w-12 h-12 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin"></div>
          </div>
          <p class="text-gray-500 mt-4 font-medium">Loading inventories...</p>
        </div>

        <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4">
          <div class="flex items-center">
            <i class="fas fa-exclamation-circle text-red-500 text-xl mr-3"></i>
            <span class="text-red-700">{{ error }}</span>
          </div>
        </div>

        <div v-else-if="inventories.length === 0" class="text-center py-16">
          <div class="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <i class="fas fa-list text-4xl text-gray-300"></i>
          </div>
          <h3 class="text-lg font-semibold text-gray-900 mb-2">No inventories yet</h3>
          <p class="text-gray-500 mb-6">Create your first inventory to organize your devices</p>
          <button
            @click="$emit('start-new')"
            class="inline-flex items-center px-5 py-2.5 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg shadow-sm transition-all duration-200"
          >
            <i class="fas fa-plus mr-2"></i>
            Create Inventory
          </button>
        </div>

        <div v-else class="grid gap-4">
          <div
            v-for="inventory in inventories"
            :key="inventory.id"
            class="group bg-gradient-to-br from-white to-gray-50 border border-gray-200 rounded-xl p-5 hover:border-primary-300 hover:shadow-md transition-all duration-200"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1 min-w-0">
                <div class="flex items-center space-x-3 mb-2">
                  <div class="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm">
                    <i class="fas fa-server text-white"></i>
                  </div>
                  <div class="flex-1 min-w-0">
                    <h3 class="text-lg font-bold text-gray-900 truncate">{{ inventory.name }}</h3>
                    <p v-if="inventory.description" class="text-sm text-gray-600 line-clamp-2 mt-0.5">
                      {{ inventory.description }}
                    </p>
                  </div>
                </div>
                <div class="flex items-center space-x-4 mt-3 text-xs text-gray-500">
                  <div class="flex items-center">
                    <i class="fas fa-calendar-alt mr-1.5"></i>
                    <span>{{ formatDate(inventory.created_at) }}</span>
                  </div>
                  <div class="flex items-center">
                    <i class="fas fa-clock mr-1.5"></i>
                    <span>{{ formatTime(inventory.updated_at) }}</span>
                  </div>
                </div>
              </div>
              <div class="flex space-x-2 ml-4 flex-shrink-0">
                <button
                  @click="$emit('edit-inventory', inventory.id)"
                  class="p-2.5 bg-blue-50 hover:bg-blue-100 text-blue-600 rounded-lg transition-colors duration-200 group-hover:shadow-sm"
                  title="Edit inventory"
                >
                  <i class="fas fa-edit"></i>
                </button>
                <button
                  @click="$emit('preview-inventory', inventory.id)"
                  class="p-2.5 bg-green-50 hover:bg-green-100 text-green-600 rounded-lg transition-colors duration-200 group-hover:shadow-sm"
                  title="Preview devices"
                >
                  <i class="fas fa-eye"></i>
                </button>
                <button
                  @click="$emit('delete-inventory', inventory.id)"
                  class="p-2.5 bg-red-50 hover:bg-red-100 text-red-600 rounded-lg transition-colors duration-200 group-hover:shadow-sm"
                  title="Delete inventory"
                >
                  <i class="fas fa-trash"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Editor and Preview slots -->
    <slot name="editor"></slot>
    <slot name="preview"></slot>
  </div>
</template>

<script setup lang="ts">
interface Inventory {
  id: number
  name: string
  description?: string
  created_at: string
  updated_at: string
}

interface Props {
  inventories: Inventory[]
  loading: boolean
  error: string | null
}

defineProps<Props>()

defineEmits<{
  'start-new': []
  'edit-inventory': [id: number]
  'preview-inventory': [id: number]
  'delete-inventory': [id: number]
}>()

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

const formatTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}
</script>
