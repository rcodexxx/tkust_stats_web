<template>
  <div class="detailed-leaderboard-page">
    <div class="leaderboard-container">
      <!-- 頁面標題和導航 -->
      <div class="page-header">
        <div class="header-nav">
          <n-button quaternary @click="goBack" class="back-button">
            <template #icon>
              <n-icon :component="ArrowLeftIcon" />
            </template>
            返回首頁
          </n-button>
        </div>

        <div class="header-title">
          <h1 class="page-title">排行榜數據</h1>
        </div>
      </div>

      <!-- 控制面板 -->
      <div class="control-panel">
        <n-card class="control-card">
          <n-space align="center" justify="space-between" wrap>
            <!-- 左側篩選控制 -->
            <n-space align="center" wrap>
              <n-switch v-model:value="includeGuests" @update:value="fetchLeaderboard">
                <template #checked>包含訪客</template>
                <template #unchecked>僅正式會員</template>
              </n-switch>
            </n-space>

            <!-- 右側操作控制 -->
            <n-space align="center">
              <n-button @click="fetchLeaderboard" :loading="loading" secondary>
                <template #icon>
                  <n-icon :component="RefreshIcon" />
                </template>
                重新整理
              </n-button>

              <n-button @click="exportData" :disabled="leaderboardData.length === 0" secondary>
                <template #icon>
                  <n-icon :component="DownloadIcon" />
                </template>
                匯出數據
              </n-button>
            </n-space>
          </n-space>
        </n-card>
      </div>

      <!-- 主要內容區域 -->
      <n-spin :show="loading" size="large">
        <template #description>載入詳細排行榜中...</template>

        <!-- 錯誤提示 -->
        <div v-if="!loading && error" class="error-container">
          <n-alert title="錯誤" type="error" closable @close="error = null">
            載入排行榜時發生錯誤: {{ error }}
          </n-alert>
        </div>

        <!-- 系統統計 -->
        <div v-if="!loading && !error && displayMembers.length > 0" class="stats-section">
          <n-card class="stats-card">
            <n-collapse>
              <n-collapse-item title="📈 系統統計" name="stats">
                <div class="stats-grid">
                  <div class="stat-item">
                    <div class="stat-value">{{ displayMembers.length }}</div>
                    <div class="stat-label">活躍球員</div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-value">{{ Math.round((topPlayer?.mu || 0) * 100) / 100 }}</div>
                    <div class="stat-label">最高技能值</div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-value">{{ averageConfidence }}</div>
                    <div class="stat-label">平均信心度</div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-value">{{ experienceDistribution.資深 || 0 }}</div>
                    <div class="stat-label">資深球員</div>
                  </div>
                </div>

                <!-- 經驗分布圖 -->
                <div class="experience-section">
                  <h4 class="section-title">經驗等級分布</h4>
                  <div class="distribution-grid">
                    <div v-for="(count, level) in experienceDistribution" :key="level" class="distribution-item">
                      <span class="level-icon">{{ getExperienceIcon(level) }}</span>
                      <span class="level-name">{{ level }}</span>
                      <n-progress
                        type="line"
                        :percentage="getDistributionPercentage(count)"
                        :show-indicator="true"
                        :height="24"
                        :color="getExperienceColor(level)"
                      >
                        {{ count }}人
                      </n-progress>
                    </div>
                  </div>
                </div>
              </n-collapse-item>

              <n-collapse-item title="📚 數據說明" name="explanation">
                <div class="explanation-content">
                  <div class="explanation-item">
                    <h5>官方分數 (Official Score)</h5>
                    <p>
                      基於 TrueSkill 算法的保守評分，計算公式為 (μ - 3σ) ×
                      100。這是排名的主要依據，代表球員在99.7%信心度下的技能下限。
                    </p>
                  </div>

                  <div class="explanation-item">
                    <h5>潛在實力 (Potential Skill)</h5>
                    <p>TrueSkill 中的 μ 值 × 100，代表球員真實技能水平的最佳估計值，不考慮不確定性因素。</p>
                  </div>

                  <div class="explanation-item">
                    <h5>穩定度 (Consistency)</h5>
                    <p>
                      基於 σ 值計算的表現一致性指標，公式為 (1 - min(σ/8.33, 1)) × 100%。數值越高表示表現越穩定可預測。
                    </p>
                  </div>

                  <div class="explanation-item">
                    <h5>評分可信度 (Rating Confidence)</h5>
                    <p>基於比賽場次的評分可靠度，計算為 min(比賽場次/30, 1) × 100%。30場比賽後達到100%可信度。</p>
                  </div>
                </div>
              </n-collapse-item>
            </n-collapse>
          </n-card>
        </div>

        <!-- 空狀態 -->
        <div v-if="!loading && !error && leaderboardData.length === 0" class="empty-container">
          <n-empty description="目前排行榜尚無資料，快去記錄第一場比賽吧！" size="huge" />
        </div>

        <!-- 排行榜表格 -->
        <div v-if="!loading && !error && leaderboardData.length > 0" class="leaderboard-section">
          <n-card class="leaderboard-card">
            <!-- 表頭 -->
            <div class="table-header">
              <div class="header-cell rank-col">#</div>
              <div class="header-cell player-col">球員</div>
              <div class="header-cell score-col">官方分數</div>
              <div class="header-cell skill-col">潛在實力</div>
              <div class="header-cell stability-col">穩定度</div>
              <div class="header-cell experience-col">經驗等級</div>
              <div class="header-cell confidence-col">可信度</div>
            </div>

            <!-- 排行榜列表 -->
            <div class="table-body">
              <div
                v-for="member in paginatedMembers"
                :key="member.id"
                :class="[
                  'player-row',
                  getRankClass(member.rank),
                  { 'negative-score': safeGet(member, 'official_rank_score', 0) < 0 }
                ]"
                @click="showPlayerDetail(member)"
              >
                <!-- 排名 -->
                <div class="cell rank-cell">
                  <div v-if="member.rank <= 3" class="rank-icon">
                    <n-icon :component="getRankIcon(member.rank)" :size="28" :color="getRankColor(member.rank)" />
                  </div>
                  <div v-else class="rank-number">{{ member.rank }}</div>
                </div>

                <!-- 球員資訊 -->
                <div class="cell player-cell">
                  <div class="player-info">
                    <div class="player-name">
                      {{ safeGet(member, 'display_name') || safeGet(member, 'name', '未知') }}
                    </div>
                    <div class="player-meta">
                      <n-tag v-if="safeGet(member, 'is_guest', false)" size="small" type="info"> 訪客 </n-tag>
                      <span v-if="safeGet(member, 'organization_name')" class="org-name">
                        {{ member.organization_name }}
                      </span>
                    </div>
                  </div>
                </div>

                <!-- 官方分數 -->
                <div class="cell score-cell">
                  <div class="score-value" :style="{ color: getScoreColor(member.rank) }">
                    {{ formatDisplayScore(safeGet(member, 'official_rank_score', 0)) }}
                  </div>
                </div>

                <!-- 潛在實力 -->
                <div class="cell skill-cell">
                  <div class="skill-value">
                    {{ formatDisplayScore(safeGet(member, 'potential_skill', 0)) }}
                  </div>
                </div>

                <!-- 穩定度 -->
                <div class="cell stability-cell">
                  <n-progress
                    type="line"
                    :percentage="safeGet(member, 'consistency_rating', 0)"
                    :show-indicator="false"
                    :height="8"
                    :color="getStabilityColor(safeGet(member, 'consistency_rating', 0))"
                  />
                  <div class="stability-text">{{ safeGet(member, 'consistency_rating', 0) }}%</div>
                </div>

                <!-- 經驗等級 -->
                <div class="cell experience-cell">
                  <div class="experience-display">
                    <span class="experience-icon">{{
                      getExperienceIcon(safeGet(member, 'experience_level', '新手'))
                    }}</span>
                    <span class="experience-text">{{ safeGet(member, 'experience_level', '新手') }}</span>
                  </div>
                </div>

                <!-- 可信度 -->
                <div class="cell confidence-cell">
                  <div class="confidence-value">{{ safeGet(member, 'rating_confidence', 0) }}%</div>
                </div>
              </div>
            </div>
          </n-card>
        </div>

        <!-- 分頁控制 -->
        <div v-if="totalPages > 1 && !loading" class="pagination-container">
          <n-pagination
            v-model:page="currentPage"
            v-model:page-size="itemsPerPage"
            :item-count="leaderboardData.length"
            :page-sizes="[10, 20, 30, 50]"
            show-size-picker
            show-quick-jumper
          >
            <template #prefix="{ itemCount }"> 共 {{ itemCount }} 位球員 </template>
          </n-pagination>
        </div>
      </n-spin>
    </div>

    <!-- 球員詳情彈窗 -->
    <n-modal v-model:show="showPlayerModal" preset="card" style="width: 90%; max-width: 700px" title="球員詳細分析">
      <div v-if="selectedPlayer" class="player-detail-modal">
        <div class="player-header">
          <h3>{{ safeGet(selectedPlayer, 'display_name') || safeGet(selectedPlayer, 'name', '未知') }}</h3>
          <div class="player-tags">
            <n-tag v-if="safeGet(selectedPlayer, 'is_guest', false)" type="info">訪客</n-tag>
            <div class="experience-display">
              <span class="experience-icon">{{
                getExperienceIcon(safeGet(selectedPlayer, 'experience_level', '新手'))
              }}</span>
              <span class="experience-text">{{ safeGet(selectedPlayer, 'experience_level', '新手') }}</span>
            </div>
          </div>
        </div>

        <div class="player-stats-grid">
          <div class="stat-card">
            <h4>官方排名分數</h4>
            <div class="stat-main-value">
              {{ formatDisplayScore(safeGet(selectedPlayer, 'official_rank_score', 0)) }}
            </div>
            <div class="stat-description">主要排名依據</div>
          </div>

          <div class="stat-card">
            <h4>潛在實力</h4>
            <div class="stat-main-value">{{ formatDisplayScore(safeGet(selectedPlayer, 'potential_skill', 0)) }}</div>
            <div class="stat-description">技術天花板 (μ × 100)</div>
          </div>

          <div class="stat-card">
            <h4>穩定度</h4>
            <div class="stat-main-value">{{ safeGet(selectedPlayer, 'consistency_rating', 0) }}%</div>
            <n-progress
              type="line"
              :percentage="safeGet(selectedPlayer, 'consistency_rating', 0)"
              :color="getStabilityColor(safeGet(selectedPlayer, 'consistency_rating', 0))"
              class="mt-2"
            />
            <div class="stat-description">表現一致性</div>
          </div>

          <div class="stat-card">
            <h4>評分可信度</h4>
            <div class="stat-main-value">{{ safeGet(selectedPlayer, 'rating_confidence', 0) }}%</div>
            <div class="stat-description">基於比賽經驗</div>
          </div>
        </div>

        <div class="player-raw-data">
          <n-collapse>
            <n-collapse-item title="原始 TrueSkill 數據" name="rawData">
              <div class="raw-data-grid">
                <div><strong>μ:</strong> {{ formatScore(safeGet(selectedPlayer, 'mu', 0), 3) }}</div>
                <div><strong>σ:</strong> {{ formatScore(safeGet(selectedPlayer, 'sigma', 0), 3) }}</div>
                <div>
                  <strong>保守評分:</strong>
                  {{ formatScore(safeGet(selectedPlayer, 'official_rank_score', 0) / 100, 2) }}
                </div>
                <div><strong>總比賽:</strong> {{ safeGet(selectedPlayer, 'total_matches', 0) }}</div>
              </div>
            </n-collapse-item>
          </n-collapse>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup>
  import { computed, onMounted, ref, watch } from 'vue'
  import { useRouter } from 'vue-router'
  import { useAuthStore } from '@/stores/authStore'
  import apiClient from '@/services/apiClient.js'
  import {
    NAlert,
    NButton,
    NCard,
    NCollapse,
    NCollapseItem,
    NEmpty,
    NIcon,
    NModal,
    NPagination,
    NProgress,
    NSpin,
    NSpace,
    NSwitch,
    NTag,
    NText
  } from 'naive-ui'
  import { Medal as Rank3Icon, ShieldSharp as Rank2Icon, TrophySharp as Rank1Icon } from '@vicons/ionicons5'
  import {
    ArrowPathIcon as RefreshIcon,
    ArrowLeftIcon,
    ArrowDownTrayIcon as DownloadIcon
  } from '@heroicons/vue/24/outline'

  const router = useRouter()
  const authStore = useAuthStore()

  // 響應式數據
  const leaderboardData = ref([])
  const loading = ref(true)
  const error = ref(null)
  const currentPage = ref(1)
  const itemsPerPage = ref(20)

  // 篩選控制
  const includeGuests = ref(false)

  // UI狀態
  const showPlayerModal = ref(false)
  const selectedPlayer = ref(null)

  // 防抖函數 (移除，因為不再需要)
  // let fetchTimeout = null
  // const debouncedFetchLeaderboard = () => {
  //   if (fetchTimeout) clearTimeout(fetchTimeout)
  //   fetchTimeout = setTimeout(fetchLeaderboard, 500)
  // }

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

  const formatScore = (score, precision = 1) => {
    if (typeof score !== 'number' || isNaN(score)) return '0.0'
    return score.toFixed(precision)
  }

  const formatDisplayScore = score => {
    if (typeof score !== 'number' || isNaN(score)) return '0'
    return Math.round(score * 100).toString()
  }

  // 獲取經驗等級圖標
  const getExperienceIcon = experienceLevel => {
    const iconMap = {
      新手: '🌱', // 新芽
      初級: '🌿', // 葉子
      中級: '🌳', // 樹
      高級: '💫', // 閃爍星
      資深: '⭐' // 星星
    }
    return iconMap[experienceLevel] || '🌱'
  }

  // === 計算屬性 ===
  const totalPages = computed(() => {
    if (!leaderboardData.value) return 0
    return Math.ceil(leaderboardData.value.length / itemsPerPage.value) || 1
  })

  const paginatedMembers = computed(() => {
    if (!leaderboardData.value || leaderboardData.value.length === 0) return []
    const startIndex = (currentPage.value - 1) * itemsPerPage.value
    const endIndex = startIndex + itemsPerPage.value
    return leaderboardData.value.slice(startIndex, endIndex)
  })

  const displayMembers = computed(() => {
    return leaderboardData.value
  })

  const topPlayer = computed(() => {
    return displayMembers.value[0] || null
  })

  const averageConfidence = computed(() => {
    if (displayMembers.value.length === 0) return 0
    const total = displayMembers.value.reduce((sum, m) => sum + (m.rating_confidence || 0), 0)
    return Math.round(total / displayMembers.value.length)
  })

  const experienceDistribution = computed(() => {
    const distribution = {}
    displayMembers.value.forEach(member => {
      const level = member.experience_level || '新手'
      distribution[level] = (distribution[level] || 0) + 1
    })
    return distribution
  })

  // === 數據獲取 ===
  const fetchLeaderboard = async () => {
    loading.value = true
    error.value = null

    try {
      let response

      // 使用備用API
      response = await apiClient.get('/members', {
        params: { view: 'leaderboard' }
      })

      if (response && Array.isArray(response.data)) {
        let filteredData = response.data

        if (!includeGuests.value) {
          filteredData = filteredData.filter(member => !safeGet(member, 'is_guest', false))
        }

        leaderboardData.value = filteredData.map((member, index) => ({
          ...member,
          rank: index + 1,
          official_rank_score:
            safeGet(member, 'official_rank_score', 0) ||
            safeGet(member, 'score', 0) ||
            safeGet(member, 'conservative_score', 0),
          potential_skill: safeGet(member, 'mu', 25),
          consistency_rating: Math.max(
            0,
            Math.min(100, Math.round((1 - Math.min(safeGet(member, 'sigma', 8.33) / 8.33, 1)) * 100))
          ),
          experience_level: safeGet(member, 'experience_level', '新手'),
          rating_confidence: Math.max(0, Math.min(100, Math.round((safeGet(member, 'total_matches', 0) / 30) * 100))),
          total_matches: safeGet(member, 'total_matches', 0)
        }))
      } else {
        throw new Error('無法獲取排行榜數據')
      }
    } catch (e) {
      error.value = e.response?.data?.message || e.message || '無法獲取排行榜數據'
      console.error('排行榜 API 錯誤:', e)
      leaderboardData.value = []
    } finally {
      loading.value = false
    }
  }

  // === UI 函數 ===
  function goBack() {
    router.push('/')
  }

  function getDistributionPercentage(count) {
    const total = displayMembers.value.length
    return total > 0 ? Math.round((count / total) * 100) : 0
  }

  function getExperienceColor(level) {
    const colorMap = {
      新手: '#22c55e',
      初級: '#3b82f6',
      中級: '#8b5cf6',
      高級: '#f59e0b',
      資深: '#ef4444'
    }
    return colorMap[level] || '#94a3b8'
  }

  function exportData() {
    try {
      const csvData = leaderboardData.value.map(member => ({
        rank: member.rank,
        name: safeGet(member, 'display_name') || safeGet(member, 'name', ''),
        organization: safeGet(member, 'organization_name', ''),
        official_rank_score: formatDisplayScore(safeGet(member, 'official_rank_score', 0)),
        potential_skill: formatDisplayScore(safeGet(member, 'potential_skill', 0)),
        consistency_rating: safeGet(member, 'consistency_rating', 0),
        experience_level: safeGet(member, 'experience_level', ''),
        rating_confidence: safeGet(member, 'rating_confidence', 0),
        total_matches: safeGet(member, 'total_matches', 0),
        is_guest: safeGet(member, 'is_guest', false) ? '是' : '否'
      }))

      const csv = [Object.keys(csvData[0]).join(','), ...csvData.map(row => Object.values(row).join(','))].join('\n')

      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `排行榜_${new Date().toISOString().split('T')[0]}.csv`
      link.click()
    } catch (error) {
      console.error('匯出失敗:', error)
    }
  }

  function getRankClass(rank) {
    if (rank === 1) return 'rank-first'
    if (rank === 2) return 'rank-second'
    if (rank === 3) return 'rank-third'
    return 'rank-other'
  }

  function getRankIcon(rank) {
    if (rank === 1) return Rank1Icon
    if (rank === 2) return Rank2Icon
    if (rank === 3) return Rank3Icon
    return null
  }

  function getRankColor(rank) {
    if (rank === 1) return '#FFD700'
    if (rank === 2) return '#C0C0C0'
    if (rank === 3) return '#CD7F32'
    return undefined
  }

  function getScoreColor(rank) {
    if (rank === 1) return '#B8860B'
    if (rank === 2) return '#696969'
    if (rank === 3) return '#8B4513'
    return '#1f2937'
  }

  function getStabilityColor(percentage) {
    if (percentage >= 80) return '#22c55e'
    if (percentage >= 60) return '#f59e0b'
    if (percentage >= 40) return '#ef4444'
    return '#6b7280'
  }

  function showPlayerDetail(member) {
    selectedPlayer.value = member
    showPlayerModal.value = true
  }

  // === 生命週期 ===
  onMounted(() => {
    if (!authStore.isAuthenticated) {
      router.push('/login')
      return
    }
    fetchLeaderboard()
  })

  // 監聽篩選條件變化
  watch(includeGuests, fetchLeaderboard)
</script>

<style scoped>
  .detailed-leaderboard-page {
    min-height: 100vh;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem 1rem;
  }

  .leaderboard-container {
    max-width: 1400px;
    margin: 0 auto;
  }

  /* === 頁面標題 === */
  .page-header {
    background: white;
    border-radius: 20px;
    padding: 2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
  }

  .header-nav {
    margin-bottom: 1rem;
  }

  .back-button {
    font-weight: 500;
    border-radius: 12px;
  }

  .header-title {
    text-align: center;
  }

  .page-title {
    font-size: 2.5rem;
    font-weight: 800;
    color: transparent;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 0.5rem 0;
    display: inline-block;
  }

  .page-subtitle {
    font-size: 1rem;
    color: #64748b;
  }

  /* === 控制面板 === */
  .control-panel {
    margin-bottom: 1.5rem;
  }

  .control-card {
    border-radius: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    background: white;
  }

  /* === 統計區域 === */
  .stats-section {
    margin-bottom: 1.5rem;
  }

  .stats-card {
    border-radius: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    background: white;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .stat-item {
    text-align: center;
    padding: 1.5rem;
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    border-radius: 16px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  }

  .stat-value {
    font-size: 2.5rem;
    font-weight: 800;
    color: #1e293b;
    margin-bottom: 0.5rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .stat-label {
    font-size: 0.875rem;
    color: #64748b;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .experience-section {
    margin-top: 2rem;
  }

  .section-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #374151;
    margin-bottom: 1.5rem;
    text-align: center;
  }

  .distribution-grid {
    display: grid;
    gap: 1rem;
  }

  .distribution-item {
    display: grid;
    grid-template-columns: 40px 100px 1fr;
    gap: 1rem;
    align-items: center;
    padding: 1rem;
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    border-radius: 12px;
  }

  .level-icon {
    font-size: 1.5rem;
    text-align: center;
  }

  .level-name {
    font-size: 0.875rem;
    font-weight: 600;
    color: #374151;
  }

  /* === 數據說明 === */
  .explanation-content {
    display: grid;
    gap: 1.5rem;
  }

  .explanation-item {
    padding: 1.5rem;
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    border-radius: 12px;
    border-left: 4px solid #667eea;
  }

  .explanation-item h5 {
    font-size: 1rem;
    font-weight: 700;
    color: #1e293b;
    margin: 0 0 0.75rem 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .explanation-item p {
    font-size: 0.875rem;
    color: #64748b;
    line-height: 1.6;
    margin: 0;
    font-weight: 500;
  }

  /* === 錯誤和空狀態 === */
  .error-container,
  .empty-container {
    margin: 2rem 0;
  }

  /* === 排行榜表格 === */
  .leaderboard-section {
    margin-bottom: 2rem;
  }

  .leaderboard-card {
    border-radius: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    background: white;
  }

  .table-header {
    display: grid;
    grid-template-columns: 80px 1fr 120px 120px 140px 140px 120px;
    gap: 1rem;
    padding: 1.5rem 2rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: 700;
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .header-cell {
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
  }

  /* 響應式隱藏欄位 */
  .experience-col,
  .stability-col,
  .confidence-col,
  .skill-col {
    display: flex;
  }

  @media (max-width: 1200px) {
    .experience-col {
      display: none;
    }
  }

  @media (max-width: 900px) {
    .stability-col,
    .confidence-col {
      display: none;
    }
  }

  @media (max-width: 600px) {
    .skill-col {
      display: none;
    }
  }

  .table-body {
    background: white;
  }

  .player-row {
    display: grid;
    grid-template-columns: 80px 1fr 120px 120px 140px 140px 120px;
    gap: 1rem;
    padding: 1.5rem 2rem;
    border-bottom: 1px solid #f1f5f9;
    transition: all 0.3s ease;
    cursor: pointer;
    align-items: center;
    position: relative;
  }

  .player-row:hover {
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  }

  .player-row:last-child {
    border-bottom: none;
  }

  /* 排名樣式 */
  .player-row.rank-first {
    background: linear-gradient(135deg, #fef3c7 0%, #fbbf24 20%);
    border-left: 6px solid #f59e0b;
  }

  .player-row.rank-second {
    background: linear-gradient(135deg, #f1f5f9 0%, #cbd5e1 20%);
    border-left: 6px solid #64748b;
  }

  .player-row.rank-third {
    background: linear-gradient(135deg, #fed7aa 0%, #fb923c 20%);
    border-left: 6px solid #ea580c;
  }

  .player-row.negative-score {
    border-left: 6px solid #dc2626;
    background: linear-gradient(135deg, #fef2f2 0%, #fecaca 20%);
  }

  .cell {
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
  }

  .rank-cell {
    justify-content: center;
  }

  .rank-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 50px;
    height: 50px;
    background: white;
    border-radius: 50%;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .rank-number {
    font-size: 1.25rem;
    font-weight: 700;
    color: #64748b;
    background: white;
    border-radius: 50%;
    width: 45px;
    height: 45px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .player-cell {
    justify-content: flex-start;
    text-align: left;
  }

  .player-info {
    width: 100%;
  }

  .player-name {
    font-size: 1.125rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 0.25rem;
  }

  .player-meta {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  .org-name {
    font-size: 0.75rem;
    color: #64748b;
    font-weight: 500;
  }

  .score-cell .score-value {
    font-size: 1.5rem;
    font-weight: 800;
  }

  .skill-cell .skill-value {
    font-size: 1.125rem;
    font-weight: 700;
    color: #4f46e5;
  }

  .stability-cell {
    flex-direction: column;
    gap: 0.5rem;
    width: 100%;
  }

  .stability-text {
    font-size: 0.875rem;
    color: #64748b;
    font-weight: 600;
  }

  .experience-cell {
    justify-content: center;
  }

  .experience-display {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    border-radius: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  }

  .experience-icon {
    font-size: 1.25rem;
  }

  .experience-text {
    font-size: 0.875rem;
    font-weight: 600;
    color: #374151;
  }

  .confidence-cell .confidence-value {
    font-size: 1rem;
    font-weight: 700;
    color: #059669;
  }

  /* === 分頁 === */
  .pagination-container {
    display: flex;
    justify-content: center;
    margin-top: 2rem;
    padding: 2rem;
    background: white;
    border-radius: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  }

  /* === 球員詳情彈窗 === */
  .player-detail-modal {
    padding: 1rem 0;
  }

  .player-header {
    text-align: center;
    margin-bottom: 2rem;
  }

  .player-header h3 {
    font-size: 1.75rem;
    font-weight: 800;
    color: #1e293b;
    margin-bottom: 1rem;
  }

  .player-tags {
    display: flex;
    justify-content: center;
    gap: 1rem;
    flex-wrap: wrap;
    align-items: center;
  }

  .player-stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .stat-card {
    text-align: center;
    padding: 2rem;
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    border-radius: 16px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  }

  .stat-card h4 {
    font-size: 0.875rem;
    font-weight: 700;
    color: #64748b;
    margin-bottom: 1rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .stat-main-value {
    font-size: 2.5rem;
    font-weight: 800;
    color: #1e293b;
    margin-bottom: 0.75rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .stat-description {
    font-size: 0.75rem;
    color: #64748b;
    font-weight: 500;
  }

  .player-raw-data {
    margin-top: 2rem;
  }

  .raw-data-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
    font-size: 0.875rem;
  }

  .raw-data-grid div {
    padding: 1rem;
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    border-radius: 12px;
    font-weight: 500;
  }

  /* === 動畫 === */
  .player-row {
    animation: fadeInUp 0.4s ease-out;
  }

  @keyframes fadeInUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* === 響應式設計 === */
  @media (max-width: 1200px) {
    .table-header {
      grid-template-columns: 70px 1fr 100px 100px 120px 120px;
    }

    .player-row {
      grid-template-columns: 70px 1fr 100px 100px 120px 120px;
      font-size: 0.875rem;
    }

    .experience-cell,
    .experience-col {
      display: none;
    }
  }

  @media (max-width: 900px) {
    .detailed-leaderboard-page {
      padding: 1rem 0.5rem;
    }

    .page-header {
      padding: 1.5rem;
    }

    .page-title {
      font-size: 2rem;
    }

    .table-header {
      grid-template-columns: 60px 1fr 90px 90px;
      padding: 1rem;
      gap: 0.5rem;
    }

    .player-row {
      grid-template-columns: 60px 1fr 90px 90px;
      padding: 1rem;
      gap: 0.5rem;
    }

    .stability-cell,
    .confidence-cell,
    .stability-col,
    .confidence-col {
      display: none;
    }

    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
      gap: 1rem;
    }

    .stat-item {
      padding: 1rem;
    }

    .stat-value {
      font-size: 1.75rem;
    }

    .distribution-item {
      grid-template-columns: 30px 80px 1fr;
      padding: 0.75rem;
    }
  }

  @media (max-width: 600px) {
    .table-header {
      grid-template-columns: 50px 1fr 80px;
      font-size: 0.75rem;
    }

    .player-row {
      grid-template-columns: 50px 1fr 80px;
      font-size: 0.75rem;
    }

    .skill-cell,
    .skill-col {
      display: none;
    }

    .rank-icon {
      width: 40px;
      height: 40px;
    }

    .rank-number {
      width: 35px;
      height: 35px;
      font-size: 1rem;
    }

    .player-name {
      font-size: 1rem;
    }

    .score-value {
      font-size: 1.25rem;
    }
  }
</style>
