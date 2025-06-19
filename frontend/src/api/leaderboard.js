// frontend/src/api/leaderboard.js
import apiClient from '../services/apiClient'

/**
 * 排行榜 API 模組
 */
export const leaderboardAPI = {
  /**
   * 獲取排行榜數據 (推薦使用新 API)
   * @param {Object} params - 查詢參數
   * @param {boolean} [params.include_guests=true] - 是否包含訪客
   * @param {number} [params.limit=50] - 返回數量限制
   * @param {number} [params.organization_id] - 組織ID篩選
   * @param {string} [params.experience_level] - 經驗等級篩選
   * @param {number} [params.min_matches] - 最少比賽場次
   * @returns {Promise<AxiosResponse>}
   */
  async getLeaderboard(params = {}) {
    const defaultParams = {
      include_guests: true,
      limit: 50,
      ...params
    }

    try {
      // 優先使用新的專用排行榜 API
      console.log('🏆 Using new leaderboard API:', '/leaderboard')
      const response = await apiClient.get('/leaderboard', {
        params: defaultParams
      })

      // 檢查新 API 的回應格式
      if (response.data && response.data.data && Array.isArray(response.data.data)) {
        return {
          ...response,
          data: response.data.data,
          total: response.data.total,
          statistics: response.data.statistics
        }
      } else if (response.data && Array.isArray(response.data)) {
        return response
      } else {
        throw new Error('Unexpected response format from new leaderboard API')
      }
    } catch (newApiError) {
      console.warn('⚠️ New leaderboard API failed, falling back to legacy API:', newApiError.message)

      // 回退到舊的 API 端點
      return this.getLegacyLeaderboard(defaultParams)
    }
  },

  /**
   * 向後兼容的排行榜 API (舊版本)
   * @param {Object} params - 查詢參數
   * @returns {Promise<AxiosResponse>}
   */
  async getLegacyLeaderboard(params = {}) {
    console.log('🔄 Using legacy leaderboard API:', '/members?view=leaderboard')

    const legacyParams = {
      view: 'leaderboard',
      limit: params.limit || 50,
      ...params
    }

    return apiClient.get('/members', { params: legacyParams })
  },

  /**
   * 比較兩位球員
   * @param {number} playerId1 - 球員1 ID
   * @param {number} playerId2 - 球員2 ID
   * @returns {Promise<AxiosResponse>}
   */
  async comparePlayers(playerId1, playerId2) {
    try {
      // 嘗試新的比較端點
      return await apiClient.get(`/members/leaderboard/compare/${playerId1}/${playerId2}`)
    } catch (error) {
      // 回退到舊的比較端點
      console.warn('Using legacy compare endpoint')
      return await apiClient.get(`/members/${playerId1}/compare/${playerId2}`)
    }
  },

  /**
   * 獲取排行榜統計信息
   * @returns {Promise<AxiosResponse>}
   */
  async getStatistics() {
    try {
      return await apiClient.get('/members/leaderboard/statistics')
    } catch (error) {
      console.warn('Statistics endpoint not available:', error.message)
      return { data: null }
    }
  },

  /**
   * 獲取單一球員詳細資料
   * @param {number} memberId - 球員 ID
   * @returns {Promise<AxiosResponse>}
   */
  async getMemberDetail(memberId) {
    return apiClient.get(`/members/${memberId}`)
  },

  /**
   * 獲取球員比賽記錄
   * @param {number} playerId - 球員 ID
   * @param {number} [limit=10] - 記錄數量限制
   * @returns {Promise<AxiosResponse>}
   */
  async getPlayerMatches(playerId, limit = 10) {
    try {
      return await apiClient.get('/matches', {
        params: { player_id: playerId, limit }
      })
    } catch (error) {
      // 嘗試替代端點
      try {
        return await apiClient.get('/games', {
          params: { player_id: playerId, limit }
        })
      } catch (secondError) {
        console.warn('Both match endpoints failed:', error.message, secondError.message)
        return { data: [] }
      }
    }
  }
}

// 預設匯出
export default leaderboardAPI
