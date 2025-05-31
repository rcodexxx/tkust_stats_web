<template>
  <div class="login-page container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-6 col-lg-5 col-xl-4">
        <div class="card shadow-sm">
          <div class="card-body p-4 p-lg-5">
            <h2 class="card-title text-center mb-4 fw-bold">登入</h2>

            <div v-if="loginRouteMessage" class="alert alert-info p-2 mb-3 text-center small">
              {{ loginRouteMessage }}
            </div>

            <form @submit.prevent="handleLogin">
              <div class="mb-3">
                <label for="username" class="form-label">帳號 (手機號碼)</label>
                <input
                    type="text"
                    class="form-control form-control-lg"
                    id="username"
                    v-model="credentials.username"
                    required
                    placeholder="請輸入手機號碼"
                    autocomplete="username"
                >
              </div>
              <div class="mb-4">
                <label for="password" class="form-label">密碼</label>
                <input
                    type="password"
                    class="form-control form-control-lg"
                    id="password"
                    v-model="credentials.password"
                    required
                    placeholder="請輸入密碼"
                    autocomplete="current-password"
                >
              </div>

              <div v-if="authStore.status.loginError" class="alert alert-danger p-2 py-1 mb-3 text-center small">
                {{ authStore.status.loginError }}
              </div>

              <div class="d-grid">
                <button type="submit" class="btn btn-primary btn-lg" :disabled="authStore.status.loggingIn">
                  <span v-if="authStore.status.loggingIn" class="spinner-border spinner-border-sm me-2" role="status"
                        aria-hidden="true"></span>
                  {{ authStore.status.loggingIn ? '登入中...' : '登入' }}
                </button>
              </div>
            </form>

            <div class="mt-4 text-center">
              <small class="text-muted">
                還沒有帳號？
                <router-link :to="{ name: 'Register' }">快速註冊</router-link>
              </small>
              <br>
              <!--              <small class="text-muted">-->
              <!--                <router-link to="/forgot-password" class="text-decoration-none">忘記密碼？</router-link>-->
              <!--              </small>-->
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
import {useRoute, useRouter} from 'vue-router'; // 匯入 useRoute

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute(); // 獲取當前路由資訊

const credentials = reactive({
  username: '', // 將會是手機號碼
  password: '',
});

const loginRouteMessage = ref('');

onMounted(() => {
  // 清除之前的登入錯誤訊息 (如果有的話)
  authStore.status.loginError = null;
  // 檢查路由查詢參數是否有登出訊息
  if (route.query.loggedOut === 'true') {
    loginRouteMessage.value = '您已成功登出。';
    // 清除查詢參數，避免刷新頁面時再次顯示
    router.replace({query: {}});
  } else if (route.query.sessionExpired === 'true') {
    loginRouteMessage.value = '您的登入已過期，請重新登入。';
    router.replace({query: {}});
  } else if (route.query.unauthorized === 'true') {
    loginRouteMessage.value = '您需要登入才能訪問該頁面。';
    router.replace({query: {}});
  }
});

const handleLogin = async () => {
  if (!credentials.username || !credentials.password) {
    authStore.status.loginError = '手機號碼和密碼皆為必填。';
    return;
  }
  await authStore.login(credentials);
  // 導航邏輯已在 authStore.login action 中處理
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