import { ref } from 'vue'
import { makeAuthenticatedRequest } from '@/services/api'
import { useNotificationStore } from '@/stores/notification'

type CacheView = 'overview' | 'devices' | 'static_routes' | 'ospf_routes' | 'bgp_routes' | 'mac_table' | 'cdp_neighbors' | 'json_blobs'

export function useCacheManagement() {
  const notificationStore = useNotificationStore()

  // State
  const cacheStatistics = ref<any>(null)
  const loadingCacheStats = ref(false)
  const cachedDevices = ref<any[]>([])
  const loadingCachedDevices = ref(false)
  const selectedCacheView = ref<CacheView>('overview')
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

  // Methods
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

  const saveCacheSettings = async (cacheSettings: {
    defaultTtlMinutes: number
    autoRefreshEnabled: boolean
    autoRefreshIntervalMinutes: number
    cleanExpiredOnStartup: boolean
    jsonBlobTtlMinutes: number
  }) => {
    try {
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

  return {
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
    saveCacheSettings,
    formatTimestamp,
    isValidCache,
  }
}
