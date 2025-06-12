<template>
  <div class="record-match-page container-fluid mt-4 mb-5 px-md-4">
    <n-card :bordered="false" class="form-card">
      <n-form
        ref="formRef"
        :model="matchForm"
        :rules="formRules"
        label-placement="top"
        @submit.prevent="handleRecordMatch"
      >
        <!-- 比賽基本資訊 -->
        <n-divider style="margin-top: 2rem; margin-bottom: 2rem">
          <n-text style="font-size: 14px; color: #666">比賽基本資訊</n-text>
        </n-divider>
        <n-grid :x-gap="20" :y-gap="20" cols="1 s:3" responsive="screen" align-items="start">
          <n-form-item-gi label="比賽日期" path="match_date">
            <n-date-picker
              v-model:value="matchForm.match_date_ts"
              type="date"
              placeholder="選擇比賽日期"
              style="width: 100%"
              size="large"
            />
          </n-form-item-gi>
          <n-form-item-gi label="比賽類型" path="match_type">
            <n-select v-model:value="matchForm.match_type" :options="matchTypeOptions" size="large" />
          </n-form-item-gi>
          <n-form-item-gi label="賽制" path="match_format">
            <n-select v-model:value="matchForm.match_format" :options="matchFormatOptions" size="large" />
          </n-form-item-gi>
        </n-grid>

        <!-- 可折疊的詳細設定區塊 -->
        <n-divider style="margin-top: 2rem; margin-bottom: 1rem">
          <n-button text @click="showAdvancedSettings = !showAdvancedSettings" style="color: #666; font-size: 14px">
            <template #icon>
              <n-icon :component="showAdvancedSettings ? ChevronUpIcon : ChevronDownIcon" />
            </template>
            詳細設定 (選填)
          </n-button>
        </n-divider>

        <!-- 可折疊內容 -->
        <n-collapse-transition :show="showAdvancedSettings">
          <div class="advanced-settings-container">
            <!-- 場地資訊 -->
            <div class="settings-section">
              <n-grid :x-gap="16" :y-gap="16" cols="1 s:3" responsive="screen" class="mt-3">
                <n-form-item-gi label="場地材質" path="court_surface">
                  <n-select
                    v-model:value="matchForm.court_surface"
                    :options="courtSurfaceOptions"
                    placeholder="選擇場地材質"
                    clearable
                    size="medium"
                  />
                </n-form-item-gi>

                <n-form-item-gi label="場地環境" path="court_environment">
                  <n-select
                    v-model:value="matchForm.court_environment"
                    :options="courtEnvironmentOptions"
                    placeholder="選擇場地環境"
                    clearable
                    size="medium"
                  />
                </n-form-item-gi>

                <n-form-item-gi label="比賽時段" path="time_slot">
                  <n-select
                    v-model:value="matchForm.time_slot"
                    :options="timeSlotOptions"
                    placeholder="選擇比賽時段"
                    clearable
                    size="medium"
                  />
                </n-form-item-gi>
              </n-grid>
            </div>

            <!-- 比賽詳細資訊 -->
            <div class="settings-section">
              <n-grid :x-gap="16" :y-gap="16" cols="1 s:3" responsive="screen" class="mt-3">
                <n-form-item-gi label="總得分數" path="total_points">
                  <n-input-number
                    v-model:value="matchForm.total_points"
                    placeholder="總得分數"
                    :min="0"
                    clearable
                    size="medium"
                    style="width: 100%"
                  />
                </n-form-item-gi>

                <n-form-item-gi label="比賽時長 (分鐘)" path="duration_minutes">
                  <n-input-number
                    v-model:value="matchForm.duration_minutes"
                    placeholder="20-60分鐘"
                    :min="20"
                    :max="60"
                    clearable
                    size="medium"
                    style="width: 100%"
                  />
                </n-form-item-gi>

                <n-form-item-gi label="YouTube 連結" path="youtube_url">
                  <n-input
                    v-model:value="matchForm.youtube_url"
                    placeholder="https://youtube.com/watch?v=..."
                    clearable
                    size="medium"
                  />
                </n-form-item-gi>
              </n-grid>
            </div>
          </div>
        </n-collapse-transition>

        <n-divider style="margin: 2rem 0">
          <n-text style="font-size: 14px; color: #666">對戰配置</n-text>
        </n-divider>

        <!-- 對戰視覺區塊 -->
        <div :class="[...courtClasses, { changing: isChangingCourt }]">
          <div class="team-vs-container">
            <!-- A隊卡片 -->
            <div class="team-section team-a">
              <div
                class="team-card"
                :class="{
                  'winner-glow': matchForm.side_a_outcome === 'WIN',
                  'has-players': hasTeamAPlayers
                }"
              >
                <div class="team-header">
                  <n-h3 class="team-title">A隊</n-h3>
                  <div v-if="matchForm.side_a_outcome === 'WIN'" class="winner-badge">
                    <n-icon :component="TrophyIcon" />
                    勝利
                  </div>
                </div>

                <!-- A隊球員 -->
                <div class="players-container">
                  <!-- 第一位球員 (後排) -->
                  <div class="player-slot" @click="openPlayerSelector('player1_id')">
                    <div class="position-indicator">
                      <span class="position-label">後排</span>
                    </div>
                    <div class="player-avatar">
                      <n-avatar
                        v-if="getPlayerById(matchForm.player1_id)"
                        :size="48"
                        :style="{ backgroundColor: getPlayerColor(matchForm.player1_id) }"
                      >
                        {{ getPlayerInitials(matchForm.player1_id) }}
                      </n-avatar>
                      <n-avatar v-else :size="48" style="background-color: #f0f0f0; color: #ccc" class="empty-slot">
                        <n-icon :component="AddIcon" />
                      </n-avatar>
                    </div>
                    <div class="player-info">
                      <div class="player-name">
                        {{ getPlayerById(matchForm.player1_id)?.name || '點擊選擇球員' }}
                      </div>
                    </div>
                    <n-button
                      v-if="getPlayerById(matchForm.player1_id)"
                      quaternary
                      size="tiny"
                      @click.stop="clearPlayer('player1_id')"
                      class="clear-btn"
                    >
                      <n-icon :component="CloseIcon" />
                    </n-button>
                  </div>

                  <!-- 第二位球員 (前排) - 只在雙打時顯示 -->
                  <div
                    v-if="matchForm.match_type === 'doubles'"
                    class="player-slot"
                    @click="openPlayerSelector('player2_id')"
                  >
                    <div class="position-indicator">
                      <span class="position-label">前排</span>
                    </div>
                    <div class="player-avatar">
                      <n-avatar
                        v-if="getPlayerById(matchForm.player2_id)"
                        :size="48"
                        :style="{ backgroundColor: getPlayerColor(matchForm.player2_id) }"
                      >
                        {{ getPlayerInitials(matchForm.player2_id) }}
                      </n-avatar>
                      <n-avatar v-else :size="48" style="background-color: #f0f0f0; color: #ccc" class="empty-slot">
                        <n-icon :component="AddIcon" />
                      </n-avatar>
                    </div>
                    <div class="player-info">
                      <div class="player-name">
                        {{ getPlayerById(matchForm.player2_id)?.name || '點擊選擇球員' }}
                      </div>
                    </div>
                    <n-button
                      v-if="getPlayerById(matchForm.player2_id)"
                      quaternary
                      size="tiny"
                      @click.stop="clearPlayer('player2_id')"
                      class="clear-btn"
                    >
                      <n-icon :component="CloseIcon" />
                    </n-button>
                  </div>
                </div>

                <!-- A隊得分控制 -->
                <div class="score-control">
                  <div class="score-display">
                    <span class="score-number" :class="{ winning: matchForm.side_a_outcome === 'WIN' }">
                      {{ matchForm.a_games }}
                    </span>
                    <span class="score-label">局</span>
                  </div>
                  <div class="score-buttons">
                    <n-button
                      circle
                      size="small"
                      @click="adjustScore('a_games', -1)"
                      :disabled="matchForm.a_games <= 0"
                    >
                      <n-icon :component="RemoveIcon" />
                    </n-button>
                    <n-button
                      circle
                      size="small"
                      type="primary"
                      @click="adjustScore('a_games', 1)"
                      :disabled="matchForm.a_games >= scoreInputMax"
                    >
                      <n-icon :component="AddIcon" />
                    </n-button>
                  </div>
                </div>
              </div>
            </div>

            <!-- VS 區域 -->
            <div class="vs-section">
              <!--              &lt;!&ndash; 時間控制器 &ndash;&gt;-->
              <!--              <div :class="timeControllerClasses" @click="toggleTimeSlot" title="點擊切換比賽時間">-->
              <!--                <span class="time-icon">{{ currentTimeSlot.icon }}</span>-->
              <!--                <div class="time-label">{{ currentTimeSlot.label }}</div>-->
              <!--              </div>-->

              <!-- VS 球 -->
              <div class="vs-circle">
                <span class="vs-text">VS</span>
              </div>
            </div>

            <!-- B隊卡片 -->
            <div class="team-section team-b">
              <div
                class="team-card"
                :class="{
                  'winner-glow': matchForm.side_a_outcome === 'LOSS',
                  'has-players': hasTeamBPlayers
                }"
              >
                <div class="team-header">
                  <n-h3 class="team-title">B隊</n-h3>
                  <div v-if="matchForm.side_a_outcome === 'LOSS'" class="winner-badge">
                    <n-icon :component="TrophyIcon" />
                    勝利
                  </div>
                </div>

                <!-- B隊球員 -->
                <div class="players-container">
                  <!-- 第一位球員 (後排) -->
                  <div class="player-slot" @click="openPlayerSelector('player3_id')">
                    <div class="position-indicator">
                      <span class="position-label">後排</span>
                    </div>
                    <div class="player-avatar">
                      <n-avatar
                        v-if="getPlayerById(matchForm.player3_id)"
                        :size="48"
                        :style="{ backgroundColor: getPlayerColor(matchForm.player3_id) }"
                      >
                        {{ getPlayerInitials(matchForm.player3_id) }}
                      </n-avatar>
                      <n-avatar v-else :size="48" class="empty-slot">
                        <n-icon :component="AddIcon" />
                      </n-avatar>
                    </div>
                    <div class="player-info">
                      <div class="player-name">
                        {{ getPlayerById(matchForm.player3_id)?.name || '點擊選擇球員' }}
                      </div>
                    </div>
                    <n-button
                      v-if="getPlayerById(matchForm.player3_id)"
                      quaternary
                      size="tiny"
                      @click.stop="clearPlayer('player3_id')"
                      class="clear-btn"
                    >
                      <n-icon :component="CloseIcon" />
                    </n-button>
                  </div>

                  <!-- 第二位球員 (前排) - 只在雙打時顯示 -->
                  <div
                    v-if="matchForm.match_type === 'doubles'"
                    class="player-slot"
                    @click="openPlayerSelector('player4_id')"
                  >
                    <div class="position-indicator">
                      <span class="position-label">前排</span>
                    </div>
                    <div class="player-avatar">
                      <n-avatar
                        v-if="getPlayerById(matchForm.player4_id)"
                        :size="48"
                        :style="{ backgroundColor: getPlayerColor(matchForm.player4_id) }"
                      >
                        {{ getPlayerInitials(matchForm.player4_id) }}
                      </n-avatar>
                      <n-avatar v-else :size="48" style="background-color: #f0f0f0; color: #ccc" class="empty-slot">
                        <n-icon :component="AddIcon" />
                      </n-avatar>
                    </div>
                    <div class="player-info">
                      <div class="player-name">
                        {{ getPlayerById(matchForm.player4_id)?.name || '點擊選擇球員' }}
                      </div>
                    </div>
                    <n-button
                      v-if="getPlayerById(matchForm.player4_id)"
                      quaternary
                      size="tiny"
                      @click.stop="clearPlayer('player4_id')"
                      class="clear-btn"
                    >
                      <n-icon :component="CloseIcon" />
                    </n-button>
                  </div>
                </div>

                <!-- B隊得分控制 -->
                <div class="score-control">
                  <div class="score-display">
                    <span class="score-number" :class="{ winning: matchForm.side_a_outcome === 'LOSS' }">
                      {{ matchForm.b_games }}
                    </span>
                    <span class="score-label">局</span>
                  </div>
                  <div class="score-buttons">
                    <n-button
                      circle
                      size="small"
                      @click="adjustScore('b_games', -1)"
                      :disabled="matchForm.b_games <= 0"
                    >
                      <n-icon :component="RemoveIcon" />
                    </n-button>
                    <n-button
                      circle
                      size="small"
                      type="primary"
                      @click="adjustScore('b_games', 1)"
                      :disabled="matchForm.b_games >= scoreInputMax"
                    >
                      <n-icon :component="AddIcon" />
                    </n-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 球員選擇模態框 -->
        <n-modal
          v-model:show="showPlayerSelector"
          preset="card"
          style="width: 90%; max-width: 600px"
          title="選擇球員"
          size="huge"
          :bordered="false"
          :segmented="{ content: 'soft', footer: 'soft' }"
        >
          <n-input v-model:value="modalSearchTerm" placeholder="搜尋球員..." clearable size="large" class="mb-3">
            <template #prefix>
              <n-icon :component="SearchIcon" />
            </template>
          </n-input>

          <n-scrollbar style="max-height: 400px">
            <n-grid :x-gap="12" :y-gap="12" cols="2 s:3 m:4" responsive="screen">
              <n-gi v-for="player in filteredPlayersForModal" :key="player.id">
                <div
                  class="player-card"
                  @click="selectPlayerFromModal(player.id)"
                  :class="{
                    selected: currentSelectingField && matchForm[currentSelectingField] === player.id
                  }"
                >
                  <n-avatar :size="50" :style="{ backgroundColor: getPlayerColor(player.id) }">
                    {{ getPlayerInitials(player.id) }}
                  </n-avatar>
                  <div class="player-card-info">
                    <div class="player-card-name">{{ player.name }}</div>
                    <n-tag :type="getScoreTagType(player.score)" size="small" round> {{ player.score }} 分</n-tag>
                  </div>
                </div>
              </n-gi>
            </n-grid>
          </n-scrollbar>

          <template #footer>
            <n-space justify="end">
              <n-button @click="showPlayerSelector = false">取消</n-button>
            </n-space>
          </template>
        </n-modal>

        <n-space justify="center" class="mt-5 action-buttons">
          <n-button size="large" ghost @click="goBack">
            <template #icon>
              <n-icon :component="ArrowBackIcon" />
            </template>
            返回
          </n-button>
          <n-button
            type="primary"
            attr-type="submit"
            strong
            size="large"
            :loading="submitting"
            :disabled="submitting || !matchForm.side_a_outcome"
          >
            <template v-if="!submitting" #icon>
              <n-icon :component="SaveIcon" />
            </template>
            {{ submitting ? '提交中...' : '儲存比賽結果' }}
          </n-button>
        </n-space>
      </n-form>
    </n-card>
  </div>
</template>

<script setup>
  import { computed, onMounted, reactive, ref, watch } from 'vue'
  import { useRouter } from 'vue-router'
  import apiClient from '@/services/apiClient.js'
  import '@/assets/css/match-record.css'
  import {
    NAvatar,
    NButton,
    NCard,
    NCollapseTransition,
    NDatePicker,
    NDivider,
    NForm,
    NFormItemGi,
    NGi,
    NGrid,
    NH3,
    NIcon,
    NInput,
    NInputNumber,
    NModal,
    NScrollbar,
    NSelect,
    NSpace,
    NTag,
    NText,
    useMessage
  } from 'naive-ui'
  import {
    AddOutline as AddIcon,
    ArrowBackOutline as ArrowBackIcon,
    CheckmarkCircleOutline as WinIcon,
    ChevronDownOutline as ChevronDownIcon,
    ChevronUpOutline as ChevronUpIcon,
    CloseOutline as CloseIcon,
    RemoveOutline as RemoveIcon,
    SaveOutline as SaveIcon,
    SearchOutline as SearchIcon,
    TrophyOutline as TrophyIcon
  } from '@vicons/ionicons5' // --- Hooks ---

  // --- Hooks ---
  const router = useRouter()
  const message = useMessage()

  // --- State ---
  const formRef = ref(null)
  const allActiveMembers = ref([])
  const submitting = ref(false)
  const playerSearchTerm = ref('')
  const showPlayerSelector = ref(false)
  const currentSelectingField = ref(null)
  const modalSearchTerm = ref('')
  const showAdvancedSettings = ref(false) // 新增: 控制詳細設定的顯示/隱藏

  const matchForm = reactive({
    match_date_ts: new Date().getTime(),
    match_type: 'doubles',
    match_format: 'games_9',
    player1_id: null,
    player2_id: null,
    player3_id: null,
    player4_id: null,
    a_games: 0,
    b_games: 0,
    side_a_outcome: '',
    match_notes: '',

    // 新增欄位，設定預設值
    court_surface: 'hard_court', // 預設硬地
    court_environment: 'outdoor', // 預設室外
    time_slot: 'evening', // 預設晚上
    total_points: null,
    duration_minutes: null,
    youtube_url: ''
  })

  const courtSurfaceOptions = [
    { label: '硬地', value: 'hard_court' },
    { label: '紅土', value: 'clay_court' },
    { label: '草地', value: 'grass_court' },
    { label: '人工合成', value: 'synthetic' },
    { label: '地毯', value: 'carpet' }
  ]

  const courtEnvironmentOptions = [
    { label: '室內', value: 'indoor' },
    { label: '室外', value: 'outdoor' }
  ]

  const timeSlotOptions = [
    { label: '早上', value: 'morning' },
    { label: '下午', value: 'afternoon' },
    { label: '晚上', value: 'evening' }
  ]

  // --- Options & Rules ---
  const matchTypeOptions = [
    { label: '雙打', value: 'doubles' },
    { label: '單打', value: 'singles' }
  ]

  const matchFormatOptions = [
    { label: '五局制', value: 'games_5', meta: { gamesToWin: 3 } },
    { label: '七局制', value: 'games_7', meta: { gamesToWin: 4 } },
    { label: '九局制', value: 'games_9', meta: { gamesToWin: 5 } }
  ]

  // 時間段配置
  const timeSlotConfig = {
    morning: {
      icon: '☀️',
      label: '早上',
      next: 'afternoon'
    },
    afternoon: {
      icon: '🌤️',
      label: '下午',
      next: 'evening'
    },
    evening: {
      icon: '🌙',
      label: '晚上',
      next: 'morning'
    }
  }

  const formRules = {
    match_date_ts: [{ type: 'number', required: true, message: '比賽日期為必填' }],
    match_type: [{ required: true, message: '比賽類型為必填' }],
    match_format: [{ required: true, message: '賽制為必填' }],
    player1_id: [{ required: true, type: 'number', message: 'A隊球員1為必填' }],
    player3_id: [{ required: true, type: 'number', message: 'B隊球員1為必填' }],
    a_games: [{ required: true, type: 'number', message: 'A隊局數為必填' }],
    b_games: [{ required: true, type: 'number', message: 'B隊局數為必填' }],
    player2_id: [
      {
        trigger: ['blur', 'change'],
        validator: (rule, value) => {
          if (matchForm.match_type === 'doubles' && !value) {
            return new Error('雙打時，A隊球員2為必填')
          }
          return true
        }
      }
    ],
    player4_id: [
      {
        trigger: ['blur', 'change'],
        validator: (rule, value) => {
          if (matchForm.match_type === 'doubles' && !value) {
            return new Error('雙打時，B隊球員2為必填')
          }
          return true
        }
      }
    ],
    youtube_url: {
      type: 'url',
      message: '請輸入有效的 YouTube 連結',
      trigger: ['blur']
    }
  }

  // --- Computed Properties ---
  const scoreInputMax = computed(() => {
    const selectedFormat = matchFormatOptions.find(opt => opt.value === matchForm.match_format)
    return selectedFormat?.meta?.gamesToWin ?? 9
  })

  const matchResultDisplay = computed(() => {
    if (matchForm.side_a_outcome === 'WIN') return 'A隊 勝利！'
    if (matchForm.side_a_outcome === 'LOSS') return 'B隊 勝利！'
    return null
  })

  const topPlayers = computed(() => {
    return allActiveMembers.value
      .slice()
      .sort((a, b) => b.score - a.score)
      .slice(0, 8)
  })

  const filteredPlayersForModal = computed(() => {
    if (!modalSearchTerm.value) return availablePlayersForCurrentField.value
    return availablePlayersForCurrentField.value.filter(player =>
      player.name.toLowerCase().includes(modalSearchTerm.value.toLowerCase())
    )
  })

  const availablePlayersForCurrentField = computed(() => {
    if (!currentSelectingField.value) return allActiveMembers.value

    const selectedIds = new Set(
      [matchForm.player1_id, matchForm.player2_id, matchForm.player3_id, matchForm.player4_id].filter(id => id != null)
    )

    const currentId = matchForm[currentSelectingField.value]

    return allActiveMembers.value.filter(m => !selectedIds.has(m.id) || m.id === currentId)
  })

  const hasTeamAPlayers = computed(() => {
    return matchForm.player1_id || matchForm.player2_id
  })

  const hasTeamBPlayers = computed(() => {
    return matchForm.player3_id || matchForm.player4_id
  })

  // --- Helper Functions ---
  const getPlayerById = playerId => {
    if (!playerId) return null
    return allActiveMembers.value.find(m => m.id === playerId)
  }

  const isPlayerSelected = playerId => {
    return [matchForm.player1_id, matchForm.player2_id, matchForm.player3_id, matchForm.player4_id].includes(playerId)
  }

  const getPlayerInitials = playerId => {
    const player = getPlayerById(playerId)
    if (!player) return '?'
    return player.name.charAt(0).toUpperCase()
  }

  const getPlayerColor = playerId => {
    if (!playerId) return '#f0f0f0'
    const colors = ['#18a058', '#2080f0', '#f0a020', '#d03050', '#7c3aed', '#06b6d4', '#10b981', '#f59e0b']
    return colors[playerId % colors.length]
  }

  const getScoreTagType = score => {
    if (score >= 2000) return 'error'
    if (score >= 1500) return 'warning'
    if (score >= 1000) return 'info'
    return 'default'
  }

  // --- Methods ---
  const quickSelectPlayer = playerId => {
    if (isPlayerSelected(playerId)) {
      // 如果已選中，則取消選擇
      clearPlayerFromAll(playerId)
      return
    }

    // 找到第一個空位置
    if (!matchForm.player1_id) {
      matchForm.player1_id = playerId
    } else if (!matchForm.player3_id) {
      matchForm.player3_id = playerId
    } else if (matchForm.match_type === 'doubles' && !matchForm.player2_id) {
      matchForm.player2_id = playerId
    } else if (matchForm.match_type === 'doubles' && !matchForm.player4_id) {
      matchForm.player4_id = playerId
    }
  }

  const openPlayerSelector = field => {
    currentSelectingField.value = field
    modalSearchTerm.value = ''
    showPlayerSelector.value = true
  }

  const selectPlayerFromModal = playerId => {
    if (currentSelectingField.value) {
      matchForm[currentSelectingField.value] = playerId
    }
    showPlayerSelector.value = false
    currentSelectingField.value = null
  }

  const clearPlayer = field => {
    matchForm[field] = null
  }

  const clearPlayerFromAll = playerId => {
    if (matchForm.player1_id === playerId) matchForm.player1_id = null
    if (matchForm.player2_id === playerId) matchForm.player2_id = null
    if (matchForm.player3_id === playerId) matchForm.player3_id = null
    if (matchForm.player4_id === playerId) matchForm.player4_id = null
  }

  const adjustScore = (field, delta) => {
    const newValue = matchForm[field] + delta
    if (newValue >= 0 && newValue <= scoreInputMax.value) {
      matchForm[field] = newValue
    }
  }

  // --- Watchers ---
  watch(
    [() => matchForm.a_games, () => matchForm.b_games, () => matchForm.match_format],
    () => {
      const gamesToWin = scoreInputMax.value
      const gamesA = matchForm.a_games
      const gamesB = matchForm.b_games

      if (gamesA === gamesToWin && gamesA > gamesB) {
        matchForm.side_a_outcome = 'WIN'
      } else if (gamesB === gamesToWin && gamesB > gamesA) {
        matchForm.side_a_outcome = 'LOSS'
      } else {
        matchForm.side_a_outcome = ''
      }
    },
    { deep: true }
  )

  watch(
    () => matchForm.match_type,
    newType => {
      if (newType === 'singles') {
        matchForm.player2_id = null
        matchForm.player4_id = null
      }
    }
  )

  // --- API Methods ---
  async function fetchActiveMembers() {
    try {
      const response = await apiClient.get('/members', { params: { all: 'false' } })
      allActiveMembers.value = response.data.map(m => ({
        id: m.id,
        name: m.name || m.display_name,
        score: m.score
      }))
    } catch (_error) {
      message.error('獲取球員列表失敗。')
    }
  }

  const handleRecordMatch = () => {
    formRef.value?.validate(async validationErrors => {
      if (validationErrors) {
        message.error('請修正表單中的錯誤。')
        return
      }

      const gamesToWin = scoreInputMax.value
      if (matchForm.a_games < gamesToWin && matchForm.b_games < gamesToWin) {
        message.error(`比賽尚未結束，需要有一方達到 ${gamesToWin} 局才能儲存。`)
        return
      }
      if (matchForm.a_games === matchForm.b_games) {
        message.error('比賽分數不能相同，請確認勝負。')
        return
      }

      submitting.value = true
      try {
        const formatDate = timestamp => {
          if (!timestamp) return null
          const date = new Date(timestamp)
          return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
        }

        const payload = {
          match_date: formatDate(matchForm.match_date_ts),
          match_type: matchForm.match_type,
          match_format: matchForm.match_format,
          player1_id: matchForm.player1_id,
          player2_id: matchForm.match_type === 'doubles' ? matchForm.player2_id : null,
          player3_id: matchForm.player3_id,
          player4_id: matchForm.match_type === 'doubles' ? matchForm.player4_id : null,
          a_games: matchForm.a_games,
          b_games: matchForm.b_games,
          match_notes: matchForm.match_notes || null,

          // 新增欄位 - 只有在有值的時候才傳送
          court_surface: matchForm.court_surface || null,
          court_environment: matchForm.court_environment || null,
          time_slot: matchForm.time_slot || null,
          total_points: matchForm.total_points || null,
          duration_minutes: matchForm.duration_minutes || null,
          youtube_url: matchForm.youtube_url || null
        }

        const response = await apiClient.post('/match-records', payload)
        message.success(response.data.message || '比賽結果已成功儲存！')

        setTimeout(() => {
          router.push({ name: 'Leaderboard' })
        }, 1500)
      } catch (err) {
        const errorData = err.response?.data
        if (errorData?.details) {
          let errorMsg = '輸入數據有誤：\n' + Object.values(errorData.details).flat().join('\n')
          message.error(errorMsg, { duration: 7000, closable: true })
        } else {
          message.error(errorData?.message || '提交失敗，請稍後再試。')
        }
      } finally {
        submitting.value = false
      }
    })
  }
  // 切換時間段
  const toggleTimeSlot = () => {
    const current = matchForm.time_slot || 'morning'
    matchForm.time_slot = timeSlotConfig[current].next
  }

  // 獲取當前時間段信息
  const currentTimeSlot = computed(() => {
    return timeSlotConfig[matchForm.time_slot] || timeSlotConfig.morning
  })

  // 計算動態的球場 CSS 類別
  const courtClasses = computed(() => {
    const classes = ['match-arena']

    // 場地材質類別
    if (matchForm.court_surface) {
      classes.push(`court-${matchForm.court_surface}`)
    }

    // 時間段類別
    if (matchForm.time_slot) {
      classes.push(`time-${matchForm.time_slot}`)
    }

    // 環境類別
    if (matchForm.court_environment) {
      classes.push(`env-${matchForm.court_environment}`)
    }

    return classes
  })

  // 時間控制器的 CSS 類別
  const timeControllerClasses = computed(() => {
    const classes = ['time-controller']
    if (matchForm.time_slot) {
      classes.push(matchForm.time_slot)
    }
    return classes
  })

  // 為了增加視覺效果，當設定改變時觸發動畫
  const isChangingCourt = ref(false)

  const triggerCourtAnimation = () => {
    isChangingCourt.value = true
    setTimeout(() => {
      isChangingCourt.value = false
    }, 600)
  }

  // 監聽場地設定變化，觸發動畫
  watch([() => matchForm.court_surface, () => matchForm.court_environment, () => matchForm.time_slot], () => {
    triggerCourtAnimation()
  })

  onMounted(fetchActiveMembers)

  // --- UI Helpers ---
  function getWinnerTagType() {
    return 'success'
  }

  function getWinnerIcon() {
    return WinIcon
  }

  function goBack() {
    router.push({ name: 'ManagementCenter' })
  }
</script>

<style scoped>
  @import '@/assets/css/match-record.css';
  @import '@/assets/css/dynamic-field.css';
</style>
