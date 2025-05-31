<template>
  <div class="edit-profile-page container mt-4 mb-5">
    <h1 class="mb-4 page-title">編輯個人資料</h1>

    <div v-if="loading" class="text-center my-5">
      <div class="spinner-border text-primary" role="status"></div>
    </div>
    <div v-if="fetchError" class="alert alert-danger" role="alert">{{ fetchError }}</div>

    <div v-if="!loading && !fetchError && profileData.user && profileData.member" class="row">
      <div class="col-md-7">
        <div class="card shadow-sm mb-4">
          <div class="card-header bg-light">
            <h5 class="mb-0">基本及球員資料</h5>
          </div>
          <div class="card-body">
            <form @submit.prevent="handleProfileUpdate">
              <div v-if="updateMessage"
                   :class="['alert', updateStatus === 'success' ? 'alert-success' : 'alert-danger']" role="alert">
                <span style="white-space: pre-wrap;">{{ updateMessage }}</span>
              </div>

              <h6>帳號資訊</h6>
              <div class="mb-3">
                <label for="username" class="form-label">登入帳號 (手機號碼)</label>
                <input type="text" class="form-control" id="username" :value="profileData.user.username" readonly
                       disabled>
              </div>
              <div class="mb-3">
                <label for="email" class="form-label">電子郵件</label>
                <input type="email" class="form-control" id="email" v-model="editableProfile.user.email"
                       placeholder="example@example.com">
                <small v-if="validationErrors.email" class="text-danger">{{ validationErrors.email }}</small>
              </div>

              <hr class="my-4">
              <h6>球員資料</h6>
              <div class="mb-3">
                <label for="realName" class="form-label">真實姓名</label>
                <input type="text" class="form-control" id="realName" :value="profileData.member.name" readonly
                       disabled>
                <!--                <small class="form-text text-muted">真實姓名通常由管理員設定，如需修改請洽管理員。</small>-->
              </div>
              <div class="mb-3">
                <label for="displayName" class="form-label">顯示名稱/綽號*</label>
                <input type="text" class="form-control" id="displayName" v-model="editableProfile.member.display_name"
                       required>
              </div>
              <div class="mb-3">
                <label for="studentId" class="form-label">學號</label>
                <input type="text" class="form-control" id="studentId" :value="profileData.member.student_id || ''"
                       readonly disabled>
                <!--                <small class="form-text text-muted">學號通常由管理員設定。</small>-->
              </div>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="gender" class="form-label">性別</label>
                  <select class="form-select" id="gender" v-model="editableProfile.member.gender">
                    <option value="">--不指定--</option>
                    <option value="MALE">男性</option>
                    <option value="FEMALE">女性</option>
                  </select>
                  <small v-if="validationErrors.gender" class="text-danger">{{ validationErrors.gender }}</small>
                </div>
                <div class="col-md-6 mb-3">
                  <label for="position" class="form-label">習慣位置</label>
                  <select class="form-select" id="position" v-model="editableProfile.member.position">
                    <option value="">--不指定--</option>
                    <option value="VERSATILE">皆可</option>
                    <option value="BACK">後排</option>
                    <option value="FRONT">前排</option>
                  </select>
                  <small v-if="validationErrors.position" class="text-danger">{{ validationErrors.position }}</small>
                </div>
              </div>
              <div class="mb-3">
                <label for="organizationName" class="form-label">組織/隊伍</label>
                <input type="text" class="form-control" id="organizationName"
                       v-model="editableProfile.member.organization">
              </div>

              <button type="submit" class="btn btn-primary mt-2" :disabled="savingProfile">
                <span v-if="savingProfile" class="spinner-border spinner-border-sm"></span>
                {{ savingProfile ? '儲存中...' : '儲存基本資料' }}
              </button>
            </form>
          </div>
        </div>
      </div>

      <div class="col-lg-5">
        <ChangePasswordForm @password-changed-status="handlePasswordChangedStatus"/>
      </div>
    </div>
    <div v-else-if="!loading && !fetchError" class="alert alert-warning">
      無法載入個人資料，可能您還沒有關聯的球隊成員檔案。
    </div>
  </div>
</template>

<script setup>
import {onMounted, reactive, ref} from 'vue';
import {useAuthStore} from '../stores/authStore';
import apiClient from '../services/apiClient'; // 假設您有這個 Axios 實例
import ChangePasswordForm from '../components/auth/ChangePasswordForm.vue'; // 引入修改密碼組件

const authStore = useAuthStore();
const loading = ref(true);
const fetchError = ref(null);
const savingProfile = ref(false);
const updateMessage = ref('');
const updateStatus = ref(''); // 'success' or 'error'
const validationErrors = ref({}); // 用於儲存後端回傳的欄位驗證錯誤

const passwordUpdateMessage = ref('');
const passwordUpdateStatus = ref('');

// 用於顯示的當前資料 (不可直接編輯)
const profileData = reactive({
  user: null,
  member: null,
});

// 用於 v-model 綁定表單的編輯中資料
const editableProfile = reactive({
  user: {email: ''},
  member: {
    display_name: '',
    student_id: '', // 通常不可由使用者編輯，這裡可以設為 readonly 或從 profileData 讀取
    gender: '',     // 儲存 Enum 的 NAME, e.g., 'MALE'
    position: '',   // 儲存 Enum 的 NAME
    organization: '',
  }
});

// 填充表單的輔助函數
function populateEditableProfile() {
  if (profileData.user) {
    editableProfile.user.email = profileData.user.email || '';
  }
  if (profileData.member) {
    editableProfile.member.display_name = profileData.member.display_name || '';
    editableProfile.member.student_id = profileData.member.student_id || '';
    editableProfile.member.gender = profileData.member.gender || '';
    editableProfile.member.position = profileData.member.position || '';
    editableProfile.member.organization = profileData.member.organization || '';
  }
}

async function fetchProfileData() {
  loading.value = true;
  fetchError.value = null;
  try {
    const response = await apiClient.get('/profile/me'); // 或 /auth/me
    profileData.user = response.data.user_profile;
    profileData.member = response.data.team_member_profile;
    populateEditableProfile(); // 獲取數據後填充表單
  } catch (err) {
    fetchError.value = err.response?.data?.msg || err.message || "無法載入個人資料";
    console.error("Error fetching profile:", err.response || err);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  if (authStore.isAuthenticated) {
    fetchProfileData();
  } else {
    fetchError.value = "請先登入以編輯個人資料。"; // 理論上會被路由守衛攔截
  }
});

// 當 profileData 從 store (例如登入後) 或 API 更新時，也更新 editableProfile
// watch(() => authStore.currentUser, (newUser) => { // 如果 currentUser 包含所有需要的資訊
//   if(newUser && newUser.id === profileData.user?.id) { // 確保是同一個使用者
//      fetchProfileData(); // 重新獲取最新數據
//   }
// }, {deep: true});


async function handleProfileUpdate() {
  savingProfile.value = true;
  updateMessage.value = '';
  updateStatus.value = '';
  validationErrors.value = {};

  const payload = {
    email: editableProfile.user.email.trim() || null, // 如果為空則傳 null
    display_name: editableProfile.member.display_name.trim(),
    student_id: editableProfile.member.student_id.trim() || null, // 如果允許修改
    gender: editableProfile.member.gender || null, // 直接傳送 Enum 的 NAME (大寫)
    position: editableProfile.member.position || null, // 直接傳送 Enum 的 NAME
    organization: editableProfile.member.organization.trim() || null,
  };

  // 移除 payload 中值為 null 的鍵，如果後端不希望接收它們
  // for (const key in payload) {
  //   if (payload[key] === null) {
  //     delete payload[key];
  //   }
  // }
  if (!payload.display_name) { // 顯示名稱通常是必填的 (至少 fallback 到真實姓名)
    updateMessage.value = "顯示名稱為必填。";
    updateStatus.value = "error";
    savingProfile.value = false;
    return;
  }


  try {
    const response = await apiClient.put('/profile/me', payload);
    updateMessage.value = response.data.message || "個人資料已成功更新！";
    updateStatus.value = 'success';

    // 更新 Pinia store 中的使用者資訊
    if (response.data.user) { // 後端應回傳更新後的 User 物件 (其 to_dict() 包含 team_member_details)
      authStore.user = response.data.user; // 更新整個 user 物件
      localStorage.setItem('user', JSON.stringify(authStore.user)); // 同步到 localStorage
      // 重新填充表單以顯示來自伺服器的最新數據（可選，如果API回傳的就是最新數據）
      profileData.user = response.data.user; // 更新本地顯示用數據
      if (response.data.user.team_member_details) {
        profileData.member = response.data.user.team_member_details;
      }
      populateEditableProfile();
    }

  } catch (err) {
    console.error("Error updating profile:", err.response || err);
    updateMessage.value = err.response?.data?.message || err.response?.data?.error || "更新失敗，請檢查輸入。";
    if (err.response?.data?.errors) {
      validationErrors.value = err.response.data.errors; // 儲存欄位特定錯誤
      let errorDetails = [];
      for (const field in err.response.data.errors) {
        errorDetails.push(`${field}: ${err.response.data.errors[field]}`);
      }
      updateMessage.value = `更新失敗，請檢查以下欄位：\n${errorDetails.join('\n')}`;
    }
    updateStatus.value = 'error';
  } finally {
    savingProfile.value = false;
  }
}

// 用於接收 ChangePasswordForm 組件發出的事件
function handlePasswordChangedStatus(message, status) {
  // 可以在 EditProfileView 中顯示一個統一的訊息區域，或者讓 ChangePasswordForm 自己顯示
  passwordUpdateMessage.value = message; // 或者用一個獨立的 passwordUpdateMessage
  passwordUpdateStatus.value = status;   // 或者用一個獨立的 passwordUpdateStatus
  // 清除訊息，避免一直顯示
  setTimeout(() => {
    passwordUpdateMessage.value = '';
    passwordUpdateStatus.value = '';
  }, 5000);
}

</script>

<style scoped>
.edit-profile-page {
  max-width: 960px;
}

.page-title {
  color: #333;
}

.card-header {
  background-color: #f8f9fa;
}

/* 可以加入更多樣式 */
</style>