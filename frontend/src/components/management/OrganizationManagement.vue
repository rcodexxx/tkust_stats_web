// frontend/src/components/management/OrganizationManagement.vue
<template>
  <div class="organization-management-section mt-4">
    <div class="table-actions-header d-flex justify-content-end mb-3">
      <n-button type="primary" size="small" @click="openOrgFormModal(null)">
        <template #icon>
          <n-icon :component="BuildingAddIcon"/>
        </template>
        新增組織
      </n-button>
    </div>

    <div v-if="orgError" class="mb-3">
      <n-alert title="錯誤" type="error" closable @close="orgError = null">
        {{ orgError }}
      </n-alert>
    </div>
    <n-data-table
        :columns="organizationTableColumns"
        :data="filteredOrganizationData"
        :loading="loadingOrgs"
        :pagination="organizationPaginationReactive"
        :bordered="false"
        :bottom-bordered="true" સલામત :single-line="false"
        size="small"
        flex-height
        style="min-height: 400px; max-height: 70vh;"
        :scroll-x="organizationTableScrollXWidth" :resizable="true"
        @update:sorter="handleOrgSortChange"
        :row-key="row => row.id"
    />

    <div v-if="!loadingOrgs && filteredOrganizationData.length === 0 && props.searchTermProp && !orgError" class="mt-3">
      <n-empty :description="`找不到符合 '${props.searchTermProp}' 的組織。`"/>
    </div>
    <div v-if="!loadingOrgs && allFetchedOrganizations.length === 0 && !orgError" class="mt-3">
      <n-empty description="目前沒有組織資料。"/>
    </div>

    <n-modal
        v-model:show="showOrgFormModal"
        :mask-closable="false"
        preset="card"
        :title="isEditingOrg ? '編輯組織' : '新增組織'"
        style="width: 600px;"
        :bordered="true"
    >
      <n-form
          ref="orgFormRef"
          :model="currentOrganization"
          :rules="orgFormRules"
          label-placement="left"
          label-width="auto"
          require-mark-placement="right-hanging"
      >
        <n-form-item label="組織全名" path="name">
          <n-input v-model:value="currentOrganization.name" placeholder="請輸入組織全名"/>
        </n-form-item>
        <n-form-item label="城市" path="city">
          <n-input v-model:value="currentOrganization.city" placeholder="請輸入城市 (可選)"/>
        </n-form-item>
        <n-form-item label="備註" path="notes">
          <n-input type="textarea" v-model:value="currentOrganization.notes" placeholder="備註說明 (可選)"/>
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showOrgFormModal = false">取消</n-button>
          <n-button type="primary" @click="handleOrgFormSubmit" :loading="orgFormSubmitting">
            {{ isEditingOrg ? '更新組織' : '確認新增' }}
          </n-button>
        </n-space>
      </template>
    </n-modal>

  </div>
</template>

<script setup>
import {computed, h, onMounted, reactive, ref, watch} from 'vue';
import organizationService from '@/services/organizationService'; // 確保路徑正確
import {
  NAlert,
  NButton,
  NDataTable,
  NEmpty,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NModal,
  NSpace,
  NTooltip,
  useDialog,
  useMessage
} from 'naive-ui';
import {
  AddCircleOutline as BuildingAddIcon,
  PencilOutline as EditIcon,
  TrashBinOutline as DeleteIcon
} from '@vicons/ionicons5';

// ... (props, dialog, message, allFetchedOrganizations, loadingOrgs, orgError, etc. remain the same) ...
const props = defineProps({
  searchTermProp: {type: String, default: ''}
});

const dialog = useDialog();
const message = useMessage();

const allFetchedOrganizations = ref([]);
const loadingOrgs = ref(true);
const orgError = ref(null);

const organizationPaginationReactive = reactive({
  page: 1, pageSize: 10, itemCount: 0, showSizePicker: true, pageSizes: [10, 20, 50],
  onChange: (page) => organizationPaginationReactive.page = page,
  onUpdatePageSize: (pageSize) => {
    organizationPaginationReactive.pageSize = pageSize;
    organizationPaginationReactive.page = 1;
  }
});

const orgTableSortState = ref(null);

function handleOrgSortChange(sorter) {
  orgTableSortState.value = sorter;
}

const showOrgFormModal = ref(false);
const isEditingOrg = ref(false);
const orgFormSubmitting = ref(false);
const orgFormRef = ref(null);
const currentOrganization = reactive({id: null, name: '', short_name: '', city: '', notes: ''});
const orgToDelete = ref(null); // Used to store the org object for deletion

const orgFormRules = {
  name: [{required: true, message: '組織全名為必填', trigger: ['input', 'blur']}],
};

const organizationTableColumns = computed(() => [
  {title: "組織全名", key: "name", sorter: 'default', resizable: true, width: 200, ellipsis: {tooltip: true}},
  {
    title: "城市",
    key: "city",
    sorter: 'default',
    resizable: true,
    width: 100,
    ellipsis: {tooltip: true},
    render: (row) => row.city || '-'
  },
  {
    title: "成員數",
    key: "member_count",
    sorter: (a, b) => a.member_count - b.member_count,
    resizable: true,
    width: 90,
    align: 'right',
    render: (row) => row.member_count === undefined ? '-' : row.member_count // Handle undefined
  },
  {
    title: "操作", key: "actions", width: 100, align: 'center', fixed: 'right', resizable: false,
    render(row) {
      return h(NSpace, {justify: 'center'}, () => [
        h(NTooltip, null, {
          trigger: () => h(NButton, {
                size: 'tiny',
                circle: true,
                quaternary: true,
                onClick: () => openOrgFormModal(row)
              },
              {icon: () => h(NIcon, {component: EditIcon})}
          ),
          default: () => '編輯組織'
        }),
        h(NTooltip, null, {
          trigger: () => h(NButton, {
                size: 'tiny',
                circle: true,
                quaternary: true,
                type: 'error',
                // Disable delete if member_count > 0
                disabled: row.member_count > 0,
                onClick: () => confirmDeleteOrganization(row)
              },
              {icon: () => h(NIcon, {component: DeleteIcon})}
          ),
          default: () => row.member_count > 0 ? `組織尚有 ${row.member_count} 位成員，無法刪除` : '刪除組織'
        })
      ]);
    }
  }
]);

// Variable to allow deletion even if members exist (for admin override, if needed in future)
// For now, we disable based on member_count directly in button
// const allowDeleteOrgWithMembers = ref(false);

async function fetchOrganizations() {
  loadingOrgs.value = true;
  orgError.value = null;
  try {
    const response = await organizationService.getOrganizations();
    allFetchedOrganizations.value = response.data || [];
  } catch (err) {
    console.error("Error fetching organizations:", err.response || err);
    orgError.value = err.response?.data?.error || err.message || "無法載入組織列表。";
    allFetchedOrganizations.value = [];
  } finally {
    loadingOrgs.value = false;
  }
}

onMounted(fetchOrganizations);

const filteredOrganizationData = computed(() => {
  let dataToFilter = allFetchedOrganizations.value;
  const term = props.searchTermProp.toLowerCase().trim();
  if (!term) {
    organizationPaginationReactive.itemCount = dataToFilter.length;
    return dataToFilter;
  }
  const filtered = dataToFilter.filter(org =>
      org.name?.toLowerCase().includes(term) ||
      (org.short_name && org.short_name.toLowerCase().includes(term)) ||
      (org.city && org.city.toLowerCase().includes(term))
  );
  organizationPaginationReactive.itemCount = filtered.length;
  return filtered;
});

watch(() => props.searchTermProp, () => {
  organizationPaginationReactive.page = 1;
});

function openOrgFormModal(org = null) {
  if (org) {
    isEditingOrg.value = true;
    Object.assign(currentOrganization, org);
  } else {
    isEditingOrg.value = false;
    Object.assign(currentOrganization, {id: null, name: '', short_name: '', city: '', notes: ''});
  }
  showOrgFormModal.value = true;
}

async function handleOrgFormSubmit() {
  orgFormRef.value?.validate(async (errors) => {
    if (!errors) {
      orgFormSubmitting.value = true;
      const payload = {
        name: currentOrganization.name.trim(),
        short_name: currentOrganization.short_name?.trim() || null,
        city: currentOrganization.city?.trim() || null,
        notes: currentOrganization.notes?.trim() || null,
      };
      try {
        if (isEditingOrg.value && currentOrganization.id) {
          await organizationService.updateOrganization(currentOrganization.id, payload);
          message.success("組織已成功更新！");
        } else {
          await organizationService.createOrganization(payload);
          message.success("組織已成功新增！");
        }
        fetchOrganizations();
        showOrgFormModal.value = false;
      } catch (err) {
        console.error("Error submitting org form:", err.response || err);
        message.error(err.response?.data?.error || err.response?.data?.message || "操作失敗。");
      } finally {
        orgFormSubmitting.value = false;
      }
    } else {
      message.error('請檢查表單輸入。');
    }
  });
}

function confirmDeleteOrganization(org) {
  if (org.member_count > 0) {
    dialog.warning({ // Changed to warning, as it's more of a pre-condition failure
      title: '無法刪除',
      content: () => `組織 "${org.name}" 尚有關聯 ${org.member_count} 位成員，請先將成員移至其他組織或處理後再嘗試刪除。`,
      positiveText: '知道了',
      maskClosable: false,
    });
    return;
  }

  orgToDelete.value = org; // Store the org to delete
  dialog.error({
    title: '確認刪除組織',
    content: () => `您確定要刪除組織 "${org.name}" (ID: ${org.id}) 嗎？此操作無法復原！`,
    positiveText: '確認刪除',
    negativeText: '取消',
    maskClosable: false,
    onPositiveClick: async () => {
      await executeDeleteOrganization(); // Call the actual delete function
    },
    onNegativeClick: () => {
      orgToDelete.value = null; // Clear if cancelled
      message.info('已取消刪除操作');
    }
  });
}

// ****** 這裏是完成的 executeDeleteOrganization 函數 ******
async function executeDeleteOrganization() {
  if (!orgToDelete.value?.id) {
    message.error('沒有選中要刪除的組織。');
    return;
  }
  try {
    await organizationService.deleteOrganization(orgToDelete.value.id);
    message.success(`組織 "${orgToDelete.value.name}" 已成功刪除。`);
    fetchOrganizations(); // Refresh the list
  } catch (err) {
    console.error("Error deleting organization:", err.response || err);
    message.error(`刪除組織 "${orgToDelete.value.name}" 失敗: ${err.response?.data?.error || err.message}`);
  } finally {
    orgToDelete.value = null; // Clear after attempting delete
  }
}
</script>

<style scoped>
/* .organization-management-section { } */ /* 如果沒有特殊樣式，可以移除 */
/* .table-actions-header { } */ /* 如果沒有特殊樣式，可以移除 */

/* .table-sm th, .table-sm td { } */ /* Naive UI Table size="small" 已很緊湊, 通常不需額外設定 */


/* 新增：與 MemberManagement.vue 一致的固定列背景樣式 */
:deep(.n-data-table .n-data-table-th--fixed-left),
:deep(.n-data-table .n-data-table-td--fixed-left) {
  background-color: var(--card-color, #fff) !important;
}

:deep(.n-data-table .n-data-table-th--fixed-right),
:deep(.n-data-table .n-data-table-td--fixed-right) {
  background-color: var(--card-color, #fff) !important;
}

:deep(.n-data-table thead .n-data-table-th--fixed-left),
:deep(.n-data-table thead .n-data-table-th--fixed-right) {
  background-color: var(--th-color, #fafafc) !important;
}

.table-dark :deep(.n-data-table .n-data-table-th--fixed-left),
.table-dark :deep(.n-data-table .n-data-table-th--fixed-right) {
  background-color: #2a3a51 !important; /* 您的深色表頭背景 (示例) */
}
</style>