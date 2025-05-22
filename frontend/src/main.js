import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // 假設您設定了 router
import 'bootstrap/dist/css/bootstrap.min.css' // 匯入 Bootstrap CSS
import 'bootstrap/dist/js/bootstrap.bundle.min.js' // 匯入 Bootstrap JS (如果需要其 JS 功能)

const app = createApp(App)
app.use(router) // 使用 Vue Router
// app.use(createPinia()) // 如果使用 Pinia
app.mount('#app')