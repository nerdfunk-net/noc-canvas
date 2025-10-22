import { reactive } from 'vue'
import { makeAuthenticatedRequest } from '@/services/api'

interface ConnectionStatus {
  success: boolean
  message: string
}

interface TestingConnectionState {
  nautobot: boolean
  checkmk: boolean
  database: boolean
}

interface ConnectionStatusState {
  nautobot: ConnectionStatus | null
  checkmk: ConnectionStatus | null
  database: ConnectionStatus | null
}

export function usePluginConnection() {
  const testingConnection = reactive<TestingConnectionState>({
    nautobot: false,
    checkmk: false,
    database: false,
  })

  const connectionStatus = reactive<ConnectionStatusState>({
    nautobot: null,
    checkmk: null,
    database: null,
  })

  const testConnection = async (service: 'nautobot' | 'checkmk' | 'database') => {
    testingConnection[service] = true
    connectionStatus[service] = null

    try {
      let endpoint = ''
      const requestBody = {}

      if (service === 'nautobot') {
        endpoint = '/api/settings/plugins/nautobot/test-connection'
      } else if (service === 'checkmk') {
        endpoint = '/api/settings/plugins/checkmk/test-connection'
      } else if (service === 'database') {
        endpoint = '/api/settings/database/test-connection'
      }

      const response = await makeAuthenticatedRequest(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
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

  return {
    testingConnection,
    connectionStatus,
    testConnection,
    testDatabaseConnection,
  }
}
