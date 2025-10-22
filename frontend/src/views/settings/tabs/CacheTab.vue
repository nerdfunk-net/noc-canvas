<template>
  <div class="space-y-6">
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
              v-model.number="defaultTtlMinutesRef"
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
              v-model.number="autoRefreshIntervalMinutesRef"
              type="number"
              min="5"
              max="1440"
              :disabled="!autoRefreshEnabledRef"
              class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            />
            <p class="text-xs text-gray-500 mt-1">Automatic cache refresh frequency</p>
          </div>
        </div>

        <div class="space-y-2">
          <label class="flex items-center">
            <input
              v-model="autoRefreshEnabledRef"
              type="checkbox"
              class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span class="ml-2 text-sm text-gray-700">Enable Auto-refresh</span>
          </label>

          <label class="flex items-center">
            <input
              v-model="cleanExpiredOnStartupRef"
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
              v-model.number="jsonBlobTtlMinutesRef"
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
        @click="handleSaveSettings"
        class="btn-primary"
      >
        <i class="fas fa-save mr-2"></i>
        Save Settings
      </button>
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
  </div>
</template>

<script setup lang="ts">
import { ref, toRefs } from 'vue'
import { useCacheManagement } from '../composables/useCacheManagement'
import { safeJSONParseArray } from '@/utils/jsonUtils'

// Props
const props = defineProps<{
  defaultTtlMinutes: number
  autoRefreshEnabled: boolean
  autoRefreshIntervalMinutes: number
  cleanExpiredOnStartup: boolean
  jsonBlobTtlMinutes: number
}>()

// Emits
const emit = defineEmits<{
  'save-settings': [settings: {
    defaultTtlMinutes: number
    autoRefreshEnabled: boolean
    autoRefreshIntervalMinutes: number
    cleanExpiredOnStartup: boolean
    jsonBlobTtlMinutes: number
  }]
}>()

// Convert props to refs for two-way binding
const {
  defaultTtlMinutes: defaultTtlMinutesRef,
  autoRefreshEnabled: autoRefreshEnabledRef,
  autoRefreshIntervalMinutes: autoRefreshIntervalMinutesRef,
  cleanExpiredOnStartup: cleanExpiredOnStartupRef,
  jsonBlobTtlMinutes: jsonBlobTtlMinutesRef
} = toRefs(props)

// Use cache management composable
const {
  // State
  cacheStatistics,
  loadingCacheStats,
  cachedDevices,
  loadingCachedDevices,
  selectedCacheView,
  cacheError,
  showDeviceDetailsModal,
  selectedDeviceDetails,
  loadingDeviceDetails,
  staticRoutes,
  loadingStaticRoutes,
  ospfRoutes,
  loadingOSPFRoutes,
  bgpRoutes,
  loadingBGPRoutes,
  macTableEntries,
  loadingMACTable,
  cdpNeighbors,
  loadingCDPNeighbors,
  cachedJSONBlobs,
  loadingJSONBlobs,

  // Methods
  loadCacheStatistics,
  loadCachedDevices,
  openDeviceDetailsModal,
  closeDeviceDetailsModal,
  loadStaticRoutes,
  loadOSPFRoutes,
  loadBGPRoutes,
  loadMACTable,
  loadCDPNeighbors,
  loadJSONBlobs,
  getDeviceName,
  cleanExpiredCache,
  clearAllCache,
  clearJSONCache,
  formatTimestamp,
  isValidCache,
} = useCacheManagement()

// Handle save settings
const handleSaveSettings = () => {
  emit('save-settings', {
    defaultTtlMinutes: defaultTtlMinutesRef.value,
    autoRefreshEnabled: autoRefreshEnabledRef.value,
    autoRefreshIntervalMinutes: autoRefreshIntervalMinutesRef.value,
    cleanExpiredOnStartup: cleanExpiredOnStartupRef.value,
    jsonBlobTtlMinutes: jsonBlobTtlMinutesRef.value,
  })
}
</script>
