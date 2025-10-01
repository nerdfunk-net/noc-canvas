import { ref } from 'vue'
import { makeAuthenticatedRequest } from './api'

interface DeviceTemplate {
  id: number
  name: string
  filename: string
  platforms: string[]
  device_types: string[]
}

class TemplateService {
  private templates = ref<DeviceTemplate[]>([])
  private iconCache = new Map<string, HTMLImageElement>()
  private loading = ref(false)

  /**
   * Fetch all device templates from the backend
   */
  async fetchTemplates(): Promise<void> {
    this.loading.value = true
    try {
      const response = await makeAuthenticatedRequest('/api/settings/device-templates')
      if (response.ok) {
        this.templates.value = await response.json()
        console.log('✅ Device templates loaded:', this.templates.value.length)
      }
    } catch (error) {
      console.error('❌ Error fetching device templates:', error)
    } finally {
      this.loading.value = false
    }
  }

  /**
   * Find template by platform or device type
   * Priority: 1. Device type (most specific), 2. Platform, 3. null (default icon)
   */
  findTemplate(platformId?: string, deviceType?: string): DeviceTemplate | null {
    // First priority: try to match by device type (most specific)
    if (deviceType) {
      const byDeviceType = this.templates.value.find(t =>
        t.device_types.includes(deviceType)
      )
      if (byDeviceType) {
        console.log('✅ Template matched by device type:', deviceType, '→', byDeviceType.name)
        return byDeviceType
      }
    }

    // Second priority: try to match by platform
    if (platformId) {
      const byPlatform = this.templates.value.find(t =>
        t.platforms.includes(platformId)
      )
      if (byPlatform) {
        console.log('✅ Template matched by platform:', platformId, '→', byPlatform.name)
        return byPlatform
      }
    }

    return null
  }

  /**
   * Load icon as Image object for Konva (with caching)
   */
  async loadIcon(filename: string): Promise<HTMLImageElement | null> {
    // Check cache first
    if (this.iconCache.has(filename)) {
      return this.iconCache.get(filename)!
    }

    return new Promise((resolve) => {
      const img = new Image()
      img.crossOrigin = 'anonymous' // Enable CORS for canvas rendering

      img.onload = () => {
        this.iconCache.set(filename, img)
        console.log('✅ Icon loaded:', filename)
        resolve(img)
      }

      img.onerror = (error) => {
        console.error('❌ Failed to load icon:', filename, error)
        resolve(null)
      }

      // Load from public icons directory
      img.src = `/icons/${filename}`
    })
  }

  /**
   * Get icon for a device based on platform or device type
   */
  async getDeviceIcon(platformId?: string, deviceType?: string): Promise<HTMLImageElement | null> {
    const template = this.findTemplate(platformId, deviceType)

    if (!template) {
      // Only log if we have valid inputs (not undefined)
      if (platformId || deviceType) {
        console.log('ℹ️ No template found for platform:', platformId, 'deviceType:', deviceType, '- using default icon')
      }
      // Return default icon as fallback
      return await this.loadIcon('default-icon.svg')
    }

    console.log('✅ Template matched:', template.name, 'for platform:', platformId, 'deviceType:', deviceType)
    return await this.loadIcon(template.filename)
  }

  /**
   * Get icon URL for a device (for HTML rendering)
   */
  getDeviceIconUrl(platformId?: string, deviceType?: string): string | null {
    const template = this.findTemplate(platformId, deviceType)
    return template ? `/icons/${template.filename}` : null
  }

  /**
   * Clear the icon cache
   */
  clearCache(): void {
    this.iconCache.clear()
    console.log('🗑️ Template icon cache cleared')
  }

  /**
   * Get all templates
   */
  getTemplates(): DeviceTemplate[] {
    return this.templates.value
  }

  /**
   * Check if templates are loaded
   */
  isLoaded(): boolean {
    return this.templates.value.length > 0
  }
}

// Export singleton instance
export const templateService = new TemplateService()
