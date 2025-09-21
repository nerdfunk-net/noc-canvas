import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './styles/main.css'
import VueKonva from 'vue-konva'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(VueKonva)

app.mount('#app')
