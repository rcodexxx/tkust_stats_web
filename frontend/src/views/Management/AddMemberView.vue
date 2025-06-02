<template>
  <div class="admin-add-member-page container mt-4 mb-5 px-md-4">
    <n-h1 class="page-main-title">
      <n-button text @click="goBack" class="me-2 title-back-button">
        <template #icon>
          <n-icon :component="ArrowBackIcon"/>
        </template>
      </n-button>
      新增球隊成員及帳號
    </n-h1>

    <n-card :bordered="false" class="form-card">
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
            <n-divider title-placement="left" class="section-divider">登入帳號資訊</n-divider>
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
          <n-gi :span="12">
            <n-divider title-placement="left" class="section-divider">球員詳細資料</n-divider>
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
                      label-field="name" value-field="id"
                      style="width:100%"
            />
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
            <div class="switch-with-label">
              <n-switch v-model:value="formData.is_active"/>
              <span class="switch-label-text">預設活躍</span>
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
            確認新增
          </n-button>
        </n-space>
      </n-form>
    </n-card>
  </div>
</template>

<script setup>
import {onMounted, reactive, ref} from 'vue';
import {useRoute, useRouter} from 'vue-router';
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
import organizationService from '@/services/organizationService.js';

const router = useRouter();
const route = useRoute();
const message = useMessage();
const formRef = ref(null);

const memberId = ref(route.params.id);
const loadingData = ref(true);
const fetchError = ref(null);
const submitting = ref(false);

const formData = reactive({
  name: '',
  display_name: '',
  username: '', // User.username (手機號)
  // password: '', // 編輯頁面通常不直接處理密碼，應有專門的密碼重設流程
  email: '',    // User.email
  role: 'MEMBER',// User.role

  student_id: '',
  gender: null,
  position: null,
  organization_id: null,
  mu: null,
  sigma: null,
  join_date: null,
  leaved_date: null,
  is_active: true,  // Member.is_active (成員自身的活躍狀態)
  notes: ''
});

// 與 AdminAddMemberView.vue 統一
const roleOptions = [
  {label: '隊員', value: 'MEMBER'},
  {label: '幹部', value: 'CADRE'},
  {label: '教練', value: 'COACH'},
  {label: '管理員', value: 'ADMIN'}
];
const genderOptions = [
  {label: '男性', value: 'MALE'},
  {label: '女性', value: 'FEMALE'},
];
const positionOptions = [ // 與 AddMemberView.vue 統一
  {label: '皆可', value: 'VERSATILE'},
  {label: '後排', value: 'BACK'}, /* 之前 AddMember 有，EditMember 沒有 */
  {label: '前排', value: 'FRONT'} /* 之前 AddMember 有，EditMember 沒有 */
];
const organizationOptions = ref([]);

// 與 AdminAddMemberView.vue 類似的表單驗證規則
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

async function fetchOrganizationOptions() { // 改名以區分
  try {
    const orgResponse = await organizationService.getOrganizations();
    organizationOptions.value = orgResponse.data || []; // 直接使用 API 返回的對象數組
  } catch (err) {
    message.error("載入組織列表失敗");
    console.error("Failed to load organizations for select:", err);
    organizationOptions.value = [];
  }
}

async function fetchMemberDetails() {
  loadingData.value = true;
  fetchError.value = null;
  try {
    // 先獲取組織列表，以便後續 memberData.organization_id 能正確匹配
    await fetchOrganizationOptions();

    const memberResponse = await memberService.getMember(memberId.value);
    const memberData = memberResponse.data;

    formData.name = memberData.name || '';
    formData.display_name = memberData.display_name || '';
    formData.student_id = memberData.student_id || '';
    formData.gender = memberData.gender || null;
    formData.position = memberData.position || null;
    formData.organization_id = memberData.organization_id || null;
    formData.mu = (memberData.mu === null || memberData.mu === undefined) ? null : Number(memberData.mu);
    formData.sigma = (memberData.sigma === null || memberData.sigma === undefined) ? null : Number(memberData.sigma);
    formData.join_date = memberData.join_date || null;
    formData.leaved_date = memberData.leaved_date || null;
    formData.is_active = typeof memberData.is_active === 'boolean' ? memberData.is_active : true;
    formData.notes = memberData.notes || '';

    // 填充 User 相關欄位 (假設後端 to_dict 返回的 user_xxx 字段)
    formData.username = memberData.user_username || ''; // 確保後端返回的是 user_username
    formData.email = memberData.user_email || '';
    formData.role = memberData.user_role || 'MEMBER'; // 與 roleOptions 保持一致

  } catch (err) {
    fetchError.value = "無法載入成員資料進行編輯。";
    console.error("Failed to fetch member details:", err.response || err);
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
        // 準備 payload
        const updatePayload = {
          name: formData.name,
          display_name: formData.display_name,
          student_id: formData.student_id,
          username: formData.username, // User 的登入手機號
          email: formData.email,      // User 的 email
          role: formData.role,        // User 的角色
          gender: formData.gender,
          position: formData.position,
          organization_id: formData.organization_id,
          // mu 和 sigma 雖然 disabled，但其值來自 fetch，如果後端允許更新或需要傳回，則保留
          mu: formData.mu,
          sigma: formData.sigma,
          join_date: formData.join_date,
          leaved_date: formData.leaved_date,
          is_active: formData.is_active, // Member 的 is_active
          notes: formData.notes
        };

        // 清理空字串為 null，確保可選欄位正確傳遞
        for (const key in updatePayload) {
          if (updatePayload[key] === '') {
            updatePayload[key] = null;
          }
        }
        // 如果 mu/sigma 允許為空但不能是空字串，可能需要進一步處理
        if (updatePayload.mu === null || updatePayload.mu === '') delete updatePayload.mu;
        if (updatePayload.sigma === null || updatePayload.sigma === '') delete updatePayload.sigma;


        const response = await memberService.updateMember(memberId.value, updatePayload);
        message.success(response.data.message || "成員資料已成功更新！");
        await router.push({name: 'ManagementCenter', query: {tab: 'members'}}); // 跳轉回管理中心並嘗試定位到成員tab
      } catch (err) {
        const errorData = err.response?.data;
        let errorMsgToShow = errorData?.error || errorData?.message || err.message || "更新成員失敗。";
        if (errorData && errorData.errors) {
          errorMsgToShow = errorData.message || "更新失敗，請檢查欄位：";
          for (const field in errorData.errors) {
            errorMsgToShow += `\n- ${field}: ${errorData.errors[field]}`;
          }
        }
        message.error(errorMsgToShow, {duration: 7000, closable: true});
        console.error("Failed to update member:", err.response || err);
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
  // router.back(); // router.back() 可能會回到非預期頁面
  router.push({name: 'ManagementCenter', query: {tab: 'members'}});
}
</script>

<style scoped>
.admin-add-member-page {
  max-width: 800px; /* 與編輯頁面一致或您希望的寬度 */
  margin: 2rem auto 3rem auto; /* 統一頁面上下外邊距 */
  /* background-color: var(--n-body-color); /* 頁面背景色，通常由App.vue或全局設定 */
}

/* 與 RecordMatchView.vue 和 ManagementCenterView.vue 類似的標題樣式 */
.page-main-title {
  font-weight: 600;
  color: var(--n-title-text-color); /* Naive UI 標題文字顏色 */
  display: flex; /* 為了讓返回按鈕和文字垂直對齊 */
  align-items: center;
}

.title-back-button.n-button { /* 返回按鈕樣式 */
  margin-right: 12px; /* 圖標和文字間距 */
  font-size: 1.5rem; /* 調整返回按鈕圖標大小 */
}

.title-back-button.n-button .n-icon {
  color: var(--n-text-color-base); /* Naive UI 基本文字顏色 */
}


/* 與 RecordMatchView.vue 類似的卡片樣式 */
.form-card.n-card {
  margin-top: 1.5rem;
  border-radius: var(--n-border-radius); /* Naive UI 圓角變數 */
  box-shadow: var(--n-box-shadow2); /* Naive UI 二級陰影 */
  background-color: var(--n-card-color); /* Naive UI 卡片背景色 */
  padding: 10px 15px; /* 可選：卡片內部微調padding */
}

/* 分隔線樣式 */
.section-divider.n-divider:not(.n-divider--vertical) {
  margin-top: 1.5rem;
  margin-bottom: 1.25rem;
}

.section-divider.n-divider .n-divider__title { /* 分隔線標題樣式 */
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--n-text-color-2);
}

/* Switch 和旁邊文字的對齊 */
.switch-with-label {
  display: flex;
  align-items: center;
  gap: 8px; /* Switch 和文字之間的間距 */
  height: var(--n-height-m); /* 與其他表單組件高度對齊 (約34px) */
}

.switch-label-text {
  color: var(--n-text-color-3); /* 較淺的文字顏色 */
  font-size: 0.9em;
}

/* 統一按鈕區域樣式 */
.action-buttons.n-space {
  padding-top: 0.5rem; /* 與上方元素的間距 */
}

.action-buttons .n-button {
  min-width: 100px; /* 按鈕最小寬度 */
  font-weight: 500;
}
</style>