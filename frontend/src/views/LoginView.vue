<template>
  <div class="login-page-naive">
    <n-card :bordered="false" class="login-card">
      <n-h2 align="center" class="card-title-naive">登入系統</n-h2>

      <n-alert v-if="loginRouteMessage" title="提示" type="info" closable class="mb-4 login-alert"
               @close="loginRouteMessage = ''">
        {{ loginRouteMessage }}
      </n-alert>

      <n-form
          ref="formRef"
          :model="credentials"
          :rules="formRules"
          label-placement="top"
          require-mark-placement="right-hanging"
          @submit.prevent="handleLogin"
          class="login-form"
      >
        <n-form-item path="username" label="帳號 (手機號碼)">
          <n-input
              v-model:value="credentials.username"
              placeholder="請輸入手機號碼 (09開頭10位數字)"
              size="large"
              clearable
              @keydown.enter.prevent="handleLogin"
          >
            <template #prefix>
              <n-icon :component="PhoneIcon"/>
            </template>
          </n-input>
        </n-form-item>

        <n-form-item path="password" label="密碼">
          <n-input
              type="password"
              show-password-on="click"
              v-model:value="credentials.password"
              placeholder="請輸入密碼"
              size="large"
              clearable
              @keydown.enter.prevent="handleLogin"
          >
            <template #prefix>
              <n-icon :component="LockIcon"/>
            </template>
          </n-input>
        </n-form-item>

        <n-alert v-if="authStore.status.loginError" title="登入失敗" type="error" closable class="mb-3 login-alert"
                 @close="authStore.status.loginError = null">
          {{ authStore.status.loginError }}
        </n-alert>

        <n-form-item :show-label="false" class="submit-button-form-item">
          <n-button
              type="primary"
              attr-type="submit"
              block
              strong
              size="large"
              :loading="authStore.status.loggingIn"
              :disabled="authStore.status.loggingIn"
              class="login-submit-button"
          >
            {{ authStore.status.loggingIn ? '登入中...' : '登入' }}
          </n-button>
        </n-form-item>
      </n-form>

      <n-divider class="login-divider"/>

      <n-space vertical align="center" class="mt-3 additional-actions">
        <n-text>
          還沒有帳號？
          <router-link :to="{ name: 'Register' }" v-slot="{ navigate }">
            <n-button text type="primary" @click="navigate">立即快速註冊</n-button>
          </router-link>
        </n-text>
      </n-space>
    </n-card>
  </div>
</template>

<script setup>
import {onMounted, reactive, ref} from 'vue';
import {useAuthStore} from '@/stores/authStore'; // 確保路徑正確
import {useRoute, useRouter} from 'vue-router';
import {
  NAlert,
  NButton,
  NCard,
  NDivider,
  NForm,
  NFormItem,
  NH2,
  NIcon,
  NInput,
  NSpace,
  NText,
  useMessage
} from 'naive-ui';
import {KeyOutline as LockIcon, PhonePortraitOutline as PhoneIcon} from '@vicons/ionicons5';

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();
const message = useMessage(); // Naive UI message API

const formRef = ref(null); // Ref for NForm instance
const credentials = reactive({
  username: '',
  password: '',
});

const loginRouteMessage = ref('');

// Naive UI 表單驗證規則
const formRules = {
  username: [
    {required: true, message: '手機號碼為必填', trigger: ['input', 'blur']},
    {
      pattern: /^09\d{8}$/,
      message: '手機號碼格式不正確 (應為09開頭10位數字)',
      trigger: ['input', 'blur']
    }
  ],
  password: [
    {required: true, message: '密碼為必填', trigger: ['input', 'blur']},
    {min: 6, message: '密碼長度至少需要6位', trigger: ['input', 'blur']} // 可選的最小長度驗證
  ]
};

onMounted(() => {
  authStore.status.loginError = null;
  if (route.query.loggedOut === 'true') {
    loginRouteMessage.value = '您已成功登出。';
    router.replace({query: {}});
  } else if (route.query.sessionExpired === 'true') {
    loginRouteMessage.value = '您的登入已過期或無效，請重新登入。';
    router.replace({query: {}});
  } else if (route.query.unauthorized === 'true' || route.query.redirect) {
    loginRouteMessage.value = '您需要登入才能訪問該頁面。';
    const query = {...route.query};
    delete query.unauthorized;
    router.replace({query});
  }
});

const handleLogin = () => {
  formRef.value?.validate(async (validationErrors) => {
    if (!validationErrors) {
      // 表單驗證通過，執行登入
      const success = await authStore.login(credentials);
      if (success) {
        const redirectPath = route.query.redirect || '/';
        router.push(redirectPath);
      }
      // 失敗的錯誤訊息由 authStore.status.loginError 在模板中顯示
    } else {
      // Naive UI 會自動在表單項旁邊顯示錯誤，這裡可以選擇性地用 message API 提示
      message.error('請修正表單中的錯誤。');
      console.log('Login form validation errors:', validationErrors);
    }
  });
};
</script>

<style scoped>
.login-page-naive {
  display: flex;
  flex-direction: column; /* 讓卡片在垂直方向上也能有彈性 */
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - var(--header-height, 64px) - var(--footer-height, 67px)); /* 假設 header 和 footer 高度 */
  padding: 20px;
  background-color: var(--n-body-color); /* Naive UI body 背景色 */
  box-sizing: border-box;
}

.login-card.n-card {
  max-width: 400px; /* 登入卡片最大寬度，略微減小 */
  width: 100%;
  border-radius: var(--n-border-radius); /* Naive UI 圓角 */
  box-shadow: var(--n-box-shadow2); /* Naive UI 二級陰影 */
  background-color: var(--n-card-color); /* Naive UI 卡片背景色 */
  padding: 10px; /* 卡片自身的padding，微調 */
}

/* 卡片標題 */
.login-card .card-title-naive.n-h2 {
  font-weight: 600; /* 與 page-main-title 一致 */
  color: var(--n-title-text-color); /* Naive UI 標題顏色 */
  margin-bottom: 1.75rem; /* 標題與表單的間距 */
}

/* 表單 */
.login-form.n-form {
  /* 可在此處為整個表單添加特定樣式 */
}

/* 表單項 */
.login-form .n-form-item {
  margin-bottom: var(--n-form-item-margin-bottom, 24px); /* Naive UI 表單項間距或自訂 */
}

/* 最後一個表單項（按鈕）可能不需要那麼大的底部間距 */
.login-form .submit-button-form-item.n-form-item {
  margin-bottom: 0;
}

/* 輸入框和按鈕使用 Naive UI 的 size="large" 屬性來控制高度和字體大小 */
.login-form .n-input--large-size,
.login-form .login-submit-button.n-button--large-size {
  /* 如果需要微調 large size 的高度，可以在這裡覆寫 --n-height-large */
  /* 例如：--n-height-large: 40px !important; */
}

/* 登入按鈕 */
.login-submit-button.n-button {
  /* size="large" 已設定高度和大部分樣式 */
  /* strong 屬性已在模板中 */
  /* block 屬性已在模板中 */
  font-weight: 500; /* 統一按鈕字重 */
}

/* Alert 間距 */
.login-alert.n-alert {
  margin-bottom: var(--n-form-item-margin-bottom, 24px) !important;
}

/* 分隔線 */
.login-divider.n-divider:not(.n-divider--vertical) {
  margin-top: 1.8rem; /* 與上方元素的間距 */
  margin-bottom: 1.2rem; /* 與下方元素的間距 */
}

/* "還沒有帳號？" 區域 */
.additional-actions.n-space .n-text {
  color: var(--n-text-color-2); /* 使用 Naive UI 次要文字顏色 */
}

.additional-actions.n-space .n-button {
  font-weight: 500;
}
</style>