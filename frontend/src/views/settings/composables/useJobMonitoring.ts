import { ref, reactive } from 'vue'
import { useNotificationStore } from '@/stores/notification'
import { makeAuthenticatedRequest } from '@/services/api'

export interface JobResult {
  status?: string
  devices_processed?: number
  total_devices?: number
  total_commands?: number
  errors?: Array<{
    device_id?: string
    device_name?: string
    error?: string
    message?: string
  }>
  [key: string]: any
}

export interface Job {
  id: string
  name?: string
  state: string
  timestamp: string
  result?: JobResult
  traceback?: string
}

export interface Worker {
  name: string
  status: string
  loadavg: number[] | null
}

export function useJobMonitoring() {
  const notificationStore = useNotificationStore()

  // State
  const loadingJobStatus = ref(false)
  const submittingTestJob = ref(false)
  const clearingJobs = ref(false)
  const expandedJobs = ref(new Set<string>())
  let jobStatusInterval: number | null = null

  const jobStatus = reactive({
    workerActive: false,
    queueSize: 0,
    activeJobs: 0,
    workers: [] as Worker[],
    recentJobs: [] as Job[]
  })

  // Helper function to check if job result has errors
  const hasErrors = (result: any): boolean => {
    if (!result) return false
    return result.errors && Array.isArray(result.errors) && result.errors.length > 0
  }

  // Toggle job expansion
  const toggleJobExpansion = (jobId: string) => {
    if (expandedJobs.value.has(jobId)) {
      expandedJobs.value.delete(jobId)
    } else {
      expandedJobs.value.add(jobId)
    }
    // Trigger reactivity
    expandedJobs.value = new Set(expandedJobs.value)
  }

  // Format job timestamp
  const formatJobTime = (timestamp: string): string => {
    if (!timestamp) return 'Unknown'
    try {
      const date = new Date(timestamp)
      return date.toLocaleString()
    } catch {
      return timestamp
    }
  }

  // Refresh job status
  const refreshJobStatus = async () => {
    loadingJobStatus.value = true
    try {
      const response = await makeAuthenticatedRequest('/api/settings/jobs/status')

      if (response.ok) {
        const data = await response.json()
        jobStatus.workerActive = data.workerActive
        jobStatus.queueSize = data.queueSize
        jobStatus.activeJobs = data.activeJobs
        jobStatus.workers = data.workers || []
        jobStatus.recentJobs = data.recentJobs || []

        if (data.error) {
          notificationStore.addNotification({
            title: 'Job Status Warning',
            message: data.error,
            type: 'warning',
          })
        }
      } else {
        throw new Error('Failed to fetch job status')
      }
    } catch (error) {
      notificationStore.addNotification({
        title: 'Job Status Error',
        message: 'Failed to fetch job status. Make sure the backend is running.',
        type: 'error',
      })
      console.error('Failed to fetch job status:', error)
    } finally {
      loadingJobStatus.value = false
    }
  }

  // Submit test job
  const submitTestJob = async () => {
    submittingTestJob.value = true
    try {
      const response = await makeAuthenticatedRequest('/api/settings/jobs/test', {
        method: 'POST'
      })

      if (response.ok) {
        const data = await response.json()
        notificationStore.addNotification({
          title: 'Test Job Started',
          message: `Test job submitted with ID: ${data.jobId}`,
          type: 'success',
        })
        // Refresh job status after a short delay to see the new job
        setTimeout(() => refreshJobStatus(), 1000)
      } else {
        throw new Error('Failed to submit test job')
      }
    } catch (error) {
      notificationStore.addNotification({
        title: 'Test Job Error',
        message: 'Failed to submit test job. Make sure the Celery worker is running.',
        type: 'error',
      })
      console.error('Failed to submit test job:', error)
    } finally {
      submittingTestJob.value = false
    }
  }

  // Clear job logs
  const clearJobLogs = async () => {
    if (!confirm('Are you sure you want to clear all job logs? This will remove all completed job results from Redis.')) {
      return
    }

    clearingJobs.value = true
    try {
      const response = await makeAuthenticatedRequest('/api/settings/jobs/clear', {
        method: 'POST'
      })

      if (response.ok) {
        const data = await response.json()
        notificationStore.addNotification({
          title: 'Jobs Cleared',
          message: data.message || 'All job logs have been cleared successfully.',
          type: 'success',
        })
        // Refresh to show updated (empty) list
        await refreshJobStatus()
      } else {
        throw new Error('Failed to clear job logs')
      }
    } catch (error) {
      notificationStore.addNotification({
        title: 'Clear Jobs Error',
        message: 'Failed to clear job logs. Please try again.',
        type: 'error',
      })
      console.error('Failed to clear job logs:', error)
    } finally {
      clearingJobs.value = false
    }
  }

  // Start auto-refresh
  const startAutoRefresh = () => {
    if (jobStatusInterval !== null) return

    jobStatusInterval = window.setInterval(async () => {
      if (!loadingJobStatus.value) {
        await refreshJobStatus()
      }
    }, 2000)
    console.log('▶️ Started job status auto-refresh')
  }

  // Stop auto-refresh
  const stopAutoRefresh = () => {
    if (jobStatusInterval !== null) {
      clearInterval(jobStatusInterval)
      jobStatusInterval = null
      console.log('⏹ Stopped job status auto-refresh')
    }
  }

  return {
    // State
    jobStatus,
    loadingJobStatus,
    submittingTestJob,
    clearingJobs,
    expandedJobs,

    // Methods
    refreshJobStatus,
    submitTestJob,
    clearJobLogs,
    hasErrors,
    toggleJobExpansion,
    formatJobTime,
    startAutoRefresh,
    stopAutoRefresh
  }
}
