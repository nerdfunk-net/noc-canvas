import { ref } from 'vue'

export const useDeviceIcons = () => {
  const deviceIcons = ref<Map<string, HTMLImageElement>>(new Map())
  const iconsLoaded = ref(false)

  // Dynamically load icons from public directory
  const loadDeviceIcons = async () => {
    // Define icon paths dynamically (no static imports needed)
    const iconFiles: Record<string, string> = {
      router: '/icons/default-icon.svg',
      switch: '/icons/default-icon.svg',
      firewall: '/icons/default-icon.svg',
      vpn_gateway: '/icons/default-icon.svg',
    }

    const loadPromises = Object.entries(iconFiles).map(([type, iconPath]) => {
      return new Promise<void>((resolve) => {
        const img = new Image()
        img.onload = () => {
          deviceIcons.value.set(type, img)
          resolve()
        }
        img.onerror = () => {
          console.warn(`Failed to load icon for ${type}:`, iconPath, '- will use template system')
          resolve() // Don't reject, just skip
        }
        img.src = iconPath
      })
    })

    try {
      await Promise.all(loadPromises)
      iconsLoaded.value = true
      console.log('✅ Default device icons loaded')
    } catch (error) {
      console.error('❌ Error loading device icons:', error)
      iconsLoaded.value = false
    }
  }

  // Get device icon (for Konva canvas)
  const getDeviceIcon = (type: string): HTMLImageElement | null => {
    return deviceIcons.value.get(type) || null
  }

  // Get device icon URL (for regular HTML) - return default icon
  const getDeviceIconUrl = (type: string): string => {
    return '/icons/default-icon.svg'
  }

  // Get device icon as emoji (fallback)
  const getDeviceIconEmoji = (type: string): string => {
    const icons = {
      router: '🔀',
      switch: '🔁',
      firewall: '🛡️',
      vpn_gateway: '🔐',
    }
    return icons[type as keyof typeof icons] || '📡'
  }

  return {
    deviceIcons,
    iconsLoaded,
    loadDeviceIcons,
    getDeviceIcon,
    getDeviceIconUrl,
    getDeviceIconEmoji,
  }
}
