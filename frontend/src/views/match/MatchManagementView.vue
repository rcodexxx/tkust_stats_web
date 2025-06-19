<template>
  <div class="match-management-page container-fluid mt-4 mb-5 px-md-4">
    <!-- 頁面標題 -->
    <div class="page-header mb-4">
      <h1 class="page-title">比賽記錄管理</h1>
      <div class="page-actions">
        <n-space>
          <n-button type="primary" size="large" @click="goToRecordMatchPage">
            <template #icon>
              <n-icon :component="AddIcon" />
            </template>
            記錄新比賽
          </n-button>
          <n-button @click="handleRefreshData" :loading="loading" size="large">
            <template #icon>
              <n-icon :component="RefreshIcon" />
            </template>
            重新整理
          </n-button>
        </n-space>
      </div>
    </div>

    <!-- 搜尋卡片 -->
    <n-card :bordered="false" class="search-card mb-4">
      <template #header>
        <div class="search-header">
          <n-button
            @click="toggleSearchPanel"
            :type="searchPanelVisible ? 'primary' : 'default'"
            size="large"
            strong
          >
            <template #icon>
              <n-icon :component="searchPanelVisible ? ChevronUpIcon : SearchIcon" />
            </template>
            {{ searchPanelVisible ? '收起搜尋' : '進階搜尋' }}
            <n-badge
              v-if="activeFiltersCount > 0"
              :value="activeFiltersCount"
              :offset="[10, -5]"
              type="error"
            />
          </n-button>
          <n-spin v-if="searching" size="small" />
        </div>
      </template>

      <!-- 搜尋面板 -->
      <n-collapse-transition :show="searchPanelVisible">
        <div class="search-panel">
          <n-form ref="searchFormRef" :model="searchForm" label-placement="top" size="medium">
            <n-grid :x-gap="20" :y-gap="20" cols="1 s:2 m:3 l:4" responsive="screen">
              <!-- 球員搜尋 -->
              <n-form-item-gi label="球員">
                <n-select
                  v-model:value="searchForm.player_ids"
                  :options="playerOptions"
                  multiple
                  filterable
                  clearable
                  placeholder="選擇或搜尋球員"
                  :loading="playersLoading"
                  @search="handlePlayerSearch"
                  :max-tag-count="2"
                />
              </n-form-item-gi>

              <!-- 比賽類型 -->
              <n-form-item-gi label="比賽類型">
                <n-select
                  v-model:value="searchForm.match_type"
                  :options="matchTypeOptions"
                  clearable
                  placeholder="選擇類型"
                />
              </n-form-item-gi>

              <!-- 賽制 -->
              <n-form-item-gi label="賽制">
                <n-select
                  v-model:value="searchForm.match_format"
                  :options="matchFormatOptions"
                  clearable
                  placeholder="選擇賽制"
                />
              </n-form-item-gi>

              <!-- 勝負結果 -->
              <n-form-item-gi label="勝負結果">
                <n-select
                  v-model:value="searchForm.win_loss"
                  :options="winLossOptions"
                  clearable
                  placeholder="選擇勝負"
                  :disabled="!searchForm.player_ids || searchForm.player_ids.length === 0"
                />
              </n-form-item-gi>

              <!-- 日期範圍 -->
              <n-form-item-gi label="日期範圍" :span="2">
                <n-date-picker
                  v-model:value="searchForm.dateRange"
                  type="daterange"
                  clearable
                  format="yyyy-MM-dd"
                  placeholder="選擇日期範圍"
                  style="width: 100%"
                />
              </n-form-item-gi>

              <!-- 分數差距 -->
              <n-form-item-gi label="分數差距" :span="2">
                <n-input-group>
                  <n-input-number
                    v-model:value="searchForm.min_score_diff"
                    placeholder="最小差距"
                    :min="0"
                    :max="10"
                    style="width: 50%"
                  />
                  <n-input-number
                    v-model:value="searchForm.max_score_diff"
                    placeholder="最大差距"
                    :min="0"
                    :max="10"
                    style="width: 50%"
                  />
                </n-input-group>
              </n-form-item-gi>
            </n-grid>

            <!-- 重置按鈕 -->
            <n-divider style="margin: 2rem 0 1.5rem 0" />
            <div class="search-actions">
              <n-space justify="center">
                <n-button @click="handleResetSearch" size="large">
                  <template #icon>
                    <n-icon :component="RefreshIcon" />
                  </template>
                  重置
                </n-button>
              </n-space>
            </div>
          </n-form>
        </div>
      </n-collapse-transition>

      <!-- 活躍篩選條件 -->
      <div v-if="activeFilters.length > 0" class="active-filters">
        <div class="filters-container">
          <span class="filter-label">
            <n-icon :component="FilterIcon" style="margin-right: 0.5rem" />
            篩選條件:
          </span>
          <n-space size="small" wrap>
            <n-tag
              v-for="filter in activeFilters"
              :key="filter.key"
              closable
              @close="removeFilter(filter.key)"
              type="info"
              size="medium"
              round
            >
              {{ filter.label }}
            </n-tag>
          </n-space>
          <n-button size="small" text type="error" @click="handleResetSearch">
            清除全部
          </n-button>
        </div>
      </div>

      <!-- 搜尋結果統計 -->
      <div v-if="searchExecuted" class="search-stats">
        <n-alert type="info" :show-icon="false">
          <template #header>
            <n-space align="center">
              <n-icon :component="StatsIcon" />
              <span>找到 <strong>{{ totalResults }}</strong> 筆記錄</span>
              <span v-if="activeFiltersCount > 0" class="filter-info">
                (已套用 {{ activeFiltersCount }} 個篩選條件)
              </span>
            </n-space>
          </template>
        </n-alert>
      </div>
    </n-card>

    <!-- 錯誤提示 -->
    <div v-if="fetchError" class="mb-4">
      <n-alert title="載入錯誤" type="error" closable @close="fetchError = null">
        {{ fetchError }}
      </n-alert>
    </div>

    <!-- 比賽記錄表格卡片 -->
    <n-card :bordered="false" class="table-card">
      <template #header>
        <n-space justify="space-between" align="center">
          <span class="table-title">
            <n-icon :component="TableIcon" style="margin-right: 0.5rem" />
            比賽記錄列表
          </span>
          <n-space>
            <n-tag type="info" size="small" round>
              總計: {{ totalResults }} 筆
            </n-tag>
          </n-space>
        </n-space>
      </template>

      <n-data-table
        :columns="tableColumns"
        :data="displayRecords"
        :loading="loading"
        :pagination="paginationConfig"
        :bordered="false"
        :bottom-bordered="true"
        :single-line="false"
        size="medium"
        flex-height
        style="min-height: 400px"
        :scroll-x="1200"
        :row-key="row => row.id"
        striped
      />

      <!-- 空狀態 -->
      <div v-if="!loading && displayRecords.length === 0" class="empty-state">
        <n-empty description="沒有找到符合條件的比賽記錄">
          <template #icon>
            <n-icon :component="EmptyIcon" size="64" />
          </template>
          <template #extra>
            <n-space>
              <n-button type="primary" @click="goToRecordMatchPage" size="large">
                <template #icon>
                  <n-icon :component="AddIcon" />
                </template>
                新增第一場比賽
              </n-button>
              <n-button @click="handleResetSearch" v-if="searchExecuted" size="large">
                重置搜尋條件
              </n-button>
            </n-space>
          </template>
        </n-empty>
      </div>
    </n-card>
  </div>
</template>

<script setup>
import { computed, h, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  NAlert,
  NBadge,
  NButton,
  NCard,
  NCollapseTransition,
  NDataTable,
  NDatePicker,
  NDivider,
  NEmpty,
  NForm,
  NFormItemGi,
  NGrid,
  NIcon,
  NInputGroup,
  NInputNumber,
  NSelect,
  NSpace,
  NSpin,
  NTag,
  NTooltip,
  useDialog,
  useMessage
} from 'naive-ui'
import {
  AddCircleOutline as AddIcon,
  BarChartOutline as StatsIcon,
  ChevronUpOutline as ChevronUpIcon,
  FunnelOutline as FilterIcon,
  GridOutline as TableIcon,
  PencilOutline as EditIcon,
  RefreshOutline as RefreshIcon,
  SearchOutline as SearchIcon,
  TrashBinOutline as DeleteIcon,
  TrophyOutline as EmptyIcon
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
const isResetting = ref(false)

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
  match_type: null,
  match_format: null,
  win_loss: null,
  dateRange: null,
  min_score_diff: null,
  max_score_diff: null
})

// 防抖搜尋
let searchTimeout = null
const SEARCH_DEBOUNCE_DELAY = 500

// 選項配置
const matchTypeOptions = [
  { label: '雙打', value: 'doubles' },
  { label: '單打', value: 'singles' }
]

const matchFormatOptions = [
  { label: '五局制', value: 'games_5' },
  { label: '七局制', value: 'games_7' },
  { label: '九局制', value: 'games_9' }
]

const winLossOptions = [
  { label: '勝利', value: 'win' },
  { label: '失敗', value: 'loss' }
]

// 輔助函數
const getMatchTypeDisplay = value => matchTypeOptions.find(opt => opt.value === value)?.label || value
const getMatchFormatDisplay = value => matchFormatOptions.find(opt => opt.value === value)?.label || value

// 高亮球員名字
const renderPlayerNameWithHighlight = playerName => {
  if (!playerName) return '-'

  if (!searchedPlayerNames.value || searchedPlayerNames.value.length === 0) {
    return playerName
  }

  const matchedSearchTerm = searchedPlayerNames.value.find(searchName =>
    playerName.toLowerCase().includes(searchName.toLowerCase())
  )

  if (matchedSearchTerm) {
    const escapeRegExp = string => string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const regex = new RegExp(`(${escapeRegExp(matchedSearchTerm)})`, 'gi')
    const highlightedHTML = playerName.replace(regex, '<mark class="search-highlight">$1</mark>')

    return h('span', {
      innerHTML: highlightedHTML
    })
  }

  return playerName
}

// 執行搜尋
const performSearch = async () => {
  const hasSearchConditions =
    (searchForm.player_ids && searchForm.player_ids.length > 0) ||
    searchForm.match_type ||
    searchForm.match_format ||
    searchForm.win_loss ||
    (searchForm.dateRange && searchForm.dateRange.length === 2) ||
    searchForm.min_score_diff !== null ||
    searchForm.max_score_diff !== null

  if (!hasSearchConditions) {
    displayRecords.value = allMatchRecords.value
    totalResults.value = allMatchRecords.value.length
    searchExecuted.value = false
    return
  }

  try {
    const params = buildSearchParams()
    const response = await apiClient.get('/match-records', { params })

    let recordsData = []
    let paginationData = null

    if (response.data?.match_records) {
      recordsData = response.data.match_records
      paginationData = response.data.pagination
    } else if (Array.isArray(response.data)) {
      recordsData = response.data
    }

    displayRecords.value = recordsData
    totalResults.value = paginationData?.total || recordsData.length
    searchExecuted.value = true

  } catch (error) {
    console.error('搜尋失敗:', error)
    fetchError.value = error.response?.data?.message || '搜尋失敗'
  }
}

// 防抖搜尋
const debounceSearch = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }

  searching.value = true
  searchTimeout = setTimeout(async () => {
    if (!isResetting.value) {
      await performSearch()
    }
    searching.value = false
  }, SEARCH_DEBOUNCE_DELAY)
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

  if (searchForm.match_type) {
    const typeLabel = matchTypeOptions.find(t => t.value === searchForm.match_type)?.label
    filters.push({ key: 'match_type', label: `類型: ${typeLabel}` })
  }

  if (searchForm.match_format) {
    const formatLabel = matchFormatOptions.find(f => f.value === searchForm.match_format)?.label
    filters.push({ key: 'match_format', label: `賽制: ${formatLabel}` })
  }

  if (searchForm.win_loss) {
    const winLossLabel = winLossOptions.find(w => w.value === searchForm.win_loss)?.label
    filters.push({ key: 'win_loss', label: `結果: ${winLossLabel}` })
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
    debounceSearch()
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
          return renderPlayerNameWithHighlight(row.player1.name)
        }
      },
      {
        title: '前排',
        key: 'player2',
        width: 120,
        ellipsis: { tooltip: true },
        render: row => {
          if (!row.player2) return '-'
          return renderPlayerNameWithHighlight(row.player2.name)
        }
      }
    ]
  },
  {
    title: 'VS',
    key: 'vs',
    width: 50,
    align: 'center',
    render: () => h('span', { class: 'vs-separator' }, 'VS')
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
          return renderPlayerNameWithHighlight(row.player3.name)
        }
      },
      {
        title: '前排',
        key: 'player4',
        width: 120,
        ellipsis: { tooltip: true },
        render: row => {
          if (!row.player4) return '-'
          return renderPlayerNameWithHighlight(row.player4.name)
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
        outcomeTag = h(NTag, { type: 'success', size: 'small', round: true }, { default: () => 'A勝' })
      } else if (row.side_a_outcome === 'loss') {
        outcomeTag = h(NTag, { type: 'error', size: 'small', round: true }, { default: () => 'B勝' })
      }

      const elements = [
        h('div', { class: 'score-display' }, `${row.a_games} : ${row.b_games}`)
      ]
      if (outcomeTag) {
        elements.push(outcomeTag)
      }

      return h('div', { class: 'score-container' }, elements)
    }
  },
  {
    title: '類型',
    key: 'match_type',
    width: 100,
    render: row => getMatchTypeDisplay(row.match_type)
  },
  {
    title: '賽制',
    key: 'match_format',
    width: 100,
    render: row => getMatchFormatDisplay(row.match_format)
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    align: 'center',
    fixed: 'right',
    render: row => {
      return h('div', { class: 'action-buttons' }, [
        h(NTooltip, null, {
          trigger: () =>
            h(
              NButton,
              {
                size: 'small',
                circle: true,
                onClick: () => editMatchRecord(row.id),
                class: 'action-btn edit-btn'
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
                size: 'small',
                circle: true,
                type: 'error',
                onClick: () => confirmDeleteMatch(row),
                class: 'action-btn delete-btn'
              },
              { icon: () => h(NIcon, { component: DeleteIcon }) }
            ),
          default: () => '刪除'
        })
      ])
    }
  }
])

// 監聽搜尋條件變化
watch(
  () => [
    searchForm.player_ids,
    searchForm.match_type,
    searchForm.match_format,
    searchForm.win_loss,
    searchForm.dateRange,
    searchForm.min_score_diff,
    searchForm.max_score_diff
  ],
  (newValues, oldValues) => {
    if (!oldValues || isResetting.value) {
      return
    }

    const hasChanged = newValues.some((newVal, index) => {
      const oldVal = oldValues[index]
      if (Array.isArray(newVal) && Array.isArray(oldVal)) {
        return JSON.stringify(newVal) !== JSON.stringify(oldVal)
      }
      return newVal !== oldVal
    })

    if (hasChanged) {
      currentPage.value = 1
      debounceSearch()
    }
  },
  { deep: true }
)

// 監聽球員選擇變更
watch(
  () => searchForm.player_ids,
  newIds => {
    if (!newIds || newIds.length === 0) {
      searchForm.win_loss = null
    }
  }
)

// 方法
const toggleSearchPanel = () => {
  searchPanelVisible.value = !searchPanelVisible.value
}

const handlePlayerSearch = async query => {
  if (!query || query.length < 2) {
    await loadPlayers()
    return
  }

  playersLoading.value = true
  try {
    const response = await apiClient.get(`/members?search=${encodeURIComponent(query)}&limit=20`)

    let membersData = response.data
    if (response.data?.members) {
      membersData = response.data.members
    } else if (response.data?.data) {
      membersData = response.data.data
    }

    if (!Array.isArray(membersData)) {
      membersData = []
    }

    const searchResults = membersData.map(member => ({
      label: member.name,
      value: member.id
    }))

    const existingIds = new Set(playerOptions.value.map(p => p.value))
    const newOptions = searchResults.filter(p => !existingIds.has(p.value))
    playerOptions.value = [...playerOptions.value, ...newOptions]

  } catch (error) {
    console.error('搜尋球員失敗:', error)
  } finally {
    playersLoading.value = false
  }
}

const buildSearchParams = () => {
  const params = {
    page: currentPage.value,
    per_page: pageSize.value
  }

  if (searchForm.player_ids?.length > 0) {
    params.player_id = searchForm.player_ids[0]
  }

  if (searchForm.match_type) {
    params.match_type = searchForm.match_type
  }

  if (searchForm.match_format) {
    params.match_format = searchForm.match_format
  }

  if (searchForm.dateRange?.length === 2) {
    params.start_date = new Date(searchForm.dateRange[0]).toISOString().split('T')[0]
    params.end_date = new Date(searchForm.dateRange[1]).toISOString().split('T')[0]
  }

  Object.keys(params).forEach(key => {
    if (params[key] === null || params[key] === undefined || params[key] === '') {
      delete params[key]
    }
  })

  return params
}

const handleResetSearch = async () => {
  isResetting.value = true

  if (searchTimeout) {
    clearTimeout(searchTimeout)
    searchTimeout = null
  }

  Object.keys(searchForm).forEach(key => {
    if (Array.isArray(searchForm[key])) {
      searchForm[key] = []
    } else {
      searchForm[key] = null
    }
  })

  await nextTick()
  isResetting.value = false

  searchExecuted.value = false
  currentPage.value = 1
  fetchError.value = null

  displayRecords.value = allMatchRecords.value
  totalResults.value = allMatchRecords.value.length
}

const removeFilter = async filterKey => {
  isResetting.value = true

  switch (filterKey) {
    case 'player_ids':
      searchForm.player_ids = []
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

  await nextTick()
  isResetting.value = false
}

const handlePageChange = page => {
  currentPage.value = page
  debounceSearch()
}

const fetchMatchRecords = async () => {
  loading.value = true
  fetchError.value = null

  try {
    const params = {
      page: currentPage.value,
      per_page: pageSize.value,
      sort_by: 'match_date',
      sort_order: 'desc'
    }

    const response = await apiClient.get('/match-records', { params })

    let recordsData = []
    let paginationData = null

    if (response.data?.match_records) {
      recordsData = response.data.match_records
      paginationData = response.data.pagination
    } else if (Array.isArray(response.data)) {
      recordsData = response.data
    }

    allMatchRecords.value = recordsData
    displayRecords.value = recordsData
    totalResults.value = paginationData?.total || recordsData.length

  } catch (err) {
    console.error('載入比賽記錄失敗:', err)
    fetchError.value = err.response?.data?.message || '無法載入比賽記錄'
  } finally {
    loading.value = false
  }
}

const handleRefreshData = () => {
  fetchMatchRecords()
}

const goToRecordMatchPage = () => {
  router.push({ name: 'RecordMatch' })
}

const editMatchRecord = recordId => {
  router.push({ name: 'EditMatch', params: { id: recordId } })
}

const confirmDeleteMatch = record => {
  dialog.error({
    title: '確認刪除比賽記錄',
    content: `您確定要刪除這場比賽記錄嗎？`,
    positiveText: '確認刪除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await apiClient.delete(`/match-records/${record.id}`)
        message.success(`比賽記錄已成功刪除`)
        await handleRefreshData()
      } catch (err) {
        console.error('刪除失敗:', err)
        message.error(err.response?.data?.message || '刪除失敗')
      }
    }
  })
}

const loadPlayers = async () => {
  try {
    const response = await apiClient.get('/members?all=true&sort_by=name&sort_order=asc')

    let membersData = response.data
    if (response.data?.members) {
      membersData = response.data.members
    } else if (response.data?.data) {
      membersData = response.data.data
    }

    if (!Array.isArray(membersData)) {
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

onUnmounted(() => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
})
</script>

<style scoped>
/* === 統一設計系統 === */
.match-management-page {
  background: #f5f5f5;
  min-height: 100vh;
}

/* === 頁面標題 === */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 0;
  border-bottom: 1px solid #e9ecef;
  margin-bottom: 2rem;
}

.page-title {
  margin: 0;
  color: #2c3e50;
  font-size: 2rem;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* === 卡片樣式 === */
.search-card,
.table-card {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(15px);
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  border: 1px solid #e9ecef;
}

/* === 搜尋區域 === */
.search-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-panel {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  padding: 2rem;
  margin-top: 1rem;
  border: 1px solid #dee2e6;
  position: relative;
  overflow: hidden;
}

.search-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
}

.search-actions {
  margin-top: 1rem;
  padding-top: 1rem;
}

/* === 活躍篩選條件 === */
.active-filters {
  background: #f1f5f9;
  border-radius: 12px;
  padding: 1.5rem;
  margin-top: 1rem;
  border: 1px solid #cbd5e1;
}

.filters-container {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.filter-label {
  font-weight: 600;
  color: #475569;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
}

/* === 搜尋統計 === */
.search-stats {
  margin-top: 1rem;
}

.filter-info {
  color: #6b7280;
  font-size: 0.875rem;
}

/* === 表格樣式 === */
.table-title {
  font-weight: 600;
  color: #374151;
  display: flex;
  align-items: center;
}

/* === 搜尋高亮 === */
:deep(.search-highlight) {
  background-color: #fef3c7;
  color: #92400e;
  font-weight: 600;
  padding: 2px 4px;
  border-radius: 3px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* === 表格內容樣式 === */
.vs-separator {
  font-weight: bold;
  color: #667eea;
  font-size: 0.875rem;
}

.score-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.score-display {
  font-weight: 700;
  font-size: 1rem;
  color: #374151;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
}

.action-btn {
  transition: all 0.2s ease;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

/* === 空狀態 === */
.empty-state {
  padding: 3rem 2rem;
  text-align: center;
}

/* === 響應式設計 === */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }

  .page-title {
    font-size: 1.75rem;
  }

  .search-panel {
    padding: 1.5rem;
  }

  .filters-container {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
}

@media (max-width: 480px) {
  .page-title {
    font-size: 1.5rem;
  }

  .search-panel {
    padding: 1rem;
  }
}
</style>