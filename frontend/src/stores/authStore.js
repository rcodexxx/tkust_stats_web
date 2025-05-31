// frontend/src/stores/authStore.js
import {defineStore} from 'pinia';
import axios from 'axios'; // 或者您封裝的 apiClient
import router from '../router'; // 用於登入/登出後的跳轉

const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    timeout: 10000,
});

// 請求攔截器：自動附加 Authorization 標頭
apiClient.interceptors.request.use(config => {
    const token = localStorage.getItem('accessToken');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
}, error => {
    return Promise.reject(error);
});

// 回應攔截器：處理 401 (Token 過期/無效) 等錯誤
apiClient.interceptors.response.use(
    response => response,
    async error => {
        const originalRequest = error.config;
        if (error.response && error.response.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true; // 標記已重試，避免無限循環
            console.warn("Access token expired or invalid. Attempting to refresh or logout.");

            const refreshToken = localStorage.getItem('refreshToken');
            if (refreshToken) {
                try {
                    const refreshResponse = await axios.post(`${import.meta.env.VITE_API_BASE_URL}/auth/refresh`, {}, {
                        headers: {'Authorization': `Bearer ${refreshToken}`}
                    });
                    const newAccessToken = refreshResponse.data.access_token;
                    localStorage.setItem('accessToken', newAccessToken);
                    apiClient.defaults.headers.common['Authorization'] = `Bearer ${newAccessToken}`;
                    originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
                    return apiClient(originalRequest); // 重試原始請求
                } catch (refreshError) {
                    console.error("Refresh token failed:", refreshError);
                    // Refresh 失敗，執行登出
                }
            }
// 如果沒有 refresh token 邏輯或 refresh 失敗，則執行登出
            const authStore = useAuthStore(); // 在攔截器內部獲取 store 實例
            authStore.logoutAndRedirect();
            return Promise.reject(error);
        }
        return Promise.reject(error);
    }
);


export const useAuthStore = defineStore('auth', {
    state: () => ({
        accessToken: localStorage.getItem('accessToken') || null,
        refreshToken: localStorage.getItem('refreshToken') || null, // 如果使用 refresh token
        user: JSON.parse(localStorage.getItem('user')) || null, // 儲存使用者物件 {id, username, name, display_name, role}
        status: { // 用於追蹤 API 請求狀態
            loggingIn: false,
            loginError: null,
            registering: false,
            registerError: null,
        },
    }),
    getters: {
        isAuthenticated: (state) => !!state.accessToken,
        currentUser: (state) => state.user,
        userRole: (state) => state.user?.role, // 例如 'ADMIN', 'PLAYER', 'CADRE'
        userDisplayName: (state) => {
            if (state.user) {
                return state.user.display_name || state.user.name || state.user.username || '使用者';
            }
            return '訪客';
        },
        isAdmin: (state) => state.user?.role === 'ADMIN',
        isCadre: (state) => state.user?.role === 'CADRE',
        isCoach: (state) => state.user?.role === 'COACH',
    },
    actions: {
        async login(credentials) {
            this.status.loggingIn = true;
            this.status.loginError = null;
            try {
                const response = await apiClient.post('/auth/login', credentials); // 使用 apiClient
                const {access_token, refresh_token, user} = response.data;

                this.accessToken = access_token;
                if (refresh_token) this.refreshToken = refresh_token;
                this.user = user;

                localStorage.setItem('accessToken', access_token);
                if (refresh_token) localStorage.setItem('refreshToken', refresh_token);
                localStorage.setItem('user', JSON.stringify(user));

                apiClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`; // 更新 Axios 實例的預設標頭

                router.push(router.currentRoute.value.query.redirect || '/'); // 跳轉到首頁或之前想去的頁面
                return true;
            } catch (error) {
                this.status.loginError = error.response?.data?.msg || '登入失敗，請檢查帳號或密碼。';
                console.error("Login error in store:", error.response?.data || error.message);
                this.clearAuthData(); // 清除可能的無效數據
                return false;
            } finally {
                this.status.loggingIn = false;
            }
        },
        async register(payload) { // 假設 payload 是 { phone_number: '...' }
            this.status.registering = true;
            this.status.registerError = null;
            try {
                const response = await apiClient.post('/auth/register', payload);
// 快速註冊成功後，通常也會回傳 token 和 user info，可以直接登入
                const {access_token, refresh_token, user, initial_password_info} = response.data;

                this.accessToken = access_token;
                if (refresh_token) this.refreshToken = refresh_token;
                this.user = user;

                localStorage.setItem('accessToken', access_token);
                if (refresh_token) localStorage.setItem('refreshToken', refresh_token);
                localStorage.setItem('user', JSON.stringify(user));
                apiClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

                // alert(initial_password_info || "註冊成功！請記住您的初始密碼並盡快修改。"); // 提示初始密碼
                router.push('/'); // 跳轉到首頁
                return true;
            } catch (error) {
                this.status.registerError = error.response?.data?.msg || error.response?.data?.error || '快速註冊失敗。';
                console.error("Quick register error in store:", error.response?.data || error.message);
                return false;
            } finally {
                this.status.registering = false;
            }
        },
        logoutAndRedirect() {
            console.log("Executing logout and redirecting to login.");
            this.accessToken = null;
            this.refreshToken = null;
            this.user = null;
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('user');
            delete apiClient.defaults.headers.common['Authorization']; // 清除 apiClient 的預設標頭

            // 傳遞查詢參數，讓登入頁可以顯示「已登出」或「Session 過期」的訊息
            router.push({name: 'Login', query: {sessionExpired: 'true'}}).catch(err => {
                if (err.name !== 'NavigationDuplicated' && err.name !== 'NavigationCancelled') {
                    console.error("Router push error during logout:", err);
                }
            });
        },
        clearAuthData() {
            this.accessToken = null;
            this.refreshToken = null;
            this.user = null;
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('user');
            delete apiClient.defaults.headers.common['Authorization'];
        },
        async fetchCurrentUser() {
            if (!this.accessToken) { // 如果本地沒有 token，則不需要獲取
                this.clearAuthData(); // 確保狀態乾淨
                return;
            }
            this.status.loading = true; // 可以用一個通用的 loading 狀態
            try {
                const response = await apiClient.get('/auth/me'); // 使用 apiClient
                this.user = response.data.user;
                localStorage.setItem('user', JSON.stringify(this.user));
            } catch (error) {
                console.warn("Failed to fetch current user, token might be invalid/expired.", error.response || error);
                this.logoutAndRedirect(); // Token 無效，執行登出流程
            } finally {
                this.status.loading = false;
            }
        }
    },
});