<template>
  <div class="space-y-6">
    <!-- Celery Worker Status -->
    <div class="card p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-900">Worker Status</h2>
        <div class="flex space-x-2">
          <button @click="submitTestJob" class="btn-primary" :disabled="!jobStatus.workerActive || submittingTestJob">
            <i class="fas fa-play mr-2" :class="{ 'animate-spin': submittingTestJob }"></i>
            {{ submittingTestJob ? 'Starting...' : 'Test Job' }}
          </button>
          <button @click="refreshJobStatus" class="btn-secondary" :disabled="loadingJobStatus">
            <i class="fas fa-sync-alt mr-2" :class="{ 'animate-spin': loadingJobStatus }"></i>
            {{ loadingJobStatus ? 'Refreshing...' : 'Refresh' }}
          </button>
        </div>
      </div>

      <!-- Worker Information -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div class="bg-gray-50 p-4 rounded-lg">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-gray-600">Worker Status</span>
            <div class="flex items-center">
              <div
                :class="[
                  'w-3 h-3 rounded-full mr-2',
                  jobStatus.workerActive ? 'bg-green-500' : 'bg-red-500'
                ]"
              ></div>
              <span :class="jobStatus.workerActive ? 'text-green-700' : 'text-red-700'">
                {{ jobStatus.workerActive ? 'Active' : 'Inactive' }}
              </span>
            </div>
          </div>
        </div>

        <div class="bg-gray-50 p-4 rounded-lg">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-gray-600">Queue Size</span>
            <span class="text-xl font-bold text-blue-600">{{ jobStatus.queueSize || 0 }}</span>
          </div>
        </div>

        <div class="bg-gray-50 p-4 rounded-lg">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-gray-600">Running Jobs</span>
            <span class="text-xl font-bold text-orange-600">{{ jobStatus.activeJobs || 0 }}</span>
          </div>
        </div>
      </div>

      <!-- Worker Details -->
      <div v-if="jobStatus.workers && jobStatus.workers.length > 0" class="space-y-3">
        <h3 class="text-md font-semibold text-gray-900">Connected Workers</h3>
        <div class="space-y-2">
          <div
            v-for="worker in jobStatus.workers"
            :key="worker.name"
            class="bg-white border border-gray-200 rounded-lg p-3"
          >
            <div class="flex items-center justify-between">
              <div>
                <span class="font-medium text-gray-900">{{ worker.name }}</span>
                <span class="text-sm text-gray-500 ml-2">{{ worker.status }}</span>
              </div>
              <div class="text-sm text-gray-600">
                Load: {{ worker.loadavg ? worker.loadavg.join(', ') : 'N/A' }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- No Workers Message -->
      <div v-else class="text-center py-8">
        <div class="text-4xl mb-4">⚠️</div>
        <h3 class="text-lg font-medium text-gray-900 mb-2">No Workers Connected</h3>
        <p class="text-gray-600">Make sure the Celery worker is running.</p>
      </div>
    </div>

    <!-- Recent Jobs -->
    <div class="card p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-900">Recent Jobs</h2>
        <button
          v-if="jobStatus.recentJobs && jobStatus.recentJobs.length > 0"
          @click="clearJobLogs"
          class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition font-medium text-sm flex items-center gap-2"
          :disabled="clearingJobs"
        >
          <i class="fas fa-trash-alt" :class="{ 'animate-spin': clearingJobs }"></i>
          {{ clearingJobs ? 'Clearing...' : 'Clear Jobs' }}
        </button>
      </div>

      <div v-if="jobStatus.recentJobs && jobStatus.recentJobs.length > 0" class="space-y-3">
        <div
          v-for="job in jobStatus.recentJobs"
          :key="job.id"
          class="bg-white border border-gray-200 rounded-lg p-4"
        >
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center">
              <span class="font-medium text-gray-900">{{ job.name || job.id }}</span>
              <span
                :class="[
                  'ml-2 px-2 py-1 text-xs rounded-full font-semibold',
                  job.state === 'SUCCESS' && hasErrors(job.result) ? 'bg-yellow-100 text-yellow-800' :
                  job.state === 'SUCCESS' ? 'bg-green-100 text-green-800' :
                  job.state === 'PENDING' ? 'bg-yellow-100 text-yellow-800' :
                  job.state === 'STARTED' ? 'bg-blue-100 text-blue-800' :
                  job.state === 'FAILURE' ? 'bg-red-100 text-red-800' :
                  'bg-gray-100 text-gray-800'
                ]"
              >
                {{ job.state === 'SUCCESS' && hasErrors(job.result) ? 'COMPLETED WITH ERRORS' : job.state }}
              </span>
            </div>
            <span class="text-sm text-gray-500">{{ formatJobTime(job.timestamp) }}</span>
          </div>

          <div v-if="job.result" class="mt-3">
            <button
              @click="toggleJobExpansion(job.id)"
              class="flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-800 transition"
            >
              <i :class="expandedJobs.has(job.id) ? 'fas fa-chevron-down' : 'fas fa-chevron-right'"></i>
              {{ expandedJobs.has(job.id) ? 'Hide Details' : 'Show Details' }}
            </button>

            <div v-if="expandedJobs.has(job.id)" class="mt-3 bg-gray-50 p-3 rounded-lg border border-gray-200">
              <!-- Summary Info -->
              <div class="grid grid-cols-2 gap-3 mb-3 text-sm">
                <div v-if="job.result.status">
                  <span class="font-medium text-gray-700">Status:</span>
                  <span class="ml-1 text-gray-900">{{ job.result.status }}</span>
                </div>
                <div v-if="job.result.devices_processed !== undefined">
                  <span class="font-medium text-gray-700">Devices Processed:</span>
                  <span class="ml-1 text-gray-900">{{ job.result.devices_processed }} / {{ job.result.total_devices || 0 }}</span>
                </div>
                <div v-if="job.result.total_commands !== undefined">
                  <span class="font-medium text-gray-700">Commands:</span>
                  <span class="ml-1 text-gray-900">{{ job.result.total_commands }}</span>
                </div>
              </div>

              <!-- Errors Section -->
              <div v-if="job.result.errors && job.result.errors.length > 0" class="mt-3">
                <h4 class="font-semibold text-red-700 mb-2 flex items-center gap-2">
                  <i class="fas fa-exclamation-triangle"></i>
                  Errors ({{ job.result.errors.length }})
                </h4>
                <div class="space-y-2">
                  <div
                    v-for="(error, idx) in job.result.errors"
                    :key="idx"
                    class="bg-red-50 border border-red-200 rounded p-3"
                  >
                    <div v-if="error.device_name" class="font-medium text-red-900 mb-1">
                      Device: {{ error.device_name }}
                    </div>
                    <div v-if="error.device_id" class="text-xs text-red-600 mb-1">
                      ID: {{ error.device_id }}
                    </div>
                    <div v-if="error.error || error.message" class="text-sm text-red-800">
                      {{ error.error || error.message }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- Raw Result -->
              <details class="mt-3">
                <summary class="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                  Raw Result
                </summary>
                <pre class="mt-2 text-xs bg-white p-2 rounded border border-gray-300 overflow-x-auto">{{ JSON.stringify(job.result, null, 2) }}</pre>
              </details>
            </div>
          </div>

          <div v-if="job.traceback" class="text-sm text-red-600 mt-3 bg-red-50 p-3 rounded border border-red-200">
            <strong class="flex items-center gap-2">
              <i class="fas fa-times-circle"></i>
              Error:
            </strong>
            <pre class="whitespace-pre-wrap text-xs mt-2">{{ job.traceback }}</pre>
          </div>
        </div>
      </div>

      <div v-else class="text-center py-8">
        <div class="text-4xl mb-4">📋</div>
        <h3 class="text-lg font-medium text-gray-900 mb-2">No Recent Jobs</h3>
        <p class="text-gray-600">Job history will appear here when tasks are executed.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useJobMonitoring } from '../composables/useJobMonitoring'

const {
  jobStatus,
  loadingJobStatus,
  submittingTestJob,
  clearingJobs,
  expandedJobs,
  refreshJobStatus,
  submitTestJob,
  clearJobLogs,
  hasErrors,
  toggleJobExpansion,
  formatJobTime,
  startAutoRefresh,
  stopAutoRefresh
} = useJobMonitoring()

onMounted(() => {
  refreshJobStatus()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>
