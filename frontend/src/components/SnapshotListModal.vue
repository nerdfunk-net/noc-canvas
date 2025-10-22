<template>
  <div v-if="show" class="modal-overlay" @click.self="close">
    <div class="modal-container">
      <div class="modal-header">
        <h2>Device Snapshots</h2>
        <button class="close-btn" @click="close">&times;</button>
      </div>

      <div class="modal-body">
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>Loading snapshots...</p>
        </div>

        <div v-else-if="error" class="error-state">
          <p class="error-message">{{ error }}</p>
        </div>

        <div v-else-if="snapshotGroups.length === 0" class="empty-state">
          <p>No snapshots found for this device.</p>
        </div>

        <div v-else class="snapshots-table">
          <table>
            <thead>
              <tr>
                <th class="expand-col"></th>
                <th>Created</th>
                <th>Commands</th>
                <th>Notes</th>
                <th class="actions-col">Actions</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="group in snapshotGroups" :key="group.snapshot_group_id">
                <!-- Group row -->
                <tr class="group-row" @click="toggleGroup(group.snapshot_group_id)">
                  <td class="expand-cell">
                    <span class="expand-icon">{{ expandedGroups.has(group.snapshot_group_id) ? '▼' : '▶' }}</span>
                  </td>
                  <td class="date-cell">{{ formatDate(group.created_at) }}</td>
                  <td class="command-count-cell">
                    <span class="badge">{{ group.command_count }} commands</span>
                    <span class="command-list">{{ group.commands.join(', ') }}</span>
                  </td>
                  <td class="notes-cell">{{ group.notes || '-' }}</td>
                  <td class="actions-cell" @click.stop>
                    <button class="action-btn delete-btn" @click="handleDeleteGroup(group.snapshot_group_id)" title="Delete Entire Snapshot">
                      🗑️ Delete
                    </button>
                  </td>
                </tr>

                <!-- Expanded command rows -->
                <template v-if="expandedGroups.has(group.snapshot_group_id)">
                  <tr v-for="command in group.commands" :key="`${group.snapshot_group_id}-${command}`" class="command-row">
                    <td class="expand-cell"></td>
                    <td class="date-cell sub-cell">{{ formatDate(group.created_at) }}</td>
                    <td class="command-cell sub-cell">
                      <span class="command-icon">📄</span>
                      {{ command }}
                    </td>
                    <td class="notes-cell sub-cell">-</td>
                    <td class="actions-cell sub-cell">
                      <button class="action-btn view-btn" @click="handleShowCommand(group.snapshot_group_id, command)" title="View Details">
                        👁️ View
                      </button>
                    </td>
                  </tr>
                </template>
              </template>
            </tbody>
          </table>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-secondary" @click="close">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import secureStorage from '@/services/secureStorage'

interface SnapshotGroup {
  snapshot_group_id: string
  device_id: string
  device_name: string
  type: string
  created_at: string
  updated_at: string
  notes?: string
  command_count: number
  commands: string[]
}

interface Props {
  show: boolean
  deviceId: string | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
  show: [snapshotId: number]
}>()

const loading = ref(false)
const error = ref('')
const snapshotGroups = ref<SnapshotGroup[]>([])
const expandedGroups = ref<Set<string>>(new Set())
const individualSnapshots = ref<any[]>([])

watch(() => props.show, async (newShow) => {
  if (newShow && props.deviceId) {
    await loadSnapshots()
  }
})

const loadSnapshots = async () => {
  if (!props.deviceId) return

  loading.value = true
  error.value = ''
  snapshotGroups.value = []
  expandedGroups.value.clear()

  try {
    const token = secureStorage.getToken()
    if (!token) {
      throw new Error('Not authenticated')
    }

    // Load grouped snapshots
    const groupedResponse = await fetch(`/api/snapshots/list?device_id=${props.deviceId}&type=snapshot&grouped=true`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (!groupedResponse.ok) {
      throw new Error(`Failed to load snapshots: ${groupedResponse.status} ${groupedResponse.statusText}`)
    }

    snapshotGroups.value = await groupedResponse.json()

    // Load individual snapshots for detail viewing
    const individualResponse = await fetch(`/api/snapshots/list?device_id=${props.deviceId}&type=snapshot&grouped=false`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (individualResponse.ok) {
      individualSnapshots.value = await individualResponse.json()
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to load snapshots'
    console.error('Error loading snapshots:', err)
  } finally {
    loading.value = false
  }
}

const toggleGroup = (groupId: string) => {
  if (expandedGroups.value.has(groupId)) {
    expandedGroups.value.delete(groupId)
  } else {
    expandedGroups.value.add(groupId)
  }
  // Force reactivity
  expandedGroups.value = new Set(expandedGroups.value)
}

const handleShowCommand = (groupId: string, command: string) => {
  // Find the snapshot ID for this specific command
  const snapshot = individualSnapshots.value.find(
    s => s.snapshot_group_id === groupId && s.command === command
  )
  if (snapshot) {
    emit('show', snapshot.id)
  }
}

const handleDeleteGroup = async (groupId: string) => {
  if (!confirm('Are you sure you want to delete this entire snapshot (all commands)?')) {
    return
  }

  try {
    const token = secureStorage.getToken()
    if (!token) {
      throw new Error('Not authenticated')
    }
    const response = await fetch(`/api/snapshots/group/${groupId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (!response.ok) {
      throw new Error(`Failed to delete snapshot group: ${response.status} ${response.statusText}`)
    }

    // Reload snapshots after deletion
    await loadSnapshots()
  } catch (err: any) {
    error.value = err.message || 'Failed to delete snapshot group'
    console.error('Error deleting snapshot group:', err)
  }
}

const formatDate = (dateString: string) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const close = () => {
  emit('close')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-container {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  max-width: 1200px;
  width: 90%;
  max-height: 90vh;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f9fafb;
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #111827;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  color: #6b7280;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #e5e7eb;
  color: #111827;
}

.modal-body {
  padding: 24px;
  max-height: 70vh;
  overflow-y: auto;
  background: #ffffff;
}

.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #6b7280;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-message {
  color: #ef4444;
  font-size: 14px;
}

.snapshots-table {
  width: 100%;
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

thead {
  background: #f9fafb;
  position: sticky;
  top: 0;
  z-index: 10;
}

th {
  padding: 12px 16px;
  text-align: left;
  font-size: 12px;
  font-weight: 600;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid #e5e7eb;
}

.expand-col {
  width: 40px;
}

.actions-col {
  width: 150px;
  text-align: center;
}

.group-row {
  background: #eff6ff;
  cursor: pointer;
  transition: all 0.2s;
}

.group-row:hover {
  background: #dbeafe;
}

.command-row {
  background: #f9fafb;
  border-left: 3px solid #3b82f6;
}

.command-row:hover {
  background: #f3f4f6;
}

td {
  padding: 12px 16px;
  font-size: 13px;
  color: #111827;
  border-bottom: 1px solid #f3f4f6;
}

.sub-cell {
  padding-left: 24px;
  font-size: 12px;
}

.expand-cell {
  text-align: center;
  width: 40px;
}

.expand-icon {
  color: #3b82f6;
  font-size: 14px;
  display: inline-block;
  transition: transform 0.2s;
}

.date-cell {
  font-size: 12px;
  color: #6b7280;
  white-space: nowrap;
}

.command-count-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.badge {
  display: inline-block;
  background: #dbeafe;
  color: #3b82f6;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  width: fit-content;
}

.command-list {
  font-size: 11px;
  color: #6b7280;
  line-height: 1.4;
}

.command-cell {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  color: #3b82f6;
  font-weight: 500;
}

.command-icon {
  margin-right: 6px;
  opacity: 0.6;
}

.notes-cell {
  font-size: 12px;
  color: #6b7280;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.actions-cell {
  display: flex;
  gap: 8px;
  justify-content: center;
  align-items: center;
}

.action-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.view-btn {
  background: #3b82f6;
  color: #ffffff;
}

.view-btn:hover {
  background: #2563eb;
}

.delete-btn {
  background: #ffffff;
  color: #ef4444;
  border: 1px solid #fecaca;
}

.delete-btn:hover {
  background: #fef2f2;
  border-color: #ef4444;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  background: #f9fafb;
}

.btn {
  padding: 10px 24px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn-secondary {
  background: #3b82f6;
  color: #ffffff;
  border: 1px solid #3b82f6;
}

.btn-secondary:hover {
  background: #2563eb;
  border-color: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

/* Scrollbar styling */
.modal-body::-webkit-scrollbar {
  width: 8px;
}

.modal-body::-webkit-scrollbar-track {
  background: #f3f4f6;
  border-radius: 4px;
}

.modal-body::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 4px;
}

.modal-body::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
</style>
