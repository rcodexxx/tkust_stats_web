<template>
  <div class="admin-edit-member-page container mt-4 mb-5 px-md-4">
    <n-h1 class="page-main-title">
      <n-button text @click="goBack" class="me-2 title-back-button">
        <template #icon>
          <n-icon :component="ArrowBackIcon"/>
        </template>
      </n-button>
      編輯成員資料
    </n-h1>

    <div v-if="loadingData" class="text-center my-5">
      <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;"></div>
    </div>
    <div v-if="fetchError" class="alert alert-danger">{{ fetchError }}</div>

    <n-card :bordered="false" class="form-card" v-if="!loadingData && !fetchError && formData.name !== undefined">
      <n-form
          ref="formRef"
          :model="formData"
          label-placement="top"
          require-mark-placement="right-hanging"
          @submit.prevent="handleUpdateMember"
          :rules="formRules"
      >
        <n-grid :x-gap="24" :y-gap="12" :cols="12" item-responsive>
          <n-form-item-gi :span="12" label="真實姓名*" path="name">
            <n-input v-model:value="formData.name" placeholder="成員的真實姓名"/>
          </n-form-item-gi>
          <n-form-item-gi :span="12" label="顯示名稱/綽號" path="display_name">
            <n-input v-model:value="formData.display_name" placeholder="排行榜上顯示的名稱"/>
          </n-form-item-gi>

          <n-gi :span="12">
            <n-divider title-placement="left" class="section-divider">帳號資訊</n-divider>
          </n-gi>
          <n-form-item-gi :span="12" :md="6" label="手機號碼 (登入帳號)*" path="username">
            <n-input v-model:value="formData.username" placeholder="09xxxxxxxx"/>
            <small class="form-text text-muted">若成員尚無帳號，提供手機號將自動創建帳號，密碼同手機號。</small>
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="電子郵件" path="email">
            <n-input v-model:value="formData.email" placeholder="example@example.com (可選)"/>
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="角色*" path="role">
            <n-select v-model:value="formData.role" :options="roleOptions" placeholder="選擇角色"/>
          </n-form-item-gi>


          <n-gi :span="12">
            <n-divider title-placement="left" class="section-divider">球員詳細資料</n-divider>
          </n-gi>
          <n-form-item-gi :span="12" :md="6" label="學號 (7-9位數字)" path="student_id">
            <n-input v-model:value="formData.student_id" placeholder="選填"/>
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="性別" path="gender">
            <n-select
                v-model:value="formData.gender"
                :options="genderOptions"
                placeholder="選擇性別"
                clearable/>
          </n-form-item-gi>

          <n-form-item-gi :span="12" :md="6" label="習慣位置" path="position">
            <n-select
                v-model:value="formData.position"
                :options="positionOptions"
                placeholder="選擇位置"
                clearable/>
          </n-form-item-gi>

          <n-form-item-gi :span="12" :md="6" label="所屬組織" path="organization_id">
            <n-select
                v-model:value="formData.organization_id"
                :options="organizationOptions"
                placeholder="選擇組織"
                clearable
                filterable
                label-field="name"
                value-field="id"/>
          </n-form-item-gi>

          <n-form-item-gi :span="12" :md="6" label="&mu; (目前分數)" path="mu">
            <n-input-number
                v-model:value="formData.mu"
                :step="0.1"
                placeholder="成員目前 Mu 值"
                style="width:100%"
                :disabled="true"
            />
          </n-form-item-gi>

          <n-form-item-gi :span="12" :md="6" label="&sigma; (分數標準差)" path="sigma">
            <n-input-number
                v-model:value="formData.sigma"
                :step="0.001"
                placeholder="成員目前 Sigma 值"
                style="width:100%"
                :disabled="true"
            />
          </n-form-item-gi>

          <n-form-item-gi :span="12" :md="6" label="入隊日期" path="joined_date">
            <n-date-picker
                v-model:formatted-value="formData.join_date"
                type="date"
                value-format="yyyy-MM-dd"
                placeholder="選填，預設今日"
                style="width:100%"
                clearable
            />
          </n-form-item-gi>

          <n-form-item-gi :span="12" :md="6" label="離隊日期" path="leaved_date">
            <n-date-picker
                v-model:formatted-value="formData.leaved_date"
                type="date"
                value-format="yyyy-MM-dd"
                placeholder="選填"
                style="width:100%"
                clearable
            />
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="成員活躍狀態" path="is_active">
            <div class="switch-with-label">
              <n-switch v-model:value="formData.is_active"/>
              <span class="switch-label-text">此成員是否活躍</span>
            </div>
          </n-form-item-gi>


          <n-form-item-gi :span="12" label="備註" path="notes">
            <n-input
                type="textarea"
                v-model:value="formData.notes"
                placeholder="選填"
                :autosize="{ minRows: 2, maxRows: 4 }"
            />
          </n-form-item-gi>
        </n-grid>

        <n-space justify="end" class="mt-4 action-buttons">
          <n-button @click="goBack" size="medium">取消</n-button>
          <n-button type="primary" attr-type="submit" :loading="submitting" size="medium" strong>
            確認更新
          </n-button>
        </n-space>
      </n-form>
    </n-card>
  </div>
</template>

<script setup>
import {onMounted, reactive, ref} from 'vue';
import {useRoute, useRouter} from 'vue-router';
import {NDatePicker, NInputNumber, NSwitch, useMessage} from 'naive-ui';
import {ArrowBackOutline as ArrowBackIcon} from '@vicons/ionicons5';
import memberService from '@/services/memberService.js';
import organizationService from '@/services/organizationService.js';

const router = useRouter();
const route = useRoute();
const message = useMessage();
const formRef = ref(null);

const memberId = ref(route.params.id); // 從路由參數獲取 memberId
const loadingData = ref(true);
const fetchError = ref(null);
const submitting = ref(false);

const formData = reactive({
  name: '',
  display_name: '',
  username: '', // User.username (手機號)
  email: '',    // User.email
  role: 'MEMBER',// User.role  // 注意 AddMember用的是 MEMBER, 這裡用 PLAYER

  student_id: '',
  gender: null,
  position: null,
  organization_id: null,
  mu: null,
  sigma: null,
  join_date: null, // 之前模板中 path 是 "joined_date"
  leaved_date: null,
  notes: ''
});

const formRules = {
  name: [{required: true, message: '真實姓名為必填', trigger: ['input', 'blur']}],
  username: [
    {required: true, message: '手機號碼 (登入帳號) 為必填', trigger: ['input', 'blur']},
    {pattern: /^09\d{8}$/, message: '手機號碼格式不正確 (應為09開頭10位數字)', trigger: ['input', 'blur']}
  ],
  email: [{type: 'email', message: '請輸入有效的電子郵件格式', trigger: ['input', 'blur']}],
  student_id: [{
    pattern: /^\d{7,9}$/, message: '學號必須是7到9位數字', trigger: ['input', 'blur'],
    required: false
  }],
  role: [{required: true, message: '角色為必填', trigger: ['change', 'blur']}],
};

const roleOptions = [
  {label: '隊員', value: 'MEMBER'}, // label 是中文，value 是 Enum 的 NAME
  {label: '幹部', value: 'CADRE'},
  {label: '教練', value: 'COACH'},
  {label: '管理員', value: 'ADMIN'}
];

const genderOptions = [
  {label: '男性', value: 'MALE'},
  {label: '女性', value: 'FEMALE'},
];
const positionOptions = [
  {label: '皆可', value: 'VERSATILE'},
  {label: '後排', value: 'BACK'},
  {label: '前排', value: 'FRONT'}
];

const organizationOptions = ref([]); // 從 API 獲取

async function fetchOrganizationDetails() {
  try {
    const orgResponse = await organizationService.getOrganizations();
    if (orgResponse && Array.isArray(orgResponse.data)) {
      organizationOptions.value = orgResponse.data.map(org => ({
        label: org.name, // 讓 label 更豐富
        value: org.id
      }));
    } else {
      organizationOptions.value = []; // 如果 API 沒有回傳預期的陣列，則設為空陣列
      console.warn("Organization data from API is not an array or is missing:", orgResponse.data);
    }
  } catch (err) {
    console.error("Failed to fetch organization details:", err.response || err);
    organizationOptions.value = []; // 出錯時也確保是空陣列
  }
}

async function fetchMemberDetails() {
  loadingData.value = true;
  fetchError.value = null;
  try {
    const memberResponse = await memberService.getMember(memberId.value);
    const memberData = memberResponse.data;

    formData.name = memberData.name || '';
    formData.display_name = memberData.display_name || '';
    formData.student_id = memberData.student_id || '';
    formData.gender = memberData.gender || null;
    formData.position = memberData.position || null;
    formData.organization_id = memberData.organization_id || null;
    formData.mu = memberData.mu !== undefined ? memberData.mu : null; // 確保 mu 和 sigma 可以為0
    formData.sigma = memberData.sigma !== undefined ? memberData.sigma : null;
    formData.join_date = memberData.join_date || null; // 模板中是 join_date
    formData.leaved_date = memberData.leaved_date || null;
    formData.is_active = typeof memberData.is_active === 'boolean' ? memberData.is_active : true;
    formData.notes = memberData.notes || '';

    // 填充 User 相關欄位
    formData.username = memberData.username || ''; // 假設後端 to_dict 返回 user_username
    formData.email = memberData.user_email || '';
    formData.role = memberData.user_role || 'MEMBER';
    // 注意 AddMember 中 role 預設是 PLAYER，但您這裡的 roleOptions 有 MEMBER

    // 獲取組織列表 (與 AddMember 邏輯類似)
    await fetchOrganizationDetails(); // 確保此函數已定義或導入

  } catch (err) {
    // ... (錯誤處理)
  } finally {
    loadingData.value = false;
  }
}

onMounted(fetchMemberDetails);

const handleUpdateMember = async () => {
  formRef.value?.validate(async (errors) => {
    if (!errors) {
      submitting.value = true;
      try {
        const payload = {...formData};

        const updatePayload = {
          name: payload.name,
          display_name: payload.display_name,
          student_id: payload.student_id || null, // Member 的學號
          username: payload.username || null,     // User 的登入手機號
          email: payload.email || null,           // User 的 email
          role: payload.role,                   // User 的角色
          gender: payload.gender || null,
          position: payload.position || null,
          organization_id: payload.organization_id || null,
          mu: payload.mu,
          sigma: payload.sigma,
          joined_date: payload.joined_date || null,
          leaved_date: payload.leaved_date || null,
          is_active: payload.is_active,
          is_active_user: payload.is_active_user, // User 帳號狀態
          notes: payload.notes || null
        };
        // 清理空字串為 null
        for (const key in updatePayload) {
          if (updatePayload[key] === '') updatePayload[key] = null;
        }


        const response = await memberService.updateMember(memberId.value, updatePayload);
        message.success(response.data.message || "成員資料已成功更新！");
        await router.push({name: 'ManagementCenter'});
      } catch (err) {
        // ... (錯誤處理，類似 AddMemberView) ...
        const errorData = err.response?.data;
        if (errorData && errorData.errors) {
          let errorMsg = errorData.message || "更新失敗，請檢查欄位：";
          for (const field in errorData.errors) {
            errorMsg += `\n- ${field}: ${errorData.errors[field]}`;
          }
          message.error(errorMsg, {duration: 7000});
        } else {
          message.error(errorData?.error || err.message || "更新成員失敗。");
        }
      } finally {
        submitting.value = false;
      }
    } else {
      message.error("請修正表單中的錯誤。");
    }
  });
};

function goBack() {
  router.push({name: 'ManagementCenter'}); // 或 router.back()
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