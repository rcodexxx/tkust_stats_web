<template>
  <div class="member-management-section">
    <!-- 表格上方的操作按鈕 -->
    <div class="table-actions-header d-flex justify-content-end mb-3">
      <router-link v-slot="{ navigate }" :to="{ name: 'AddMember' }">
        <n-button type="primary" size="small" :disabled="loadingMembers" @click="navigate">
          <template #icon>
            <n-icon :component="PersonAddIcon" />
          </template>
          新增成員
        </n-button>
      </router-link>
    </div>

    <!-- 錯誤提示 -->
    <div v-if="memberError" class="mb-3">
      <n-alert title="錯誤" type="error" closable @close="memberError = null">
        {{ memberError }}
      </n-alert>
    </div>

    <!-- 成員資料表格 -->
    <n-data-table
      :columns="memberTableColumns"
      :data="paginatedMembers"
      :loading="loadingMembers"
      :pagination="paginationConfig"
      :bordered="false"
      :bottom-bordered="true"
      :single-line="false"
      size="small"
      style="min-height: 400px; max-height: 70vh"
      :scroll-x="tableScrollXWidth"
      :resizable="true"
    />

    <!-- 空狀態提示 -->
    <div v-if="!loadingMembers && filteredMembers.length === 0 && props.searchTermProp && !memberError" class="mt-3">
      <n-empty :description="`找不到符合 '${props.searchTermProp}' 的成員。`" />
    </div>
    <div v-if="!loadingMembers && allFetchedMembers.length === 0 && !memberError" class="mt-3">
      <n-empty description="目前沒有成員資料。" />
    </div>
  </div>
</template>

<script setup>
  import { computed, h, onMounted, reactive, ref, watch } from 'vue'
  import { RouterLink, useRouter } from 'vue-router'
  import apiClient from '@/services/apiClient'
  import { NAlert, NButton, NDataTable, NEmpty, NIcon, NSpace, NTag, NTooltip, useDialog, useMessage } from 'naive-ui'
  import {
    PencilOutline as EditIcon,
    PersonAddOutline as PersonAddIcon,
    TrashBinOutline as DeleteIcon
  } from '@vicons/ionicons5'

  // --- Props & Hooks ---
  const props = defineProps({
    searchTermProp: { type: String, default: '' }
  })
  const router = useRouter()
  const dialog = useDialog()
  const message = useMessage()

  // --- 狀態管理 (State) ---
  const allFetchedMembers = ref([])
  const loadingMembers = ref(true)
  const memberError = ref(null)
  const currentPage = ref(1)
  const pageSize = ref(10)

  // --- 表格分頁設定 ---
  const memberPagination = reactive({
    page: 1,
    pageSize: 10,
    showSizePicker: true,
    pageSizes: [10, 20, 30, 50],
    onChange: page => {
      currentPage.value = page
      memberPagination.page = page
    },
    onUpdatePageSize: newPageSize => {
      pageSize.value = newPageSize
      memberPagination.pageSize = newPageSize
      currentPage.value = 1
      memberPagination.page = 1
    }
  })

  // --- 輔助函數 (Helpers) ---
  function getRoleDisplay(roleValue) {
    const roles = { admin: '管理員', cadre: '幹部', coach: '教練', member: '隊員' }
    return roles[roleValue] || roleValue
  }

  function getRoleNaiveType(roleValue) {
    const types = { admin: 'error', cadre: 'warning', coach: 'success', member: 'info' }
    return types[roleValue] || 'default'
  }

  function getGenderDisplay(genderValue) {
    const genders = { male: '男', female: '女' }
    return genders[genderValue] || '-'
  }

  function getPositionDisplay(positionValue) {
    const positions = { back: '後排', front: '前排', versatile: '皆可' }
    return positions[positionValue] || '-'
  }

  // --- 表格欄位定義 ---
  const memberTableColumns = computed(() => [
    {
      title: '名稱',
      key: 'name',
      sorter: 'default',
      fixed: 'left',
      width: 150,
      resizable: true,
      ellipsis: { tooltip: true },
      render: row => {
        return h(
          RouterLink,
          { to: { name: 'EditMember', params: { id: row.id } }, class: 'table-link' },
          { default: () => row.name }
        )
      }
    },
    {
      title: '學號',
      key: 'student_id',
      sorter: 'default',
      width: 120,
      resizable: true,
      render: row => row.student_id || '-'
    },
    {
      title: '性別',
      key: 'gender',
      width: 80,
      align: 'center',
      filterOptions: [
        { label: '男', value: 'male' },
        { label: '女', value: 'female' }
      ],
      filter: (value, row) => row.gender === value,
      render: row => getGenderDisplay(row.gender)
    },
    {
      title: '位置',
      key: 'position',
      width: 100,
      align: 'center',
      filterOptions: [
        { label: '後排', value: 'back' },
        { label: '前排', value: 'front' },
        { label: '皆可', value: 'versatile' }
      ],
      filter: (value, row) => row.position === value,
      render: row => getPositionDisplay(row.position)
    },
    {
      title: '組織',
      key: 'organization_name',
      sorter: 'default',
      width: 180,
      resizable: true,
      ellipsis: { tooltip: true },
      render: row => row.organization?.short_name || row.organization?.name || '-'
    },
    {
      title: 'μ',
      key: 'mu',
      sorter: (a, b) => a.mu - b.mu,
      width: 80,
      resizable: true,
      align: 'right',
      render: row => row.mu?.toFixed(2) || '-'
    },
    {
      title: '角色',
      key: 'user.role',
      width: 110,
      resizable: true,
      align: 'center',
      filterOptions: [
        { label: '管理員', value: 'admin' },
        { label: '幹部', value: 'cadre' },
        { label: '教練', value: 'coach' },
        { label: '隊員', value: 'member' }
      ],
      filter: (value, row) => row.user?.role === value,
      render: row => {
        const role = row.user?.role
        return role
          ? h(
              NTag,
              { type: getRoleNaiveType(role), size: 'small', round: true },
              { default: () => getRoleDisplay(role) }
            )
          : h('span', { class: 'text-muted' }, '無')
      }
    },
    {
      title: '操作',
      key: 'actions',
      fixed: 'right',
      width: 100,
      align: 'center',
      render: row => {
        return h(NSpace, { justify: 'center' }, () => [
          h(NTooltip, null, {
            trigger: () =>
              h(
                NButton,
                {
                  size: 'tiny',
                  circle: true,
                  onClick: () => editMember(row.id)
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
                  onClick: () => confirmDeleteMember(row)
                },
                { icon: () => h(NIcon, { component: DeleteIcon }) }
              ),
            default: () => '刪除'
          })
        ])
      }
    }
  ])

  // --- 計算屬性 ---
  const tableScrollXWidth = computed(() => {
    return memberTableColumns.value.reduce((sum, col) => sum + (col.width || 120), 0)
  })

  // 過濾後的成員數據
  const filteredMembers = computed(() => {
    const term = props.searchTermProp.toLowerCase().trim()
    if (!term) {
      return allFetchedMembers.value
    }
    return allFetchedMembers.value.filter(member => {
      // 搜尋多個欄位
      const searchFields = [
        member.name,
        member.display_name,
        member.user?.display_name,
        member.student_id,
        member.organization?.name,
        member.organization?.short_name,
        member.user?.username
      ]

      return searchFields.some(field => field && String(field).toLowerCase().includes(term))
    })
  })

  // 分頁後的數據
  const paginatedMembers = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    return filteredMembers.value.slice(start, end)
  })

  // 分頁配置
  const paginationConfig = computed(() => ({
    ...memberPagination,
    page: currentPage.value,
    pageSize: pageSize.value,
    itemCount: filteredMembers.value.length,
    prefix: ({ itemCount }) => `共 ${itemCount} 位成員`
  }))

  // --- API 呼叫與邏輯 ---
  async function fetchMembers() {
    loadingMembers.value = true
    memberError.value = null
    try {
      const response = await apiClient.get('/members', { params: { all: true } })
      allFetchedMembers.value = response.data || []
    } catch (err) {
      memberError.value = err.response?.data?.message || '無法載入成員列表。'
    } finally {
      loadingMembers.value = false
    }
  }

  // --- 生命週期 ---
  onMounted(fetchMembers)

  // 監聽搜尋條件變化，重置到第一頁
  watch(
    () => props.searchTermProp,
    () => {
      currentPage.value = 1
      memberPagination.page = 1
    }
  )

  // --- 操作方法 ---
  function editMember(memberId) {
    router.push({ name: 'EditMember', params: { id: memberId } })
  }

  function confirmDeleteMember(member) {
    dialog.error({
      title: '確認刪除',
      content: () => `您確定要刪除成員 "${member.name}" 嗎？此操作將一併刪除其關聯的登入帳號，且無法復原！`,
      positiveText: '確認刪除',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await apiClient.delete(`/members/${member.id}`)
          message.success(`成員 ${member.name} 已成功刪除。`)
          await fetchMembers()
        } catch (err) {
          message.error(err.response?.data?.message || `刪除失敗。`)
        }
      }
    })
  }
</script>

<style scoped>
  :deep(.table-link) {
    color: var(--n-text-color); /* 使用 Naive UI 的基本文字顏色變數 */
    text-decoration: none;
    font-weight: 500;
  }

  :deep(.table-link:hover) {
    color: var(--n-primary-color); /* 滑鼠懸停時使用主題主要顏色 */
    text-decoration: underline;
  }

  /* 讓已訪問和未訪問的連結顏色保持一致 */
  :deep(.table-link:visited) {
    color: var(--n-text-color);
  }

  /* Naive UI 表格的 sticky column 背景通常由其主題控制，
   如果需要覆蓋，可以使用 :deep() 選擇器 */
  :deep(.n-data-table .n-data-table-th--fixed-left),
  :deep(.n-data-table .n-data-table-td--fixed-left) {
    background-color: var(--card-color, #fff) !important; /* 確保背景色 */
  }

  :deep(.n-data-table .n-data-table-th--fixed-right),
  :deep(.n-data-table .n-data-table-td--fixed-right) {
    background-color: var(--card-color, #fff) !important;
  }

  :deep(.n-data-table thead .n-data-table-th--fixed-left),
  :deep(.n-data-table thead .n-data-table-th--fixed-right) {
    background-color: var(--th-color, #fafafc) !important; /* Naive UI 表頭背景色 */
  }

  /* 如果您在 App.vue 中為 table-dark 設定了更深的顏色，這裡也需要對應 */
  .table-dark :deep(.n-data-table .n-data-table-th--fixed-left),
  .table-dark :deep(.n-data-table .n-data-table-th--fixed-right) {
    background-color: #2a3a51 !important; /* 您的深色表頭背景 (示例) */
  }
</style>
