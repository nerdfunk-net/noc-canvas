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
  routing_style?: 'straight' | 'orthogonal'
  waypoints?: { x: number; y: number }[]
  layer?: 'layer2' | 'layer3'
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

// Track if we're currently refreshing the token to avoid multiple simultaneous refreshes
let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []

// Subscribe to token refresh
const subscribeTokenRefresh = (callback: (token: string) => void) => {
  refreshSubscribers.push(callback)
}

// Notify all subscribers when token is refreshed
const onTokenRefreshed = (token: string) => {
  refreshSubscribers.forEach(callback => callback(token))
  refreshSubscribers = []
}

// Callback for when 401 occurs - to be set by the app
let on401Callback: (() => void) | null = null

export const set401Handler = (callback: () => void) => {
  on401Callback = callback
}

// Helper function to make authenticated requests with proper URL handling
export const makeAuthenticatedRequest = async (
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> => {
  const url = `${API_BASE_URL}${endpoint}`
  // Try secure storage first, fallback to localStorage
  const token = secureStorage.getToken() || localStorage.getItem('token')

  const config: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
  }

  const response = await fetch(url, config)

  // Handle 401 Unauthorized
  if (response.status === 401) {
    // Don't try to refresh if we're logging in or refreshing
    if (endpoint === '/api/auth/login' || endpoint === '/api/auth/refresh') {
      return response
    }

    // If already refreshing, wait for the new token
    if (isRefreshing) {
      return new Promise((resolve) => {
        subscribeTokenRefresh((newToken: string) => {
          // Retry the request with new token
          const newConfig = {
            ...config,
            headers: {
              ...config.headers,
              Authorization: `Bearer ${newToken}`,
            },
          }
          resolve(fetch(url, newConfig))
        })
      })
    }

    // Try to refresh the token
    isRefreshing = true
    try {
      const refreshResponse = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      })

      if (refreshResponse.ok) {
        const { access_token } = await refreshResponse.json()
        secureStorage.setToken(access_token)
        isRefreshing = false
        onTokenRefreshed(access_token)

        // Retry the original request with new token
        const newConfig = {
          ...config,
          headers: {
            ...config.headers,
            Authorization: `Bearer ${access_token}`,
          },
        }
        return fetch(url, newConfig)
      } else {
        // Refresh failed, trigger logout
        isRefreshing = false
        if (on401Callback) {
          on401Callback()
        }
        return response
      }
    } catch (error) {
      isRefreshing = false
      if (on401Callback) {
        on401Callback()
      }
      return response
    }
  }

  return response
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

  async refreshToken() {
    return apiClient.post<{ access_token: string; token_type: string }>('/api/auth/refresh')
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
    id: string
    name: string
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
    disable_cache?: boolean
  }) {
    const searchParams = new URLSearchParams()
    if (params?.limit) searchParams.append('limit', params.limit.toString())
    if (params?.offset) searchParams.append('offset', params.offset.toString())
    if (params?.filter_type) searchParams.append('filter_type', params.filter_type)
    if (params?.filter_value) searchParams.append('filter_value', params.filter_value)
    if (params?.disable_cache) searchParams.append('disable_cache', 'true')

    const endpoint = `/api/nautobot/devices${searchParams.toString() ? '?' + searchParams.toString() : ''}`
    return apiClient.get<NautobotDeviceResponse>(endpoint)
  },

  async getAllDevices(disableCache: boolean = false) {
    // Load all devices without pagination
    return this.getDevices({ limit: 10000, disable_cache: disableCache })
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

// Topology interfaces and API
export type LinkType = 'cdp_neighbor' | 'lldp_neighbor' | 'static_route' | 'ospf_route' | 'bgp_route' | 'arp_discovered' | 'mac_table'

export interface TopologyNode {
  device_id: string
  device_name: string
  primary_ip?: string
  platform?: string
  device_type?: string
  position_x?: number
  position_y?: number
  metadata?: Record<string, any>
}

export interface TopologyLink {
  source_device_id: string
  target_device_id: string
  source_device_name: string
  target_device_name: string
  source_interface?: string
  target_interface?: string
  link_type: LinkType
  bidirectional: boolean
  link_metadata?: Record<string, any>
}

export interface TopologyGraph {
  nodes: TopologyNode[]
  links: TopologyLink[]
  metadata?: Record<string, any>
}

export interface TopologyStatistics {
  total_devices: number
  total_links: number
  link_types_breakdown: Record<string, number>
  devices_by_platform: Record<string, number>
  isolated_devices: number
  average_connections_per_device: number
}

export interface TopologyBuildRequest {
  device_ids?: string[]
  include_cdp?: boolean
  include_routing?: boolean
  route_types?: string[]
  include_layer2?: boolean
  auto_layout?: boolean
  layout_algorithm?: 'force_directed' | 'hierarchical' | 'circular'
}

export interface NeighborResolution {
  neighbor_name: string
  neighbor_ip?: string
  device_id?: string
  device_name?: string
  matched_by?: string
  confidence: string
}

export const topologyApi = {
  async buildTopology(params?: {
    device_ids?: string[]
    include_cdp?: boolean
    include_routing?: boolean
    route_types?: string[]
    include_layer2?: boolean
    auto_layout?: boolean
    layout_algorithm?: string
  }): Promise<TopologyGraph> {
    const queryParams = new URLSearchParams()

    if (params?.device_ids) {
      params.device_ids.forEach(id => queryParams.append('device_ids', id))
    }
    if (params?.include_cdp !== undefined) {
      queryParams.append('include_cdp', String(params.include_cdp))
    }
    if (params?.include_routing !== undefined) {
      queryParams.append('include_routing', String(params.include_routing))
    }
    if (params?.route_types) {
      params.route_types.forEach(type => queryParams.append('route_types', type))
    }
    if (params?.include_layer2 !== undefined) {
      queryParams.append('include_layer2', String(params.include_layer2))
    }
    if (params?.auto_layout !== undefined) {
      queryParams.append('auto_layout', String(params.auto_layout))
    }
    if (params?.layout_algorithm) {
      queryParams.append('layout_algorithm', params.layout_algorithm)
    }

    const endpoint = `/api/topology/build${queryParams.toString() ? '?' + queryParams.toString() : ''}`
    return apiClient.get<TopologyGraph>(endpoint)
  },

  async buildTopologyPost(request: TopologyBuildRequest): Promise<TopologyGraph> {
    return apiClient.post<TopologyGraph>('/api/topology/build', request)
  },

  async getCdpTopology(params?: {
    device_ids?: string[]
    auto_layout?: boolean
    layout_algorithm?: string
  }): Promise<TopologyGraph> {
    const queryParams = new URLSearchParams()

    if (params?.device_ids) {
      params.device_ids.forEach(id => queryParams.append('device_ids', id))
    }
    if (params?.auto_layout !== undefined) {
      queryParams.append('auto_layout', String(params.auto_layout))
    }
    if (params?.layout_algorithm) {
      queryParams.append('layout_algorithm', params.layout_algorithm)
    }

    const endpoint = `/api/topology/cdp${queryParams.toString() ? '?' + queryParams.toString() : ''}`
    return apiClient.get<TopologyGraph>(endpoint)
  },

  async getRoutingTopology(params?: {
    device_ids?: string[]
    route_types?: string[]
    auto_layout?: boolean
    layout_algorithm?: string
  }): Promise<TopologyGraph> {
    const queryParams = new URLSearchParams()

    if (params?.device_ids) {
      params.device_ids.forEach(id => queryParams.append('device_ids', id))
    }
    if (params?.route_types) {
      params.route_types.forEach(type => queryParams.append('route_types', type))
    }
    if (params?.auto_layout !== undefined) {
      queryParams.append('auto_layout', String(params.auto_layout))
    }
    if (params?.layout_algorithm) {
      queryParams.append('layout_algorithm', params.layout_algorithm)
    }

    const endpoint = `/api/topology/routing${queryParams.toString() ? '?' + queryParams.toString() : ''}`
    return apiClient.get<TopologyGraph>(endpoint)
  },

  async getLayer2Topology(params?: {
    device_ids?: string[]
    auto_layout?: boolean
    layout_algorithm?: string
  }): Promise<TopologyGraph> {
    const queryParams = new URLSearchParams()

    if (params?.device_ids) {
      params.device_ids.forEach(id => queryParams.append('device_ids', id))
    }
    if (params?.auto_layout !== undefined) {
      queryParams.append('auto_layout', String(params.auto_layout))
    }
    if (params?.layout_algorithm) {
      queryParams.append('layout_algorithm', params.layout_algorithm)
    }

    const endpoint = `/api/topology/layer2${queryParams.toString() ? '?' + queryParams.toString() : ''}`
    return apiClient.get<TopologyGraph>(endpoint)
  },

  async resolveNeighbor(neighbor_name: string, neighbor_ip?: string): Promise<NeighborResolution> {
    return apiClient.post<NeighborResolution>('/api/topology/resolve-neighbor', {
      neighbor_name,
      neighbor_ip
    })
  },

  async getStatistics(params?: {
    device_ids?: string[]
    include_cdp?: boolean
    include_routing?: boolean
    route_types?: string[]
    include_layer2?: boolean
  }): Promise<TopologyStatistics> {
    const queryParams = new URLSearchParams()

    if (params?.device_ids) {
      params.device_ids.forEach(id => queryParams.append('device_ids', id))
    }
    if (params?.include_cdp !== undefined) {
      queryParams.append('include_cdp', String(params.include_cdp))
    }
    if (params?.include_routing !== undefined) {
      queryParams.append('include_routing', String(params.include_routing))
    }
    if (params?.route_types) {
      params.route_types.forEach(type => queryParams.append('route_types', type))
    }
    if (params?.include_layer2 !== undefined) {
      queryParams.append('include_layer2', String(params.include_layer2))
    }

    const endpoint = `/api/topology/statistics${queryParams.toString() ? '?' + queryParams.toString() : ''}`
    return apiClient.get<TopologyStatistics>(endpoint)
  }
}

// Device communication API
export const devicesApi = {
  async getInterfaces(deviceId: string, useTextfsm: boolean = true, disableCache: boolean = false): Promise<{
    success: boolean
    output?: any
    error?: string
    parsed?: boolean
    parser_used?: string
    cached?: boolean
  }> {
    const queryParams = new URLSearchParams()
    if (useTextfsm) {
      queryParams.append('use_textfsm', 'true')
    }
    if (disableCache) {
      queryParams.append('disable_cache', 'true')
    }
    const endpoint = `/api/devices/${deviceId}/interfaces${queryParams.toString() ? '?' + queryParams.toString() : ''}`
    return apiClient.get(endpoint)
  }
}

