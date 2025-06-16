<template>
  <div class="home-leaderboard-page">
    <div class="leaderboard-content-wrapper">
      <!-- 頁面標題 -->
      <div class="leaderboard-header mb-4">
        <h1 class="page-title">🏆 軟式網球排行榜</h1>
        <div class="leaderboard-description">
          <!--          <n-text depth="3" style="font-size: 16px"> 基於 TrueSkill 評分系統的球員實力排名 </n-text>-->
        </div>
      </div>

      <n-spin :show="loading" size="large">
        <template #description>載入排行榜中...</template>

        <!-- 錯誤提示 -->
        <div v-if="!loading && error" class="mt-4">
          <n-alert title="載入失敗" type="error" show-icon>
            {{ error }}
          </n-alert>
        </div>

        <!-- 排行榜統計摘要 (桌面版顯示) -->
        <div v-if="!loading && !error && hasValidStats" class="stats-summary mb-4 desktop-only">
          <n-card size="small" class="stats-card">
            <div class="stats-row">
              <div class="stat-item">
                <n-statistic label="總球員數" :value="safeGet(systemStats, 'basic.total_active_players', 0)" />
              </div>
              <div class="stat-item">
                <n-statistic
                  label="平均分數"
                  :value="formatDisplayScore(safeGet(systemStats, 'basic.average_conservative_score', 0))"
                  suffix="分"
                />
              </div>
              <div class="stat-item">
                <n-statistic
                  label="最高分數"
                  :value="formatDisplayScore(safeGet(systemStats, 'basic.score_range.max', 0))"
                  suffix="分"
                />
              </div>
            </div>
          </n-card>
        </div>

        <!-- 空狀態 -->
        <div v-if="!loading && !error">
          <n-empty v-if="displayMembers.length === 0" description="目前尚無排行榜資料" class="py-5" size="huge" />

          <!-- 排行榜列表 -->
          <div v-if="displayMembers.length > 0" class="home-leaderboard-list">
            <!-- F1頒獎台風格 (桌面版) -->
            <div class="f1-podium-desktop desktop-only mb-4">
              <div class="podium-container">
                <!-- 第二名 (左邊) -->
                <div v-if="topThree[1]" class="podium-position position-2">
                  <div class="podium-card rank-2">
                    <div class="rank-icon">
                      <n-icon :component="getRankIconComponent(2)" :size="35" :color="getRankIconColor(2)" />
                    </div>
                    <div class="player-info">
                      <div class="player-name">{{ getPlayerDisplayName(topThree[1]) }}</div>
                      <div v-if="topThree[1].organization_name" class="player-org">
                        {{ topThree[1].organization_name }}
                      </div>
                      <div class="experience-badge">
                        <n-tag
                          :type="getExperienceTagType(safeGet(topThree[1], 'experience_level', '未知'))"
                          size="small"
                        >
                          {{ safeGet(topThree[1], 'experience_level', '未知') }}
                        </n-tag>
                      </div>
                    </div>
                    <div class="score-display">
                      <div class="score-number">
                        {{ formatDisplayScore(safeGet(topThree[1], 'official_rank_score', 0)) }}
                      </div>
                      <div class="score-label">分</div>
                    </div>
                    <div class="match-count">{{ getMatchCount(topThree[1]) }} 場比賽</div>
                  </div>
                </div>

                <!-- 第一名 (中間，最高) -->
                <div v-if="topThree[0]" class="podium-position position-1">
                  <div class="podium-card rank-1">
                    <div class="crown-icon">👑</div>
                    <div class="rank-icon">
                      <n-icon :component="getRankIconComponent(1)" :size="45" :color="getRankIconColor(1)" />
                    </div>
                    <div class="player-info">
                      <div class="player-name">{{ getPlayerDisplayName(topThree[0]) }}</div>
                      <div v-if="topThree[0].organization_name" class="player-org">
                        {{ topThree[0].organization_name }}
                      </div>
                      <div class="experience-badge">
                        <n-tag
                          :type="getExperienceTagType(safeGet(topThree[0], 'experience_level', '未知'))"
                          size="small"
                        >
                          {{ safeGet(topThree[0], 'experience_level', '未知') }}
                        </n-tag>
                      </div>
                    </div>
                    <div class="score-display">
                      <div class="score-number">
                        {{ formatDisplayScore(safeGet(topThree[0], 'official_rank_score', 0)) }}
                      </div>
                      <div class="score-label">分</div>
                    </div>
                    <div class="match-count">{{ getMatchCount(topThree[0]) }} 場比賽</div>
                  </div>
                </div>

                <!-- 第三名 (右邊) -->
                <div v-if="topThree[2]" class="podium-position position-3">
                  <div class="podium-card rank-3">
                    <div class="rank-icon">
                      <n-icon :component="getRankIconComponent(3)" :size="35" :color="getRankIconColor(3)" />
                    </div>
                    <div class="player-info">
                      <div class="player-name">{{ getPlayerDisplayName(topThree[2]) }}</div>
                      <div v-if="topThree[2].organization_name" class="player-org">
                        {{ topThree[2].organization_name }}
                      </div>
                      <div class="experience-badge">
                        <n-tag
                          :type="getExperienceTagType(safeGet(topThree[2], 'experience_level', '未知'))"
                          size="small"
                        >
                          {{ safeGet(topThree[2], 'experience_level', '未知') }}
                        </n-tag>
                      </div>
                    </div>
                    <div class="score-display">
                      <div class="score-number">
                        {{ formatDisplayScore(safeGet(topThree[2], 'official_rank_score', 0)) }}
                      </div>
                      <div class="score-label">分</div>
                    </div>
                    <div class="match-count">{{ getMatchCount(topThree[2]) }} 場比賽</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 手機版前三名簡潔顯示 -->
            <div class="mobile-top-three mobile-only mb-4">
              <div v-for="(member, index) in topThree" :key="member.id" class="mobile-rank-card">
                <div class="mobile-rank-content">
                  <div class="rank-icon-mobile">
                    <n-icon
                      :component="getRankIconComponent(index + 1)"
                      :size="24"
                      :color="getRankIconColor(index + 1)"
                    />
                  </div>
                  <div class="player-name-mobile">{{ getPlayerDisplayName(member) }}</div>
                  <div class="score-mobile">{{ formatDisplayScore(safeGet(member, 'official_rank_score', 0)) }}分</div>
                  <div class="matches-mobile">{{ getMatchCount(member) }}場</div>
                </div>
              </div>
            </div>

            <!-- 其他排名 -->
            <div v-if="otherRanks.length > 0" class="other-ranks">
              <h3 class="section-title">第 4 - {{ Math.min(displayMembers.length, 20) }} 名</h3>

              <!-- 桌面版列表 -->
              <n-list class="ranking-list desktop-only">
                <n-list-item v-for="member in otherRanks" :key="member.id">
                  <div class="rank-item">
                    <div class="rank-number">{{ member.rank }}</div>

                    <div class="player-section">
                      <div class="player-name">{{ getPlayerDisplayName(member) }}</div>
                      <div class="player-details">
                        <span v-if="member.organization_name" class="org-name">
                          {{ member.organization_name }}
                        </span>
                        <n-tag :type="getExperienceTagType(safeGet(member, 'experience_level', '未知'))" size="tiny">
                          {{ safeGet(member, 'experience_level', '未知') }}
                        </n-tag>
                      </div>
                    </div>

                    <div class="score-section">
                      <div class="score-main">
                        {{ formatDisplayScore(safeGet(member, 'official_rank_score', 0)) }} 分
                      </div>
                      <div class="match-info">{{ getMatchCount(member) }} 場</div>
                    </div>
                  </div>
                </n-list-item>
              </n-list>

              <!-- 手機版簡潔卡片 -->
              <div class="mobile-rank-list mobile-only">
                <div v-for="member in otherRanks" :key="member.id" class="mobile-rank-card">
                  <div class="mobile-rank-content">
                    <div class="rank-number-mobile">{{ member.rank }}</div>
                    <div class="player-name-mobile">{{ getPlayerDisplayName(member) }}</div>
                    <div class="score-mobile">
                      {{ formatDisplayScore(safeGet(member, 'official_rank_score', 0)) }}分
                    </div>
                    <div class="matches-mobile">{{ getMatchCount(member) }}場</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 查看更多提示 -->
            <div v-if="displayMembers.length >= 20" class="view-more-hint">
              <n-card class="hint-card">
                <div class="hint-content">
                  <n-icon :component="InfoIcon" size="20" color="#6366f1" />
                  <span>想查看完整排行榜和詳細統計？</span>
                  <n-button type="primary" size="small" @click="goToDetailedRanking"> 前往詳細排行榜 </n-button>
                </div>
              </n-card>
            </div>
          </div>
        </div>
      </n-spin>
    </div>
  </div>
</template>

<script setup>
  import { computed, onMounted, ref } from 'vue'
  import { useRouter } from 'vue-router'
  import apiClient from '@/services/apiClient.js'
  import { NAlert, NButton, NCard, NEmpty, NIcon, NList, NListItem, NSpin, NStatistic, NTag, NText } from 'naive-ui'
  import { Medal as Rank3Icon, ShieldSharp as Rank2Icon, TrophySharp as Rank1Icon } from '@vicons/ionicons5'
  import { InformationCircleIcon as InfoIcon } from '@heroicons/vue/24/outline'

  const router = useRouter()

  // 響應式數據
  const leaderboardData = ref([])
  const systemStats = ref(null)
  const loading = ref(true)
  const error = ref(null)

  // === 安全訪問和格式化函數 ===
  const safeGet = (obj, path, defaultValue = undefined) => {
    if (!obj || typeof obj !== 'object') return defaultValue

    const keys = path.split('.')
    let current = obj

    for (const key of keys) {
      if (current === null || current === undefined || !(key in current)) {
        return defaultValue
      }
      current = current[key]
    }

    return current !== undefined ? current : defaultValue
  }

  // 格式化顯示分數 (x100)
  const formatDisplayScore = score => {
    if (typeof score !== 'number' || isNaN(score)) return '0'
    return Math.round(score * 100).toString()
  }

  // 獲取球員顯示名稱
  const getPlayerDisplayName = member => {
    return safeGet(member, 'display_name') || safeGet(member, 'name', '未知球員')
  }

  // 獲取比賽場數 (檢查多個可能的字段名稱)
  const getMatchCount = member => {
    const totalMatches = safeGet(member, 'total_matches', 0)

    // 調試：顯示實際的 total_matches 值
    if (process.env.NODE_ENV === 'development' && member) {
      console.log(
        `Player: ${getPlayerDisplayName(member)}, total_matches: ${totalMatches}, type: ${typeof totalMatches}`
      )
    }

    return (
      totalMatches ||
      safeGet(member, 'matches_played', 0) ||
      safeGet(member, 'match_count', 0) ||
      safeGet(member, 'games_played', 0) ||
      safeGet(member, 'total_games', 0) ||
      safeGet(member, 'matches', 0) ||
      safeGet(member, 'games', 0) ||
      0
    )
  }

  // === 計算屬性 ===
  const hasValidStats = computed(() => {
    return (
      systemStats.value && typeof systemStats.value === 'object' && safeGet(systemStats.value, 'basic') !== undefined
    )
  })

  // 顯示的球員（前20名）
  const displayMembers = computed(() => {
    return leaderboardData.value.slice(0, 20)
  })

  // 前三名
  const topThree = computed(() => {
    return displayMembers.value.slice(0, 3)
  })

  // 其他排名（第4-20名）
  const otherRanks = computed(() => {
    return displayMembers.value.slice(3)
  })

  // === 獲取排行榜數據 ===
  const fetchLeaderboard = async () => {
    loading.value = true
    error.value = null

    try {
      // 固定參數：只顯示正式會員，前20名
      const params = new URLSearchParams({
        include_guests: false,
        limit: 20
      })

      let response
      let data

      try {
        response = await apiClient.get(`/members/leaderboard?${params}`)
        data = response.data

        if (data && Array.isArray(data.data)) {
          leaderboardData.value = data.data.map((member, index) => ({
            ...member,
            rank: index + 1,
            // 確保必要屬性存在
            official_rank_score: safeGet(member, 'official_rank_score', 0),
            experience_level: safeGet(member, 'experience_level', '未知'),
            organization_name: safeGet(member, 'organization_name', '')
          }))

          systemStats.value = safeGet(data, 'statistics', null)
        } else {
          throw new Error('API 回應格式不正確')
        }
      } catch (newApiError) {
        console.warn('新 API 失敗，使用備用方案:', newApiError.message)

        // 備用：舊 API
        response = await apiClient.get('/members', {
          params: { view: 'leaderboard' }
        })

        if (response && Array.isArray(response.data)) {
          const membersOnly = response.data.filter(member => !safeGet(member, 'is_guest', false)).slice(0, 20)

          leaderboardData.value = membersOnly.map((member, index) => ({
            ...member,
            rank: index + 1,
            official_rank_score: safeGet(member, 'score', 0) || safeGet(member, 'conservative_score', 0),
            experience_level: safeGet(member, 'experience_level', '未知'),
            organization_name: safeGet(member, 'organization_name', '')
          }))

          systemStats.value = null
        } else {
          throw new Error('無法獲取排行榜數據')
        }
      }
    } catch (e) {
      error.value = e.response?.data?.message || e.message || '載入排行榜時發生錯誤，請稍後再試'
      console.error('排行榜 API 錯誤:', e)
      leaderboardData.value = []
      systemStats.value = null
    } finally {
      loading.value = false
    }
  }

  // UI 函數
  function getRankIconComponent(rank) {
    if (rank === 1) return Rank1Icon
    if (rank === 2) return Rank2Icon
    if (rank === 3) return Rank3Icon
    return null
  }

  function getRankIconColor(rank) {
    if (rank === 1) return '#FFD700'
    if (rank === 2) return '#C0C0C0'
    if (rank === 3) return '#CD7F32'
    return undefined
  }

  function getExperienceTagType(experienceLevel) {
    const typeMap = {
      新手: 'default',
      初級: 'info',
      中級: 'warning',
      高級: 'success',
      資深: 'error'
    }
    return typeMap[experienceLevel] || 'default'
  }

  function goToDetailedRanking() {
    router.push('/leaderboard/detailed')
  }

  // 生命週期
  onMounted(fetchLeaderboard)
</script>

<style scoped>
  .home-leaderboard-page {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    padding: 2rem 1rem;
  }

  .leaderboard-content-wrapper {
    max-width: 1000px;
    margin: 0 auto;
    background: white;
    border-radius: 20px;
    padding: 2rem;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
  }

  .page-title {
    margin: 0 0 0.5rem 0;
    font-size: 2.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
  }

  .leaderboard-description {
    text-align: center;
    margin-bottom: 2rem;
    color: #6b7280;
  }

  /* 統計摘要 */
  .stats-summary {
    margin-bottom: 2rem;
  }

  .stats-card {
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  }

  .stats-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 2rem;
    text-align: center;
  }

  /* F1頒獎台風格 (桌面版) */
  .f1-podium-desktop {
    perspective: 1000px;
  }

  .podium-container {
    display: flex;
    justify-content: center;
    align-items: flex-end;
    gap: 0;
    padding: 2rem 0;
    position: relative;
  }

  /* 統一底座 */
  .podium-container::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 90%;
    height: 40px;
    background: linear-gradient(135deg, #e2e8f0, #cbd5e1);
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    z-index: 0;
  }

  .podium-position {
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    z-index: 1;
  }

  .position-1 {
    order: 2;
    transform: scale(1.1) translateY(-20px);
  }

  .position-2 {
    order: 1;
    transform: translateY(-10px);
  }

  .position-3 {
    order: 3;
    transform: translateY(-10px);
  }

  .podium-card {
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    border: 2px solid transparent;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
    width: 260px;
    z-index: 2;
  }

  .rank-1 {
    background: linear-gradient(135deg, #ffd700, #ffed4e);
    border: 3px solid #ffd700;
    box-shadow: 0 12px 40px rgba(255, 215, 0, 0.3);
  }

  .rank-2 {
    background: linear-gradient(135deg, #c0c0c0, #e5e5e5);
    border: 3px solid #c0c0c0;
    box-shadow: 0 10px 30px rgba(192, 192, 192, 0.3);
  }

  .rank-3 {
    background: linear-gradient(135deg, #cd7f32, #daa447);
    border: 3px solid #cd7f32;
    box-shadow: 0 8px 25px rgba(205, 127, 50, 0.3);
  }

  .crown-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
    animation: bounce 2s infinite;
  }

  @keyframes bounce {
    0%,
    20%,
    50%,
    80%,
    100% {
      transform: translateY(0);
    }
    40% {
      transform: translateY(-10px);
    }
    60% {
      transform: translateY(-5px);
    }
  }

  .podium-card:hover {
    transform: translateY(-4px);
  }

  .rank-icon {
    margin-bottom: 1rem;
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .rank-icon .n-icon {
    background: white;
    border-radius: 50%;
    padding: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .player-info {
    margin-bottom: 1rem;
  }

  .player-name {
    font-size: 1.25rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 0.25rem;
  }

  .player-org {
    font-size: 0.875rem;
    color: #64748b;
    margin-bottom: 0.5rem;
  }

  .experience-badge {
    margin-bottom: 1rem;
  }

  .score-display {
    margin-bottom: 0.75rem;
  }

  .score-number {
    font-size: 2rem;
    font-weight: 800;
    color: #1e293b;
    line-height: 1;
  }

  .score-label {
    font-size: 0.875rem;
    color: #64748b;
    font-weight: 500;
  }

  .match-count {
    font-size: 0.875rem;
    color: #64748b;
    font-weight: 500;
  }

  /* 手機版簡潔卡片 */
  .mobile-top-three,
  .mobile-rank-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .mobile-rank-card {
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    border: 1px solid #e2e8f0;
    transition: all 0.2s ease;
    width: 100%;
  }

  /* 前三名手機版卡片顏色 */
  .mobile-top-three .mobile-rank-card:nth-child(1) {
    background: linear-gradient(135deg, #ffd700, #ffed4e);
    border: 2px solid #ffd700;
  }

  .mobile-top-three .mobile-rank-card:nth-child(2) {
    background: linear-gradient(135deg, #c0c0c0, #e5e5e5);
    border: 2px solid #c0c0c0;
  }

  .mobile-top-three .mobile-rank-card:nth-child(3) {
    background: linear-gradient(135deg, #cd7f32, #daa447);
    border: 2px solid #cd7f32;
  }

  /* 第四名之後白色背景 */
  .mobile-rank-list .mobile-rank-card {
    background: white;
  }

  .mobile-rank-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .mobile-rank-content {
    display: grid;
    grid-template-columns: 50px 1fr auto auto;
    gap: 1rem;
    align-items: center;
    padding: 1rem 1.5rem;
  }

  .rank-icon-mobile {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .rank-icon-mobile .n-icon {
    background: white;
    border-radius: 50%;
    padding: 6px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .rank-number-mobile {
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.125rem;
    font-weight: 600;
    color: #64748b;
    background: white;
    border-radius: 50%;
    width: 32px;
    height: 32px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    margin: 0 auto;
  }

  .player-name-mobile {
    font-size: 1rem;
    font-weight: 600;
    color: #1e293b;
    text-align: left;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .score-mobile {
    font-size: 1rem;
    font-weight: 700;
    color: #1e293b;
    text-align: right;
    min-width: 60px;
  }

  .matches-mobile {
    font-size: 0.875rem;
    color: #64748b;
    text-align: right;
    min-width: 50px;
  }

  /* 其他排名 */
  .other-ranks {
    margin-bottom: 2rem;
  }

  .section-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #374151;
    margin-bottom: 1rem;
    text-align: center;
  }

  .ranking-list {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  }

  .rank-item {
    display: grid;
    grid-template-columns: 60px 1fr auto;
    gap: 1rem;
    align-items: center;
    padding: 1rem 1.5rem;
    background: white;
    border-bottom: 1px solid #f1f5f9;
    transition: all 0.2s ease;
  }

  .rank-item:hover {
    background: #f8fafc;
  }

  .rank-item:last-child {
    border-bottom: none;
  }

  .rank-number {
    font-size: 1.125rem;
    font-weight: 600;
    color: #64748b;
    text-align: center;
  }

  .player-section {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .player-section .player-name {
    font-size: 1rem;
    font-weight: 600;
    color: #1e293b;
  }

  .player-details {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .org-name {
    font-size: 0.875rem;
    color: #64748b;
  }

  .score-section {
    text-align: right;
  }

  .score-main {
    font-size: 1.125rem;
    font-weight: 700;
    color: #1e293b;
  }

  .match-info {
    font-size: 0.75rem;
    color: #64748b;
  }

  /* 查看更多提示 */
  .view-more-hint {
    margin-top: 2rem;
  }

  .hint-card {
    background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
    border: none;
  }

  .hint-content {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    text-align: center;
    color: #4338ca;
    font-weight: 500;
  }

  /* 響應式設計 */
  .desktop-only {
    display: block;
  }

  .mobile-only {
    display: none;
  }

  @media (max-width: 768px) {
    .desktop-only {
      display: none;
    }

    .mobile-only {
      display: block;
    }

    .home-leaderboard-page {
      padding: 1rem 0.5rem;
    }

    .leaderboard-content-wrapper {
      padding: 1.5rem;
    }

    .page-title {
      font-size: 2rem;
    }

    .hint-content {
      flex-direction: column;
      gap: 0.75rem;
    }

    .mobile-rank-content {
      grid-template-columns: 50px 1fr auto auto;
      gap: 0.75rem;
    }

    .score-mobile,
    .matches-mobile {
      font-size: 0.875rem;
    }
  }

  @media (max-width: 480px) {
    .mobile-rank-content {
      grid-template-columns: 45px 1fr 50px 40px;
      gap: 0.5rem;
      padding: 1rem;
    }

    .player-name-mobile {
      font-size: 0.9rem;
    }

    .score-mobile {
      font-size: 0.85rem;
    }

    .matches-mobile {
      font-size: 0.75rem;
    }
  }
</style>
