<template>
  <div class="edit-profile-page container-fluid mt-4 mb-5 px-md-4">
    <n-h1 align="center" class="page-main-title mb-4">
      <n-icon :component="SettingsIcon" size="30" class="title-icon" />
      帳號與個人資料設定
    </n-h1>

    <div v-if="loading" class="text-center my-5">
      <n-spin size="large" />
    </div>
    <n-alert
      v-if="fetchError"
      title="載入錯誤"
      type="error"
      closable
      class="mb-4"
      @close="fetchError = null"
    >
      {{ fetchError }}
    </n-alert>

    <n-grid
      v-if="!loading && !fetchError && profileData"
      x-gap="24"
      y-gap="20"
      cols="1 s:2"
      item-responsive
      responsive="screen"
    >
      <n-gi>
        <n-card title="基本及球員資料" :bordered="false" class="form-section-card">
          <n-form
            ref="profileFormRef"
            :model="editableProfile"
            :rules="profileFormRules"
            label-placement="top"
            @submit.prevent="handleProfileUpdate"
          >
            <!-- 用於顯示更新成功或失敗的訊息 -->
            <n-alert
              v-if="updateMessage"
              :title="updateStatus === 'success' ? '成功' : '更新失敗'"
              :type="updateStatus"
              closable
              class="mb-4"
              @close="clearUpdateMessage"
            >
              <span style="white-space: pre-wrap">{{ updateMessage }}</span>
            </n-alert>

            <!-- 帳號資訊區塊 -->
            <n-h6 class="form-section-subtitle">帳號資訊</n-h6>
            <n-form-item label="登入帳號 (手機號碼)">
              <n-input :value="profileData.username" readonly disabled />
            </n-form-item>
            <n-form-item label="電子郵件" path="email">
              <n-input
                v-model:value="editableProfile.email"
                placeholder="example@example.com"
                clearable
              />
            </n-form-item>
            <n-form-item label="顯示暱稱" path="display_name">
              <n-input
                v-model:value="editableProfile.display_name"
                placeholder="您希望在網站上顯示的名稱"
              />
            </n-form-item>

            <!-- 球員資料區塊 (僅當有關聯的 member_profile 時顯示) -->
            <template v-if="profileData.member_profile">
              <n-h6 class="form-section-subtitle">球員資料</n-h6>
              <n-form-item label="真實姓名">
                <n-input v-model:value="editableProfile.name" placeholder="真實姓名" />
              </n-form-item>
              <n-form-item label="學號">
                <n-input v-model:value="editableProfile.student_id" placeholder="學號" />
              </n-form-item>

              <n-grid :x-gap="16" :cols="2">
                <n-form-item-gi label="性別" path="gender">
                  <n-select
                    v-model:value="editableProfile.gender"
                    :options="genderOptions"
                    placeholder="選擇性別"
                    clearable
                  />
                </n-form-item-gi>
                <n-form-item-gi label="習慣位置" path="position">
                  <n-select
                    v-model:value="editableProfile.position"
                    :options="positionOptions"
                    placeholder="選擇位置"
                    clearable
                  />
                </n-form-item-gi>
              </n-grid>

              <n-form-item label="所屬組織" path="organization_id">
                <n-select
                  v-model:value="editableProfile.organization_id"
                  :options="organizationOptions"
                  placeholder="選擇組織"
                  clearable
                  filterable
                />
              </n-form-item>
            </template>

            <n-button type="primary" attr-type="submit" :loading="saving" strong block class="mt-4">
              {{ saving ? '儲存中...' : '儲存變更' }}
            </n-button>
          </n-form>
        </n-card>
      </n-gi>

      <n-gi>
        <!-- 密碼修改組件可以保持不變 -->
        <ChangePasswordForm
          class="form-section-card"
          @password-changed-status="handlePasswordChangedStatusMessage"
        />
      </n-gi>
    </n-grid>

    <div v-else-if="!loading && !fetchError && !profileData.member_profile" class="mt-4">
      <n-alert title="提示" type="info">
        您的帳號尚未關聯球隊成員資料，部分個人資料功能可能不可用。請聯繫管理員。
      </n-alert>
    </div>
  </div>
</template>

<script setup>
  import { onMounted, reactive, ref } from 'vue'
  import { useAuthStore } from '@/stores/authStore'
  import { useRouter } from 'vue-router'
  import apiClient from '@/services/apiClient'
  import ChangePasswordForm from '@/components/auth/ChangePasswordForm.vue'
  import {
    NAlert,
    NButton,
    NCard,
    NForm,
    NFormItem,
    NFormItemGi,
    NGi,
    NGrid,
    NH1,
    NH6,
    NIcon,
    NInput,
    NSelect,
    NSpin,
    useMessage
  } from 'naive-ui'
  import { SettingsOutline as SettingsIcon } from '@vicons/ionicons5'

  const authStore = useAuthStore()
  const router = useRouter()
  const message = useMessage()

  // --- 狀態 ---
  const loading = ref(true)
  const saving = ref(false)
  const fetchError = ref(null)
  const updateMessage = ref('')
  const updateStatus = ref('') // 'success' or 'error'

  const profileFormRef = ref(null)

  // 顯示用資料 (從 API 獲取)
  const profileData = ref(null)

  // 表單綁定用資料 (只包含使用者可編輯的欄位)
  const editableProfile = reactive({
    email: '',
    display_name: '',
    gender: null,
    position: null,
    organization_id: null
  })

  // 下拉選單選項
  const organizationOptions = ref([])
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

  // 表單驗證規則
  const profileFormRules = {
    email: [{ type: 'email', message: '請輸入有效的電子郵件格式', trigger: ['input', 'blur'] }],
    display_name: [{ required: true, message: '顯示暱稱為必填', trigger: ['input', 'blur'] }]
  }

  // --- 方法 ---

  // 將從 API 獲取的數據填充到表單中
  function populateForm(data) {
    if (!data) return
    profileData.value = data

    // 填充 User 相關的可編輯欄位
    editableProfile.email = data.email || ''
    editableProfile.display_name = data.display_name || ''

    // 填充 Member 相關的可編輯欄位
    if (data.member_profile) {
      editableProfile.name = data.member_profile.name || ''
      editableProfile.student_id = data.member_profile.student_id || ''

      // 確保 Select 的 v-model 在無效值時設為 null
      const validGender = genderOptions.some(opt => opt.value === data.member_profile.gender)
      editableProfile.gender = validGender ? data.member_profile.gender : null

      const validPosition = positionOptions.some(opt => opt.value === data.member_profile.position)
      editableProfile.position = validPosition ? data.member_profile.position : null

      editableProfile.organization_id =
        data.member_profile.organization?.id > 0 ? data.member_profile.organization.id : null
    }
  }

  // 獲取個人資料
  async function fetchProfileData() {
    loading.value = true
    fetchError.value = null
    try {
      const response = await apiClient.get('/profile/me')
      // 直接將後端回傳的 user 物件傳遞給 populateForm
      populateForm(response.data)
    } catch (err) {
      fetchError.value = err.response?.data?.message || '無法載入個人資料'
      console.error('Error fetching profile:', err.response || err)
    } finally {
      loading.value = false
    }
  }

  // 獲取組織列表用於下拉選單
  async function fetchOrganizationOptions() {
    try {
      const response = await apiClient.get('/organizations')
      organizationOptions.value = response.data.map(org => ({
        label: org.name,
        value: org.id
      }))
    } catch (_error) {
      message.error('載入組織列表失敗')
    }
  }

  // 處理個人資料更新
  const handleProfileUpdate = async () => {
    profileFormRef.value?.validate(async validationErrors => {
      if (!validationErrors) {
        saving.value = true
        clearUpdateMessage()

        try {
          const response = await apiClient.put('/profile/me', editableProfile)
          updateStatus.value = 'success'
          updateMessage.value = response.data.message || '個人資料已成功更新！'
          message.success(updateMessage.value)

          // 更新 Pinia store 和本地顯示數據
          const updatedProfile = response.data.profile
          authStore.user = updatedProfile // 更新 store 中的 user 物件
          localStorage.setItem('user', JSON.stringify(updatedProfile))
          populateForm(updatedProfile) // 用更新後的數據重新填充表單
        } catch (err) {
          updateStatus.value = 'error'
          updateMessage.value = err.response?.data?.message || '更新失敗，請稍後再試。'
          message.error(updateMessage.value)
          console.error('Error updating profile:', err.response || err)
        } finally {
          saving.value = false
        }
      }
    })
  }

  // --- 生命週期鉤子 ---
  onMounted(() => {
    if (authStore.isAuthenticated) {
      fetchProfileData()
      fetchOrganizationOptions()
    } else {
      // 如果未認證，直接導向登入頁面
      router.push({ name: 'Login', query: { unauthorized: 'true' } })
    }
  })

  // --- 其他輔助函數 ---
  function clearUpdateMessage() {
    updateMessage.value = ''
    updateStatus.value = ''
  }

  function handlePasswordChangedStatusMessage(msg, status) {
    updateMessage.value = msg
    updateStatus.value = status
  }
</script>

<style scoped>
  .edit-profile-page {
    max-width: 1000px;
    margin: 2rem auto 3rem auto; /* 統一頁面上下外邊距 */
  }

  .page-main-title.n-h1 {
    font-weight: 600;
    color: var(--n-title-text-color); /* Naive UI 標題文字顏色 */
    /* display: flex; align-items: center; */ /* 如果標題內有返回按鈕可以啟用 */
  }

  .title-icon {
    color: var(--n-primary-color);
    margin-right: 10px;
    vertical-align: -4px;
  }

  .form-section-card.n-card {
    margin-top: 0; /* grid 的 y-gap 會處理間距 */
    border-radius: var(--n-border-radius);
    box-shadow: var(--n-box-shadow2); /* Naive UI 二級陰影 */
    background-color: var(--n-card-color);
    height: 100%; /* 如果希望左右兩欄卡片等高 */
  }

  /* 覆蓋 Naive UI Card 預設的 header 和 content padding 以實現更細緻的控制 */
  .form-section-card :deep(.n-card-header) {
    padding-top: 16px; /* 調整標題區域的上padding */
    padding-bottom: 12px; /* 標題和內容之間的padding */
    padding-left: 20px;
    padding-right: 20px;
    font-size: 1.2rem; /* 標題字體略大 */
    font-weight: 600;
  }

  .form-section-card :deep(.n-card__content) {
    padding: 0 20px 20px 20px; /* 內容區域的padding，頂部padding已由header的padding-bottom控制 */
  }

  /* 表單內子標題 */
  .form-section-subtitle.n-h6 {
    font-weight: 600;
    margin-top: 1.5rem;
    margin-bottom: 1rem;
    color: var(--n-primary-color);
    /* border-bottom: 1px solid var(--n-divider-color); */ /* 考慮移除邊框，讓 n-divider 組件處理 */
    /* padding-bottom: 0.5rem; */
    font-size: 1.05em;
  }

  .form-section-subtitle:first-of-type {
    margin-top: 0.5rem; /* 第一個子標題與卡片標題的間距 */
  }

  /* 表單中使用的 n-divider */
  .section-divider-form.n-divider:not(.n-divider--vertical) {
    margin-top: 1.75rem; /* 調整分隔線的上下間距 */
    margin-bottom: 0.25rem; /* 與下方子標題的間距更緊湊 */
  }

  /* 表單項標籤 */
  .n-form-item :deep(.n-form-item-label) {
    font-weight: 500 !important;
    color: var(--n-text-color-2) !important; /* 使用 Naive UI 次要文字顏色 */
    padding-bottom: 6px !important; /* 標籤和輸入框之間的距離 */
  }

  /* 表單底部提交按鈕 */
  .form-submit-button.n-button {
    margin-top: 1.5rem;
    /* height: var(--n-height-l); */ /* 改用 Naive UI 按鈕的 size prop 來控制高度 */
    /* font-size: 1rem; */ /* Naive UI Button size prop 會影響字體大小 */
    /* 使用 Naive UI 的 size="large" prop 可以達到類似效果 */
  }

  /* 為了讓 strong block 按鈕更好看，可以微調 */
  .n-button--block.n-button--strong {
    font-weight: 500;
  }

  /* 確保 n-grid 的 y-gap 生效，如果 form-item 有自己的 margin-bottom，可能會導致雙倍間距 */
  /* Naive UI n-form-item 預設的 margin-bottom 在 n-grid 中通常能良好配合 y-gap */
  /* 如果需要微調，可以針對性地調整 n-form-item 的 margin */
  .n-form .n-form-item {
    /* 更精確的選擇器 */
    margin-bottom: var(--n-form-item-margin-bottom, 20px); /* 使用 Naive UI 變數或自訂值 */
  }

  .n-grid .n-form-item {
    /* 在 grid 內的 form-item，可能不需要底部 margin，由 grid gap 控制 */
    margin-bottom: 0;
  }

  /* 針對 read-only input 的樣式，使其看起來更像純文字 (可選) */
  .n-input.n-input--disabled :deep(input),
  .n-input.n-input--readonly :deep(input) {
    color: var(--n-text-color-base) !important;
    cursor: default !important;
    background-color: var(
      --n-color-disabled
    ) !important; /* 使用disabled背景色使其看起來不可編輯但仍清晰 */
    border-color: var(--n-border-color) !important; /* 保持與普通輸入框相似的邊框 */
    opacity: 1 !important; /* 確保文字清晰 */
  }

  /* 如果您不希望 disabled input 有明顯的背景色，可以設為 transparent 或 card color */
  /* .n-input.n-input--disabled :deep(input) { background-color: transparent !important; } */
</style>
