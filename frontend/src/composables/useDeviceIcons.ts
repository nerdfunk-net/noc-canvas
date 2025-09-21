import { ref } from 'vue'

// Import SVG icons
import routerIcon from '/icons/router-svgrepo-com.svg'
import switchIcon from '/icons/switch-svgrepo-com.svg'
import firewallIcon from '/icons/firewall-fire-svgrepo-com.svg'
import shieldIcon from '/icons/shield-user-svgrepo-com.svg'

export const useDeviceIcons = () => {
  const deviceIcons = ref<Map<string, HTMLImageElement>>(new Map())
  const iconsLoaded = ref(false)

  // Load SVG icons as Image objects
  const loadDeviceIcons = async () => {
    const iconPaths = {
      router: routerIcon,
      switch: switchIcon,
      firewall: firewallIcon,
      vpn_gateway: shieldIcon
    }

    const loadPromises = Object.entries(iconPaths).map(([type, iconPath]) => {
      return new Promise<void>((resolve, reject) => {
        const img = new Image()
        img.onload = () => {
          deviceIcons.value.set(type, img)
          resolve()
        }
        img.onerror = () => {
          console.error(`Failed to load icon for ${type}:`, iconPath)
          reject(new Error(`Failed to load ${type} icon`))
        }
        img.src = iconPath
      })
    })

    try {
      await Promise.all(loadPromises)
      iconsLoaded.value = true
      console.log('✅ All device icons loaded successfully')
    } catch (error) {
      console.error('❌ Error loading device icons:', error)
      iconsLoaded.value = false
    }
  }

  // Get device icon (for Konva canvas)
  const getDeviceIcon = (type: string): HTMLImageElement | null => {
    return deviceIcons.value.get(type) || deviceIcons.value.get('router') || null
  }

  // Get device icon URL (for regular HTML)
  const getDeviceIconUrl = (type: string): string => {
    const iconPaths = {
      router: routerIcon,
      switch: switchIcon,
      firewall: firewallIcon,
      vpn_gateway: shieldIcon
    }
    return iconPaths[type as keyof typeof iconPaths] || iconPaths.router
  }

  // Get device icon as emoji (fallback)
  const getDeviceIconEmoji = (type: string): string => {
    const icons = {
      router: '🔀',
      switch: '🔁',
      firewall: '🛡️',
      vpn_gateway: '🔐'
    }
    return icons[type as keyof typeof icons] || '📡'
  }

  return {
    deviceIcons,
    iconsLoaded,
    loadDeviceIcons,
    getDeviceIcon,
    getDeviceIconUrl,
    getDeviceIconEmoji
  }
}