// frontend/src/stores/authStore.js
import {defineStore} from 'pinia';

import apiClient from '@/services/apiClient';
import router from '@/router';

export const useAuthStore = defineStore('auth', {
    state: () => ({
        accessToken: localStorage.getItem('accessToken') || null,
        refreshToken: localStorage.getItem('refreshToken') || null,
        user: JSON.parse(localStorage.getItem('user')) || null,
        status: {
            loggingIn: false, loginError: null,
            registering: false, registerError: null,
            refreshingToken: false, refreshTokenError: null, // 新增刷新狀態
            fetchingUser: false, fetchUserError: null,     // 新增獲取使用者狀態
        },
    }),
    getters: {
        isAuthenticated: (state) => !!state.accessToken,
        currentUser: (state) => state.user,
        userRole: (state) => state.user?.role,
        userDisplayName: (state) => { /* ... (與之前相同) ... */
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
                const response = await apiClient.post('/auth/login', credentials);
                const {access_token, refresh_token, user} = response.data;

                this.accessToken = access_token;
                if (refresh_token) this.refreshToken = refresh_token;
                this.user = user;

                localStorage.setItem('accessToken', access_token);
                if (refresh_token) localStorage.setItem('refreshToken', refresh_token);
                localStorage.setItem('user', JSON.stringify(user));

                // apiClient 的請求攔截器會自動處理後續請求的 Authorization 標頭

                router.push(router.currentRoute.value.query.redirect || '/');
                return true;
            } catch (error) {
                this.status.loginError = error.response?.data?.msg || '登入失敗，請檢查帳號或密碼。';
                console.error("Login error in store:", error.response?.data || error.message);
                this.clearAuthDataLocally(); // 只清除本地，不觸發跳轉，讓攔截器或調用方處理
                return false;
            } finally {
                this.status.loggingIn = false;
            }
        },

        clearRegisterError() {
            this.status.registerError = null;
        },

        // 假設這個 register action 是用於「快速註冊」
        async register(payload) { // payload 應為 { phone_number: '...' }
            this.status.registering = true;
            this.status.registerError = null;
            try {
                // 確認 API 端點是否與後端匹配 (例如 /auth/quick_register)
                const response = await apiClient.post('/auth/register', payload);
                const {access_token, refresh_token, user, initial_password_info} = response.data;

                this.accessToken = access_token;
                if (refresh_token) this.refreshToken = refresh_token;
                this.user = user;

                localStorage.setItem('accessToken', access_token);
                if (refresh_token) localStorage.setItem('refreshToken', refresh_token);
                localStorage.setItem('user', JSON.stringify(user));

                alert(initial_password_info || "註冊成功！請記住您的初始密碼並盡快修改。");
                router.push('/');
                return true;
            } catch (error) {
                this.status.registerError = error.response?.data?.msg || error.response?.data?.error || '快速註冊失敗。';
                console.error("Register error in store:", error.response?.data || error.message);
                return false;
            } finally {
                this.status.registering = false;
            }
        },

        logoutAndRedirect() {
            console.log("AuthStore: Executing logout and redirecting to login.");
            this.clearAuthDataLocally();
            router.push({name: 'Login', query: {sessionExpired: 'true'}}).catch(err => {
                if (err.name !== 'NavigationDuplicated' && err.name !== 'NavigationCancelled') {
                    console.error("Router push error during logout:", err);
                }
            });
        },

        clearAuthDataLocally() { // 只清除本地數據，不進行路由跳轉
            this.accessToken = null;
            this.refreshToken = null;
            this.user = null;
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('user');
            // 不需要手動 delete apiClient.defaults.headers.common['Authorization']
            // 因為請求攔截器每次都會從 localStorage 讀取
        },

        async refreshTokenAction() { // 新增的刷新 Token action
            if (!this.refreshToken) {
                console.warn("AuthStore: No refresh token available for refreshing.");
                this.logoutAndRedirect(); // 沒有 refresh token，直接登出
                return null;
            }
            this.status.refreshingToken = true;
            this.status.refreshTokenError = null;
            try {
                // 刷新 Token 的請求本身也需要帶上 Refresh Token
                // 注意：這個請求不應該被上面的401攔截器再次攔截並嘗試刷新，
                // 所以 apiClient 中的攔截器需要有 originalRequest.url !== '/auth/refresh' 的判斷
                const refreshResponse = await apiClient.post('/auth/refresh', {}, {
                    // 如果 apiClient 的請求攔截器已經能正確處理，則不需要手動加標頭
                    // 否則，需要一個不帶攔截器的 axios 實例，或者確保此請求被特殊處理
                    // headers: { 'Authorization': `Bearer ${this.refreshToken}` } // 通常攔截器會處理
                });

                const newAccessToken = refreshResponse.data.access_token;
                this.accessToken = newAccessToken;
                localStorage.setItem('accessToken', newAccessToken);
                console.log("AuthStore: Access token refreshed via refreshTokenAction.");
                return newAccessToken;
            } catch (error) {
                console.error("AuthStore: Refresh token action failed.", error.response?.data || error.message);
                this.status.refreshTokenError = error.response?.data?.msg || "刷新憑證失敗，請重新登入。";
                this.logoutAndRedirect(); // 刷新失敗，登出
                return null;
            } finally {
                this.status.refreshingToken = false;
            }
        },

        async fetchCurrentUser() {
            if (!this.accessToken) {
                this.clearAuthDataLocally();
                return;
            }
            this.status.fetchingUser = true;
            this.status.fetchUserError = null;
            try {
                const response = await apiClient.get('/auth/me');
                if (response.data && response.data.user) {
                    this.user = response.data.user;
                    localStorage.setItem('user', JSON.stringify(this.user));
                } else {
                    throw new Error("User data not found in /auth/me response");
                }
            } catch (error) {
                console.warn("AuthStore: Failed to fetch current user.", error.response || error.message);
                this.status.fetchUserError = "獲取使用者資訊失敗。";
                // 攔截器應該已經處理了 401 並觸發登出
                // 如果是其他錯誤，不一定需要立即登出，但 token 可能已失效
                // if (error.response && error.response.status !== 401) {
                //   // Maybe do nothing here, let user retry or see an error
                // }
            } finally {
                this.status.fetchingUser = false;
            }
        }
    },
});