<template>
  <n-card title="修改密碼" :bordered="false" class="change-password-card shadow-sm">
    <template #header-extra>
      <n-icon :component="KeyIcon" size="20"/>
    </template>

    <n-alert
        v-if="message"
        :title="status === 'success' ? '操作成功' : '操作失敗'"
        :type="status === 'success' ? 'success' : 'error'"
        closable
        class="mb-4"
        @close="clearMessage"
    >
      <span style="white-space: pre-wrap;">{{ message }}</span>
    </n-alert>

    <n-form
        ref="formRef"
        :model="passwords"
        :rules="formRules"
        label-placement="top"
        require-mark-placement="right-hanging"
        @submit.prevent="handleChangePassword"
    >
      <n-form-item label="目前密碼*" path="old_password">
        <n-input
            type="password"
            v-model:value="passwords.old_password"
            placeholder="請輸入您目前的密碼"
            show-password-on="click"
            clearable
            @keydown.enter.prevent="handleChangePassword"
        />
      </n-form-item>
      <n-form-item label="新密碼*" path="new_password">
        <n-input
            type="password"
            v-model:value="passwords.new_password"
            placeholder="請輸入新密碼 (至少6位)"
            show-password-on="click"
            clearable
            @keydown.enter.prevent="handleChangePassword"
        />
      </n-form-item>
      <n-form-item label="確認新密碼*" path="confirm_new_password">
        <n-input
            type="password"
            v-model:value="passwords.confirm_new_password"
            placeholder="再次輸入新密碼"
            show-password-on="click"
            clearable
            :status="passwords.new_password && passwords.confirm_new_password && passwords.new_password !== passwords.confirm_new_password ? 'error' : undefined"
            @keydown.enter.prevent="handleChangePassword"
        />
        <template #feedback
                  v-if="passwords.new_password && passwords.confirm_new_password && passwords.new_password !== passwords.confirm_new_password">
          新密碼與確認新密碼不一致！
        </template>
      </n-form-item>

      <n-button
          type="warning"
          attr-type="submit"
          block
          strong
          :loading="submitting"
          :disabled="submitting"
          class="mt-3"
      >
        {{ submitting ? '處理中...' : '確認修改密碼' }}
      </n-button>
    </n-form>
  </n-card>
</template>

<script setup>
import {defineEmits, reactive, ref} from 'vue';
import apiClient from '@/services/apiClient'; // 確保路徑正確
import {NAlert, NButton, NCard, NForm, NFormItem, NIcon, NInput, useMessage} from 'naive-ui';
import {KeyOutline as KeyIcon} from '@vicons/ionicons5';

const messageApi = useMessage(); // Naive UI message API

const formRef = ref(null); // Ref for NForm instance
const passwords = reactive({
  old_password: '',
  new_password: '',
  confirm_new_password: ''
});

const submitting = ref(false);
const message = ref(''); // 用於 n-alert 的訊息
const status = ref('');  // 'success' or 'error', 用於 n-alert 的 type

const emit = defineEmits(['password-changed-status']);

function clearMessage() {
  message.value = '';
  status.value = '';
}

// Naive UI 表單驗證規則
const formRules = {
  old_password: [
    {required: true, message: '目前密碼為必填', trigger: ['input', 'blur']}
  ],
  new_password: [
    {required: true, message: '新密碼為必填', trigger: ['input', 'blur']},
    {min: 6, message: '新密碼長度至少需要6位', trigger: ['input', 'blur']}
  ],
  confirm_new_password: [
    {required: true, message: '確認新密碼為必填', trigger: ['input', 'blur']},
    {
      validator: (rule, value) => {
        if (value !== passwords.new_password) {
          return new Error('新密碼與確認新密碼不一致');
        }
        return true;
      },
      trigger: ['input', 'blur'] // 也在 new_password 輸入時觸發 (如果需要，通常 blur 就夠了)
    }
  ]
};


const handleChangePassword = () => {
  formRef.value?.validate(async (validationErrors) => {
    if (!validationErrors) {
      clearMessage(); // 清除之前的 n-alert 訊息
      submitting.value = true;
      try {
        const response = await apiClient.post('/auth/change-password', {
          old_password: passwords.old_password,
          new_password: passwords.new_password
        });

        messageApi.success(response.data.msg || '密碼已成功修改！'); // 使用 Naive UI 全局 message
        emit('password-changed-status', response.data.msg || '密碼已成功修改！', 'success');

        // 清空表單
        passwords.old_password = '';
        passwords.new_password = '';
        passwords.confirm_new_password = '';
        // 可以在父組件決定是否強制登出或提示重新登入
      } catch (err) {
        const errorMsg = err.response?.data?.msg || '修改密碼失敗，請檢查輸入。';
        messageApi.error(errorMsg);
        emit('password-changed-status', errorMsg, 'error');
        console.error("Error changing password:", err.response || err);
      } finally {
        submitting.value = false;
      }
    } else {
      messageApi.error('請修正表單中的紅色提示錯誤。');
      console.log('Change password form validation errors:', validationErrors);
    }
  });
};
</script>

<style scoped>
.change-password-card.n-card {
  /* 您可以為這個卡片添加特定樣式 */
  /* 例如，如果父組件 EditProfileView 使用了 grid，這裡的 card 可以自適應 */
}

.n-card > .n-card-header .n-card-header__main { /* 調整卡片標題字重 (如果需要) */
  font-weight: 600;
}

.n-form-item {
  margin-bottom: 18px; /* 調整表單項間距 */
}

.n-button[block] {
  /* 大按鈕的樣式 */
}

/* 密碼可見性切換按鈕 (show-password-on="click" 已由 Naive UI Input 處理) */
/* 如果需要自訂圖示，Naive UI Input 的 password-visible-icon 和 password-invisible-icon 插槽可用 */
</style>