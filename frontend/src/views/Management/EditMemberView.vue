<template>
  <div class="admin-edit-member-page container mt-4 mb-5">
    <n-h1>
      <n-button text @click="goBack" class="me-2">
        <template #icon>
          <n-icon :component="ArrowBackIcon"/>
        </template>
      </n-button>
      編輯成員資料
    </n-h1>

    <div v-if="loadingData" class="text-center my-5">
      <div class="spinner-border text-primary"></div>
    </div>
    <div v-if="fetchError" class="alert alert-danger">{{ fetchError }}</div>

    <n-card :bordered="false" class="shadow-sm" v-if="!loadingData && !fetchError && formData.name !== undefined">
      <n-form
          ref="formRef"
          :model="formData"
          label-placement="top"
          require-mark-placement="right-hanging"
          @submit.prevent="handleUpdateMember"
      >
        <n-grid :x-gap="24" :y-gap="12" :cols="12" item-responsive>
          <n-form-item-gi :span="12" label="真實姓名*" path="name">
            <n-input v-model:value="formData.name" placeholder="成員的真實姓名"/>
          </n-form-item-gi>
          <n-form-item-gi :span="12" label="顯示名稱/綽號" path="display_name">
            <n-input v-model:value="formData.display_name" placeholder="排行榜上顯示的名稱"/>
          </n-form-item-gi>

          <n-gi :span="12">
            <n-divider title-placement="left">帳號資訊</n-divider>
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
            <n-divider title-placement="left">球員詳細資料</n-divider>
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

          <n-form-item-gi :span="12" :md="6" label="&mu;" path="mu">
            <n-input-number
                v-model:value="formData.mu"
                :min="0"
                :step="0.1"
                placeholder="預設 (例如 25.0)"
                clearable
                style="width:100%"
                :disabled="true"
            />
          </n-form-item-gi>

          <n-form-item-gi :span="12" :md="6" label="&sigma;" path="sigma">
            <n-input-number
                v-model:value="formData.sigma"
                :min="0.1"
                :step="0.001"
                placeholder="預設 (例如 8.333)"
                clearable
                style="width:100%"
                :disabled="true"
            />
          </n-form-item-gi>

          <n-form-item-gi :span="12" :md="6" label="入隊日期" path="joined_date">
            <n-date-picker
                v-model:formatted-value="formData.joined_date"
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

          <n-form-item-gi :span="12" label="備註" path="notes">
            <n-input
                type="textarea"
                v-model:value="formData.notes"
                placeholder="選填"
                :autosize="{ minRows: 2, maxRows: 4 }"
            />
          </n-form-item-gi>
        </n-grid>

        <n-space justify="end" class="mt-4">
          <n-button @click="goBack">取消</n-button>
          <n-button type="primary" attr-type="submit" :loading="submitting">
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
import {NButton, NCard, NDivider, NForm, NFormItemGi, NH1, NIcon, NInput, NSelect, NSpace, useMessage} from 'naive-ui';
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
  password: '', // User 密碼 (僅新增時，或有專門修改密碼功能)
  email: '',    // User.email
  role: 'MEMBER',// User.role
  is_active_user: true, // User.is_active

  student_id: '', // Member.student_id (學號)
  gender: null,     // Member.gender (Enum NAME, e.g., 'MALE')
  position: null,   // Member.position (Enum NAME)
  organization_id: null, // Member.organization_id
  mu: null,
  sigma: null,
  joined_date: null, // Member.joined_date (YYYY-MM-DD string)
  leaved_date: null, // Member.leaved_date (YYYY-MM-DD string)
  is_active: true,  // Member.is_active
  notes: ''
});

const roleOptions = [
  {label: '隊員', value: 'MEMBER'}, // label 是中文，value 是 Enum 的 NAME
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
    formData.gender = memberData.gender || null; // API 應回傳 Enum NAME
    formData.position = memberData.position || null;
    formData.organization_id = memberData.organization_id || null;
    formData.mu = memberData.mu || null;
    formData.sigma = memberData.sigma || null;
    formData.joined_date = memberData.joined_date || null; // 使用 Member 模型的 joined_date
    formData.leaved_date = memberData.leaved_date || null;
    formData.is_active = typeof memberData.is_active === 'boolean' ? memberData.is_active : true;
    formData.notes = memberData.notes || '';

    // 填充 User 相關欄位 (如果存在)
    formData.username = memberData.username || ''; // username (手機號)
    formData.email = memberData.user_email || ''; // 假設 to_dict 返回 user_email
    formData.role = memberData.user_role || '';

    // 獲取組織列表用於下拉選單
    const orgResponse = await organizationService.getOrganizations();
    organizationOptions.value = orgResponse.data || [];

  } catch (err) {
    fetchError.value = "無法載入成員資料進行編輯。";
    console.error("Failed to fetch member details:", err);
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
.admin-edit-member-page {
  max-width: 800px;
  margin: auto;
}
</style>