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
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  max-width: 900px;
  width: 90%;
  max-height: 90vh;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
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
  padding: 24px 28px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(90deg, rgba(59, 130, 246, 0.1) 0%, rgba(147, 51, 234, 0.1) 100%);
}

.modal-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #f1f5f9;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.close-btn {
  background: none;
  border: none;
  font-size: 32px;
  color: #94a3b8;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #f1f5f9;
  transform: rotate(90deg);
}

.modal-body {
  padding: 28px;
  max-height: 70vh;
  overflow-y: auto;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #cbd5e1;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(59, 130, 246, 0.2);
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
  color: #f87171;
  font-size: 14px;
}

.snapshot-info {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.snapshot-info h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #e2e8f0;
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
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  font-size: 14px;
  color: #94a3b8;
  font-weight: 500;
  min-width: 100px;
}

.detail-value {
  font-size: 14px;
  color: #e2e8f0;
  font-weight: 400;
  text-align: right;
  flex: 1;
  word-break: break-word;
}

.output-section {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  overflow: hidden;
}

.output-tabs {
  display: flex;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(15, 23, 42, 0.4);
}

.tab-btn {
  flex: 1;
  padding: 12px 20px;
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.tab-btn:hover {
  background: rgba(59, 130, 246, 0.1);
  color: #cbd5e1;
}

.tab-btn.active {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  border-bottom: 2px solid #3b82f6;
}

.output-content {
  padding: 20px;
  max-height: 400px;
  overflow: auto;
}

.output-pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.5;
  color: #e2e8f0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.modal-footer {
  padding: 20px 28px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: flex-end;
  background: rgba(15, 23, 42, 0.4);
}

.btn {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.btn-secondary {
  background: rgba(71, 85, 105, 0.5);
  color: #cbd5e1;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.btn-secondary:hover {
  background: rgba(71, 85, 105, 0.7);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

/* Scrollbar styling */
.modal-body::-webkit-scrollbar,
.output-content::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.modal-body::-webkit-scrollbar-track,
.output-content::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.4);
  border-radius: 4px;
}

.modal-body::-webkit-scrollbar-thumb,
.output-content::-webkit-scrollbar-thumb {
  background: rgba(71, 85, 105, 0.6);
  border-radius: 4px;
}

.modal-body::-webkit-scrollbar-thumb:hover,
.output-content::-webkit-scrollbar-thumb:hover {
  background: rgba(71, 85, 105, 0.8);
}
</style>
