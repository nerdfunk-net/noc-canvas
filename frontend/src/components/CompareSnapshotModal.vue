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
              <div class="diff-header">
                <h3 v-if="selectedCommand">{{ selectedCommand }}</h3>
                <h3 v-else>Select a command to view differences</h3>

                <div v-if="selectedCommand" class="diff-controls">
                  <div class="tabs">
                    <button
                      :class="['tab-btn', { active: activeTab === 'summary' }]"
                      @click="activeTab = 'summary'"
                    >
                      Summary
                    </button>
                    <button
                      :class="['tab-btn', { active: activeTab === 'raw' }]"
                      @click="activeTab = 'raw'"
                    >
                      Raw
                    </button>
                  </div>
                  <button
                    v-if="activeTab === 'summary'"
                    :class="['filter-btn', { active: showDiffOnly }]"
                    @click="showDiffOnly = !showDiffOnly"
                  >
                    {{ showDiffOnly ? 'Show All' : 'Show Diff Only' }}
                  </button>
                </div>
              </div>

              <div v-if="selectedCommand && loadingDiff" class="diff-loading">
                <div class="spinner-small"></div>
                <p>Computing diff...</p>
              </div>

              <div v-else-if="selectedCommand && diffResult" class="diff-content">
                <div v-if="diffResult.identical" class="no-diff-message">
                  <span class="icon">✓</span>
                  <p>No differences found. Baseline and snapshot are identical for this command.</p>
                </div>
                <div v-else>
                  <!-- Summary Tab -->
                  <div v-if="activeTab === 'summary'" class="summary-view">
                    <!-- Structured comparison for supported commands -->
                    <div v-if="diffResult.structured">
                      <div
                        v-for="(itemData, itemName) in filteredStructuredData"
                        :key="itemName"
                        class="interface-group"
                      >
                        <div class="interface-header" :class="itemData.status">
                          <span class="interface-name">{{ itemName }}</span>
                          <span class="interface-status">{{ itemData.status }}</span>
                        </div>
                        <table class="diff-table">
                          <thead>
                            <tr>
                              <th>Field</th>
                              <th>Baseline</th>
                              <th>Snapshot</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr
                              v-for="field in itemData.fields"
                              :key="field.field"
                              :class="field.changed ? 'different' : 'equal'"
                            >
                              <td class="field-name">{{ field.field }}</td>
                              <td class="baseline-value">{{ field.baseline || '-' }}</td>
                              <td class="snapshot-value">{{ field.snapshot || '-' }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>

                    <!-- Fallback line-by-line comparison -->
                    <table v-else class="diff-table">
                      <thead>
                        <tr>
                          <th>Line</th>
                          <th>Baseline</th>
                          <th>Snapshot</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr
                          v-for="(row, index) in filteredTableData"
                          :key="index"
                          :class="row.status"
                        >
                          <td class="line-number">{{ row.lineNumber }}</td>
                          <td class="baseline-value">{{ row.baseline }}</td>
                          <td class="snapshot-value">{{ row.snapshot }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  <!-- Raw Tab -->
                  <div v-if="activeTab === 'raw'" class="diff-display">
                    <pre class="diff-text">{{ diffResult.diff }}</pre>
                  </div>
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
import { ref, watch, computed } from 'vue'
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
const activeTab = ref<'summary' | 'raw'>('summary')
const showDiffOnly = ref(false)

const filteredTableData = computed(() => {
  if (!diffResult.value?.tableData) return []
  if (!showDiffOnly.value) return diffResult.value.tableData
  return diffResult.value.tableData.filter((row: any) => row.status === 'different')
})

const filteredStructuredData = computed(() => {
  // Support interfaces, routes, arp_entries, or any other grouped data
  const data = diffResult.value?.structured?.interfaces ||
                diffResult.value?.structured?.routes ||
                diffResult.value?.structured?.arp_entries
  if (!data) return {}

  if (!showDiffOnly.value) {
    return data
  }

  // Filter to show only items with changes AND only changed fields
  const filtered: any = {}
  for (const [itemName, itemData] of Object.entries(data)) {
    const item = itemData as any

    // Skip unchanged items
    if (item.status === 'unchanged') continue

    // For changed items, filter to show only changed fields
    if (item.status === 'changed') {
      filtered[itemName] = {
        ...item,
        fields: item.fields.filter((field: any) => field.changed)
      }
    } else {
      // For added/removed items, show all fields
      filtered[itemName] = item
    }
  }
  return filtered
})

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

      // Try structured comparison first
      const structuredResponse = await fetch(`/api/snapshots/compare?baseline_id=${baselineData.id}&snapshot_id=${snapshotData.id}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      }).then(r => r.json())

      if (structuredResponse.supported) {
        // Use structured comparison to determine if there are differences
        const comparison = structuredResponse.comparison
        const data = comparison.interfaces || comparison.routes || comparison.arp_entries

        let hasDifference = false
        if (data) {
          for (const itemData of Object.values(data)) {
            if ((itemData as any).status !== 'unchanged') {
              hasDifference = true
              break
            }
          }
        }
        commandDiffStatus.value[command] = hasDifference
      } else {
        // Fallback to simple string comparison for unsupported commands
        const [baselineDetail, snapshotDetail] = await Promise.all([
          fetch(`/api/snapshots/${baselineData.id}`, {
            headers: { 'Authorization': `Bearer ${token}` },
          }).then(r => r.json()),
          fetch(`/api/snapshots/${snapshotData.id}`, {
            headers: { 'Authorization': `Bearer ${token}` },
          }).then(r => r.json())
        ])

        const hasDifference = baselineDetail.normalized_output !== snapshotDetail.normalized_output
        commandDiffStatus.value[command] = hasDifference
      }

    } catch (err) {
      console.error(`Error computing diff status for ${command}:`, err)
      commandDiffStatus.value[command] = false
    }
  }
}

const selectCommand = async (command: string) => {
  selectedCommand.value = command
  activeTab.value = 'summary' // Reset to summary tab
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
      // Try structured comparison first
      const structuredResponse = await fetch(`/api/snapshots/compare?baseline_id=${baselineData.id}&snapshot_id=${snapshotData.id}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      }).then(r => r.json())

      // Generate text diff for Raw tab
      const diff = generateDiff(baselineOutput, snapshotOutput)

      if (structuredResponse.supported) {
        // Use structured comparison for Summary tab
        diffResult.value = {
          identical: false,
          diff,
          structured: structuredResponse.comparison
        }
      } else {
        // Fallback to line-by-line comparison
        const tableData = generateTableData(baselineOutput, snapshotOutput)
        diffResult.value = {
          identical: false,
          diff,
          tableData
        }
      }
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

const generateTableData = (baseline: string, snapshot: string) => {
  const baselineLines = baseline.split('\n')
  const snapshotLines = snapshot.split('\n')
  const maxLines = Math.max(baselineLines.length, snapshotLines.length)
  const tableData: Array<{ lineNumber: number; baseline: string; snapshot: string; status: 'equal' | 'different' }> = []

  for (let i = 0; i < maxLines; i++) {
    const baseLine = baselineLines[i] || ''
    const snapLine = snapshotLines[i] || ''

    tableData.push({
      lineNumber: i + 1,
      baseline: baseLine,
      snapshot: snapLine,
      status: baseLine === snapLine ? 'equal' : 'different'
    })
  }

  return tableData
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
  background: rgba(0, 0, 0, 0.5);
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
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  max-width: 1400px;
  width: 95%;
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
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f9fafb;
}

.modal-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #111827;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #6b7280;
  cursor: pointer;
  padding: 0;
  width: 28px;
  height: 28px;
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

.spinner-small {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
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
  color: #ef4444;
  font-size: 14px;
}

.compare-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.selector-section {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
}

.selector-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.snapshot-select {
  width: 100%;
  padding: 10px 12px;
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  color: #111827;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.snapshot-select:hover {
  border-color: #3b82f6;
}

.snapshot-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.comparison-panel {
  display: flex;
  gap: 20px;
  min-height: 400px;
}

.command-list {
  flex: 0 0 300px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  overflow-y: auto;
}

.command-list h3 {
  margin: 0 0 12px 0;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.command-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.command-item {
  padding: 10px 12px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.command-item:hover {
  background: #eff6ff;
  border-color: #3b82f6;
}

.command-item.active {
  background: #dbeafe;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}

.command-icon {
  font-size: 16px;
  opacity: 0.6;
}

.command-name {
  flex: 1;
  font-size: 13px;
  color: #111827;
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
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.diff-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  gap: 16px;
}

.diff-view h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #111827;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.diff-controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.tabs {
  display: flex;
  gap: 4px;
  background: #f3f4f6;
  padding: 4px;
  border-radius: 6px;
}

.tab-btn {
  padding: 6px 16px;
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

.filter-btn {
  padding: 6px 14px;
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  color: #374151;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.filter-btn:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}

.filter-btn.active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: #ffffff;
}

.diff-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: #6b7280;
}

.diff-content {
  padding: 16px;
  flex: 1;
  overflow-y: auto;
}

.summary-view {
  overflow-x: auto;
}

.interface-group {
  margin-bottom: 24px;
}

.interface-group:last-child {
  margin-bottom: 0;
}

.interface-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 8px 8px 0 0;
  border-left: 4px solid;
  margin-bottom: 0;
  border: 1px solid #e5e7eb;
  border-bottom: none;
}

.interface-header.unchanged {
  border-left-color: #10b981;
  background: #f0fdf4;
}

.interface-header.changed {
  border-left-color: #f59e0b;
  background: #fffbeb;
}

.interface-header.added {
  border-left-color: #3b82f6;
  background: #eff6ff;
}

.interface-header.removed {
  border-left-color: #ef4444;
  background: #fef2f2;
}

.interface-name {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-weight: 600;
  font-size: 14px;
  color: #111827;
}

.interface-status {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 4px 10px;
  border-radius: 4px;
  background: #ffffff;
}

.interface-header.unchanged .interface-status {
  color: #10b981;
}

.interface-header.changed .interface-status {
  color: #f59e0b;
}

.interface-header.added .interface-status {
  color: #3b82f6;
}

.interface-header.removed .interface-status {
  color: #ef4444;
}

.interface-group .diff-table {
  border-radius: 0 0 8px 8px;
  overflow: hidden;
}

.diff-table {
  width: 100%;
  border-collapse: collapse;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.diff-table thead {
  position: sticky;
  top: 0;
  background: #f9fafb;
  z-index: 1;
}

.diff-table th {
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 2px solid #e5e7eb;
  text-transform: uppercase;
  font-size: 11px;
  letter-spacing: 0.5px;
  background: #f9fafb;
}

.diff-table th:first-child {
  text-align: center;
}

/* For structured comparison (Field column) */
.interface-group .diff-table th:nth-child(1) {
  width: 40%;
}

.interface-group .diff-table th:nth-child(2),
.interface-group .diff-table th:nth-child(3) {
  width: 30%;
}

/* For line-by-line comparison (Line column) */
.summary-view > .diff-table th:nth-child(1) {
  width: 80px;
}

.summary-view > .diff-table th:nth-child(2),
.summary-view > .diff-table th:nth-child(3) {
  width: calc((100% - 80px) / 2);
}

.diff-table td {
  padding: 8px 12px;
  border-bottom: 1px solid #f3f4f6;
  color: #111827;
  white-space: pre-wrap;
  word-break: break-all;
}

.diff-table .line-number,
.diff-table .field-name {
  text-align: left;
  color: #6b7280;
  font-weight: 600;
  background: #f9fafb;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.diff-table .line-number {
  text-align: center;
}

.diff-table tr.equal {
  background: #f0fdf4;
  border-left: 3px solid #10b981;
}

.diff-table tr.different {
  background: #fef2f2;
  border-left: 3px solid #ef4444;
}

.diff-table tr.equal td {
  color: #065f46;
}

.diff-table tr.different td {
  color: #991b1b;
}

.diff-table tr.different .baseline-value {
  background: #fee2e2;
}

.diff-table tr.different .snapshot-value {
  background: #fecaca;
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
  color: #059669;
}

.diff-display {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
}

.diff-text {
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.6;
  color: #111827;
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
  color: #6b7280;
  text-align: center;
}

.no-selection-message {
  min-height: 400px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
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
.command-list::-webkit-scrollbar,
.diff-view::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.modal-body::-webkit-scrollbar-track,
.command-list::-webkit-scrollbar-track,
.diff-view::-webkit-scrollbar-track {
  background: #f3f4f6;
  border-radius: 4px;
}

.modal-body::-webkit-scrollbar-thumb,
.command-list::-webkit-scrollbar-thumb,
.diff-view::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 4px;
}

.modal-body::-webkit-scrollbar-thumb:hover,
.command-list::-webkit-scrollbar-thumb:hover,
.diff-view::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
</style>
