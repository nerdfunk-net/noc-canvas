import { ref } from 'vue'
import { type Device } from '@/stores/devices'
import { makeAuthenticatedRequest } from '@/services/api'

export function useDeviceConfiguration() {
  // Config modal state
  const showConfigModal = ref(false)
  const configModalTitle = ref('')
  const configModalContent = ref('')
  const configModalLoading = ref(false)

  // Show device running config
  const showDeviceRunningConfig = async (device: Device) => {
    configModalTitle.value = `Running Configuration - ${device.name}`
    configModalContent.value = ''
    configModalLoading.value = true
    showConfigModal.value = true

    try {
      const response = await makeAuthenticatedRequest(`/api/devices/${device.id}/config/running`, {
        method: 'GET',
      })

      if (response.ok) {
        const data = await response.json()
        configModalContent.value = data.config || 'No configuration available'
      } else {
        const errorText = await response.text()
        configModalContent.value = `Error: ${errorText}`
      }
    } catch (error) {
      configModalContent.value = `Error: ${error instanceof Error ? error.message : 'Unknown error'}`
    } finally {
      configModalLoading.value = false
    }
  }

  // Show device startup config
  const showDeviceStartupConfig = async (device: Device) => {
    configModalTitle.value = `Startup Configuration - ${device.name}`
    configModalContent.value = ''
    configModalLoading.value = true
    showConfigModal.value = true

    try {
      const response = await makeAuthenticatedRequest(`/api/devices/${device.id}/config/startup`, {
        method: 'GET',
      })

      if (response.ok) {
        const data = await response.json()
        configModalContent.value = data.config || 'No configuration available'
      } else {
        const errorText = await response.text()
        configModalContent.value = `Error: ${errorText}`
      }
    } catch (error) {
      configModalContent.value = `Error: ${error instanceof Error ? error.message : 'Unknown error'}`
    } finally {
      configModalLoading.value = false
    }
  }

  // Show device config changes
  const showDeviceChanges = async (device: Device) => {
    configModalTitle.value = `Configuration Changes - ${device.name}`
    configModalContent.value = ''
    configModalLoading.value = true
    showConfigModal.value = true

    try {
      const response = await makeAuthenticatedRequest(`/api/devices/${device.id}/config/changes`, {
        method: 'GET',
      })

      if (response.ok) {
        const data = await response.json()
        configModalContent.value = data.changes || 'No changes detected'
      } else {
        const errorText = await response.text()
        configModalContent.value = `Error: ${errorText}`
      }
    } catch (error) {
      configModalContent.value = `Error: ${error instanceof Error ? error.message : 'Unknown error'}`
    } finally {
      configModalLoading.value = false
    }
  }

  // Show multi-device config
  const showMultiDeviceConfig = async (devices: Device[]) => {
    configModalTitle.value = `Running Configuration - ${devices.length} Devices`
    configModalContent.value = ''
    configModalLoading.value = true
    showConfigModal.value = true

    try {
      let allConfigs = ''
      for (const device of devices) {
        const response = await makeAuthenticatedRequest(`/api/devices/${device.id}/config/running`, {
          method: 'GET',
        })

        if (response.ok) {
          const data = await response.json()
          allConfigs += `\n\n=== ${device.name} ===\n${data.config || 'No configuration available'}\n`
        } else {
          allConfigs += `\n\n=== ${device.name} ===\nError: Failed to fetch configuration\n`
        }
      }
      configModalContent.value = allConfigs || 'No configurations available'
    } catch (error) {
      configModalContent.value = `Error: ${error instanceof Error ? error.message : 'Unknown error'}`
    } finally {
      configModalLoading.value = false
    }
  }

  // Show multi-device changes
  const showMultiDeviceChanges = async (devices: Device[]) => {
    configModalTitle.value = `Configuration Changes - ${devices.length} Devices`
    configModalContent.value = ''
    configModalLoading.value = true
    showConfigModal.value = true

    try {
      let allChanges = ''
      for (const device of devices) {
        const response = await makeAuthenticatedRequest(`/api/devices/${device.id}/config/changes`, {
          method: 'GET',
        })

        if (response.ok) {
          const data = await response.json()
          allChanges += `\n\n=== ${device.name} ===\n${data.changes || 'No changes detected'}\n`
        } else {
          allChanges += `\n\n=== ${device.name} ===\nError: Failed to fetch changes\n`
        }
      }
      configModalContent.value = allChanges || 'No changes detected'
    } catch (error) {
      configModalContent.value = `Error: ${error instanceof Error ? error.message : 'Unknown error'}`
    } finally {
      configModalLoading.value = false
    }
  }

  // Close config modal
  const closeConfigModal = () => {
    showConfigModal.value = false
    configModalTitle.value = ''
    configModalContent.value = ''
  }

  return {
    // State
    showConfigModal,
    configModalTitle,
    configModalContent,
    configModalLoading,

    // Methods
    showDeviceRunningConfig,
    showDeviceStartupConfig,
    showDeviceChanges,
    showMultiDeviceConfig,
    showMultiDeviceChanges,
    closeConfigModal,
  }
}
