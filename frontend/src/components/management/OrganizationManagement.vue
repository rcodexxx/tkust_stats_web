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
    <div v-if="orgSubmitMessage"
         :class="['mb-3', 'alert', orgSubmitStatus === 'success' ? 'alert-success' : 'alert-danger']" role="alert">
      {{ orgSubmitMessage }}
    </div>

    <n-data-table
        :columns="organizationTableColumns"
        :data="filteredOrganizationData"
        :loading="loadingOrgs"
        :pagination="organizationPaginationReactive"
        :bordered="false"
        :single-line="false"
        size="small"
        flex-height
        style="min-height: 400px; max-height: 70vh;"
        scroll-x="600"
        resizable
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
        <n-form-item label="組織簡稱" path="short_name">
          <n-input v-model:value="currentOrganization.short_name" placeholder="請輸入組織簡稱 (可選)"/>
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
  useDialog,
  useMessage
} from 'naive-ui';
import {
  AddCircleOutline as BuildingAddIcon,
  PencilOutline as EditIcon,
  TrashBinOutline as DeleteIcon
} from '@vicons/ionicons5';

const props = defineProps({
  searchTermProp: {type: String, default: ''}
});

const dialog = useDialog();
const message = useMessage();

const allFetchedOrganizations = ref([]);
const loadingOrgs = ref(true);
const orgError = ref(null);

// Pagination state
const organizationPaginationReactive = reactive({
  page: 1, pageSize: 10, itemCount: 0, showSizePicker: true, pageSizes: [10, 20, 50],
  onChange: (page) => organizationPaginationReactive.page = page,
  onUpdatePageSize: (pageSize) => {
    organizationPaginationReactive.pageSize = pageSize;
    organizationPaginationReactive.page = 1;
  }
});

// Sort state
const orgTableSortState = ref(null);

function handleOrgSortChange(sorter) {
  orgTableSortState.value = sorter;
}

// Modal and Form state
const showOrgFormModal = ref(false);
const isEditingOrg = ref(false);
const orgFormSubmitting = ref(false);
const orgFormValidationError = ref(null); // 其實 Naive Form 有自己的驗證顯示
const orgFormRef = ref(null); // Ref for NForm instance
const currentOrganization = reactive({id: null, name: '', short_name: '', city: '', notes: ''});
const orgToDelete = ref(null);

const orgFormRules = {
  name: [{required: true, message: '組織全名為必填', trigger: ['input', 'blur']}],
  // short_name, city, notes 設為非必填
};

// Column Definitions
const organizationTableColumns = computed(() => [
  {title: "組織全名", key: "name", sorter: 'default', resizable: true, width: 200, ellipsis: {tooltip: true}},
  {
    title: "簡稱",
    key: "short_name",
    sorter: 'default',
    resizable: true,
    width: 120,
    ellipsis: {tooltip: true},
    render: (row) => row.short_name || '-'
  },
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
    render: (row) => row.member_count || 0
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
                onClick: () => confirmDeleteOrganization(row)
              },
              {icon: () => h(NIcon, {component: DeleteIcon})}
          ),
          default: () => '刪除組織'
        })
      ]);
    }
  }
]);

async function fetchOrganizations() {
  loadingOrgs.value = true;
  orgError.value = null;
  try {
    const response = await organizationService.getOrganizations(); // 假設可以接受搜尋參數
    allFetchedOrganizations.value = response.data || [];
  } catch (err) { /* ... */
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
  // orgFormValidationError.value = null; // Naive Form 會自己處理
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
      orgSubmitMessage.value = ''; // 清除列表上方的訊息
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
      console.log('Organization form validation errors:', errors);
      message.error('請檢查表單輸入。');
    }
  });
}

function confirmDeleteOrganization(org) {
  orgToDelete.value = org;
  dialog.error({
    title: '確認刪除組織',
    content: () => `您確定要刪除組織 "${org.name}" (ID: ${org.id}) 嗎？${org.member_count > 0 ? `\n注意：此組織尚有關聯 ${org.member_count} 位成員！刪除前請先處理這些成員。` : '\n此操作無法復原！'}`,
    positiveText: '確認刪除',
    negativeText: '取消',
    maskClosable: false,
    positiveButtonProps: {disabled: org.member_count > 0 && !allowDeleteOrgWithMembers.value},
    onPositiveClick: async () => { /* ... executeDeleteOrganization ... */
    },
    onNegativeClick: () => {
      orgToDelete.value = null;
    }
  });
}

async function executeDeleteOrganization() { /* ... (與 Member 類似，調用 org service) ... */
}

// 清除訊息
const orgSubmitMessage = ref('');
const orgSubmitStatus = ref(''); // 'success' or 'error'

</script>

<style scoped>
/* OrganizationManagement.vue 特有的樣式 */
.table-actions-header {
  /* 可以調整按鈕和搜尋框的對齊 */
}

.table-sm th, .table-sm td { /* Naive UI Table size="small" 已經很緊湊 */
  /* padding: 0.5rem; */
  /* font-size: 0.85rem; */
}
</style>