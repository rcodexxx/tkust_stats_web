<template>
  <div class="match-management-page container mt-4 mb-5 px-md-4">
    <n-h1 class="page-main-title">比賽記錄管理</n-h1>

    <div class="table-actions-header d-flex justify-content-end mb-3">
      <n-button type="primary" size="small" @click="goToRecordMatchPage">
        <template #icon>
          <n-icon :component="AddIcon" />
        </template>
        記錄新比賽
      </n-button>
    </div>

    <div v-if="fetchError" class="mb-3">
      <n-alert title="錯誤" type="error" closable @close="fetchError = null">
        {{ fetchError }}
      </n-alert>
    </div>

    <n-data-table
      :columns="tableColumns"
      :data="allMatchRecords"
      :loading="loading"
      :pagination="pagination"
      :bordered="false"
      :bottom-bordered="true"
      :single-line="false"
      size="small"
      flex-height
      style="min-height: 400px; max-height: 75vh"
      :scroll-x="1000"
      :row-key="row => row.id"
    />
  </div>
</template>

<script setup>
  import { computed, h, onMounted, reactive, ref } from 'vue'
  import { useRouter } from 'vue-router'
  import {
    NAlert,
    NButton,
    NDataTable,
    NH1,
    NIcon,
    NSpace,
    NTag,
    NTooltip,
    useDialog,
    useMessage
  } from 'naive-ui'
  import {
    AddCircleOutline as AddIcon,
    PencilOutline as EditIcon,
    TrashBinOutline as DeleteIcon
  } from '@vicons/ionicons5'
  import apiClient from '@/services/apiClient'
  import { format } from 'date-fns' // 推薦使用 date-fns 來格式化日期

  // --- Hooks ---
  const router = useRouter()
  const dialog = useDialog()
  const message = useMessage()

  // --- 狀態管理 (State) ---
  const allMatchRecords = ref([])
  const loading = ref(true)
  const fetchError = ref(null)

  // --- 表格分頁設定 ---
  const pagination = reactive({
    page: 1,
    pageSize: 15,
    showSizePicker: true,
    pageSizes: [15, 30, 50, 100]
  })

  const matchTypeOptions = [
    { label: '雙打', value: 'doubles' },
    { label: '單打', value: 'singles' }
  ]
  const matchFormatOptions = [
    { label: '五局制', value: 'games_5' },
    { label: '七局制', value: 'games_7' },
    {
      label: '九局制',
      value: 'games_9'
    }
  ]

  const getMatchTypeDisplay = value =>
    matchTypeOptions.find(opt => opt.value === value)?.label || value
  const getMatchFormatDisplay = value =>
    matchFormatOptions.find(opt => opt.value === value)?.label || value

  // --- 表格欄位定義 ---
  const tableColumns = computed(() => [
    {
      title: '比賽日期',
      key: 'match_date',
      sorter: 'default',
      width: 120,
      render: row => (row.match_date ? format(new Date(row.match_date), 'yyyy-MM-dd') : '-')
    },
    {
      title: '對戰組合',
      key: 'matchup',
      resizable: true,
      width: 350,
      ellipsis: { tooltip: true },
      render(row) {
        const sideA = [row.player1?.name, row.player2?.name].filter(Boolean).join(' / ')
        const sideB = [row.player3?.name, row.player4?.name].filter(Boolean).join(' / ')
        return `${sideA || 'N/A'} vs ${sideB || 'N/A'}`
      }
    },
    {
      title: '比分',
      key: 'score',
      width: 120,
      align: 'center',
      render(row) {
        let outcomeTag = null
        if (row.side_a_outcome === 'WIN') {
          outcomeTag = h(
            NTag,
            { type: 'success', size: 'tiny', round: true },
            { default: () => 'A勝' }
          )
        } else if (row.side_a_outcome === 'LOSS') {
          outcomeTag = h(
            NTag,
            { type: 'error', size: 'tiny', round: true },
            { default: () => 'B勝' }
          )
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
      render(row) {
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

  // --- 方法 (Methods) ---
  async function fetchMatchRecords() {
    loading.value = true
    fetchError.value = null
    try {
      const response = await apiClient.get('/match-records')
      allMatchRecords.value = response.data || []
    } catch (err) {
      fetchError.value = err.response?.data?.message || '無法載入比賽記錄。'
    } finally {
      loading.value = false
    }
  }

  function goToRecordMatchPage() {
    // 跳轉到您之前建立的「記錄賽果」頁面
    router.push({ name: 'RecordMatch' })
  }

  function editMatchRecord(recordId) {
    // 未來您可以建立一個「編輯比賽記錄」的頁面
    message.info(`編輯功能待開發，目標 ID: ${recordId}`)
    // router.push({ name: 'EditMatchRecord', params: { id: recordId } });
  }

  function confirmDeleteMatch(record) {
    dialog.error({
      title: '確認刪除比賽記錄',
      // content: `您確定要刪除這場比賽記錄嗎？`,
      positiveText: '確認刪除',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await apiClient.delete(`/match-records/${record.id}`)
          message.success(`比賽記錄 #${record.id} 已成功刪除。`)
          await fetchMatchRecords() // 重新獲取列表
        } catch (err) {
          message.error(err.response?.data?.message || `刪除失敗。`)
        }
      }
    })
  }

  // --- 生命週期鉤子 (Lifecycle Hooks) ---
  onMounted(fetchMatchRecords)
</script>

<style scoped>
  /* 頁面和表格的基本樣式 */
  .match-management-page {
    max-width: 1200px; /* 您可以根據喜好調整寬度 */
    margin: 2rem auto;
  }

  .page-main-title {
    font-weight: 600;
  }
</style>
