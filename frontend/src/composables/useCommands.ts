import { ref, computed } from 'vue'
import { settingsApi, type DeviceCommand } from '@/services/api'

// Global state for commands (shared across all components)
const commands = ref<DeviceCommand[]>([])
const commandsLoading = ref(false)
const commandsError = ref<string | null>(null)
const commandsLoaded = ref(false)

// Platform mapping from Nautobot platform names to command platform names
const mapPlatformToCommandPlatform = (nautobotPlatform: string | undefined): string | null => {
  if (!nautobotPlatform) return null

  const platformMap: Record<string, string> = {
    'cisco_ios': 'IOS',
    'cisco_xe': 'IOS XE',
    'cisco_nxos': 'Nexus',
  }

  return platformMap[nautobotPlatform.toLowerCase()] || null
}

export function useCommands() {
  // Load commands from backend
  const loadCommands = async (force = false) => {
    // Don't reload if already loaded and not forcing
    if (commandsLoaded.value && !force) {
      return commands.value
    }

    commandsLoading.value = true
    commandsError.value = null

    try {
      console.log('🔄 Loading commands from backend...')
      const loadedCommands = await settingsApi.getDeviceCommands()
      commands.value = loadedCommands
      commandsLoaded.value = true
      console.log('✅ Commands loaded successfully:', loadedCommands.length, 'commands')
      return loadedCommands
    } catch (error) {
      console.warn('⚠️ Failed to load commands (likely due to authentication):', error)
      commandsError.value = error instanceof Error ? error.message : 'Failed to load commands'
      commands.value = []
      // Don't mark as loaded so it can retry later when authenticated
      commandsLoaded.value = false
      return []
    } finally {
      commandsLoading.value = false
    }
  }

  // Reload commands from backend (force reload)
  const reloadCommands = async () => {
    console.log('🔄 Reloading commands...')
    return await loadCommands(true)
  }

  // Get commands for specific platform
  const getCommandsForPlatform = (nautobotPlatform: string | null): DeviceCommand[] => {
    const commandPlatform = mapPlatformToCommandPlatform(nautobotPlatform || undefined)
    if (!commandPlatform) return []

    const filteredCommands = commands.value.filter(cmd => cmd.platform === commandPlatform)
    console.log(`📋 Found ${filteredCommands.length} commands for platform ${commandPlatform} (from ${nautobotPlatform})`)
    return filteredCommands
  }

  // Get device platform from properties
  const getDevicePlatform = (deviceProperties: string | undefined): string | null => {
    if (!deviceProperties) return null

    try {
      const properties = JSON.parse(deviceProperties)
      return properties.platform || null
    } catch {
      return null
    }
  }

  // Initialize commands on app startup
  const initializeCommands = async () => {
    console.log('🚀 Initializing commands on app startup...')
    await loadCommands()
  }

  return {
    // State
    commands: computed(() => commands.value),
    commandsLoading: computed(() => commandsLoading.value),
    commandsError: computed(() => commandsError.value),
    commandsLoaded: computed(() => commandsLoaded.value),

    // Actions
    loadCommands,
    reloadCommands,
    getCommandsForPlatform,
    getDevicePlatform,
    initializeCommands,
    mapPlatformToCommandPlatform,
  }
}