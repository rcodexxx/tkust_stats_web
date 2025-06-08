import {defineStore} from 'pinia';
import {computed, reactive, ref} from 'vue';
import router from '@/router';
import apiClient from '@/services/apiClient';

export const useAuthStore = defineStore('auth', () => {
    // --- STATE ---
    const user = ref(null);
    const accessToken = ref(null);
    const refreshToken = ref(null);

    const status = reactive({
        loggingIn: false,
        loginError: null,
        registering: false,
        registerError: null,
        refreshingToken: false,
        refreshTokenError: null,
    });

    // --- GETTERS ---
    const isAuthenticated = computed(() => !!accessToken.value && !!user.value);
    const userDisplayName = computed(() => user.value?.display_name || '訪客');
    const userRole = computed(() => user.value?.role);
    const isAdmin = computed(() => userRole.value === 'admin');
    const isCoach = computed(() => userRole.value === 'coach');
    const isCadre = computed(() => userRole.value === 'cadre');

    // --- ACTIONS ---

    /**
     * 將認證數據儲存到 state 和 localStorage，並設定 axios 標頭。
     * 這現在是一個可被外部呼叫的 action。
     */
    function setAuthData(data) {
        if (!data || !data.user || !data.access_token) {
            console.error("setAuthData 失敗：傳入的數據無效。");
            return;
        }
        user.value = data.user;
        accessToken.value = data.access_token;
        if (data.refresh_token) {
            refreshToken.value = data.refresh_token;
        }
        localStorage.setItem('user', JSON.stringify(user.value));
        localStorage.setItem('accessToken', accessToken.value);
        if (refreshToken.value) {
            localStorage.setItem('refreshToken', refreshToken.value);
        }
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${accessToken.value}`;
    }

    async function login(credentials) {
        status.loggingIn = true;
        status.loginError = null;
        try {
            const response = await apiClient.post('/auth/login', credentials);
            setAuthData(response.data); // 登入成功後呼叫 setAuthData
            return true;
        } catch (error) {
            status.loginError = error.response?.data?.message || '發生未知的登入錯誤。';
            return false;
        } finally {
            status.loggingIn = false;
        }
    }

    async function register(payload) {
        status.registering = true;
        status.registerError = null;
        try {
            // 註冊 action 現在只負責發送請求，不處理登入
            // 成功時返回後端的回應數據
            const response = await apiClient.post('/auth/register', payload);
            return {success: true, data: response.data};
        } catch (error) {
            if (error.response?.data?.details) {
                const details = error.response.data.details;
                const errorMessages = Object.keys(details)
                    .map(key => `${key}: ${details[key].join(', ')}`)
                    .join('; ');
                status.registerError = `${error.response.data.message || '輸入數據有誤'}: ${errorMessages}`;
            } else {
                status.registerError = error.response?.data?.message || '註冊失敗，請稍後再試。';
            }
            return {success: false, error: status.registerError};
        } finally {
            status.registering = false;
        }
    }

    function clearAuthDataLocally() {
        user.value = null;
        accessToken.value = null;
        refreshToken.value = null;
        localStorage.removeItem('user');
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        delete apiClient.defaults.headers.common['Authorization'];
    }

    function logoutAndRedirect() {
        clearAuthDataLocally();
        router.push({name: 'Login', query: {loggedOut: 'true'}});
    }

    async function refreshTokenAction() {
        if (!refreshToken.value) {
            logoutAndRedirect();
            return null;
        }
        status.refreshingToken = true;
        status.refreshTokenError = null;
        try {
            const response = await apiClient.post('/auth/refresh');
            const newAccessToken = response.data.access_token;
            accessToken.value = newAccessToken;
            localStorage.setItem('accessToken', newAccessToken);
            apiClient.defaults.headers.common['Authorization'] = `Bearer ${newAccessToken}`;
            return newAccessToken;
        } catch (error) {
            status.refreshTokenError = "您的登入已過期，請重新登入。";
            logoutAndRedirect();
            return null;
        } finally {
            status.refreshingToken = false;
        }
    }

    function init() {
        const storedUser = localStorage.getItem('user');
        const storedToken = localStorage.getItem('accessToken');
        if (storedUser && storedToken) {
            user.value = JSON.parse(storedUser);
            accessToken.value = storedToken;
            refreshToken.value = localStorage.getItem('refreshToken');
            apiClient.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
        }
    }

    init();

    return {
        user, accessToken, refreshToken, status,
        isAuthenticated, userDisplayName, userRole, isAdmin, isCoach, isCadre,
        login,
        register,
        logoutAndRedirect,
        refreshTokenAction,
        init,
        setAuthData,
        clearLoginError: () => {
            status.loginError = null;
        },
        clearRegisterError: () => {
            status.registerError = null;
        }
    };
});
