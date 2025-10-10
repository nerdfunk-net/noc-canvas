<template>
  <div class="h-screen w-screen bg-black flex flex-col">
    <!-- Header Bar -->
    <div class="flex items-center justify-between px-4 py-2 border-b border-gray-700 bg-gradient-to-r from-gray-800 to-gray-900">
      <h3 class="text-lg font-semibold text-white flex items-center gap-2">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        SSH Terminal - {{ deviceName || deviceId }}
        <span
          v-if="connectionStatus === 'connected'"
          class="ml-2 px-2 py-1 text-xs font-medium bg-green-400 text-green-900 rounded-full flex items-center gap-1"
        >
          <span class="w-2 h-2 bg-green-900 rounded-full animate-pulse"></span>
          Connected
        </span>
        <span
          v-else-if="connectionStatus === 'connecting'"
          class="ml-2 px-2 py-1 text-xs font-medium bg-yellow-400 text-yellow-900 rounded-full flex items-center gap-1"
        >
          <span class="w-2 h-2 bg-yellow-900 rounded-full animate-pulse"></span>
          Connecting...
        </span>
        <span
          v-else-if="connectionStatus === 'disconnected'"
          class="ml-2 px-2 py-1 text-xs font-medium bg-red-400 text-red-900 rounded-full"
        >
          Disconnected
        </span>
      </h3>
      <button
        @click="closeWindow"
        class="text-white hover:text-gray-300 transition-colors p-1 rounded hover:bg-gray-700"
        type="button"
        aria-label="Close terminal"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Terminal Container -->
    <div class="flex-1 overflow-hidden bg-black">
      <div ref="terminalContainer" class="w-full h-full"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'

const route = useRoute()

// Get parameters from URL query (NO TOKEN - security fix)
const deviceId = ref(route.query.deviceId as string)
const deviceName = ref(route.query.deviceName as string)
// Token will be received via postMessage
const token = ref<string>('')

const terminalContainer = ref<HTMLElement | null>(null)
const terminal = ref<Terminal | null>(null)
const fitAddon = ref<FitAddon | null>(null)
const ws = ref<WebSocket | null>(null)
const connectionStatus = ref<'connecting' | 'connected' | 'disconnected'>('connecting')
const authReceived = ref(false)

const closeWindow = () => {
  if (ws.value) {
    ws.value.close()
  }
  window.close()
}

const connectWebSocket = () => {
  if (!deviceId.value || !token.value) {
    console.error('❌ SSH Terminal: Missing device ID or authentication token')
    connectionStatus.value = 'disconnected'
    return
  }

  console.log('🔌 SSH Terminal: Connecting to WebSocket')
  connectionStatus.value = 'connecting'

  // Construct WebSocket URL WITHOUT token (security fix)
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const wsUrl = `${protocol}//${host}/api/ws/ssh/${deviceId.value}`

  console.log('🔗 WebSocket URL:', wsUrl)
  ws.value = new WebSocket(wsUrl)

  ws.value.onopen = () => {
    console.log('✅ SSH Terminal: WebSocket connection opened')
    // Send authentication token as first message
    if (token.value && ws.value) {
      ws.value.send(JSON.stringify({
        type: 'auth',
        token: token.value
      }))
      connectionStatus.value = 'connected'
    } else {
      console.error('❌ SSH Terminal: No token available for authentication')
      connectionStatus.value = 'disconnected'
    }
  }

  ws.value.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data)
      console.log('📨 SSH Terminal: Received message:', message.type)

      switch (message.type) {
        case 'output':
          if (terminal.value && message.data) {
            terminal.value.write(message.data)
          }
          break

        case 'connected':
          console.log('✅ SSH Terminal: SSH session connected to device')
          connectionStatus.value = 'connected'
          break

        case 'error':
          console.error('❌ SSH Terminal: Error from backend:', message.message)
          if (terminal.value) {
            terminal.value.write(`\r\n\x1b[1;31mError: ${message.message}\x1b[0m\r\n`)
          }
          connectionStatus.value = 'disconnected'
          break

        case 'disconnected':
          console.log('🔌 SSH Terminal: SSH session disconnected')
          connectionStatus.value = 'disconnected'
          if (terminal.value) {
            terminal.value.write('\r\n\x1b[1;33mConnection closed by remote host.\x1b[0m\r\n')
          }
          // Auto-close window after a short delay
          setTimeout(() => {
            window.close()
          }, 2000)
          break

        default:
          console.warn('⚠️ SSH Terminal: Unknown message type:', message.type)
      }
    } catch (err) {
      console.error('❌ SSH Terminal: Error parsing WebSocket message:', err)
    }
  }

  ws.value.onerror = (event) => {
    console.error('❌ SSH Terminal: WebSocket error:', event)
    connectionStatus.value = 'disconnected'
  }

  ws.value.onclose = () => {
    console.log('🔌 SSH Terminal: WebSocket closed')
    connectionStatus.value = 'disconnected'
  }
}

const initializeTerminal = () => {
  if (!terminalContainer.value) {
    console.error('Terminal container not found')
    return
  }

  // Create terminal
  terminal.value = new Terminal({
    cursorBlink: true,
    fontSize: 14,
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    theme: {
      background: '#000000',
      foreground: '#ffffff',
      cursor: '#ffffff',
      cursorAccent: '#000000',
      selectionBackground: 'rgba(255, 255, 255, 0.3)',
    },
    scrollback: 10000,
  })

  // Add fit addon
  fitAddon.value = new FitAddon()
  terminal.value.loadAddon(fitAddon.value)

  // Open terminal
  terminal.value.open(terminalContainer.value)
  fitAddon.value.fit()

  // Handle terminal input
  terminal.value.onData((data) => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify({ type: 'input', data }))
    }
  })

  // Handle window resize
  window.addEventListener('resize', () => {
    if (fitAddon.value && terminal.value) {
      fitAddon.value.fit()
      // Send resize info to backend
      if (ws.value && ws.value.readyState === WebSocket.OPEN) {
        ws.value.send(
          JSON.stringify({
            type: 'resize',
            cols: terminal.value.cols,
            rows: terminal.value.rows,
          })
        )
      }
    }
  })

  // Connect WebSocket after terminal is ready
  connectWebSocket()
}

// SECURITY: Receive authentication token via postMessage
const handlePostMessage = (event: MessageEvent) => {
  // Verify origin for security
  if (event.origin !== window.location.origin) {
    console.warn('⚠️ Ignored message from untrusted origin:', event.origin)
    return
  }

  // Handle authentication message from parent window
  if (event.data && event.data.type === 'terminal_auth') {
    console.log('🔐 SSH Terminal: Received authentication token via postMessage')
    token.value = event.data.token
    authReceived.value = true

    // Initialize terminal once we have authentication
    initializeTerminal()
  }
}

onMounted(() => {
  // Listen for authentication token from parent window
  window.addEventListener('message', handlePostMessage)

  // Signal to parent window that we're ready to receive token
  if (window.opener) {
    window.opener.postMessage({
      type: 'terminal_ready'
    }, window.location.origin)
  } else {
    console.error('❌ SSH Terminal: No parent window found')
  }
})

onBeforeUnmount(() => {
  // Clean up message listener
  window.removeEventListener('message', handlePostMessage)

  if (ws.value) {
    ws.value.close()
  }
  if (terminal.value) {
    terminal.value.dispose()
  }
})
</script>

<style scoped>
/* Ensure terminal takes full height */
.xterm {
  height: 100%;
  width: 100%;
}
</style>
