import { defineStore } from 'pinia'
import { computed, reactive, ref } from 'vue'
import router from '@/router'
import apiClient from '@/services/apiClient'

export const useAuthStore = defineStore('auth', () => {
  // --- STATE ---
  const user = ref(null)
  const accessToken = ref(null)
  const refreshToken = ref(null)

  const status = reactive({
    loggingIn: false,
    loginError: null,
    registering: false,
    registerError: null,
    refreshingToken: false,
    refreshTokenError: null,
    fetchingUser: false,
    fetchUserError: null
  })

  // --- GETTERS ---
  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)
  const userDisplayName = computed(() => user.value?.display_name || '訪客')
  const userRole = computed(() => user.value?.role)
  const isAdmin = computed(() => userRole.value === 'admin')
  const isCoach = computed(() => userRole.value === 'coach')
  const isCadre = computed(() => userRole.value === 'cadre')

  // --- ACTIONS ---

  /**
   * 將認證數據儲存到 state 和 localStorage，並設定 axios 標頭。
   */
  function setAuthData(data) {
    if (!data || !data.user || !data.access_token) {
      console.error('setAuthData 失敗：傳入的數據無效。')
      return
    }
    user.value = data.user
    accessToken.value = data.access_token
    if (data.refresh_token) {
      refreshToken.value = data.refresh_token
    }
    localStorage.setItem('user', JSON.stringify(user.value))
    localStorage.setItem('accessToken', accessToken.value)
    if (refreshToken.value) {
      localStorage.setItem('refreshToken', refreshToken.value)
    }
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${accessToken.value}`
  }

  /**
   * 登入
   */
  async function login(credentials) {
    status.loggingIn = true
    status.loginError = null
    try {
      const response = await apiClient.post('/auth/login', credentials)
      setAuthData(response.data)
      return true
    } catch (error) {
      status.loginError = error.response?.data?.message || '發生未知的登入錯誤。'
      return false
    } finally {
      status.loggingIn = false
    }
  }

  /**
   * 註冊
   */
  async function register(payload) {
    status.registering = true
    status.registerError = null
    try {
      const response = await apiClient.post('/auth/register', payload)
      return { success: true, data: response.data }
    } catch (error) {
      if (error.response?.data?.details) {
        const details = error.response.data.details
        const errorMessages = Object.keys(details)
          .map(key => `${key}: ${details[key].join(', ')}`)
          .join('; ')
        status.registerError = `${error.response.data.message || '輸入數據有誤'}: ${errorMessages}`
      } else {
        status.registerError = error.response?.data?.message || '註冊失敗，請稍後再試。'
      }
      return { success: false, error: status.registerError }
    } finally {
      status.registering = false
    }
  }

  /**
   * 獲取當前使用者資料
   */
  async function fetchCurrentUser() {
    if (!accessToken.value) {
      return null
    }

    status.fetchingUser = true
    status.fetchUserError = null

    try {
      const response = await apiClient.get('/auth/me') // 假設有這個端點
      if (response.data) {
        user.value = response.data
        localStorage.setItem('user', JSON.stringify(user.value))
      }
      return user.value
    } catch (error) {
      status.fetchUserError = error.response?.data?.message || '無法獲取使用者資料'
      // 如果是 401 錯誤，可能需要刷新 token 或登出
      if (error.response?.status === 401) {
        const newToken = await refreshTokenAction()
        if (newToken) {
          // 重試一次
          try {
            const retryResponse = await apiClient.get('/auth/me')
            user.value = retryResponse.data
            localStorage.setItem('user', JSON.stringify(user.value))
            return user.value
          } catch (_retryError) {
            logoutAndRedirect()
          }
        }
      }
      return null
    } finally {
      status.fetchingUser = false
    }
  }

  /**
   * 清除本地認證資料
   */
  function clearAuthDataLocally() {
    user.value = null
    accessToken.value = null
    refreshToken.value = null
    localStorage.removeItem('user')
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
    delete apiClient.defaults.headers.common['Authorization']
  }

  /**
   * 登出並重定向
   */
  function logoutAndRedirect() {
    clearAuthDataLocally()
    router.push({ name: 'Login', query: { loggedOut: 'true' } })
  }

  /**
   * 刷新 Token
   */
  async function refreshTokenAction() {
    if (!refreshToken.value) {
      logoutAndRedirect()
      return null
    }

    status.refreshingToken = true
    status.refreshTokenError = null

    try {
      const response = await apiClient.post('/auth/refresh', {
        refresh_token: refreshToken.value // 可能需要在 body 中傳送 refresh token
      })
      const newAccessToken = response.data.access_token
      accessToken.value = newAccessToken
      localStorage.setItem('accessToken', newAccessToken)
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${newAccessToken}`

      // 如果後端也返回新的 refresh token
      if (response.data.refresh_token) {
        refreshToken.value = response.data.refresh_token
        localStorage.setItem('refreshToken', refreshToken.value)
      }

      return newAccessToken
    } catch (_error) {
      status.refreshTokenError = '您的登入已過期，請重新登入。'
      logoutAndRedirect()
      return null
    } finally {
      status.refreshingToken = false
    }
  }

  /**
   * 初始化（從 localStorage 恢復狀態）
   */
  function init() {
    const storedUser = localStorage.getItem('user')
    const storedToken = localStorage.getItem('accessToken')
    const storedRefreshToken = localStorage.getItem('refreshToken')

    if (storedUser && storedToken) {
      try {
        user.value = JSON.parse(storedUser)
        accessToken.value = storedToken
        refreshToken.value = storedRefreshToken
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`
      } catch (error) {
        console.error('無法解析儲存的使用者資料:', error)
        clearAuthDataLocally()
      }
    }
  }

  // 初始化
  init()

  return {
    // State
    user,
    accessToken,
    refreshToken,
    status,

    // Getters
    isAuthenticated,
    userDisplayName,
    userRole,
    isAdmin,
    isCoach,
    isCadre,

    // Actions
    login,
    register,
    fetchCurrentUser,
    logoutAndRedirect,
    refreshTokenAction,
    setAuthData,
    clearAuthDataLocally,
    init,

    // Error clearing methods
    clearLoginError: () => {
      status.loginError = null
    },
    clearRegisterError: () => {
      status.registerError = null
    },
    clearFetchUserError: () => {
      status.fetchUserError = null
    }
  }
})
