/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_NODE_ENV: string
  readonly VITE_ENABLE_SECURE_STORAGE: string
  readonly VITE_SESSION_TIMEOUT_HOURS: string
  readonly VITE_ENABLE_DEBUG_LOGS: string
  readonly VITE_ENABLE_PERFORMANCE_MONITORING: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
