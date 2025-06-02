<template>
  <n-card title="修改密碼" :bordered="false" class="change-password-card shadow-sm">

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
import {NAlert, NButton, NCard, NForm, NFormItem, NInput, useMessage} from 'naive-ui';

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
/* .change-password-card.n-card 已被父組件的 .form-section-card 樣式覆蓋，
   如果 form-section-card 的樣式是全局的或能正確作用於子組件的根 n-card，
   則這裡不需要太多重複的卡片樣式。 */

/* 如果 form-section-card 的 :deep() 樣式無法穿透到這裡的 n-card-header 和 n-card__content，
   您可能需要在这里也定义类似的样式，或者確保 form-section-card 的樣式定義在全局。
   假設父組件的 form-section-card 樣式能夠正確應用。 */

/* 微調表單項間距 */
.n-form-item {
  margin-bottom: 20px; /* 與其他表單統一，例如 EditProfileView */
}

.n-form-item:last-of-type { /* 最後一個表單項底部不需要那麼大間距，因為按鈕會有 mt-3 */
  margin-bottom: 12px;
}

/* 提交按鈕樣式 (確保與其他表單的提交按鈕風格一致) */
.form-submit-button.n-button { /* 與 EditProfileView.vue 中使用的 class 一致 */
  margin-top: 1.5rem; /* 與上方元素的間距 */
  height: var(--n-height-m); /* 使用 Naive UI 中等按鈕的高度，或 --n-height-l (大) */
  font-size: 0.95rem; /* 按鈕文字大小 */
  /* strong 屬性已在模板中 */
}
</style>