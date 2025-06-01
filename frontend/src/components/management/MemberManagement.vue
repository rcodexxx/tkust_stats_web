<template>
  <div class="member-management-section">
    <div
        class="table-actions-header d-flex flex-column flex-sm-row justify-content-sm-end align-items-stretch align-items-sm-center mb-3 gap-2">
      <router-link :to="{ name: 'AddMember' }" v-slot="{ navigate }">
        <n-button type="primary" size="small" @click="navigate" :disabled="loadingMembers">
          <template #icon>
            <n-icon :component="PersonAddIcon"/>
          </template>
          新增成員
        </n-button>
      </router-link>
    </div>

    <div v-if="memberError" class="mb-3">
      <n-alert title="錯誤" type="error" closable @close="memberError = null">
        {{ memberError }}
      </n-alert>
    </div>

    <n-data-table
        :columns="memberTableColumns"
        :data="filteredDataForTable"
        :loading="loadingMembers"
        :pagination="memberPaginationReactive"
        :bordered="false"
        :bottom-bordered="true"
        :single-line="false"
        size="small"
        flex-height
        style="min-height: 450px; max-height: 70vh;"
        :scroll-x="tableScrollXWidth"
        :resizable="true"
        @update:sorter="handleMemberSortChange"
        :row-key="row => row.id"
    />

    <div v-if="!loadingMembers && filteredDataForTable.length === 0 && props.searchTermProp && !memberError"
         class="mt-3">
      <n-empty :description="`找不到符合 '${props.searchTermProp}' 的成員。`"/>
    </div>
    <div v-if="!loadingMembers && allFetchedMembers.length === 0 && !memberError" class="mt-3">
      <n-empty description="目前沒有成員資料。"/>
    </div>
  </div>
</template>

<script setup>
import {computed, h, onMounted, reactive, ref, watch} from 'vue';
import {useRouter} from 'vue-router';
import memberService from '@/services/memberService';
import {NAlert, NButton, NDataTable, NEmpty, NIcon, NSpace, NTag, NTooltip, useDialog, useMessage} from 'naive-ui';
import {
  PencilOutline as EditIcon,
  PersonAddOutline as PersonAddIcon,
  TrashBinOutline as DeleteIcon,
} from '@vicons/ionicons5';

const props = defineProps({
  searchTermProp: {
    type: String,
    default: ''
  }
});

const router = useRouter();
const dialog = useDialog();
const message = useMessage();

const allFetchedMembers = ref([]);
const loadingMembers = ref(true);
const memberError = ref(null);

const memberPaginationReactive = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 30, 50],
  onChange: (page) => {
    memberPaginationReactive.page = page;
  },
  onUpdatePageSize: (pageSize) => {
    memberPaginationReactive.pageSize = pageSize;
    memberPaginationReactive.page = 1;
  }
});

const tableSortState = ref(null);

function handleMemberSortChange(sorter) {
  tableSortState.value = sorter;
  // Naive UI data table handles client-side sorting automatically if sorter is defined in columns
  // If you need to trigger a re-sort or custom logic, you can do it here
}

// 列定義 (Naive UI Columns)
const memberTableColumns = computed(() => [
  {
    title: "名稱(帳號)",
    key: "name",
    sorter: 'default',
    fixed: 'left',
    width: 180,
    resizable: true,
    ellipsis: {tooltip: true},
    render(row) {
      return h('div', [
        h('span', {style: {fontWeight: '500'}}, row.name),
        row.username ? h('small', {class: 'd-block text-muted'}, `(${row.username})`) : null
      ]);
    }
  },
  {
    title: "學號",
    key: "student_id",
    sorter: 'default',
    fixed: 'left',
    width: 120,
    resizable: true,
    ellipsis: {tooltip: true},
    render: (row) => row.student_id || '-'
  },
  {
    title: "組織",
    key: "organization_name",
    sorter: 'default',
    width: 150,
    resizable: true,
    ellipsis: {tooltip: true},
    render: (row) => row.organization_name || '-'
  },
  {title: "分數", key: "score", sorter: (a, b) => a.score - b.score, width: 80, resizable: true, align: 'right'},
  {
    title: "μ",
    key: "mu",
    sorter: (a, b) => a.mu - b.mu,
    width: 70,
    resizable: true,
    align: 'right',
    render: (row) => row.mu?.toFixed(1) || '-'
  },
  {
    title: "角色", key: "user_role",
    sorter: (a, b) => getRoleDisplay(a.user_role).localeCompare(getRoleDisplay(b.user_role), 'zh-Hant-TW'),
    width: 100, resizable: true, align: 'center',
    filterOptions: [
      {label: '管理員', value: 'ADMIN'}, {label: '幹部', value: 'CADRE'},
      {label: '隊員', value: 'PLAYER'}, {label: '教練', value: 'COACH'}
    ],
    filter(value, row) {
      return row.user_role === value;
    },
    render(row) {
      return row.user_role
          ? h(NTag, {type: getRoleNaiveType(row.user_role), size: 'small', round: true, bordered: false},
              {default: () => getRoleDisplay(row.user_role)})
          : h('span', {class: 'text-muted'}, '無帳號');
    }
  },
  {
    title: "操作", key: "actions", fixed: 'right', width: 100, align: 'center', resizable: false,
    render(row) {
      return h(NSpace, {justify: 'center'}, () => [
        h(NTooltip, null, {
          trigger: () => h(NButton, {size: 'tiny', circle: true, quaternary: true, onClick: () => editMember(row.id)},
              {icon: () => h(NIcon, {component: EditIcon})}
          ),
          default: () => '編輯成員'
        }),
        h(NTooltip, null, {
          trigger: () => h(NButton, {
                size: 'tiny',
                circle: true,
                quaternary: true,
                type: 'error',
                onClick: () => confirmDeleteMember(row)
              },
              {icon: () => h(NIcon, {component: DeleteIcon})}
          ),
          default: () => '刪除成員'
        })
      ]);
    }
  }
]);

// 計算表格的 scroll-x 以觸發固定列，基於可見列的總寬度
const tableScrollXWidth = computed(() => {
  let totalWidth = 0;
  memberTableColumns.value.forEach(col => {
    // 這裡可以加入邏輯，如果未來有 column visibility 控制
    totalWidth += (col.width || 120); // 如果沒有設定 width，給一個預設值
  });
  // 如果總寬度小於某個閾值 (例如視窗寬度)，可以不設定 scroll-x，讓表格自然排列
  // 但為了確保 sticky column 總能工作 (因為它們依賴於可滾動的容器)，通常會設定一個值
  return totalWidth;
});

async function fetchMembers() {
  loadingMembers.value = true;
  memberError.value = null;
  try {
    const response = await memberService.getAllMembers(false); // false = 獲取所有成員
    allFetchedMembers.value = response.data || [];
  } catch (err) {
    console.error("Error fetching members for Naive Table:", err.response || err);
    memberError.value = err.response?.data?.error || err.message || "無法載入成員列表。";
    allFetchedMembers.value = [];
  } finally {
    loadingMembers.value = false;
  }
}

onMounted(fetchMembers);

// 過濾後的數據傳給 n-data-table
const filteredDataForTable = computed(() => {
  let dataToFilter = allFetchedMembers.value;
  const term = props.searchTermProp.toLowerCase().trim();

  if (!term) {
    memberPaginationReactive.itemCount = dataToFilter.length; // 更新總條目數
    return dataToFilter;
  }
  const filtered = dataToFilter.filter(member => {
    return (
        member.name?.toLowerCase().includes(term) ||
        (member.username && member.username.toLowerCase().includes(term)) ||
        (member.student_id && member.student_id.toLowerCase().includes(term)) ||
        (member.organization_name && member.organization_name.toLowerCase().includes(term)) ||
        (member.user_role && getRoleDisplay(member.user_role).toLowerCase().includes(term))
    );
  });
  memberPaginationReactive.itemCount = filtered.length; // 更新總條目數
  return filtered;
});

watch(() => props.searchTermProp, () => {
  memberPaginationReactive.page = 1; // 搜尋詞改變時，回到第一頁
});


// --- Modal 相關 ---
const memberToDelete = ref(null);

function confirmDeleteMember(member) {
  memberToDelete.value = {id: member.id, name: member.name};
  dialog.error({
    title: '確認刪除',
    content: () => `您確定要刪除成員 "${member.name}" (ID: ${member.id}) 嗎？此操作通常會一併刪除其關聯的登入帳號，且可能無法復原！`,
    positiveText: '確認刪除',
    negativeText: '取消',
    maskClosable: false,
    onPositiveClick: async () => {
      if (!memberToDelete.value?.id) return;
      try {
        await memberService.deleteMember(memberToDelete.value.id);
        message.success(`成員 ${memberToDelete.value.name} 已成功刪除。`);
        fetchMembers(); // 重新獲取列表
      } catch (err) {
        console.error("Error deleting member:", err.response || err);
        message.error(`刪除成員失敗: ${err.response?.data?.error || err.message}`);
      } finally {
        memberToDelete.value = null;
      }
    },
    onNegativeClick: () => {
      memberToDelete.value = null;
      message.info('已取消刪除');
    }
  });
}

// --- 輔助函數 ---
function getRoleDisplay(roleName) {
  if (roleName === 'ADMIN') return '管理員';
  if (roleName === 'CADRE') return '幹部';
  if (roleName === 'COACH') return '教練';
  if (roleName === 'PLAYER') return '隊員';
  return roleName || 'N/A';
}

function getRoleNaiveType(roleName) { // 用於 Naive UI Tag 的 type
  if (roleName === 'ADMIN') return 'error';
  if (roleName === 'CADRE') return 'warning';
  if (roleName === 'PLAYER') return 'info';
  if (roleName === 'COACH') return 'success'; // 例如
  return 'default';
}

function editMember(memberId) {
  router.push({name: 'AdminEditMember', params: {id: memberId}});
}

</script>

<style scoped>
.member-management-section {
  /* background-color: #fff; */
  padding: 15px;
  border-radius: 8px;
  /* box-shadow: 0 1px 3px rgba(0,0,0,0.05); */
}

.table-actions-header {
  /* 樣式微調 */
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
.table-dark :deep(.n-data-table-th--fixed-left), /* 針對 .table-dark 容器內的 n-data-table */
.table-dark :deep(.n-data-table-th--fixed-right) {
  background-color: #2a3a51 !important; /* 您的深色表頭背景 */
}

</style>