// frontend/src/services/apiClient.js
import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 請求攔截器 - 添加調試信息
apiClient.interceptors.request.use(
  config => {
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`)

    const token = localStorage.getItem('accessToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    console.error('❌ Request Error:', error)
    return Promise.reject(error)
  }
)

// 回應攔截器 - 添加調試信息和 301 錯誤處理
apiClient.interceptors.response.use(
  response => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`)
    return response
  },
  async error => {
    const originalRequest = error.config
    const status = error.response ? error.response.status : null

    // 處理 301 重定向錯誤
    if (status === 301) {
      console.error('🔄 301 Redirect Error:', {
        url: originalRequest.url,
        baseURL: originalRequest.baseURL,
        fullURL: `${originalRequest.baseURL}${originalRequest.url}`,
        redirectLocation: error.response.headers?.location
      })

      // 如果有重定向位置，嘗試使用新 URL
      if (error.response.headers?.location) {
        const newUrl = error.response.headers.location
        console.log(`🔄 Attempting redirect to: ${newUrl}`)
        originalRequest.url = newUrl
        originalRequest.baseURL = ''
        return apiClient(originalRequest)
      }
    }

    // 原有的 401 處理邏輯
    if (status === 401 && originalRequest.url !== '/auth/refresh' && !originalRequest._retryRefresh) {
      originalRequest._retryRefresh = true
      console.warn('⚠️ Access token potentially expired (401)')

      try {
        const { useAuthStore } = await import('@/stores/authStore')
        const authStore = useAuthStore()

        const newAccessToken = await authStore.refreshTokenAction()
        if (newAccessToken) {
          console.log('🔄 Token refreshed, retrying request')
          originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`
          return apiClient(originalRequest)
        } else {
          console.warn('❌ Refresh token failed, logging out')
          return Promise.reject(error)
        }
      } catch (storeError) {
        console.error('❌ Store interaction error:', storeError)
        const { useAuthStore } = await import('@/stores/authStore')
        const authStore = useAuthStore()
        authStore.logoutAndRedirect()
        return Promise.reject(error)
      }
    }

    console.error(`❌ API Error: ${status} ${originalRequest.url}`, error)
    return Promise.reject(error)
  }
)

export default apiClient
