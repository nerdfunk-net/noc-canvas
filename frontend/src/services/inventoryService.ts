/**
 * Inventory Service - API client for device inventory management
 */

import { makeAuthenticatedRequest } from './api'

// Type definitions
export interface LogicalCondition {
  field: string
  operator: string
  value: string
}

export interface LogicalOperation {
  operation_type: string
  conditions: LogicalCondition[]
  nested_operations: LogicalOperation[]
}

export interface DeviceInfo {
  id: string
  name: string
  location?: string
  role?: string
  tags: string[]
  device_type?: string
  manufacturer?: string
  platform?: string
  primary_ip4?: string
  status?: string
}

export interface InventoryPreviewRequest {
  operations: LogicalOperation[]
}

export interface InventoryPreviewResponse {
  devices: DeviceInfo[]
  total_count: number
  operations_executed: number
}

export interface InventoryCreate {
  name: string
  description?: string
  operations: LogicalOperation[]
}

export interface InventoryUpdate {
  name?: string
  description?: string
  operations?: LogicalOperation[]
}

export interface InventoryResponse {
  id: number
  name: string
  description?: string
  operations: LogicalOperation[]
  owner_id: number
  created_at: string
  updated_at: string
}

export interface InventoryListItem {
  id: number
  name: string
  description?: string
  owner_id: number
  created_at: string
  updated_at: string
  device_count?: number
}

export interface FieldOption {
  value: string
  label: string
}

export interface CustomField {
  name: string
  label: string
  type: string
}

/**
 * Inventory Service API client
 */
class InventoryService {
  private readonly baseEndpoint = '/api/inventory'

  /**
   * Preview devices based on logical operations
   */
  async preview(operations: LogicalOperation[]): Promise<InventoryPreviewResponse> {
    const response = await makeAuthenticatedRequest(`${this.baseEndpoint}/preview`, {
      method: 'POST',
      body: JSON.stringify({ operations }),
    })

    if (!response.ok) {
      throw new Error(`Failed to preview inventory: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * Get all inventories for the current user
   */
  async getAll(): Promise<InventoryListItem[]> {
    const response = await makeAuthenticatedRequest(`${this.baseEndpoint}/inventories`)

    if (!response.ok) {
      throw new Error(`Failed to fetch inventories: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * Get a specific inventory by ID
   */
  async get(id: number): Promise<InventoryResponse> {
    const response = await makeAuthenticatedRequest(`${this.baseEndpoint}/inventories/${id}`)

    if (!response.ok) {
      throw new Error(`Failed to fetch inventory: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * Create a new inventory
   */
  async create(data: InventoryCreate): Promise<InventoryResponse> {
    const response = await makeAuthenticatedRequest(`${this.baseEndpoint}/inventories`, {
      method: 'POST',
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      throw new Error(`Failed to create inventory: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * Update an existing inventory
   */
  async update(id: number, data: InventoryUpdate): Promise<InventoryResponse> {
    const response = await makeAuthenticatedRequest(`${this.baseEndpoint}/inventories/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      throw new Error(`Failed to update inventory: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * Delete an inventory
   */
  async delete(id: number): Promise<void> {
    const response = await makeAuthenticatedRequest(`${this.baseEndpoint}/inventories/${id}`, {
      method: 'DELETE',
    })

    if (!response.ok) {
      throw new Error(`Failed to delete inventory: ${response.statusText}`)
    }
  }

  /**
   * Get field options for building logical operations
   */
  async getFieldOptions(): Promise<{
    fields: FieldOption[]
    operators: FieldOption[]
    logical_operations: FieldOption[]
  }> {
    const response = await makeAuthenticatedRequest(`${this.baseEndpoint}/field-options`)

    if (!response.ok) {
      throw new Error(`Failed to fetch field options: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * Get custom fields available for devices
   */
  async getCustomFields(): Promise<{ custom_fields: CustomField[] }> {
    const response = await makeAuthenticatedRequest(`${this.baseEndpoint}/custom-fields`)

    if (!response.ok) {
      throw new Error(`Failed to fetch custom fields: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * Get available values for a specific field
   */
  async getFieldValues(fieldName: string): Promise<{
    field: string
    values: FieldOption[]
    input_type: string
  }> {
    const response = await makeAuthenticatedRequest(`${this.baseEndpoint}/field-values/${fieldName}`)

    if (!response.ok) {
      throw new Error(`Failed to fetch field values: ${response.statusText}`)
    }

    return response.json()
  }
}

// Export a singleton instance
export const inventoryService = new InventoryService()
export default inventoryService
