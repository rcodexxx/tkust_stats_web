// frontend/src/services/apiClient.js
import axios from 'axios'
// import router from '@/router'; // router 的使用最好由 store action 內部處理

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000
})

// 請求攔截器
apiClient.interceptors.request.use(
  config => {
    const token = localStorage.getItem('accessToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 回應攔截器
apiClient.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config
    const status = error.response ? error.response.status : null
    const data = error.response ? error.response.data : null

    // 只處理 401 錯誤，並且避免對刷新 Token 的請求本身進行無限重試刷新
    if (
      status === 401 &&
      originalRequest.url !== '/auth/refresh' &&
      !originalRequest._retryRefresh
    ) {
      originalRequest._retryRefresh = true // 標記此原始請求已嘗試刷新
      console.warn('Axios Interceptor: Access token potentially expired or invalid (401).')

      // 動態匯入 store 以調用 action
      try {
        const { useAuthStore } = await import('@/stores/authStore')
        const authStore = useAuthStore()

        const newAccessToken = await authStore.refreshTokenAction() // 嘗試刷新 token
        if (newAccessToken) {
          console.log('Axios Interceptor: Token refreshed. Retrying original request.')
          originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`
          return apiClient(originalRequest) // 使用 apiClient 重試
        } else {
          // Refresh token 失敗或沒有 refresh token，authStore.refreshTokenAction 內部應已處理登出
          // 此處可以 reject 原始錯誤，或者 authStore.logoutAndRedirect() 已導航
          console.warn(
            'Axios Interceptor: Refresh token failed or not available. Logout should have been triggered.'
          )
          return Promise.reject(error) // 繼續拋出原始錯誤，讓調用方知道
        }
      } catch (storeError) {
        console.error(
          'Axios Interceptor: Error during store interaction or refresh attempt.',
          storeError
        )
        // 確保即使 store 操作失敗也執行登出
        const { useAuthStore } = await import('@/stores/authStore')
        const authStore = useAuthStore()
        authStore.logoutAndRedirect() // 確保執行登出
        return Promise.reject(error)
      }
    }
    // 對於其他錯誤，或者已經重試過刷新的 401，直接拋出
    return Promise.reject(error)
  }
)

export default apiClient
