import {createApp} from 'vue'
import {createPinia} from "pinia";

import App from './App.vue'
import router from './router'

import 'bootstrap/dist/css/bootstrap.min.css' // 匯入 Bootstrap CSS
import 'bootstrap/dist/js/bootstrap.bundle.min.js'


const app = createApp(App)
const pinia = createPinia()

app.use(pinia);
app.use(router)

app.mount('#app')