/**
 * Logging utility that respects environment
 * In production, only errors are logged (sanitized)
 * In development, all logs are enabled
 */

const isDevelopment = import.meta.env.DEV || import.meta.env.VITE_ENABLE_DEBUG_LOGS === 'true'

/**
 * Sanitize data for logging (remove sensitive information)
 */
function sanitize(data: any): any {
  if (typeof data === 'string') {
    // Don't log long tokens or sensitive-looking strings
    if (data.length > 100) {
      return `[String: ${data.length} chars]`
    }
    return data
  }

  if (typeof data === 'object' && data !== null) {
    // Hide potentially sensitive object data in production
    if (!isDevelopment) {
      return '[Object]'
    }
    return data
  }

  return data
}

export const logger = {
  /**
   * Debug logs - only in development
   */
  debug: (...args: any[]) => {
    if (isDevelopment) {
      console.log(...args)
    }
  },

  /**
   * Info logs - only in development
   */
  info: (...args: any[]) => {
    if (isDevelopment) {
      console.info(...args)
    }
  },

  /**
   * Warning logs - always shown but sanitized
   */
  warn: (...args: any[]) => {
    const sanitized = isDevelopment ? args : args.map(sanitize)
    console.warn(...sanitized)
  },

  /**
   * Error logs - always shown but sanitized
   */
  error: (...args: any[]) => {
    const sanitized = isDevelopment ? args : args.map(sanitize)
    console.error(...sanitized)
  },

  /**
   * Group start - only in development
   */
  group: (label: string) => {
    if (isDevelopment) {
      console.group(label)
    }
  },

  /**
   * Group end - only in development
   */
  groupEnd: () => {
    if (isDevelopment) {
      console.groupEnd()
    }
  }
}

// Export type for better IDE support
export type Logger = typeof logger
