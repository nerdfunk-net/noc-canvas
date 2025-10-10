/**
 * Utility functions for opening SSH terminals in separate windows
 */

import secureStorage from '@/services/secureStorage'

interface TerminalWindowOptions {
  deviceId: string
  deviceName?: string
  width?: number
  height?: number
}

/**
 * Open an SSH terminal in a new browser window
 * 
 * This allows users to work in the main app while having terminal sessions
 * open simultaneously in separate windows.
 * 
 * @param options - Configuration for the terminal window
 * @returns Window reference or null if popup was blocked
 * 
 * @example
 * ```typescript
 * const terminalWindow = openTerminalWindow({
 *   deviceId: 'device-123',
 *   deviceName: 'router1.example.com',
 *   width: 1000,
 *   height: 700
 * })
 * 
 * if (!terminalWindow) {
 *   alert('Please allow popups for this site')
 * }
 * ```
 */
export function openTerminalWindow(options: TerminalWindowOptions): Window | null {
  const {
    deviceId,
    deviceName = deviceId,
    width = 1000,
    height = 700,
  } = options

  // Get authentication token from secure storage
  const token = secureStorage.getToken()

  if (!token) {
    console.error('❌ Terminal Window: No authentication token found')
    return null
  }

  // Calculate window position (centered on screen)
  const left = (window.screen.width - width) / 2
  const top = (window.screen.height - height) / 2

  // Build URL WITHOUT token (security fix)
  const baseUrl = window.location.origin
  const params = new URLSearchParams({
    deviceId,
    deviceName,
  })
  const url = `${baseUrl}/terminal?${params.toString()}`

  // Window features
  const features = [
    `width=${width}`,
    `height=${height}`,
    `left=${left}`,
    `top=${top}`,
    'menubar=no',
    'toolbar=no',
    'location=no',
    'status=no',
    'resizable=yes',
    'scrollbars=no',
  ].join(',')

  // Open new window
  const terminalWindow = window.open(url, `terminal_${deviceId}`, features)

  if (!terminalWindow) {
    console.error('❌ Terminal Window: Failed to open (popup blocked?)')
    return null
  }

  // SECURITY: Send token via postMessage instead of URL
  // Wait for child window to load before sending message
  const messageListener = (event: MessageEvent) => {
    // Verify origin for security
    if (event.origin !== window.location.origin) {
      return
    }

    // Child window signals it's ready to receive token
    if (event.data && event.data.type === 'terminal_ready') {
      terminalWindow.postMessage({
        type: 'terminal_auth',
        token: token,
        deviceId: deviceId,
        deviceName: deviceName
      }, window.location.origin)

      // Clean up listener after sending token
      window.removeEventListener('message', messageListener)
    }
  }

  window.addEventListener('message', messageListener)

  console.log(`✅ Terminal Window: Opened for device ${deviceName}`)

  return terminalWindow
}

/**
 * Check if popup windows are allowed
 * 
 * @returns true if popups are allowed, false otherwise
 */
export function canOpenPopup(): boolean {
  try {
    const testWindow = window.open('', '', 'width=1,height=1')
    if (testWindow) {
      testWindow.close()
      return true
    }
    return false
  } catch {
    return false
  }
}

/**
 * Open multiple terminal windows at once
 * 
 * Useful for opening terminals to multiple devices simultaneously.
 * Includes a small delay between windows to avoid popup blocker issues.
 * 
 * @param devices - Array of device configurations
 * @returns Array of window references
 */
export async function openMultipleTerminals(
  devices: Array<{ deviceId: string; deviceName?: string }>
): Promise<Array<Window | null>> {
  const windows: Array<Window | null> = []

  for (let i = 0; i < devices.length; i++) {
    const device = devices[i]
    
    // Offset window position for each terminal
    const offset = i * 50
    const terminalWindow = openTerminalWindow({
      ...device,
      width: 1000 + offset,
      height: 700,
    })
    
    windows.push(terminalWindow)
    
    // Small delay to avoid popup blocker
    if (i < devices.length - 1) {
      await new Promise(resolve => setTimeout(resolve, 100))
    }
  }

  return windows
}

/**
 * Close all terminal windows
 * 
 * Note: This only works for windows opened by the current page
 * due to browser security restrictions.
 */
export function closeAllTerminals() {
  // This is limited - we can only close windows we opened
  // and only if they're still on the same origin
  console.log('⚠️ Terminal windows must be closed manually or will close when session ends')
}
