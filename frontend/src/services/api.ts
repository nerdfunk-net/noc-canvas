import type { User } from '@/stores/auth'
import type { Device, Connection } from '@/stores/devices'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

class ApiClient {
  private baseURL: string

  constructor(baseURL: string) {
    this.baseURL = baseURL
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    const token = localStorage.getItem('token')

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

export const devicesApi = {
  async getDevices() {
    return apiClient.get<Device[]>('/api/devices/')
  },

  async createDevice(device: Omit<Device, 'id'>) {
    return apiClient.post<Device>('/api/devices/', device)
  },

  async updateDevice(deviceId: number, updates: Partial<Device>) {
    return apiClient.put<Device>(`/api/devices/${deviceId}`, updates)
  },

  async deleteDevice(deviceId: number) {
    return apiClient.delete(`/api/devices/${deviceId}`)
  },

  async getConnections() {
    return apiClient.get<Connection[]>('/api/devices/connections')
  },

  async createConnection(connection: Omit<Connection, 'id'>) {
    return apiClient.post<Connection>('/api/devices/connections', connection)
  },
}