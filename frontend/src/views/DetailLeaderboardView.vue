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
          <h1 class="page-title">📊 詳細排行榜</h1>
          <n-text depth="3" class="page-subtitle">
            完整的四維度評分分析與球員詳細統計
          </n-text>
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

              <n-select
                v-model:value="experienceFilter"
                :options="experienceOptions"
                placeholder="篩選經驗等級"
                clearable
                style="width: 150px"
                @update:value="fetchLeaderboard"
              />

              <n-input-number
                v-model:value="minMatches"
                placeholder="最少比賽"
                :min="0"
                :max="100"
                style="width: 120px"
                @update:value="debouncedFetchLeaderboard"
              />
            </n-space>

            <!-- 右側操作控制 -->
            <n-space align="center">
              <n-tooltip>
                <template #trigger>
                  <n-button
                    quaternary
                    circle
                    @click="showDetailedView = !showDetailedView"
                    :type="showDetailedView ? 'primary' : 'default'"
                  >
                    <n-icon :component="showDetailedView ? EyeIcon : EyeOffIcon" />
                  </n-button>
                </template>
                {{ showDetailedView ? '簡化視圖' : '詳細視圖' }}
              </n-tooltip>

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
        <div v-if="!loading && !error && hasValidStats" class="stats-section">
          <n-card title="📈 系統統計" class="stats-card">
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-value">{{ safeGet(systemStats, 'basic.total_active_players', 0) }}</div>
                <div class="stat-label">活躍球員</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ formatDisplayScore(safeGet(systemStats, 'basic.average_conservative_score', 0)) }}</div>
                <div class="stat-label">平均分數</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">
                  {{ formatDisplayScore(safeGet(systemStats, 'basic.score_range.min', 0)) }} -
                  {{ formatDisplayScore(safeGet(systemStats, 'basic.score_range.max', 0)) }}
                </div>
                <div class="stat-label">分數範圍</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ safeGet(systemStats, 'system_health.experienced_players', 0) }}</div>
                <div class="stat-label">有經驗球員</div>
              </div>
            </div>

            <!-- 經驗分布圖 -->
            <div v-if="hasExperienceDistribution" class="experience-section">
              <h4 class="section-title">經驗等級分布</h4>
              <div class="distribution-grid">
                <div
                  v-for="(count, level) in systemStats.experience_distribution"
                  :key="level"
                  class="distribution-item"
                >
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
          </n-card>
        </div>

        <!-- 空狀態 -->
        <div v-if="!loading && !error && leaderboardData.length === 0" class="empty-container">
          <n-empty description="目前排行榜尚無資料，快去記錄第一場比賽吧！" size="huge" />
        </div>

        <!-- 排行榜表格 -->
        <div v-if="!loading && !error && leaderboardData.length > 0" class="leaderboard-section">
          <n-card class="leaderboard-card">
            <!-- 桌面版表頭 -->
            <div v-if="!isMobile" class="table-header">
              <div class="header-cell rank-col">#</div>
              <div class="header-cell player-col">球員</div>
              <div v-if="showDetailedView" class="header-cell score-col">官方分數</div>
              <div v-if="showDetailedView" class="header-cell skill-col">潛在實力</div>
              <div v-if="showDetailedView" class="header-cell stability-col">穩定度</div>
              <div v-if="showDetailedView" class="header-cell experience-col">經驗等級</div>
              <div v-if="showDetailedView" class="header-cell confidence-col">可信度</div>
              <div v-if="!showDetailedView" class="header-cell score-col">分數</div>
              <div class="header-cell matches-col">比賽場次</div>
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
                    <n-icon
                      :component="getRankIcon(member.rank)"
                      :size="isMobile ? 24 : 28"
                      :color="getRankColor(member.rank)"
                    />
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
                      <n-tag v-if="safeGet(member, 'is_guest', false)" size="small" type="info">
                        訪客
                      </n-tag>
                      <span v-if="safeGet(member, 'organization_name')" class="org-name">
                        {{ member.organization_name }}
                      </span>
                    </div>
                  </div>
                </div>

                <!-- 詳細視圖欄位 -->
                <template v-if="showDetailedView && !isMobile">
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
                    <n-tag
                      :type="getExperienceTagType(safeGet(member, 'experience_level', '未知'))"
                      size="small"
                    >
                      {{ safeGet(member, 'experience_level', '未知') }}
                    </n-tag>
                  </div>

                  <!-- 可信度 -->
                  <div class="cell confidence-cell">
                    <div class="confidence-value">{{ safeGet(member, 'rating_confidence', 0) }}%</div>
                  </div>
                </template>

                <!-- 簡化視圖分數 -->
                <div v-if="!showDetailedView && !isMobile" class="cell score-cell">
                  <div class="score-value" :style="{ color: getScoreColor(member.rank) }">
                    {{ formatDisplayScore(safeGet(member, 'official_rank_score', 0)) }}
                  </div>
                </div>

                <!-- 手機版簡化顯示 -->
                <div v-if="isMobile" class="cell mobile-info">
                  <div class="mobile-score">
                    {{ formatDisplayScore(safeGet(member, 'official_rank_score', 0)) }}
                  </div>
                  <n-tag
                    v-if="showDetailedView"
                    :type="getExperienceTagType(safeGet(member, 'experience_level', '未知'))"
                    size="tiny"
                  >
                    {{ safeGet(member, 'experience_level', '未知') }}
                  </n-tag>
                </div>

                <!-- 比賽場次 -->
                <div class="cell matches-cell">
                  <div class="matches-count">{{ safeGet(member, 'total_matches', 0) }}</div>
                  <div class="matches-label">場</div>
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
            <n-tag :type="getExperienceTagType(safeGet(selectedPlayer, 'experience_level', '未知'))">
              {{ safeGet(selectedPlayer, 'experience_level', '未知') }}
            </n-tag>
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
                <div><strong>μ (Mu):</strong> {{ formatScore(safeGet(selectedPlayer, 'mu', 0), 3) }}</div>
                <div><strong>σ (Sigma):</strong> {{ formatScore(safeGet(selectedPlayer, 'sigma', 0), 3) }}</div>
                <div>
                  <strong>保守評分:</strong>
                  {{ formatScore(safeGet(selectedPlayer, 'official_rank_score', 0) / 100, 2) }}
                </div>
                <div><strong>總比賽:</strong> {{ safeGet(selectedPlayer, 'total_matches', 0) }}</div>
                <div>
                  <strong>是否有經驗:</strong>
                  {{ safeGet(selectedPlayer, 'is_experienced_player', false) ? '是' : '否' }}
                </div>
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
  NInputNumber,
  NModal,
  NPagination,
  NProgress,
  NSelect,
  NSpin,
  NSpace,
  NSwitch,
  NTag,
  NText,
  NTooltip
} from 'naive-ui'
import { Medal as Rank3Icon, ShieldSharp as Rank2Icon, TrophySharp as Rank1Icon } from '@vicons/ionicons5'
import {
  EyeIcon,
  EyeSlashIcon as EyeOffIcon,
  ArrowPathIcon as RefreshIcon,
  ArrowLeftIcon,
  ArrowDownTrayIcon as DownloadIcon
} from '@heroicons/vue/24/outline'

const router = useRouter()
const authStore = useAuthStore()

// 響應式數據
const leaderboardData = ref([])
const systemStats = ref(null)
const loading = ref(true)
const error = ref(null)
const currentPage = ref(1)
const itemsPerPage = ref(20)

// 篩選控制
const includeGuests = ref(false)
const experienceFilter = ref(null)
const minMatches = ref(0)
const showDetailedView = ref(true)

// UI狀態
const showPlayerModal = ref(false)
const selectedPlayer = ref(null)
const isMobile = ref(window.innerWidth < 768)

// 篩選選項
const experienceOptions = [
  { label: '新手', value: '新手' },
  { label: '初級', value: '初級' },
  { label: '中級', value: '中級' },
  { label: '高級', value: '高級' },
  { label: '資深', value: '資深' }
]

// 響應式監聽
window.addEventListener('resize', () => {
  isMobile.value = window.innerWidth < 768
})

// 防抖函數
let fetchTimeout = null
const debouncedFetchLeaderboard = () => {
  if (fetchTimeout) clearTimeout(fetchTimeout)
  fetchTimeout = setTimeout(fetchLeaderboard, 500)
}

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

// === 計算屬性 ===
const hasValidStats = computed(() => {
  return systemStats.value && typeof systemStats.value === 'object' && safeGet(systemStats.value, 'basic') !== undefined
})

const hasExperienceDistribution = computed(() => {
  return systemStats.value &&
         systemStats.value.experience_distribution &&
         Object.keys(systemStats.value.experience_distribution).length > 0
})

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

// === 數據獲取 ===
const fetchLeaderboard = async () => {
  loading.value = true
  error.value = null

  try {
    const params = new URLSearchParams({
      include_guests: includeGuests.value,
      limit: 200
    })

    if (experienceFilter.value) {
      params.append('experience_level', experienceFilter.value)
    }

    if (minMatches.value > 0) {
      params.append('min_matches', minMatches.value)
    }

    let response
    let data

    try {
      // 嘗試新的API
      response = await apiClient.get(`/members/leaderboard?${params}`)
      data = response.data

      if (data && Array.isArray(data.data)) {
        leaderboardData.value = data.data.map((member, index) => ({
          ...member,
          rank: index + 1,
          official_rank_score: safeGet(member, 'score', 0) || safeGet(member, 'conservative_score', 0),
          potential_skill: safeGet(member, 'mu', 25),
          consistency_rating: Math.max(0, Math.min(100, Math.round((1 - Math.min(safeGet(member, 'sigma', 8.33) / 8.33, 1)) * 100))),
          experience_level: safeGet(member, 'experience_level', '未知'),
          rating_confidence: Math.max(0, Math.min(100, Math.round((safeGet(member, 'total_matches', 0) / 30) * 100))),
          total_matches: safeGet(member, 'total_matches', 0)
        }))

        systemStats.value = safeGet(data, 'statistics', null)
      } else {
        throw new Error('API 回應格式不正確')
      }
    } catch (newApiError) {
      console.warn('新 API 失敗，使用備用方案:', newApiError.message)

      // 備用舊API
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
          official_rank_score: safeGet(member, 'score', 0) || safeGet(member, 'conservative_score', 0),
          potential_skill: safeGet(member, 'mu', 25),
          consistency_rating: Math.max(0, Math.min(100, Math.round((1 - Math.min(safeGet(member, 'sigma', 8.33) / 8.33, 1)) * 100))),
          experience_level: safeGet(member, 'experience_level', '未知'),
          rating_confidence: Math.max(0, Math.min(100, Math.round((safeGet(member, 'total_matches', 0) / 30) * 100))),
          total_matches: safeGet(member, 'total_matches', 0)
        }))

        systemStats.value = null
      } else {
        throw new Error('備用 API 也失敗了')
      }
    }
  } catch (e) {
    error.value = e.response?.data?.message || e.message || '無法獲取排行榜數據'
    console.error('排行榜 API 錯誤:', e)
    leaderboardData.value = []
    systemStats.value = null
  } finally {
    loading.value = false
  }
}

// === UI 函數 ===
function goBack() {
  router.push('/')
}

function getDistributionPercentage(count) {
  const total = safeGet(systemStats.value, 'basic.total_active_players', 1)
  return Math.round((count / total) * 100)
}

function getExperienceColor(level) {
  const colorMap = {
    '新手': '#34d399',
    '初級': '#60a5fa',
    '中級': '#a78bfa',
    '高級': '#fb7185',
    '資深': '#f59e0b'
  }
  return colorMap[level] || '#94a3b8'
}

function exportData() {
  try {
    const csvData = leaderboardData.value.map(member => ({
      排名: member.rank,
      姓名: safeGet(member, 'display_name') || safeGet(member, 'name', ''),
      組織: safeGet(member, 'organization_name', ''),
      官方分數: formatDisplayScore(safeGet(member, 'official_rank_score', 0)),
      潛在實力: formatDisplayScore(safeGet(member, 'potential_skill', 0)),
      穩定度: safeGet(member, 'consistency_rating', 0),
      經驗等級: safeGet(member, 'experience_level', ''),
      可信度: safeGet(member, 'rating_confidence', 0),
      比賽場次: safeGet(member, 'total_matches', 0),
      是否訪客: safeGet(member, 'is_guest', false) ? '是' : '否'
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
  if (percentage >= 80) return '#18a058'
  if (percentage >= 60) return '#f0a020'
  if (percentage >= 40) return '#d03050'
  return '#909399'
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
watch([includeGuests, experienceFilter], fetchLeaderboard)
</script>

<style scoped>
.detailed-leaderboard-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 1rem;
}

.leaderboard-container {
  max-width: 1200px;
  margin: 0 auto;
}

/* === 頁面標題 === */
.page-header {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.header-nav {
  margin-bottom: 1rem;
}

.back-button {
  font-weight: 500;
}

.header-title {
  text-align: center;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0 0 0.5rem 0;
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
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

/* === 統計區域 === */
.stats-section {
  margin-bottom: 1.5rem;
}

.stats-card {
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-item {
  text-align: center;
  padding: 1rem;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-radius: 12px;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 0.875rem;
  color: #64748b;
  font-weight: 500;
}

.experience-section {
  margin-top: 2rem;
}

.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 1rem;
}

.distribution-grid {
  display: grid;
  gap: 0.75rem;
}

.distribution-item {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 1rem;
  align-items: center;
}

.level-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
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
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 60px 1fr 100px 100px 120px 100px 80px 100px;
  gap: 1rem;
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-bottom: 1px solid #e2e8f0;
  font-weight: 600;
  color: #374151;
  font-size: 0.875rem;
}

.table-header.simple {
  grid-template-columns: 60px 1fr 100px 100px;
}

.header-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.table-body {
  background: white;
}

.player-row {
  display: grid;
  grid-template-columns: 60px 1fr 100px 100px 120px 100px 80px 100px;
  gap: 1rem;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #f1f5f9;
  transition: all 0.2s ease;
  cursor: pointer;
  align-items: center;
}

.player-row.simple {
  grid-template-columns: 60px 1fr 100px 100px;
}

.player-row:hover {
  background: #f8fafc;
  transform: translateY(-1px);
}

.player-row:last-child {
  border-bottom: none;
}

/* 排名樣式 */
.player-row.rank-first {
  background: linear-gradient(135deg, #fef3c7 0%, #fbbf24 20%);
  border-left: 4px solid #f59e0b;
}

.player-row.rank-second {
  background: linear-gradient(135deg, #f1f5f9 0%, #cbd5e1 20%);
  border-left: 4px solid #64748b;
}

.player-row.rank-third {
  background: linear-gradient(135deg, #fed7aa 0%, #fb923c 20%);
  border-left: 4px solid #ea580c;
}

.player-row.negative-score {
  border-left: 4px solid #dc2626;
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
  width: 40px;
  height: 40px;
  background: white;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.rank-number {
  font-size: 1.25rem;
  font-weight: 600;
  color: #64748b;
  background: white;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.player-cell {
  justify-content: flex-start;
  text-align: left;
}

.player-info {
  width: 100%;
}

.player-name {
  font-size: 1rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 0.25rem;
}

.player-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.org-name {
  font-size: 0.75rem;
  color: #64748b;
}

.score-cell .score-value {
  font-size: 1.25rem;
  font-weight: 700;
}

.skill-cell .skill-value {
  font-size: 1rem;
  font-weight: 600;
  color: #4f46e5;
}

.stability-cell {
  flex-direction: column;
  gap: 0.25rem;
}

.stability-text {
  font-size: 0.75rem;
  color: #64748b;
}

.confidence-cell .confidence-value {
  font-size: 0.875rem;
  font-weight: 500;
  color: #059669;
}

.matches-cell {
  flex-direction: column;
  gap: 0.25rem;
}

.matches-count {
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
}

.matches-label {
  font-size: 0.75rem;
  color: #64748b;
}

/* === 手機版樣式 === */
@media (max-width: 768px) {
  .detailed-leaderboard-page {
    padding: 0.5rem;
  }

  .page-header {
    padding: 1.5rem;
  }

  .page-title {
    font-size: 2rem;
  }

  .table-header {
    grid-template-columns: 50px 1fr 80px 80px;
    padding: 0.75rem 1rem;
    font-size: 0.75rem;
  }

  .player-row {
    grid-template-columns: 50px 1fr 80px 80px;
    padding: 1rem;
  }

  .mobile-info {
    flex-direction: column;
    gap: 0.25rem;
  }

  .mobile-score {
    font-size: 1.125rem;
    font-weight: 700;
    color: #1e293b;
  }

  .rank-icon {
    width: 32px;
    height: 32px;
  }

  .rank-number {
    width: 28px;
    height: 28px;
    font-size: 1rem;
  }

  .player-name {
    font-size: 0.875rem;
  }

  .matches-count {
    font-size: 0.875rem;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }

  .stat-item {
    padding: 0.75rem;
  }

  .stat-value {
    font-size: 1.5rem;
  }
}

/* === 分頁 === */
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 2rem;
  padding: 1rem;
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
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 0.5rem;
}

.player-tags {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.player-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  text-align: center;
  padding: 1.5rem;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-radius: 12px;
}

.stat-card h4 {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-main-value {
  font-size: 2rem;
  font-weight: 800;
  color: #1e293b;
  margin-bottom: 0.5rem;
}

.stat-description {
  font-size: 0.75rem;
  color: #64748b;
}

.player-raw-data {
  margin-top: 2rem;
}

.raw-data-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
  font-size: 0.875rem;
}

.raw-data-grid div {
  padding: 0.5rem;
  background: #f8fafc;
  border-radius: 6px;
}

/* === 動畫 === */
.player-row {
  animation: fadeInUp 0.4s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 錯誤提示樣式 */
.n-alert {
  border-radius: 12px;
}

/* 載入狀態 */
.n-spin {
  min-height: 400px;
}
</style>