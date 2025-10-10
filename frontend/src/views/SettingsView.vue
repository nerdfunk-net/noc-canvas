<template>
  <MainLayout>
    <div class="h-full flex bg-white">
      <!-- Left Sidebar Navigation -->
      <div class="hidden md:flex w-64 bg-white border-r border-gray-200 flex-col">
        <!-- Navigation Menu -->
        <nav class="flex-1 p-3 space-y-1">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-all duration-200 text-left group',
              activeTab === tab.id
                ? 'bg-primary-50 text-primary-700 shadow-sm ring-1 ring-primary-200'
                : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900',
            ]"
          >
            <i 
              :class="[
                tab.icon, 
                'mr-3 w-4 h-4 flex-shrink-0 transition-colors duration-200',
                activeTab === tab.id 
                  ? 'text-primary-600' 
                  : 'text-gray-500 group-hover:text-gray-700'
              ]"
            ></i>
            <span class="font-medium">{{ tab.name }}</span>
          </button>
        </nav>
      </div>

      <!-- Mobile Menu Toggle -->
      <div class="md:hidden w-full">
        <div class="bg-white border-b border-gray-200 px-4 py-3">
          <div class="flex items-center justify-end">
            <button
              @click="showMobileMenu = !showMobileMenu"
              class="p-2 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100"
            >
              <i class="fas fa-bars"></i>
            </button>
          </div>
          
          <!-- Mobile Menu Dropdown -->
          <div v-if="showMobileMenu" class="mt-3 border-t border-gray-200 pt-3">
            <nav class="space-y-1">
              <button
                v-for="tab in tabs"
                :key="tab.id"
                @click="activeTab = tab.id; showMobileMenu = false"
                :class="[
                  'w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors text-left',
                  activeTab === tab.id
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-700 hover:bg-gray-50',
                ]"
              >
                <i :class="tab.icon" class="mr-3 w-4 h-4 flex-shrink-0"></i>
                {{ tab.name }}
              </button>
            </nav>
          </div>
        </div>
      </div>

      <!-- Main Content Area -->
      <div class="flex-1 overflow-y-auto">
        <div class="p-4 md:p-6">
          <div :class="activeTab === 'templates' ? 'max-w-7xl' : 'max-w-4xl'">
            <!-- Page Header (hidden on mobile when menu is open) -->
            <div class="mb-6" :class="{ 'hidden md:block': showMobileMenu }">
              <h2 class="text-xl md:text-2xl font-bold text-gray-900">
                {{ tabs.find(t => t.id === activeTab)?.name }} Settings
              </h2>
              <p class="mt-1 text-sm text-gray-500">
                Manage your {{ tabs.find(t => t.id === activeTab)?.name.toLowerCase() }} configuration and preferences.
              </p>
            </div>

            <!-- Tab Content -->
            <div class="space-y-6" :class="{ 'hidden md:block': showMobileMenu }">
          <!-- General Tab -->
          <div v-if="activeTab === 'general'" class="space-y-6">
            <!-- Canvas Settings -->
            <div class="card p-6">
              <h2 class="text-lg font-semibold text-gray-900 mb-4">Canvas Settings</h2>
              <div class="space-y-4">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 items-end">
                  <div>
                    <label class="flex items-center">
                      <input
                        v-model="settings.canvas.autoSaveEnabled"
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
                      v-model.number="settings.canvas.autoSaveInterval"
                      type="number"
                      min="30"
                      step="10"
                      :disabled="!settings.canvas.autoSaveEnabled"
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
                      v-model.number="settings.netmiko.readTimeout"
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
                      v-model.number="settings.netmiko.lastRead"
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
                      v-model.number="settings.netmiko.connTimeout"
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
                      v-model.number="settings.netmiko.authTimeout"
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
                      v-model.number="settings.netmiko.bannerTimeout"
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
                      v-model.number="settings.netmiko.blockingTimeout"
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
                      v-model.number="settings.netmiko.timeout"
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
                      v-model.number="settings.netmiko.sessionTimeout"
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

          <!-- Templates Tab -->
          <div v-if="activeTab === 'templates'" class="space-y-6">
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
                  @click="openTemplateDialog()"
                  class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
                >
                  <i class="fas fa-plus mr-2"></i>
                  Add Template
                </button>
              </div>

              <!-- Loading State -->
              <div v-if="loadingTemplates" class="flex items-center justify-center py-12">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span class="ml-3 text-gray-600">Loading templates...</span>
              </div>

              <!-- Error State -->
              <div
                v-else-if="templatesError"
                class="bg-red-50 border border-red-200 rounded-md p-4 mb-6"
              >
                <div class="flex items-center">
                  <i class="fas fa-exclamation-circle text-red-600 mr-2"></i>
                  <p class="text-sm text-red-800">{{ templatesError }}</p>
                </div>
              </div>

              <!-- Empty State -->
              <div
                v-else-if="deviceTemplates.length === 0"
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
                    <tr v-for="template in deviceTemplates" :key="template.id">
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
                          @click="openTemplateDialog(template)"
                          class="inline-flex items-center px-3 py-1.5 border border-blue-600 text-blue-600 rounded hover:bg-blue-50 transition-colors"
                        >
                          <svg class="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                          Edit
                        </button>
                        <button
                          @click="deleteTemplate(template)"
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

          <!-- Commands Tab -->
          <div v-if="activeTab === 'commands'" class="space-y-6">
            <!-- Commands Management -->
            <div class="card p-6">
              <div class="flex items-center justify-between mb-6">
                <h2 class="text-lg font-semibold text-gray-900">Device Commands</h2>
                <button
                  @click="openCommandDialog()"
                  class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
                >
                  <i class="fas fa-plus mr-2"></i>
                  Add Command
                </button>
              </div>

              <!-- Loading State -->
              <div v-if="loadingCommands" class="flex items-center justify-center py-12">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span class="ml-3 text-gray-600">Loading commands...</span>
              </div>

              <!-- Error State -->
              <div
                v-else-if="commandsError"
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
                    <h3 class="text-sm font-medium text-red-800">Error Loading Commands</h3>
                    <p class="mt-1 text-sm text-red-700">{{ commandsError }}</p>
                  </div>
                </div>
              </div>

              <!-- Empty State -->
              <div v-else-if="commands.length === 0" class="text-center py-12 text-gray-500">
                <div
                  class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4"
                >
                  <i class="fas fa-terminal text-gray-400 text-2xl"></i>
                </div>
                <p class="text-base font-medium text-gray-900 mb-1">No commands configured</p>
                <p class="text-sm text-gray-500">Add your first device command to get started</p>
              </div>

              <!-- Commands Table -->
              <div v-else class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                  <thead class="bg-gray-50">
                    <tr>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Command
                      </th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Display
                      </th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Template
                      </th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Platform
                      </th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Parser
                      </th>
                      <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                    <tr v-for="command in commands" :key="command.id" class="hover:bg-gray-50">
                      <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm font-medium text-gray-900 font-mono bg-gray-100 px-2 py-1 rounded">
                          {{ command.command }}
                        </div>
                      </td>
                      <td class="px-6 py-4">
                        <div class="text-sm text-gray-900">
                          {{ command.display || '-' }}
                        </div>
                      </td>
                      <td class="px-6 py-4">
                        <div class="text-sm text-gray-900 font-mono text-xs max-w-xs truncate" :title="command.template">
                          {{ command.template || '-' }}
                        </div>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {{ command.platform }}
                        </span>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          {{ command.parser }}
                        </span>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div class="flex items-center justify-end space-x-2">
                          <button
                            @click="openCommandDialog(command)"
                            class="inline-flex items-center p-1.5 border border-transparent text-xs leading-4 font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                            title="Edit command"
                          >
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                            </svg>
                          </button>
                          <button
                            @click="deleteCommand(command)"
                            class="inline-flex items-center p-1.5 border border-transparent text-xs leading-4 font-medium rounded text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
                            title="Delete command"
                          >
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                            </svg>
                          </button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <!-- Command Dialog -->
          <div
            v-if="showCommandDialog"
            class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            @click.self="closeCommandDialog"
          >
            <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-2xl mx-4">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold text-gray-900">
                  {{ editingCommand ? 'Edit Command' : 'Add Command' }}
                </h3>
                <button
                  @click="closeCommandDialog"
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

              <form @submit.prevent="saveCommand">
                <div class="space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Command</label>
                    <textarea
                      v-model="commandForm.command"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                      placeholder="show ip interface brief"
                      rows="3"
                      required
                    ></textarea>
                  </div>

                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Display</label>
                    <input
                      v-model="commandForm.display"
                      type="text"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Display name for this command"
                    />
                  </div>

                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Template</label>
                    <textarea
                      v-model="commandForm.template"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                      placeholder="Jinja2 template for output rendering"
                      rows="4"
                    ></textarea>
                    <p class="mt-1 text-xs text-gray-500">Use Jinja2 syntax to template command output</p>
                  </div>

                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Platform</label>
                    <select
                      v-model="commandForm.platform"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      required
                    >
                      <option v-for="platform in commandPlatforms" :key="platform.value" :value="platform.value">
                        {{ platform.label }}
                      </option>
                    </select>
                  </div>

                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Parser</label>
                    <select
                      v-model="commandForm.parser"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      required
                    >
                      <option v-for="parser in parsers" :key="parser.value" :value="parser.value">
                        {{ parser.label }}
                      </option>
                    </select>
                  </div>
                </div>

                <div class="flex justify-end space-x-3 mt-6">
                  <button
                    type="button"
                    @click="closeCommandDialog"
                    class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    class="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
                  >
                    {{ editingCommand ? 'Update' : 'Create' }}
                  </button>
                </div>
              </form>
            </div>
          </div>

          <!-- Inventory Tab -->
          <div v-if="activeTab === 'inventory'" class="space-y-6">
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
                    @click="startNewInventory" 
                    class="inline-flex items-center px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg shadow-sm transition-all duration-200 hover:shadow-md transform hover:-translate-y-0.5"
                  >
                    <i class="fas fa-plus mr-2"></i>
                    New Inventory
                  </button>
                </div>
              </div>

              <div class="p-6">
                <div v-if="loadingInventories" class="text-center py-12">
                  <div class="inline-block">
                    <div class="w-12 h-12 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin"></div>
                  </div>
                  <p class="text-gray-500 mt-4 font-medium">Loading inventories...</p>
                </div>

                <div v-else-if="inventoriesError" class="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div class="flex items-center">
                    <i class="fas fa-exclamation-circle text-red-500 text-xl mr-3"></i>
                    <span class="text-red-700">{{ inventoriesError }}</span>
                  </div>
                </div>

                <div v-else-if="inventories.length === 0" class="text-center py-16">
                  <div class="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <i class="fas fa-list text-4xl text-gray-300"></i>
                  </div>
                  <h3 class="text-lg font-semibold text-gray-900 mb-2">No inventories yet</h3>
                  <p class="text-gray-500 mb-6">Create your first inventory to organize your devices</p>
                  <button 
                    @click="startNewInventory" 
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
                            <span>{{ new Date(inventory.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) }}</span>
                          </div>
                          <div class="flex items-center">
                            <i class="fas fa-clock mr-1.5"></i>
                            <span>{{ new Date(inventory.updated_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }) }}</span>
                          </div>
                        </div>
                      </div>
                      <div class="flex space-x-2 ml-4 flex-shrink-0">
                        <button
                          @click="editInventory(inventory.id)"
                          class="p-2.5 bg-blue-50 hover:bg-blue-100 text-blue-600 rounded-lg transition-colors duration-200 group-hover:shadow-sm"
                          title="Edit inventory"
                        >
                          <i class="fas fa-edit"></i>
                        </button>
                        <button
                          @click="previewInventoryById(inventory.id)"
                          class="p-2.5 bg-green-50 hover:bg-green-100 text-green-600 rounded-lg transition-colors duration-200 group-hover:shadow-sm"
                          title="Preview devices"
                        >
                          <i class="fas fa-eye"></i>
                        </button>
                        <button
                          @click="deleteInventory(inventory.id)"
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

            <!-- Inventory Editor (shown when creating/editing) -->
            <div v-if="showInventoryEditor" class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div class="bg-gradient-to-r from-indigo-50 to-purple-50 px-6 py-4 border-b border-indigo-200">
                <div class="flex items-center justify-between">
                  <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center shadow-sm">
                      <i class="fas fa-wrench text-white"></i>
                    </div>
                    <div>
                      <h2 class="text-lg font-bold text-gray-900">
                        {{ editingInventoryId ? 'Edit Inventory' : 'Create New Inventory' }}
                      </h2>
                      <p class="text-sm text-gray-600">Build a device inventory using logical conditions</p>
                    </div>
                  </div>
                  <button @click="cancelInventoryEdit" class="p-2 hover:bg-white/50 rounded-lg transition-colors">
                    <i class="fas fa-times text-gray-500"></i>
                  </button>
                </div>
              </div>

              <div class="p-6 space-y-6">
                <!-- Name and Description -->
                <div class="bg-gradient-to-br from-gray-50 to-white rounded-xl border border-gray-200 p-5 shadow-sm space-y-4">
                  <h3 class="text-sm font-bold text-gray-900 uppercase tracking-wide flex items-center">
                    <i class="fas fa-info-circle text-primary-500 mr-2"></i>
                    Basic Information
                  </h3>
                  <div>
                    <label class="block text-sm font-semibold text-gray-700 mb-2">
                      Inventory Name <span class="text-red-500">*</span>
                    </label>
                    <input
                      v-model="inventoryForm.name"
                      type="text"
                      class="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all shadow-sm"
                      placeholder="e.g., Production Routers"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-gray-700 mb-2">Description</label>
                    <textarea
                      v-model="inventoryForm.description"
                      class="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all resize-none shadow-sm"
                      rows="3"
                      placeholder="Describe the purpose of this inventory..."
                    ></textarea>
                  </div>
                </div>

              <!-- Logical Operations Builder -->
              <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-200 p-5 shadow-sm space-y-4">
                <h3 class="text-sm font-bold text-gray-900 uppercase tracking-wide flex items-center">
                  <i class="fas fa-filter text-blue-500 mr-2"></i>
                  Device Filters & Conditions
                </h3>
                
                <!-- Current Conditions -->
                <div v-if="inventoryConditions.length > 0" class="space-y-2">
                  <div
                    v-for="(condition, index) in inventoryConditions"
                    :key="index"
                    class="flex items-center space-x-3 bg-white border border-gray-200 p-4 rounded-lg hover:border-blue-300 transition-all shadow-sm"
                  >
                    <span v-if="index > 0" class="px-3 py-1 rounded-full text-xs font-bold shadow-sm" :class="{
                      'bg-blue-500 text-white': condition.logic === 'AND',
                      'bg-purple-500 text-white': condition.logic === 'OR',
                      'bg-red-500 text-white': condition.logic === 'NOT'
                    }">
                      {{ condition.logic }}
                    </span>
                    <span class="text-sm font-bold text-gray-900">{{ getFieldLabel(condition.field) }}</span>
                    <span class="text-sm text-gray-500 font-medium">{{ condition.operator }}</span>
                    <span class="text-sm font-bold text-primary-600 flex-1">{{ condition.value }}</span>
                    <button
                      @click="removeInventoryCondition(index)"
                      class="p-2 bg-red-50 hover:bg-red-100 text-red-600 rounded-lg transition-colors shadow-sm flex-shrink-0"
                      title="Remove condition"
                    >
                      <i class="fas fa-trash text-xs"></i>
                    </button>
                  </div>
                </div>
                
                <div v-else class="text-center py-8 bg-white rounded-lg border border-dashed border-gray-300">
                  <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <i class="fas fa-filter text-2xl text-gray-300"></i>
                  </div>
                  <p class="text-gray-500 font-medium">No conditions added yet</p>
                  <p class="text-sm text-gray-400 mt-1">Add your first condition below to start building your inventory</p>
                </div>

                <!-- Add Condition Form -->
                <div class="bg-white rounded-xl border-2 border-blue-200 p-5 shadow-sm">
                  <h4 class="text-sm font-bold text-gray-900 mb-4 flex items-center">
                    <i class="fas fa-plus-circle text-green-500 mr-2"></i>
                    Add New Condition
                  </h4>
                  <div class="grid grid-cols-1 md:grid-cols-5 gap-3 items-end">
                    <div v-if="inventoryConditions.length > 0">
                      <label class="block text-sm font-semibold text-gray-700 mb-2">Logic Operator</label>
                      <select v-model="currentInventoryLogic" class="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 font-medium shadow-sm">
                        <option value="AND">AND</option>
                        <option value="OR">OR</option>
                        <option value="NOT">NOT</option>
                      </select>
                    </div>
                    <div>
                      <label class="block text-sm font-semibold text-gray-700 mb-2">Field</label>
                      <select
                        v-model="currentInventoryField"
                        @change="onInventoryFieldChange"
                        class="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 shadow-sm"
                      >
                        <option value="">Select field...</option>
                        <option v-for="field in inventoryFieldOptions" :key="field.value" :value="field.value">
                          {{ field.label }}
                        </option>
                      </select>
                    </div>
                    <div>
                      <label class="block text-sm font-semibold text-gray-700 mb-2">Operator</label>
                      <select v-model="currentInventoryOperator" class="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 shadow-sm">
                        <option v-for="op in inventoryOperatorOptions" :key="op.value" :value="op.value">
                          {{ op.label }}
                        </option>
                      </select>
                    </div>
                    <div>
                      <label class="block text-sm font-semibold text-gray-700 mb-2">Value</label>
                      <select
                        v-if="inventoryFieldValues.length > 0"
                        v-model="currentInventoryValue"
                        class="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 shadow-sm"
                      >
                        <option value="">Select value...</option>
                        <option v-for="val in inventoryFieldValues" :key="val.value" :value="val.value">
                          {{ val.label }}
                        </option>
                      </select>
                      <input
                        v-else
                        v-model="currentInventoryValue"
                        type="text"
                        class="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 shadow-sm"
                        placeholder="Enter value..."
                      />
                    </div>
                    <button
                      @click="addInventoryCondition"
                      :disabled="!currentInventoryField || !currentInventoryValue"
                      class="px-6 py-2.5 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 disabled:from-gray-300 disabled:to-gray-400 text-white font-medium rounded-lg shadow-sm transition-all duration-200 hover:shadow-md transform hover:-translate-y-0.5 disabled:transform-none flex items-center justify-center"
                    >
                      <i class="fas fa-plus mr-2"></i>
                      Add
                    </button>
                  </div>
                </div>
              </div>

              <!-- Action Buttons -->
              <div class="flex items-center justify-between pt-4 border-t border-gray-200">
                <button
                  @click="cancelInventoryEdit"
                  :disabled="savingInventory"
                  class="px-6 py-2.5 bg-gray-100 hover:bg-gray-200 disabled:bg-gray-50 text-gray-700 disabled:text-gray-400 font-medium rounded-lg transition-colors"
                >
                  <i class="fas fa-times mr-2"></i>
                  Cancel
                </button>
                <div class="flex gap-3">
                  <button
                    @click="previewCurrentInventory"
                    :disabled="inventoryConditions.length === 0 || loadingInventoryPreview"
                    class="px-6 py-2.5 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 disabled:from-gray-300 disabled:to-gray-400 text-white font-medium rounded-lg shadow-sm transition-all duration-200 hover:shadow-md transform hover:-translate-y-0.5 disabled:transform-none flex items-center"
                  >
                    <i :class="['mr-2', loadingInventoryPreview ? 'fas fa-spinner fa-spin' : 'fas fa-eye']"></i>
                    {{ loadingInventoryPreview ? 'Previewing...' : 'Preview Devices' }}
                  </button>
                  <button
                    @click="saveCurrentInventory"
                    :disabled="!inventoryForm.name || inventoryConditions.length === 0 || savingInventory"
                    class="px-6 py-2.5 bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 disabled:from-gray-300 disabled:to-gray-400 text-white font-medium rounded-lg shadow-sm transition-all duration-200 hover:shadow-md transform hover:-translate-y-0.5 disabled:transform-none flex items-center"
                  >
                    <i :class="['mr-2', savingInventory ? 'fas fa-spinner fa-spin' : 'fas fa-save']"></i>
                    {{ savingInventory ? 'Saving...' : 'Save Inventory' }}
                  </button>
                </div>
              </div>
            </div>
          </div>

            <!-- Preview Results -->
            <div v-if="showInventoryPreview && inventoryPreviewDevices.length > 0" class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div class="bg-gradient-to-r from-green-50 to-emerald-50 px-6 py-4 border-b border-green-200">
                <div class="flex items-center space-x-3">
                  <div class="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center shadow-sm">
                    <i class="fas fa-eye text-white"></i>
                  </div>
                  <div>
                    <h3 class="text-lg font-bold text-gray-900">Preview Results</h3>
                    <p class="text-sm text-gray-600">{{ inventoryPreviewDevices.length }} devices match your conditions</p>
                  </div>
                </div>
              </div>
              
              <div class="p-6">
                <div class="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
                  <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gradient-to-r from-gray-50 to-gray-100">
                      <tr>
                        <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Name</th>
                        <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Location</th>
                        <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Role</th>
                        <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">IP Address</th>
                        <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Status</th>
                      </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                      <tr v-for="device in inventoryPreviewDevices.slice(0, 20)" :key="device.id" class="hover:bg-gray-50 transition-colors">
                        <td class="px-4 py-3 text-sm font-semibold text-gray-900">{{ device.name }}</td>
                        <td class="px-4 py-3 text-sm text-gray-600">{{ device.location || 'N/A' }}</td>
                        <td class="px-4 py-3 text-sm text-gray-600">{{ device.role || 'N/A' }}</td>
                        <td class="px-4 py-3 text-sm text-gray-600 font-mono">{{ device.primary_ip4 || 'N/A' }}</td>
                        <td class="px-4 py-3 text-sm">
                          <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold shadow-sm" :class="{
                            'bg-green-100 text-green-700': device.status?.toLowerCase() === 'active',
                            'bg-gray-100 text-gray-700': device.status?.toLowerCase() !== 'active'
                          }">
                            {{ device.status || 'N/A' }}
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div v-if="inventoryPreviewDevices.length > 20" class="mt-4 flex items-center justify-center bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <i class="fas fa-info-circle text-blue-500 mr-2"></i>
                  <span class="text-sm text-blue-700 font-medium">Showing first 20 of {{ inventoryPreviewDevices.length }} matching devices</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Scheduler Tab -->
          <div v-if="activeTab === 'scheduler'" class="space-y-6">
            <SchedulerManagement />
          </div>

          <!-- Jobs Tab -->
          <div v-if="activeTab === 'jobs'" class="space-y-6">
            <!-- Celery Worker Status -->
            <div class="card p-6">
              <div class="flex items-center justify-between mb-4">
                <h2 class="text-lg font-semibold text-gray-900">Worker Status</h2>
                <div class="flex space-x-2">
                  <button @click="submitTestJob" class="btn-primary" :disabled="!jobStatus.workerActive || submittingTestJob">
                    <i class="fas fa-play mr-2" :class="{ 'animate-spin': submittingTestJob }"></i>
                    {{ submittingTestJob ? 'Starting...' : 'Test Job' }}
                  </button>
                  <button @click="refreshJobStatus" class="btn-secondary" :disabled="loadingJobStatus">
                    <i class="fas fa-sync-alt mr-2" :class="{ 'animate-spin': loadingJobStatus }"></i>
                    {{ loadingJobStatus ? 'Refreshing...' : 'Refresh' }}
                  </button>
                </div>
              </div>
              
              <!-- Worker Information -->
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div class="bg-gray-50 p-4 rounded-lg">
                  <div class="flex items-center justify-between">
                    <span class="text-sm font-medium text-gray-600">Worker Status</span>
                    <div class="flex items-center">
                      <div 
                        :class="[
                          'w-3 h-3 rounded-full mr-2',
                          jobStatus.workerActive ? 'bg-green-500' : 'bg-red-500'
                        ]"
                      ></div>
                      <span :class="jobStatus.workerActive ? 'text-green-700' : 'text-red-700'">
                        {{ jobStatus.workerActive ? 'Active' : 'Inactive' }}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div class="bg-gray-50 p-4 rounded-lg">
                  <div class="flex items-center justify-between">
                    <span class="text-sm font-medium text-gray-600">Queue Size</span>
                    <span class="text-xl font-bold text-blue-600">{{ jobStatus.queueSize || 0 }}</span>
                  </div>
                </div>
                
                <div class="bg-gray-50 p-4 rounded-lg">
                  <div class="flex items-center justify-between">
                    <span class="text-sm font-medium text-gray-600">Running Jobs</span>
                    <span class="text-xl font-bold text-orange-600">{{ jobStatus.activeJobs || 0 }}</span>
                  </div>
                </div>
              </div>

              <!-- Worker Details -->
              <div v-if="jobStatus.workers && jobStatus.workers.length > 0" class="space-y-3">
                <h3 class="text-md font-semibold text-gray-900">Connected Workers</h3>
                <div class="space-y-2">
                  <div 
                    v-for="worker in jobStatus.workers" 
                    :key="worker.name"
                    class="bg-white border border-gray-200 rounded-lg p-3"
                  >
                    <div class="flex items-center justify-between">
                      <div>
                        <span class="font-medium text-gray-900">{{ worker.name }}</span>
                        <span class="text-sm text-gray-500 ml-2">{{ worker.status }}</span>
                      </div>
                      <div class="text-sm text-gray-600">
                        Load: {{ worker.loadavg ? worker.loadavg.join(', ') : 'N/A' }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- No Workers Message -->
              <div v-else class="text-center py-8">
                <div class="text-4xl mb-4">⚠️</div>
                <h3 class="text-lg font-medium text-gray-900 mb-2">No Workers Connected</h3>
                <p class="text-gray-600">Make sure the Celery worker is running.</p>
              </div>
            </div>

            <!-- Recent Jobs -->
            <div class="card p-6">
              <div class="flex items-center justify-between mb-4">
                <h2 class="text-lg font-semibold text-gray-900">Recent Jobs</h2>
                <button 
                  v-if="jobStatus.recentJobs && jobStatus.recentJobs.length > 0"
                  @click="clearJobLogs" 
                  class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition font-medium text-sm flex items-center gap-2"
                  :disabled="clearingJobs"
                >
                  <i class="fas fa-trash-alt" :class="{ 'animate-spin': clearingJobs }"></i>
                  {{ clearingJobs ? 'Clearing...' : 'Clear Jobs' }}
                </button>
              </div>
              
              <div v-if="jobStatus.recentJobs && jobStatus.recentJobs.length > 0" class="space-y-3">
                <div 
                  v-for="job in jobStatus.recentJobs" 
                  :key="job.id"
                  class="bg-white border border-gray-200 rounded-lg p-4"
                >
                  <div class="flex items-center justify-between mb-2">
                    <div class="flex items-center">
                      <span class="font-medium text-gray-900">{{ job.name || job.id }}</span>
                      <span 
                        :class="[
                          'ml-2 px-2 py-1 text-xs rounded-full',
                          job.state === 'SUCCESS' ? 'bg-green-100 text-green-800' :
                          job.state === 'PENDING' ? 'bg-yellow-100 text-yellow-800' :
                          job.state === 'STARTED' ? 'bg-blue-100 text-blue-800' :
                          job.state === 'FAILURE' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'
                        ]"
                      >
                        {{ job.state }}
                      </span>
                    </div>
                    <span class="text-sm text-gray-500">{{ formatJobTime(job.timestamp) }}</span>
                  </div>
                  
                  <div v-if="job.result" class="text-sm text-gray-600 mt-2">
                    <strong>Result:</strong> {{ JSON.stringify(job.result) }}
                  </div>
                  
                  <div v-if="job.traceback" class="text-sm text-red-600 mt-2 bg-red-50 p-2 rounded">
                    <strong>Error:</strong>
                    <pre class="whitespace-pre-wrap text-xs mt-1">{{ job.traceback }}</pre>
                  </div>
                </div>
              </div>
              
              <div v-else class="text-center py-8">
                <div class="text-4xl mb-4">📋</div>
                <h3 class="text-lg font-medium text-gray-900 mb-2">No Recent Jobs</h3>
                <p class="text-gray-600">Job history will appear here when tasks are executed.</p>
              </div>
            </div>
          </div>

          <!-- Cache Tab -->
          <div v-if="activeTab === 'cache'" class="space-y-6">
            <!-- Cache Settings -->
            <div class="card p-6">
              <h2 class="text-lg font-semibold text-gray-900 mb-4">Cache Settings</h2>
              <div class="space-y-4">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                      Default TTL (minutes)
                    </label>
                    <input
                      v-model.number="settings.cache.defaultTtlMinutes"
                      type="number"
                      min="1"
                      max="1440"
                      class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    />
                    <p class="text-xs text-gray-500 mt-1">How long cache entries remain valid</p>
                  </div>

                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                      Auto-refresh Interval (minutes)
                    </label>
                    <input
                      v-model.number="settings.cache.autoRefreshIntervalMinutes"
                      type="number"
                      min="5"
                      max="1440"
                      :disabled="!settings.cache.autoRefreshEnabled"
                      class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    />
                    <p class="text-xs text-gray-500 mt-1">Automatic cache refresh frequency</p>
                  </div>
                </div>

                <div class="space-y-2">
                  <label class="flex items-center">
                    <input
                      v-model="settings.cache.autoRefreshEnabled"
                      type="checkbox"
                      class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span class="ml-2 text-sm text-gray-700">Enable Auto-refresh</span>
                  </label>

                  <label class="flex items-center">
                    <input
                      v-model="settings.cache.cleanExpiredOnStartup"
                      type="checkbox"
                      class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span class="ml-2 text-sm text-gray-700">Clean Expired Cache on Startup</span>
                  </label>
                </div>
              </div>

              <!-- JSON Blob Cache Subsection -->
              <div class="mt-6 pt-6 border-t border-gray-200">
                <h3 class="text-base font-semibold text-gray-900 mb-4">JSON Blob Cache</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                      Default TTL (minutes)
                    </label>
                    <input
                      v-model.number="settings.cache.jsonBlobTtlMinutes"
                      type="number"
                      min="1"
                      max="10080"
                      class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    />
                    <p class="text-xs text-gray-500 mt-1">How long JSON blob cache entries remain valid (max: 7 days)</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Cache Statistics -->
            <div class="card p-6">
              <div class="flex items-center justify-between mb-4">
                <h2 class="text-lg font-semibold text-gray-900">Cache Statistics</h2>
                <button
                  @click="loadCacheStatistics"
                  class="btn-secondary text-sm"
                  :disabled="loadingCacheStats"
                >
                  <i class="fas fa-sync-alt mr-2" :class="{ 'fa-spin': loadingCacheStats }"></i>
                  {{ loadingCacheStats ? 'Loading...' : 'Refresh' }}
                </button>
              </div>

              <div v-if="cacheError" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
                {{ cacheError }}
              </div>

              <div v-if="cacheStatistics" class="space-y-6">
                <!-- Total Counts -->
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div class="bg-blue-50 p-4 rounded-lg border border-blue-200">
                    <div class="text-2xl font-bold text-blue-700">{{ cacheStatistics.total.devices }}</div>
                    <div class="text-sm text-blue-600">Devices</div>
                  </div>
                  <div class="bg-green-50 p-4 rounded-lg border border-green-200">
                    <div class="text-2xl font-bold text-green-700">{{ cacheStatistics.total.interfaces }}</div>
                    <div class="text-sm text-green-600">Interfaces</div>
                  </div>
                  <div class="bg-purple-50 p-4 rounded-lg border border-purple-200">
                    <div class="text-2xl font-bold text-purple-700">{{ cacheStatistics.total.ip_addresses }}</div>
                    <div class="text-sm text-purple-600">IP Addresses</div>
                  </div>
                  <div class="bg-orange-50 p-4 rounded-lg border border-orange-200">
                    <div class="text-2xl font-bold text-orange-700">{{ cacheStatistics.total.arp_entries }}</div>
                    <div class="text-sm text-orange-600">ARP Entries</div>
                  </div>
                  <div class="bg-cyan-50 p-4 rounded-lg border border-cyan-200">
                    <div class="text-2xl font-bold text-cyan-700">{{ cacheStatistics.total.static_routes }}</div>
                    <div class="text-sm text-cyan-600">Static Routes</div>
                  </div>
                  <div class="bg-teal-50 p-4 rounded-lg border border-teal-200">
                    <div class="text-2xl font-bold text-teal-700">{{ cacheStatistics.total.ospf_routes }}</div>
                    <div class="text-sm text-teal-600">OSPF Routes</div>
                  </div>
                  <div class="bg-emerald-50 p-4 rounded-lg border border-emerald-200">
                    <div class="text-2xl font-bold text-emerald-700">{{ cacheStatistics.total.bgp_routes }}</div>
                    <div class="text-sm text-emerald-600">BGP Routes</div>
                  </div>
                  <div class="bg-indigo-50 p-4 rounded-lg border border-indigo-200">
                    <div class="text-2xl font-bold text-indigo-700">{{ cacheStatistics.total.mac_table_entries }}</div>
                    <div class="text-sm text-indigo-600">MAC Table Entries</div>
                  </div>
                  <div class="bg-pink-50 p-4 rounded-lg border border-pink-200">
                    <div class="text-2xl font-bold text-pink-700">{{ cacheStatistics.total.cdp_neighbors }}</div>
                    <div class="text-sm text-pink-600">CDP Neighbors</div>
                  </div>
                  <div class="bg-amber-50 p-4 rounded-lg border border-amber-200">
                    <div class="text-2xl font-bold text-amber-700">{{ cacheStatistics.total.json_blobs }}</div>
                    <div class="text-sm text-amber-600">JSON Blobs</div>
                  </div>
                </div>

                <!-- Cache Status -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div class="border border-gray-200 rounded-lg p-4">
                    <h3 class="text-sm font-semibold text-gray-700 mb-2">Cache Validity</h3>
                    <div class="flex items-center justify-between">
                      <span class="text-green-600">Valid: {{ cacheStatistics.cache_status.valid }}</span>
                      <span class="text-red-600">Expired: {{ cacheStatistics.cache_status.expired }}</span>
                    </div>
                    <div class="mt-2 bg-gray-200 rounded-full h-2">
                      <div
                        class="bg-green-600 h-2 rounded-full"
                        :style="{ width: cacheStatistics.cache_status.valid_percentage + '%' }"
                      ></div>
                    </div>
                    <div class="text-xs text-gray-500 mt-1 text-center">
                      {{ cacheStatistics.cache_status.valid_percentage }}% valid
                    </div>
                  </div>

                  <div class="border border-gray-200 rounded-lg p-4">
                    <h3 class="text-sm font-semibold text-gray-700 mb-2">Polling Status</h3>
                    <div class="flex items-center justify-between">
                      <span class="text-blue-600">Enabled: {{ cacheStatistics.polling.enabled }}</span>
                      <span class="text-gray-600">Disabled: {{ cacheStatistics.polling.disabled }}</span>
                    </div>
                  </div>
                </div>

                <!-- Recent Updates -->
                <div v-if="cacheStatistics.recent_updates.length > 0" class="border border-gray-200 rounded-lg p-4">
                  <h3 class="text-sm font-semibold text-gray-700 mb-2">Recently Updated Devices</h3>
                  <div class="space-y-2">
                    <div
                      v-for="device in cacheStatistics.recent_updates"
                      :key="device.device_id"
                      class="flex items-center justify-between text-sm"
                    >
                      <span class="font-medium text-gray-900">{{ device.device_name }}</span>
                      <span class="text-gray-500">{{ formatTimestamp(device.last_updated) }}</span>
                    </div>
                  </div>
                </div>

                <!-- Top Devices -->
                <div v-if="cacheStatistics.top_devices.length > 0" class="border border-gray-200 rounded-lg p-4">
                  <h3 class="text-sm font-semibold text-gray-700 mb-2">Devices by Interface Count</h3>
                  <div class="space-y-2">
                    <div
                      v-for="device in cacheStatistics.top_devices"
                      :key="device.device_name"
                      class="flex items-center justify-between text-sm"
                    >
                      <span class="font-medium text-gray-900">{{ device.device_name }}</span>
                      <span class="text-gray-500">{{ device.interface_count }} interfaces</span>
                    </div>
                  </div>
                </div>
              </div>

              <div v-else-if="!loadingCacheStats" class="text-center py-8 text-gray-500">
                <i class="fas fa-database text-4xl mb-2"></i>
                <p>Click Refresh to load cache statistics</p>
              </div>
            </div>

            <!-- Cache Browser -->
            <div class="card p-6">
              <h2 class="text-lg font-semibold text-gray-900 mb-4">Cache Browser</h2>

              <!-- View Selector -->
              <div class="flex flex-wrap gap-2 mb-4">
                <button
                  @click="selectedCacheView = 'overview'"
                  :class="[
                    'px-4 py-2 text-sm rounded-lg transition-colors',
                    selectedCacheView === 'overview'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  ]"
                >
                  Overview
                </button>
                <button
                  @click="selectedCacheView = 'devices'; loadCachedDevices()"
                  :class="[
                    'px-4 py-2 text-sm rounded-lg transition-colors',
                    selectedCacheView === 'devices'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  ]"
                >
                  Devices
                </button>
                <button
                  @click="selectedCacheView = 'static_routes'; loadStaticRoutes()"
                  :class="[
                    'px-4 py-2 text-sm rounded-lg transition-colors',
                    selectedCacheView === 'static_routes'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  ]"
                >
                  Static Routes
                </button>
                <button
                  @click="selectedCacheView = 'ospf_routes'; loadOSPFRoutes()"
                  :class="[
                    'px-4 py-2 text-sm rounded-lg transition-colors',
                    selectedCacheView === 'ospf_routes'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  ]"
                >
                  OSPF Routes
                </button>
                <button
                  @click="selectedCacheView = 'bgp_routes'; loadBGPRoutes()"
                  :class="[
                    'px-4 py-2 text-sm rounded-lg transition-colors',
                    selectedCacheView === 'bgp_routes'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  ]"
                >
                  BGP Routes
                </button>
                <button
                  @click="selectedCacheView = 'mac_table'; loadMACTable()"
                  :class="[
                    'px-4 py-2 text-sm rounded-lg transition-colors',
                    selectedCacheView === 'mac_table'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  ]"
                >
                  MAC Table
                </button>
                <button
                  @click="selectedCacheView = 'cdp_neighbors'; loadCDPNeighbors()"
                  :class="[
                    'px-4 py-2 text-sm rounded-lg transition-colors',
                    selectedCacheView === 'cdp_neighbors'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  ]"
                >
                  CDP Neighbors
                </button>
                <button
                  @click="selectedCacheView = 'json_blobs'; loadJSONBlobs()"
                  :class="[
                    'px-4 py-2 text-sm rounded-lg transition-colors',
                    selectedCacheView === 'json_blobs'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  ]"
                >
                  Json
                </button>
              </div>

              <!-- Devices View -->
              <div v-if="selectedCacheView === 'devices'">
                <div v-if="loadingCachedDevices" class="text-center py-8 text-gray-500">
                  <i class="fas fa-spinner fa-spin text-2xl mb-2"></i>
                  <p>Loading cached devices...</p>
                </div>

                <div v-else-if="cachedDevices.length > 0" class="overflow-x-auto">
                  <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                      <tr>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Device Name</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Primary IP</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Platform</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Updated</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Valid Until</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Polling</th>
                      </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                      <tr v-for="device in cachedDevices" :key="device.device_id" class="hover:bg-gray-50">
                        <td class="px-4 py-3 text-sm font-medium">
                          <button
                            @click="openDeviceDetailsModal(device.device_id)"
                            class="text-primary-600 hover:text-primary-800 hover:underline transition-colors"
                          >
                            {{ device.device_name }}
                          </button>
                        </td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ device.primary_ip || '-' }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ device.platform || '-' }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ formatTimestamp(device.last_updated) }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">
                          <span :class="isValidCache(device.cache_valid_until) ? 'text-green-600' : 'text-red-600'">
                            {{ formatTimestamp(device.cache_valid_until) }}
                          </span>
                        </td>
                        <td class="px-4 py-3 text-sm">
                          <span
                            :class="device.polling_enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'"
                            class="px-2 py-1 rounded-full text-xs"
                          >
                            {{ device.polling_enabled ? 'Enabled' : 'Disabled' }}
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <div v-else class="text-center py-8 text-gray-500">
                  <i class="fas fa-inbox text-4xl mb-2"></i>
                  <p>No cached devices found</p>
                </div>
              </div>

              <!-- Static Routes View -->
              <div v-if="selectedCacheView === 'static_routes'">
                <div v-if="loadingStaticRoutes" class="text-center py-8 text-gray-500">
                  <i class="fas fa-spinner fa-spin text-2xl mb-2"></i>
                  <p>Loading static routes...</p>
                </div>
                <div v-else-if="staticRoutes.length > 0" class="overflow-x-auto">
                  <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                      <tr>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Device</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Network</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Next Hop</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Interface</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Metric</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Distance</th>
                      </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                      <tr v-for="route in staticRoutes" :key="route.id" class="hover:bg-gray-50">
                        <td class="px-4 py-3 text-sm text-gray-900">{{ getDeviceName(route.device_id) }}</td>
                        <td class="px-4 py-3 text-sm font-mono text-gray-900">{{ route.network }}</td>
                        <td class="px-4 py-3 text-sm font-mono text-gray-500">{{ route.nexthop_ip || '-' }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ route.interface_name || '-' }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ route.metric || '-' }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ route.distance || '-' }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div v-else class="text-center py-8 text-gray-500">
                  <i class="fas fa-inbox text-4xl mb-2"></i>
                  <p>No static routes cached</p>
                </div>
              </div>

              <!-- OSPF Routes View -->
              <div v-if="selectedCacheView === 'ospf_routes'">
                <div v-if="loadingOSPFRoutes" class="text-center py-8 text-gray-500">
                  <i class="fas fa-spinner fa-spin text-2xl mb-2"></i>
                  <p>Loading OSPF routes...</p>
                </div>
                <div v-else-if="ospfRoutes.length > 0" class="overflow-x-auto">
                  <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                      <tr>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Device</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Network</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Next Hop</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Interface</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Metric</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Area</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                      </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                      <tr v-for="route in ospfRoutes" :key="route.id" class="hover:bg-gray-50">
                        <td class="px-4 py-3 text-sm text-gray-900">{{ getDeviceName(route.device_id) }}</td>
                        <td class="px-4 py-3 text-sm font-mono text-gray-900">{{ route.network }}</td>
                        <td class="px-4 py-3 text-sm font-mono text-gray-500">{{ route.nexthop_ip || '-' }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ route.interface_name || '-' }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ route.metric || '-' }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ route.area || '-' }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ route.route_type || '-' }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div v-else class="text-center py-8 text-gray-500">
                  <i class="fas fa-inbox text-4xl mb-2"></i>
                  <p>No OSPF routes cached</p>
                </div>
              </div>

              <!-- BGP Routes View -->
              <div v-if="selectedCacheView === 'bgp_routes'">
                <div v-if="loadingBGPRoutes" class="text-center py-8 text-gray-500">
                  <i class="fas fa-spinner fa-spin text-2xl mb-2"></i>
                  <p>Loading BGP routes...</p>
                </div>
                <div v-else-if="bgpRoutes.length > 0" class="overflow-x-auto">
                  <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                      <tr>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Device</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Network</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Next Hop</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">AS Path</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Metric</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Local Pref</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                      <tr v-for="route in bgpRoutes" :key="route.id" class="hover:bg-gray-50">
                        <td class="px-4 py-3 text-sm text-gray-900">{{ getDeviceName(route.device_id) }}</td>
                        <td class="px-4 py-3 text-sm font-mono text-gray-900">{{ route.network }}</td>
                        <td class="px-4 py-3 text-sm font-mono text-gray-500">{{ route.nexthop_ip || '-' }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ route.as_path || '-' }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ route.metric || '-' }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ route.local_pref || '-' }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ route.status || '-' }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div v-else class="text-center py-8 text-gray-500">
                  <i class="fas fa-inbox text-4xl mb-2"></i>
                  <p>No BGP routes cached</p>
                </div>
              </div>

              <!-- MAC Address Table View -->
              <div v-if="selectedCacheView === 'mac_table'">
                <div v-if="loadingMACTable" class="text-center py-8 text-gray-500">
                  <i class="fas fa-spinner fa-spin text-2xl mb-2"></i>
                  <p>Loading MAC address table...</p>
                </div>
                <div v-else-if="macTableEntries.length > 0" class="overflow-x-auto">
                  <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                      <tr>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Device</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">MAC Address</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">VLAN</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Interface/Port</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                      </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                      <tr v-for="entry in macTableEntries" :key="entry.id" class="hover:bg-gray-50">
                        <td class="px-4 py-3 text-sm text-gray-900">{{ getDeviceName(entry.device_id) }}</td>
                        <td class="px-4 py-3 text-sm font-mono text-gray-900">{{ entry.mac_address }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ entry.vlan_id || '-' }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ entry.interface_name || '-' }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ entry.entry_type || '-' }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div v-else class="text-center py-8 text-gray-500">
                  <i class="fas fa-inbox text-4xl mb-2"></i>
                  <p>No MAC address table entries cached</p>
                </div>
              </div>

              <!-- CDP Neighbors View -->
              <div v-if="selectedCacheView === 'cdp_neighbors'">
                <div v-if="loadingCDPNeighbors" class="text-center py-8 text-gray-500">
                  <i class="fas fa-spinner fa-spin text-2xl mb-2"></i>
                  <p>Loading CDP neighbors...</p>
                </div>
                <div v-else-if="cdpNeighbors.length > 0" class="overflow-x-auto">
                  <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                      <tr>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Device</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Neighbor</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Neighbor IP</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Local Interface</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Neighbor Interface</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Platform</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Capabilities</th>
                      </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                      <tr v-for="neighbor in cdpNeighbors" :key="neighbor.id" class="hover:bg-gray-50">
                        <td class="px-4 py-3 text-sm text-gray-900">{{ getDeviceName(neighbor.device_id) }}</td>
                        <td class="px-4 py-3 text-sm font-medium text-gray-900">{{ neighbor.neighbor_name }}</td>
                        <td class="px-4 py-3 text-sm font-mono text-gray-500">{{ neighbor.neighbor_ip || '-' }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ neighbor.local_interface }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ neighbor.neighbor_interface || '-' }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ neighbor.platform || '-' }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ neighbor.capabilities || '-' }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div v-else class="text-center py-8 text-gray-500">
                  <i class="fas fa-inbox text-4xl mb-2"></i>
                  <p>No CDP neighbors cached</p>
                </div>
              </div>

              <!-- JSON Blobs View -->
              <div v-if="selectedCacheView === 'json_blobs'">
                <div v-if="loadingJSONBlobs" class="text-center py-8 text-gray-500">
                  <i class="fas fa-spinner fa-spin text-2xl mb-2"></i>
                  <p>Loading JSON blobs...</p>
                </div>
                <div v-else-if="cachedJSONBlobs.length > 0" class="overflow-x-auto">
                  <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                      <tr>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Device</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Command</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Updated</th>
                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Size</th>
                      </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                      <tr v-for="blob in cachedJSONBlobs" :key="blob.id" class="hover:bg-gray-50">
                        <td class="px-4 py-3 text-sm text-gray-900">{{ getDeviceName(blob.device_id) }}</td>
                        <td class="px-4 py-3 text-sm font-mono text-gray-600">{{ blob.command }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ new Date(blob.updated_at).toLocaleString() }}</td>
                        <td class="px-4 py-3 text-sm text-gray-500">{{ blob.json_data ? safeJSONParseArray(blob.json_data).length : 0 }} items</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div v-else class="text-center py-8 text-gray-500">
                  <i class="fas fa-inbox text-4xl mb-2"></i>
                  <p>No JSON blobs cached</p>
                </div>
              </div>

              <!-- Overview (placeholder) -->
              <div v-if="selectedCacheView === 'overview'" class="text-center py-8 text-gray-500">
                <p>Select a view to browse cache data</p>
              </div>
            </div>

            <!-- Actions -->
            <div class="flex justify-end space-x-3">
              <button
                @click="cleanExpiredCache"
                class="btn-secondary"
              >
                <i class="fas fa-trash mr-2"></i>
                Clean Expired Cache
              </button>
              <button
                @click="clearJSONCache"
                class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center"
              >
                <i class="fas fa-trash-alt mr-2"></i>
                Clear JSON Cache
              </button>
              <button
                @click="clearAllCache"
                class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center"
              >
                <i class="fas fa-trash-alt mr-2"></i>
                Clear All Cache
              </button>
              <button
                @click="saveCacheSettings"
                class="btn-primary"
              >
                <i class="fas fa-save mr-2"></i>
                Save Settings
              </button>
            </div>
          </div>

          <!-- Profile Tab -->
          <div v-if="activeTab === 'profile'" class="space-y-6">
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
                      @click="addCredential"
                      class="p-2.5 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-all shadow-sm hover:shadow-md transform hover:-translate-y-0.5"
                      title="Add credential"
                    >
                      <i class="fas fa-plus"></i>
                    </button>
                    <button
                      @click="removeLastCredential"
                      :disabled="settings.credentials.length === 0"
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
                  v-if="settings.credentials.length === 0"
                  class="text-center py-16 bg-gradient-to-br from-gray-50 to-white rounded-xl border border-dashed border-gray-300"
                >
                  <div class="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <i class="fas fa-key text-4xl text-gray-300"></i>
                  </div>
                  <h3 class="text-lg font-semibold text-gray-900 mb-2">No credentials yet</h3>
                  <p class="text-gray-500 mb-6">Add your first credential to get started</p>
                  <button
                    @click="addCredential"
                    class="inline-flex items-center px-5 py-2.5 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg shadow-sm transition-all duration-200"
                  >
                    <i class="fas fa-plus mr-2"></i>
                    Add Credential
                  </button>
                </div>

                <div v-else class="space-y-4">
                  <div
                    v-for="(credential, index) in settings.credentials"
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
                        @click="removeCredential(index)"
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

            <!-- Change Password -->
            <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div class="bg-gradient-to-r from-purple-50 to-pink-50 px-6 py-4 border-b border-purple-200">
                <div class="flex items-center space-x-3">
                  <div class="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg flex items-center justify-center shadow-sm">
                    <i class="fas fa-shield-alt text-white"></i>
                  </div>
                  <div>
                    <h2 class="text-lg font-bold text-gray-900">Change Login Password</h2>
                    <p class="text-sm text-gray-600">Update your account password</p>
                  </div>
                </div>
              </div>

              <div class="p-6">
                <div class="max-w-md space-y-5">
                  <div>
                    <label class="block text-sm font-semibold text-gray-700 mb-2">
                      <i class="fas fa-key text-gray-500 mr-1"></i>
                      Current Password
                    </label>
                    <input
                      v-model="passwordChange.currentPassword"
                      type="password"
                      placeholder="Enter current password"
                      class="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all shadow-sm"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-gray-700 mb-2">
                      <i class="fas fa-lock text-green-500 mr-1"></i>
                      New Password
                    </label>
                    <input
                      v-model="passwordChange.newPassword"
                      type="password"
                      placeholder="Enter new password"
                      class="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all shadow-sm"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-semibold text-gray-700 mb-2">
                      <i class="fas fa-check-circle text-blue-500 mr-1"></i>
                      Confirm New Password
                    </label>
                    <input
                      v-model="passwordChange.confirmPassword"
                      type="password"
                      placeholder="Confirm new password"
                      class="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all shadow-sm"
                    />
                  </div>
                  
                  <!-- Password strength indicator -->
                  <div v-if="passwordChange.newPassword" class="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <div class="flex items-start space-x-2">
                      <i class="fas fa-info-circle text-blue-500 mt-0.5"></i>
                      <div class="text-sm text-blue-700">
                        <p class="font-semibold mb-1">Password requirements:</p>
                        <ul class="list-disc list-inside space-y-0.5 text-xs">
                          <li>At least 8 characters long</li>
                          <li>Contains uppercase and lowercase letters</li>
                          <li>Includes numbers and special characters</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  <div class="pt-2">
                    <button
                      @click="changePassword"
                      :disabled="changingPassword || !isPasswordChangeValid"
                      class="w-full px-6 py-3 bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 disabled:from-gray-300 disabled:to-gray-400 text-white font-medium rounded-lg shadow-sm transition-all duration-200 hover:shadow-md transform hover:-translate-y-0.5 disabled:transform-none flex items-center justify-center"
                    >
                      <i :class="['mr-2', changingPassword ? 'fas fa-spinner fa-spin' : 'fas fa-sync-alt']"></i>
                      {{ changingPassword ? 'Changing Password...' : 'Change Password' }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Save Button (for General and Plugins tabs only, NOT for inventory) -->
          <div v-if="activeTab !== 'profile' && activeTab !== 'canvas' && activeTab !== 'commands' && activeTab !== 'cache' && activeTab !== 'jobs' && activeTab !== 'scheduler' && activeTab !== 'inventory'" class="flex justify-end">
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

          <!-- Template Dialog -->
          <div
            v-if="showTemplateDialog"
            class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            @click.self="closeTemplateDialog"
          >
            <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <div class="flex items-center justify-between mb-6">
                <h3 class="text-xl font-semibold text-gray-900">
                  {{ editingTemplate ? 'Edit Template' : 'Add Template' }}
                </h3>
                <button
                  @click="closeTemplateDialog"
                  class="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <i class="fas fa-times text-xl"></i>
                </button>
              </div>

              <form @submit.prevent="saveTemplate" class="space-y-6">
                <!-- Template Name -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Template Name <span class="text-red-500">*</span>
                  </label>
                  <input
                    v-model="templateForm.name"
                    type="text"
                    required
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., Switch Template"
                  />
                </div>

                <!-- File Upload -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    SVG Icon <span class="text-red-500">*</span>
                  </label>
                  <div class="flex items-center space-x-3">
                    <input
                      type="file"
                      ref="fileInput"
                      @change="onFileSelected"
                      accept=".svg"
                      class="hidden"
                    />
                    <button
                      type="button"
                      @click="$refs.fileInput.click()"
                      class="px-4 py-2 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 transition-colors"
                    >
                      <i class="fas fa-upload mr-2"></i>
                      Choose SVG File
                    </button>
                    <span v-if="selectedFile || templateForm.filename" class="text-sm text-gray-600">
                      {{ selectedFile ? selectedFile.name : templateForm.filename }}
                    </span>
                  </div>
                  <p v-if="uploadError" class="mt-2 text-sm text-red-600">{{ uploadError }}</p>
                </div>

                <!-- Platforms Multi-Select -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Platforms
                  </label>
                  <div class="border border-gray-300 rounded-md p-3 max-h-48 overflow-y-auto">
                    <div v-if="loadingPlatforms" class="text-sm text-gray-500">Loading platforms...</div>
                    <div v-else-if="platforms.length === 0" class="text-sm text-gray-500">No platforms available</div>
                    <div v-else class="space-y-2">
                      <label
                        v-for="platform in platforms"
                        :key="platform.id"
                        class="flex items-center space-x-2 hover:bg-gray-50 p-2 rounded cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          :value="platform.id"
                          v-model="templateForm.platforms"
                          class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span class="text-sm text-gray-700">{{ platform.name }}</span>
                      </label>
                    </div>
                  </div>
                </div>

                <!-- Device Types Multi-Select -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Device Types
                  </label>
                  <div class="border border-gray-300 rounded-md p-3 max-h-48 overflow-y-auto">
                    <div v-if="loadingDeviceTypes" class="text-sm text-gray-500">Loading device types...</div>
                    <div v-else-if="deviceTypes.length === 0" class="text-sm text-gray-500">No device types available</div>
                    <div v-else class="space-y-2">
                      <label
                        v-for="deviceType in deviceTypes"
                        :key="deviceType.model"
                        class="flex items-center space-x-2 hover:bg-gray-50 p-2 rounded cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          :value="deviceType.model"
                          v-model="templateForm.device_types"
                          class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span class="text-sm text-gray-700">
                          {{ deviceType.manufacturer }} {{ deviceType.model }}
                        </span>
                      </label>
                    </div>
                  </div>
                </div>

                <!-- Form Actions -->
                <div class="flex justify-end space-x-3 pt-4 border-t">
                  <button
                    type="button"
                    @click="closeTemplateDialog"
                    class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    :disabled="savingTemplate"
                    class="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
                  >
                    <i v-if="savingTemplate" class="fas fa-spinner fa-spin mr-2"></i>
                    <i v-else class="fas fa-save mr-2"></i>
                    {{ savingTemplate ? 'Saving...' : (editingTemplate ? 'Update Template' : 'Create Template') }}
                  </button>
                </div>
              </form>
            </div>
          </div>

          <!-- Save Button (for Profile tab) -->
          <div v-if="activeTab === 'profile'" class="flex justify-end pt-4">
            <button 
              @click="saveProfile" 
              :disabled="savingProfile"
              class="px-6 py-3 bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 disabled:from-gray-300 disabled:to-gray-400 text-white font-medium rounded-lg shadow-sm transition-all duration-200 hover:shadow-md transform hover:-translate-y-0.5 disabled:transform-none flex items-center"
            >
              <i :class="['mr-2', savingProfile ? 'fas fa-spinner fa-spin' : 'fas fa-save']"></i>
              {{ savingProfile ? 'Saving...' : 'Save Credentials' }}
            </button>
          </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Device Details Modal -->
    <div
      v-if="showDeviceDetailsModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      @click.self="closeDeviceDetailsModal"
    >
      <div class="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        <!-- Modal Header -->
        <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 class="text-xl font-semibold text-gray-900">
              {{ selectedDeviceDetails?.device_name || 'Device Details' }}
            </h2>
            <p v-if="selectedDeviceDetails" class="text-sm text-gray-500 mt-1">
              {{ selectedDeviceDetails.primary_ip }} • {{ selectedDeviceDetails.platform }}
            </p>
          </div>
          <button
            @click="closeDeviceDetailsModal"
            class="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <i class="fas fa-times text-xl"></i>
          </button>
        </div>

        <!-- Modal Content -->
        <div v-if="loadingDeviceDetails" class="p-12 text-center text-gray-500">
          <i class="fas fa-spinner fa-spin text-4xl mb-4"></i>
          <p>Loading device details...</p>
        </div>

        <div v-else-if="selectedDeviceDetails" class="p-6 space-y-6">
          <!-- Device Info -->
          <div class="border border-gray-200 rounded-lg p-4">
            <h3 class="text-lg font-semibold text-gray-900 mb-3">Device Information</h3>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <span class="text-sm font-medium text-gray-500">Device ID:</span>
                <p class="text-sm text-gray-900 font-mono">{{ selectedDeviceDetails.device_id }}</p>
              </div>
              <div>
                <span class="text-sm font-medium text-gray-500">Last Updated:</span>
                <p class="text-sm text-gray-900">{{ formatTimestamp(selectedDeviceDetails.last_updated) }}</p>
              </div>
              <div>
                <span class="text-sm font-medium text-gray-500">Cache Valid Until:</span>
                <p class="text-sm" :class="isValidCache(selectedDeviceDetails.cache_valid_until) ? 'text-green-600' : 'text-red-600'">
                  {{ formatTimestamp(selectedDeviceDetails.cache_valid_until) }}
                </p>
              </div>
              <div>
                <span class="text-sm font-medium text-gray-500">Polling Status:</span>
                <span
                  :class="selectedDeviceDetails.polling_enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'"
                  class="inline-block px-2 py-1 rounded-full text-xs ml-2"
                >
                  {{ selectedDeviceDetails.polling_enabled ? 'Enabled' : 'Disabled' }}
                </span>
              </div>
            </div>
          </div>

          <!-- Interfaces -->
          <div v-if="selectedDeviceDetails.interfaces && selectedDeviceDetails.interfaces.length > 0" class="border border-gray-200 rounded-lg p-4">
            <h3 class="text-lg font-semibold text-gray-900 mb-3">
              Interfaces ({{ selectedDeviceDetails.interfaces.length }})
            </h3>
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">MAC Address</th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Speed</th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Duplex</th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">VLAN</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="iface in selectedDeviceDetails.interfaces" :key="iface.id" class="hover:bg-gray-50">
                    <td class="px-3 py-2 text-sm font-medium text-gray-900">{{ iface.interface_name }}</td>
                    <td class="px-3 py-2 text-sm text-gray-500">{{ iface.description || '-' }}</td>
                    <td class="px-3 py-2 text-sm">
                      <span
                        :class="{
                          'text-green-600': iface.status?.toLowerCase() === 'up',
                          'text-red-600': iface.status?.toLowerCase() === 'down',
                          'text-gray-600': !iface.status || iface.status?.toLowerCase() === 'admin-down'
                        }"
                      >
                        {{ iface.status || '-' }}
                      </span>
                    </td>
                    <td class="px-3 py-2 text-sm text-gray-500 font-mono">{{ iface.mac_address || '-' }}</td>
                    <td class="px-3 py-2 text-sm text-gray-500">{{ iface.speed || '-' }}</td>
                    <td class="px-3 py-2 text-sm text-gray-500">{{ iface.duplex || '-' }}</td>
                    <td class="px-3 py-2 text-sm text-gray-500">{{ iface.vlan_id || '-' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- IP Addresses -->
          <div v-if="selectedDeviceDetails.ip_addresses && selectedDeviceDetails.ip_addresses.length > 0" class="border border-gray-200 rounded-lg p-4">
            <h3 class="text-lg font-semibold text-gray-900 mb-3">
              IP Addresses ({{ selectedDeviceDetails.ip_addresses.length }})
            </h3>
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">IP Address</th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Subnet Mask</th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Interface</th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Version</th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Primary</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="ip in selectedDeviceDetails.ip_addresses" :key="ip.id" class="hover:bg-gray-50">
                    <td class="px-3 py-2 text-sm font-medium text-gray-900 font-mono">{{ ip.ip_address }}</td>
                    <td class="px-3 py-2 text-sm text-gray-500 font-mono">{{ ip.subnet_mask || '-' }}</td>
                    <td class="px-3 py-2 text-sm text-gray-500">{{ ip.interface_name || '-' }}</td>
                    <td class="px-3 py-2 text-sm text-gray-500">IPv{{ ip.ip_version }}</td>
                    <td class="px-3 py-2 text-sm">
                      <span v-if="ip.is_primary" class="text-green-600">
                        <i class="fas fa-check"></i>
                      </span>
                      <span v-else class="text-gray-400">-</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- ARP Entries -->
          <div v-if="selectedDeviceDetails.arp_entries && selectedDeviceDetails.arp_entries.length > 0" class="border border-gray-200 rounded-lg p-4">
            <h3 class="text-lg font-semibold text-gray-900 mb-3">
              ARP Entries ({{ selectedDeviceDetails.arp_entries.length }})
            </h3>
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">IP Address</th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">MAC Address</th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Interface</th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Age</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="arp in selectedDeviceDetails.arp_entries" :key="arp.id" class="hover:bg-gray-50">
                    <td class="px-3 py-2 text-sm font-medium text-gray-900 font-mono">{{ arp.ip_address }}</td>
                    <td class="px-3 py-2 text-sm text-gray-500 font-mono">{{ arp.mac_address }}</td>
                    <td class="px-3 py-2 text-sm text-gray-500">{{ arp.interface_name || '-' }}</td>
                    <td class="px-3 py-2 text-sm text-gray-500">{{ arp.arp_type || '-' }}</td>
                    <td class="px-3 py-2 text-sm text-gray-500">{{ arp.age || '-' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Empty State -->
          <div v-if="!selectedDeviceDetails.interfaces?.length && !selectedDeviceDetails.ip_addresses?.length && !selectedDeviceDetails.arp_entries?.length"
               class="text-center py-8 text-gray-500">
            <i class="fas fa-inbox text-4xl mb-2"></i>
            <p>No cached data available for this device</p>
          </div>
        </div>

        <div v-else class="p-12 text-center text-gray-500">
          <i class="fas fa-exclamation-triangle text-4xl mb-4"></i>
          <p>Failed to load device details</p>
        </div>

        <!-- Modal Footer -->
        <div class="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end">
          <button
            @click="closeDeviceDetailsModal"
            class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import SchedulerManagement from '@/components/SchedulerManagement.vue'
import { useNotificationStore } from '@/stores/notification'
import { canvasApi, type CanvasListItem, makeAuthenticatedRequest } from '@/services/api'
import { useDevicesStore } from '@/stores/devices'
import secureStorage from '@/services/secureStorage'
import { useCommands } from '@/composables/useCommands'
import { safeJSONParse, safeJSONParseArray, safeJSONParseObject } from '@/utils/jsonUtils'
import inventoryService, { type LogicalOperation, type LogicalCondition } from '@/services/inventoryService'

const notificationStore = useNotificationStore()
const router = useRouter()
const route = useRoute()
const deviceStore = useDevicesStore()
const { reloadCommands } = useCommands()

// Persist active tab in sessionStorage to survive re-renders/HMR
// Also check for query parameter on initial load
const getInitialTab = () => {
  const tabFromQuery = route.query.tab as string
  if (tabFromQuery) return tabFromQuery
  return sessionStorage.getItem('settings-active-tab') || 'general'
}
const activeTab = ref(getInitialTab())
const showMobileMenu = ref(false)

// Watch for tab changes and persist to sessionStorage
watch(activeTab, (newTab) => {
  sessionStorage.setItem('settings-active-tab', newTab)
  console.log('📑 Active tab changed to:', newTab)
})

// Watch for route query changes (e.g., when navigating from other components)
watch(() => route.query.tab, (newTab) => {
  if (newTab && typeof newTab === 'string') {
    activeTab.value = newTab
  }
})
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

// Job monitoring state
const loadingJobStatus = ref(false)
const submittingTestJob = ref(false)
const clearingJobs = ref(false)
let jobStatusInterval: number | null = null
const jobStatus = reactive({
  workerActive: false,
  queueSize: 0,
  activeJobs: 0,
  workers: [] as Array<{
    name: string,
    status: string,
    loadavg: number[] | null
  }>,
  recentJobs: [] as Array<{
    id: string,
    name?: string,
    state: string,
    timestamp: string,
    result?: any,
    traceback?: string
  }>
})

const tabs = [
  { id: 'general', name: 'General', icon: 'fas fa-cog' },
  { id: 'plugins', name: 'Plugins', icon: 'fas fa-plug' },
  { id: 'canvas', name: 'Canvas', icon: 'fas fa-layer-group' },
  { id: 'templates', name: 'Templates', icon: 'fas fa-shapes' },
  { id: 'commands', name: 'Commands', icon: 'fas fa-terminal' },
  { id: 'inventory', name: 'Inventory', icon: 'fas fa-list' },
  { id: 'scheduler', name: 'Scheduler', icon: 'fas fa-clock' },
  { id: 'jobs', name: 'Jobs', icon: 'fas fa-tasks' },
  { id: 'cache', name: 'Cache', icon: 'fas fa-database' },
  { id: 'profile', name: 'Profile', icon: 'fas fa-user' },
]

const settings = reactive({
  nautobot: {
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
  netmiko: {
    readTimeout: 10,
    lastRead: null as number | null,
    connTimeout: 10,
    authTimeout: null as number | null,
    bannerTimeout: 15,
    blockingTimeout: 20,
    timeout: 100,
    sessionTimeout: 60,
  },
  canvas: {
    autoSaveEnabled: false,
    autoSaveInterval: 60,
  },
  cache: {
    defaultTtlMinutes: 60,
    autoRefreshEnabled: false,
    autoRefreshIntervalMinutes: 30,
    cleanExpiredOnStartup: true,
    jsonBlobTtlMinutes: 30, // 30 minutes default
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
    id?: number
    name: string
    username: string
    password: string
    purpose: string
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

// Commands state
const commands = ref<Array<{
  id: number
  command: string
  display?: string | null
  template?: string | null
  platform: string
  parser: string
  created_at: string
  updated_at?: string | null
}>>([])
const loadingCommands = ref(false)
const commandsError = ref<string | null>(null)
const editingCommand = ref<any>(null)

// Device Templates state
const deviceTemplates = ref<Array<{
  id: number
  name: string
  filename: string
  platforms: string[]
  device_types: string[]
}>>([])
const loadingTemplates = ref(false)
const templatesError = ref<string | null>(null)
const editingTemplate = ref<any>(null)
const showTemplateDialog = ref(false)
const savingTemplate = ref(false)
const selectedFile = ref<File | null>(null)
const uploadError = ref<string | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

// Platforms and Device Types
const platforms = ref<Array<{ id: string; name: string }>>([])
const deviceTypes = ref<Array<{ model: string; manufacturer: string; display: string }>>([])
const loadingPlatforms = ref(false)
const loadingDeviceTypes = ref(false)

const templateForm = reactive({
  name: '',
  filename: '',
  platforms: [] as string[],
  device_types: [] as string[]
})
const showCommandDialog = ref(false)
const commandForm = reactive({
  command: '',
  display: '',
  template: '',
  platform: 'IOS',
  parser: 'TextFSM'
})

const commandPlatforms = [
  { value: 'IOS', label: 'IOS' },
  { value: 'IOS XE', label: 'IOS XE' },
  { value: 'Nexus', label: 'Nexus' }
]

const parsers = [
  { value: 'TextFSM', label: 'TextFSM' },
  { value: 'TTP', label: 'TTP' },
  { value: 'Scrapli', label: 'Scrapli' }
]

// Inventory management state
const inventories = ref<any[]>([])
const loadingInventories = ref(false)
const inventoriesError = ref<string | null>(null)
const showInventoryEditor = ref(false)
const editingInventoryId = ref<number | null>(null)
const inventoryForm = reactive({
  name: '',
  description: ''
})
const inventoryConditions = ref<Array<{field: string, operator: string, value: string, logic: string}>>([])
const currentInventoryField = ref('')
const currentInventoryOperator = ref('equals')
const currentInventoryValue = ref('')
const currentInventoryLogic = ref('AND')
const inventoryFieldOptions = ref<Array<{value: string, label: string}>>([])
const inventoryOperatorOptions = ref<Array<{value: string, label: string}>>([])
const inventoryFieldValues = ref<Array<{value: string, label: string}>>([])
const loadingInventoryPreview = ref(false)
const savingInventory = ref(false)
const showInventoryPreview = ref(false)
const inventoryPreviewDevices = ref<any[]>([])

// Cache management state
const cacheStatistics = ref<any>(null)
const loadingCacheStats = ref(false)
const cachedDevices = ref<any[]>([])
const loadingCachedDevices = ref(false)
const selectedCacheView = ref<'overview' | 'devices' | 'static_routes' | 'ospf_routes' | 'bgp_routes' | 'mac_table' | 'cdp_neighbors' | 'json_blobs'>('overview')
const cacheError = ref<string | null>(null)
const showDeviceDetailsModal = ref(false)
const selectedDeviceDetails = ref<any>(null)
const loadingDeviceDetails = ref(false)

// Routing cache state
const staticRoutes = ref<any[]>([])
const loadingStaticRoutes = ref(false)
const ospfRoutes = ref<any[]>([])
const loadingOSPFRoutes = ref(false)
const bgpRoutes = ref<any[]>([])
const loadingBGPRoutes = ref(false)

// MAC address table cache state
const macTableEntries = ref<any[]>([])
const loadingMACTable = ref(false)

// CDP neighbors cache state
const cdpNeighbors = ref<any[]>([])
const loadingCDPNeighbors = ref(false)

// JSON blobs cache state
const cachedJSONBlobs = ref<any[]>([])
const loadingJSONBlobs = ref(false)

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

// Commands management functions
const loadCommandsIfNeeded = async () => {
  if (activeTab.value === 'commands' && commands.value.length === 0) {
    await refreshCommands()
  }
}

// Watch activeTab to load canvases, commands, and job status
watch(activeTab, loadCanvasesIfNeeded)
watch(activeTab, loadCommandsIfNeeded)

// Auto-fetch inventories and field options when Inventory tab is selected
watch(activeTab, async (newTab) => {
  if (newTab === 'inventory') {
    await Promise.all([
      loadInventories(),
      loadInventoryFieldOptions()
    ])
  }
})

// Auto-fetch templates and platforms when Templates tab is selected
watch(activeTab, async (newTab) => {
  if (newTab === 'templates') {
    await Promise.all([
      fetchTemplates(),
      fetchPlatforms()
    ])
  }
})

// Also fetch on mount if tabs are already active (from sessionStorage)
onMounted(() => {
  if (activeTab.value === 'templates') {
    console.log('🔄 Templates tab active on mount, fetching templates...')
    Promise.all([
      fetchTemplates(),
      fetchPlatforms()
    ])
  }

  if (activeTab.value === 'inventory') {
    console.log('🔄 Inventory tab active on mount, fetching inventories...')
    Promise.all([
      loadInventories(),
      loadInventoryFieldOptions()
    ])
  }

  // Start job status monitoring if jobs tab is active on mount
  if (activeTab.value === 'jobs') {
    console.log('🔄 Jobs tab active on mount, starting auto-refresh...')
    refreshJobStatus()
    jobStatusInterval = window.setInterval(async () => {
      if (!loadingJobStatus.value) {
        await refreshJobStatus()
      }
    }, 2000)
    console.log('▶️ Started job status auto-refresh on mount')
  }

  // Load cache settings from localStorage
  const savedCacheSettings = localStorage.getItem('cacheSettings')
  if (savedCacheSettings) {
    const parsed = safeJSONParseObject(savedCacheSettings, {})
    settings.cache.defaultTtlMinutes = parsed.defaultTtlMinutes ?? 60
    settings.cache.autoRefreshEnabled = parsed.autoRefreshEnabled ?? false
    settings.cache.autoRefreshIntervalMinutes = parsed.autoRefreshIntervalMinutes ?? 30
    settings.cache.cleanExpiredOnStartup = parsed.cleanExpiredOnStartup ?? true
    settings.cache.jsonBlobTtlMinutes = parsed.jsonBlobTtlMinutes ?? 30
  }
})

// Cleanup: stop auto-refresh when component unmounts
onBeforeUnmount(() => {
  if (jobStatusInterval !== null) {
    clearInterval(jobStatusInterval)
    jobStatusInterval = null
    console.log('🧹 Cleaned up job status auto-refresh on unmount')
  }
})

// Auto-refresh job status when Jobs tab is selected
watch(activeTab, async (newTab, oldTab) => {
  // Clear any existing interval when switching away from jobs tab
  if (oldTab === 'jobs' && jobStatusInterval !== null) {
    clearInterval(jobStatusInterval)
    jobStatusInterval = null
    console.log('⏹ Stopped job status auto-refresh')
  }
  
  if (newTab === 'jobs') {
    // Immediately refresh on tab switch
    await refreshJobStatus()
    
    // Set up auto-refresh every 2 seconds while on jobs tab
    jobStatusInterval = window.setInterval(async () => {
      if (!loadingJobStatus.value) {
        await refreshJobStatus()
      }
    }, 2000)
    console.log('▶️ Started job status auto-refresh (every 2 seconds)')
  }
})

const refreshCommands = async () => {
  loadingCommands.value = true
  commandsError.value = null

  try {
    const response = await makeAuthenticatedRequest('/api/settings/commands')
    if (response.ok) {
      const data = await response.json()
      commands.value = data
    } else {
      throw new Error('Failed to load commands')
    }
  } catch (err) {
    commandsError.value = err instanceof Error ? err.message : 'Failed to load commands'
  } finally {
    loadingCommands.value = false
  }
}

const openCommandDialog = (command?: any) => {
  if (command) {
    editingCommand.value = command
    commandForm.command = command.command
    commandForm.display = command.display || ''
    commandForm.template = command.template || ''
    commandForm.platform = command.platform
    commandForm.parser = command.parser
  } else {
    editingCommand.value = null
    commandForm.command = ''
    commandForm.display = ''
    commandForm.template = ''
    commandForm.platform = 'IOS'
    commandForm.parser = 'TextFSM'
  }
  showCommandDialog.value = true
}

const closeCommandDialog = () => {
  showCommandDialog.value = false
  editingCommand.value = null
  commandForm.command = ''
  commandForm.display = ''
  commandForm.template = ''
  commandForm.platform = 'IOS'
  commandForm.parser = 'TextFSM'
}

const saveCommand = async () => {
  try {
    const payload = {
      command: commandForm.command,
      display: commandForm.display || null,
      template: commandForm.template || null,
      platform: commandForm.platform,
      parser: commandForm.parser,
    }

    let response
    if (editingCommand.value) {
      // Update existing command
      response = await makeAuthenticatedRequest(`/api/settings/commands/${editingCommand.value.id}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      })
    } else {
      // Create new command
      response = await makeAuthenticatedRequest('/api/settings/commands', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
    }

    if (response.ok) {
      notificationStore.addNotification({
        title: 'Success',
        message: `Command ${editingCommand.value ? 'updated' : 'created'} successfully`,
        type: 'success',
      })
      closeCommandDialog()
      await refreshCommands()
      // Also reload the commands cache used by NOCCanvas context menu
      await reloadCommands()
    } else {
      // Handle validation errors
      const errorData = await response.json()
      let errorMessage = `Failed to ${editingCommand.value ? 'update' : 'create'} command`

      if (response.status === 400 && errorData.detail) {
        // Show specific validation error message
        errorMessage = errorData.detail
      }

      notificationStore.addNotification({
        title: 'Error',
        message: errorMessage,
        type: 'error',
      })
    }
  } catch (error) {
    notificationStore.addNotification({
      title: 'Error',
      message: `Failed to ${editingCommand.value ? 'update' : 'create'} command`,
      type: 'error',
    })
  }
}

const deleteCommand = async (command: any) => {
  if (confirm(`Are you sure you want to delete the command "${command.command}"?`)) {
    try {
      const response = await makeAuthenticatedRequest(`/api/settings/commands/${command.id}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        notificationStore.addNotification({
          title: 'Success',
          message: 'Command deleted successfully',
          type: 'success',
        })
        await refreshCommands()
        // Also reload the commands cache used by NOCCanvas context menu
        await reloadCommands()
      } else {
        throw new Error('Failed to delete command')
      }
    } catch (error) {
      notificationStore.addNotification({
        title: 'Error',
        message: 'Failed to delete command',
        type: 'error',
      })
    }
  }
}

// Inventory Functions

const loadInventories = async () => {
  loadingInventories.value = true
  inventoriesError.value = null
  try {
    const items = await inventoryService.getAll()
    inventories.value = items
  } catch (error) {
    console.error('Error loading inventories:', error)
    inventoriesError.value = error instanceof Error ? error.message : 'Failed to load inventories'
  } finally {
    loadingInventories.value = false
  }
}

const loadInventoryFieldOptions = async () => {
  try {
    const options = await inventoryService.getFieldOptions()
    inventoryFieldOptions.value = options.fields
    inventoryOperatorOptions.value = options.operators
  } catch (error) {
    console.error('Error loading field options:', error)
  }
}

const startNewInventory = () => {
  showInventoryEditor.value = true
  editingInventoryId.value = null
  inventoryForm.name = ''
  inventoryForm.description = ''
  inventoryConditions.value = []
  currentInventoryField.value = ''
  currentInventoryValue.value = ''
  currentInventoryLogic.value = 'AND'
  inventoryFieldValues.value = []
  showInventoryPreview.value = false
  inventoryPreviewDevices.value = []
}

const editInventory = async (id: number) => {
  try {
    const inventory = await inventoryService.get(id)
    showInventoryEditor.value = true
    editingInventoryId.value = id
    inventoryForm.name = inventory.name
    inventoryForm.description = inventory.description || ''
    
    // Convert operations to conditions for UI
    inventoryConditions.value = []
    for (const operation of inventory.operations) {
      for (const condition of operation.conditions) {
        inventoryConditions.value.push({
          field: condition.field,
          operator: condition.operator,
          value: condition.value,
          logic: operation.operation_type
        })
      }
    }
  } catch (error) {
    console.error('Error loading inventory:', error)
    notificationStore.addNotification({
      title: 'Error',
      message: 'Failed to load inventory',
      type: 'error',
    })
  }
}

const deleteInventory = async (id: number) => {
  if (confirm('Are you sure you want to delete this inventory?')) {
    try {
      await inventoryService.delete(id)
      notificationStore.addNotification({
        title: 'Success',
        message: 'Inventory deleted successfully',
        type: 'success',
      })
      await loadInventories()
    } catch (error) {
      console.error('Error deleting inventory:', error)
      notificationStore.addNotification({
        title: 'Error',
        message: 'Failed to delete inventory',
        type: 'error',
      })
    }
  }
}

const onInventoryFieldChange = async () => {
  currentInventoryValue.value = ''
  inventoryFieldValues.value = []
  
  if (currentInventoryField.value && currentInventoryField.value !== 'custom_fields') {
    try {
      const result = await inventoryService.getFieldValues(currentInventoryField.value)
      inventoryFieldValues.value = result.values
    } catch (error) {
      console.error('Error loading field values:', error)
    }
  }
}

const getFieldLabel = (fieldValue: string): string => {
  const field = inventoryFieldOptions.value.find(f => f.value === fieldValue)
  return field?.label || fieldValue
}

const addInventoryCondition = () => {
  if (!currentInventoryField.value || !currentInventoryValue.value) return
  
  inventoryConditions.value.push({
    field: currentInventoryField.value,
    operator: currentInventoryOperator.value,
    value: currentInventoryValue.value,
    logic: inventoryConditions.value.length > 0 ? currentInventoryLogic.value : 'AND'
  })
  
  // Reset form
  currentInventoryField.value = ''
  currentInventoryOperator.value = 'equals'
  currentInventoryValue.value = ''
  currentInventoryLogic.value = 'AND'
  inventoryFieldValues.value = []
}

const removeInventoryCondition = (index: number) => {
  inventoryConditions.value.splice(index, 1)
}

const buildOperationsFromConditions = (): LogicalOperation[] => {
  if (inventoryConditions.value.length === 0) return []

  if (inventoryConditions.value.length === 1) {
    return [{
      operation_type: 'AND',
      conditions: [{
        field: inventoryConditions.value[0].field,
        operator: inventoryConditions.value[0].operator,
        value: inventoryConditions.value[0].value
      }],
      nested_operations: []
    }]
  }

  // Group conditions by logic operator
  const andConditions: LogicalCondition[] = []
  const orConditions: LogicalCondition[] = []
  const notConditions: LogicalCondition[] = []

  inventoryConditions.value.forEach((condition, index) => {
    const logicType = index === 0 ? 'AND' : condition.logic
    const cond: LogicalCondition = {
      field: condition.field,
      operator: condition.operator,
      value: condition.value
    }

    if (logicType === 'NOT') {
      notConditions.push(cond)
    } else if (logicType === 'OR') {
      orConditions.push(cond)
    } else {
      andConditions.push(cond)
    }
  })

  const operations: LogicalOperation[] = []

  if (orConditions.length > 0) {
    operations.push({
      operation_type: 'OR',
      conditions: orConditions,
      nested_operations: []
    })
  } else if (andConditions.length > 0) {
    operations.push({
      operation_type: 'AND',
      conditions: andConditions,
      nested_operations: []
    })
  }

  notConditions.forEach(condition => {
    operations.push({
      operation_type: 'NOT',
      conditions: [condition],
      nested_operations: []
    })
  })

  return operations
}

const previewCurrentInventory = async () => {
  if (inventoryConditions.value.length === 0) return

  loadingInventoryPreview.value = true
  try {
    const operations = buildOperationsFromConditions()
    const result = await inventoryService.preview(operations)
    inventoryPreviewDevices.value = result.devices
    showInventoryPreview.value = true
  } catch (error) {
    console.error('Error previewing inventory:', error)
    notificationStore.addNotification({
      title: 'Error',
      message: 'Failed to preview inventory',
      type: 'error',
    })
  } finally {
    loadingInventoryPreview.value = false
  }
}

const previewInventoryById = async (id: number) => {
  try {
    const inventory = await inventoryService.get(id)
    loadingInventoryPreview.value = true
    const result = await inventoryService.preview(inventory.operations)
    inventoryPreviewDevices.value = result.devices
    showInventoryPreview.value = true
  } catch (error) {
    console.error('Error previewing inventory:', error)
    notificationStore.addNotification({
      title: 'Error',
      message: 'Failed to preview inventory',
      type: 'error',
    })
  } finally {
    loadingInventoryPreview.value = false
  }
}

const saveCurrentInventory = async () => {
  if (!inventoryForm.name || inventoryConditions.value.length === 0) return

  savingInventory.value = true
  try {
    const operations = buildOperationsFromConditions()
    
    if (editingInventoryId.value) {
      await inventoryService.update(editingInventoryId.value, {
        name: inventoryForm.name,
        description: inventoryForm.description || undefined,
        operations
      })
      notificationStore.addNotification({
        title: 'Success',
        message: 'Inventory updated successfully',
        type: 'success',
      })
    } else {
      await inventoryService.create({
        name: inventoryForm.name,
        description: inventoryForm.description || undefined,
        operations
      })
      notificationStore.addNotification({
        title: 'Success',
        message: 'Inventory created successfully',
        type: 'success',
      })
    }

    showInventoryEditor.value = false
    await loadInventories()
  } catch (error) {
    console.error('Error saving inventory:', error)
    notificationStore.addNotification({
      title: 'Error',
      message: 'Failed to save inventory',
      type: 'error',
    })
  } finally {
    savingInventory.value = false
  }
}

const cancelInventoryEdit = () => {
  showInventoryEditor.value = false
  editingInventoryId.value = null
  inventoryForm.name = ''
  inventoryForm.description = ''
  inventoryConditions.value = []
  showInventoryPreview.value = false
  inventoryPreviewDevices.value = []
}

// Device Templates Functions

const fetchTemplates = async () => {
  loadingTemplates.value = true
  templatesError.value = null
  try {
    console.log('🔄 Fetching templates from API...')
    const response = await makeAuthenticatedRequest('/api/settings/device-templates')
    console.log('📥 Templates API response:', response.status, response.ok)
    if (response.ok) {
      const data = await response.json()
      console.log('✅ Templates data received:', data)
      deviceTemplates.value = data
      console.log('📊 deviceTemplates.value now has', deviceTemplates.value.length, 'items')
    } else {
      throw new Error('Failed to fetch templates')
    }
  } catch (error) {
    console.error('❌ Error fetching templates:', error)
    templatesError.value = 'Failed to load device templates'
  } finally {
    loadingTemplates.value = false
  }
}

const fetchPlatforms = async () => {
  loadingPlatforms.value = true
  try {
    const response = await makeAuthenticatedRequest('/api/nautobot/platforms')
    if (response.ok) {
      const data = await response.json()
      platforms.value = data.map((p: any) => ({ id: p.id, name: p.name }))
    }
  } catch (error) {
    console.error('Error fetching platforms:', error)
  } finally {
    loadingPlatforms.value = false
  }
}

const fetchDeviceTypes = async () => {
  loadingDeviceTypes.value = true
  try {
    const response = await makeAuthenticatedRequest('/api/nautobot/device-types')
    if (response.ok) {
      const data = await response.json()
      deviceTypes.value = data.results.map((dt: any) => ({
        model: dt.model,
        manufacturer: dt.manufacturer,
        display: dt.display
      }))
    }
  } catch (error) {
    console.error('Error fetching device types:', error)
  } finally {
    loadingDeviceTypes.value = false
  }
}

const openTemplateDialog = (template?: any) => {
  editingTemplate.value = template || null
  if (template) {
    templateForm.name = template.name
    templateForm.filename = template.filename
    templateForm.platforms = [...template.platforms]
    templateForm.device_types = [...template.device_types]
  } else {
    templateForm.name = ''
    templateForm.filename = ''
    templateForm.platforms = []
    templateForm.device_types = []
  }
  selectedFile.value = null
  uploadError.value = null
  showTemplateDialog.value = true

  // Fetch platforms and device types when opening dialog
  fetchPlatforms()
  fetchDeviceTypes()
}

const closeTemplateDialog = () => {
  showTemplateDialog.value = false
  editingTemplate.value = null
  selectedFile.value = null
  uploadError.value = null
}

const onFileSelected = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (file) {
    if (!file.name.endsWith('.svg')) {
      uploadError.value = 'Only SVG files are supported'
      selectedFile.value = null
      return
    }
    selectedFile.value = file
    uploadError.value = null
  }
}

const saveTemplate = async () => {
  savingTemplate.value = true
  uploadError.value = null

  try {
    // Upload file if a new one is selected
    let filename = templateForm.filename
    if (selectedFile.value) {
      // SECURITY: Get token for authentication from secure storage only
      const token = secureStorage.getToken()

      if (!token) {
        throw new Error('Authentication token not found')
      }

      // Function to upload file with optional override
      const uploadFile = async (override: boolean = false) => {
        const formData = new FormData()
        formData.append('file', selectedFile.value!)

        const url = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/settings/device-templates/upload${override ? '?override=true' : ''}`

        return await fetch(url, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
            // Don't set Content-Type - browser will set it with boundary for FormData
          },
          body: formData
        })
      }

      // Try to upload file
      let uploadResponse = await uploadFile(false)

      // If file already exists, ask user if they want to override
      if (!uploadResponse.ok) {
        let error
        try {
          error = await uploadResponse.json()
        } catch (e) {
          console.error('Failed to parse upload error response:', e)
          throw new Error(`Upload failed with status ${uploadResponse.status}`)
        }

        if (error.detail && error.detail.includes('already exists')) {
          const confirmOverride = confirm(`The file '${selectedFile.value.name}' already exists. Do you want to override it?`)
          if (!confirmOverride) {
            savingTemplate.value = false
            return
          }
          // User confirmed, upload with override=true
          uploadResponse = await uploadFile(true)

          if (!uploadResponse.ok) {
            let retryError
            try {
              retryError = await uploadResponse.json()
              throw new Error(retryError.detail || 'Failed to upload file even with override')
            } catch (e) {
              throw new Error(`Failed to upload file even with override (Status: ${uploadResponse.status})`)
            }
          }
        } else {
          throw new Error(error.detail || 'Failed to upload file')
        }
      }

      const uploadResult = await uploadResponse.json()
      filename = uploadResult.filename
      console.log('✅ File uploaded successfully:', filename)
    }

    // Validate that we have a filename
    if (!filename) {
      throw new Error('No file selected. Please upload an SVG file.')
    }

    // Create or update template
    const templateData = {
      name: templateForm.name,
      filename: filename,
      platforms: templateForm.platforms,
      device_types: templateForm.device_types
    }

    const url = editingTemplate.value
      ? `/api/settings/device-templates/${editingTemplate.value.id}`
      : '/api/settings/device-templates'

    const method = editingTemplate.value ? 'PUT' : 'POST'

    // SECURITY: Get token to verify it exists from secure storage only
    const token = secureStorage.getToken()
    console.log('📤 Saving template:', {
      isEditing: !!editingTemplate.value,
      editingTemplateId: editingTemplate.value?.id,
      url,
      method,
      templateData,
      hasToken: !!token,
      tokenPreview: token ? `${token.substring(0, 20)}...` : 'NONE'
    })

    const response = await makeAuthenticatedRequest(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(templateData)
    })

    console.log('📥 Template save response:', {
      status: response.status,
      ok: response.ok,
      statusText: response.statusText
    })

    if (!response.ok) {
      let errorMessage = 'Failed to save template'
      try {
        const error = await response.json()
        errorMessage = error.detail || error.message || errorMessage
        console.error('Template save error:', error)
      } catch (e) {
        console.error('Failed to parse error response:', e)
      }
      throw new Error(`${errorMessage} (Status: ${response.status})`)
    }

    notificationStore.addNotification({
      title: 'Success',
      message: `Template ${editingTemplate.value ? 'updated' : 'created'} successfully`,
      type: 'success'
    })

    console.log('✅ Template saved, activeTab before close:', activeTab.value)
    closeTemplateDialog()
    console.log('✅ Dialog closed, activeTab:', activeTab.value)
    await fetchTemplates()
    console.log('✅ Templates fetched, activeTab:', activeTab.value)
  } catch (error: any) {
    uploadError.value = error.message
    notificationStore.addNotification({
      title: 'Error',
      message: error.message || 'Failed to save template',
      type: 'error'
    })
  } finally {
    savingTemplate.value = false
  }
}

const deleteTemplate = async (template: any) => {
  if (confirm(`Are you sure you want to delete the template "${template.name}"?`)) {
    try {
      const response = await makeAuthenticatedRequest(`/api/settings/device-templates/${template.id}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        notificationStore.addNotification({
          title: 'Success',
          message: 'Template deleted successfully',
          type: 'success'
        })
        await fetchTemplates()
      } else {
        throw new Error('Failed to delete template')
      }
    } catch (error) {
      notificationStore.addNotification({
        title: 'Error',
        message: 'Failed to delete template',
        type: 'error'
      })
    }
  }
}

const getPlatformName = (platformId: string) => {
  const platform = platforms.value.find(p => p.id === platformId)
  return platform ? platform.name : platformId
}

const addCredential = () => {
  settings.credentials.push({
    name: '',
    username: '',
    password: '',
    purpose: 'ssh',
  })
}

const removeCredential = async (index: number) => {
  const credential = settings.credentials[index]

  // If the credential has an ID, delete it from the backend
  if (credential.id) {
    try {
      const response = await makeAuthenticatedRequest(`/api/credentials/${credential.id}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        notificationStore.addNotification({
          title: 'Credential Deleted',
          message: `Credential "${credential.name}" has been deleted successfully.`,
          type: 'success',
        })
      } else {
        throw new Error('Failed to delete credential from server')
      }
    } catch (error) {
      notificationStore.addNotification({
        title: 'Delete Failed',
        message: 'Failed to delete credential from server.',
        type: 'error',
      })
      console.error('Failed to delete credential:', error)
      return // Don't remove from local array if server delete failed
    }
  }

  // Remove from local array
  settings.credentials.splice(index, 1)
}

const removeLastCredential = () => {
  if (settings.credentials.length > 0) {
    settings.credentials.pop()
  }
}

const loadCredentials = async () => {
  try {
    const credentialsResponse = await makeAuthenticatedRequest('/api/credentials/with-passwords')
    if (credentialsResponse.ok) {
      const credentialsData = await credentialsResponse.json()
      settings.credentials = credentialsData.credentials.map((cred: any) => ({
        id: cred.id,
        name: cred.name,
        username: cred.username,
        password: cred.password,
        purpose: cred.purpose,
      })) || []
    } else {
      console.error('Failed to load credentials from API')
      settings.credentials = []
    }
  } catch (error) {
    console.error('Failed to load credentials:', error)
    settings.credentials = []
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
        netmiko: settings.netmiko,
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
    // Save/update each credential individually
    const promises = settings.credentials.map(async (credential) => {
      if (credential.id) {
        // Update existing credential
        return makeAuthenticatedRequest(`/api/credentials/${credential.id}`, {
          method: 'PUT',
          body: JSON.stringify({
            name: credential.name,
            username: credential.username,
            password: credential.password,
            purpose: credential.purpose,
          }),
        })
      } else {
        // Create new credential
        return makeAuthenticatedRequest('/api/credentials/', {
          method: 'POST',
          body: JSON.stringify({
            name: credential.name,
            username: credential.username,
            password: credential.password,
            purpose: credential.purpose,
          }),
        })
      }
    })

    const results = await Promise.all(promises)

    // Check if all requests succeeded
    const allSucceeded = results.every(response => response.ok)

    if (allSucceeded) {
      notificationStore.addNotification({
        title: 'Credentials Saved',
        message: 'Your credentials have been saved successfully.',
        type: 'success',
      })
      // Reload credentials to get updated IDs
      await loadCredentials()
    } else {
      throw new Error('Failed to save some credentials')
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

// Cache Management Functions
const loadCacheStatistics = async () => {
  loadingCacheStats.value = true
  cacheError.value = null
  try {
    const response = await makeAuthenticatedRequest('/api/cache/statistics')
    if (response.ok) {
      cacheStatistics.value = await response.json()
    } else {
      throw new Error('Failed to load cache statistics')
    }
  } catch (error) {
    console.error('Failed to load cache statistics:', error)
    cacheError.value = 'Failed to load cache statistics'
  } finally {
    loadingCacheStats.value = false
  }
}

const loadCachedDevices = async () => {
  loadingCachedDevices.value = true
  cacheError.value = null
  try {
    const response = await makeAuthenticatedRequest('/api/cache/devices?limit=1000')
    if (response.ok) {
      cachedDevices.value = await response.json()
    } else {
      throw new Error('Failed to load cached devices')
    }
  } catch (error) {
    console.error('Failed to load cached devices:', error)
    cacheError.value = 'Failed to load cached devices'
  } finally {
    loadingCachedDevices.value = false
  }
}

const openDeviceDetailsModal = async (deviceId: string) => {
  showDeviceDetailsModal.value = true
  loadingDeviceDetails.value = true
  selectedDeviceDetails.value = null

  try {
    const response = await makeAuthenticatedRequest(`/api/cache/devices/${deviceId}/details`)
    if (response.ok) {
      selectedDeviceDetails.value = await response.json()
    } else {
      throw new Error('Failed to load device details')
    }
  } catch (error) {
    console.error('Failed to load device details:', error)
    notificationStore.addNotification({
      title: 'Error',
      message: 'Failed to load device details',
      type: 'error',
    })
  } finally {
    loadingDeviceDetails.value = false
  }
}

const closeDeviceDetailsModal = () => {
  showDeviceDetailsModal.value = false
  selectedDeviceDetails.value = null
}

const loadStaticRoutes = async () => {
  loadingStaticRoutes.value = true
  try {
    const response = await makeAuthenticatedRequest('/api/cache/routes/static?limit=1000')
    if (response.ok) {
      const data = await response.json()
      staticRoutes.value = data.results || []
    }
  } catch (error) {
    console.error('Failed to load static routes:', error)
    notificationStore.addNotification({
      title: 'Error',
      message: 'Failed to load static routes',
      type: 'error',
    })
  } finally {
    loadingStaticRoutes.value = false
  }
}

const loadOSPFRoutes = async () => {
  loadingOSPFRoutes.value = true
  try {
    const response = await makeAuthenticatedRequest('/api/cache/routes/ospf?limit=1000')
    if (response.ok) {
      const data = await response.json()
      ospfRoutes.value = data.results || []
    }
  } catch (error) {
    console.error('Failed to load OSPF routes:', error)
    notificationStore.addNotification({
      title: 'Error',
      message: 'Failed to load OSPF routes',
      type: 'error',
    })
  } finally {
    loadingOSPFRoutes.value = false
  }
}

const loadBGPRoutes = async () => {
  loadingBGPRoutes.value = true
  try {
    const response = await makeAuthenticatedRequest('/api/cache/routes/bgp?limit=1000')
    if (response.ok) {
      const data = await response.json()
      bgpRoutes.value = data.results || []
    }
  } catch (error) {
    console.error('Failed to load BGP routes:', error)
    notificationStore.addNotification({
      title: 'Error',
      message: 'Failed to load BGP routes',
      type: 'error',
    })
  } finally {
    loadingBGPRoutes.value = false
  }
}

const loadMACTable = async () => {
  loadingMACTable.value = true
  try {
    const response = await makeAuthenticatedRequest('/api/cache/mac-table?limit=1000')
    if (response.ok) {
      const data = await response.json()
      macTableEntries.value = data.results || []
    }
  } catch (error) {
    console.error('Failed to load MAC address table:', error)
    notificationStore.addNotification({
      title: 'Error',
      message: 'Failed to load MAC address table',
      type: 'error',
    })
  } finally {
    loadingMACTable.value = false
  }
}

const loadCDPNeighbors = async () => {
  loadingCDPNeighbors.value = true
  try {
    const response = await makeAuthenticatedRequest('/api/cache/cdp-neighbors?limit=1000')
    if (response.ok) {
      const data = await response.json()
      cdpNeighbors.value = data.results || []
    }
  } catch (error) {
    console.error('Failed to load CDP neighbors:', error)
    notificationStore.addNotification({
      title: 'Error',
      message: 'Failed to load CDP neighbors',
      type: 'error',
    })
  } finally {
    loadingCDPNeighbors.value = false
  }
}

const loadJSONBlobs = async () => {
  loadingJSONBlobs.value = true
  try {
    const response = await makeAuthenticatedRequest('/api/cache/json-blobs?limit=1000')
    if (response.ok) {
      const data = await response.json()
      cachedJSONBlobs.value = data.results || []
    }
  } catch (error) {
    console.error('Failed to load JSON blobs:', error)
    notificationStore.addNotification({
      title: 'Error',
      message: 'Failed to load JSON blobs',
      type: 'error',
    })
  } finally {
    loadingJSONBlobs.value = false
  }
}

const getDeviceName = (deviceId: string) => {
  const device = cachedDevices.value.find(d => d.device_id === deviceId)
  return device ? device.device_name : deviceId
}

const cleanExpiredCache = async () => {
  try {
    console.log('🧹 Cleaning expired cache...')
    const response = await makeAuthenticatedRequest('/api/cache/expired', {
      method: 'DELETE'
    })
    console.log('📡 Clean cache response status:', response.status)

    if (response.ok) {
      const result = await response.json()
      console.log('✅ Clean cache result:', result)
      notificationStore.addNotification({
        title: 'Cache Cleaned',
        message: result.message || 'Expired cache entries have been cleaned',
        type: 'success',
      })
      // Reload statistics
      await loadCacheStatistics()
    } else {
      const errorText = await response.text()
      console.error('❌ Clean cache failed:', response.status, errorText)
      throw new Error(`Failed to clean cache: ${response.status} - ${errorText}`)
    }
  } catch (error) {
    console.error('❌ Failed to clean cache:', error)
    notificationStore.addNotification({
      title: 'Clean Failed',
      message: error instanceof Error ? error.message : 'Failed to clean expired cache entries',
      type: 'error',
    })
  }
}

const clearAllCache = async () => {
  // Confirm before clearing all cache
  if (!confirm('⚠️ This will delete ALL cached data including devices, interfaces, IP addresses, ARP entries, routes, MAC table, and CDP neighbors. Are you sure?')) {
    return
  }

  try {
    console.log('🗑️  Clearing all cache...')
    const response = await makeAuthenticatedRequest('/api/cache/all', {
      method: 'DELETE'
    })
    console.log('📡 Clear all cache response status:', response.status)

    if (response.ok) {
      const result = await response.json()
      console.log('✅ Clear all cache result:', result)
      notificationStore.addNotification({
        title: 'All Cache Cleared',
        message: `Cleared ${result.total_cleared} total entries`,
        type: 'success',
      })
      // Reload statistics
      await loadCacheStatistics()
      // Clear browser displays
      cachedDevices.value = []
      staticRoutes.value = []
      ospfRoutes.value = []
      bgpRoutes.value = []
      macTableEntries.value = []
      cdpNeighbors.value = []
      cachedJSONBlobs.value = []
    } else {
      const errorText = await response.text()
      console.error('❌ Clear all cache failed:', response.status, errorText)
      throw new Error(`Failed to clear cache: ${response.status} - ${errorText}`)
    }
  } catch (error) {
    console.error('❌ Failed to clear all cache:', error)
    notificationStore.addNotification({
      title: 'Clear Failed',
      message: error instanceof Error ? error.message : 'Failed to clear all cache',
      type: 'error',
    })
  }
}

const clearJSONCache = async () => {
  // Confirm before clearing JSON cache
  if (!confirm('⚠️ This will delete ALL JSON blob cache data (parsed command outputs). Are you sure?')) {
    return
  }

  try {
    console.log('🗑️  Clearing JSON blob cache...')
    
    // Get all JSON blobs to find unique device IDs
    const response = await makeAuthenticatedRequest('/api/cache/json-blobs?limit=10000')
    if (!response.ok) {
      throw new Error('Failed to fetch JSON blobs')
    }
    
    const data = await response.json()
    const jsonBlobs = data.results || []
    
    // Extract unique device IDs
    const deviceIds = [...new Set(jsonBlobs.map((blob: any) => blob.device_id))]
    console.log(`📋 Found ${deviceIds.length} devices with JSON cache`)
    
    if (deviceIds.length === 0) {
      notificationStore.addNotification({
        title: 'No JSON Cache',
        message: 'No JSON blob cache to clear',
        type: 'info',
      })
      return
    }
    
    // Delete JSON cache for each device
    let successCount = 0
    let failCount = 0
    
    for (const deviceId of deviceIds) {
      try {
        const deleteResponse = await makeAuthenticatedRequest(`/api/cache/json/${deviceId}`, {
          method: 'DELETE'
        })
        
        if (deleteResponse.ok) {
          successCount++
          console.log(`✅ Cleared JSON cache for device ${deviceId}`)
        } else {
          failCount++
          console.error(`❌ Failed to clear JSON cache for device ${deviceId}`)
        }
      } catch (error) {
        failCount++
        console.error(`❌ Error clearing JSON cache for device ${deviceId}:`, error)
      }
    }
    
    // Show result notification
    if (failCount === 0) {
      notificationStore.addNotification({
        title: 'JSON Cache Cleared',
        message: `Successfully cleared JSON cache for ${successCount} device(s)`,
        type: 'success',
      })
    } else {
      notificationStore.addNotification({
        title: 'JSON Cache Partially Cleared',
        message: `Cleared ${successCount} device(s), failed ${failCount}`,
        type: 'warning',
      })
    }
    
    // Reload statistics and JSON blobs
    await loadCacheStatistics()
    await loadJSONBlobs()
    
  } catch (error) {
    console.error('❌ Failed to clear JSON cache:', error)
    notificationStore.addNotification({
      title: 'Clear Failed',
      message: error instanceof Error ? error.message : 'Failed to clear JSON cache',
      type: 'error',
    })
  }
}

const saveCacheSettings = async () => {
  try {
    const cacheSettings = {
      defaultTtlMinutes: settings.cache.defaultTtlMinutes,
      autoRefreshEnabled: settings.cache.autoRefreshEnabled,
      autoRefreshIntervalMinutes: settings.cache.autoRefreshIntervalMinutes,
      cleanExpiredOnStartup: settings.cache.cleanExpiredOnStartup,
      jsonBlobTtlMinutes: settings.cache.jsonBlobTtlMinutes,
    }

    // Save to localStorage as backup
    localStorage.setItem('cacheSettings', JSON.stringify(cacheSettings))

    // Save to backend database
    const response = await makeAuthenticatedRequest('/api/settings/cache/settings', {
      method: 'POST',
      body: JSON.stringify(cacheSettings)
    })

    if (!response.ok) {
      throw new Error('Failed to save cache settings to server')
    }

    console.log('✅ Cache settings saved to database')

    notificationStore.addNotification({
      title: 'Settings Saved',
      message: 'Cache settings have been saved successfully',
      type: 'success',
    })
  } catch (error) {
    console.error('Failed to save cache settings:', error)
    notificationStore.addNotification({
      title: 'Save Failed',
      message: 'Failed to save cache settings',
      type: 'error',
    })
  }
}

const formatTimestamp = (timestamp: string | null) => {
  if (!timestamp) return '-'
  const date = new Date(timestamp)
  return date.toLocaleString()
}

const isValidCache = (validUntil: string | null) => {
  if (!validUntil) return false
  return new Date(validUntil) > new Date()
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

// Job monitoring functions
const refreshJobStatus = async () => {
  loadingJobStatus.value = true
  try {
    const response = await makeAuthenticatedRequest('/api/settings/jobs/status')
    
    if (response.ok) {
      const data = await response.json()
      jobStatus.workerActive = data.workerActive
      jobStatus.queueSize = data.queueSize
      jobStatus.activeJobs = data.activeJobs
      jobStatus.workers = data.workers || []
      jobStatus.recentJobs = data.recentJobs || []
      
      if (data.error) {
        notificationStore.addNotification({
          title: 'Job Status Warning',
          message: data.error,
          type: 'warning',
        })
      }
    } else {
      throw new Error('Failed to fetch job status')
    }
  } catch (error) {
    notificationStore.addNotification({
      title: 'Job Status Error',
      message: 'Failed to fetch job status. Make sure the backend is running.',
      type: 'error',
    })
    console.error('Failed to fetch job status:', error)
  } finally {
    loadingJobStatus.value = false
  }
}

const formatJobTime = (timestamp: string): string => {
  if (!timestamp) return 'Unknown'
  try {
    const date = new Date(timestamp)
    return date.toLocaleString()
  } catch {
    return timestamp
  }
}

const submitTestJob = async () => {
  submittingTestJob.value = true
  try {
    const response = await makeAuthenticatedRequest('/api/settings/jobs/test', {
      method: 'POST'
    })
    
    if (response.ok) {
      const data = await response.json()
      notificationStore.addNotification({
        title: 'Test Job Started',
        message: `Test job submitted with ID: ${data.jobId}`,
        type: 'success',
      })
      // Refresh job status after a short delay to see the new job
      setTimeout(() => refreshJobStatus(), 1000)
    } else {
      throw new Error('Failed to submit test job')
    }
  } catch (error) {
    notificationStore.addNotification({
      title: 'Test Job Error',
      message: 'Failed to submit test job. Make sure the Celery worker is running.',
      type: 'error',
    })
    console.error('Failed to submit test job:', error)
  } finally {
    submittingTestJob.value = false
  }
}

const clearJobLogs = async () => {
  if (!confirm('Are you sure you want to clear all job logs? This will remove all completed job results from Redis.')) {
    return
  }
  
  clearingJobs.value = true
  try {
    const response = await makeAuthenticatedRequest('/api/settings/jobs/clear', {
      method: 'POST'
    })
    
    if (response.ok) {
      const data = await response.json()
      notificationStore.addNotification({
        title: 'Jobs Cleared',
        message: data.message || 'All job logs have been cleared successfully.',
        type: 'success',
      })
      // Refresh to show updated (empty) list
      await refreshJobStatus()
    } else {
      throw new Error('Failed to clear job logs')
    }
  } catch (error) {
    notificationStore.addNotification({
      title: 'Clear Jobs Error',
      message: 'Failed to clear job logs. Please try again.',
      type: 'error',
    })
    console.error('Failed to clear job logs:', error)
  } finally {
    clearingJobs.value = false
  }
}

// Load settings on component mount
const loadSettings = async () => {
  try {
    const response = await makeAuthenticatedRequest('/api/settings/unified')

    if (response.ok) {
      const data = await response.json()
      // Merge data with existing settings to preserve defaults for missing fields
      if (data.canvas) {
        Object.assign(settings.canvas, data.canvas)
      }
      if (data.nautobot) {
        Object.assign(settings.nautobot, data.nautobot)
      }
      if (data.checkmk) {
        Object.assign(settings.checkmk, data.checkmk)
      }
      if (data.netmiko) {
        Object.assign(settings.netmiko, data.netmiko)
      }
      if (data.cache) {
        Object.assign(settings.cache, data.cache)
      }
      if (data.database) {
        Object.assign(settings.database, data.database)
      }
      if (data.credentials) {
        settings.credentials = data.credentials
      }
    } else {
      // Fallback to localStorage
      const saved = localStorage.getItem('noc-canvas-settings')
      if (saved) {
        const savedData = safeJSONParseObject(saved, {})
        if (savedData.canvas) {
          Object.assign(settings.canvas, savedData.canvas)
        }
        if (savedData.nautobot) {
          Object.assign(settings.nautobot, savedData.nautobot)
        }
        if (savedData.checkmk) {
          Object.assign(settings.checkmk, savedData.checkmk)
        }
        if (savedData.netmiko) {
          Object.assign(settings.netmiko, savedData.netmiko)
        }
        if (savedData.cache) {
          Object.assign(settings.cache, savedData.cache)
        }
        if (savedData.database) {
          Object.assign(settings.database, savedData.database)
        }
      }
    }
  } catch (error) {
    console.error('Failed to load settings:', error)
    // Fallback to localStorage
    const saved = localStorage.getItem('noc-canvas-settings')
    if (saved) {
      const savedData = safeJSONParseObject(saved, {})
      if (savedData.canvas) {
        Object.assign(settings.canvas, savedData.canvas)
      }
      if (savedData.nautobot) {
        Object.assign(settings.nautobot, savedData.nautobot)
      }
      if (savedData.checkmk) {
        Object.assign(settings.checkmk, savedData.checkmk)
      }
      if (savedData.netmiko) {
        Object.assign(settings.netmiko, savedData.netmiko)
      }
      if (savedData.cache) {
        Object.assign(settings.cache, savedData.cache)
      }
      if (savedData.database) {
        Object.assign(settings.database, savedData.database)
      }
    }
  }

  // Load credentials
  await loadCredentials()
}

loadSettings()
</script>


<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
