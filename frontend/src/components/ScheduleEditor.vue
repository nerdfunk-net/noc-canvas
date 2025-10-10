<template>
  <div
    v-if="show"
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
    @click.self="$emit('close')"
  >
    <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b border-gray-200">
        <h2 class="text-xl font-semibold text-gray-900">
          {{ isEdit ? 'Edit Scheduled Job' : 'Create Scheduled Job' }}
        </h2>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">
          <i class="fas fa-times text-xl"></i>
        </button>
      </div>

      <!-- Form -->
      <div class="p-6 space-y-6">
        <!-- Name -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Job Name <span class="text-red-500">*</span>
          </label>
          <input
            v-model="form.name"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            placeholder="e.g., Daily Nautobot Sync"
            required
          />
        </div>

        <!-- Description -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Description</label>
          <textarea
            v-model="form.description"
            rows="2"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            placeholder="Optional description of what this job does"
          ></textarea>
        </div>

        <!-- Task Selection -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Task <span class="text-red-500">*</span>
          </label>
          <select
            v-model="form.task"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            required
            @change="onTaskChange"
          >
            <option value="">Select a task...</option>
            <option v-for="task in availableTasks" :key="task.task" :value="task.task">
              {{ task.name }} - {{ task.description }}
            </option>
          </select>
          <p v-if="selectedTask" class="mt-1 text-xs text-gray-500">
            {{ selectedTask.description }}
          </p>
        </div>

        <!-- Schedule Type -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Schedule Type <span class="text-red-500">*</span>
          </label>
          <div class="flex space-x-4">
            <label class="flex items-center">
              <input
                v-model="form.schedule_type"
                type="radio"
                value="interval"
                class="mr-2"
              />
              <span>Interval</span>
            </label>
            <label class="flex items-center">
              <input
                v-model="form.schedule_type"
                type="radio"
                value="crontab"
                class="mr-2"
              />
              <span>Cron Expression</span>
            </label>
          </div>
        </div>

        <!-- Interval Schedule -->
        <div v-if="form.schedule_type === 'interval'" class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Every <span class="text-red-500">*</span>
            </label>
            <input
              v-model.number="form.interval.every"
              type="number"
              min="1"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              required
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Period <span class="text-red-500">*</span>
            </label>
            <select
              v-model="form.interval.period"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              required
            >
              <option value="seconds">Seconds</option>
              <option value="minutes">Minutes</option>
              <option value="hours">Hours</option>
              <option value="days">Days</option>
            </select>
          </div>
        </div>

        <!-- Crontab Schedule -->
        <div v-if="form.schedule_type === 'crontab'" class="space-y-4">
          <div class="bg-blue-50 border border-blue-200 rounded-md p-3">
            <p class="text-sm text-blue-800">
              <i class="fas fa-info-circle mr-1"></i>
              Use cron syntax: * = any, */5 = every 5, 0-23 = range, 1,3,5 = specific values
            </p>
          </div>

          <div class="grid grid-cols-5 gap-3">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Minute</label>
              <input
                v-model="form.crontab.minute"
                type="text"
                class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="*"
              />
              <span class="text-xs text-gray-500">0-59</span>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Hour</label>
              <input
                v-model="form.crontab.hour"
                type="text"
                class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="*"
              />
              <span class="text-xs text-gray-500">0-23</span>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Day</label>
              <input
                v-model="form.crontab.day_of_month"
                type="text"
                class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="*"
              />
              <span class="text-xs text-gray-500">1-31</span>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Month</label>
              <input
                v-model="form.crontab.month_of_year"
                type="text"
                class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="*"
              />
              <span class="text-xs text-gray-500">1-12</span>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Day of Week</label>
              <input
                v-model="form.crontab.day_of_week"
                type="text"
                class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="*"
              />
              <span class="text-xs text-gray-500">0-6</span>
            </div>
          </div>

          <!-- Common Cron Presets -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Quick Presets</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="preset in cronPresets"
                :key="preset.name"
                @click="applyCronPreset(preset)"
                type="button"
                class="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
              >
                {{ preset.name }}
              </button>
            </div>
          </div>
        </div>

        <!-- Task Arguments -->
        <div v-if="selectedTask && (Object.keys(selectedTask.kwargs_schema).length > 0 || Object.keys(selectedTask.args_schema).length > 0)">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Task Arguments (JSON)
          </label>
          <textarea
            v-model="argsJson"
            rows="4"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 font-mono text-sm"
            placeholder='{"key": "value"}'
          ></textarea>
          <p class="mt-1 text-xs text-gray-500">
            Available parameters: {{ Object.keys(selectedTask.kwargs_schema).join(', ') || 'None' }}
          </p>
        </div>

        <!-- Options -->
        <div class="space-y-3">
          <label class="flex items-center">
            <input
              v-model="form.enabled"
              type="checkbox"
              class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span class="ml-2 text-sm text-gray-700">Enable immediately</span>
          </label>

          <label class="flex items-center">
            <input
              v-model="form.one_off"
              type="checkbox"
              class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span class="ml-2 text-sm text-gray-700">Run only once (one-off task)</span>
          </label>
        </div>

        <!-- Expiry Date -->
        <div>
          <label class="flex items-center mb-2">
            <input
              v-model="hasExpiry"
              type="checkbox"
              class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span class="ml-2 text-sm font-medium text-gray-700">Set expiry date</span>
          </label>
          <input
            v-if="hasExpiry"
            v-model="expiryDate"
            type="datetime-local"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
      </div>

      <!-- Footer -->
      <div class="flex items-center justify-end space-x-3 p-6 border-t border-gray-200 bg-gray-50">
        <button
          @click="$emit('close')"
          type="button"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          @click="handleSave"
          type="button"
          class="btn-primary"
        >
          <i class="fas fa-save mr-2"></i>
          {{ isEdit ? 'Update' : 'Create' }} Schedule
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'

interface Props {
  show: boolean
  schedule?: any
  availableTasks: any[]
}

const props = defineProps<Props>()
const emit = defineEmits(['close', 'save'])

const isEdit = computed(() => !!props.schedule)

const form = ref({
  name: '',
  task: '',
  description: '',
  schedule_type: 'interval',
  interval: {
    every: 1,
    period: 'hours'
  },
  crontab: {
    minute: '*',
    hour: '*',
    day_of_week: '*',
    day_of_month: '*',
    month_of_year: '*'
  },
  args: [],
  kwargs: {},
  enabled: true,
  one_off: false,
  expires: null as string | null
})

const argsJson = ref('{}')
const hasExpiry = ref(false)
const expiryDate = ref('')

const selectedTask = computed(() => {
  return props.availableTasks.find(t => t.task === form.value.task)
})

const cronPresets = [
  { name: 'Every minute', cron: { minute: '*', hour: '*', day_of_month: '*', month_of_year: '*', day_of_week: '*' } },
  { name: 'Hourly', cron: { minute: '0', hour: '*', day_of_month: '*', month_of_year: '*', day_of_week: '*' } },
  { name: 'Daily at midnight', cron: { minute: '0', hour: '0', day_of_month: '*', month_of_year: '*', day_of_week: '*' } },
  { name: 'Weekly (Mon)', cron: { minute: '0', hour: '0', day_of_month: '*', month_of_year: '*', day_of_week: '1' } },
  { name: 'Monthly (1st)', cron: { minute: '0', hour: '0', day_of_month: '1', month_of_year: '*', day_of_week: '*' } },
]

watch(() => props.show, (newVal) => {
  if (newVal) {
    if (props.schedule) {
      // Edit mode - populate form with existing schedule
      form.value = {
        name: props.schedule.name,
        task: props.schedule.task,
        description: props.schedule.description || '',
        schedule_type: props.schedule.schedule_type,
        interval: props.schedule.interval || { every: 1, period: 'hours' },
        crontab: props.schedule.crontab || { minute: '*', hour: '*', day_of_week: '*', day_of_month: '*', month_of_year: '*' },
        args: props.schedule.args || [],
        kwargs: props.schedule.kwargs || {},
        enabled: props.schedule.enabled,
        one_off: props.schedule.one_off,
        expires: props.schedule.expires || null
      }
      argsJson.value = JSON.stringify(props.schedule.kwargs || {}, null, 2)

      if (props.schedule.expires) {
        hasExpiry.value = true
        // Convert ISO string to datetime-local format
        const date = new Date(props.schedule.expires)
        expiryDate.value = date.toISOString().slice(0, 16)
      }
    } else {
      // Create mode - reset form
      resetForm()
    }
  }
})

const resetForm = () => {
  form.value = {
    name: '',
    task: '',
    description: '',
    schedule_type: 'interval',
    interval: {
      every: 1,
      period: 'hours'
    },
    crontab: {
      minute: '*',
      hour: '*',
      day_of_week: '*',
      day_of_month: '*',
      month_of_year: '*'
    },
    args: [],
    kwargs: {},
    enabled: true,
    one_off: false,
    expires: null
  }
  argsJson.value = '{}'
  hasExpiry.value = false
  expiryDate.value = ''
}

const onTaskChange = () => {
  // Reset args when task changes
  argsJson.value = '{}'
  form.value.kwargs = {}
}

const applyCronPreset = (preset: any) => {
  form.value.crontab = { ...preset.cron }
}

const handleSave = () => {
  // Validate
  if (!form.value.name || !form.value.task) {
    alert('Please fill in all required fields')
    return
  }

  // Parse JSON args
  try {
    form.value.kwargs = JSON.parse(argsJson.value)
  } catch (e) {
    alert('Invalid JSON in task arguments')
    return
  }

  // Handle expiry
  if (hasExpiry.value && expiryDate.value) {
    form.value.expires = new Date(expiryDate.value).toISOString()
  } else {
    form.value.expires = null
  }

  // Prepare data based on schedule type
  const scheduleData: any = {
    name: form.value.name,
    task: form.value.task,
    description: form.value.description,
    schedule_type: form.value.schedule_type,
    args: form.value.args,
    kwargs: form.value.kwargs,
    enabled: form.value.enabled,
    one_off: form.value.one_off,
    expires: form.value.expires
  }

  if (form.value.schedule_type === 'interval') {
    scheduleData.interval = form.value.interval
  } else {
    scheduleData.crontab = form.value.crontab
  }

  emit('save', scheduleData)
}
</script>
