import type { User } from '@/stores/auth'
import secureStorage from './secureStorage'

// Canvas interfaces
export interface CanvasDeviceData {
  id: number
  name: string
  device_type: string
  ip_address?: string
  position_x: number
  position_y: number
  properties?: string
}

export interface CanvasConnectionData {
  id: number
  source_device_id: number
  target_device_id: number
  connection_type: string
  properties?: string
}

export interface CanvasData {
  devices: CanvasDeviceData[]
  connections: CanvasConnectionData[]
}

export interface CanvasCreateRequest {
  name: string
  sharable: boolean
  canvas_data: CanvasData
}

export interface CanvasResponse {
  id: number
  name: string
  owner_id: number
  sharable: boolean
  canvas_data: CanvasData
  created_at: string
  updated_at: string
}

export interface CanvasListItem {
  id: number
  name: string
  owner_id: number
  owner_username: string
  sharable: boolean
  is_own: boolean
  created_at: string
  updated_at: string
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Helper function to make authenticated requests with proper URL handling
export const makeAuthenticatedRequest = async (
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> => {
  const url = `${API_BASE_URL}${endpoint}`
  // Try secure storage first, fallback to localStorage
  const token = secureStorage.getToken() || localStorage.getItem('token')

  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
    ...options,
  }

  return fetch(url, config)
}

class ApiClient {
  private baseURL: string

  constructor(baseURL: string) {
    this.baseURL = baseURL
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    // Try secure storage first, fallback to localStorage
    const token = secureStorage.getToken() || localStorage.getItem('token')

    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    }

    const response = await fetch(url, config)

    if (!response.ok) {
      const error = await response.text()
      throw new Error(error)
    }

    return response.json()
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' })
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }
}

const apiClient = new ApiClient(API_BASE_URL)

export const authApi = {
  async login(username: string, password: string) {
    return apiClient.post<{ access_token: string; token_type: string }>('/api/auth/login', {
      username,
      password,
    })
  },

  async register(username: string, password: string) {
    return apiClient.post<User>('/api/auth/register', {
      username,
      password,
    })
  },

  async getMe() {
    return apiClient.get<User>('/api/auth/me')
  },
}

export interface NautobotDevice {
  id: string
  name: string
  primary_ip4?: {
    address: string
  }
  location?: {
    name: string
  }
  role?: {
    name: string
  }
  status?: {
    name: string
  }
  device_type?: {
    model: string
  }
  platform?: {
    network_driver: string
  }
  cf_last_backup?: string
}

interface NautobotDeviceResponse {
  devices: NautobotDevice[]
  count: number
  has_more: boolean
  is_paginated: boolean
  current_offset: number
  current_limit: number | null
  next: string | null
  previous: string | null
}

export const nautobotApi = {
  async getDevices(params?: {
    limit?: number
    offset?: number
    filter_type?: string
    filter_value?: string
  }) {
    const searchParams = new URLSearchParams()
    if (params?.limit) searchParams.append('limit', params.limit.toString())
    if (params?.offset) searchParams.append('offset', params.offset.toString())
    if (params?.filter_type) searchParams.append('filter_type', params.filter_type)
    if (params?.filter_value) searchParams.append('filter_value', params.filter_value)

    const endpoint = `/api/nautobot/devices${searchParams.toString() ? '?' + searchParams.toString() : ''}`
    return apiClient.get<NautobotDeviceResponse>(endpoint)
  },

  async getAllDevices() {
    // Load all devices without pagination
    return this.getDevices({ limit: 10000 })
  },

  async getDeviceById(deviceId: string) {
    return apiClient.get<NautobotDevice>(`/api/nautobot/devices/${deviceId}`)
  },

  async searchDevices(query: string, filterType: string = 'name') {
    return this.getDevices({
      filter_type: filterType,
      filter_value: query,
      limit: 100,
    })
  },
}

// Canvas API
export const canvasApi = {
  async saveCanvas(canvasData: CanvasCreateRequest) {
    return apiClient.post<CanvasResponse>('/api/canvas', canvasData)
  },

  async getCanvases() {
    return apiClient.get<CanvasResponse[]>('/api/canvas')
  },

  async getCanvasList() {
    return apiClient.get<CanvasListItem[]>('/api/canvas/list')
  },

  async getCanvas(canvasId: number) {
    return apiClient.get<CanvasResponse>(`/api/canvas/${canvasId}`)
  },

  async updateCanvas(canvasId: number, canvasData: Partial<CanvasCreateRequest>) {
    return apiClient.put<CanvasResponse>(`/api/canvas/${canvasId}`, canvasData)
  },

  async deleteCanvas(canvasId: number) {
    return apiClient.delete(`/api/canvas/${canvasId}`)
  },
}

// Device Commands interfaces and API
export interface DeviceCommand {
  id: number
  command: string
  display?: string | null
  platform: string
  parser: string
  created_at: string
  updated_at?: string | null
}

export const settingsApi = {
  async getDeviceCommands(): Promise<DeviceCommand[]> {
    const response = await apiClient.get<DeviceCommand[]>('/api/settings/commands')
    return response
  }
}
