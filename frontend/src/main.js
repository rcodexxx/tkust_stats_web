import {createApp} from 'vue'
import {createPinia} from 'pinia'

import App from './App.vue'
import router from './router'
import naive from 'naive-ui'
import {useAuthStore} from "@/stores/authStore.js";

import 'vfonts/Lato.css'
import 'vfonts/FiraCode.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(naive)

router.beforeEach((to, from, next) => {
    const authStore = useAuthStore();

    const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
    const guestOnly = to.matched.some(record => record.meta.guestOnly);

    if (requiresAuth && !authStore.isAuthenticated) {
        // 如果頁面需要認證，但使用者未登入，則導向登入頁
        // 將他們想去的頁面路徑儲存在 query 中，以便登入後重定向
        next({name: 'Login', query: {redirect: to.fullPath}});
    } else if (guestOnly && authStore.isAuthenticated) {
        // 如果頁面只允許訪客訪問，但使用者已登入，則導向首頁
        next({name: 'Leaderboard'});
    } else {
        // 其他所有情況，正常放行
        next();
    }
});

app.mount('#app')