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

        <!-- 修正：移除對不存在的 successMessage 的依賴 -->
        <!-- 錯誤訊息現在由本地的 registerError ref 控制 -->
        <n-alert v-if="registerError" title="註冊失敗" type="error" closable class="mb-3 form-alert"
                 @close="registerError = null">
          {{ registerError }}
        </n-alert>

        <n-form-item :show-label="false" class="submit-button-form-item">
          <n-button
              type="primary"
              attr-type="submit"
              block
              strong
              size="large"
              :loading="registering"
              :disabled="registering"
              class="register-button main-submit-button"
          >
            {{ registering ? '註冊中...' : '確認註冊' }}
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
import {reactive, ref} from 'vue';
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
import apiClient from '@/services/apiClient';

const authStore = useAuthStore();
const router = useRouter();
const message = useMessage();

const formRef = ref(null);
const registering = ref(false);
const registerError = ref(null); // 組件本地的錯誤狀態

const registrationData = reactive({
  phone_number: '',
});

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

const handleRegister = () => {
  formRef.value?.validate(async (validationErrors) => {
    if (!validationErrors) {
      registering.value = true;
      registerError.value = null;
      try {
        // --- 修正：傳送的 payload 的鍵名必須是 phone_number (camelCase) ---
        const response = await apiClient.post('/auth/register', {
          phone_number: registrationData.phone_number
        });

        // 註冊成功後，不再自動登入，而是顯示成功訊息並引導至登入頁面
        message.success(response.data.message || "註冊成功！請前往登入頁面。", {duration: 5000});

        // 跳轉到登入頁面
        await router.push({name: 'Leaderboard'});

      } catch (error) {
        // 將後端返回的錯誤訊息顯示在 alert 中
        const errorData = error.response?.data;
        if (errorData && errorData.details) {
          // 處理來自 Marshmallow 的詳細驗證錯誤
          registerError.value = `輸入數據有誤: ${Object.values(errorData.details).flat().join(' ')}`;
        } else {
          registerError.value = errorData?.message || '註冊失敗，請稍後再試。';
        }
      } finally {
        registering.value = false;
      }
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