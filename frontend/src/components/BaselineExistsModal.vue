<template>
  <div v-if="show" class="modal-overlay" @click.self="close">
    <div class="modal-container">
      <div class="modal-header">
        <h2>Baseline Already Exists</h2>
        <button class="close-btn" @click="close">&times;</button>
      </div>

      <div class="modal-body">
        <div class="info-section">
          <p class="message">
            A baseline already exists for <strong>{{ deviceName }}</strong>
          </p>
        </div>

        <div class="baseline-details">
          <h3>Existing Baseline Information</h3>
          <div class="detail-grid">
            <div class="detail-row">
              <span class="detail-label">Device:</span>
              <span class="detail-value">{{ baselineData.device_name }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Created:</span>
              <span class="detail-value">{{ formatDate(baselineData.created_at) }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Last Updated:</span>
              <span class="detail-value">{{ formatDate(baselineData.updated_at) }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Version:</span>
              <span class="detail-value">{{ baselineData.version }}</span>
            </div>
            <div class="detail-row" v-if="baselineData.notes">
              <span class="detail-label">Notes:</span>
              <span class="detail-value">{{ baselineData.notes }}</span>
            </div>
          </div>
        </div>

        <div class="action-description">
          <p><strong>This will replace the existing baseline with new data.</strong></p>
          <p class="mt-2">The version number will increment and the timestamp will be updated to reflect the current capture.</p>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-secondary" @click="close">Cancel</button>
        <button class="btn btn-warning" @click="handleOverwrite">
          <span class="btn-icon">🔄</span>
          Overwrite Baseline
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface BaselineData {
  device_name: string
  created_at: string
  updated_at: string
  version: number
  notes?: string
}

interface Props {
  show: boolean
  deviceName: string
  baselineData: BaselineData
}

const props = withDefaults(defineProps<Props>(), {
  show: false,
  deviceName: '',
  baselineData: () => ({
    device_name: '',
    created_at: '',
    updated_at: '',
    version: 1,
    notes: ''
  })
})

const emit = defineEmits<{
  close: []
  overwrite: []
}>()

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

const handleOverwrite = () => {
  emit('overwrite')
  close()
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
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
  max-width: 600px;
  width: 90%;
  max-height: 85vh;
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
  max-height: 60vh;
  overflow-y: auto;
  background: #ffffff;
}

.info-section {
  margin-bottom: 24px;
}

.message {
  font-size: 16px;
  color: #374151;
  margin: 0;
  line-height: 1.6;
}

.message strong {
  color: #3b82f6;
  font-weight: 600;
}

.baseline-details {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 24px;
}

.baseline-details h3 {
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
  min-width: 120px;
}

.detail-value {
  font-size: 14px;
  color: #111827;
  font-weight: 400;
  text-align: right;
  flex: 1;
  word-break: break-word;
}

.action-description {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  padding: 16px 20px;
}

.action-description p {
  margin: 0;
  font-size: 14px;
  color: #374151;
  line-height: 1.6;
}

.action-description .mt-2 {
  margin-top: 8px;
}

.action-description strong {
  color: #111827;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  background: #f9fafb;
}

.btn {
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.btn-icon {
  font-size: 16px;
}

.btn-secondary {
  background: #ffffff;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover {
  background: #f9fafb;
  border-color: #9ca3af;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.btn-warning {
  background: #f59e0b;
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
}

.btn-warning:hover {
  background: #d97706;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
}

.btn:active {
  transform: translateY(0);
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
