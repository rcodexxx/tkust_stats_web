import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import 'bootstrap/dist/css/bootstrap.min.css' // 匯入 Bootstrap CSS
import 'bootstrap/dist/js/bootstrap.bundle.min.js' // 匯入 Bootstrap JS (如果需要其 JS 功能)

const app = createApp(App)
app.use(router)
app.mount('#app')