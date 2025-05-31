<template>
  <div class="quick-register-page container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-6 col-lg-5 col-xl-4">
        <div class="card shadow-sm">
          <div class="card-body p-4 p-lg-5">
            <h2 class="card-title text-center mb-4 fw-bold">快速註冊</h2>
            <!--            <p class="text-center text-muted mb-4 small">-->
            <!--              僅需輸入您的手機號碼即可快速加入。系統將為您設定一組初始密碼，強烈建議您首次登入後立即修改。</p>-->

            <form @submit.prevent="handleRegister">
              <div class="mb-3">
                <label for="phone_number" class="form-label">手機號碼 (將作為您的登入帳號)*</label>
                <input
                    type="tel"
                    class="form-control form-control-lg"
                    id="phone_number"
                    v-model="registrationData.phone_number"
                    required
                    placeholder="例如：0912345678"
                    pattern="09\d{8}"
                    title="請輸入有效的10位台灣手機號碼 (09開頭)"
                >
              </div>

              <div v-if="authStore.status.registerError" class="alert alert-danger p-2 py-1 mb-3 text-center small">
                {{ authStore.status.registerError }}
              </div>
              <div v-if="successMessage" class="alert alert-success p-2 py-1 mb-3 text-center small">
                {{ successMessage }}
              </div>

              <div class="d-grid">
                <button type="submit" class="btn btn-success btn-lg" :disabled="authStore.status.registering">
                  <span v-if="authStore.status.registering" class="spinner-border spinner-border-sm me-2" role="status"
                        aria-hidden="true"></span>
                  {{ authStore.status.registering ? '註冊中...' : '註冊並登入' }}
                </button>
              </div>
            </form>

            <div class="mt-4 text-center">
              <small class="text-muted">
                已經有帳號了？
                <router-link :to="{ name: 'Login' }">直接登入</router-link>
              </small>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {onMounted, reactive, ref} from 'vue';
import {useAuthStore} from '../stores/authStore';

const authStore = useAuthStore();
const registrationData = reactive({
  phone_number: '',
});
const successMessage = ref(''); // 用於顯示註冊成功後的特定訊息

onMounted(() => {
  authStore.status.registerError = null; // 清除可能殘留的錯誤訊息
});

const handleRegister = async () => {
  if (!registrationData.phone_number || !/^09\d{8}$/.test(registrationData.phone_number)) {
    authStore.status.registerError = '請輸入有效的10位台灣手機號碼 (09開頭)。';
    return;
  }
  successMessage.value = ''; // 清除之前的成功訊息
  const success = await authStore.register(registrationData);
  if (success) {
    // authStore.quickRegister 內部已經處理了跳轉和 token/user 設定
    // 可以在這裡設定一個額外的成功訊息，或者依賴 authStore 的提示
    // successMessage.value = "註冊成功！已自動為您登入。請記住您的初始密碼。";
    // alert(...) 的提示在 authStore 中
  }
  // 錯誤訊息由 authStore.status.registerError 顯示
};
</script>

<style scoped>
.login-page {
  width: 100%;
}

.form-signin {
  max-width: 400px;
  padding: 1rem;
}

.form-signin .form-floating:focus-within {
  z-index: 2;
}

.form-signin input[type="text"] {
  margin-bottom: -1px;
  border-bottom-right-radius: 0;
  border-bottom-left-radius: 0;
}

.form-signin input[type="password"] {
  margin-bottom: 10px;
  border-top-left-radius: 0;
  border-top-right-radius: 0;
}

.card {
  border-radius: 1rem;
}

.btn-lg {
  font-weight: 500;
}
</style>