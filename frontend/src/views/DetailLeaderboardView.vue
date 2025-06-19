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
          <h1 class="page-title">詳細數據</h1>
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

              <!-- 最少比賽場次篩選 -->
              <n-input-number
                v-model:value="minMatches"
                :min="0"
                :max="100"
                placeholder="最少場次"
                @update:value="fetchLeaderboard"
                style="width: 120px"
              >
                <template #prefix>🎾</template>
              </n-input-number>
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
                    <div class="stat-value">{{ formatScore(topPlayer?.potential_skill || 0, 1) }}</div>
                    <div class="stat-label">最高潛在實力</div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-value">{{ averageConfidence }}%</div>
                    <div class="stat-label">平均勝率</div>
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

              <n-collapse-item title="📚評分系統說明" name="explanation">
                <div class="explanation-content">
                  <div class="explanation-intro"></div>

                  <div class="explanation-item">
                    <h5>🏆 官方排名分數 (Conservative Score)</h5>
                    <p>
                      <strong>計算公式：μ - 3σ</strong><br />
                      這是主要排名依據，代表球員在 99.7% 信心度下的技能下限。
                      採用保守評分避免新手虛高問題，確保排名可靠性。
                    </p>
                  </div>

                  <div class="explanation-item">
                    <h5>⚡ 潛在實力 (Potential Skill)</h5>
                    <p>
                      <strong>計算公式：μ 值</strong><br />
                      代表球員真實技能水平的最佳估計值，不考慮不確定性。 這是技術天花板，顯示球員的理論最高水平。
                    </p>
                  </div>

                  <div class="explanation-item">
                    <h5>📊 穩定度評分 (Consistency)</h5>
                    <p>
                      <strong>計算公式：(1 - min(σ/8.33, 1)) × 100%</strong><br />
                      基於 σ 值的表現一致性指標。σ 值越小，穩定度越高。 多打比賽可提升穩定度，體現技術成熟度。
                    </p>
                  </div>

                  <div class="explanation-item">
                    <h5>🎓 經驗等級分析</h5>
                    <p>
                      <strong>基於 σ 值的經驗分級：</strong><br />
                      • σ ≥ 7.0：🌱 新手（剛開始）<br />
                      • 5.0 ≤ σ < 7.0：🌿 初級（有基礎）<br />
                      • 3.0 ≤ σ < 5.0：🌳 中級（有經驗）<br />
                      • 2.0 ≤ σ < 3.0：💫 高級（技術成熟）<br />
                      • σ < 2.0：⭐ 資深（大師級）
                    </p>
                  </div>

                  <div class="explanation-item">
                    <h5>🎮 比賽影響機制</h5>
                    <p>
                      <strong>勝利：</strong>μ 上升，σ 下降（技術提升，不確定性減少）<br />
                      <strong>失敗：</strong>μ 下降，σ 下降（略微退步，但經驗增加）<br />
                      <strong>懸殊比分：</strong>分數變化較小（實力差距明顯）<br />
                      <strong>接近比分：</strong>分數變化較大（競爭激烈）<br />
                      <strong>性別獎勵：</strong>女性擊敗男性額外 +0.6 μ
                    </p>
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
              <div class="header-cell winrate-col">勝率</div>
              <div class="header-cell stability-col">穩定度</div>
              <div class="header-cell experience-col">經驗等級</div>
              <div class="header-cell matches-col">比賽記錄</div>
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
                      {{ safeGet(member, 'name') || safeGet(member, 'display_name', '未知') }}
                    </div>
                    <div class="player-meta">
                      <n-tag v-if="safeGet(member, 'is_guest', false)" size="small" type="info"> 訪客</n-tag>
                      <span v-if="safeGet(member, 'organization_name')" class="org-name">
                        {{ member.organization_name }}
                      </span>
                    </div>
                  </div>
                </div>

                <!-- 官方分數 -->
                <div class="cell score-cell">
                  <div class="score-value" :style="{ color: getScoreColor(member.rank) }">
                    {{ formatScore(safeGet(member, 'official_rank_score', 0), 2) }}
                  </div>
                </div>

                <!-- 潛在實力 -->
                <div class="cell skill-cell">
                  <div class="skill-value">
                    {{ formatScore(safeGet(member, 'potential_skill', 0), 2) }}
                  </div>
                </div>

                <!-- 勝率 -->
                <div class="cell winrate-cell">
                  <div class="winrate-display">
                    <div class="winrate-percentage" :style="{ color: getWinRateColor(safeGet(member, 'win_rate', 0)) }">
                      {{ safeGet(member, 'win_rate', 0) }}%
                    </div>
                    <div class="winrate-detail">
                      {{ safeGet(member, 'wins', 0) }}勝{{ safeGet(member, 'losses', 0) }}敗
                    </div>
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

                <!-- 比賽記錄 -->
                <div class="cell matches-cell">
                  <div class="matches-display">
                    <div class="matches-total">{{ safeGet(member, 'total_matches', 0) }}場</div>
                    <div class="matches-detail">
                      {{ safeGet(member, 'wins', 0) }}勝 {{ safeGet(member, 'losses', 0) }}敗
                    </div>
                  </div>
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
            <template #prefix="{ itemCount }"> 共 {{ itemCount }} 位球員</template>
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
              {{ formatScore(safeGet(selectedPlayer, 'official_rank_score', 0), 2) }}
            </div>
            <div class="stat-description">保守評分</div>
          </div>

          <div class="stat-card">
            <h4>潛在實力</h4>
            <div class="stat-main-value">{{ formatScore(safeGet(selectedPlayer, 'potential_skill', 0), 2) }}</div>
            <div class="stat-description">技術天花板</div>
          </div>

          <div class="stat-card">
            <h4>勝率表現</h4>
            <div class="stat-main-value" :style="{ color: getWinRateColor(safeGet(selectedPlayer, 'win_rate', 0)) }">
              {{ safeGet(selectedPlayer, 'win_rate', 0) }}%
            </div>
            <div class="stat-description">
              {{ safeGet(selectedPlayer, 'wins', 0) }}勝 {{ safeGet(selectedPlayer, 'losses', 0) }}敗
            </div>
          </div>

          <div class="stat-card">
            <h4>穩定度</h4>
            <div class="stat-main-value">{{ safeGet(selectedPlayer, 'consistency_rating', 0) }}%</div>
            <!--            <n-progress-->
            <!--              type="line"-->
            <!--              :percentage="safeGet(selectedPlayer, 'consistency_rating', 0)"-->
            <!--              :color="getStabilityColor(safeGet(selectedPlayer, 'consistency_rating', 0))"-->
            <!--              class="mt-2"-->
            <!--            />-->
            <div class="stat-description">表現一致性</div>
          </div>

          <div class="stat-card">
            <h4>比賽經驗</h4>
            <div class="stat-main-value">{{ safeGet(selectedPlayer, 'total_matches', 0) }}</div>
            <div class="stat-description">總比賽場次</div>
          </div>

          <div class="stat-card">
            <h4>經驗等級</h4>
            <div class="stat-main-value">
              <span class="experience-icon" style="font-size: 2rem">
                {{ getExperienceIcon(safeGet(selectedPlayer, 'experience_level', '新手')) }}
              </span>
            </div>
            <div class="stat-description">{{ safeGet(selectedPlayer, 'experience_level', '新手') }}</div>
          </div>
        </div>

        <div class="player-raw-data">
          <n-collapse>
            <n-collapse-item title="原始 TrueSkill 數據" name="rawData">
              <div class="raw-data-grid">
                <div><strong>μ (技能期望值):</strong> {{ formatScore(safeGet(selectedPlayer, 'mu', 25), 3) }}</div>
                <div><strong>σ (不確定性):</strong> {{ formatScore(safeGet(selectedPlayer, 'sigma', 8.33), 3) }}</div>
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
    NSpace,
    NSpin,
    NSwitch,
    NTag
  } from 'naive-ui'
  import { Medal as Rank3Icon, ShieldSharp as Rank2Icon, TrophySharp as Rank1Icon } from '@vicons/ionicons5'
  import {
    ArrowDownTrayIcon as DownloadIcon,
    ArrowLeftIcon,
    ArrowPathIcon as RefreshIcon
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
  const minMatches = ref(0)

  // UI狀態
  const showPlayerModal = ref(false)
  const selectedPlayer = ref(null)

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
    const total = displayMembers.value.reduce((sum, m) => sum + (m.win_rate || 0), 0)
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
      // 使用新的 /leaderboard API 端點
      const params = {
        include_guests: includeGuests.value,
        limit: 100 // 獲取更多數據以便前端篩選
      }

      if (minMatches.value > 0) {
        params.min_matches = minMatches.value
      }

      console.log('發送請求到 /leaderboard，參數:', params)
      const response = await apiClient.get('/leaderboard', { params })

      console.log('API 完整響應:', response)
      console.log('響應數據結構:', response.data)

      // 檢查不同可能的數據結構
      let leaderboardArray = null

      if (response && response.data) {
        // 嘗試不同的數據位置
        if (Array.isArray(response.data)) {
          // 數據直接在 response.data 中
          leaderboardArray = response.data
          console.log('數據位置: response.data (直接數組)')
        } else if (response.data.data && Array.isArray(response.data.data)) {
          // 數據在 response.data.data 中
          leaderboardArray = response.data.data
          console.log('數據位置: response.data.data')
        } else if (response.data.leaderboard && Array.isArray(response.data.leaderboard)) {
          // 數據在 response.data.leaderboard 中
          leaderboardArray = response.data.leaderboard
          console.log('數據位置: response.data.leaderboard')
        } else {
          console.error('無法找到排行榜數組數據，響應結構:', {
            hasData: !!response.data,
            dataKeys: response.data ? Object.keys(response.data) : [],
            dataType: typeof response.data,
            isArray: Array.isArray(response.data)
          })
          throw new Error(`API 返回數據格式不正確。數據類型: ${typeof response.data}`)
        }

        if (leaderboardArray && leaderboardArray.length > 0) {
          console.log(`找到 ${leaderboardArray.length} 筆排行榜記錄`)
          console.log('第一筆記錄結構:', leaderboardArray[0])

          // 處理排行榜數據
          leaderboardData.value = leaderboardArray.map((member, index) => {
            // 正確計算各項指標
            const mu = safeGet(member, 'mu', 25)
            const sigma = safeGet(member, 'sigma', 8.33)
            const totalMatches = safeGet(member, 'total_matches', 0)
            const winRate = safeGet(member, 'win_rate', 0)
            const wins = safeGet(member, 'wins', 0)
            const losses = safeGet(member, 'losses', 0)
            const rank = safeGet(member, 'rank', index + 1)

            console.log(`球員 ${member.name || member.display_name}: mu=${mu}, sigma=${sigma}, winRate=${winRate}`)

            return {
              ...member,
              rank: rank,
              // 官方分數：(μ - 3σ) * 100
              official_rank_score: safeGet(member, 'conservative_score', 0) * 100,
              // 潛在實力：μ值
              potential_skill: mu * 100,
              // 穩定度：(1 - min(σ/8.33, 1)) × 100%
              consistency_rating: Math.max(0, Math.min(100, Math.round((1 - Math.min(sigma / 8.33, 1)) * 100))),
              // 經驗等級
              experience_level: safeGet(member, 'experience_level', '新手'),
              // 比賽統計
              total_matches: totalMatches,
              wins: wins,
              losses: losses,
              win_rate: winRate,
              // 保留原始值
              mu: mu,
              sigma: sigma
            }
          })

          console.log(`成功處理 ${leaderboardData.value.length} 筆排行榜記錄`)

          // 如果API沒有返回排名，則手動排序並添加排名
          if (leaderboardData.value.length > 0 && !leaderboardData.value[0].rank) {
            leaderboardData.value.sort((a, b) => b.official_rank_score - a.official_rank_score)
            leaderboardData.value.forEach((member, index) => {
              member.rank = index + 1
            })
            console.log('手動添加排名完成')
          }
        } else {
          console.warn('API 返回空的排行榜數據')
          leaderboardData.value = []
        }
      } else {
        throw new Error('API 響應為空或格式錯誤')
      }
    } catch (e) {
      const errorMsg = e.response?.data?.message || e.message || '載入排行榜時發生錯誤'
      error.value = errorMsg
      console.error('排行榜 API 錯誤詳情:', {
        error: e,
        response: e.response,
        message: errorMsg
      })
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
        排名: member.rank,
        姓名: safeGet(member, 'display_name') || safeGet(member, 'name', ''),
        組織: safeGet(member, 'organization_name', ''),
        官方分數: formatScore(safeGet(member, 'official_rank_score', 0), 2),
        潛在實力: formatScore(safeGet(member, 'potential_skill', 0), 2),
        勝率: `${safeGet(member, 'win_rate', 0)}%`,
        勝場: safeGet(member, 'wins', 0),
        敗場: safeGet(member, 'losses', 0),
        總場次: safeGet(member, 'total_matches', 0),
        穩定度: `${safeGet(member, 'consistency_rating', 0)}%`,
        經驗等級: safeGet(member, 'experience_level', ''),
        是否訪客: safeGet(member, 'is_guest', false) ? '是' : '否',
        原始μ值: formatScore(safeGet(member, 'mu', 25), 3),
        原始σ值: formatScore(safeGet(member, 'sigma', 8.33), 3)
      }))

      const csv = [Object.keys(csvData[0]).join(','), ...csvData.map(row => Object.values(row).join(','))].join('\n')

      const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `TrueSkill排行榜_${new Date().toISOString().split('T')[0]}.csv`
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

  function getWinRateColor(winRate) {
    if (winRate >= 70) return '#22c55e' // 綠色 - 高勝率
    if (winRate >= 50) return '#3b82f6' // 藍色 - 中等勝率
    if (winRate >= 30) return '#f59e0b' // 橙色 - 低勝率
    return '#ef4444' // 紅色 - 很低勝率
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
  watch([includeGuests, minMatches], () => {
    // 防抖處理
    clearTimeout(window.fetchTimeout)
    window.fetchTimeout = setTimeout(fetchLeaderboard, 500)
  })
</script>

<style scoped>
  .detailed-leaderboard-page {
    min-height: 100vh;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1.5rem 0.8rem; /* 縮小 padding */
    font-size: 0.85rem; /* 整體字體基準縮小 */
  }

  .leaderboard-container {
    max-width: 1600px; /* 增加最大寬度以適應更多內容 */
    margin: 0 auto;
  }

  /* === 頁面標題 === */
  .page-header {
    background: white;
    border-radius: 16px; /* 縮小圓角 */
    padding: 1.5rem; /* 縮小 padding */
    margin-bottom: 1rem;
    box-shadow: 0 15px 45px rgba(0, 0, 0, 0.08); /* 減少陰影 */
  }

  .header-nav {
    margin-bottom: 0.8rem;
  }

  .back-button {
    font-weight: 500;
    border-radius: 10px;
    font-size: 0.85rem;
  }

  .header-title {
    text-align: center;
  }

  .page-title {
    font-size: 2rem; /* 縮小標題 */
    font-weight: 800;
    color: transparent;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 0.3rem 0;
    display: inline-block;
  }

  .page-subtitle {
    font-size: 0.85rem;
    color: #64748b;
    margin: 0;
  }

  /* === 控制面板 === */
  .control-panel {
    margin-bottom: 1rem;
  }

  .control-card {
    border-radius: 16px;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.08);
    background: white;
  }

  /* === 統計區域 === */
  .stats-section {
    margin-bottom: 1rem;
  }

  .stats-card {
    border-radius: 16px;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.08);
    background: white;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); /* 縮小最小寬度 */
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .stat-item {
    text-align: center;
    padding: 1rem; /* 縮小 padding */
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    border-radius: 12px;
    box-shadow: 0 3px 9px rgba(0, 0, 0, 0.04);
  }

  .stat-value {
    font-size: 1.2rem; /* 縮小統計數值 */
    font-weight: 800;
    color: #1e293b;
    margin-bottom: 0.3rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .stat-label {
    font-size: 0.7rem; /* 縮小標籤 */
    color: #64748b;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .experience-section {
    margin-top: 1.5rem;
  }

  .section-title {
    font-size: 1rem; /* 縮小章節標題 */
    font-weight: 700;
    color: #374151;
    margin-bottom: 1rem;
    text-align: center;
  }

  .distribution-grid {
    display: grid;
    gap: 0.8rem;
  }

  .distribution-item {
    display: grid;
    grid-template-columns: 30px 80px 1fr; /* 縮小圖標和名稱寬度 */
    gap: 0.8rem;
    align-items: center;
    padding: 0.8rem;
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    border-radius: 10px;
  }

  .level-icon {
    font-size: 1.2rem; /* 縮小圖標 */
    text-align: center;
  }

  .level-name {
    font-size: 0.75rem; /* 縮小等級名稱 */
    font-weight: 600;
    color: #374151;
  }

  /* === 數據說明 === */
  .explanation-content {
    display: grid;
    gap: 1rem;
  }

  .explanation-intro {
    padding: 1rem;
    background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
    border-radius: 10px;
    text-align: center;
  }

  .explanation-intro h4 {
    font-size: 1rem;
    font-weight: 700;
    color: #1e293b;
    margin: 0 0 0.5rem 0;
  }

  .explanation-intro p {
    font-size: 0.75rem;
    color: #64748b;
    margin: 0;
    font-weight: 500;
  }

  .explanation-item {
    padding: 1rem;
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    border-radius: 10px;
    border-left: 3px solid #667eea;
  }

  .explanation-item h5 {
    font-size: 0.85rem;
    font-weight: 700;
    color: #1e293b;
    margin: 0 0 0.5rem 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .explanation-item p {
    font-size: 0.75rem;
    color: #64748b;
    line-height: 1.5;
    margin: 0;
    font-weight: 500;
  }

  /* === 錯誤和空狀態 === */
  .error-container,
  .empty-container {
    margin: 1.5rem 0;
  }

  /* === 排行榜表格 === */
  .leaderboard-section {
    margin-bottom: 1.5rem;
  }

  .leaderboard-card {
    border-radius: 16px;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.08);
    overflow: hidden;
    background: white;
  }

  .table-header {
    display: grid;
    grid-template-columns: 60px 1fr 100px 100px 100px 120px 120px 120px 120px; /* 縮小列寬 */
    gap: 0.8rem;
    padding: 1rem 1.5rem; /* 縮小 padding */
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: 700;
    font-size: 0.7rem; /* 縮小表頭字體 */
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .header-cell {
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    white-space: nowrap; /* 防止換行 */
  }

  /* 響應式隱藏欄位 */
  .experience-col,
  .stability-col,
  .matches-col,
  .winrate-col,
  .raw-score-col,
  .skill-col {
    display: flex;
  }

  @media (max-width: 1600px) {
    .experience-col,
    .matches-col {
      display: none;
    }
  }

  @media (max-width: 1400px) {
    .raw-score-col {
      display: none;
    }
  }

  @media (max-width: 1200px) {
    .winrate-col {
      display: none;
    }
  }

  @media (max-width: 900px) {
    .stability-col {
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
    grid-template-columns: 60px 1fr 100px 100px 100px 120px 120px 120px 120px; /* 與表頭一致 */
    gap: 0.8rem;
    padding: 0.8rem 1.5rem; /* 縮小 padding */
    border-bottom: 1px solid #f1f5f9;
    transition: all 0.2s ease; /* 加快動畫 */
    cursor: pointer;
    align-items: center;
    position: relative;
    font-size: 0.8rem; /* 整體縮小字體 */
  }

  .player-row:hover {
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    transform: translateY(-1px); /* 減少懸浮效果 */
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
  }

  .player-row:last-child {
    border-bottom: none;
  }

  /* 排名樣式 */
  .player-row.rank-first {
    background: linear-gradient(135deg, #fef3c7 0%, #fbbf24 15%);
    border-left: 4px solid #f59e0b;
  }

  .player-row.rank-second {
    background: linear-gradient(135deg, #f1f5f9 0%, #cbd5e1 15%);
    border-left: 4px solid #64748b;
  }

  .player-row.rank-third {
    background: linear-gradient(135deg, #fed7aa 0%, #fb923c 15%);
    border-left: 4px solid #ea580c;
  }

  .player-row.negative-score {
    border-left: 4px solid #dc2626;
    background: linear-gradient(135deg, #fef2f2 0%, #fecaca 15%);
  }

  .cell {
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    white-space: nowrap; /* 防止換行 */
    overflow: hidden; /* 隱藏溢出 */
  }

  .rank-cell {
    justify-content: center;
  }

  .rank-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px; /* 縮小圖標 */
    height: 36px;
    background: white;
    border-radius: 50%;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  }

  .rank-number {
    font-size: 0.95rem; /* 縮小排名數字 */
    font-weight: 700;
    color: #64748b;
    background: white;
    border-radius: 50%;
    width: 32px; /* 縮小尺寸 */
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  }

  .player-cell {
    justify-content: flex-start;
    text-align: left;
  }

  .player-info {
    width: 100%;
    min-width: 0; /* 允許 flex 收縮 */
  }

  .player-name {
    font-size: 0.9rem; /* 縮小球員名稱 */
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 0.15rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis; /* 超長名稱用省略號 */
  }

  .player-meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: nowrap; /* 不換行 */
  }

  .org-name {
    font-size: 0.65rem; /* 縮小組織名稱 */
    color: #64748b;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 80px; /* 限制組織名稱寬度 */
  }

  .score-cell .score-value {
    font-size: 1.1rem; /* 縮小主要分數 */
    font-weight: 800;
  }

  .score-label {
    font-size: 0.6rem;
    color: #64748b;
    margin-top: 0.15rem;
    font-weight: 500;
  }

  .raw-score-cell {
    justify-content: center;
    text-align: center;
  }

  .raw-score-value {
    font-size: 0.9rem; /* 縮小原始分數 */
    font-weight: 700;
    color: #6366f1;
  }

  .skill-cell {
    justify-content: center;
    text-align: center;
  }

  .skill-cell .skill-value {
    font-size: 0.85rem; /* 縮小技能值 */
    font-weight: 700;
    color: #4f46e5;
  }

  .stability-cell {
    flex-direction: column;
    gap: 0.3rem;
    width: 100%;
  }

  .stability-text {
    font-size: 0.7rem; /* 縮小穩定度文字 */
    color: #64748b;
    font-weight: 600;
  }

  .experience-cell {
    justify-content: center;
  }

  .experience-display {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.3rem 0.6rem; /* 縮小 padding */
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    border-radius: 15px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  }

  .experience-icon {
    font-size: 1rem; /* 縮小經驗圖標 */
  }

  .experience-text {
    font-size: 0.7rem; /* 縮小經驗文字 */
    font-weight: 600;
    color: #374151;
    white-space: nowrap;
  }

  .winrate-cell {
    justify-content: center;
  }

  .winrate-display {
    text-align: center;
  }

  .winrate-percentage {
    font-size: 0.95rem; /* 縮小勝率 */
    font-weight: 700;
    margin-bottom: 0.15rem;
  }

  .winrate-detail {
    font-size: 0.6rem;
    color: #64748b;
    font-weight: 500;
    white-space: nowrap;
  }

  .matches-cell {
    justify-content: center;
  }

  .matches-display {
    text-align: center;
  }

  .matches-total {
    font-size: 0.8rem; /* 縮小比賽數量 */
    font-weight: 700;
    color: #059669;
    margin-bottom: 0.15rem;
  }

  .matches-detail {
    font-size: 0.6rem;
    color: #64748b;
    font-weight: 500;
    white-space: nowrap;
  }

  /* === 分頁 === */
  .pagination-container {
    display: flex;
    justify-content: center;
    margin-top: 1.5rem;
    padding: 1.5rem;
    background: white;
    border-radius: 16px;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.08);
  }

  /* === 球員詳情彈窗 === */
  .player-detail-modal {
    padding: 0.8rem 0;
  }

  .player-header {
    text-align: center;
    margin-bottom: 1.5rem;
  }

  .player-header h3 {
    font-size: 1.4rem; /* 縮小彈窗標題 */
    font-weight: 800;
    color: #1e293b;
    margin-bottom: 0.8rem;
  }

  .player-tags {
    display: flex;
    justify-content: center;
    gap: 0.8rem;
    flex-wrap: wrap;
    align-items: center;
  }

  .player-stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); /* 縮小最小寬度 */
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .stat-card {
    text-align: center;
    padding: 1.2rem; /* 縮小卡片 padding */
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    border-radius: 12px;
    box-shadow: 0 3px 9px rgba(0, 0, 0, 0.04);
  }

  .stat-card h4 {
    font-size: 0.7rem; /* 縮小卡片標題 */
    font-weight: 700;
    color: #64748b;
    margin-bottom: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .stat-main-value {
    font-size: 1.8rem; /* 縮小主要數值 */
    font-weight: 800;
    color: #1e293b;
    margin-bottom: 0.5rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .stat-description {
    font-size: 0.65rem; /* 縮小描述文字 */
    color: #64748b;
    font-weight: 500;
  }

  .player-raw-data {
    margin-top: 1.5rem;
  }

  .raw-data-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 0.8rem;
    font-size: 0.75rem; /* 縮小原始數據文字 */
  }

  .raw-data-grid div {
    padding: 0.8rem;
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    border-radius: 10px;
    font-weight: 500;
  }

  /* === 動畫 === */
  .player-row {
    animation: fadeInUp 0.3s ease-out; /* 加快動畫 */
  }

  @keyframes fadeInUp {
    from {
      opacity: 0;
      transform: translateY(15px); /* 減少移動距離 */
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* === 響應式設計 === */
  @media (max-width: 1600px) {
    .table-header {
      grid-template-columns: 55px 1fr 90px 90px 90px 110px 110px;
    }

    .player-row {
      grid-template-columns: 55px 1fr 90px 90px 90px 110px 110px;
      font-size: 0.75rem;
    }

    .experience-cell,
    .experience-col,
    .matches-cell,
    .matches-col {
      display: none;
    }
  }

  @media (max-width: 1400px) {
    .table-header {
      grid-template-columns: 55px 1fr 85px 85px 100px 100px;
    }

    .player-row {
      grid-template-columns: 55px 1fr 85px 85px 100px 100px;
    }

    .raw-score-cell,
    .raw-score-col {
      display: none;
    }
  }

  @media (max-width: 1200px) {
    .table-header {
      grid-template-columns: 50px 1fr 80px 80px 90px;
    }

    .player-row {
      grid-template-columns: 50px 1fr 80px 80px 90px;
    }

    .winrate-cell,
    .winrate-col {
      display: none;
    }
  }

  @media (max-width: 900px) {
    .detailed-leaderboard-page {
      padding: 1rem 0.5rem;
    }

    .page-header {
      padding: 1rem;
    }

    .page-title {
      font-size: 1.6rem;
    }

    .table-header {
      grid-template-columns: 45px 1fr 70px 70px;
      padding: 0.8rem 1rem;
      gap: 0.4rem;
      font-size: 0.65rem;
    }

    .player-row {
      grid-template-columns: 45px 1fr 70px 70px;
      padding: 0.8rem 1rem;
      gap: 0.4rem;
      font-size: 0.7rem;
    }

    .stability-cell,
    .stability-col {
      display: none;
    }

    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
      gap: 0.8rem;
    }

    .stat-item {
      padding: 0.8rem;
    }

    .stat-value {
      font-size: 1rem;
    }

    .distribution-item {
      grid-template-columns: 25px 60px 1fr;
      padding: 0.6rem;
    }
  }

  @media (max-width: 600px) {
    .table-header {
      grid-template-columns: 40px 1fr 65px;
      font-size: 0.6rem;
    }

    .player-row {
      grid-template-columns: 40px 1fr 65px;
      font-size: 0.65rem;
    }

    .skill-cell,
    .skill-col {
      display: none;
    }

    .rank-icon {
      width: 30px;
      height: 30px;
    }

    .rank-number {
      width: 28px;
      height: 28px;
      font-size: 0.8rem;
    }

    .player-name {
      font-size: 0.8rem;
    }

    .score-value {
      font-size: 1rem;
    }

    .org-name {
      max-width: 60px;
    }
  }
</style>
