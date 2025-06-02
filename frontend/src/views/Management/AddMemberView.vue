<template>
  <div class="admin-add-member-page container mt-4 mb-5">
    <n-h1>
      <n-button text @click="goBack" class="me-2">
        <template #icon>
          <n-icon :component="ArrowBackIcon"/>
        </template>
      </n-button>
      新增球隊成員及帳號
    </n-h1>

    <n-card :bordered="false" class="shadow-sm">
      <n-form
          ref="formRef"
          :model="formData"
          :rules="formRules"
          label-placement="top"
          require-mark-placement="right-hanging"
          @submit.prevent="handleAddMember"
      >
        <n-grid :x-gap="24" :y-gap="12" :cols="12" item-responsive>
          <n-form-item-gi :span="12" label="真實姓名*" path="name">
            <n-input v-model:value="formData.name" placeholder="請輸入成員的真實姓名"/>
          </n-form-item-gi>
          <n-form-item-gi :span="12" label="顯示名稱/綽號" path="display_name">
            <n-input v-model:value="formData.display_name" placeholder="排行榜上顯示的名稱 (預設同真實姓名)"/>
          </n-form-item-gi>

          <n-gi :span="12">
            <n-divider title-placement="left">登入帳號資訊</n-divider>
          </n-gi>
          <n-form-item-gi :span="12" :md="6" label="手機號碼 (登入帳號)*" path="username">
            <n-input v-model:value="formData.username" placeholder="09xxxxxxxx (用於登入)"/>
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="初始密碼" path="password">
            <n-input type="password" v-model:value="formData.password" placeholder="可選，預設為手機號碼"
                     show-password-on="click"/>
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="電子郵件" path="email">
            <n-input v-model:value="formData.email" placeholder="example@example.com (可選)"/>
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="角色*" path="role">
            <n-select v-model:value="formData.role" :options="roleOptions" placeholder="選擇角色"/>
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="帳號狀態" path="is_active_user">
            <n-switch v-model:value="formData.is_active_user"/>
            預設啟用
          </n-form-item-gi>

          <n-gi :span="12">
            <n-divider title-placement="left">球員詳細資料</n-divider>
          </n-gi>
          <n-form-item-gi :span="12" :md="6" label="學號 (7-9位數字)" path="student_id">
            <n-input v-model:value="formData.student_id" placeholder="選填"/>
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="性別" path="gender">
            <n-select v-model:value="formData.gender" :options="genderOptions" placeholder="選擇性別" clearable/>
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="習慣位置" path="position">
            <n-select v-model:value="formData.position" :options="positionOptions" placeholder="選擇位置" clearable/>
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="所屬組織" path="organization_id">
            <n-select v-model:value="formData.organization_id"
                      :options="organizationOptions"
                      placeholder="選擇組織"
                      clearable filterable
                      label-field="name" value-field="id"/>
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="初始 Mu (μ)" path="mu">
            <n-input-number v-model:value="formData.mu" :min="0" :step="0.1" placeholder="預設 25.0" clearable
                            style="width:100%"/>
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="初始 Sigma (σ)" path="sigma">
            <n-input-number v-model:value="formData.sigma" :min="0.1" :step="0.001" placeholder="預設約 8.333" clearable
                            style="width:100%"/>
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="球拍" path="racket">
            <n-input v-model:value="formData.racket" placeholder="選填"/>
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="入隊日期" path="join_date">
            <n-date-picker v-model:formatted-value="formData.join_date" type="date" value-format="yyyy-MM-dd"
                           placeholder="選填，預設今日" style="width:100%"/>
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="成員活躍狀態" path="is_active">
            <n-switch v-model:value="formData.is_active"/>
            預設活躍
          </n-form-item-gi>
          <n-form-item-gi :span="12" label="備註" path="notes">
            <n-input type="textarea" v-model:value="formData.notes" placeholder="選填"
                     :autosize="{ minRows: 2, maxRows: 4 }"/>
          </n-form-item-gi>
        </n-grid>

        <n-space justify="end" class="mt-4">
          <n-button @click="goBack">取消</n-button>
          <n-button type="primary" attr-type="submit" :loading="submitting">
            確認新增
          </n-button>
        </n-space>
      </n-form>
    </n-card>
  </div>
</template>

<script setup>
import {onMounted, reactive, ref} from 'vue';
import {useRouter} from 'vue-router';
import {
  NButton,
  NCard,
  NDatePicker,
  NDivider,
  NForm,
  NFormItemGi,
  NH1,
  NIcon,
  NInput,
  NInputNumber,
  NSelect,
  NSpace,
  NSwitch,
  useMessage
} from 'naive-ui';
import {ArrowBackOutline as ArrowBackIcon} from '@vicons/ionicons5';
import memberService from '@/services/memberService.js';
import organizationService from '@/services/organizationService.js'; // 用於獲取組織列表

const router = useRouter();
const message = useMessage(); // Naive UI message API
const formRef = ref(null); // 用於 Naive UI Form 的驗證

const submitting = ref(false);
const formData = reactive({
  name: '',
  display_name: '',
  username: '', // 手機號
  password: '',
  email: '',
  role: 'PLAYER', // 預設
  is_active_user: true,
  student_id: '',
  gender: null,
  position: null,
  organization_id: null,
  mu: null, // 預設會由後端或模型處理
  sigma: null,
  racket: '',
  join_date: null, // YYYY-MM-DD
  is_active: true, // Member.is_active
  notes: ''
});

// 下拉選單選項
const roleOptions = [
  {label: '隊員', value: 'PLAYER'},
  {label: '幹部', value: 'CADRE'},
  {label: '教練', value: 'COACH'},
  {label: '管理員', value: 'ADMIN'}
];
const genderOptions = [
  {label: '男性', value: 'MALE'},
  {label: '女性', value: 'FEMALE'},
  {label: '其他', value: 'OTHER'}
];
const positionOptions = [
  {label: '單打', value: 'SINGLES'}, {label: '雙打網前', value: 'DOUBLES_NET'},
  {label: '雙打底線', value: 'DOUBLES_BASELINE'}, {label: '皆可', value: 'VERSATILE'},
  {label: '後排', value: 'BACK'}, {label: '前排', value: 'FRONT'}
];
const organizationOptions = ref([]);

// Naive UI 表單驗證規則
const formRules = {
  name: [{required: true, message: '真實姓名為必填', trigger: ['input', 'blur']}],
  username: [
    {required: true, message: '手機號碼 (登入帳號) 為必填', trigger: ['input', 'blur']},
    {pattern: /^09\d{8}$/, message: '手機號碼格式不正確 (應為09開頭10位數字)', trigger: ['input', 'blur']}
  ],
  // password: [{ min: 6, message: '密碼長度至少6位', trigger: ['input', 'blur'] }], // 如果有輸入才驗證
  email: [{type: 'email', message: '請輸入有效的電子郵件格式', trigger: ['input', 'blur']}],
  student_id: [{
    pattern: /^\d{7,9}$/, message: '學號必須是7到9位數字', trigger: ['input', 'blur'],
    required: false // 設為非必填
  }],
  role: [{required: true, message: '角色為必填', trigger: ['change', 'blur']}],
};


async function fetchInitialData() {
  try {
    const orgResponse = await organizationService.getOrganizations();
    organizationOptions.value = orgResponse.data || [];
  } catch (error) {
    message.error("載入組織列表失敗");
    console.error("Failed to load organizations for select:", error);
  }
}

onMounted(fetchInitialData);

const handleAddMember = async () => {
  formRef.value?.validate(async (errors) => {
    if (!errors) {
      submitting.value = true;
      try {
        // 準備 payload，確保空字串轉為 null (如果後端期望 null)
        const payload = {...formData};
        if (payload.password === '') delete payload.password; // 如果密碼為空，則不傳遞，讓後端用預設
        if (payload.email === '') payload.email = null;
        if (payload.student_id === '') payload.student_id = null;
        if (payload.gender === '') payload.gender = null;
        if (payload.position === '') payload.position = null;
        if (payload.organization_id === '') payload.organization_id = null;
        if (payload.racket === '') payload.racket = null;
        if (payload.join_date === '') payload.join_date = null;
        if (payload.notes === '') payload.notes = null;
        if (payload.mu === null) delete payload.mu; // 如果未填，則不傳，讓後端用預設
        if (payload.sigma === null) delete payload.sigma;


        const response = await memberService.createMember(payload);
        message.success(response.data.message || "成員及帳號已成功建立！");
        if (response.data.initial_password_info) {
          message.info(response.data.initial_password_info, {duration: 10000}); // 延長提示時間
        }
        router.push({name: 'TeamManagement'}); // 跳轉回管理列表
      } catch (err) {
        const errorData = err.response?.data;
        if (errorData && errorData.errors) {
          let errorMsg = errorData.message || "新增失敗，請檢查欄位：";
          for (const field in errorData.errors) {
            errorMsg += `\n- ${field}: ${errorData.errors[field]}`;
          }
          message.error(errorMsg, {duration: 7000});
        } else {
          message.error(errorData?.error || err.message || "新增成員失敗。");
        }
        console.error("Failed to create member:", err.response || err);
      } finally {
        submitting.value = false;
      }
    } else {
      message.error("請修正表單中的錯誤。");
      console.log('Form validation errors:', errors);
    }
  });
};

function goBack() {
  router.back();
}
</script>

<style scoped>
.admin-add-member-page {
  max-width: 800px;
  margin: auto;
}

.page-title {
  color: #333;
}

.n-card {
  margin-top: 1.5rem;
}

/* 可以加入更多樣式 */
</style>