import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import '@/styles/var.scss'
import '@/styles/global.scss'
import App from './App.vue'
import router from './router'
import DefaultLayout from './layouts/DefaultLayout.vue'
import LofterTabbar from './components/LofterTabbar.vue'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.component('DefaultLayout', DefaultLayout)
app.component('LofterTabbar', LofterTabbar)
app.mount('#app')
