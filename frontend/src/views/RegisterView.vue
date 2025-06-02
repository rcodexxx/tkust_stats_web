<template>
  <div class="quick-register-page-naive">
    <n-card :bordered="false" class="register-card" hoverable>
      <n-h2 align="center" class="card-title-naive">快速註冊</n-h2>
      <n-p align="center" class="text-muted-naive mb-4">
        僅需輸入您的手機號碼即可快速加入。<br>
        系統將使用您的手機號碼作為初始密碼，<br>
      </n-p>

      <n-form
          ref="formRef"
          :model="registrationData"
          :rules="formRules"
          label-placement="top"
          require-mark-placement="right-hanging"
          @submit.prevent="handleRegister"
      >
        <n-form-item path="phone_number" label="手機號碼 (將作為您的登入帳號與初始密碼)">
          <n-input
              v-model:value="registrationData.phone_number"
              placeholder="例如：0912345678"
              size="large"
              clearable
              @keydown.enter.prevent="handleRegister"
          >
            <template #prefix>
              <n-icon :component="PhoneIcon"/>
            </template>
          </n-input>
        </n-form-item>

        <n-alert v-if="authStore.status.registerError" title="註冊失敗" type="error" closable class="mb-3"
                 @close="authStore.status.registerError = null">
          {{ authStore.status.registerError }}
        </n-alert>
        <n-alert v-if="successMessage" title="提示" type="info" closable class="mb-3" @close="successMessage = ''">
          {{ successMessage }}
        </n-alert>

        <n-form-item :show-label="false">
          <n-button
              type="primary"
              attr-type="submit"
              block
              strong
              size="large"
              :loading="authStore.status.registering"
              :disabled="authStore.status.registering"
              class="register-button"
          >
            {{ authStore.status.registering ? '註冊中...' : '確認註冊並登入' }}
          </n-button>
        </n-form-item>
      </n-form>

      <n-divider/>

      <n-space vertical align="center" class="mt-3">
        <n-text>
          已經有帳號了？
          <router-link :to="{ name: 'Login' }" v-slot="{ navigate }">
            <n-button text type="primary" @click="navigate">立即登入</n-button>
          </router-link>
        </n-text>
      </n-space>
    </n-card>
  </div>
</template>

<script setup>
import {onMounted, reactive, ref} from 'vue';
import {useAuthStore} from '@/stores/authStore'; // 確保路徑正確
import {useRouter} from 'vue-router';
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
import {PhonePortraitOutline as PhoneIcon} from '@vicons/ionicons5';

const authStore = useAuthStore();
const router = useRouter(); // 如果註冊成功後需要手動跳轉 (雖然 store action 已處理)
const message = useMessage(); // Naive UI message API

const formRef = ref(null); // Ref for NForm instance
const registrationData = reactive({
  phone_number: '', // 後端 API 期待的是 phone_number 或 username 作為手機號
});
const successMessage = ref(''); // 用於顯示註冊成功後的特定訊息 (例如後端回傳的 initial_password_info)

// Naive UI 表單驗證規則
const formRules = {
  phone_number: [
    {required: true, message: '手機號碼為必填', trigger: ['input', 'blur']},
    {
      pattern: /^09\d{8}$/,
      message: '手機號碼格式不正確 (應為09開頭10位數字)',
      trigger: ['input', 'blur']
    }
  ]
};

onMounted(() => {
  authStore.status.registerError = null; // 清除可能殘留的錯誤訊息
});

const handleRegister = () => {
  formRef.value?.validate(async (validationErrors) => {
    if (!validationErrors) {
      successMessage.value = ''; // 清除之前的成功訊息

      // 準備傳遞給 store action 的 payload
      // authStore.register action 期望的 payload 是 { username: '...', ... }
      // 如果您的 register action 內部會將 phone_number 轉為 username，則可以這樣傳
      // 或者直接傳遞符合 action 期望的結構
      const payload = {
        username: registrationData.phone_number, // 將 phone_number 作為 username 傳遞
        // 如果您的 register action 直接接收 phone_number，則用下面的
        // phone_number: registrationData.phone_number
      };

      // 您之前 authStore 中的 register action 的註解是：
      // async register(payload) { // 假設 payload 是 { phone_number: '...' }
      // ... apiClient.post('/auth/quick_register', payload); ...
      // 如果是這樣，那 payload 應該是 { phone_number: ... }
      // 請確保與 authStore.register action 的期望一致
      // 假設 authStore.register 期望 { username: '...' }
      const success = await authStore.register(payload);

      if (success) {
        // 登入成功訊息和跳轉已在 authStore.register action 中處理 (例如 alert(initial_password_info))
        // 這裡可以選擇性地再顯示一個訊息，或者完全依賴 store 中的提示
        // 例如，如果 store 中沒有 alert，可以在這裡 message.success
        // message.success("註冊成功並已自動登入！請記住您的初始密碼。");
      }
      // 錯誤訊息由 authStore.status.registerError 在模板中顯示
    } else {
      message.error('請修正表單中的錯誤。');
      console.log('Quick Register form validation errors:', validationErrors);
    }
  });
};
</script>

<style scoped>
.quick-register-page-naive {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 120px); /* 減去 header 和 footer 的大致高度 */
  padding: 20px;
  background-color: var(--body-color); /* 使用 App.vue themeOverrides 中的 bodyColor */
}

.register-card.n-card {
  max-width: 420px;
  width: 100%;
  border-radius: var(--border-radius-large, 12px); /* 使用主題設定或自訂 */
  box-shadow: var(--box-shadow-2);
}

.card-title-naive.n-h2 {
  font-weight: 700; /* 來自 uenify 的 font-weight */
  color: var(--text-color-1); /* 使用主題設定 */
}

.text-muted-naive { /* 自訂的 muted text 顏色 */
  color: var(--text-color-3, #888888);
  font-size: 0.9em;
}

.n-form-item {
  margin-bottom: 20px;
}

.n-alert {
  margin-bottom: 20px !important;
}

.register-button.n-button { /* 如果用 block 屬性，確保 padding 合適 */
  /* Naive UI Button size="large" 通常有合適的 padding */
}

.n-divider {
  margin-top: 1.5rem;
  margin-bottom: 1rem;
}
</style>