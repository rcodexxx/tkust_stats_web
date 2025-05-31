<template>
  <div class="card shadow-sm change-password-card">
    <div class="card-header bg-light">
      <h5 class="mb-0"><i class="bi bi-key-fill me-2"></i>修改密碼</h5>
    </div>
    <div class="card-body">
      <div v-if="message"
           :class="['alert', status === 'success' ? 'alert-success' : 'alert-danger', 'alert-dismissible', 'fade', 'show']"
           role="alert">
        <span style="white-space: pre-wrap;">{{ message }}</span>
        <button type="button" class="btn-close" @click="clearMessage" aria-label="Close"></button>
      </div>
      <form @submit.prevent="handleChangePassword">
        <div class="mb-3">
          <label for="old_password" class="form-label">目前密碼*</label>
          <div class="input-group">
            <input :type="showOldPassword ? 'text' : 'password'"
                   class="form-control"
                   id="old_password"
                   v-model="passwords.old_password"
                   required
                   autocomplete="current-password">
            <button class="btn btn-outline-secondary" type="button" @click="toggleOldPasswordVisibility"
                    title="顯示/隱藏密碼">
              <i :class="showOldPassword ? 'bi bi-eye-slash-fill' : 'bi bi-eye-fill'"></i>
            </button>
          </div>
        </div>
        <div class="mb-3">
          <label for="new_password" class="form-label">新密碼*</label>
          <div class="input-group">
            <input :type="showNewPassword ? 'text' : 'password'"
                   class="form-control"
                   id="new_password"
                   v-model="passwords.new_password"
                   required
                   autocomplete="new-password">
            <button class="btn btn-outline-secondary" type="button" @click="toggleNewPasswordVisibility"
                    title="顯示/隱藏密碼">
              <i :class="showNewPassword ? 'bi bi-eye-slash-fill' : 'bi bi-eye-fill'"></i>
            </button>
          </div>
          <small class="form-text text-muted">密碼長度至少6位。</small>
        </div>
        <div class="mb-3">
          <label for="confirm_new_password" class="form-label">確認新密碼*</label>
          <div class="input-group">
            <input :type="showConfirmNewPassword ? 'text' : 'password'"
                   class="form-control"
                   id="confirm_new_password"
                   v-model="passwords.confirm_new_password"
                   required
                   autocomplete="new-password">
            <button class="btn btn-outline-secondary" type="button" @click="toggleConfirmNewPasswordVisibility"
                    title="顯示/隱藏密碼">
              <i :class="showConfirmNewPassword ? 'bi bi-eye-slash-fill' : 'bi bi-eye-fill'"></i>
            </button>
          </div>
          <small
              v-if="passwords.new_password && passwords.confirm_new_password && passwords.new_password !== passwords.confirm_new_password"
              class="text-danger d-block mt-1">
            新密碼與確認密碼不一致！
          </small>
        </div>
        <button type="submit" class="btn btn-warning w-100" :disabled="submitting">
          <span v-if="submitting" class="spinner-border spinner-border-sm me-1"></span>
          {{ submitting ? '處理中...' : '確認修改密碼' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import {defineEmits, reactive, ref} from 'vue';
import apiClient from '../../services/apiClient'; // 您的 Axios 實例
// import { useAuthStore } from '@/stores/authStore'; // 如果需要登出等操作

// const authStore = useAuthStore(); // 如果需要登出

const passwords = reactive({
  old_password: '',
  new_password: '',
  confirm_new_password: ''
});

const showOldPassword = ref(false);
const showNewPassword = ref(false);
const showConfirmNewPassword = ref(false);

const submitting = ref(false);
const message = ref('');
const status = ref(''); // 'success' or 'error'

const emit = defineEmits(['password-changed-status']); // 用於通知父組件結果

function toggleOldPasswordVisibility() {
  showOldPassword.value = !showOldPassword.value;
}

function toggleNewPasswordVisibility() {
  showNewPassword.value = !showNewPassword.value;
}

function toggleConfirmNewPasswordVisibility() {
  showConfirmNewPassword.value = !showConfirmNewPassword.value;
}

function clearMessage() {
  message.value = '';
  status.value = '';
}

async function handleChangePassword() {
  clearMessage(); // 清除舊訊息

  if (!passwords.old_password || !passwords.new_password || !passwords.confirm_new_password) {
    message.value = '所有密碼欄位皆為必填。';
    status.value = 'error';
    emit('password-changed-status', message.value, status.value);
    return;
  }
  if (passwords.new_password.length < 6) { // 與後端驗證一致
    message.value = '新密碼長度至少需要6位。';
    status.value = 'error';
    emit('password-changed-status', message.value, status.value);
    return;
  }
  if (passwords.new_password !== passwords.confirm_new_password) {
    message.value = '新密碼與確認新密碼不一致。';
    status.value = 'error';
    emit('password-changed-status', message.value, status.value);
    return;
  }

  submitting.value = true;
  try {
    const response = await apiClient.post('/auth/change-password', { // API 端點
      old_password: passwords.old_password,
      new_password: passwords.new_password
      // 後端不需要 confirm_new_password，前端已驗證
    });
    message.value = response.data.msg || '密碼已成功修改！建議您重新登入以確保所有變更生效。';
    status.value = 'success';
    // 清空表單
    passwords.old_password = '';
    passwords.new_password = '';
    passwords.confirm_new_password = '';
    // 成功修改密碼後，可以考慮是否要強制使用者重新登入，或者提示他們
    // authStore.logoutAndRedirect(); // 例如，修改密碼後強制重新登入
  } catch (err) {
    message.value = err.response?.data?.msg || '修改密碼失敗，請檢查您輸入的目前密碼是否正確。';
    status.value = 'error';
    console.error("Error changing password:", err.response || err);
  } finally {
    submitting.value = false;
    emit('password-changed-status', message.value, status.value); // 無論成功失敗都通知父組件
  }
}
</script>

<style scoped>
.change-password-card {
  /* 您可以為這個卡片添加特定樣式 */
}

.card-header h5 {
  font-weight: 600;
  color: #333;
}

.form-text.text-muted {
  font-size: 0.8rem;
}

.btn-outline-secondary { /* 密碼顯示切換按鈕樣式 */
  min-width: 40px; /* 確保按鈕有足夠寬度 */
}
</style>