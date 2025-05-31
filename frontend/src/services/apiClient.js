import axios from 'axios';
// import { useAuthStore } from '@/stores/authStore'; // 避免循環依賴，如果需要 store 可以在攔截器內部獲取

const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    timeout: 10000,
});

// 請求攔截器
apiClient.interceptors.request.use(config => {
    const token = localStorage.getItem('accessToken'); // 從 localStorage 獲取 token
    // console.log("Interceptor: Retrieved token from localStorage:", token); // [除錯日誌1]
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
        // console.log("Interceptor: Authorization header set:", config.headers.Authorization); // [除錯日誌2]
    } else {
        console.log("Interceptor: No token found in localStorage."); // [除錯日誌3]
    }
    return config;
}, error => {
    return Promise.reject(error);
});

// 回應攔截器 (處理 401 等)
apiClient.interceptors.response.use(
    response => response,
    async error => {
        const originalRequest = error.config;
        const authStore = useAuthStore(); // 獲取 authStore 實例 (確保 Pinia 已初始化)

        // 檢查是否是 Access Token 過期導致的 401 錯誤
        if (error.response && error.response.status === 401 &&
            error.response.data && error.response.data.error === "token_expired" &&
            !originalRequest._retryRefresh) { // originalRequest._retryRefresh 避免無限重試刷新

            originalRequest._retryRefresh = true; // 標記已嘗試刷新
            const currentRefreshToken = authStore.refreshToken; // 從 store 或 localStorage 獲取

            if (currentRefreshToken) {
                console.log("Access token expired, attempting to refresh...");
                try {
                    // 發送請求到後端 /api/auth/refresh 端點
                    // 注意：刷新 token 的請求本身通常也需要帶上 refresh token 作為 Bearer token
                    const refreshResponse = await axios.post(
                        `${import.meta.env.VITE_API_BASE_URL}/auth/refresh`,
                        {}, // POST 通常需要 body，即使是空的
                        {headers: {'Authorization': `Bearer ${currentRefreshToken}`}}
                    );

                    const newAccessToken = refreshResponse.data.access_token;

                    // 更新 store 和 localStorage 中的 access token
                    authStore.accessToken = newAccessToken;
                    localStorage.setItem('accessToken', newAccessToken);

                    // 更新 apiClient 實例的預設標頭 (如果請求攔截器依賴它)
                    // 或者確保請求攔截器總是從 localStorage 讀取最新的 token
                    apiClient.defaults.headers.common['Authorization'] = `Bearer ${newAccessToken}`;

                    // 更新原始失敗請求的 Authorization 標頭
                    originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;

                    console.log("Access token refreshed successfully. Retrying original request.");
                    return apiClient(originalRequest); // 使用新的 access token 重試原始請求
                } catch (refreshError) {
                    console.error("Refresh token failed or also expired:", refreshError.response?.data || refreshError.message);
                    authStore.logoutAndRedirect(); // Refresh 失敗，執行登出
                    return Promise.reject(refreshError); // 或者包裝一個新的錯誤
                }
            } else {
                console.warn("No refresh token available to refresh access token.");
                authStore.logoutAndRedirect(); // 沒有 refresh token，直接登出
                return Promise.reject(error);
            }
        } else if (error.response && error.response.status === 401) {
            // 其他 401 錯誤 (例如 "Missing Authorization Header", "Invalid token")
            console.warn("Other 401 error:", error.response.data?.msg);
            authStore.logoutAndRedirect();
        }

        return Promise.reject(error); // 將其他錯誤繼續傳播
    }
);

export default apiClient;