<template>
  <div v-if="show" class="modal-overlay" @click.self="close">
    <div class="modal-container">
      <div class="modal-header">
        <h2>Compare Baseline vs Snapshot</h2>
        <button class="close-btn" @click="close">&times;</button>
      </div>

      <div class="modal-body">
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>Loading data...</p>
        </div>

        <div v-else-if="error" class="error-state">
          <p class="error-message">{{ error }}</p>
        </div>

        <div v-else-if="!baseline" class="error-state">
          <p class="error-message">No baseline found for this device. Please create a baseline first.</p>
        </div>

        <div v-else class="compare-container">
          <!-- Snapshot Selector -->
          <div class="selector-section">
            <label class="selector-label">Select Snapshot to Compare:</label>
            <select v-model="selectedSnapshotGroupId" @change="loadSelectedSnapshot" class="snapshot-select">
              <option value="">-- Select a snapshot --</option>
              <option v-for="group in snapshotGroups" :key="group.snapshot_group_id" :value="group.snapshot_group_id">
                {{ formatDate(group.created_at) }} - {{ group.command_count }} commands
              </option>
            </select>
          </div>

          <!-- Comparison Panel -->
          <div v-if="selectedSnapshot" class="comparison-panel">
            <!-- Command List (Left) -->
            <div class="command-list">
              <h3>Commands</h3>
              <div class="command-items">
                <div
                  v-for="cmd in selectedSnapshot.commands"
                  :key="cmd"
                  :class="['command-item', { active: selectedCommand === cmd }]"
                  @click="selectCommand(cmd)"
                >
                  <span class="command-icon">📄</span>
                  <span class="command-name">{{ cmd }}</span>
                  <span
                    v-if="commandDiffStatus[cmd] !== undefined"
                    :class="['diff-indicator', commandDiffStatus[cmd] ? 'has-diff' : 'no-diff']"
                    :title="commandDiffStatus[cmd] ? 'Has differences' : 'No differences'"
                  >
                    ●
                  </span>
                </div>
              </div>
            </div>

            <!-- Diff View (Right) -->
            <div class="diff-view">
              <h3 v-if="selectedCommand">{{ selectedCommand }}</h3>
              <h3 v-else>Select a command to view differences</h3>

              <div v-if="selectedCommand && loadingDiff" class="diff-loading">
                <div class="spinner-small"></div>
                <p>Computing diff...</p>
              </div>

              <div v-else-if="selectedCommand && diffResult" class="diff-content">
                <div v-if="diffResult.identical" class="no-diff-message">
                  <span class="icon">✓</span>
                  <p>No differences found. Baseline and snapshot are identical for this command.</p>
                </div>
                <div v-else class="diff-display">
                  <pre class="diff-text">{{ diffResult.diff }}</pre>
                </div>
              </div>

              <div v-else-if="selectedCommand && !diffResult" class="no-data-message">
                <p>No data available for comparison.</p>
              </div>

              <div v-else class="placeholder-message">
                <span class="icon">👈</span>
                <p>Select a command from the list to see the comparison</p>
              </div>
            </div>
          </div>

          <!-- No Snapshot Selected -->
          <div v-else class="no-selection-message">
            <span class="icon">⬆️</span>
            <p>Please select a snapshot from the dropdown above to begin comparison</p>
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
}>()

const loading = ref(false)
const error = ref('')
const baseline = ref<any>(null)
const snapshotGroups = ref<SnapshotGroup[]>([])
const selectedSnapshotGroupId = ref('')
const selectedSnapshot = ref<any>(null)
const individualSnapshots = ref<any[]>([])
const individualBaselines = ref<any[]>([])
const selectedCommand = ref('')
const diffResult = ref<any>(null)
const loadingDiff = ref(false)
const commandDiffStatus = ref<Record<string, boolean>>({})

watch(() => props.show, async (newShow) => {
  if (newShow && props.deviceId) {
    await loadData()
  }
})

const loadData = async () => {
  loading.value = true
  error.value = ''
  baseline.value = null
  snapshotGroups.value = []
  selectedSnapshotGroupId.value = ''
  selectedSnapshot.value = null
  selectedCommand.value = ''

  try {
    const token = secureStorage.getToken()
    if (!token) {
      throw new Error('Not authenticated')
    }

    // Load baseline
    const baselineResponse = await fetch(`/api/snapshots/list?device_id=${props.deviceId}&type=baseline&grouped=true`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (baselineResponse.ok) {
      const baselines = await baselineResponse.json()
      if (baselines.length > 0) {
        baseline.value = baselines[0]
      }
    }

    // Load individual baselines for comparison
    const individualBaselineResponse = await fetch(`/api/snapshots/list?device_id=${props.deviceId}&type=baseline&grouped=false`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (individualBaselineResponse.ok) {
      individualBaselines.value = await individualBaselineResponse.json()
    }

    // Load snapshots
    const snapshotResponse = await fetch(`/api/snapshots/list?device_id=${props.deviceId}&type=snapshot&grouped=true`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (snapshotResponse.ok) {
      snapshotGroups.value = await snapshotResponse.json()
    }

    // Load individual snapshots
    const individualResponse = await fetch(`/api/snapshots/list?device_id=${props.deviceId}&type=snapshot&grouped=false`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (individualResponse.ok) {
      individualSnapshots.value = await individualResponse.json()
    }

  } catch (err: any) {
    error.value = err.message || 'Failed to load data'
    console.error('Error loading data:', err)
  } finally {
    loading.value = false
  }
}

const loadSelectedSnapshot = async () => {
  const group = snapshotGroups.value.find(g => g.snapshot_group_id === selectedSnapshotGroupId.value)
  selectedSnapshot.value = group
  selectedCommand.value = ''
  diffResult.value = null
  commandDiffStatus.value = {}

  if (!group) return

  // Compute diff status for all commands in the background
  await computeAllDiffStatuses(group.commands)
}

const computeAllDiffStatuses = async (commands: string[]) => {
  const token = secureStorage.getToken()
  if (!token) return

  for (const command of commands) {
    try {
      // Find baseline and snapshot data for this command
      const baselineData = individualBaselines.value.find(b => b.command === command)
      const snapshotData = individualSnapshots.value.find(
        s => s.snapshot_group_id === selectedSnapshotGroupId.value && s.command === command
      )

      if (!baselineData || !snapshotData) {
        commandDiffStatus.value[command] = false
        continue
      }

      // Fetch full details
      const [baselineDetail, snapshotDetail] = await Promise.all([
        fetch(`/api/snapshots/${baselineData.id}`, {
          headers: { 'Authorization': `Bearer ${token}` },
        }).then(r => r.json()),
        fetch(`/api/snapshots/${snapshotData.id}`, {
          headers: { 'Authorization': `Bearer ${token}` },
        }).then(r => r.json())
      ])

      // Compare normalized outputs
      const hasDifference = baselineDetail.normalized_output !== snapshotDetail.normalized_output
      commandDiffStatus.value[command] = hasDifference

    } catch (err) {
      console.error(`Error computing diff status for ${command}:`, err)
      commandDiffStatus.value[command] = false
    }
  }
}

const selectCommand = async (command: string) => {
  selectedCommand.value = command
  await computeDiff(command)
}

const computeDiff = async (command: string) => {
  loadingDiff.value = true
  diffResult.value = null

  try {
    // Find baseline and snapshot data for this command
    const baselineData = individualBaselines.value.find(b => b.command === command)
    const snapshotData = individualSnapshots.value.find(
      s => s.snapshot_group_id === selectedSnapshotGroupId.value && s.command === command
    )

    if (!baselineData || !snapshotData) {
      diffResult.value = { error: 'Data not found for comparison' }
      return
    }

    // Fetch full details
    const token = secureStorage.getToken()
    const [baselineDetail, snapshotDetail] = await Promise.all([
      fetch(`/api/snapshots/${baselineData.id}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      }).then(r => r.json()),
      fetch(`/api/snapshots/${snapshotData.id}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      }).then(r => r.json())
    ])

    // Compare normalized outputs
    const baselineOutput = baselineDetail.normalized_output
    const snapshotOutput = snapshotDetail.normalized_output

    if (baselineOutput === snapshotOutput) {
      diffResult.value = { identical: true }
    } else {
      // Generate a simple diff
      const diff = generateDiff(baselineOutput, snapshotOutput)
      diffResult.value = { identical: false, diff }
    }

  } catch (err: any) {
    console.error('Error computing diff:', err)
    diffResult.value = { error: err.message || 'Failed to compute diff' }
  } finally {
    loadingDiff.value = false
  }
}

const generateDiff = (baseline: string, snapshot: string): string => {
  // Simple line-by-line diff
  const baselineLines = baseline.split('\n')
  const snapshotLines = snapshot.split('\n')
  const maxLines = Math.max(baselineLines.length, snapshotLines.length)
  const diff: string[] = []

  diff.push('=== BASELINE vs SNAPSHOT ===\n')

  for (let i = 0; i < maxLines; i++) {
    const baseLine = baselineLines[i] || ''
    const snapLine = snapshotLines[i] || ''

    if (baseLine !== snapLine) {
      if (baseLine) {
        diff.push(`- ${baseLine}`)
      }
      if (snapLine) {
        diff.push(`+ ${snapLine}`)
      }
    } else {
      diff.push(`  ${baseLine}`)
    }
  }

  return diff.join('\n')
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
  align-items: flex-start;
  justify-content: center;
  padding-top: 3vh;
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
  max-width: 1400px;
  width: 95%;
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
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(90deg, rgba(59, 130, 246, 0.1) 0%, rgba(147, 51, 234, 0.1) 100%);
}

.modal-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #f1f5f9;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #94a3b8;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
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

.spinner-small {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(59, 130, 246, 0.2);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
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

.compare-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.selector-section {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 12px 16px;
}

.selector-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #cbd5e1;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.snapshot-select {
  width: 100%;
  padding: 8px 12px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 8px;
  color: #e2e8f0;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.snapshot-select:hover {
  border-color: rgba(59, 130, 246, 0.5);
  background: rgba(15, 23, 42, 0.9);
}

.snapshot-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.comparison-panel {
  display: flex;
  gap: 20px;
  min-height: 400px;
}

.command-list {
  flex: 0 0 300px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 12px;
  overflow-y: auto;
}

.command-list h3 {
  margin: 0 0 10px 0;
  font-size: 12px;
  font-weight: 600;
  color: #cbd5e1;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.command-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.command-item {
  padding: 8px 10px;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.command-item:hover {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.3);
}

.command-item.active {
  background: rgba(59, 130, 246, 0.3);
  border-color: rgba(59, 130, 246, 0.5);
}

.command-icon {
  font-size: 16px;
  opacity: 0.7;
}

.command-name {
  flex: 1;
  font-size: 13px;
  color: #e2e8f0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.diff-indicator {
  width: 8px;
  height: 8px;
  font-size: 20px;
  line-height: 8px;
}

.diff-indicator.has-diff {
  color: #ef4444;
}

.diff-indicator.no-diff {
  color: #10b981;
}

.diff-view {
  flex: 1;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 20px;
  overflow-y: auto;
}

.diff-view h3 {
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 600;
  color: #cbd5e1;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.diff-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: #94a3b8;
}

.diff-content {
  padding: 16px;
}

.no-diff-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 60px;
  color: #10b981;
  text-align: center;
}

.no-diff-message .icon {
  font-size: 48px;
}

.no-diff-message p {
  font-size: 14px;
  margin: 0;
}

.diff-display {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
}

.diff-text {
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.5;
  color: #e2e8f0;
  white-space: pre;
}

.no-data-message,
.placeholder-message,
.no-selection-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 60px;
  color: #94a3b8;
  text-align: center;
}

.no-selection-message {
  min-height: 400px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
}

.icon {
  font-size: 48px;
}

.no-data-message p,
.placeholder-message p,
.no-selection-message p {
  font-size: 14px;
  margin: 0;
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
.command-list::-webkit-scrollbar,
.diff-view::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.modal-body::-webkit-scrollbar-track,
.command-list::-webkit-scrollbar-track,
.diff-view::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.4);
  border-radius: 4px;
}

.modal-body::-webkit-scrollbar-thumb,
.command-list::-webkit-scrollbar-thumb,
.diff-view::-webkit-scrollbar-thumb {
  background: rgba(71, 85, 105, 0.6);
  border-radius: 4px;
}

.modal-body::-webkit-scrollbar-thumb:hover,
.command-list::-webkit-scrollbar-thumb:hover,
.diff-view::-webkit-scrollbar-thumb:hover {
  background: rgba(71, 85, 105, 0.8);
}
</style>
