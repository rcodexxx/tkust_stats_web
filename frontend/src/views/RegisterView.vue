<template>
  <div class="quick-register-page-naive">
    <n-card :bordered="false" class="register-card">
      <n-h2 align="center" class="card-title-naive">快速註冊</n-h2>
      <n-p align="center" class="card-subtitle-naive mb-4">
        僅需輸入您的手機號碼即可快速加入。<br>
        系統將使用您的手機號碼作為初始密碼。
      </n-p>

      <n-form
          ref="formRef"
          :model="registrationData"
          :rules="formRules"
          label-placement="top"
          require-mark-placement="right-hanging"
          @submit.prevent="handleRegister"
          class="register-form"
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

        <n-alert v-if="authStore.status.registerError" title="註冊失敗" type="error" closable class="mb-3 form-alert"
                 @close="authStore.clearRegisterError()">
          {{ authStore.status.registerError }}
        </n-alert>
        <n-alert v-if="successMessage" title="提示" type="info" closable class="mb-3 form-alert"
                 @close="successMessage = ''">
          {{ successMessage }}
        </n-alert>

        <n-form-item :show-label="false" class="submit-button-form-item">
          <n-button
              type="primary"
              attr-type="submit"
              block
              strong
              size="large"
              :loading="authStore.status.registering"
              :disabled="authStore.status.registering"
              class="register-button main-submit-button"
          >
            {{ authStore.status.registering ? '註冊中...' : '確認註冊並登入' }}
          </n-button>
        </n-form-item>
      </n-form>

      <n-divider class="form-action-divider"/>

      <n-space vertical align="center" class="mt-3 additional-actions">
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
import {useAuthStore} from '@/stores/authStore';
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
  NP,
  NSpace,
  NText,
  useMessage
} from 'naive-ui';
import {PhonePortraitOutline as PhoneIcon} from '@vicons/ionicons5';

const authStore = useAuthStore();
const router = useRouter();
const message = useMessage();

const formRef = ref(null);
const registrationData = reactive({
  phone_number: '',
});
const successMessage = ref(''); // 保持，用於顯示註冊成功後的特定後端訊息

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
  authStore.clearRegisterError();
});


const handleRegister = () => {
  formRef.value?.validate(async (validationErrors) => {
    if (!validationErrors) {
      successMessage.value = '';

      // 確保 payload 與 authStore.register action 期望的一致
      // 根據您之前的 store action 註釋，它期望 { phone_number: '...' }
      const payload = {
        phone_number: registrationData.phone_number,
      };
      // 如果您的 store action 期望 { username: '...' }，則用下面這個
      // const payload = { username: registrationData.phone_number };

      const registrationResult = await authStore.register(payload); // register action 應返回包含成功狀態和消息的對象

      if (registrationResult && registrationResult.success) {
        // 註冊成功後的跳轉等邏輯已在 authStore.register 中處理
        // (例如 router.push('/') 和 alert(initial_password_info))
        // 如果 store action 返回了 initial_password_info，可以在這裡用 successMessage 顯示
        if (registrationResult.initial_password_info) {
          successMessage.value = registrationResult.initial_password_info + " 請妥善保管並盡快登入修改。";
        } else {
          // 也可以在這裡用 Naive UI message 提示
          // message.success("註冊成功並已自動登入！");
        }
      }
      // 註冊失敗的錯誤訊息由 authStore.status.registerError 在模板的 n-alert 中顯示
    } else {
      message.error('請修正表單中的錯誤。');
    }
  });
};
</script>

<style scoped>
.quick-register-page-naive {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - var(--header-height, 64px) - var(--footer-height, 67px)); /* 確保CSS變數已定義或替換為實際值 */
  padding: 20px;
  background-color: var(--n-body-color); /* Naive UI body 背景色 */
  box-sizing: border-box;
}

.register-card.n-card {
  max-width: 400px; /* 與登入頁面卡片寬度一致 */
  width: 100%;
  border-radius: var(--n-border-radius);
  box-shadow: var(--n-box-shadow2);
  background-color: var(--n-card-color);
  padding: 15px 10px; /* 調整卡片自身的 padding */
}

/* 卡片標題 */
.register-card .card-title-naive.n-h2 {
  font-weight: 600;
  color: var(--n-title-text-color);
  margin-bottom: 0.75rem; /* 標題與下方副標題的間距 */
}

/* 卡片副標題/說明文字 */
.register-card .card-subtitle-naive.n-p { /* 針對 n-p 元素 */
  color: var(--n-text-color-3); /* Naive UI 輔助文字顏色 */
  font-size: 0.9em;
  line-height: 1.6;
  margin-bottom: 1.75rem !important; /* 副標題與表單的間距 */
}

/* 表單 */
.register-form.n-form {
  /* 可在此處為整個表單添加特定樣式 */
}

/* 表單項 */
.register-form .n-form-item {
  margin-bottom: var(--n-form-item-margin-bottom, 24px);
}

/* 最後一個表單項（按鈕）可能不需要那麼大的底部間距 */
.register-form .submit-button-form-item.n-form-item {
  margin-bottom: 0;
}

/* Alert 間距 */
.form-alert.n-alert { /* 使用 form-alert class 統一 alert 間距 */
  margin-bottom: var(--n-form-item-margin-bottom, 24px) !important;
}


/* 註冊按鈕 */
.main-submit-button.n-button { /* .register-button 已改名為 .main-submit-button */
  font-weight: 500;
  /* size="large" 已設定高度和大部分樣式 */
}

/* 分隔線 */
.form-action-divider.n-divider:not(.n-divider--vertical) { /* 使用 form-action-divider class */
  margin-top: 1.8rem;
  margin-bottom: 1.2rem;
}

/* "已經有帳號了？" 區域 */
.additional-actions.n-space .n-text {
  color: var(--n-text-color-2);
}

.additional-actions.n-space .n-button { /* 針對 text button */
  font-weight: 500;
}
</style>