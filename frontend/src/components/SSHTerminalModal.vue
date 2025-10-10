<template>
  <div
    v-if="show"
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    @click.self="close"
    data-modal="true"
  >
    <div class="bg-white rounded-lg shadow-xl w-[90vw] h-[85vh] max-w-7xl flex flex-col" data-modal="true">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-gray-800 to-gray-900">
        <h3 class="text-xl font-semibold text-white flex items-center gap-2">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          SSH Terminal - {{ deviceName || deviceId }}
          <span
            v-if="connectionStatus === 'connected'"
            class="ml-2 px-3 py-1 text-sm font-medium bg-green-400 text-green-900 rounded-full flex items-center gap-1"
          >
            <span class="w-2 h-2 bg-green-900 rounded-full animate-pulse"></span>
            Connected
          </span>
          <span
            v-else-if="connectionStatus === 'connecting'"
            class="ml-2 px-3 py-1 text-sm font-medium bg-yellow-400 text-yellow-900 rounded-full flex items-center gap-1"
          >
            <span class="w-2 h-2 bg-yellow-900 rounded-full animate-pulse"></span>
            Connecting...
          </span>
          <span
            v-else-if="connectionStatus === 'disconnected'"
            class="ml-2 px-3 py-1 text-sm font-medium bg-red-400 text-red-900 rounded-full"
          >
            Disconnected
          </span>
        </h3>
        <button
          @click.stop="close"
          class="text-white hover:text-gray-300 transition-colors p-2 rounded-lg hover:bg-gray-700"
          type="button"
          aria-label="Close terminal"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Terminal Container -->
      <div class="flex-1 p-0 overflow-hidden bg-black">
        <!-- Error State -->
        <div v-if="error" class="h-full flex items-center justify-center p-6">
          <div class="bg-red-900 bg-opacity-90 border border-red-700 rounded-lg p-6 max-w-md">
            <div class="flex items-start gap-3">
              <svg class="w-6 h-6 text-red-300 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <h4 class="font-medium text-red-100">Connection Error</h4>
                <p class="text-sm text-red-200 mt-1">{{ error }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Terminal -->
        <div v-else ref="terminalContainer" class="w-full h-full"></div>
      </div>

      <!-- Footer with info -->
      <div class="px-6 py-3 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
        <div class="text-sm text-gray-600">
          <span v-if="deviceIp">{{ deviceIp }}</span>
        </div>
        <div class="text-xs text-gray-500">
          Press Ctrl+C to interrupt • Type 'exit' to close connection
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onBeforeUnmount, nextTick } from 'vue'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { WebLinksAddon } from '@xterm/addon-web-links'
import '@xterm/xterm/css/xterm.css'
import { useAuthStore } from '@/stores/auth'

interface Props {
  show: boolean
  deviceId: string
  deviceName?: string
}

const props = defineProps<Props>()
const emit = defineEmits(['close'])

const authStore = useAuthStore()
const terminalContainer = ref<HTMLElement | null>(null)
const terminal = ref<Terminal | null>(null)
const fitAddon = ref<FitAddon | null>(null)
const webLinksAddon = ref<WebLinksAddon | null>(null)
const resizeObserver = ref<ResizeObserver | null>(null)
const websocket = ref<WebSocket | null>(null)
const connectionStatus = ref<'disconnected' | 'connecting' | 'connected'>('disconnected')
const error = ref<string | null>(null)
const deviceIp = ref<string | null>(null)

// Initialize terminal and WebSocket connection
const initTerminal = async () => {
  if (!terminalContainer.value) return

  try {
    // Create terminal instance
    terminal.value = new Terminal({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: 'Menlo, Monaco, "Courier New", monospace',
      theme: {
        background: '#000000',
        foreground: '#ffffff',
        cursor: '#ffffff',
        cursorAccent: '#000000',
        selectionBackground: '#4d4d4d',
        black: '#000000',
        red: '#e06c75',
        green: '#98c379',
        yellow: '#d19a66',
        blue: '#61afef',
        magenta: '#c678dd',
        cyan: '#56b6c2',
        white: '#abb2bf',
        brightBlack: '#5c6370',
        brightRed: '#e06c75',
        brightGreen: '#98c379',
        brightYellow: '#d19a66',
        brightBlue: '#61afef',
        brightMagenta: '#c678dd',
        brightCyan: '#56b6c2',
        brightWhite: '#ffffff',
      },
      allowProposedApi: true,
    })

    // Add fit addon
    fitAddon.value = new FitAddon()
    terminal.value.loadAddon(fitAddon.value)

    // Add web links addon
    webLinksAddon.value = new WebLinksAddon()
    terminal.value.loadAddon(webLinksAddon.value)

    // Open terminal in container
    terminal.value.open(terminalContainer.value)

    // Fit terminal to container
    await nextTick()
    fitAddon.value.fit()

    // Handle terminal input
    terminal.value.onData((data) => {
      if (websocket.value && websocket.value.readyState === WebSocket.OPEN) {
        websocket.value.send(JSON.stringify({
          type: 'input',
          data: data
        }))
      }
    })

    // Handle terminal resize
    terminal.value.onResize((size) => {
      if (websocket.value && websocket.value.readyState === WebSocket.OPEN) {
        websocket.value.send(JSON.stringify({
          type: 'resize',
          cols: size.cols,
          rows: size.rows
        }))
      }
    })

    // Handle window resize
    resizeObserver.value = new ResizeObserver(() => {
      if (fitAddon.value) {
        fitAddon.value.fit()
      }
    })
    resizeObserver.value.observe(terminalContainer.value)

    // Connect WebSocket
    connectWebSocket()

  } catch (err) {
    console.error('Error initializing terminal:', err)
    error.value = 'Failed to initialize terminal'
  }
}

// Connect to SSH WebSocket
const connectWebSocket = () => {
  const token = authStore.token
  if (!token) {
    error.value = 'Not authenticated'
    console.error('❌ SSH Terminal: No authentication token available')
    return
  }

  connectionStatus.value = 'connecting'
  error.value = null

  // Determine WebSocket protocol (ws or wss based on current protocol)
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/api/ws/ssh/${props.deviceId}?token=${token}`

  console.log('🔌 SSH Terminal: Connecting to WebSocket')
  console.log('   Device ID:', props.deviceId)
  console.log('   Device Name:', props.deviceName)
  console.log('   Protocol:', protocol)
  console.log('   Host:', window.location.host)
  console.log('   Full URL:', wsUrl.replace(token, token.substring(0, 20) + '...'))

  websocket.value = new WebSocket(wsUrl)

  websocket.value.onopen = () => {
    console.log('✅ SSH Terminal: WebSocket connection opened')
    connectionStatus.value = 'connected'
  }

  websocket.value.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data)
      console.log('📨 SSH Terminal: Received message:', message.type, message)

      switch (message.type) {
        case 'output':
          // Write output to terminal
          if (terminal.value && message.data) {
            terminal.value.write(message.data)
          }
          break

        case 'connected':
          console.log('✅ SSH Terminal: SSH session connected to device')
          console.log('   Device Name:', message.device_name)
          console.log('   Device IP:', message.device_ip)
          deviceIp.value = message.device_ip
          break

        case 'error':
          console.error('❌ SSH Terminal: Error from backend:', message.message)
          error.value = message.message
          connectionStatus.value = 'disconnected'
          break

        case 'disconnected':
          const reason = message.reason || 'unknown'
          const disconnectMessage = message.message || 'Connection closed'

          console.log('🔌 SSH Terminal: SSH session disconnected')
          console.log('   Reason:', reason)
          console.log('   Message:', disconnectMessage)

          connectionStatus.value = 'disconnected'

          if (terminal.value) {
            if (reason === 'normal') {
              // Normal exit (user typed exit)
              terminal.value.write('\r\n\x1b[32mSession ended.\x1b[0m\r\n')
              // Auto-close modal after 1 second
              setTimeout(() => {
                console.log('✅ SSH Terminal: Auto-closing modal after normal exit')
                close()
              }, 1000)
            } else if (reason === 'error') {
              // Connection error
              terminal.value.write(`\r\n\x1b[31mConnection lost: ${disconnectMessage}\x1b[0m\r\n`)
            } else {
              // Unknown reason
              terminal.value.write('\r\n\x1b[31mConnection closed by remote host.\x1b[0m\r\n')
            }
          }
          break

        default:
          console.warn('⚠️ SSH Terminal: Unknown message type:', message.type, message)
      }
    } catch (err) {
      console.error('❌ SSH Terminal: Error parsing WebSocket message:', err, event.data)
    }
  }

  websocket.value.onerror = (event) => {
    console.error('❌ SSH Terminal: WebSocket error:', event)
    error.value = 'WebSocket connection error'
    connectionStatus.value = 'disconnected'
  }

  websocket.value.onclose = (event) => {
    console.log('🔌 SSH Terminal: WebSocket closed')
    console.log('   Code:', event.code)
    console.log('   Reason:', event.reason || 'No reason provided')
    console.log('   Clean close:', event.wasClean)
    connectionStatus.value = 'disconnected'

    if (terminal.value && !error.value) {
      terminal.value.write('\r\n\x1b[33mConnection closed.\x1b[0m\r\n')
    }
  }
}

// Clean up terminal and WebSocket
const cleanup = () => {
  // Disconnect ResizeObserver first
  if (resizeObserver.value) {
    try {
      resizeObserver.value.disconnect()
    } catch (err) {
      console.error('Error disconnecting resize observer:', err)
    }
    resizeObserver.value = null
  }

  // Close WebSocket
  if (websocket.value) {
    try {
      websocket.value.close()
    } catch (err) {
      console.error('Error closing websocket:', err)
    }
    websocket.value = null
  }

  // Dispose terminal (this will also dispose loaded addons)
  if (terminal.value) {
    try {
      terminal.value.dispose()
    } catch (err) {
      console.error('Error disposing terminal:', err)
    }
    terminal.value = null
  }

  // Clear addon references
  fitAddon.value = null
  webLinksAddon.value = null

  // Reset state
  connectionStatus.value = 'disconnected'
  error.value = null
  deviceIp.value = null
}

// Close modal
const close = () => {
  cleanup()
  emit('close')
}

// Watch for show prop changes
watch(() => props.show, async (newValue) => {
  if (newValue) {
    await nextTick()
    initTerminal()
  } else {
    cleanup()
  }
})

// Cleanup on unmount
onBeforeUnmount(() => {
  cleanup()
})
</script>

<style scoped>
/* Ensure terminal fills container properly */
:deep(.xterm) {
  height: 100%;
  width: 100%;
  padding: 10px;
}

:deep(.xterm-viewport) {
  overflow-y: auto !important;
}
</style>
