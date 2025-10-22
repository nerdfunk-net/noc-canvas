<template>
  <div class="space-y-6">
    <!-- Device Shape Templates -->
    <div class="card p-6 w-full max-w-full">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-lg font-semibold text-gray-900">Device Shape Templates</h2>
          <p class="text-sm text-gray-600 mt-1">
            Create custom templates and assign them to platforms or device types.
          </p>
        </div>
        <button
          @click="$emit('add-template')"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
        >
          <i class="fas fa-plus mr-2"></i>
          Add Template
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex items-center justify-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span class="ml-3 text-gray-600">Loading templates...</span>
      </div>

      <!-- Error State -->
      <div
        v-else-if="error"
        class="bg-red-50 border border-red-200 rounded-md p-4 mb-6"
      >
        <div class="flex items-center">
          <i class="fas fa-exclamation-circle text-red-600 mr-2"></i>
          <p class="text-sm text-red-800">{{ error }}</p>
        </div>
      </div>

      <!-- Empty State -->
      <div
        v-else-if="templates.length === 0"
        class="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300"
      >
        <div class="flex flex-col items-center">
          <i class="fas fa-shapes text-gray-400 text-4xl mb-4"></i>
          <p class="text-base font-medium text-gray-900 mb-1">No templates configured</p>
          <p class="text-sm text-gray-500">Add your first device template to get started</p>
        </div>
      </div>

      <!-- Templates Table -->
      <div v-else class="overflow-x-auto">
        <table class="w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Icon
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Template Name
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Icon File
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Platforms
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Device Types
              </th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="template in templates" :key="template.id">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center justify-center w-12 h-12 bg-gray-100 rounded-lg">
                  <img
                    :src="`/icons/${template.filename}`"
                    :alt="template.name"
                    class="w-10 h-10 object-contain"
                    @error="(e) => (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 24 24%22%3E%3Ctext x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 font-size=%2212%22%3E%3F%3C/text%3E%3C/svg%3E'"
                  />
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{{ template.name }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-500">{{ template.filename }}</div>
              </td>
              <td class="px-6 py-4">
                <div class="text-sm text-gray-500">
                  <span v-if="template.platforms.length === 0" class="text-gray-400 italic">None</span>
                  <span v-else class="inline-flex flex-wrap gap-1">
                    <span
                      v-for="platformId in template.platforms.slice(0, 3)"
                      :key="platformId"
                      class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {{ getPlatformName(platformId) }}
                    </span>
                    <span
                      v-if="template.platforms.length > 3"
                      class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800"
                    >
                      +{{ template.platforms.length - 3 }} more
                    </span>
                  </span>
                </div>
              </td>
              <td class="px-6 py-4">
                <div class="text-sm text-gray-500">
                  <span v-if="template.device_types.length === 0" class="text-gray-400 italic">None</span>
                  <span v-else class="inline-flex flex-wrap gap-1">
                    <span
                      v-for="deviceType in template.device_types.slice(0, 3)"
                      :key="deviceType"
                      class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800"
                    >
                      {{ deviceType }}
                    </span>
                    <span
                      v-if="template.device_types.length > 3"
                      class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800"
                    >
                      +{{ template.device_types.length - 3 }} more
                    </span>
                  </span>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                <button
                  @click="$emit('edit-template', template)"
                  class="inline-flex items-center px-3 py-1.5 border border-blue-600 text-blue-600 rounded hover:bg-blue-50 transition-colors"
                >
                  <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  Edit
                </button>
                <button
                  @click="$emit('delete-template', template)"
                  class="inline-flex items-center px-3 py-1.5 border border-red-600 text-red-600 rounded hover:bg-red-50 transition-colors"
                >
                  <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  Delete
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Template {
  id: number
  name: string
  filename: string
  platforms: string[]
  device_types: string[]
}

interface Props {
  templates: Template[]
  loading: boolean
  error: string | null
  getPlatformName: (id: string) => string
}

defineProps<Props>()
defineEmits<{
  'add-template': []
  'edit-template': [template: Template]
  'delete-template': [template: Template]
}>()
</script>
