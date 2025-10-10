<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Scheduled Jobs</h2>
        <p class="mt-1 text-sm text-gray-500">
          Manage periodic tasks and cron jobs for automated operations
        </p>
      </div>
      <button @click="showCreateModal = true" class="btn-primary">
        <i class="fas fa-plus mr-2"></i>
        Create Schedule
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="text-center">
        <svg class="animate-spin h-8 w-8 mx-auto mb-2 text-primary-600" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <p class="text-sm text-gray-500">Loading scheduled jobs...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4">
      <div class="flex">
        <i class="fas fa-exclamation-circle text-red-400 mt-0.5 mr-3"></i>
        <div>
          <h3 class="text-sm font-medium text-red-800">Error loading schedules</h3>
          <p class="mt-1 text-sm text-red-700">{{ error }}</p>
          <button @click="loadSchedules" class="mt-2 text-sm text-red-800 hover:text-red-900 font-medium">
            Try Again
          </button>
        </div>
      </div>
    </div>

    <!-- Schedules List -->
    <div v-else-if="schedules.length === 0" class="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
      <i class="fas fa-clock text-gray-400 text-5xl mb-4"></i>
      <h3 class="text-lg font-medium text-gray-900 mb-2">No scheduled jobs yet</h3>
      <p class="text-sm text-gray-500 mb-4">Create your first scheduled job to automate tasks</p>
      <button @click="showCreateModal = true" class="btn-primary">
        <i class="fas fa-plus mr-2"></i>
        Create Schedule
      </button>
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="schedule in schedules"
        :key="schedule.id"
        class="card p-4 hover:shadow-md transition-shadow"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center space-x-3 mb-2">
              <h3 class="text-lg font-semibold text-gray-900">{{ schedule.name }}</h3>
              <span
                :class="[
                  'px-2 py-1 text-xs font-medium rounded-full',
                  schedule.enabled
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-600'
                ]"
              >
                {{ schedule.enabled ? 'Enabled' : 'Disabled' }}
              </span>
              <span
                v-if="schedule.one_off"
                class="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800"
              >
                One-off
              </span>
            </div>

            <p v-if="schedule.description" class="text-sm text-gray-600 mb-3">
              {{ schedule.description }}
            </p>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              <div>
                <span class="text-gray-500">Task:</span>
                <span class="ml-2 font-mono text-gray-700">{{ getTaskName(schedule.task) }}</span>
              </div>

              <div>
                <span class="text-gray-500">Schedule:</span>
                <span class="ml-2 font-medium text-gray-700">{{ formatSchedule(schedule) }}</span>
              </div>

              <div v-if="schedule.last_run_at">
                <span class="text-gray-500">Last Run:</span>
                <span class="ml-2 text-gray-700">{{ formatDate(schedule.last_run_at) }}</span>
              </div>

              <div>
                <span class="text-gray-500">Total Runs:</span>
                <span class="ml-2 text-gray-700">{{ schedule.total_run_count }}</span>
              </div>
            </div>

            <div v-if="schedule.expires" class="mt-2 text-sm">
              <span class="text-gray-500">Expires:</span>
              <span class="ml-2 text-orange-600">{{ formatDate(schedule.expires) }}</span>
            </div>
          </div>

          <div class="flex items-center space-x-2 ml-4">
            <!-- Toggle Enable/Disable Button -->
            <button
              @click="toggleSchedule(schedule)"
              :class="[
                'flex items-center justify-center w-9 h-9 rounded-lg transition-all duration-200 shadow-sm hover:shadow-md',
                schedule.enabled
                  ? 'bg-orange-100 text-orange-700 hover:bg-orange-200'
                  : 'bg-green-100 text-green-700 hover:bg-green-200'
              ]"
              :title="schedule.enabled ? 'Disable Schedule' : 'Enable Schedule'"
            >
              <!-- Pause Icon (when enabled) -->
              <svg v-if="schedule.enabled" class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              <!-- Play Icon (when disabled) -->
              <svg v-else class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd" />
              </svg>
            </button>

            <!-- Edit Button -->
            <button
              @click="editSchedule(schedule)"
              class="flex items-center justify-center w-9 h-9 rounded-lg transition-all duration-200 shadow-sm hover:shadow-md bg-blue-100 text-blue-700 hover:bg-blue-200"
              title="Edit Schedule"
            >
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
              </svg>
            </button>

            <!-- Delete Button -->
            <button
              @click="confirmDelete(schedule)"
              class="flex items-center justify-center w-9 h-9 rounded-lg transition-all duration-200 shadow-sm hover:shadow-md bg-red-100 text-red-700 hover:bg-red-200"
              title="Delete Schedule"
            >
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <ScheduleEditor
      :show="showCreateModal || showEditModal"
      :schedule="editingSchedule"
      :available-tasks="availableTasks"
      @close="closeModals"
      @save="handleSave"
    />

    <!-- Delete Confirmation Dialog -->
    <ConfirmDialog
      :show="showDeleteDialog"
      title="Delete Scheduled Job"
      :message="`Are you sure you want to delete '${deletingSchedule?.name}'? This action cannot be undone.`"
      confirm-text="Delete"
      cancel-text="Cancel"
      @confirm="handleDelete"
      @cancel="showDeleteDialog = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { makeAuthenticatedRequest } from '@/services/api'
import ScheduleEditor from './ScheduleEditor.vue'
import ConfirmDialog from './ConfirmDialog.vue'

interface Schedule {
  id: number
  name: string
  task: string
  description?: string
  schedule_type: string
  crontab?: {
    minute: string
    hour: string
    day_of_week: string
    day_of_month: string
    month_of_year: string
  }
  interval?: {
    every: number
    period: string
  }
  args: any[]
  kwargs: Record<string, any>
  enabled: boolean
  one_off: boolean
  last_run_at?: string
  total_run_count: number
  date_changed: string
  expires?: string
}

interface AvailableTask {
  name: string
  task: string
  description: string
  args_schema: Record<string, any>
  kwargs_schema: Record<string, any>
}

const schedules = ref<Schedule[]>([])
const availableTasks = ref<AvailableTask[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const showCreateModal = ref(false)
const showEditModal = ref(false)
const editingSchedule = ref<Schedule | null>(null)

const showDeleteDialog = ref(false)
const deletingSchedule = ref<Schedule | null>(null)

const loadSchedules = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await makeAuthenticatedRequest('/api/scheduler/tasks')
    if (response.ok) {
      schedules.value = await response.json()
    } else {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to load schedules' }))
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }
  } catch (err: any) {
    error.value = err.message || 'An error occurred while loading schedules'
    console.error('Error loading schedules:', err)
  } finally {
    loading.value = false
  }
}

const loadAvailableTasks = async () => {
  try {
    const response = await makeAuthenticatedRequest('/api/scheduler/available-tasks')
    if (response.ok) {
      availableTasks.value = await response.json()
    }
  } catch (err) {
    console.error('Error loading available tasks:', err)
  }
}

const getTaskName = (taskPath: string): string => {
  const parts = taskPath.split('.')
  return parts[parts.length - 1]
}

const formatSchedule = (schedule: Schedule): string => {
  if (schedule.schedule_type === 'crontab' && schedule.crontab) {
    const c = schedule.crontab
    // Simple cron formatting
    if (c.minute === '*' && c.hour === '*' && c.day_of_week === '*' && c.day_of_month === '*') {
      return 'Every minute'
    }
    return `${c.minute} ${c.hour} ${c.day_of_month} ${c.month_of_year} ${c.day_of_week}`
  } else if (schedule.schedule_type === 'interval' && schedule.interval) {
    return `Every ${schedule.interval.every} ${schedule.interval.period}`
  }
  return 'Unknown'
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleString()
}

const toggleSchedule = async (schedule: Schedule) => {
  try {
    const response = await makeAuthenticatedRequest(`/api/scheduler/tasks/${schedule.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: !schedule.enabled })
    })

    if (response.ok) {
      schedule.enabled = !schedule.enabled
    } else {
      throw new Error('Failed to toggle schedule')
    }
  } catch (err) {
    console.error('Error toggling schedule:', err)
    alert('Failed to toggle schedule. Please try again.')
  }
}

const editSchedule = (schedule: Schedule) => {
  editingSchedule.value = { ...schedule }
  showEditModal.value = true
}

const confirmDelete = (schedule: Schedule) => {
  deletingSchedule.value = schedule
  showDeleteDialog.value = true
}

const handleDelete = async () => {
  if (!deletingSchedule.value) return

  try {
    const response = await makeAuthenticatedRequest(
      `/api/scheduler/tasks/${deletingSchedule.value.id}`,
      { method: 'DELETE' }
    )

    if (response.ok) {
      await loadSchedules()
      showDeleteDialog.value = false
      deletingSchedule.value = null
    } else {
      throw new Error('Failed to delete schedule')
    }
  } catch (err) {
    console.error('Error deleting schedule:', err)
    alert('Failed to delete schedule. Please try again.')
  }
}

const closeModals = () => {
  showCreateModal.value = false
  showEditModal.value = false
  editingSchedule.value = null
}

const handleSave = async (scheduleData: any) => {
  try {
    const isEdit = !!editingSchedule.value

    const response = await makeAuthenticatedRequest(
      isEdit ? `/api/scheduler/tasks/${editingSchedule.value!.id}` : '/api/scheduler/tasks',
      {
        method: isEdit ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(scheduleData)
      }
    )

    if (response.ok) {
      await loadSchedules()
      closeModals()
    } else {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Failed to save schedule')
    }
  } catch (err: any) {
    console.error('Error saving schedule:', err)
    alert(err.message || 'Failed to save schedule. Please try again.')
  }
}

onMounted(async () => {
  await Promise.all([loadSchedules(), loadAvailableTasks()])
})
</script>
