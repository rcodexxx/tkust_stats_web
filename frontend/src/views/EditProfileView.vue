<template>
  <div class="edit-profile-page container-fluid mt-4 mb-5 px-md-4">
    <n-h1 align="center" class="page-main-title mb-4">
      <n-icon :component="SettingsIcon" size="30" class="title-icon"/>
      編輯個人資料與帳號設定
    </n-h1>

    <div v-if="loading" class="text-center my-5">
      <n-spin size="large"/>
    </div>
    <n-alert title="載入錯誤" type="error" v-if="fetchError" closable @close="fetchError = null" class="mb-4">
      {{ fetchError }}
    </n-alert>

    <n-grid x-gap="24" y-gap="16" :cols="12" item-responsive
            v-if="!loading && !fetchError && profileData.user && profileData.member">
      {/* --- 左側：基本及球員資料編輯 --- */}
      <n-gi :span="12" :md="7">
        <n-card title="基本及球員資料" :bordered="false" class="form-section-card">
          <n-form
              ref="profileFormRef"
              :model="editableProfile"
              :rules="profileFormRules"
              label-placement="top"
              require-mark-placement="right-hanging"
              @submit.prevent="handleProfileUpdate"
          >
            <n-alert
                v-if="profileUpdateMessage"
                :title="profileUpdateStatus === 'success' ? '成功' : '更新失敗'"
                :type="profileUpdateStatus === 'success' ? 'success' : 'error'"
                closable
                class="mb-4"
                @close="clearProfileUpdateMessage"
            >
              <span style="white-space: pre-wrap;">{{ profileUpdateMessage }}</span>
            </n-alert>

            <n-h6 class="form-section-subtitle">帳號資訊</n-h6>
            <n-form-item-gi :span="12" label="登入帳號 (手機號碼)">
              <n-input :value="profileData.user?.username" readonly disabled/>
            </n-form-item-gi>
            <n-form-item-gi :span="12" label="電子郵件" path="user.email">
              <n-input v-model:value="editableProfile.user.email" placeholder="example@example.com" clearable/>
            </n-form-item-gi>
            <n-form-item-gi :span="12" label="目前角色">
              <n-tag v-if="profileData.user?.role" :type="getRoleNaiveType(profileData.user.role)" round>
                {{ getRoleDisplay(profileData.user.role) }}
              </n-tag>
              <span v-else>未設定</span>
            </n-form-item-gi>


            <n-divider/>
            <n-h6 class="form-section-subtitle">球員資料</n-h6>
            <n-form-item-gi :span="12" label="真實姓名">
              <n-input :value="profileData.member?.name" readonly disabled/>
            </n-form-item-gi>
            <n-form-item-gi :span="12" label="學號">
              <n-input :value="profileData.member?.student_id || ''" readonly disabled/>
            </n-form-item-gi>

            <n-form-item-gi :span="12" label="顯示名稱/綽號*" path="member.display_name">
              <n-input v-model:value="editableProfile.member.display_name" placeholder="您希望顯示的名稱"/>
            </n-form-item-gi>

            <n-grid :x-gap="16" :cols="2" :collapsed="isMobile" :collapsed-rows="2">
              <n-form-item-gi label="性別" path="member.gender">
                <n-select v-model:value="editableProfile.member.gender" :options="genderOptions" placeholder="選擇性別"
                          clearable/>
              </n-form-item-gi>
              <n-form-item-gi label="習慣位置" path="member.position">
                <n-select v-model:value="editableProfile.member.position" :options="positionOptions"
                          placeholder="選擇位置" clearable/>
              </n-form-item-gi>
            </n-grid>

            <n-form-item-gi :span="12" label="所屬組織" path="member.organization_id">
              <n-select
                  v-model:value="editableProfile.member.organization_id"
                  :options="organizationOptions"
                  placeholder="選擇組織"
                  clearable
                  filterable
                  label-field="label"
                  value-field="value"/>
            </n-form-item-gi>

            <n-button type="primary" attr-type="submit" :loading="savingProfile" strong block class="mt-3">
              {{ savingProfile ? '儲存中...' : '儲存個人資料' }}
            </n-button>
          </n-form>
        </n-card>
      </n-gi>
      <n-gi :span="12" :md="5">
        <ChangePasswordForm @password-changed-status="handlePasswordChangedStatusMessage" class="form-section-card"/>
      </n-gi>
    </n-grid>

    <div v-else-if="!loading && !fetchError && !profileData.member" class="mt-4">
      <n-alert title="提示" type="info">
        您的帳號尚未關聯球隊成員資料，部分個人資料功能可能不可用。請聯繫管理員。
      </n-alert>
    </div>
  </div>
</template>

<script setup>
import {computed, onMounted, reactive, ref} from 'vue';
import {useAuthStore} from '@/stores/authStore';
import {useRouter} from 'vue-router';
import apiClient from '@/services/apiClient';
import organizationService from '@/services/organizationService';
import ChangePasswordForm from '@/components/auth/ChangePasswordForm.vue';
import {
  NAlert,
  NButton,
  NCard,
  NDivider,
  NForm,
  NFormItemGi,
  NGi,
  NGrid,
  NH1,
  NH6,
  NIcon,
  NInput,
  NSelect,
  NSpin,
  useMessage
} from 'naive-ui';
import {SettingsOutline as SettingsIcon} from '@vicons/ionicons5';

const authStore = useAuthStore();
const router = useRouter();
// const route = useRoute(); // 如果不需要從路由讀取 id (因為是 /profile/me)
const message = useMessage();

const loading = ref(true); // 修改變數名稱以區分
const fetchError = ref(null);
const savingProfile = ref(false);
const profileUpdateMessage = ref('');
const profileUpdateStatus = ref('');
// const validationErrors = ref({}); // Naive UI Form 會自己處理欄位驗證提示

const profileFormRef = ref(null);

// 顯示用資料 (從 API 獲取)
const profileData = reactive({
  user: null,
  member: null,
});

// 表單綁定用資料 (只包含使用者可編輯的欄位)
const editableProfile = reactive({
  user: {email: ''},
  member: {
    display_name: '',
    gender: null,
    position: null,
    organization_id: null,
    racket: '',
    notes: ''
    // username, name, student_id, role, mu, sigma, is_active* 不讓使用者自己改
  }
});

// 下拉選單選項
const genderOptions = [
  {label: '男性', value: 'MALE'}, {label: '女性', value: 'FEMALE'}
];
const positionOptions = [
  {label: '皆可', value: 'VERSATILE'},
  {label: '後排', value: 'BACK'},
  {label: '前排', value: 'FRONT'}
];
const organizationOptions = ref([]);

// Naive UI 表單驗證規則 (只驗證可編輯欄位)
const profileFormRules = {
  user: {
    email: [{type: 'email', message: '請輸入有效的電子郵件格式', trigger: ['input', 'blur']}]
  },
  member: {
    display_name: [{required: true, message: '顯示名稱/綽號為必填', trigger: ['input', 'blur']}],
  }
};

function populateEditableForms() {
  if (profileData.user) {
    editableProfile.user.email = profileData.user.email || '';
  }
  if (profileData.member) {
    editableProfile.member.display_name = profileData.member.display_name || (profileData.member.name || '');
    editableProfile.member.gender = profileData.member.gender || null; // API 應回傳 Enum NAME
    editableProfile.member.position = profileData.member.position || null;
    editableProfile.member.organization_id = profileData.member.organization_id || null;
  }
}

async function fetchProfileData() {
  loading.value = true;
  fetchError.value = null;
  try {
    const response = await apiClient.get('/profile/me'); // 使用者獲取自己的資料
    if (response.data.user_profile && response.data.team_member_profile) {
      profileData.user = response.data.user_profile;
      profileData.member = response.data.team_member_profile;
      populateEditableForms();
    } else {
      fetchError.value = "無法獲取完整的個人資料。";
      if (!response.data.team_member_profile && response.data.user_profile) {
        fetchError.value = "您的帳號尚未關聯球隊成員資料，部分個人資料功能可能不可用。請聯繫管理員。";
        profileData.user = response.data.user_profile; // 至少顯示 User 資料
      }
    }
  } catch (err) {
    fetchError.value = err.response?.data?.msg || err.message || "無法載入個人資料";
    console.error("Error fetching profile:", err.response || err);
  } finally {
    loading.value = false;
  }
}

async function fetchOrganizationOptions() {
  try {
    const orgResponse = await organizationService.getOrganizations();
    organizationOptions.value = orgResponse.data.map(org => ({
      label: org.name + (org.short_name ? ` (${org.short_name})` : ''),
      value: org.id // value 是數字 ID
    })) || [];
  } catch (error) {
    message.error("載入組織列表失敗");
  }
}

onMounted(() => {
  if (authStore.isAuthenticated) {
    fetchProfileData();
    fetchOrganizationOptions();
  } else {
    fetchError.value = "請先登入以編輯個人資料。";
    router.push({name: 'Login', query: {unauthorized: 'true'}});
  }
});

const handleProfileUpdate = async () => {
  profileFormRef.value?.validate(async (validationErrs) => {
    if (!validationErrs) {
      savingProfile.value = true;
      profileUpdateMessage.value = '';
      profileUpdateStatus.value = '';

      const payload = {
        email: editableProfile.user.email?.trim() || null,
        display_name: editableProfile.member.display_name?.trim(),
        gender: editableProfile.member.gender || null,
        position: editableProfile.member.position || null,
        organization_id: editableProfile.member.organization_id === '' ? null : editableProfile.member.organization_id, // 空字串轉 null
      };
      if (!payload.display_name) {
        message.error("顯示名稱為必填。");
        savingProfile.value = false;
        return;
      }

      try {
        const response = await apiClient.put('/profile/me', payload); // API 端點也應對應使用者更新自己的資料
        profileUpdateMessage.value = response.data.message || "個人資料已成功更新！";
        profileUpdateStatus.value = 'success';
        message.success(profileUpdateMessage.value);

        // 更新 Pinia store 和本地顯示數據
        if (response.data.user) { // 假設後端回傳更新後的 User (內含 member detail)
          authStore.user = response.data.user;
          localStorage.setItem('user', JSON.stringify(authStore.user));
          profileData.user = response.data.user; // 使用 User.to_dict() 結構
          if (response.data.user.team_member_details) { // 根據後端 User.to_dict() 結構
            profileData.member = response.data.user.team_member_details;
          } else if (response.data.user_profile && response.data.team_member_profile) { // 或者分離的結構
            profileData.user = response.data.user_profile;
            profileData.member = response.data.team_member_profile;
          }
          populateEditableForms();
        } else if (response.data.user_profile && response.data.team_member_profile) {
          // 另一種可能的回應結構
          const updatedUserForStore = {
            ...authStore.user,
            email: response.data.user_profile.email,
            name: response.data.team_member_profile.name,
            display_name: response.data.team_member_profile.display_name,
          };
          authStore.user = updatedUserForStore;
          localStorage.setItem('user', JSON.stringify(updatedUserForStore));
          profileData.user = response.data.user_profile;
          profileData.member = response.data.team_member_profile;
          populateEditableForms();
        }

      } catch (err) {
        profileUpdateStatus.value = 'error';
        if (err.response && err.response.data) {
          if (err.response.data.errors) {
            let errorMsg = err.response.data.message || "請修正表單中的錯誤：";
            for (const field in err.response.data.errors) {
              errorMsg += `\n- ${field}: ${err.response.data.errors[field]}`;
            }
            profileUpdateMessage.value = errorMsg;
            message.error(errorMsg, {duration: 7000});
          } else {
            profileUpdateMessage.value = err.response.data.error || err.response.data.message || "更新失敗。";
            message.error(profileUpdateMessage.value);
          }
        } else {
          profileUpdateMessage.value = "更新失敗，請稍後再試。";
          message.error(profileUpdateMessage.value);
        }
        console.error("Error updating profile:", err.response || err);
      } finally {
        savingProfile.value = false;
      }
    } else {
      message.error("請檢查表單，修正錯誤後再提交。");
    }
  });
};

function handlePasswordChangedStatusMessage(msg, status) {
  // 這個函數現在用於在 EditProfileView 的 alert 中顯示密碼修改結果
  profileUpdateMessage.value = msg;
  profileUpdateStatus.value = status;
  setTimeout(() => {
    profileUpdateMessage.value = '';
    profileUpdateStatus.value = '';
  }, 7000); // 7 秒後清除訊息
}

function clearProfileUpdateMessage() {
  profileUpdateMessage.value = '';
  profileUpdateStatus.value = '';
}

function goBack() {
  router.back();
} // 或 router.push({ name: 'Leaderboard' });

const isMobile = computed(() => typeof window !== 'undefined' && window.innerWidth < 768);

// 輔助函數：獲取角色顯示名稱
function getRoleDisplay(roleName) {
  if (roleName === 'ADMIN') return '管理員';
  if (roleName === 'CADRE') return '幹部';
  if (roleName === 'COACH') return '教練';
  if (roleName === 'PLAYER') return '隊員';
  return roleName || '未設定';
}

// 輔助函數：獲取 Naive UI Tag 的 type
function getRoleNaiveType(roleName) {
  if (roleName === 'ADMIN') return 'error';
  if (roleName === 'CADRE') return 'warning';
  if (roleName === 'PLAYER') return 'info';
  if (roleName === 'COACH') return 'success';
  return 'default';
}

</script>

<style scoped>
.edit-profile-page {
  max-width: 1000px; /* 調整以容納兩欄 */
  margin: auto;
}

.page-main-title.n-h1 {
  font-weight: 600;
  color: var(--text-color-1);
}

.title-icon {
  color: var(--primary-color);
  margin-right: 10px;
  vertical-align: -4px;
}

.form-section-card.n-card {
  margin-top: 0;
  box-shadow: var(--box-shadow-1); /* 使用主題中較淺的陰影 */
}

.form-section-card .n-card-header {
  padding-bottom: 12px;
  font-weight: 600;
}

.form-section-card .n-card__content {
  padding-top: 20px; /* 增加卡片內容的上邊距 */
}


.form-section-subtitle.n-h6 {
  font-weight: 600;
  margin-top: 1.5rem;
  margin-bottom: 1rem;
  color: var(--primary-color);
  border-bottom: 1px solid #efefef;
  padding-bottom: 0.5rem;
  font-size: 1.1em;
}

.form-section-subtitle:first-of-type {
  margin-top: 0.5rem; /* 第一個子標題的上邊距小一點 */
}

.n-form-item .n-form-item-label {
  font-weight: 500 !important;
  color: var(--text-color-2) !important; /* 標籤使用次要文字顏色 */
}

.form-text.text-muted {
  font-size: 0.8em;
  color: var(--text-color-3) !important; /* 更淺的輔助文字 */
}

.n-button[block] {
  margin-top: 0.5rem; /* 按鈕與上方元素的間距 */
}
</style>