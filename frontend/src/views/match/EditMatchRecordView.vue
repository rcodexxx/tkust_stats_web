<template>
  <div class="record-match-page container-fluid mt-4 mb-5 px-md-4">
    <!-- 載入狀態 -->
    <n-spin :show="loading" style="width: 100%">
      <n-card :bordered="false" class="form-card">
        <!-- 頁面標題 -->
        <div class="page-header mb-4">
          <n-button @click="goBack" quaternary circle style="margin-right: 1rem">
            <template #icon>
              <n-icon :component="ArrowLeftIcon" />
            </template>
          </n-button>
          <h1 class="page-title">編輯比賽記錄 #{{ recordId }}</h1>
        </div>

        <!-- 表單內容 -->
        <n-form
          ref="formRef"
          :model="matchForm"
          :rules="formRules"
          label-placement="top"
          @submit.prevent="handleUpdateMatch"
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

          <!-- 球員選擇區域 - 使用組件 -->
          <n-divider style="margin-top: 2rem; margin-bottom: 2rem">
            <n-text style="font-size: 14px; color: #666">球員設定</n-text>
          </n-divider>

          <MatchPlayerSelector ref="playerSelectorRef" v-model="matchForm" />

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
                      :max="180"
                      clearable
                      size="medium"
                      style="width: 100%"
                    />
                  </n-form-item-gi>

                  <n-form-item-gi label="YouTube 網址" path="youtube_url">
                    <n-input
                      v-model:value="matchForm.youtube_url"
                      placeholder="https://www.youtube.com/watch?v=..."
                      clearable
                      size="medium"
                    />
                  </n-form-item-gi>
                </n-grid>
              </div>

              <!-- 比賽備註 -->
              <div class="settings-section">
                <n-form-item label="比賽備註" path="match_notes">
                  <n-input
                    v-model:value="matchForm.match_notes"
                    type="textarea"
                    placeholder="記錄比賽中的特殊事件、精彩表現或其他備註..."
                    :rows="3"
                    size="medium"
                  />
                </n-form-item>
              </div>
            </div>
          </n-collapse-transition>

          <!-- 操作按鈕 -->
          <n-divider style="margin-top: 2rem; margin-bottom: 2rem" />
          <n-space justify="space-between" style="width: 100%">
            <n-button @click="goBack" size="large">
              <template #icon>
                <n-icon :component="ArrowLeftIcon" />
              </template>
              返回
            </n-button>
            <n-space>
              <n-button @click="resetForm" size="large">
                <template #icon>
                  <n-icon :component="RefreshIcon" />
                </template>
                重置
              </n-button>
              <n-button
                type="primary"
                size="large"
                :loading="submitting"
                :disabled="!canSubmit"
                @click="handleUpdateMatch"
              >
                <template #icon>
                  <n-icon :component="SaveIcon" />
                </template>
                更新比賽記錄
              </n-button>
            </n-space>
          </n-space>
        </n-form>
      </n-card>
    </n-spin>
  </div>
</template>

<script setup>
  import { computed, ref, watch, onMounted, nextTick } from 'vue'
  import { useRouter, useRoute } from 'vue-router'
  import { useMessage } from 'naive-ui'
  import apiClient from '@/services/apiClient'
  import MatchPlayerSelector from '@/components/MatchPlayerSelector.vue'

  // Icons
  import {
    ArrowBackOutline as ArrowLeftIcon,
    ChevronDownOutline as ChevronDownIcon,
    ChevronUpOutline as ChevronUpIcon,
    RefreshOutline as RefreshIcon,
    SaveOutline as SaveIcon
  } from '@vicons/ionicons5'

  const router = useRouter()
  const route = useRoute()
  const message = useMessage()

  // State
  const loading = ref(true)
  const submitting = ref(false)
  const showAdvancedSettings = ref(false)
  const formRef = ref(null)
  const recordId = ref(route.params.id)
  const playerSelectorRef = ref(null)

  // Form data
  const matchForm = ref({
    match_date_ts: null,
    match_date: '',
    match_type: 'doubles',
    match_format: 'games_9',
    player1_id: null,
    player2_id: null,
    player3_id: null,
    player4_id: null,
    a_games: 0,
    b_games: 0,
    match_notes: '',
    court_surface: null,
    court_environment: null,
    time_slot: null,
    total_points: null,
    duration_minutes: null,
    youtube_url: ''
  })

  // Options
  const matchTypeOptions = [
    { label: '單打', value: 'singles' },
    { label: '雙打', value: 'doubles' }
  ]

  const matchFormatOptions = [
    { label: '五局制', value: 'games_5' },
    { label: '七局制', value: 'games_7' },
    { label: '九局制', value: 'games_9' }
  ]

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

  // Form rules
  const formRules = {
    match_date: [{ required: true, message: '請選擇比賽日期', trigger: 'change' }],
    match_type: [{ required: true, message: '請選擇比賽類型', trigger: 'change' }],
    match_format: [{ required: true, message: '請選擇賽制', trigger: 'change' }],
    player1_id: [{ required: true, message: '請選擇球員1', trigger: 'change' }],
    player3_id: [{ required: true, message: '請選擇球員3', trigger: 'change' }]
  }

  // Computed properties
  const scoreInputMax = computed(() => {
    const formatMap = {
      games_5: 3,
      games_7: 4,
      games_9: 5
    }
    return formatMap[matchForm.value.match_format] || 5
  })

  const canSubmit = computed(() => {
    const form = matchForm.value

    // 基本必填檢查
    if (!form.player1_id || !form.player3_id) {
      return false
    }

    // 雙打模式需要四個球員
    if (form.match_type === 'doubles' && (!form.player2_id || !form.player4_id)) {
      return false
    }

    // 比賽必須有勝負
    const maxGames = scoreInputMax.value
    return (
      (form.a_games === maxGames && form.a_games > form.b_games) ||
      (form.b_games === maxGames && form.b_games > form.a_games)
    )
  })

  // 🔧 載入比賽記錄相關球員的方法
  const loadMatchPlayers = async (playerIds) => {
    try {
      // 過濾掉空值
      const validPlayerIds = playerIds.filter(id => id !== null && id !== undefined)

      if (validPlayerIds.length === 0) {
        return
      }

      console.log('載入比賽相關球員:', validPlayerIds)

      // 為每個球員ID獲取詳細信息
      const playerPromises = validPlayerIds.map(async (playerId) => {
        try {
          const response = await apiClient.get(`/members/${playerId}`)
          return response.data.member || response.data
        } catch (error) {
          console.warn(`無法載入球員 ${playerId}:`, error)
          return null
        }
      })

      const players = await Promise.all(playerPromises)
      const validPlayers = players.filter(player => player !== null)

      console.log('成功載入球員信息:', validPlayers)

      // 通知 MatchPlayerSelector 組件新增這些球員
      if (playerSelectorRef.value && validPlayers.length > 0) {
        await nextTick()
        // 調用組件的方法來添加球員
        if (typeof playerSelectorRef.value.addPlayersToList === 'function') {
          playerSelectorRef.value.addPlayersToList(validPlayers)
        }
      }

    } catch (error) {
      console.error('載入比賽球員失敗:', error)
    }
  }

  // API Methods
  const fetchMatchRecord = async () => {
    try {
      loading.value = true
      console.log('正在載入比賽記錄 ID:', recordId.value)

      const response = await apiClient.get(`/match-records/${recordId.value}`)
      console.log('完整 API 響應:', response.data)

      // 🔧 正確的數據結構解析
      const record = response.data.match_record || response.data.record || response.data
      console.log('解析後的比賽記錄:', record)

      if (!record) {
        throw new Error('沒有收到比賽記錄數據')
      }

      // 處理日期
      let matchDate = null
      if (record.match_date) {
        try {
          matchDate = new Date(record.match_date).getTime()
          if (isNaN(matchDate)) {
            console.warn('日期格式無效:', record.match_date)
            matchDate = null
          }
        } catch (e) {
          console.warn('日期解析失敗:', record.match_date, e)
          matchDate = null
        }
      }

      // 🔧 正確填充表單數據，處理球員對象結構
      matchForm.value = {
        match_date_ts: matchDate,
        match_date: record.match_date || '',
        match_type: record.match_type || 'doubles',
        match_format: record.match_format || 'games_9',
        // 🔧 正確處理球員ID - 支持直接ID和對象結構
        player1_id: record.player1?.id || record.player1_id || null,
        player2_id: record.player2?.id || record.player2_id || null,
        player3_id: record.player3?.id || record.player3_id || null,
        player4_id: record.player4?.id || record.player4_id || null,
        a_games: record.a_games || 0,
        b_games: record.b_games || 0,
        match_notes: record.match_notes || '',
        court_surface: record.court_surface || null,
        court_environment: record.court_environment || null,
        time_slot: record.time_slot || null,
        total_points: record.total_points || null,
        duration_minutes: record.duration_minutes || null,
        youtube_url: record.youtube_url || ''
      }

      console.log('填充後的表單數據:', matchForm.value)

      // 🔧 載入完比賽數據後，確保相關球員信息也已載入
      await nextTick()

      const playerIds = [
        matchForm.value.player1_id,
        matchForm.value.player2_id,
        matchForm.value.player3_id,
        matchForm.value.player4_id
      ].filter(id => id !== null && id !== undefined)

      if (playerIds.length > 0) {
        await loadMatchPlayers(playerIds)
      }

    } catch (error) {
      console.error('載入比賽記錄失敗:', error)
      const errorMsg = error.response?.data?.message || error.message || '載入比賽記錄失敗'
      message.error(`載入比賽記錄失敗: ${errorMsg}`)

      // 如果是 404 錯誤，給出更具體的提示
      if (error.response?.status === 404) {
        message.error(`找不到 ID 為 ${recordId.value} 的比賽記錄`)
      }

      // 延遲跳轉，讓用戶看到錯誤訊息
      setTimeout(() => {
        router.push({ name: 'MatchManagement' })
      }, 2000)
    } finally {
      loading.value = false
    }
  }

  const handleUpdateMatch = async () => {
    try {
      const valid = await formRef.value?.validate()
      if (!valid) {
        message.error('請修正表單中的錯誤。')
        return
      }
    } catch (e) {
      message.error('請修正表單中的錯誤。')
      return
    }

    const gamesToWin = scoreInputMax.value
    if (matchForm.value.a_games < gamesToWin && matchForm.value.b_games < gamesToWin) {
      message.error(`比賽尚未結束，需要有一方達到 ${gamesToWin} 局才能儲存。`)
      return
    }
    if (matchForm.value.a_games === matchForm.value.b_games) {
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
        match_date: formatDate(matchForm.value.match_date_ts) || matchForm.value.match_date,
        match_type: matchForm.value.match_type,
        match_format: matchForm.value.match_format,
        player1_id: matchForm.value.player1_id,
        player2_id: matchForm.value.match_type === 'doubles' ? matchForm.value.player2_id : null,
        player3_id: matchForm.value.player3_id,
        player4_id: matchForm.value.match_type === 'doubles' ? matchForm.value.player4_id : null,
        a_games: matchForm.value.a_games,
        b_games: matchForm.value.b_games,
        match_notes: matchForm.value.match_notes || null,
        court_surface: matchForm.value.court_surface || null,
        court_environment: matchForm.value.court_environment || null,
        time_slot: matchForm.value.time_slot || null,
        total_points: matchForm.value.total_points || null,
        duration_minutes: matchForm.value.duration_minutes || null,
        youtube_url: matchForm.value.youtube_url || null
      }

      console.log('發送更新請求:', payload)

      const response = await apiClient.put(`/match-records/${recordId.value}`, payload)
      console.log('更新響應:', response.data)

      message.success(response.data.message || '比賽記錄已成功更新！')

      setTimeout(() => {
        router.push({ name: 'MatchManagement' })
      }, 1500)
    } catch (err) {
      console.error('更新失敗詳細信息:', {
        error: err,
        response: err.response?.data,
        status: err.response?.status,
        statusText: err.response?.statusText
      })

      const errorData = err.response?.data
      let errorMessage = '更新失敗，請稍後再試。'

      if (errorData?.details) {
        errorMessage = '輸入數據有誤：\n' + Object.values(errorData.details).flat().join('\n')
        message.error(errorMessage, { duration: 7000, closable: true })
      } else if (errorData?.message) {
        errorMessage = errorData.message
        message.error(errorMessage)
      } else if (err.response?.status === 404) {
        errorMessage = '找不到要更新的比賽記錄'
        message.error(errorMessage)
      } else if (err.response?.status === 403) {
        errorMessage = '您沒有權限更新此比賽記錄'
        message.error(errorMessage)
      } else {
        message.error(errorMessage)
      }
    } finally {
      submitting.value = false
    }
  }

  const resetForm = async () => {
    try {
      await fetchMatchRecord()
      message.info('表單已重置為原始數據')
    } catch (error) {
      message.error('重置失敗，請重新載入頁面')
    }
  }

  const goBack = () => {
    router.push({ name: 'MatchManagement' })
  }

  // Watchers
  watch(
    [() => matchForm.value.a_games, () => matchForm.value.b_games, () => matchForm.value.match_format],
    () => {
      const gamesToWin = scoreInputMax.value
      const gamesA = matchForm.value.a_games
      const gamesB = matchForm.value.b_games

      if (gamesA === gamesToWin && gamesA > gamesB) {
        matchForm.value.side_a_outcome = 'WIN'
      } else if (gamesB === gamesToWin && gamesB > gamesA) {
        matchForm.value.side_a_outcome = 'LOSS'
      } else {
        matchForm.value.side_a_outcome = ''
      }
    },
    { deep: true }
  )

  watch(
    () => matchForm.value.match_type,
    newType => {
      if (newType === 'singles') {
        matchForm.value.player2_id = null
        matchForm.value.player4_id = null
      }
    }
  )

  // 🔧 監聽球員變化，確保新選擇的球員信息已載入
  watch(
    [
      () => matchForm.value.player1_id,
      () => matchForm.value.player2_id,
      () => matchForm.value.player3_id,
      () => matchForm.value.player4_id
    ],
    async (newPlayerIds, oldPlayerIds) => {
      // 檢查是否有新的球員被選擇
      const newIds = newPlayerIds.filter((id, index) => id !== oldPlayerIds?.[index] && id !== null)

      if (newIds.length > 0) {
        await loadMatchPlayers(newIds)
      }
    },
    { deep: true }
  )

  // Lifecycle
  onMounted(async () => {
    await fetchMatchRecord()
  })
</script>

<style scoped>
  /* 頁面容器 */
  .record-match-page {
    background: #f5f5f5;
    min-height: 100vh;
  }

  .form-card {
    background: rgba(255, 255, 255, 0.98);
    backdrop-filter: blur(15px);
    border-radius: 16px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
    padding: 2rem;
    border: 1px solid #e9ecef;
  }

  /* 頁面標題 */
  .page-header {
    display: flex;
    align-items: center;
    margin-bottom: 2rem;
    padding: 1rem 0;
    border-bottom: 1px solid #e9ecef;
  }

  .page-title {
    margin: 0;
    color: #2c3e50;
    font-size: 1.8rem;
    font-weight: 600;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  /* 進階設定容器 */
  .advanced-settings-container {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 16px;
    padding: 2rem;
    margin-top: 1rem;
    border: 1px solid #dee2e6;
    position: relative;
    overflow: hidden;
  }

  .advanced-settings-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  }

  /* 設定區塊 */
  .settings-section {
    margin-bottom: 1.5rem;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.7);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.3);
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
  }

  .settings-section:hover {
    background: rgba(255, 255, 255, 0.9);
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  }

  .settings-section:last-child {
    margin-bottom: 0;
  }

  /* 響應式調整 */
  @media (max-width: 768px) {
    .page-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }

    .page-title {
      font-size: 1.5rem;
    }

    .advanced-settings-container {
      padding: 1rem;
    }
  }
</style>