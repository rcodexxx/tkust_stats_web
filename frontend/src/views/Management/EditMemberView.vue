<template>
  <div class="admin-edit-member-page container mt-4 mb-5 px-md-4">
    <!-- 載入中狀態 -->
    <div v-if="loadingData" class="text-center my-5">
      <n-spin size="large"/>
    </div>
    <!-- 錯誤狀態 -->
    <n-alert title="載入錯誤" type="error" v-else-if="fetchError" closable @close="fetchError = null" class="mb-4">
      {{ fetchError }}
    </n-alert>

    <!-- 主內容區塊，確保 formData.id 存在後才渲染，避免非同步錯誤 -->
    <div v-else-if="formData.id">
      <!-- 頁面標題和返回按鈕 -->
      <n-h1 class="page-main-title">
        <n-button text @click="goBack" class="me-2 title-back-button">
          <template #icon>
            <n-icon :component="ArrowBackIcon"/>
          </template>
        </n-button>
        編輯成員資料: {{ formData.name }}
      </n-h1>

      <n-card :bordered="false" class="form-card">
        <n-form
            ref="formRef"
            :model="formData"
            label-placement="top"
            @submit.prevent="handleUpdateMember"
            :rules="formRules"
        >
          <n-alert
              v-if="updateMessage"
              :title="updateStatus === 'success' ? '成功' : '更新失敗'"
              :type="updateStatus"
              closable class="mb-4" @close="clearUpdateMessage"
          >
            <span style="white-space: pre-wrap;">{{ updateMessage }}</span>
          </n-alert>

          <n-grid :x-gap="24" :y-gap="12" :cols="12" item-responsive>
            <!-- 個人資訊 -->
            <n-form-item-gi :span="12" :md="6" label="真實姓名" path="name">
              <n-input v-model:value="formData.name" placeholder="成員的真實姓名"/>
            </n-form-item-gi>
            <n-form-item-gi :span="12" :md="6" label="顯示名稱/綽號 (用於使用者設定)" path="display_name">
              <n-input v-model:value="formData.display_name" placeholder="排行榜或登入時顯示的名稱"/>
            </n-form-item-gi>

            <!-- 帳號資訊 -->
            <n-gi :span="12">
              <n-divider title-placement="left" class="section-divider">帳號資訊</n-divider>
            </n-gi>
            <n-form-item-gi :span="12" :md="6" label="手機號碼 (登入帳號)" path="username">
              <n-input v-model:value="formData.username" placeholder="09xxxxxxxx"/>
            </n-form-item-gi>
            <n-form-item-gi :span="12" :md="6" label="電子郵件" path="email">
              <n-input v-model:value="formData.email" placeholder="example@example.com (可選)"/>
            </n-form-item-gi>
            <n-form-item-gi :span="12" :md="6" label="使用者角色*" path="role">
              <n-select v-model:value="formData.role" :options="roleOptions" placeholder="選擇角色"/>
            </n-form-item-gi>

            <!-- 球員詳細資料 -->
            <n-gi :span="12">
              <n-divider title-placement="left" class="section-divider">球員詳細資料</n-divider>
            </n-gi>
            <n-form-item-gi :span="12" :md="6" label="學號" path="student_id">
              <n-input v-model:value="formData.student_id" placeholder="選填"/>
            </n-form-item-gi>
            <n-form-item-gi :span="12" :md="6" label="性別" path="gender">
              <n-select v-model:value="formData.gender" :options="genderOptions" placeholder="選擇性別" clearable/>
            </n-form-item-gi>
            <n-form-item-gi :span="12" :md="6" label="習慣位置" path="position">
              <n-select v-model:value="formData.position" :options="positionOptions" placeholder="選擇位置" clearable/>
            </n-form-item-gi>
            <n-form-item-gi :span="12" :md="6" label="所屬組織" path="organization_id">
              <n-select v-model:value="formData.organization_id" :options="organizationOptions" placeholder="選擇組織"
                        clearable filterable/>
            </n-form-item-gi>

            <!-- 分數 (唯讀) -->
            <n-form-item-gi :span="12" :md="6" label="μ (目前分數)">
              <n-input-number v-model:value="formData.mu" :step="0.1" style="width:100%" disabled/>
            </n-form-item-gi>
            <n-form-item-gi :span="12" :md="6" label="σ (分數標準差)">
              <n-input-number v-model:value="formData.sigma" :step="0.001" style="width:100%" disabled/>
            </n-form-item-gi>


            <!-- 隊籍日期與狀態 -->
            <n-form-item-gi :span="12" :md="6" label="入隊日期" path="joined_date_ts">
              <n-date-picker v-model:value="formData.joined_date_ts" type="date" clearable style="width:100%"/>
            </n-form-item-gi>
            <n-form-item-gi :span="12" :md="6" label="離隊日期" path="leaved_date_ts">
              <n-date-picker v-model:value="formData.leaved_date_ts" type="date" clearable style="width:100%"/>
            </n-form-item-gi>
            <n-form-item-gi :span="12" :md="6" label="成員活躍狀態">
              <div class="switch-with-label">
                <n-switch v-model:value="formData.is_active"/>
                <span class="switch-label-text">{{ formData.is_active ? '現役' : '非現役' }}</span>
              </div>
            </n-form-item-gi>

            <n-form-item-gi :span="12" label="備註" path="notes">
              <n-input type="textarea" v-model:value="formData.notes" placeholder="選填"
                       :autosize="{ minRows: 2, maxRows: 4 }"/>
            </n-form-item-gi>
          </n-grid>

          <n-space justify="end" class="mt-4 action-buttons">
            <n-button @click="goBack" size="medium">取消</n-button>
            <n-button type="primary" attr-type="submit" :loading="submitting" size="medium" strong>
              {{ submitting ? '儲存中...' : '確認更新' }}
            </n-button>
          </n-space>
        </n-form>
      </n-card>
    </div>
  </div>
</template>

<script setup>
import {onMounted, reactive, ref} from 'vue';
import {useRouter} from 'vue-router';
import {
  NAlert,
  NButton,
  NCard,
  NDatePicker,
  NDivider,
  NForm,
  NFormItemGi,
  NGi,
  NGrid,
  NH1,
  NIcon,
  NInput,
  NInputNumber,
  NSelect,
  NSpin,
  NSwitch,
  useMessage
} from 'naive-ui';
import {ArrowBackOutline as ArrowBackIcon} from '@vicons/ionicons5';
import apiClient from '@/services/apiClient';

// --- Props & Router ---
const props = defineProps({
  id: {type: [String, Number], required: true}
});
const router = useRouter();
const message = useMessage();

// --- 狀態管理 (State) ---
const loadingData = ref(true);
const submitting = ref(false);
const fetchError = ref(null);
const updateMessage = ref('');
const updateStatus = ref('');
const formRef = ref(null);

// 簡化：現在只用一個 reactive 物件來管理所有表單數據
const formData = reactive({
  id: null, // 新增 id，用於 v-if 判斷數據是否已載入
  name: '',
  display_name: '',
  username: '',
  email: '',
  role: null,
  student_id: '',
  gender: null,
  position: null,
  organization_id: null,
  mu: null,
  sigma: null,
  is_active: true,
  joined_date_ts: null,
  leaved_date_ts: null,
  notes: ''
});

// --- 選項與規則 (Options & Rules) ---
const organizationOptions = ref([]);
const genderOptions = [{label: '男性', value: 'male'}, {label: '女性', value: 'female'}];
const positionOptions = [{label: '後排', value: 'back'}, {label: '前排', value: 'front'}, {
  label: '皆可',
  value: 'versatile'
}];
const roleOptions = [
  {label: '隊員', value: 'member'}, {label: '幹部', value: 'cadre'},
  {label: '教練', value: 'coach'}, {label: '管理員', value: 'admin'}
];

const formRules = {
  name: [{required: true, message: '真實姓名為必填', trigger: ['blur', 'input']}],
  username: [
    {required: true, message: '手機號碼為必填', trigger: ['blur', 'input']},
    {pattern: /^09\d{8}$/, message: '手機號碼格式不正確', trigger: ['blur', 'input']}
  ],
  email: [{type: 'email', message: '請輸入有效的電子郵件格式', trigger: ['blur', 'input']}],
  student_id: [{
    required: false, trigger: ['blur', 'input'],
    validator: (rule, value) => {
      if (value && !/^\d{7,9}$/.test(value)) return new Error('學號必須是7到9位數字');
      return true;
    }
  }],
  role: [{required: true, message: '角色為必填', trigger: ['change']}],
};

// --- 方法 (Methods) ---
function populateForm(data) {
  if (!data) return;

  formData.id = data.id;
  formData.name = data.name || '';
  formData.student_id = data.student_id || '';

  // 檢查後端回傳的值是否存在於我們的選項中，如果不存在，則設為 null
  const findOption = (options, value) => options.some(opt => opt.value === value) ? value : null;

  formData.gender = findOption(genderOptions, data.gender);
  formData.position = findOption(positionOptions, data.position);
  // 對於 organization_id，我們假設從 API 獲取的 id 是有效的，直接賦值
  formData.organization_id = data.organization_id || null;

  formData.mu = data.mu;
  formData.sigma = data.sigma;

  formData.notes = data.notes || '';
  formData.joined_date_ts = data.joined_date ? new Date(data.joined_date).getTime() : null;
  formData.leaved_date_ts = data.leaved_date ? new Date(data.leaved_date).getTime() : null;

  if (data.user) {
    formData.username = data.user.username || '';
    formData.email = data.user.email || '';
    formData.display_name = data.user.display_name || '';
    formData.role = findOption(roleOptions, data.user.role);
    formData.is_active = data.user.is_active;
  } else {
    // 如果沒有關聯的 user，將 user 相關欄位設為預設空值
    formData.username = '';
    formData.email = '';
    formData.display_name = '';
    formData.role = null;
    formData.is_active = false;
  }
}

async function fetchData() {
  loadingData.value = true;
  fetchError.value = null;
  try {
    const response = await apiClient.get(`/members/${props.id}`);
    populateForm(response.data);
  } catch (err) {
    fetchError.value = err.response?.data?.message || "無法載入成員資料";
  } finally {
    loadingData.value = false;
  }
}

async function fetchOrganizationOptions() {
  try {
    const response = await apiClient.get('/organizations');
    organizationOptions.value = response.data.map(org => ({label: org.name, value: org.id}));
  } catch (error) {
    message.error("載入組織列表失敗");
  }
}

/**
 * 格式化時間戳為 'YYYY-MM-DD' 字串，避免時區問題。
 * @param {number | null} timestamp - The timestamp to format.
 * @returns {string | null}
 */
const formatDate = (timestamp) => {
  if (!timestamp) return null;
  const date = new Date(timestamp);
  // 獲取本地時區的年、月、日
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const handleUpdateMember = () => {
  formRef.value?.validate(async (validationErrors) => {
    if (validationErrors) {
      message.error("請檢查表單，修正錯誤後再提交。");
      return;
    }
    submitting.value = true;
    clearUpdateMessage();

    // --- 修正：使用輔助函式格式化日期 ---
    const payload = {
      // Member Fields
      name: formData.name,
      student_id: formData.student_id || null,
      gender: formData.gender,
      position: formData.position,
      organization_id: formData.organization_id,
      joined_date: formatDate(formData.joined_date_ts),
      leaved_date: formatDate(formData.leaved_date_ts),
      notes: formData.notes,

      // User Fields
      username: formData.username,
      email: formData.email || null,
      display_name: formData.display_name,
      role: formData.role,
      is_active: formData.is_active
    };

    try {
      const response = await apiClient.put(`/members/${props.id}`, payload);
      updateStatus.value = 'success';
      updateMessage.value = response.data.message || "成員資料已成功更新！";
      message.success(updateMessage.value);

      goBack();

    } catch (err) {
      updateStatus.value = 'error';
      updateMessage.value = err.response?.data?.message || "更新失敗，請稍後再試。";
      message.error(updateMessage.value, {duration: 5000});
    } finally {
      submitting.value = false;
    }
  });
};

// --- 生命週期鉤子 (Lifecycle Hooks) ---
onMounted(() => {
  fetchData();
  fetchOrganizationOptions();
});

// --- 輔助函數 (Helpers) ---
function clearUpdateMessage() {
  updateMessage.value = '';
  updateStatus.value = '';
}

function goBack() {
  router.push({name: 'ManagementCenter'});
}
</script>

<style scoped>
.admin-edit-member-page { /* 改名以匹配模板 */
  max-width: 800px;
  margin: 2rem auto 3rem auto;
}

/* 與 AdminAddMemberView.vue 相同的樣式 */
.page-main-title {
  font-weight: 600;
  color: var(--n-title-text-color);
  display: flex;
  align-items: center;
}

.title-back-button.n-button {
  margin-right: 12px;
  font-size: 1.5rem;
}

.title-back-button.n-button .n-icon {
  color: var(--n-text-color-base);
}

.form-card.n-card {
  margin-top: 1.5rem;
  border-radius: var(--n-border-radius);
  box-shadow: var(--n-box-shadow2);
  background-color: var(--n-card-color);
  padding: 10px 15px;
}

.section-divider.n-divider:not(.n-divider--vertical) {
  margin-top: 1.5rem;
  margin-bottom: 1.25rem;
}

.section-divider.n-divider .n-divider__title {
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--n-text-color-2);
}

.switch-with-label {
  display: flex;
  align-items: center;
  gap: 8px;
  height: var(--n-height-m);
}

.switch-label-text {
  color: var(--n-text-color-3);
  font-size: 0.9em;
}

.action-buttons.n-space {
  padding-top: 0.5rem;
}

.action-buttons .n-button {
  min-width: 100px;
  font-weight: 500;
}

/* 編輯頁面特有的 spinner 樣式 (如果使用 Bootstrap spinner) */
.spinner-border.text-primary {
  color: var(--n-primary-color) !important; /* 使其顏色與 Naive UI 主題一致 */
}

.alert.alert-danger { /* Bootstrap alert，如果使用 n-alert 則不需要 */
  color: var(--n-error-color);
  background-color: var(--n-color-embedded-error);
  border-color: var(--n-error-color-hover);
}
</style>