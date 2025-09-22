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
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
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
                      <p>
                        The canvas size is unlimited and will automatically adjust based on your
                        content.
                      </p>
                    </div>
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
                    :disabled="testingConnection.database"
                    class="px-3 py-1 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50"
                  >
                    {{ testingConnection.database ? 'Testing...' : 'Test Connection' }}
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
                      v-model="settings.database.host"
                      type="text"
                      placeholder="192.168.1.100 or db.example.com"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2"> Port </label>
                    <input
                      v-model.number="settings.database.port"
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
                      v-model="settings.database.database"
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
                      v-model="settings.database.username"
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
                      v-model="settings.database.password"
                      type="password"
                      placeholder="Enter database password"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                  <div class="md:col-span-2">
                    <label class="flex items-center">
                      <input
                        v-model="settings.database.ssl"
                        type="checkbox"
                        class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                      />
                      <span class="ml-2 text-sm text-gray-700">Use SSL Connection</span>
                    </label>
                  </div>
                </div>
                <div class="mt-4 flex space-x-3">
                  <button
                    @click="testConnection('database')"
                    class="btn-secondary"
                    :disabled="testingConnection.database"
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
                    {{ testingConnection.database ? 'Testing...' : 'Test Connection' }}
                  </button>
                  <div v-if="connectionStatus.database" class="flex items-center">
                    <i
                      :class="
                        connectionStatus.database.success
                          ? 'fas fa-check-circle text-green-500'
                          : 'fas fa-times-circle text-red-500'
                      "
                      class="mr-2"
                    ></i>
                    <span
                      :class="connectionStatus.database.success ? 'text-green-700' : 'text-red-700'"
                      class="text-sm"
                    >
                      {{ connectionStatus.database.message }}
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

          <!-- Plugins Tab -->
          <div v-if="activeTab === 'plugins'" class="space-y-6">
            <!-- Nautobot Plugin -->
            <div class="card p-6">
              <div class="flex items-center justify-between mb-4">
                <h2 class="text-lg font-semibold text-gray-900">Nautobot Integration</h2>
                <label class="relative inline-flex items-center cursor-pointer">
                  <input v-model="settings.nautobot.enabled" type="checkbox" class="sr-only peer" />
                  <div
                    class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"
                  ></div>
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
                  <input v-model="settings.checkmk.enabled" type="checkbox" class="sr-only peer" />
                  <div
                    class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"
                  ></div>
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
                    <span class="text-sm font-medium text-gray-600"
                      >Credential {{ index + 1 }}</span
                    >
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
                      <label class="block text-xs font-medium text-gray-700 mb-1"> Name </label>
                      <input
                        v-model="credential.name"
                        type="text"
                        placeholder="Credential name"
                        class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                    <div>
                      <label class="block text-xs font-medium text-gray-700 mb-1"> Username </label>
                      <input
                        v-model="credential.username"
                        type="text"
                        placeholder="Username"
                        class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                    <div>
                      <label class="block text-xs font-medium text-gray-700 mb-1"> Password </label>
                      <input
                        v-model="credential.password"
                        type="password"
                        placeholder="Password"
                        class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                  </div>
                </div>
                <div
                  v-if="settings.credentials.length === 0"
                  class="text-center py-6 text-gray-500"
                >
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
                  <label class="block text-sm font-medium text-gray-700 mb-2"> New Password </label>
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
          <div v-if="activeTab !== 'profile' && activeTab !== 'canvas'" class="flex justify-end">
            <button @click="saveSettings" class="btn-primary" :disabled="saving">
              <i class="fas fa-save mr-2"></i>
              {{ saving ? 'Saving...' : 'Save Settings' }}
            </button>
          </div>

          <!-- Canvas Tab -->
          <div v-if="activeTab === 'canvas'" class="space-y-6">
            <!-- Canvas Management -->
            <div class="card p-6">
              <div class="flex items-center justify-between mb-6">
                <h2 class="text-lg font-semibold text-gray-900">Canvas Management</h2>
                <div class="flex items-center space-x-3">
                  <!-- Selection Info -->
                  <span v-if="selectedCanvases.size > 0" class="text-sm text-gray-600">
                    {{ selectedCanvases.size }} selected
                  </span>

                  <!-- Action Buttons -->
                  <button
                    v-if="selectedCanvases.size === 1"
                    @click="showRenameDialog"
                    class="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
                    title="Rename selected canvas"
                  >
                    <i class="fas fa-edit mr-1"></i>
                    Rename
                  </button>

                  <button
                    v-if="selectedCanvases.size === 1"
                    @click="loadSelectedCanvas"
                    class="px-3 py-1 text-xs bg-green-600 hover:bg-green-700 text-white rounded-md transition-colors"
                    title="Load selected canvas"
                  >
                    <i class="fas fa-folder-open mr-1"></i>
                    Load
                  </button>

                  <button
                    v-if="selectedCanvases.size > 0"
                    @click="showDeleteDialog"
                    class="px-3 py-1 text-xs bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
                    title="Delete selected canvases"
                  >
                    <i class="fas fa-trash mr-1"></i>
                    Delete ({{ selectedCanvases.size }})
                  </button>

                  <button
                    @click="refreshCanvases"
                    :disabled="loadingCanvases"
                    class="px-3 py-1 text-xs bg-gray-600 hover:bg-gray-700 disabled:bg-gray-400 text-white rounded-md transition-colors"
                    title="Refresh canvas list"
                  >
                    <i
                      :class="loadingCanvases ? 'fas fa-spinner fa-spin' : 'fas fa-sync-alt'"
                      class="mr-1"
                    ></i>
                    Refresh
                  </button>
                </div>
              </div>

              <!-- Loading State -->
              <div v-if="loadingCanvases" class="flex items-center justify-center py-12">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span class="ml-3 text-gray-600">Loading canvases...</span>
              </div>

              <!-- Error State -->
              <div
                v-else-if="canvasError"
                class="bg-red-50 border border-red-200 rounded-md p-4 mb-6"
              >
                <div class="flex">
                  <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path
                      fill-rule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clip-rule="evenodd"
                    />
                  </svg>
                  <div class="ml-3">
                    <h3 class="text-sm font-medium text-red-800">Error Loading Canvases</h3>
                    <p class="mt-1 text-sm text-red-700">{{ canvasError }}</p>
                  </div>
                </div>
              </div>

              <!-- Empty State -->
              <div v-else-if="canvases.length === 0" class="text-center py-12 text-gray-500">
                <div
                  class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4"
                >
                  <svg
                    class="w-8 h-8 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="1.5"
                      d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                    ></path>
                  </svg>
                </div>
                <p class="text-base font-medium text-gray-900 mb-1">No saved canvases</p>
                <p class="text-sm text-gray-500">Create your first canvas to get started</p>
              </div>

              <!-- Canvas Grid -->
              <div v-else>
                <!-- Search Bar -->
                <div class="mb-6">
                  <div class="relative">
                    <input
                      v-model="canvasSearchQuery"
                      type="text"
                      placeholder="Search canvases..."
                      class="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                    <div
                      class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none"
                    >
                      <svg
                        class="h-5 w-5 text-gray-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                        ></path>
                      </svg>
                    </div>
                  </div>
                </div>

                <!-- Canvas Tiles -->
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                  <div
                    v-for="canvas in filteredCanvases"
                    :key="canvas.id"
                    class="relative border border-gray-200 rounded-lg p-4 hover:bg-gray-50 hover:border-gray-300 cursor-pointer transition-all duration-200"
                    :class="{
                      'ring-2 ring-blue-500 bg-blue-50 border-blue-200': selectedCanvases.has(
                        canvas.id
                      ),
                      'hover:shadow-md': !selectedCanvases.has(canvas.id),
                    }"
                    @click="toggleCanvasSelection(canvas.id)"
                  >
                    <!-- Selection Checkbox -->
                    <div class="absolute top-3 right-3">
                      <div
                        class="w-5 h-5 border-2 rounded"
                        :class="
                          selectedCanvases.has(canvas.id)
                            ? 'bg-blue-600 border-blue-600'
                            : 'border-gray-300'
                        "
                      >
                        <svg
                          v-if="selectedCanvases.has(canvas.id)"
                          class="w-3 h-3 text-white ml-0.5 mt-0.5"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fill-rule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clip-rule="evenodd"
                          ></path>
                        </svg>
                      </div>
                    </div>

                    <!-- Canvas Content -->
                    <div class="pr-8">
                      <!-- Canvas Icon -->
                      <div
                        class="w-12 h-12 bg-gradient-to-br rounded-lg flex items-center justify-center mb-3"
                        :class="getCanvasIconGradient(canvas)"
                      >
                        <svg
                          class="w-6 h-6 text-white"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                          ></path>
                        </svg>
                      </div>

                      <!-- Canvas Name -->
                      <h3
                        class="font-medium text-gray-900 text-sm mb-1 truncate"
                        :title="canvas.name"
                      >
                        {{ canvas.name }}
                      </h3>

                      <!-- Canvas Info -->
                      <div class="text-xs text-gray-500 mb-2">
                        <span v-if="canvas.is_own" class="text-blue-600 font-medium"
                          >Your canvas</span
                        >
                        <span v-else>
                          <svg
                            class="w-3 h-3 inline mr-1 text-gray-400"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              stroke-width="2"
                              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                            ></path>
                          </svg>
                          {{ canvas.owner_username }}
                        </span>
                        <span v-if="canvas.sharable" class="ml-2 text-green-600">• Shared</span>
                      </div>

                      <!-- Date -->
                      <p class="text-xs text-gray-400">
                        {{ formatCanvasDate(canvas.updated_at) }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Rename Canvas Modal -->
          <div
            v-if="showRenameDialogModal"
            class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            @click.self="closeRenameDialog"
          >
            <div class="bg-white rounded-lg shadow-xl p-6 w-96 max-w-md">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold text-gray-900">Rename Canvas</h3>
                <button
                  @click="closeRenameDialog"
                  class="text-gray-400 hover:text-gray-600 transition-colors"
                  type="button"
                >
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M6 18L18 6M6 6l12 12"
                    ></path>
                  </svg>
                </button>
              </div>

              <form @submit.prevent="confirmRename">
                <div class="mb-4">
                  <label class="block text-sm font-medium text-gray-700 mb-2">Canvas Name</label>
                  <input
                    v-model="renameCanvasName"
                    type="text"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter new name"
                    required
                  />
                </div>

                <div v-if="renameError" class="bg-red-50 border border-red-200 rounded-md p-3 mb-4">
                  <p class="text-sm text-red-600">{{ renameError }}</p>
                </div>

                <div class="flex justify-end space-x-3">
                  <button
                    type="button"
                    @click="closeRenameDialog"
                    class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    class="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
                  >
                    Rename
                  </button>
                </div>
              </form>
            </div>
          </div>

          <!-- Delete Canvas Confirmation Modal -->
          <div
            v-if="showDeleteDialogModal"
            class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            @click.self="closeDeleteDialog"
          >
            <div class="bg-white rounded-lg shadow-xl p-6 w-96 max-w-md">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold text-gray-900">Delete Canvases</h3>
                <button
                  @click="closeDeleteDialog"
                  class="text-gray-400 hover:text-gray-600 transition-colors"
                  type="button"
                >
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M6 18L18 6M6 6l12 12"
                    ></path>
                  </svg>
                </button>
              </div>

              <div class="mb-6">
                <div class="flex items-center mb-3">
                  <div class="flex-shrink-0">
                    <svg
                      class="h-8 w-8 text-red-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 14.5c-.77.833.192 2.5 1.732 2.5z"
                      ></path>
                    </svg>
                  </div>
                  <div class="ml-3">
                    <h3 class="text-sm font-medium text-gray-900">Confirm Deletion</h3>
                  </div>
                </div>

                <p class="text-gray-700 text-sm leading-relaxed">
                  Are you sure you want to delete {{ selectedCanvases.size }} canvas{{
                    selectedCanvases.size === 1 ? '' : 'es'
                  }}? This action cannot be undone.
                </p>
              </div>

              <div class="flex justify-end space-x-3">
                <button
                  @click="closeDeleteDialog"
                  class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
                  type="button"
                >
                  Cancel
                </button>
                <button
                  @click="confirmDelete"
                  class="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-colors"
                  type="button"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>

          <!-- Load Canvas Confirmation Modal -->
          <div
            v-if="showLoadConfirmationModal"
            class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            @click.self="closeLoadConfirmation"
          >
            <div class="bg-white rounded-lg shadow-xl p-6 w-96 max-w-md">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold text-gray-900">Load Canvas</h3>
                <button
                  @click="closeLoadConfirmation"
                  class="text-gray-400 hover:text-gray-600 transition-colors"
                  type="button"
                >
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M6 18L18 6M6 6l12 12"
                    ></path>
                  </svg>
                </button>
              </div>

              <div class="mb-6">
                <div class="flex items-center mb-3">
                  <div class="flex-shrink-0">
                    <svg
                      class="h-8 w-8 text-amber-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 14.5c-.77.833.192 2.5 1.732 2.5z"
                      ></path>
                    </svg>
                  </div>
                  <div class="ml-3">
                    <h3 class="text-sm font-medium text-gray-900">
                      Current Canvas Will Be Replaced
                    </h3>
                  </div>
                </div>

                <p class="text-gray-700 text-sm leading-relaxed mb-3">
                  Loading <strong>{{ canvasToLoad?.name }}</strong> will replace your current canvas
                  with {{ deviceStore.devices.length }} device{{
                    deviceStore.devices.length === 1 ? '' : 's'
                  }}.
                </p>

                <p class="text-gray-600 text-sm">
                  Any unsaved changes will be lost. Are you sure you want to continue?
                </p>
              </div>

              <div class="flex justify-end space-x-3">
                <button
                  @click="closeLoadConfirmation"
                  class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
                  type="button"
                >
                  Cancel
                </button>
                <button
                  @click="confirmLoadCanvas"
                  class="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
                  type="button"
                >
                  Load Canvas
                </button>
              </div>
            </div>
          </div>

          <!-- Save Button (for Profile tab) -->
          <div v-if="activeTab === 'profile'" class="flex justify-end">
            <button @click="saveProfile" class="btn-primary" :disabled="savingProfile">
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
import { ref, reactive, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import { useNotificationStore } from '@/stores/notification'
import { canvasApi, type CanvasListItem, makeAuthenticatedRequest } from '@/services/api'
import { useDevicesStore } from '@/stores/devices'

const notificationStore = useNotificationStore()
const router = useRouter()
const deviceStore = useDevicesStore()

const activeTab = ref('general')
const saving = ref(false)
const savingProfile = ref(false)
const changingPassword = ref(false)
const testingConnection = reactive({
  nautobot: false,
  checkmk: false,
  database: false,
})
const connectionStatus = reactive({
  nautobot: null as { success: boolean; message: string } | null,
  checkmk: null as { success: boolean; message: string } | null,
  database: null as { success: boolean; message: string } | null,
})

const tabs = [
  { id: 'general', name: 'General', icon: 'fas fa-cog' },
  { id: 'plugins', name: 'Plugins', icon: 'fas fa-plug' },
  { id: 'canvas', name: 'Canvas', icon: 'fas fa-layer-group' },
  { id: 'profile', name: 'Profile', icon: 'fas fa-user' },
]

const settings = reactive({
  nautobot: {
    enabled: false,
    url: '',
    token: '',
    verifyTls: true,
    timeout: 30,
  },
  checkmk: {
    enabled: false,
    url: '',
    site: 'cmk',
    username: '',
    password: '',
    verifyTls: true,
  },
  canvas: {
    autoSaveInterval: 60,
    gridEnabled: true,
  },
  database: {
    host: '',
    port: 5432,
    database: '',
    username: '',
    password: '',
    ssl: false,
  },
  credentials: [] as Array<{
    name: string
    username: string
    password: string
  }>,
})

const passwordChange = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

// Canvas management state
const canvases = ref<CanvasListItem[]>([])
const selectedCanvases = ref(new Set<number>())
const loadingCanvases = ref(false)
const canvasError = ref<string | null>(null)
const canvasSearchQuery = ref('')

// Modal/dialog states
const showRenameDialogModal = ref(false)
const showDeleteDialogModal = ref(false)
const showLoadConfirmationModal = ref(false)
const renameCanvasId = ref<number | null>(null)
const renameCanvasName = ref('')
const renameError = ref<string | null>(null)
const canvasToLoad = ref<CanvasListItem | null>(null)

const isPasswordChangeValid = computed(() => {
  return (
    passwordChange.currentPassword &&
    passwordChange.newPassword &&
    passwordChange.confirmPassword &&
    passwordChange.newPassword === passwordChange.confirmPassword &&
    passwordChange.newPassword.length >= 6
  )
})

// Canvas computed properties
const filteredCanvases = computed(() => {
  if (!canvasSearchQuery.value.trim()) {
    return canvases.value
  }

  const query = canvasSearchQuery.value.toLowerCase()
  return canvases.value.filter(
    (canvas) =>
      canvas.name.toLowerCase().includes(query) ||
      canvas.owner_username.toLowerCase().includes(query)
  )
})

// Canvas management functions
const refreshCanvases = async () => {
  loadingCanvases.value = true
  canvasError.value = null

  try {
    console.log('🔄 Loading canvases...')
    const response = await canvasApi.getCanvasList()
    canvases.value = response
    console.log('✅ Loaded canvases:', response)
  } catch (err) {
    console.error('❌ Failed to load canvases:', err)
    canvasError.value = err instanceof Error ? err.message : 'Failed to load canvases'
  } finally {
    loadingCanvases.value = false
  }
}

const toggleCanvasSelection = (canvasId: number) => {
  if (selectedCanvases.value.has(canvasId)) {
    selectedCanvases.value.delete(canvasId)
  } else {
    selectedCanvases.value.add(canvasId)
  }
}

const getCanvasIconGradient = (canvas: CanvasListItem) => {
  if (canvas.is_own) {
    return 'from-blue-500 to-indigo-600'
  } else if (canvas.sharable) {
    return 'from-green-500 to-emerald-600'
  } else {
    return 'from-gray-500 to-slate-600'
  }
}

const formatCanvasDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)

  if (diffInHours < 24) {
    return `${Math.floor(diffInHours)} hours ago`
  } else if (diffInHours < 24 * 7) {
    return `${Math.floor(diffInHours / 24)} days ago`
  } else {
    return date.toLocaleDateString()
  }
}

const showRenameDialog = () => {
  const selectedIds = Array.from(selectedCanvases.value)
  if (selectedIds.length === 1) {
    const canvas = canvases.value.find((c) => c.id === selectedIds[0])
    if (canvas) {
      renameCanvasId.value = canvas.id
      renameCanvasName.value = canvas.name
      renameError.value = null
      showRenameDialogModal.value = true
    }
  }
}

const showDeleteDialog = () => {
  if (selectedCanvases.value.size > 0) {
    showDeleteDialogModal.value = true
  }
}

const loadSelectedCanvas = async () => {
  const selectedIds = Array.from(selectedCanvases.value)
  if (selectedIds.length === 1) {
    const canvasId = selectedIds[0]
    const selectedCanvas = canvases.value.find((c) => c.id === canvasId)

    if (!selectedCanvas) return

    // Check if current canvas has content
    if (deviceStore.devices.length > 0) {
      canvasToLoad.value = selectedCanvas
      showLoadConfirmationModal.value = true
    } else {
      // Canvas is empty, load directly
      await performCanvasLoad(canvasId, selectedCanvas.name)
    }
  }
}

const closeLoadConfirmation = () => {
  showLoadConfirmationModal.value = false
  canvasToLoad.value = null
}

const confirmLoadCanvas = async () => {
  if (canvasToLoad.value) {
    await performCanvasLoad(canvasToLoad.value.id, canvasToLoad.value.name)
    closeLoadConfirmation()
  }
}

const performCanvasLoad = async (canvasId: number, canvasName: string) => {
  try {
    console.log('🔄 Loading canvas from Settings:', canvasId)

    // Clear current canvas first if it has devices (uses API to maintain sync)
    if (deviceStore.devices.length > 0) {
      await deviceStore.clearDevices()
      console.log('✅ Current canvas cleared')
    }

    // Fetch canvas data
    const canvas = await canvasApi.getCanvas(canvasId)
    console.log('✅ Canvas data loaded:', canvas)

    // Load devices from canvas data (uses API to maintain sync)
    for (const deviceData of canvas.canvas_data.devices) {
      const device = await deviceStore.createDevice({
        name: deviceData.name,
        device_type: deviceData.device_type as 'router' | 'switch' | 'firewall' | 'vpn_gateway',
        ip_address: deviceData.ip_address,
        position_x: deviceData.position_x,
        position_y: deviceData.position_y,
        properties: deviceData.properties,
      })
      console.log('✅ Device created:', device)
    }

    // Load connections from canvas data (uses API to maintain sync)
    for (const connectionData of canvas.canvas_data.connections) {
      const connection = await deviceStore.createConnection({
        source_device_id: connectionData.source_device_id,
        target_device_id: connectionData.target_device_id,
        connection_type: connectionData.connection_type,
        properties: connectionData.properties,
      })
      console.log('✅ Connection created:', connection)
    }

    console.log('✅ Canvas loaded successfully from Settings')
    notificationStore.addNotification({
      title: 'Success',
      message: `Canvas "${canvasName}" loaded successfully`,
      type: 'success',
    })

    // Navigate to main view after successful loading
    await router.push('/')
  } catch (error) {
    console.error('❌ Failed to load canvas:', error)
    notificationStore.addNotification({
      title: 'Error',
      message: 'Failed to load canvas',
      type: 'error',
    })
  }
}

// Canvas modal functions
const closeRenameDialog = () => {
  showRenameDialogModal.value = false
  renameCanvasId.value = null
  renameCanvasName.value = ''
  renameError.value = null
}

const confirmRename = async () => {
  if (!renameCanvasId.value || !renameCanvasName.value.trim()) return

  try {
    // Check if name already exists (exclude current canvas)
    const existingCanvas = canvases.value.find(
      (c) =>
        c.name.toLowerCase() === renameCanvasName.value.toLowerCase() &&
        c.id !== renameCanvasId.value
    )

    if (existingCanvas) {
      renameError.value = 'A canvas with this name already exists'
      return
    }

    // Update canvas name
    await canvasApi.updateCanvas(renameCanvasId.value, {
      name: renameCanvasName.value.trim(),
    })

    // Update local canvas list
    const canvasIndex = canvases.value.findIndex((c) => c.id === renameCanvasId.value)
    if (canvasIndex !== -1) {
      canvases.value[canvasIndex].name = renameCanvasName.value.trim()
    }

    notificationStore.addNotification({
      title: 'Success',
      message: 'Canvas renamed successfully',
      type: 'success',
    })

    closeRenameDialog()
  } catch (error) {
    console.error('❌ Failed to rename canvas:', error)
    renameError.value = error instanceof Error ? error.message : 'Failed to rename canvas'
  }
}

const closeDeleteDialog = () => {
  showDeleteDialogModal.value = false
}

const confirmDelete = async () => {
  const canvasIds = Array.from(selectedCanvases.value)

  try {
    // Delete each canvas
    for (const canvasId of canvasIds) {
      await canvasApi.deleteCanvas(canvasId)
    }

    // Remove from local list
    canvases.value = canvases.value.filter((canvas) => !canvasIds.includes(canvas.id))

    // Clear selection
    selectedCanvases.value.clear()

    notificationStore.addNotification({
      title: 'Success',
      message: `${canvasIds.length} canvas${canvasIds.length === 1 ? '' : 'es'} deleted successfully`,
      type: 'success',
    })

    closeDeleteDialog()
  } catch (error) {
    console.error('❌ Failed to delete canvases:', error)
    notificationStore.addNotification({
      title: 'Error',
      message: 'Failed to delete canvases',
      type: 'error',
    })
  }
}

// Load canvases when the canvas tab is shown
const loadCanvasesIfNeeded = async () => {
  if (activeTab.value === 'canvas' && canvases.value.length === 0) {
    await refreshCanvases()
  }
}

// Watch activeTab to load canvases
watch(activeTab, loadCanvasesIfNeeded)

const addCredential = () => {
  settings.credentials.push({
    name: '',
    username: '',
    password: '',
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

const testConnection = async (service: 'nautobot' | 'checkmk' | 'database') => {
  testingConnection[service] = true
  connectionStatus[service] = null

  try {
    let endpoint = ''
    let payload = {}

    if (service === 'nautobot') {
      endpoint = '/api/settings/test-nautobot'
      payload = {
        url: settings.nautobot.url,
        token: settings.nautobot.token,
        verify_ssl: settings.nautobot.verifyTls,
        timeout: settings.nautobot.timeout,
      }
    } else if (service === 'checkmk') {
      endpoint = '/api/settings/test-checkmk'
      payload = {
        url: settings.checkmk.url,
        site: settings.checkmk.site,
        username: settings.checkmk.username,
        password: settings.checkmk.password,
        verify_ssl: settings.checkmk.verifyTls,
      }
    } else if (service === 'database') {
      endpoint = '/api/settings/test-database'
      payload = {
        host: settings.database.host,
        port: settings.database.port,
        database: settings.database.database,
        username: settings.database.username,
        password: settings.database.password,
        ssl: settings.database.ssl,
      }
    }

    const response = await makeAuthenticatedRequest(endpoint, {
      method: 'POST',
      body: JSON.stringify(payload),
    })

    const result = await response.json()

    if (response.ok && result.success) {
      connectionStatus[service] = {
        success: true,
        message: result.message || 'Connection successful!',
      }
    } else {
      connectionStatus[service] = {
        success: false,
        message: result.message || result.detail || 'Connection failed',
      }
    }
  } catch (error) {
    connectionStatus[service] = {
      success: false,
      message: `Connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
    }
  } finally {
    testingConnection[service] = false
  }
}

const testDatabaseConnection = async () => {
  await testConnection('database')
}

const saveSettings = async () => {
  saving.value = true
  try {
    const response = await makeAuthenticatedRequest('/api/settings/unified', {
      method: 'POST',
      body: JSON.stringify({
        nautobot: settings.nautobot,
        checkmk: settings.checkmk,
        canvas: settings.canvas,
        database: settings.database,
      }),
    })

    if (response.ok) {
      notificationStore.addNotification({
        title: 'Settings Saved',
        message: 'Your settings have been saved successfully.',
        type: 'success',
      })
      localStorage.setItem('noc-canvas-settings', JSON.stringify(settings))
    } else {
      throw new Error('Failed to save settings')
    }
  } catch (error) {
    notificationStore.addNotification({
      title: 'Save Failed',
      message: 'Failed to save settings. Please try again.',
      type: 'error',
    })
    console.error('Failed to save settings:', error)
  } finally {
    saving.value = false
  }
}

const saveProfile = async () => {
  savingProfile.value = true
  try {
    const response = await makeAuthenticatedRequest('/api/settings/credentials', {
      method: 'POST',
      body: JSON.stringify({ credentials: settings.credentials }),
    })

    if (response.ok) {
      notificationStore.addNotification({
        title: 'Credentials Saved',
        message: 'Your credentials have been saved successfully.',
        type: 'success',
      })
      localStorage.setItem('noc-canvas-credentials', JSON.stringify(settings.credentials))
    } else {
      throw new Error('Failed to save credentials')
    }
  } catch (error) {
    notificationStore.addNotification({
      title: 'Save Failed',
      message: 'Failed to save credentials. Please try again.',
      type: 'error',
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
    const response = await makeAuthenticatedRequest('/api/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({
        current_password: passwordChange.currentPassword,
        new_password: passwordChange.newPassword,
      }),
    })

    if (response.ok) {
      notificationStore.addNotification({
        title: 'Password Changed',
        message: 'Your password has been changed successfully.',
        type: 'success',
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
      message:
        error instanceof Error ? error.message : 'Failed to change password. Please try again.',
      type: 'error',
    })
  } finally {
    changingPassword.value = false
  }
}

// Load settings on component mount
const loadSettings = async () => {
  try {
    const response = await makeAuthenticatedRequest('/api/settings/unified')

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
    const credentialsResponse = await makeAuthenticatedRequest('/api/settings/credentials')

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
