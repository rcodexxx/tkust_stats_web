<template>
  <div class="organization-management-section">
    <!-- 表格上方的操作按鈕 -->
    <div class="table-actions-header d-flex justify-content-end mb-3">
      <n-button type="primary" size="small" @click="openFormModal(null)">
        <template #icon>
          <n-icon :component="BuildingAddIcon"/>
        </template>
        新增組織
      </n-button>
    </div>

    <!-- 錯誤提示 -->
    <div v-if="fetchError" class="mb-3">
      <n-alert title="錯誤" type="error" closable @close="fetchError = null">
        {{ fetchError }}
      </n-alert>
    </div>

    <!-- 組織資料表格 -->
    <n-data-table
        :columns="tableColumns"
        :data="filteredOrganizations"
        :loading="loading"
        :pagination="pagination"
        :bordered="false"
        :bottom-bordered="true"
        :single-line="false"
        size="small"
        flex-height
        style="min-height: 400px; max-height: 70vh;"
        :scroll-x="tableScrollXWidth"
        :resizable="true"
    />

    <!-- 空狀態提示 -->
    <div v-if="!loading && filteredOrganizations.length === 0" class="mt-3">
      <n-empty
          :description="props.searchTermProp ? `找不到符合 '${props.searchTermProp}' 的組織。` : '目前沒有組織資料。'"/>
    </div>

    <n-modal
        v-model:show="showFormModal"
        :mask-closable="false"
        preset="card"
        :title="isEditing ? '編輯組織' : '新增組織'"
        style="width: 650px; padding: 24px;"
        :bordered="true"
    >
      <n-form
          ref="formRef"
          :model="currentOrg"
          :rules="formRules"
          label-placement="top"
          @submit.prevent="handleFormSubmit"
      >
        <n-grid :x-gap="24" :cols="2">
          <n-form-item-gi :span="1" label="組織全名*" path="name">
            <n-input v-model:value="currentOrg.name" placeholder="請輸入組織全名"/>
          </n-form-item-gi>
          <n-form-item-gi :span="1" label="組織簡稱" path="short_name">
            <n-input v-model:value="currentOrg.short_name" placeholder="例如：台大軟網"/>
          </n-form-item-gi>
        </n-grid>

        <n-form-item label="組織描述" path="description">
          <n-input type="textarea" v-model:value="currentOrg.description" placeholder="關於組織的簡介 (選填)"/>
        </n-form-item>

        <n-divider title-placement="left" class="section-divider">聯絡資訊</n-divider>

        <n-grid :x-gap="24" :cols="2">
          <n-form-item-gi :span="1" label="主要聯絡人" path="contact_person">
            <n-input v-model:value="currentOrg.contact_person" placeholder="選填"/>
          </n-form-item-gi>
          <n-form-item-gi :span="1" label="聯絡電話" path="contact_phone">
            <n-input v-model:value="currentOrg.contact_phone" placeholder="選填"/>
          </n-form-item-gi>
        </n-grid>
        <n-form-item label="聯絡Email" path="contact_email">
          <n-input v-model:value="currentOrg.contact_email" placeholder="選填"/>
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showFormModal = false">取消</n-button>
          <n-button type="primary" @click="handleFormSubmit" :loading="submitting">
            {{ isEditing ? '確認更新' : '確認新增' }}
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import {computed, h, onMounted, reactive, ref, watch} from 'vue';
import {
  NAlert,
  NButton,
  NDataTable,
  NEmpty,
  NForm,
  NFormItem,
  NFormItemGi,
  NGrid,
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
import apiClient from '@/services/apiClient';

// --- Props & Hooks ---
const props = defineProps({
  searchTermProp: {type: String, default: ''}
});
const dialog = useDialog();
const message = useMessage();

// --- 狀態管理 (State) ---
const allOrganizations = ref([]);
const loading = ref(true);
const fetchError = ref(null);

// Modal 相關狀態
const showFormModal = ref(false);
const isEditing = ref(false);
const submitting = ref(false);
const formRef = ref(null);
const currentOrg = reactive({
  id: null, name: '', short_name: '', description: '',
  contact_person: '', contact_email: '', contact_phone: ''
});

// 表單驗證規則
const formRules = {
  name: [{required: true, message: '組織全名為必填', trigger: ['input', 'blur']}],
  contact_email: [{type: 'email', message: '請輸入有效的電子郵件格式', trigger: ['blur']}]
};

// --- 表格相關 ---
const pagination = reactive({
  page: 1, pageSize: 10, showSizePicker: true,
  pageSizes: [10, 20, 50]
});

const tableColumns = computed(() => [
  {title: "組織全名", key: "name", sorter: 'default', resizable: true, width: 200, ellipsis: {tooltip: true}},
  {
    title: "組織簡稱",
    key: "short_name",
    sorter: 'default',
    resizable: true,
    width: 150,
    render: (row) => row.short_name || '-'
  },
  {
    title: "聯絡人",
    key: "contact_person",
    sorter: 'default',
    resizable: true,
    width: 120,
    render: (row) => row.contact_person || '-'
  },
  {
    title: "成員數",
    key: "members_count",
    sorter: (a, b) => a.members_count - b.members_count,
    resizable: true,
    width: 90,
    align: 'right'
  },
  {
    title: "操作", key: "actions", width: 100, align: 'center', fixed: 'right',
    render(row) {
      return h(NSpace, {justify: 'center'}, () => [
        h(NTooltip, null, {
          trigger: () => h(NButton, {
            size: 'tiny',
            circle: true,
            onClick: () => openFormModal(row)
          }, {icon: () => h(NIcon, {component: EditIcon})}),
          default: () => '編輯'
        }),
        h(NTooltip, null, {
          trigger: () => h(NButton, {
            size: 'tiny', circle: true, type: 'error',
            disabled: row.members_count > 0,
            onClick: () => confirmDelete(row)
          }, {icon: () => h(NIcon, {component: DeleteIcon})}),
          default: () => row.members_count > 0 ? `組織尚有 ${row.members_count} 位成員，無法刪除` : '刪除組織'
        })
      ]);
    }
  }
]);

const tableScrollXWidth = computed(() => {
  return tableColumns.value.reduce((sum, col) => sum + (col.width || 120), 0);
});

const filteredOrganizations = computed(() => {
  const term = props.searchTermProp.toLowerCase().trim();
  if (!term) return allOrganizations.value;
  return allOrganizations.value.filter(org =>
      (org.name && org.name.toLowerCase().includes(term)) ||
      (org.short_name && org.short_name.toLowerCase().includes(term)) ||
      (org.contact_person && org.contact_person.toLowerCase().includes(term))
  );
});

// --- 方法 (Methods) ---
async function fetchOrganizations() {
  loading.value = true;
  fetchError.value = null;
  try {
    const response = await apiClient.get('/organizations');
    allOrganizations.value = response.data || [];
  } catch (err) {
    fetchError.value = err.response?.data?.message || "無法載入組織列表。";
  } finally {
    loading.value = false;
  }
}

function openFormModal(org = null) {
  formRef.value?.restoreValidation();
  if (org) {
    isEditing.value = true;
    Object.assign(currentOrg, org);
  } else {
    isEditing.value = false;
    Object.assign(currentOrg, {
      id: null, name: '', short_name: '', description: '',
      contact_person: '', contact_email: '', contact_phone: ''
    });
  }
  showFormModal.value = true;
}

async function handleFormSubmit() {
  formRef.value?.validate(async (errors) => {
    if (errors) {
      message.error('請檢查表單輸入。');
      return;
    }
    submitting.value = true;
    try {
      // 準備 payload，只包含模型有的欄位
      const payload = {
        name: currentOrg.name.trim(),
        short_name: currentOrg.short_name?.trim() || null,
        description: currentOrg.description?.trim() || null,
        contact_person: currentOrg.contact_person?.trim() || null,
        contact_email: currentOrg.contact_email?.trim() || null,
        contact_phone: currentOrg.contact_phone?.trim() || null,
      };

      if (isEditing.value) {
        await apiClient.put(`/organizations/${currentOrg.id}`, payload);
        message.success("組織已成功更新！");
      } else {
        await apiClient.post('/organizations', payload);
        message.success("組織已成功新增！");
      }
      showFormModal.value = false;
      await fetchOrganizations();
    } catch (err) {
      message.error(err.response?.data?.message || "操作失敗。");
    } finally {
      submitting.value = false;
    }
  });
}

function confirmDelete(org) {
  dialog.error({
    title: '確認刪除組織',
    content: `您確定要刪除組織 "${org.name}" 嗎？此操作無法復原！`,
    positiveText: '確認刪除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await apiClient.delete(`/organizations/${org.id}`);
        message.success(`組織 "${org.name}" 已成功刪除。`);
        await fetchOrganizations();
      } catch (err) {
        message.error(err.response?.data?.message || `刪除組織失敗。`);
      }
    }
  });
}

onMounted(fetchOrganizations);

watch(() => props.searchTermProp, () => {
  pagination.page = 1;
});
</script>

<style scoped>
/* 您的 CSS 樣式保持不變 */
.organization-management-section {
}

.table-actions-header {
}

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
  background-color: #2a3a51 !important;
}
</style>
