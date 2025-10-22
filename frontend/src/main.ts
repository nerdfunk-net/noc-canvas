import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './styles/main.css'
import '@fortawesome/fontawesome-free/css/all.min.css'
import VueKonva from 'vue-konva'
import { useCommands } from './composables/useCommands'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(VueKonva)

app.mount('#app')

// Initialize commands after app is mounted
const { initializeCommands } = useCommands()
initializeCommands()
