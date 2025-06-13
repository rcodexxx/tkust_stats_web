<template>
  <div class="match-management-page container mt-4 mb-5 px-md-4">
    <n-h1 class="page-main-title">比賽記錄管理</n-h1>

    <!-- 頁面操作按鈕 -->
    <div class="page-actions mb-4">
      <n-space>
        <n-button type="primary" size="medium" @click="goToRecordMatchPage">
          <template #icon>
            <n-icon :component="AddIcon" />
          </template>
          記錄新比賽
        </n-button>
        <n-button @click="handleRefreshData" :loading="loading">
          <template #icon>
            <n-icon :component="RefreshIcon" />
          </template>
          重新整理
        </n-button>
      </n-space>
    </div>

    <!-- 進階搜尋區域 -->
    <div class="search-section">
      <div class="search-header">
        <n-button @click="toggleSearchPanel" :type="searchPanelVisible ? 'primary' : 'default'">
          <template #icon>
            <n-icon :component="searchPanelVisible ? ChevronUpIcon : SearchIcon" />
          </template>
          {{ searchPanelVisible ? '收起搜尋' : '進階搜尋' }}
          <span v-if="activeFiltersCount > 0" class="filter-count">
            {{ activeFiltersCount }}
          </span>
        </n-button>
      </div>

      <!-- 搜尋面板 -->
      <n-collapse-transition :show="searchPanelVisible">
        <div class="search-panel">
          <n-form ref="searchFormRef" :model="searchForm" label-placement="left" label-width="100" size="small">
            <n-grid :cols="24" :x-gap="16" :y-gap="12">
              <!-- 球員搜尋 -->
              <n-form-item-gi :span="12" label="球員">
                <n-select
                  v-model:value="searchForm.player_ids"
                  :options="playerOptions"
                  multiple
                  filterable
                  clearable
                  placeholder="選擇或搜尋球員"
                  :loading="playersLoading"
                  @search="handlePlayerSearch"
                  @update:value="handleFormChange"
                />
              </n-form-item-gi>

              <!-- 位置 -->
              <n-form-item-gi :span="12" label="位置">
                <n-select
                  v-model:value="searchForm.player_position"
                  :options="positionOptions"
                  clearable
                  placeholder="選擇位置"
                  @update:value="handleFormChange"
                  :disabled="!searchForm.player_ids || searchForm.player_ids.length === 0"
                />
              </n-form-item-gi>

              <!-- 比賽類型 -->
              <n-form-item-gi :span="8" label="類型">
                <n-select
                  v-model:value="searchForm.match_type"
                  :options="matchTypeOptions"
                  clearable
                  placeholder="選擇類型"
                  @update:value="handleFormChange"
                />
              </n-form-item-gi>

              <!-- 賽制 -->
              <n-form-item-gi :span="8" label="賽制">
                <n-select
                  v-model:value="searchForm.match_format"
                  :options="matchFormatOptions"
                  clearable
                  placeholder="選擇賽制"
                  @update:value="handleFormChange"
                />
              </n-form-item-gi>

              <!-- 勝方 -->
              <n-form-item-gi :span="8" label="勝方">
                <n-select
                  v-model:value="searchForm.winner_side"
                  :options="winnerOptions"
                  clearable
                  placeholder="選擇勝方"
                  @update:value="handleFormChange"
                />
              </n-form-item-gi>

              <!-- 日期範圍 -->
              <n-form-item-gi :span="12" label="日期範圍">
                <n-date-picker
                  v-model:value="searchForm.dateRange"
                  type="daterange"
                  clearable
                  format="yyyy-MM-dd"
                  placeholder="選擇日期範圍"
                  style="width: 100%"
                  @update:value="handleFormChange"
                />
              </n-form-item-gi>

              <!-- 分數差距 -->
              <n-form-item-gi :span="12" label="分數差距">
                <n-input-group>
                  <n-input-number
                    v-model:value="searchForm.min_score_diff"
                    placeholder="最小"
                    :min="0"
                    :max="20"
                    style="width: 50%"
                    @update:value="handleFormChange"
                  />
                  <n-input-number
                    v-model:value="searchForm.max_score_diff"
                    placeholder="最大"
                    :min="0"
                    :max="20"
                    style="width: 50%"
                    @update:value="handleFormChange"
                  />
                </n-input-group>
              </n-form-item-gi>
            </n-grid>

            <!-- 搜尋按鈕 -->
            <div class="search-actions">
              <n-space>
                <n-button type="primary" @click="handleSearch" :loading="searching">
                  <template #icon>
                    <n-icon :component="SearchIcon" />
                  </template>
                  搜尋
                </n-button>
                <n-button @click="handleResetSearch">
                  <template #icon>
                    <n-icon :component="RefreshIcon" />
                  </template>
                  重置
                </n-button>
                <n-button @click="handleExport" v-if="searchExecuted && displayRecords.length > 0">
                  <template #icon>
                    <n-icon :component="DownloadIcon" />
                  </template>
                  匯出結果
                </n-button>
              </n-space>
            </div>
          </n-form>
        </div>
      </n-collapse-transition>

      <!-- 活躍篩選條件 -->
      <div v-if="activeFilters.length > 0" class="active-filters">
        <n-space size="small" align="center">
          <span class="filter-label">篩選條件:</span>
          <n-tag
            v-for="filter in activeFilters"
            :key="filter.key"
            closable
            @close="removeFilter(filter.key)"
            type="info"
            size="small"
          >
            {{ filter.label }}
          </n-tag>
          <n-button size="tiny" text @click="handleResetSearch">清除全部</n-button>
        </n-space>
      </div>

      <!-- 搜尋結果統計 -->
      <div v-if="searchExecuted" class="search-stats">
        <n-space justify="space-between" align="center">
          <span class="search-info">
            找到 {{ totalResults }} 筆記錄
            <span v-if="activeFiltersCount > 0" class="filter-info">
              (已套用 {{ activeFiltersCount }} 個篩選條件)
            </span>
          </span>
        </n-space>
      </div>
    </div>

    <!-- 錯誤提示 -->
    <div v-if="fetchError" class="mb-3">
      <n-alert title="錯誤" type="error" closable @close="fetchError = null">
        {{ fetchError }}
      </n-alert>
    </div>

    <!-- 比賽記錄表格 -->
    <n-data-table
      :columns="tableColumns"
      :data="displayRecords"
      :loading="loading"
      :pagination="paginationConfig"
      :bordered="false"
      :bottom-bordered="true"
      :single-line="false"
      size="small"
      flex-height
      style="min-height: 400px; max-height: 75vh"
      :scroll-x="1200"
      :row-key="row => row.id"
    />

    <!-- 空狀態 -->
    <n-empty v-if="!loading && displayRecords.length === 0" description="沒有找到比賽記錄" style="margin: 2rem 0">
      <template #extra>
        <n-button type="primary" @click="goToRecordMatchPage"> 新增第一場比賽 </n-button>
      </template>
    </n-empty>
  </div>
</template>

<script setup>
import { computed, h, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  NAlert,
  NButton,
  NCollapseTransition,
  NDataTable,
  NDatePicker,
  NEmpty,
  NForm,
  NFormItemGi,
  NGrid,
  NH1,
  NIcon,
  NInputGroup,
  NInputNumber,
  NSelect,
  NSpace,
  NTag,
  NTooltip,
  useDialog,
  useMessage
} from 'naive-ui'
import {
  AddCircleOutline as AddIcon,
  ChevronUpOutline as ChevronUpIcon,
  DownloadOutline as DownloadIcon,
  PencilOutline as EditIcon,
  RefreshOutline as RefreshIcon,
  SearchOutline as SearchIcon,
  TrashBinOutline as DeleteIcon
} from '@vicons/ionicons5'
import apiClient from '@/services/apiClient.js'
import { format } from 'date-fns'

// Hooks
  const router = useRouter()
  const dialog = useDialog()
  const message = useMessage()

  // 基本狀態
  const loading = ref(true)
  const searching = ref(false)
  const playersLoading = ref(false)
  const searchExecuted = ref(false)
  const searchPanelVisible = ref(false)
  const fetchError = ref(null)

  // 數據狀態
  const allMatchRecords = ref([])
  const displayRecords = ref([])
  const totalResults = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(15)
  const playerOptions = ref([])

  // 搜尋表單
  const searchForm = reactive({
    player_ids: [],
    player_position: null,
    match_type: null,
    match_format: null,
    win_loss: null, // 改為 win_loss，基於選中球員的勝負
    dateRange: null,
    min_score_diff: null,
    max_score_diff: null
  })

  // 分頁設定
  const pagination = reactive({
    page: 1,
    pageSize: 15,
    showSizePicker: true,
    pageSizes: [15, 30, 50, 100]
  })

  // 選項配置
  const positionOptions = [
    { label: '前排', value: 'front' },
    { label: '後排', value: 'back' },
    { label: '任意位置', value: 'any' }
  ]

  const matchTypeOptions = [
    { label: '雙打', value: 'doubles' },
    { label: '單打', value: 'singles' }
  ]

  const matchFormatOptions = [
    { label: '五局制', value: 'games_5' },
    { label: '七局制', value: 'games_7' },
    { label: '九局制', value: 'games_9' }
  ]

  const winnerOptions = [
    { label: '勝', value: 'win' },
    { label: '負', value: 'loss' }
  ]

  // 輔助函數
  const getMatchTypeDisplay = value => matchTypeOptions.find(opt => opt.value === value)?.label || value
  const getMatchFormatDisplay = value => matchFormatOptions.find(opt => opt.value === value)?.label || value

  // 🔧 高亮球員名字的輔助函數
  const renderPlayerNameWithHighlight = playerName => {
    if (!playerName) return '-'

    // 如果沒有搜尋球員，直接返回名稱
    if (!searchedPlayerNames.value || searchedPlayerNames.value.length === 0) {
      return playerName
    }

    // 檢查是否有搜尋的球員名稱需要高亮
    const matchedSearchTerm = searchedPlayerNames.value.find(searchName =>
      playerName.toLowerCase().includes(searchName.toLowerCase())
    )

    if (matchedSearchTerm) {
      // 創建高亮的 HTML
      const escapeRegExp = string => string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      const regex = new RegExp(`(${escapeRegExp(matchedSearchTerm)})`, 'gi')
      const highlightedHTML = playerName.replace(regex, '<mark class="search-highlight">$1</mark>')

      // 返回包含 HTML 的 span 元素
      return h('span', {
        innerHTML: highlightedHTML
      })
    }

    return playerName
  }

  // 計算屬性
  const activeFilters = computed(() => {
    const filters = []

    if (searchForm.player_ids?.length > 0) {
      const playerNames = searchForm.player_ids
        .map(id => playerOptions.value.find(p => p.value === id)?.label || id)
        .join(', ')
      filters.push({ key: 'player_ids', label: `球員: ${playerNames}` })
    }

    if (searchForm.player_position) {
      const positionLabel = positionOptions.find(p => p.value === searchForm.player_position)?.label
      filters.push({ key: 'player_position', label: `位置: ${positionLabel}` })
    }

    if (searchForm.match_type) {
      const typeLabel = matchTypeOptions.find(t => t.value === searchForm.match_type)?.label
      filters.push({ key: 'match_type', label: `類型: ${typeLabel}` })
    }

    if (searchForm.match_format) {
      const formatLabel = matchFormatOptions.find(f => f.value === searchForm.match_format)?.label
      filters.push({ key: 'match_format', label: `賽制: ${formatLabel}` })
    }

    if (searchForm.win_loss) {
      const winLossLabel = winnerOptions.find(w => w.value === searchForm.win_loss)?.label
      filters.push({ key: 'win_loss', label: `勝負: ${winLossLabel}` })
    }

    if (searchForm.dateRange?.length === 2) {
      const [start, end] = searchForm.dateRange
      const startDate = new Date(start).toLocaleDateString()
      const endDate = new Date(end).toLocaleDateString()
      filters.push({ key: 'dateRange', label: `日期: ${startDate} ~ ${endDate}` })
    }

    if (searchForm.min_score_diff !== null || searchForm.max_score_diff !== null) {
      const min = searchForm.min_score_diff ?? '不限'
      const max = searchForm.max_score_diff ?? '不限'
      filters.push({ key: 'score_diff', label: `分差: ${min} ~ ${max}` })
    }

    return filters
  })

  // 🔧 獲取當前搜尋的球員名稱（用於高亮）
  const searchedPlayerNames = computed(() => {
    if (!searchForm.player_ids || searchForm.player_ids.length === 0) {
      return []
    }
    return searchForm.player_ids
      .map(id => {
        const player = playerOptions.value.find(p => p.value === id)
        return player ? player.label : ''
      })
      .filter(name => name)
  })

  const activeFiltersCount = computed(() => activeFilters.value.length)

  // 分頁配置
  const paginationConfig = computed(() => ({
    page: currentPage.value,
    pageSize: pageSize.value,
    itemCount: totalResults.value,
    showSizePicker: true,
    pageSizes: [10, 15, 20, 50],
    showQuickJumper: true,
    prefix: ({ itemCount }) => `共 ${itemCount} 項`,
    onUpdatePage: page => {
      handlePageChange(page)
    },
    onUpdatePageSize: newPageSize => {
      pageSize.value = newPageSize
      currentPage.value = 1
      if (searchExecuted.value) {
        handleSearch()
      } else {
        pagination.pageSize = newPageSize
        pagination.page = 1
      }
    }
  }))

  // 表格欄位定義
  const tableColumns = computed(() => [
    {
      title: '比賽日期',
      key: 'match_date',
      sorter: 'default',
      width: 120,
      render: row => (row.match_date ? format(new Date(row.match_date), 'yyyy-MM-dd') : '-')
    },
    {
      title: 'Team A',
      key: 'team_a',
      children: [
        {
          title: '後排',
          key: 'player1',
          width: 120,
          ellipsis: { tooltip: true },
          render: row => {
            if (!row.player1) return '-'
            const playerName = row.player1.name
            return renderPlayerNameWithHighlight(playerName)
          }
        },
        {
          title: '前排',
          key: 'player2',
          width: 120,
          ellipsis: { tooltip: true },
          render: row => {
            if (!row.player2) return '-'
            const playerName = row.player2.name
            return renderPlayerNameWithHighlight(playerName)
          }
        }
      ]
    },
    {
      title: 'VS',
      key: 'vs',
      width: 50,
      align: 'center',
      render: () => h('span', { style: 'font-weight: bold; color: #666;' }, 'VS')
    },
    {
      title: 'Team B',
      key: 'team_b',
      children: [
        {
          title: '後排',
          key: 'player3',
          width: 120,
          ellipsis: { tooltip: true },
          render: row => {
            if (!row.player3) return '-'
            const playerName = row.player3.name
            return renderPlayerNameWithHighlight(playerName)
          }
        },
        {
          title: '前排',
          key: 'player4',
          width: 120,
          ellipsis: { tooltip: true },
          render: row => {
            if (!row.player4) return '-'
            const playerName = row.player4.name
            return renderPlayerNameWithHighlight(playerName)
          }
        }
      ]
    },
    {
      title: '比分',
      key: 'score',
      width: 120,
      align: 'center',
      render: row => {
        let outcomeTag = null
        if (row.side_a_outcome === 'win') {
          outcomeTag = h(NTag, { type: 'success', size: 'tiny', round: true }, { default: () => 'A勝' })
        } else if (row.side_a_outcome === 'loss') {
          outcomeTag = h(NTag, { type: 'error', size: 'tiny', round: true }, { default: () => 'B勝' })
        }

        const elements = [h('span', `${row.a_games} : ${row.b_games}`)]
        if (outcomeTag) {
          elements.push(outcomeTag)
        }

        return h(NSpace, { align: 'center', justify: 'center' }, () => elements)
      }
    },
    {
      title: '類型',
      key: 'match_type',
      width: 100,
      sorter: { multiple: 2 },
      filterOptions: matchTypeOptions,
      filter: (value, row) => row.match_type === value,
      render: row => getMatchTypeDisplay(row.match_type)
    },
    {
      title: '賽制',
      key: 'match_format',
      width: 120,
      sorter: { multiple: 3 },
      filterOptions: matchFormatOptions,
      filter: (value, row) => row.match_format === value,
      render: row => getMatchFormatDisplay(row.match_format)
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      align: 'center',
      fixed: 'right',
      render: row => {
        return h(NSpace, { justify: 'center' }, () => [
          h(NTooltip, null, {
            trigger: () =>
              h(
                NButton,
                {
                  size: 'tiny',
                  circle: true,
                  onClick: () => editMatchRecord(row.id)
                },
                { icon: () => h(NIcon, { component: EditIcon }) }
              ),
            default: () => '編輯'
          }),
          h(NTooltip, null, {
            trigger: () =>
              h(
                NButton,
                {
                  size: 'tiny',
                  circle: true,
                  type: 'error',
                  onClick: () => confirmDeleteMatch(row)
                },
                { icon: () => h(NIcon, { component: DeleteIcon }) }
              ),
            default: () => '刪除 (將觸發分數重算)'
          })
        ])
      }
    }
  ])

  // 監聽球員選擇變更
  watch(
    () => searchForm.player_ids,
    newIds => {
      if (!newIds || newIds.length === 0) {
        searchForm.player_position = null
        searchForm.win_loss = null // 清除勝負選擇
      }
    }
  )

  // 方法
  const toggleSearchPanel = () => {
    searchPanelVisible.value = !searchPanelVisible.value
  }

  const handlePlayerSearch = async query => {
    if (!query) return

    playersLoading.value = true
    try {
      const response = await apiClient.get(`/members?name=${encodeURIComponent(query)}`)

      // 🔧 修正數據解析
      let membersData = response.data
      if (response.data && response.data.members) {
        membersData = response.data.members
      } else if (response.data && response.data.data) {
        membersData = response.data.data
      }

      if (!Array.isArray(membersData)) {
        console.warn('球員搜尋響應不是數組:', membersData)
        membersData = []
      }

      playerOptions.value = membersData.map(member => ({
        label: member.name,
        value: member.id
      }))
    } catch (error) {
      console.error('搜尋球員失敗:', error)
      message.error('搜尋球員失敗')
    } finally {
      playersLoading.value = false
    }
  }

  const handleFormChange = () => {
    // 如果需要自動搜尋，可以在這裡加入邏輯
  }

  const buildSearchParams = () => {
    const params = {
      page: currentPage.value,
      per_page: pageSize.value
    }

    if (searchForm.player_ids?.length > 0) {
      params.player_ids = searchForm.player_ids.join(',')
    }

    if (searchForm.player_position) {
      params.player_position = searchForm.player_position
    }

    if (searchForm.match_type) {
      params.match_type = searchForm.match_type
    }

    if (searchForm.match_format) {
      params.match_format = searchForm.match_format
    }

    if (searchForm.win_loss) {
      params.win_loss = searchForm.win_loss
    }

    if (searchForm.dateRange?.length === 2) {
      params.date_from = new Date(searchForm.dateRange[0]).toISOString().split('T')[0]
      params.date_to = new Date(searchForm.dateRange[1]).toISOString().split('T')[0]
    }

    if (searchForm.min_score_diff !== null) {
      params.min_score_diff = searchForm.min_score_diff
    }

    if (searchForm.max_score_diff !== null) {
      params.max_score_diff = searchForm.max_score_diff
    }

    return params
  }

  const handleSearch = async () => {
    searching.value = true

    try {
      const params = buildSearchParams()
      const queryString = new URLSearchParams(params).toString()

      const response = await apiClient.get(`/match-records?${queryString}`)

      // 🔧 修正數據解析
      let recordsData = []
      let paginationData = null

      if (response.data) {
        if (response.data.match_records && Array.isArray(response.data.match_records)) {
          recordsData = response.data.match_records
          paginationData = response.data.pagination
        } else if (response.data.records && Array.isArray(response.data.records)) {
          recordsData = response.data.records
          paginationData = response.data.pagination
        } else if (Array.isArray(response.data)) {
          recordsData = response.data
        } else {
          console.warn('未知的搜尋響應結構:', response.data)
          recordsData = []
        }
      }

      displayRecords.value = recordsData
      totalResults.value = paginationData?.total || recordsData.length
      currentPage.value = paginationData?.current_page || paginationData?.page || 1
      searchExecuted.value = true

      message.success(`找到 ${totalResults.value} 筆符合條件的記錄`)
    } catch (error) {
      console.error('搜尋失敗:', error)
      message.error('搜尋失敗，請稍後再試')
      fetchError.value = error.response?.data?.message || '搜尋失敗'
    } finally {
      searching.value = false
    }
  }

  const handleResetSearch = () => {
    Object.keys(searchForm).forEach(key => {
      if (Array.isArray(searchForm[key])) {
        searchForm[key] = []
      } else {
        searchForm[key] = null
      }
    })

    searchExecuted.value = false
    totalResults.value = 0
    currentPage.value = 1

    // 回到顯示所有記錄
    displayRecords.value = allMatchRecords.value
    totalResults.value = allMatchRecords.value.length

    message.info('搜尋條件已重置')
  }

  const removeFilter = filterKey => {
    switch (filterKey) {
      case 'player_ids':
        searchForm.player_ids = []
        break
      case 'player_position':
        searchForm.player_position = null
        break
      case 'match_type':
        searchForm.match_type = null
        break
      case 'match_format':
        searchForm.match_format = null
        break
      case 'win_loss':
        searchForm.win_loss = null
        break
      case 'dateRange':
        searchForm.dateRange = null
        break
      case 'score_diff':
        searchForm.min_score_diff = null
        searchForm.max_score_diff = null
        break
    }

    // 自動重新搜尋
    if (searchExecuted.value) {
      handleSearch()
    }
  }

  const handlePageChange = page => {
    currentPage.value = page
    // 這個函數現在由分頁配置中的 onChange 調用
    if (searchExecuted.value) {
      handleSearch()
    } else {
      // 如果沒有搜尋，重新載入數據
      fetchMatchRecords()
    }
  }

  const handleExport = () => {
    const params = buildSearchParams()
    message.info('匯出功能開發中...')
    console.log('匯出參數:', params)
  }

  // 🔧 修正數據載入方法
  async function fetchMatchRecords() {
    loading.value = true
    fetchError.value = null
    try {
      const response = await apiClient.get('/match-records')

      // 處理不同的響應結構
      let recordsData = []
      if (response.data) {
        if (response.data.match_records && Array.isArray(response.data.match_records)) {
          recordsData = response.data.match_records
        } else if (Array.isArray(response.data)) {
          recordsData = response.data
        } else {
          console.warn('未知的比賽記錄響應結構:', response.data)
          recordsData = []
        }
      }

      allMatchRecords.value = recordsData
      displayRecords.value = recordsData
      totalResults.value = recordsData.length
    } catch (err) {
      fetchError.value = err.response?.data?.message || '無法載入比賽記錄。'
    } finally {
      loading.value = false
    }
  }

  const handleRefreshData = () => {
    if (searchExecuted.value) {
      handleSearch()
    } else {
      fetchMatchRecords()
    }
  }

  function goToRecordMatchPage() {
    router.push({ name: 'RecordMatch' })
  }

  function editMatchRecord(recordId) {
    message.info(`編輯功能待開發，目標 ID: ${recordId}`)
  }

  function confirmDeleteMatch(record) {
    dialog.error({
      title: '確認刪除比賽記錄',
      content: `您確定要刪除這場比賽記錄嗎？`,
      positiveText: '確認刪除',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await apiClient.delete(`/match-records/${record.id}`)
          message.success(`比賽記錄 #${record.id} 已成功刪除。`)
          await handleRefreshData()
        } catch (err) {
          message.error(err.response?.data?.message || `刪除失敗。`)
        }
      }
    })
  }

  // 🔧 修正球員載入方法
  const loadPlayers = async () => {
    try {
      const response = await apiClient.get('/members?all=false&sort_by=name&sort_order=asc')

      // 處理不同的響應結構
      let membersData = response.data
      if (response.data && response.data.members) {
        membersData = response.data.members
      } else if (response.data && response.data.data) {
        membersData = response.data.data
      }

      if (!Array.isArray(membersData)) {
        console.warn('球員列表響應不是數組:', membersData)
        membersData = []
      }

      playerOptions.value = membersData.map(member => ({
        label: member.name,
        value: member.id
      }))
    } catch (error) {
      console.error('載入球員列表失敗:', error)
    }
  }

  // 生命週期
  onMounted(() => {
    fetchMatchRecords()
    loadPlayers()
  })
</script>

<style scoped>
  /* === 品牌色彩系統（任天堂風格紅色） === */
  :root {
    --brand-primary: #e53e3e;
    --brand-secondary: #c53030;
    --brand-light: #fed7d7;
    --brand-dark: #9b2c2c;
  }

  /* === 主要容器和佈局 === */
  .match-management-page {
    max-width: 1600px;
    margin: 0 auto;
    padding: 2rem;
    background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
    min-height: 100vh;
  }

  .page-main-title {
    font-weight: 700;
    font-size: 2.5rem;
    margin-bottom: 2rem;
    color: #2c3e50;
    text-align: center;
    background: linear-gradient(135deg, var(--brand-primary), var(--brand-secondary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    position: relative;
  }

  .page-main-title::after {
    content: '';
    position: absolute;
    bottom: -8px;
    left: 50%;
    transform: translateX(-50%);
    width: 120px;
    height: 4px;
    background: linear-gradient(90deg, var(--brand-primary), var(--brand-secondary));
    border-radius: 2px;
  }

  /* === 頁面操作按鈕區域 === */
  .page-actions {
    display: flex;
    justify-content: flex-end;
    gap: 1rem;
    margin-bottom: 2rem;
  }

  .page-actions .n-button {
    border-radius: 8px;
    padding: 0.75rem 1.5rem;
    font-weight: 600;
    transition: all 0.2s ease;
  }

  .page-actions .n-button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  /* === 搜尋區域樣式 === */
  .search-section {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    margin-bottom: 2rem;
    border: 1px solid #e2e8f0;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  }

  .search-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0;
  }

  .search-header .n-button {
    border-radius: 8px;
    padding: 0.75rem 1.5rem;
    font-weight: 600;
    transition: all 0.2s ease;
  }

  .filter-count {
    background: var(--brand-primary);
    color: white;
    font-size: 0.75rem;
    padding: 4px 8px;
    border-radius: 12px;
    margin-left: 8px;
    font-weight: 700;
  }

  /* === 搜尋面板 === */
  .search-panel {
    background: #f8fafc;
    border-radius: 8px;
    padding: 2rem;
    margin-top: 1.5rem;
    border: 1px solid #e2e8f0;
  }

  .search-panel .n-form-item {
    margin-bottom: 1.25rem;
  }

  /* === 搜尋操作按鈕 === */
  .search-actions {
    margin-top: 2rem;
    padding-top: 1.5rem;
    border-top: 1px solid #e2e8f0;
    display: flex;
    justify-content: center;
    gap: 1rem;
  }

  .search-actions .n-button {
    border-radius: 8px;
    font-weight: 600;
    padding: 0.75rem 1.5rem;
    transition: all 0.2s ease;
  }

  .search-actions .n-button:hover {
    transform: translateY(-1px);
  }

  /* === 活躍篩選條件 === */
  .active-filters {
    background: #f1f5f9;
    border-radius: 8px;
    padding: 1rem 1.5rem;
    margin-top: 1.5rem;
    border: 1px solid #cbd5e1;
  }

  .filter-label {
    font-weight: 700;
    color: #475569;
    margin-right: 0.75rem;
    font-size: 0.875rem;
  }

  .active-filters .n-tag {
    background: white;
    border: 1px solid #cbd5e1;
    color: #475569;
    font-weight: 500;
    border-radius: 6px;
    margin: 0.25rem;
    transition: all 0.2s ease;
  }

  .active-filters .n-tag:hover {
    border-color: var(--brand-primary);
    color: var(--brand-primary);
  }

  /* === 搜尋結果統計 === */
  .search-stats {
    background: #f0f9ff;
    border-radius: 8px;
    padding: 1rem 1.5rem;
    border: 1px solid #bae6fd;
    margin-top: 1rem;
  }

  .search-info {
    font-weight: 600;
    color: #0369a1;
    font-size: 1rem;
  }

  .filter-info {
    color: #0284c7;
    font-weight: 500;
    font-size: 0.875rem;
  }

  /* === 🔧 搜尋高亮樣式 === */
  .search-highlight {
    background-color: #fef3c7;
    color: #92400e;
    font-weight: 600;
    padding: 2px 4px;
    border-radius: 3px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  }

  /* === 簡潔表格樣式 === */
  .n-data-table {
    background: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    border: 1px solid #e2e8f0;
  }

  /* 統一的表格標題列樣式 - 簡潔灰色 */
  .n-data-table .n-data-table-thead .n-data-table-th {
    background-color: #f8fafc;
    font-weight: 600;
    color: #374151;
    font-size: 0.875rem;
    padding: 1rem 0.75rem;
    border-bottom: 1px solid #e5e7eb;
    text-align: center;
  }

  /* 移除過多的顏色區分，使用邊框區分即可 */
  .n-data-table .n-data-table-thead .n-data-table-th[data-col-key='team_a'] {
    background-color: #f8fafc;
    color: #374151;
    font-weight: 700;
    border-right: 2px solid var(--brand-primary);
  }

  .n-data-table .n-data-table-thead .n-data-table-th[data-col-key='team_b'] {
    background-color: #f8fafc;
    color: #374151;
    font-weight: 700;
    border-left: 2px solid var(--brand-primary);
  }

  .n-data-table .n-data-table-thead .n-data-table-th[data-col-key='vs'] {
    background-color: var(--brand-primary);
    color: white;
    font-weight: 700;
    font-size: 0.75rem;
  }

  /* 子表頭樣式 - 保持一致性 */
  .n-data-table .n-data-table-thead .n-data-table-th[data-col-key='player1'],
  .n-data-table .n-data-table-thead .n-data-table-th[data-col-key='player2'],
  .n-data-table .n-data-table-thead .n-data-table-th[data-col-key='player3'],
  .n-data-table .n-data-table-thead .n-data-table-th[data-col-key='player4'] {
    background-color: #f8fafc;
    color: #6b7280;
    font-weight: 600;
    font-size: 0.8rem;
  }

  /* 表格行樣式 - 簡潔設計 */
  .n-data-table .n-data-table-tbody .n-data-table-tr {
    transition: background-color 0.2s ease;
    border-bottom: 1px solid #f1f5f9;
  }

  .n-data-table .n-data-table-tbody .n-data-table-tr:hover {
    background-color: #f8fafc;
  }

  .n-data-table .n-data-table-tbody .n-data-table-td {
    padding: 0.875rem 0.75rem;
    font-weight: 500;
    color: #374151;
    text-align: center;
  }

  /* 比分欄位樣式 */
  .n-data-table .n-data-table-tbody .n-data-table-td[data-col-key='score'] {
    font-weight: 700;
    font-size: 1rem;
  }

  /* === 空狀態樣式 === */
  .n-empty {
    padding: 3rem 2rem;
    background: white;
    border-radius: 8px;
    margin: 2rem 0;
    border: 1px dashed #cbd5e1;
  }

  .n-empty .n-empty__description {
    color: #6b7280;
    font-weight: 500;
    margin-bottom: 1.5rem;
  }

  /* === 主要按鈕使用品牌色 === */
  .n-button--primary {
    background-color: var(--brand-primary) !important;
    border-color: var(--brand-primary) !important;
  }

  .n-button--primary:hover {
    background-color: var(--brand-secondary) !important;
    border-color: var(--brand-secondary) !important;
  }

  /* === 載入動畫 === */
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .search-section,
  .n-data-table {
    animation: fadeIn 0.3s ease-out;
  }

  /* === 響應式設計 === */
  @media (max-width: 1200px) {
    .match-management-page {
      padding: 1.5rem;
    }
  }

  @media (max-width: 768px) {
    .match-management-page {
      padding: 1rem;
    }

    .page-main-title {
      font-size: 2rem;
      margin-bottom: 1.5rem;
    }

    .page-actions {
      flex-direction: column;
      gap: 0.75rem;
    }

    .search-section {
      padding: 1.5rem;
    }

    .search-panel {
      padding: 1.5rem;
    }

    .search-actions {
      flex-direction: column;
      gap: 0.5rem;
    }

    .active-filters {
      padding: 1rem;
    }

    .n-data-table .n-data-table-thead .n-data-table-th {
      font-size: 0.75rem;
      padding: 0.75rem 0.5rem;
    }

    .n-data-table .n-data-table-tbody .n-data-table-td {
      padding: 0.75rem 0.5rem;
      font-size: 0.875rem;
    }
  }

  @media (max-width: 480px) {
    .page-main-title {
      font-size: 1.75rem;
    }

    .search-section {
      padding: 1rem;
    }

    .search-panel {
      padding: 1rem;
    }
  }
</style>