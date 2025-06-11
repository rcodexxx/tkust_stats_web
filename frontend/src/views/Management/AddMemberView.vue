<template>
  <div class="admin-add-member-page container mt-4 mb-5 px-md-4">
    <n-h1 class="page-main-title">
      <n-button text class="me-2 title-back-button" @click="goBack">
        <template #icon>
          <n-icon :component="ArrowBackIcon" />
        </template>
      </n-button>
      新增球隊成員及帳號
    </n-h1>

    <n-card :bordered="false" class="form-card">
      <n-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-placement="top"
        @submit.prevent="handleAddMember"
      >
        <n-alert
          v-if="submitMessage"
          title="新增失敗"
          type="error"
          closable
          class="mb-4"
          @close="clearSubmitMessage"
        >
          <span style="white-space: pre-wrap">{{ submitMessage }}</span>
        </n-alert>

        <n-grid :x-gap="24" :y-gap="12" :cols="12" item-responsive>
          <n-form-item-gi :span="12" label="真實姓名*" path="name">
            <n-input v-model:value="formData.name" placeholder="請輸入成員的真實姓名" />
          </n-form-item-gi>
          <n-form-item-gi :span="12" label="顯示名稱/綽號" path="display_name">
            <n-input
              v-model:value="formData.display_name"
              placeholder="排行榜上顯示的名稱 (預設同真實姓名)"
            />
          </n-form-item-gi>

          <n-gi :span="12">
            <n-divider title-placement="left" class="section-divider">登入帳號資訊</n-divider>
          </n-gi>
          <n-form-item-gi :span="12" :md="6" label="手機號碼 (登入帳號)*" path="username">
            <n-input v-model:value="formData.username" placeholder="09xxxxxxxx (用於登入)" />
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="初始密碼" path="password">
            <n-input
              v-model:value="formData.password"
              type="password"
              placeholder="可選，預設為手機號碼"
              show-password-on="click"
            />
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="電子郵件" path="email">
            <n-input v-model:value="formData.email" placeholder="example@example.com (可選)" />
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="角色*" path="role">
            <n-select v-model:value="formData.role" :options="roleOptions" placeholder="選擇角色" />
          </n-form-item-gi>

          <n-gi :span="12">
            <n-divider title-placement="left" class="section-divider">球員詳細資料</n-divider>
          </n-gi>
          <n-form-item-gi :span="12" :md="6" label="學號" path="student_id">
            <n-input v-model:value="formData.student_id" placeholder="選填" />
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="性別" path="gender">
            <n-select
              v-model:value="formData.gender"
              :options="genderOptions"
              placeholder="選擇性別"
              clearable
            />
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="習慣位置" path="position">
            <n-select
              v-model:value="formData.position"
              :options="positionOptions"
              placeholder="選擇位置"
              clearable
            />
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="所屬組織" path="organization_id">
            <n-select
              v-model:value="formData.organization_id"
              :options="organizationOptions"
              placeholder="選擇組織"
              clearable
              filterable
            />
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="入隊日期" path="joined_date_ts">
            <n-date-picker
              v-model:value="formData.joined_date_ts"
              type="date"
              clearable
              style="width: 100%"
            />
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="6" label="活躍狀態">
            <div class="switch-with-label">
              <n-switch v-model:value="formData.is_active" />
              <span class="switch-label-text">{{ formData.is_active ? '現役' : '非現役' }}</span>
            </div>
          </n-form-item-gi>
          <n-form-item-gi :span="12" label="備註" path="notes">
            <n-input
              v-model:value="formData.notes"
              type="textarea"
              placeholder="選填"
              :autosize="{ minRows: 2, maxRows: 4 }"
            />
          </n-form-item-gi>
        </n-grid>

        <n-space justify="end" class="mt-4 action-buttons">
          <n-button size="medium" @click="goBack">取消</n-button>
          <n-button type="primary" attr-type="submit" :loading="submitting" size="medium" strong>
            {{ submitting ? '新增中...' : '確認新增' }}
          </n-button>
        </n-space>
      </n-form>
    </n-card>
  </div>
</template>

<script setup>
  import { onMounted, reactive, ref } from 'vue'
  import { useRouter } from 'vue-router'
  import {
    NAlert,
    NButton,
    NCard,
    NDatePicker,
    NDivider,
    NForm,
    NFormItemGi,
    NGi,
    NGrid,
    NH1,
    NIcon,
    NInput,
    NSelect,
    NSpace,
    NSwitch,
    useMessage
  } from 'naive-ui'
  import { ArrowBackOutline as ArrowBackIcon } from '@vicons/ionicons5'
  import apiClient from '@/services/apiClient'

  // --- Hooks ---
  const router = useRouter()
  const message = useMessage()
  const formRef = ref(null)

  // --- 狀態管理 (State) ---
  const submitting = ref(false)
  const submitMessage = ref('')

  const formData = reactive({
    name: '',
    display_name: '',
    username: '',
    password: '',
    email: '',
    role: 'member',
    student_id: '',
    gender: null,
    position: null,
    organization_id: null,
    is_active: true,
    joined_date_ts: null,
    notes: ''
  })

  // --- 選項與規則 ---
  const organizationOptions = ref([])
  const roleOptions = [
    { label: '隊員', value: 'member' },
    { label: '幹部', value: 'cadre' },
    { label: '教練', value: 'coach' }
  ] // 移除了 'admin' 選項
  const genderOptions = [
    { label: '男性', value: 'male' },
    { label: '女性', value: 'female' }
  ]
  const positionOptions = [
    { label: '後排', value: 'back' },
    { label: '前排', value: 'front' },
    {
      label: '皆可',
      value: 'versatile'
    }
  ]

  const formRules = {
    name: [{ required: true, message: '真實姓名為必填', trigger: ['blur', 'input'] }],
    username: [
      { required: true, message: '手機號碼為必填', trigger: ['blur', 'input'] },
      { pattern: /^09\d{8}$/, message: '手機號碼格式不正確', trigger: ['blur', 'input'] }
    ],
    email: [{ type: 'email', message: '請輸入有效的電子郵件格式', trigger: ['blur', 'input'] }],
    password: [
      {
        required: false,
        trigger: ['blur', 'input'],
        validator: (rule, value) => {
          if (value && value.length < 6) return new Error('密碼長度至少需要6位')
          return true
        }
      }
    ],
    student_id: [
      {
        required: false,
        trigger: ['blur', 'input'],
        validator: (rule, value) => {
          if (value && !/^\d{7,9}$/.test(value)) return new Error('學號必須是7到9位數字')
          return true
        }
      }
    ],
    role: [{ required: true, message: '角色為必填', trigger: ['change'] }]
  }

  // --- 方法 ---
  async function fetchOrganizationOptions() {
    try {
      const response = await apiClient.get('/organizations')
      organizationOptions.value = response.data.map(org => ({ label: org.name, value: org.id }))
    } catch (_error) {
      message.error('載入組織列表失敗')
    }
  }

  const handleAddMember = () => {
    formRef.value?.validate(async validationErrors => {
      if (validationErrors) {
        message.error('請檢查表單，修正錯誤後再提交。')
        return
      }
      submitting.value = true
      clearSubmitMessage()

      const formatDate = timestamp => {
        if (!timestamp) return null
        const date = new Date(timestamp)
        return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
      }

      const payload = {
        name: formData.name,
        display_name: formData.display_name || formData.name,
        username: formData.username,
        password: formData.password || null,
        email: formData.email || null,
        role: formData.role,
        student_id: formData.student_id || null,
        gender: formData.gender,
        position: formData.position,
        organization_id: formData.organization_id,
        is_active: formData.is_active,
        notes: formData.notes,
        joined_date: formatDate(formData.joined_date_ts)
      }

      try {
        // 呼叫後端的 /members 端點來創建成員
        const response = await apiClient.post('/members', payload)
        message.success(response.data.message || '成員已成功新增！')
        await router.push({ name: 'ManagementCenter' })
      } catch (err) {
        const errorData = err.response?.data
        if (errorData?.details) {
          submitMessage.value =
            '新增失敗，請檢查以下欄位：\n' + Object.values(errorData.details).flat().join('\n')
        } else {
          submitMessage.value = errorData?.message || '新增成員時發生未預期錯誤。'
        }
      } finally {
        submitting.value = false
      }
    })
  }

  // --- 生命週期鉤子 ---
  onMounted(fetchOrganizationOptions)

  // --- 輔助函數 ---
  function clearSubmitMessage() {
    submitMessage.value = ''
  }

  function goBack() {
    router.push({ name: 'ManagementCenter' })
  }
</script>

<style scoped>
  .admin-add-member-page {
    max-width: 800px; /* 與編輯頁面一致或您希望的寬度 */
    margin: 2rem auto 3rem auto; /* 統一頁面上下外邊距 */
    /* background-color: var(--n-body-color); /* 頁面背景色，通常由App.vue或全局設定 */
  }

  /* 與 RecordMatchView.vue 和 ManagementCenterView.vue 類似的標題樣式 */
  .page-main-title {
    font-weight: 600;
    color: var(--n-title-text-color); /* Naive UI 標題文字顏色 */
    display: flex; /* 為了讓返回按鈕和文字垂直對齊 */
    align-items: center;
  }

  .title-back-button.n-button {
    /* 返回按鈕樣式 */
    margin-right: 12px; /* 圖標和文字間距 */
    font-size: 1.5rem; /* 調整返回按鈕圖標大小 */
  }

  .title-back-button.n-button .n-icon {
    color: var(--n-text-color-base); /* Naive UI 基本文字顏色 */
  }

  /* 與 RecordMatchView.vue 類似的卡片樣式 */
  .form-card.n-card {
    margin-top: 1.5rem;
    border-radius: var(--n-border-radius); /* Naive UI 圓角變數 */
    box-shadow: var(--n-box-shadow2); /* Naive UI 二級陰影 */
    background-color: var(--n-card-color); /* Naive UI 卡片背景色 */
    padding: 10px 15px; /* 可選：卡片內部微調padding */
  }

  /* 分隔線樣式 */
  .section-divider.n-divider:not(.n-divider--vertical) {
    margin-top: 1.5rem;
    margin-bottom: 1.25rem;
  }

  .section-divider.n-divider .n-divider__title {
    /* 分隔線標題樣式 */
    font-size: 0.95rem;
    font-weight: 500;
    color: var(--n-text-color-2);
  }

  /* Switch 和旁邊文字的對齊 */
  .switch-with-label {
    display: flex;
    align-items: center;
    gap: 8px; /* Switch 和文字之間的間距 */
    height: var(--n-height-m); /* 與其他表單組件高度對齊 (約34px) */
  }

  .switch-label-text {
    color: var(--n-text-color-3); /* 較淺的文字顏色 */
    font-size: 0.9em;
  }

  /* 統一按鈕區域樣式 */
  .action-buttons.n-space {
    padding-top: 0.5rem; /* 與上方元素的間距 */
  }

  .action-buttons .n-button {
    min-width: 100px; /* 按鈕最小寬度 */
    font-weight: 500;
  }
</style>
