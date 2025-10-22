<template>
  <div class="space-y-6">
    <!-- Personal Credentials -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div class="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b border-blue-200">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center shadow-sm">
              <i class="fas fa-key text-white"></i>
            </div>
            <div>
              <h2 class="text-lg font-bold text-gray-900">Personal Credentials</h2>
              <p class="text-sm text-gray-600">Manage your SSH and TACACS credentials</p>
            </div>
          </div>
          <div class="flex items-center space-x-2">
            <button
              @click="$emit('add-credential')"
              class="p-2.5 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-all shadow-sm hover:shadow-md transform hover:-translate-y-0.5"
              title="Add credential"
            >
              <i class="fas fa-plus"></i>
            </button>
            <button
              @click="$emit('remove-last-credential')"
              :disabled="credentials.length === 0"
              class="p-2.5 bg-red-500 hover:bg-red-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg transition-all shadow-sm hover:shadow-md transform hover:-translate-y-0.5 disabled:transform-none"
              title="Remove last credential"
            >
              <i class="fas fa-minus"></i>
            </button>
          </div>
        </div>
      </div>

      <div class="p-6">
        <div
          v-if="credentials.length === 0"
          class="text-center py-16 bg-gradient-to-br from-gray-50 to-white rounded-xl border border-dashed border-gray-300"
        >
          <div class="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <i class="fas fa-key text-4xl text-gray-300"></i>
          </div>
          <h3 class="text-lg font-semibold text-gray-900 mb-2">No credentials yet</h3>
          <p class="text-gray-500 mb-6">Add your first credential to get started</p>
          <button
            @click="$emit('add-credential')"
            class="inline-flex items-center px-5 py-2.5 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg shadow-sm transition-all duration-200"
          >
            <i class="fas fa-plus mr-2"></i>
            Add Credential
          </button>
        </div>

        <div v-else class="space-y-4">
          <div
            v-for="(credential, index) in credentials"
            :key="index"
            class="group bg-gradient-to-br from-white to-gray-50 border-2 border-gray-200 rounded-xl p-5 hover:border-blue-300 hover:shadow-md transition-all duration-200"
          >
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center space-x-3">
                <div class="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center shadow-sm">
                  <span class="text-white font-bold text-sm">{{ index + 1 }}</span>
                </div>
                <span class="text-sm font-bold text-gray-900">Credential {{ index + 1 }}</span>
              </div>
              <button
                @click="$emit('remove-credential', index)"
                class="p-2 bg-red-50 hover:bg-red-100 text-red-600 rounded-lg transition-colors shadow-sm opacity-0 group-hover:opacity-100"
                title="Remove this credential"
              >
                <i class="fas fa-trash text-sm"></i>
              </button>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label class="block text-sm font-semibold text-gray-700 mb-2">
                  <i class="fas fa-tag text-blue-500 mr-1"></i>
                  Name
                </label>
                <input
                  v-model="credential.name"
                  type="text"
                  placeholder="e.g., Production SSH"
                  class="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all shadow-sm"
                />
              </div>
              <div>
                <label class="block text-sm font-semibold text-gray-700 mb-2">
                  <i class="fas fa-user text-green-500 mr-1"></i>
                  Username
                </label>
                <input
                  v-model="credential.username"
                  type="text"
                  placeholder="admin"
                  class="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all shadow-sm"
                />
              </div>
              <div>
                <label class="block text-sm font-semibold text-gray-700 mb-2">
                  <i class="fas fa-lock text-purple-500 mr-1"></i>
                  Password
                </label>
                <input
                  v-model="credential.password"
                  type="password"
                  placeholder="••••••••"
                  class="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all shadow-sm"
                />
              </div>
              <div>
                <label class="block text-sm font-semibold text-gray-700 mb-2">
                  <i class="fas fa-briefcase text-orange-500 mr-1"></i>
                  Purpose
                </label>
                <select
                  v-model="credential.purpose"
                  class="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all shadow-sm"
                >
                  <option value="ssh">SSH</option>
                  <option value="tacacs">TACACS</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Password Change Section Slot -->
    <slot name="password-change"></slot>
  </div>
</template>

<script setup lang="ts">
interface Credential {
  id?: number
  name: string
  username: string
  password: string
  purpose: string
}

interface Props {
  credentials: Credential[]
}

defineProps<Props>()

defineEmits<{
  'add-credential': []
  'remove-credential': [index: number]
  'remove-last-credential': []
}>()
</script>
