<template>
  <div v-if="show" class="modal-overlay" @click.self="close">
    <div class="modal-container">
      <div class="modal-header">
        <h2>Snapshot Details</h2>
        <button class="close-btn" @click="close">&times;</button>
      </div>

      <div class="modal-body">
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>Loading snapshot details...</p>
        </div>

        <div v-else-if="error" class="error-state">
          <p class="error-message">{{ error }}</p>
        </div>

        <div v-else-if="snapshot">
          <div class="snapshot-info">
            <h3>Snapshot Information</h3>
            <div class="detail-grid">
              <div class="detail-row">
                <span class="detail-label">Device:</span>
                <span class="detail-value">{{ snapshot.device_name }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Command:</span>
                <span class="detail-value">{{ snapshot.command }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Type:</span>
                <span class="detail-value">{{ snapshot.type }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Version:</span>
                <span class="detail-value">{{ snapshot.version }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Created:</span>
                <span class="detail-value">{{ formatDate(snapshot.created_at) }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Updated:</span>
                <span class="detail-value">{{ formatDate(snapshot.updated_at) }}</span>
              </div>
              <div class="detail-row" v-if="snapshot.notes">
                <span class="detail-label">Notes:</span>
                <span class="detail-value">{{ snapshot.notes }}</span>
              </div>
            </div>
          </div>

          <div class="output-section">
            <div class="output-tabs">
              <button
                :class="['tab-btn', { active: activeTab === 'raw' }]"
                @click="activeTab = 'raw'"
              >
                Raw Output
              </button>
              <button
                :class="['tab-btn', { active: activeTab === 'normalized' }]"
                @click="activeTab = 'normalized'"
              >
                Normalized Output
              </button>
            </div>

            <div class="output-content">
              <pre v-if="activeTab === 'raw'" class="output-pre">{{ snapshot.raw_output }}</pre>
              <pre v-else class="output-pre">{{ snapshot.normalized_output }}</pre>
            </div>
          </div>
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

interface Snapshot {
  id: number
  device_id: string
  device_name: string
  command: string
  type: string
  version: number
  created_at: string
  updated_at: string
  notes?: string
  raw_output: string
  normalized_output: string
}

interface Props {
  show: boolean
  snapshotId: number | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

const loading = ref(false)
const error = ref('')
const snapshot = ref<Snapshot | null>(null)
const activeTab = ref<'raw' | 'normalized'>('raw')

watch(() => props.show, async (newShow) => {
  if (newShow && props.snapshotId) {
    await loadSnapshotDetails()
  }
})

const loadSnapshotDetails = async () => {
  if (!props.snapshotId) return

  loading.value = true
  error.value = ''
  snapshot.value = null

  try {
    const token = secureStorage.getToken()
    if (!token) {
      throw new Error('Not authenticated')
    }
    const response = await fetch(`/api/snapshots/${props.snapshotId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (!response.ok) {
      throw new Error(`Failed to load snapshot: ${response.status} ${response.statusText}`)
    }

    snapshot.value = await response.json()
  } catch (err: any) {
    error.value = err.message || 'Failed to load snapshot details'
    console.error('Error loading snapshot:', err)
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString: string) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
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
  max-width: 900px;
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
.error-state {
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

.snapshot-info {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 24px;
}

.snapshot-info h3 {
  margin: 0 0 16px 0;
  font-size: 15px;
  font-weight: 600;
  color: #111827;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 8px 0;
  border-bottom: 1px solid #e5e7eb;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
  min-width: 100px;
}

.detail-value {
  font-size: 14px;
  color: #111827;
  font-weight: 400;
  text-align: right;
  flex: 1;
  word-break: break-word;
}

.output-section {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.output-tabs {
  display: flex;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
  gap: 4px;
  padding: 4px;
}

.tab-btn {
  flex: 1;
  padding: 8px 16px;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: #6b7280;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: #111827;
}

.tab-btn.active {
  background: #ffffff;
  color: #3b82f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.output-content {
  padding: 20px;
  max-height: 400px;
  overflow: auto;
  background: #f9fafb;
}

.output-pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.6;
  color: #111827;
  white-space: pre-wrap;
  word-wrap: break-word;
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
.modal-body::-webkit-scrollbar,
.output-content::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.modal-body::-webkit-scrollbar-track,
.output-content::-webkit-scrollbar-track {
  background: #f3f4f6;
  border-radius: 4px;
}

.modal-body::-webkit-scrollbar-thumb,
.output-content::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 4px;
}

.modal-body::-webkit-scrollbar-thumb:hover,
.output-content::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
</style>
