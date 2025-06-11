<template>
  <div class="login-page-naive">
    <n-card :bordered="false" class="login-card">
      <n-h2 align="center" class="card-title-naive">登入系統</n-h2>

      <n-alert
        v-if="loginRouteMessage"
        title="提示"
        type="info"
        closable
        class="mb-4 login-alert"
        @close="loginRouteMessage = ''"
      >
        {{ loginRouteMessage }}
      </n-alert>

      <n-form
        ref="formRef"
        :model="credentials"
        :rules="formRules"
        label-placement="top"
        require-mark-placement="right-hanging"
        class="login-form"
        @submit.prevent="handleLogin"
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
              <n-icon :component="PhoneIcon" />
            </template>
          </n-input>
        </n-form-item>

        <n-form-item path="password" label="密碼">
          <n-input
            v-model:value="credentials.password"
            type="password"
            show-password-on="click"
            placeholder="請輸入密碼"
            size="large"
            clearable
            @keydown.enter.prevent="handleLogin"
          >
            <template #prefix>
              <n-icon :component="LockIcon" />
            </template>
          </n-input>
        </n-form-item>

        <n-alert
          v-if="authStore.status.loginError"
          title="登入失敗"
          type="error"
          closable
          class="mb-3 login-alert"
          @close="authStore.status.loginError = null"
        >
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

      <n-divider class="login-divider" />

      <n-space vertical align="center" class="mt-3 additional-actions">
        <n-text>
          還沒有帳號？
          <router-link v-slot="{ navigate }" :to="{ name: 'Register' }">
            <n-button text type="primary" @click="navigate">立即快速註冊</n-button>
          </router-link>
        </n-text>
      </n-space>
    </n-card>
  </div>
</template>

<script setup>
  import { onMounted, reactive, ref } from 'vue'
  import { useAuthStore } from '@/stores/authStore' // 確保路徑正確
  import { useRoute, useRouter } from 'vue-router'
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
  } from 'naive-ui'
  import { KeyOutline as LockIcon, PhonePortraitOutline as PhoneIcon } from '@vicons/ionicons5'
  import '@/assets/css/login.css'

  const authStore = useAuthStore()
  const router = useRouter()
  const route = useRoute()
  const message = useMessage() // Naive UI message API

  const formRef = ref(null) // Ref for NForm instance
  const credentials = reactive({
    username: '',
    password: ''
  })

  const loginRouteMessage = ref('')

  // Naive UI 表單驗證規則
  const formRules = {
    username: [
      { required: true, message: '手機號碼為必填', trigger: ['input', 'blur'] },
      {
        pattern: /^09\d{8}$/,
        message: '手機號碼格式不正確 (應為09開頭10位數字)',
        trigger: ['input', 'blur']
      }
    ],
    password: [
      { required: true, message: '密碼為必填', trigger: ['input', 'blur'] },
      { min: 6, message: '密碼長度至少需要6位', trigger: ['input', 'blur'] } // 可選的最小長度驗證
    ]
  }

  onMounted(() => {
    authStore.status.loginError = null
    if (route.query.loggedOut === 'true') {
      loginRouteMessage.value = '您已成功登出。'
      router.replace({ query: {} })
    } else if (route.query.sessionExpired === 'true') {
      loginRouteMessage.value = '您的登入已過期或無效，請重新登入。'
      router.replace({ query: {} })
    } else if (route.query.unauthorized === 'true' || route.query.redirect) {
      loginRouteMessage.value = '您需要登入才能訪問該頁面。'
      const query = { ...route.query }
      delete query.unauthorized
      router.replace({ query })
    }
  })

  const handleLogin = () => {
    formRef.value?.validate(async validationErrors => {
      if (!validationErrors) {
        // 表單驗證通過，執行登入
        const success = await authStore.login(credentials)
        if (success) {
          const redirectPath = route.query.redirect || '/'
          router.push(redirectPath)
        }
        // 失敗的錯誤訊息由 authStore.status.loginError 在模板中顯示
      } else {
        // Naive UI 會自動在表單項旁邊顯示錯誤，這裡可以選擇性地用 message API 提示
        message.error('請修正表單中的錯誤。')
        console.log('Login form validation errors:', validationErrors)
      }
    })
  }
</script>

<style scoped></style>
