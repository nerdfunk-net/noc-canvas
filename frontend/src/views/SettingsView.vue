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
          <div :class="activeTab === 'templates' || activeTab === 'commands' ? 'max-w-7xl' : 'max-w-4xl'">
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
          <GeneralTab
            v-if="activeTab === 'general'"
            :canvas-settings="settings.canvas"
            :database-settings="settings.database"
          />

          <!-- Plugins Tab -->
          <!-- Plugins Tab -->
          <PluginsTab
            v-if="activeTab === 'plugins'"
            :nautobot-settings="settings.nautobot"
            :checkmk-settings="settings.checkmk"
            :netmiko-settings="settings.netmiko"
            :testing-connection="testingConnection"
            :connection-status="connectionStatus"
            @test-connection="testConnection"
          />

          <!-- Templates Tab -->
          <TemplatesTab
            v-if="activeTab === 'templates'"
            :templates="deviceTemplates"
            :loading="loadingTemplates"
            :error="templatesError"
            :get-platform-name="getPlatformName"
            @add-template="openTemplateDialog()"
            @edit-template="openTemplateDialog"
            @delete-template="deleteTemplate"
          />

          <!-- Commands Tab -->
          <CommandsTab
            v-if="activeTab === 'commands'"
            :commands="commands"
            :loading="loadingCommands"
            :error="commandsError"
            @add-command="openCommandDialog()"
            @edit-command="openCommandDialog"
            @delete-command="deleteCommand"
          />

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

                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Type</label>
                    <select
                      v-model="commandForm.type"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      required
                    >
                      <option v-for="commandType in commandTypes" :key="commandType.value" :value="commandType.value">
                        {{ commandType.label }}
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
          <InventoryTab
            v-if="activeTab === 'inventory'"
            :inventories="inventories"
            :loading="loadingInventories"
            :error="inventoriesError"
            @start-new="startNewInventory"
            @edit-inventory="editInventory"
            @preview-inventory="previewInventoryById"
            @delete-inventory="deleteInventory"
          >
            <template #editor>
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
            </template>
          </InventoryTab>

          <!-- Scheduler Tab -->
          <div v-if="activeTab === 'scheduler'" class="space-y-6">
            <SchedulerManagement />
          </div>

          <!-- Jobs Tab -->
          <JobsTab v-if="activeTab === 'jobs'" />

          <!-- Cache Tab -->
          <CacheTab
            v-if="activeTab === 'cache'"
            :default-ttl-minutes="settings.cache.defaultTtlMinutes"
            :auto-refresh-enabled="settings.cache.autoRefreshEnabled"
            :auto-refresh-interval-minutes="settings.cache.autoRefreshIntervalMinutes"
            :clean-expired-on-startup="settings.cache.cleanExpiredOnStartup"
            :json-blob-ttl-minutes="settings.cache.jsonBlobTtlMinutes"
            @save-settings="saveCacheSettings"
          />

          <!-- Profile Tab -->
          <ProfileTab
            v-if="activeTab === 'profile'"
            :credentials="settings.credentials"
            @add-credential="addCredential"
            @remove-credential="removeCredential"
            @remove-last-credential="removeLastCredential"
          >
            <template #password-change>
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
            </template>
          </ProfileTab>

          <!-- Save Button (for General and Plugins tabs only, NOT for inventory) -->
          <div v-if="activeTab !== 'profile' && activeTab !== 'canvas' && activeTab !== 'commands' && activeTab !== 'cache' && activeTab !== 'jobs' && activeTab !== 'scheduler' && activeTab !== 'inventory'" class="flex justify-end">
            <button @click="saveSettings" class="btn-primary" :disabled="saving">
              <i class="fas fa-save mr-2"></i>
              {{ saving ? 'Saving...' : 'Save Settings' }}
            </button>
          </div>

          <!-- Canvas Tab -->
          <CanvasTab
            v-if="activeTab === 'canvas'"
            :canvases="canvases"
            :selected-canvases="selectedCanvases"
            :search-query="canvasSearchQuery"
            :loading="loadingCanvases"
            :error="canvasError"
            @show-rename="showRenameDialog"
            @load-canvas="loadSelectedCanvas"
            @show-delete="showDeleteDialog"
            @refresh="refreshCanvases"
            @toggle-selection="toggleCanvasSelection"
            @update:search-query="canvasSearchQuery = $event"
          />

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
import JobsTab from './settings/tabs/JobsTab.vue'
import GeneralTab from './settings/tabs/GeneralTab.vue'
import PluginsTab from './settings/tabs/PluginsTab.vue'
import TemplatesTab from './settings/tabs/TemplatesTab.vue'
import CommandsTab from './settings/tabs/CommandsTab.vue'
import InventoryTab from './settings/tabs/InventoryTab.vue'
import ProfileTab from './settings/tabs/ProfileTab.vue'
import CanvasTab from './settings/tabs/CanvasTab.vue'
import CacheTab from './settings/tabs/CacheTab.vue'
import { useNotificationStore } from '@/stores/notification'
import { canvasApi, type CanvasListItem, makeAuthenticatedRequest } from '@/services/api'
import { useDevicesStore } from '@/stores/devices'
import secureStorage from '@/services/secureStorage'
import { useCommands } from '@/composables/useCommands'
import { safeJSONParse, safeJSONParseArray, safeJSONParseObject } from '@/utils/jsonUtils'
import inventoryService, { type LogicalOperation, type LogicalCondition } from '@/services/inventoryService'
import { usePluginConnection } from './settings/composables/usePluginConnection'

const notificationStore = useNotificationStore()
const router = useRouter()
const route = useRoute()
const deviceStore = useDevicesStore()
const { reloadCommands } = useCommands()
const { testingConnection, connectionStatus, testConnection, testDatabaseConnection } = usePluginConnection()

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
  parser: 'TextFSM',
  type: 'general'
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

const commandTypes = [
  { value: 'general', label: 'General' },
  { value: 'snapshot', label: 'Snapshot' }
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

  if (activeTab.value === 'commands') {
    console.log('🔄 Commands tab active on mount, fetching commands...')
    refreshCommands()
  }

  if (activeTab.value === 'inventory') {
    console.log('🔄 Inventory tab active on mount, fetching inventories...')
    Promise.all([
      loadInventories(),
      loadInventoryFieldOptions()
    ])
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

// Cleanup when component unmounts
onBeforeUnmount(() => {
  // Cleanup handled by individual tab components
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
    commandForm.type = command.type || 'general'
  } else {
    editingCommand.value = null
    commandForm.command = ''
    commandForm.display = ''
    commandForm.template = ''
    commandForm.platform = 'IOS'
    commandForm.parser = 'TextFSM'
    commandForm.type = 'general'
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
  commandForm.type = 'general'
}

const saveCommand = async () => {
  try {
    const payload = {
      command: commandForm.command,
      display: commandForm.display || null,
      template: commandForm.template || null,
      platform: commandForm.platform,
      parser: commandForm.parser,
      type: commandForm.type,
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
