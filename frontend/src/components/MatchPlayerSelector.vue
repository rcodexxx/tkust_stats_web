<!-- MatchPlayerSelector.vue -->
<template>
  <div class="match-player-selector">
    <!-- 動態網球場視覺化 -->
    <div class="arena-container">
      <div :class="courtClasses" :data-changing="isChangingCourt">
        <!-- 時間控制器 -->
        <div v-if="modelValue.time_slot" :class="timeControllerClasses" @click="toggleTimeSlot">
          <span class="time-icon">{{ currentTimeSlot.icon }}</span>
        </div>

        <!-- 球員vs球員視覺化容器 -->
        <div class="team-vs-container">
          <!-- 隊伍 A -->
          <div class="team-section">
            <div class="team-card" :class="{ 'has-players': hasTeamAPlayers, 'winner-glow': isTeamAWinner }">
              <div class="team-header">
                <h3 class="team-title">隊伍 A</h3>
                <n-tag v-if="isTeamAWinner" type="success" round size="small">
                  <template #icon>
                    <n-icon :component="WinIcon" />
                  </template>
                  勝方
                </n-tag>
              </div>

              <!-- 球員1 (後排) -->
              <div class="player-slot">
                <n-button
                  v-if="!modelValue.player1_id"
                  dashed
                  block
                  @click="openPlayerSelector('player1_id')"
                  style="height: 3.5rem"
                  class="select-player-btn"
                >
                  <template #icon>
                    <n-icon :component="AddIcon" />
                  </template>
                  <div class="btn-content">
                    <div>選擇球員</div>
                    <div class="position-hint">後排</div>
                  </div>
                </n-button>
                <div v-else class="selected-player">
                  <div class="position-indicator-simple back-row">後排</div>
                  <div class="player-card-compact">
                    <n-avatar
                      :size="32"
                      :style="{
                        backgroundColor: getPlayerColor(modelValue.player1_id),
                        color: '#fff'
                      }"
                    >
                      {{ getPlayerInitial(getPlayerName(modelValue.player1_id)) }}
                    </n-avatar>
                    <div class="player-details">
                      <div class="player-name-compact">{{ getPlayerName(modelValue.player1_id) }}</div>
                      <div v-if="getPlayerOrganization(modelValue.player1_id)" class="player-org-compact">
                        {{ getPlayerOrganization(modelValue.player1_id) }}
                      </div>
                    </div>
                    <n-button size="small" quaternary circle @click="clearPlayer('player1_id')" class="remove-btn">
                      <n-icon :component="CloseIcon" />
                    </n-button>
                  </div>
                </div>
              </div>

              <!-- 球員2 (前排) - 只在雙打時顯示 -->
              <div v-if="modelValue.match_type === 'doubles'" class="player-slot">
                <n-button
                  v-if="!modelValue.player2_id"
                  dashed
                  block
                  @click="openPlayerSelector('player2_id')"
                  style="height: 3.5rem"
                  class="select-player-btn"
                >
                  <template #icon>
                    <n-icon :component="AddIcon" />
                  </template>
                  <div class="btn-content">
                    <div>選擇搭檔</div>
                    <div class="position-hint">前排</div>
                  </div>
                </n-button>
                <div v-else class="selected-player">
                  <div class="position-indicator-simple front-row">前排</div>
                  <div class="player-card-compact">
                    <n-avatar
                      :size="32"
                      :style="{
                        backgroundColor: getPlayerColor(modelValue.player2_id),
                        color: '#fff'
                      }"
                    >
                      {{ getPlayerInitial(getPlayerName(modelValue.player2_id)) }}
                    </n-avatar>
                    <div class="player-details">
                      <div class="player-name-compact">{{ getPlayerName(modelValue.player2_id) }}</div>
                      <div v-if="getPlayerOrganization(modelValue.player2_id)" class="player-org-compact">
                        {{ getPlayerOrganization(modelValue.player2_id) }}
                      </div>
                    </div>
                    <n-button size="small" quaternary circle @click="clearPlayer('player2_id')" class="remove-btn">
                      <n-icon :component="CloseIcon" />
                    </n-button>
                  </div>
                </div>
              </div>

              <!-- 隊伍A分數控制 -->
              <div class="score-controls">
                <div class="score-wrapper" :class="{ winning: isTeamAWinner }">
                  <n-button
                    @click="adjustScore('a_games', -1)"
                    :disabled="modelValue.a_games <= 0"
                    circle
                    size="medium"
                    class="score-btn minus"
                  >
                    <n-icon :component="MinusIcon" />
                  </n-button>
                  <div class="score-display">
                    <span class="score-number">{{ modelValue.a_games }}</span>
                    <span class="score-label">局</span>
                  </div>
                  <n-button
                    @click="adjustScore('a_games', 1)"
                    :disabled="modelValue.a_games >= scoreInputMax"
                    circle
                    size="medium"
                    class="score-btn plus"
                  >
                    <n-icon :component="AddIcon" />
                  </n-button>
                </div>
              </div>
            </div>
          </div>

          <!-- VS 區域 -->
          <div class="vs-section">
            <div class="vs-circle">
              <span class="vs-text">VS</span>
            </div>
          </div>

          <!-- 隊伍 B -->
          <div class="team-section">
            <div class="team-card" :class="{ 'has-players': hasTeamBPlayers, 'winner-glow': isTeamBWinner }">
              <div class="team-header">
                <h3 class="team-title">隊伍 B</h3>
                <n-tag v-if="isTeamBWinner" type="success" round size="small">
                  <template #icon>
                    <n-icon :component="WinIcon" />
                  </template>
                  勝方
                </n-tag>
              </div>

              <!-- 球員3 (後排) -->
              <div class="player-slot">
                <n-button
                  v-if="!modelValue.player3_id"
                  dashed
                  block
                  @click="openPlayerSelector('player3_id')"
                  style="height: 3.5rem"
                  class="select-player-btn"
                >
                  <template #icon>
                    <n-icon :component="AddIcon" />
                  </template>
                  <div class="btn-content">
                    <div>選擇球員</div>
                    <div class="position-hint">後排</div>
                  </div>
                </n-button>
                <div v-else class="selected-player">
                  <div class="position-indicator-simple back-row">後排</div>
                  <div class="player-card-compact">
                    <n-avatar
                      :size="32"
                      :style="{
                        backgroundColor: getPlayerColor(modelValue.player3_id),
                        color: '#fff'
                      }"
                    >
                      {{ getPlayerInitial(getPlayerName(modelValue.player3_id)) }}
                    </n-avatar>
                    <div class="player-details">
                      <div class="player-name-compact">{{ getPlayerName(modelValue.player3_id) }}</div>
                      <div v-if="getPlayerOrganization(modelValue.player3_id)" class="player-org-compact">
                        {{ getPlayerOrganization(modelValue.player3_id) }}
                      </div>
                    </div>
                    <n-button size="small" quaternary circle @click="clearPlayer('player3_id')" class="remove-btn">
                      <n-icon :component="CloseIcon" />
                    </n-button>
                  </div>
                </div>
              </div>

              <!-- 球員4 (前排) - 只在雙打時顯示 -->
              <div v-if="modelValue.match_type === 'doubles'" class="player-slot">
                <n-button
                  v-if="!modelValue.player4_id"
                  dashed
                  block
                  @click="openPlayerSelector('player4_id')"
                  style="height: 3.5rem"
                  class="select-player-btn"
                >
                  <template #icon>
                    <n-icon :component="AddIcon" />
                  </template>
                  <div class="btn-content">
                    <div>選擇搭檔</div>
                    <div class="position-hint">前排</div>
                  </div>
                </n-button>
                <div v-else class="selected-player">
                  <div class="position-indicator-simple front-row">前排</div>
                  <div class="player-card-compact">
                    <n-avatar
                      :size="32"
                      :style="{
                        backgroundColor: getPlayerColor(modelValue.player4_id),
                        color: '#fff'
                      }"
                    >
                      {{ getPlayerInitial(getPlayerName(modelValue.player4_id)) }}
                    </n-avatar>
                    <div class="player-details">
                      <div class="player-name-compact">{{ getPlayerName(modelValue.player4_id) }}</div>
                      <div v-if="getPlayerOrganization(modelValue.player4_id)" class="player-org-compact">
                        {{ getPlayerOrganization(modelValue.player4_id) }}
                      </div>
                    </div>
                    <n-button size="small" quaternary circle @click="clearPlayer('player4_id')" class="remove-btn">
                      <n-icon :component="CloseIcon" />
                    </n-button>
                  </div>
                </div>
              </div>

              <!-- 隊伍B分數控制 -->
              <div class="score-controls">
                <div class="score-wrapper" :class="{ winning: isTeamBWinner }">
                  <n-button
                    @click="adjustScore('b_games', -1)"
                    :disabled="modelValue.b_games <= 0"
                    circle
                    size="medium"
                    class="score-btn minus"
                  >
                    <n-icon :component="MinusIcon" />
                  </n-button>
                  <div class="score-display">
                    <span class="score-number">{{ modelValue.b_games }}</span>
                    <span class="score-label">局</span>
                  </div>
                  <n-button
                    @click="adjustScore('b_games', 1)"
                    :disabled="modelValue.b_games >= scoreInputMax"
                    circle
                    size="medium"
                    class="score-btn plus"
                  >
                    <n-icon :component="AddIcon" />
                  </n-button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 可折疊的快速球員選擇 -->
    <n-divider style="margin-top: 2rem; margin-bottom: 1rem">
      <n-button text @click="showQuickSelection = !showQuickSelection" style="color: #666; font-size: 14px">
        <template #icon>
          <n-icon :component="showQuickSelection ? ChevronUpIcon : ChevronDownIcon" />
        </template>
        快速選擇球員
      </n-button>
    </n-divider>

    <n-collapse-transition :show="showQuickSelection">
      <div class="player-selection-area">
        <!-- 組織篩選控制 -->
        <div class="organization-controls mb-4">
          <div class="flex items-center gap-3">
            <n-select
              v-model:value="selectedOrganization"
              :options="organizationOptions"
              placeholder="選擇組織 (顯示全部)"
              clearable
              size="medium"
              style="min-width: 250px; flex: 1"
            />
            <n-button v-if="selectedOrganization" @click="selectedOrganization = null" quaternary size="medium">
              顯示全部
            </n-button>
          </div>
        </div>

        <!-- 球員網格 -->
        <div class="players-grid">
          <n-empty v-if="filteredPlayersByOrg.length === 0" description="沒有找到符合條件的球員" size="small" />

          <div
            v-for="player in filteredPlayersByOrg"
            :key="player.id"
            class="player-card-btn"
            :class="{
              selected: isPlayerSelected(player.id),
              disabled: isPlayerSelected(player.id)
            }"
            @click="quickSelectPlayer(player.id)"
          >
            <!-- 球員頭像 -->
            <n-avatar
              :size="40"
              :style="{
                backgroundColor: getPlayerColor(player.id),
                color: '#fff'
              }"
            >
              {{ getPlayerInitial(player.name) }}
            </n-avatar>

            <!-- 球員信息 -->
            <div class="player-info">
              <div class="player-name">
                {{ player.name }}
              </div>
              <div v-if="player.organization" class="player-org">
                {{ player.organization.short_name || player.organization.name }}
              </div>
              <div class="player-score">{{ Math.round(player.score || 1500) }} 分</div>
            </div>

            <!-- 選中指示器 -->
            <div v-if="isPlayerSelected(player.id)" class="selected-indicator">
              <n-icon :component="CheckIcon" size="16" />
            </div>
          </div>
        </div>
      </div>
    </n-collapse-transition>

    <!-- 球員選擇模態框 -->
    <n-modal
      v-model:show="showPlayerSelector"
      preset="card"
      title="選擇球員"
      style="width: 90%; max-width: 700px"
      :mask-closable="false"
    >
      <div class="modal-content">
        <n-tabs v-model:value="playerSelectorTab" type="segment" style="margin-bottom: 1rem">
          <!-- 現有球員選擇 -->
          <n-tab-pane name="existing" tab="選擇現有球員">
            <n-input
              v-model:value="modalSearchTerm"
              placeholder="搜尋球員姓名或組織..."
              clearable
              style="margin-bottom: 1.5rem"
              size="large"
            >
              <template #prefix>
                <n-icon :component="SearchIcon" />
              </template>
            </n-input>

            <n-grid :x-gap="16" :y-gap="16" cols="1 s:2 m:3 l:4" responsive="screen">
              <n-grid-item
                v-for="player in filteredPlayersForModal"
                :key="player.id"
                @click="selectPlayerFromModal(player.id)"
              >
                <div
                  class="player-card"
                  :class="{
                    selected: isPlayerSelected(player.id),
                    disabled: isPlayerSelected(player.id)
                  }"
                >
                  <n-avatar
                    round
                    :style="{
                      backgroundColor: getPlayerColor(player.id),
                      color: '#fff'
                    }"
                    size="large"
                  >
                    {{ getPlayerInitial(player.name) }}
                  </n-avatar>
                  <div class="player-card-info">
                    <div class="player-card-name">{{ player.name }}</div>
                    <div v-if="player.organization" class="player-card-org">
                      {{ player.organization.short_name || player.organization.name }}
                    </div>
                    <n-tag :type="getScoreTagType(player.score || 1500)" size="small"
                      >{{ Math.round(player.score || 1500) }}
                    </n-tag>
                  </div>
                  <!-- 已選中提示 -->
                  <div v-if="isPlayerSelected(player.id)" class="selected-overlay">
                    <n-icon :component="CheckIcon" size="24" />
                    <span>已選中</span>
                  </div>
                </div>
              </n-grid-item>
            </n-grid>
          </n-tab-pane>
          <n-tab-pane name="create-guest" tab="創建新訪客">
            <n-form ref="guestFormRef" :model="guestForm" :rules="guestRules" label-placement="top">
              <!-- 基本資訊 -->
              <n-card title="基本資訊" size="small" style="margin-bottom: 1rem">
                <n-grid :x-gap="16" :y-gap="16" cols="1 s:2">
                  <n-form-item-gi label="訪客姓名" path="name">
                    <n-input v-model:value="guestForm.name" placeholder="請輸入訪客姓名" :maxlength="20" show-count />
                  </n-form-item-gi>

                  <n-form-item-gi label="聯絡電話" path="phone">
                    <n-input v-model:value="guestForm.phone" placeholder="選填，方便聯絡" :maxlength="15" />
                  </n-form-item-gi>
                </n-grid>
              </n-card>

              <!-- 身份和歸屬 -->
              <n-card title="身份和歸屬" size="small" style="margin-bottom: 1rem">
                <n-grid :x-gap="16" :y-gap="16" cols="1 s:2">
                  <n-form-item-gi label="訪客身份" path="guest_role">
                    <n-select
                      v-model:value="guestForm.guest_role"
                      :options="guestRoleOptions"
                      placeholder="選擇訪客在比賽中的身份"
                    />
                  </n-form-item-gi>

                  <n-form-item-gi label="所屬組織" path="organization_id">
                    <n-select
                      v-model:value="guestForm.organization_id"
                      :options="organizationOptions"
                      placeholder="選擇訪客所屬組織（可選）"
                      clearable
                      filterable
                    />
                  </n-form-item-gi>
                </n-grid>
              </n-card>

              <!-- 備註說明 -->
              <n-card title="備註說明" size="small" style="margin-bottom: 1rem">
                <n-form-item label="備註" path="notes">
                  <n-input
                    v-model:value="guestForm.notes"
                    type="textarea"
                    placeholder="例如：來自XX學校、替補球員、首次合作等..."
                    :rows="3"
                    :maxlength="200"
                    show-count
                  />
                </n-form-item>
              </n-card>

              <!-- 操作按鈕 -->
              <n-space justify="end" style="margin-top: 1rem">
                <n-button @click="cancelGuestCreation">取消</n-button>
                <n-button type="primary" @click="createAndSelectGuest" :loading="creatingGuest"> 創建並選擇 </n-button>
              </n-space>
            </n-form>
          </n-tab-pane>

          <!-- 我的訪客記錄 -->
          <n-tab-pane name="my-guests" tab="我的訪客">
            <div style="margin-bottom: 1rem">
              <n-input v-model:value="myGuestsSearch" placeholder="搜尋我創建的訪客..." clearable>
                <template #prefix>
                  <n-icon :component="SearchIcon" />
                </template>
              </n-input>
            </div>

            <n-spin :show="loadingMyGuests">
              <n-list v-if="filteredMyGuests.length > 0" hoverable>
                <n-list-item
                  v-for="guest in filteredMyGuests"
                  :key="guest.id"
                  style="cursor: pointer; border-radius: 8px; margin-bottom: 8px"
                  :class="{ 'selected-guest': isPlayerSelected(guest.id) }"
                  @click="selectGuestFromHistory(guest.id)"
                >
                  <template #prefix>
                    <n-avatar round :style="{ backgroundColor: getPlayerColor(guest.id), color: '#fff' }">
                      {{ getPlayerInitial(guest.name) }}
                    </n-avatar>
                  </template>

                  <n-thing>
                    <template #header>
                      <n-space align="center">
                        {{ guest.name }}
                        <n-tag size="small" :type="getGuestRoleTagType(guest.guest_role)">
                          {{ guest.guest_role_display || '中性' }}
                        </n-tag>
                      </n-space>
                    </template>

                    <template #description>
                      <n-space>
                        <span v-if="guest.organization">
                          {{ guest.organization.short_name || guest.organization.name }}
                        </span>
                        <span style="color: #999"> 使用 {{ guest.usage_count || 0 }} 次 </span>
                        <span v-if="guest.last_used_at" style="color: #999">
                          最近：{{ formatDate(guest.last_used_at) }}
                        </span>
                      </n-space>
                    </template>

                    <div v-if="guest.guest_notes" style="margin-top: 4px; color: #666; font-size: 0.85rem">
                      {{ guest.guest_notes }}
                    </div>
                  </n-thing>

                  <template #suffix>
                    <div v-if="isPlayerSelected(guest.id)" style="color: #18a058">
                      <n-icon :component="CheckIcon" size="24" />
                    </div>
                  </template>
                </n-list-item>
              </n-list>

              <n-empty v-else description="尚未創建任何訪客" />
            </n-spin>
          </n-tab-pane>
        </n-tabs>
      </div>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showPlayerSelector = false">取消</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
  import { computed, onMounted, ref, watch } from 'vue'
  import { useMessage } from 'naive-ui'
  import apiClient from '@/services/apiClient' // Icons
  import {
    AddOutline as AddIcon,
    CheckmarkCircleOutline as WinIcon,
    CheckmarkOutline as CheckIcon,
    ChevronDownOutline as ChevronDownIcon,
    ChevronUpOutline as ChevronUpIcon,
    CloseOutline as CloseIcon,
    RemoveOutline as MinusIcon,
    SearchOutline as SearchIcon
  } from '@vicons/ionicons5' // Props

  // Props
  const props = defineProps({
    modelValue: {
      type: Object,
      required: true
    }
  })

  // Emits
  const emit = defineEmits(['update:modelValue'])

  // State
  const message = useMessage()
  const showQuickSelection = ref(false)
  const showPlayerSelector = ref(false)
  const currentSelectingField = ref(null)
  const modalSearchTerm = ref('')
  const selectedOrganization = ref(null)
  const allActiveMembers = ref([])
  const organizationOptions = ref([])
  const isChangingCourt = ref(false)
  const myGuestsList = ref([])
  const playerSelectorTab = ref('existing')
  const myGuestsSearch = ref('')
  const loadingMyGuests = ref(false)
  const creatingGuest = ref(false)
  const guestRoleOptions = ref([])
  const guestForm = ref({
    name: '',
    phone: '',
    guest_role: 'neutral',
    organization_id: null,
    notes: ''
  })
  const guestFormRef = ref(null)

  // Time slot config
  const timeSlotConfig = {
    morning: {
      label: '早上',
      icon: '🌅',
      next: 'afternoon'
    },
    afternoon: {
      label: '下午',
      icon: '☀️',
      next: 'evening'
    },
    evening: {
      label: '晚上',
      icon: '🌙',
      next: 'morning'
    }
  }

  // Computed properties
  const scoreInputMax = computed(() => {
    const formatMap = {
      games_5: 3,
      games_7: 4,
      games_9: 5
    }
    return formatMap[props.modelValue.match_format] || 2
  })

  const hasTeamAPlayers = computed(() => {
    return props.modelValue.player1_id && (props.modelValue.match_type === 'singles' || props.modelValue.player2_id)
  })

  const hasTeamBPlayers = computed(() => {
    return props.modelValue.player3_id && (props.modelValue.match_type === 'singles' || props.modelValue.player4_id)
  })

  const isTeamAWinner = computed(() => {
    const aGames = props.modelValue.a_games
    const bGames = props.modelValue.b_games
    const maxGames = scoreInputMax.value
    return aGames === maxGames && aGames > bGames
  })

  const isTeamBWinner = computed(() => {
    const aGames = props.modelValue.a_games
    const bGames = props.modelValue.b_games
    const maxGames = scoreInputMax.value
    return bGames === maxGames && bGames > aGames
  })

  const currentTimeSlot = computed(() => {
    return timeSlotConfig[props.modelValue.time_slot] || timeSlotConfig.morning
  })

  const courtClasses = computed(() => {
    const classes = ['match-arena']

    if (props.modelValue.court_surface) {
      classes.push(`court-${props.modelValue.court_surface}`)
    }

    if (props.modelValue.time_slot) {
      classes.push(`time-${props.modelValue.time_slot}`)
    }

    if (props.modelValue.court_environment) {
      classes.push(`env-${props.modelValue.court_environment}`)
    }

    return classes
  })

  const timeControllerClasses = computed(() => {
    const classes = ['time-controller']
    if (props.modelValue.time_slot) {
      classes.push(props.modelValue.time_slot)
    }
    return classes
  })

  const filteredPlayersByOrg = computed(() => {
    let players = allActiveMembers.value

    if (selectedOrganization.value) {
      players = players.filter(player => player.organization && player.organization.id === selectedOrganization.value)
    }

    return players.sort((a, b) => {
      const nameA = a.name || ''
      const nameB = b.name || ''
      return nameA.localeCompare(nameB)
    })
  })

  const filteredPlayersForModal = computed(() => {
    if (!modalSearchTerm.value) return allActiveMembers.value

    const searchTerm = modalSearchTerm.value.toLowerCase()

    return allActiveMembers.value.filter(player => {
      const playerName = (player.name || '').toLowerCase()
      const orgName = player.organization
        ? (player.organization.short_name || player.organization.name || '').toLowerCase()
        : ''

      return playerName.includes(searchTerm) || orgName.includes(searchTerm)
    })
  })

  // Methods
  const updateData = (field, value) => {
    emit('update:modelValue', {
      ...props.modelValue,
      [field]: value
    })
  }

  const updateScore = (field, value) => {
    updateData(field, value || 0)
  }

  const adjustScore = (field, delta) => {
    const currentValue = props.modelValue[field] || 0
    const newValue = currentValue + delta
    if (newValue >= 0 && newValue <= scoreInputMax.value) {
      updateData(field, newValue)
    }
  }

  const getPlayerName = playerId => {
    const player = allActiveMembers.value.find(p => p.id === playerId)
    return player ? player.name : '未知球員'
  }

  const getPlayerOrganization = playerId => {
    const player = allActiveMembers.value.find(p => p.id === playerId)
    return player?.organization ? player.organization.short_name || player.organization.name : ''
  }

  const getPlayerInitial = name => {
    if (!name) return '?'
    return name.charAt(0).toUpperCase()
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

  const isPlayerSelected = playerId => {
    return (
      props.modelValue.player1_id === playerId ||
      props.modelValue.player2_id === playerId ||
      props.modelValue.player3_id === playerId ||
      props.modelValue.player4_id === playerId
    )
  }

  const clearPlayer = field => {
    updateData(field, null)
  }

  const clearPlayerFromAll = playerId => {
    const updates = {}
    if (props.modelValue.player1_id === playerId) updates.player1_id = null
    if (props.modelValue.player2_id === playerId) updates.player2_id = null
    if (props.modelValue.player3_id === playerId) updates.player3_id = null
    if (props.modelValue.player4_id === playerId) updates.player4_id = null

    emit('update:modelValue', {
      ...props.modelValue,
      ...updates
    })
  }

  const quickSelectPlayer = playerId => {
    // 如果已經選中這個球員，提示用戶
    if (isPlayerSelected(playerId)) {
      message.warning('此球員已被選中，請選擇其他球員')
      return
    }

    // 找到第一個空位置
    if (!props.modelValue.player1_id) {
      updateData('player1_id', playerId)
    } else if (!props.modelValue.player3_id) {
      updateData('player3_id', playerId)
    } else if (props.modelValue.match_type === 'doubles' && !props.modelValue.player2_id) {
      updateData('player2_id', playerId)
    } else if (props.modelValue.match_type === 'doubles' && !props.modelValue.player4_id) {
      updateData('player4_id', playerId)
    } else {
      message.warning('所有位置都已選擇球員')
    }
  }

  const openPlayerSelector = field => {
    currentSelectingField.value = field
    modalSearchTerm.value = ''
    showPlayerSelector.value = true
  }

  const selectPlayerFromModal = playerId => {
    if (isPlayerSelected(playerId)) {
      message.warning('此球員已被選中，請選擇其他球員')
      return
    }

    if (currentSelectingField.value) {
      updateData(currentSelectingField.value, playerId)
    }
    showPlayerSelector.value = false
    currentSelectingField.value = null
  }

  const toggleTimeSlot = () => {
    const current = props.modelValue.time_slot || 'morning'
    updateData('time_slot', timeSlotConfig[current].next)
  }

  const triggerCourtAnimation = () => {
    isChangingCourt.value = true
    setTimeout(() => {
      isChangingCourt.value = false
    }, 600)
  }

  // API Methods
  const fetchActiveMembers = async () => {
    try {
      const response = await apiClient.get('/members', {
        params: {
          all: 'false',
          sort_by: 'name',
          sort_order: 'asc'
        }
      })

      let membersData = response.data
      if (response.data.members) {
        membersData = response.data.members
      } else if (response.data.data) {
        membersData = response.data.data
      }

      if (!Array.isArray(membersData)) {
        console.warn('球員數據不是數組:', membersData)
        membersData = []
      }

      allActiveMembers.value = membersData

      // 提取組織選項
      const orgMap = new Map()
      membersData.forEach(member => {
        if (member.organization) {
          const orgId = member.organization.id
          const orgLabel = member.organization.short_name || member.organization.name
          if (!orgMap.has(orgId)) {
            orgMap.set(orgId, {
              value: orgId,
              label: orgLabel,
              memberCount: 0
            })
          }
          orgMap.get(orgId).memberCount++
        }
      })

      organizationOptions.value = Array.from(orgMap.values())
        .map(org => ({
          value: org.value,
          label: `${org.label} (${org.memberCount}人)`
        }))
        .sort((a, b) => a.label.localeCompare(b.label))
    } catch (error) {
      console.error('獲取球員列表失敗:', error)
      message.error('獲取球員列表失敗。')
    }
  }

  const guestRules = {
    name: [
      { required: true, message: '請輸入訪客姓名', trigger: 'blur' },
      { min: 2, max: 20, message: '姓名長度應為2-20個字符', trigger: 'blur' }
    ],
    phone: [{ pattern: /^[0-9\-+\s()]*$/, message: '請輸入有效的電話號碼', trigger: 'blur' }],
    guest_role: [{ required: true, message: '請選擇訪客身份', trigger: 'change' }]
  }

  // 計算屬性
  const filteredMyGuests = computed(() => {
    if (!myGuestsSearch.value.trim()) {
      return myGuestsList.value
    }

    const searchTerm = myGuestsSearch.value.toLowerCase()
    return myGuestsList.value.filter(
      guest =>
        guest.name.toLowerCase().includes(searchTerm) ||
        (guest.organization?.name || '').toLowerCase().includes(searchTerm) ||
        (guest.guest_phone || '').includes(searchTerm) ||
        (guest.guest_notes || '').toLowerCase().includes(searchTerm)
    )
  })

  // 方法
  const loadGuestRoleOptions = async () => {
    try {
      const response = await apiClient.get('/members/guests/role-options')
      guestRoleOptions.value = response.data.options.map(option => ({
        value: option.value,
        label: `${option.label} - ${option.description}`
      }))
    } catch (error) {
      console.error('載入訪客身份選項失敗:', error)
      // 提供備用選項
      guestRoleOptions.value = [
        { value: 'teammate', label: '隊友 - 外出比賽的合作夥伴' },
        { value: 'opponent', label: '對手 - 記錄比賽的對戰對手' },
        { value: 'substitute', label: '替補 - 臨時替補球員' },
        { value: 'neutral', label: '中性 - 身份未明確' }
      ]
    }
  }

  const loadMyGuests = async () => {
    loadingMyGuests.value = true
    try {
      const response = await apiClient.get('/members/guests/search', {
        params: { limit: 50 }
      })
      myGuestsList.value = response.data.guests || []
    } catch (error) {
      console.error('載入我的訪客失敗:', error)
      message.error('載入訪客記錄失敗')
    } finally {
      loadingMyGuests.value = false
    }
  }

  const createAndSelectGuest = async () => {
    try {
      await guestFormRef.value?.validate()

      creatingGuest.value = true

      const response = await apiClient.post('/members/guests', guestForm.value)
      const newGuest = response.data.member

      // 添加到本地列表
      allActiveMembers.value.push(newGuest)
      myGuestsList.value.unshift(newGuest)

      // 自動選擇新創建的訪客
      if (currentSelectingField.value) {
        updateData(currentSelectingField.value, newGuest.id)
      }

      // 重置表單並關閉模態框
      resetGuestForm()
      showPlayerSelector.value = false
      currentSelectingField.value = null

      message.success(`訪客 "${newGuest.name}" 創建成功！`)
    } catch (error) {
      console.error('創建訪客失敗:', error)
      message.error(error.response?.data?.message || '創建訪客失敗')
    } finally {
      creatingGuest.value = false
    }
  }

  const selectGuestFromHistory = guestId => {
    if (isPlayerSelected(guestId)) {
      message.warning('此球員已被選中，請選擇其他球員')
      return
    }

    if (currentSelectingField.value) {
      updateData(currentSelectingField.value, guestId)

      // 更新使用記錄
      const guest = myGuestsList.value.find(g => g.id === guestId)
      if (guest) {
        guest.usage_count = (guest.usage_count || 0) + 1
        guest.last_used_at = new Date().toISOString()
      }
    }

    showPlayerSelector.value = false
    currentSelectingField.value = null
  }

  const cancelGuestCreation = () => {
    resetGuestForm()
    playerSelectorTab.value = 'existing'
  }

  const resetGuestForm = () => {
    guestForm.value = {
      name: '',
      phone: '',
      guest_role: 'neutral',
      organization_id: null,
      notes: ''
    }
  }

  const getGuestRoleTagType = role => {
    const typeMap = {
      teammate: 'success',
      opponent: 'warning',
      substitute: 'info',
      neutral: 'default'
    }
    return typeMap[role] || 'default'
  }

  const formatDate = dateString => {
    return new Date(dateString).toLocaleDateString('zh-TW')
  }

  // Watchers
  watch(
    [() => props.modelValue.court_surface, () => props.modelValue.court_environment, () => props.modelValue.time_slot],
    () => {
      triggerCourtAnimation()
    }
  )

  watch(showPlayerSelector, show => {
    if (show) {
      loadMyGuests()
      loadGuestRoleOptions()
    }
  })

  // 重置頁籤當模態框關閉時
  watch(showPlayerSelector, show => {
    if (!show) {
      playerSelectorTab.value = 'existing'
    }
  })

  // Lifecycle
  onMounted(() => {
    fetchActiveMembers()
  })
</script>

<style scoped>
  @import '@/assets/css/match-player-selector.css';

  .position-indicator-simple {
    position: absolute;
    top: -8px;
    left: -4px;
    z-index: 15;
    padding: 0.3rem 0.6rem;
    border-radius: 6px;
    font-size: 0.7rem;
    font-weight: 700;
    color: #1f2937;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    transform: scale(0.9);
    white-space: nowrap;
    line-height: 1;
    text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
  }

  .position-indicator-simple.back-row {
    background: linear-gradient(45deg, #fef3c7, #fcd34d);
    border: 1px solid #f59e0b;
    color: #92400e;
  }

  .position-indicator-simple.front-row {
    background: linear-gradient(45deg, #dbeafe, #93c5fd);
    border: 1px solid #3b82f6;
    color: #1e40af;
  }

  .position-indicator-simple.back-row-alt {
    background: #fed7d7;
    border: 1px solid #f56565;
    color: #c53030;
  }

  .position-indicator-simple.front-row-alt {
    background: #bee3f8;
    border: 1px solid #4299e1;
    color: #2b6cb0;
  }

  .score-controls {
    margin-top: 1rem;
  }

  .score-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    background: #ffffff;
    border: 2px solid #e5e7eb;
    border-radius: 12px;
    padding: 1rem;
  }

  .score-display {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
    min-width: 60px;
    justify-content: center;
  }

  .score-number {
    font-size: 2rem;
    font-weight: 700;
    color: #1f2937;
    transition: all 0.3s ease;
  }

  .score-label {
    font-size: 0.9rem;
    color: #6b7280;
    font-weight: 600;
  }

  .score-btn {
    flex-shrink: 0;
    transition: all 0.3s ease;
    width: 36px;
    height: 36px;
    border: 2px solid;
    font-weight: 600;
  }

  .score-btn:hover:not(:disabled) {
    transform: scale(1.1);
  }

  .score-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .score-btn.minus {
    background: #ffffff;
    border-color: #ef4444;
    color: #ef4444;
  }

  .score-btn.minus:hover:not(:disabled) {
    background: #ef4444;
    color: #ffffff;
  }

  .score-btn.plus {
    background: #3b82f6;
    border-color: #3b82f6;
    color: #ffffff;
  }

  .score-btn.plus:hover:not(:disabled) {
    background: #2563eb;
    border-color: #2563eb;
  }

  .score-wrapper.winning .score-number {
    color: #059669;
    text-shadow: 0 0 10px rgba(5, 150, 105, 0.3);
  }

  .score-wrapper.winning {
    border-color: #10b981;
    background: #f0fdf4;
  }

  .modal-content {
    padding: 1rem;
  }

  .player-card-btn.disabled,
  .player-card.disabled {
    opacity: 0.6;
    cursor: not-allowed;
    pointer-events: none;
  }

  .player-card.disabled {
    position: relative;
    overflow: hidden;
  }

  .selected-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(16, 185, 129, 0.9);
    color: white;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 600;
    gap: 0.25rem;
  }

  .selected-player {
    position: relative;
    padding-top: 8px;
  }

  .player-card-compact {
    margin-top: 4px;
  }

  @media (max-width: 768px) {
    .position-indicator-simple {
      top: -6px;
      left: -2px;
      padding: 0.25rem 0.5rem;
      font-size: 0.65rem;
      transform: scale(0.85);
    }

    .score-wrapper {
      gap: 0.75rem;
      padding: 0.75rem;
    }

    .score-number {
      font-size: 1.75rem;
    }

    .score-btn {
      width: 32px;
      height: 32px;
    }
  }

  .selected-guest {
    background-color: #f0fdf4;
    border: 1px solid #10b981;
  }

  .player-card.selected {
    border-color: #10b981;
    background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);
  }

  .selected-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(16, 185, 129, 0.9);
    color: white;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 600;
    gap: 0.25rem;
  }
</style>
