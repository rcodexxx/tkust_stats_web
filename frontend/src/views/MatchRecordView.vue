<template>
  <div class="record-match-page container-fluid mt-4 mb-5 px-md-4">
    <n-h1 align="center" class="page-main-title mb-4">
      <n-icon :component="ClipboardIcon" size="32" class="title-icon"/>
      記錄校內排名賽結果
    </n-h1>

    <n-alert
        v-if="submitMessage"
        :title="submitStatus === 'success' ? '成功' : '錯誤'"
        :type="submitStatus === 'success' ? 'success' : 'error'"
        closable
        class="mb-4"
        @close="clearMessages"
    >
      <span style="white-space: pre-wrap;">{{ submitMessage }}</span>
    </n-alert>

    <n-card :bordered="false" class="form-card shadow-sm">
      <n-form
          ref="formRef"
          :model="matchForm"
          :rules="formRules"
          label-placement="top"
          require-mark-placement="right-hanging"
          @submit.prevent="handleRecordMatch"
      >
        <n-grid :x-gap="20" :y-gap="16" :cols="12" item-responsive>
          <n-form-item-gi :span="12" :md="4" label="比賽日期*" path="match_date">
            <n-date-picker
                v-model:formatted-value="matchForm.match_date"
                type="date"
                value-format="yyyy-MM-dd"
                placeholder="選擇比賽日期"
                style="width:100%"
            />
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="4" label="比賽類型*" path="match_type">
            <n-select
                v-model:value="matchForm.match_type"
                :options="matchTypeOptions"
                placeholder="選擇比賽類型"
            />
          </n-form-item-gi>
          <n-form-item-gi :span="12" :md="4" label="賽制" path="match_format">
            <n-select
                v-model:value="matchForm.match_format"
                :options="matchFormatOptions"
                placeholder="選擇賽制"
            />
          </n-form-item-gi>
        </n-grid>

        <n-divider style="margin-top: 1.5rem; margin-bottom: 1.5rem;"/>

        <n-grid :x-gap="24" :y-gap="16" :cols="12" item-responsive>
          {/* A 方隊伍 */}
          <n-gi :span="12" :lg="6" class="team-section team-a-section">
            <n-h5 class="team-title text-primary">
              <n-icon class="me-1"/>
              A 方隊伍
            </n-h5>
            <n-form-item label="A 方球員 1*" path="side_a_player1_id">
              <n-select
                  v-model:value="matchForm.side_a_player1_id"
                  :options="availableSideAPlayer1"
                  placeholder="選擇球員" filterable clearable
                  label-field="nameWithScore" value-field="id"
              />
            </n-form-item>
            <n-form-item v-if="matchForm.match_type === 'DOUBLES'" label="A 方球員 2*" path="side_a_player2_id">
              <n-select
                  v-model:value="matchForm.side_a_player2_id"
                  :options="availableSideAPlayer2"
                  placeholder="選擇球員" filterable clearable
                  label-field="nameWithScore" value-field="id"
              />
            </n-form-item>
            <n-form-item label="A 方局數/分數*" path="side_a_games_won">
              <n-input-number
                  v-model:value="matchForm.side_a_games_won"
                  :min="0" placeholder="輸入局數" style="width:100%"
              />
            </n-form-item>
          </n-gi>

          {/* B 方隊伍 */}
          <n-gi :span="12" :lg="6" class="team-section team-b-section">
            <n-h5 class="team-title text-error">
              <n-icon :component="PeopleIcon" class="me-1"/>
              B 方隊伍
            </n-h5>
            <n-form-item label="B 方球員 1*" path="side_b_player1_id">
              <n-select
                  v-model:value="matchForm.side_b_player1_id"
                  :options="availableSideBPlayer1"
                  placeholder="選擇球員" filterable clearable
                  label-field="nameWithScore" value-field="id"
              />
            </n-form-item>
            <n-form-item v-if="matchForm.match_type === 'DOUBLES'" label="B 方球員 2*" path="side_b_player2_id">
              <n-select
                  v-model:value="matchForm.side_b_player2_id"
                  :options="availableSideBPlayer2"
                  placeholder="選擇球員" filterable clearable
                  label-field="nameWithScore" value-field="id"
              />
            </n-form-item>
            <n-form-item label="B 方局數/分數*" path="side_b_games_won">
              <n-input-number
                  v-model:value="matchForm.side_b_games_won"
                  :min="0" placeholder="輸入局數" style="width:100%"
              />
            </n-form-item>
          </n-gi>
        </n-grid>

        <n-alert
            v-if="calculatedOutcomeDisplay"
            :title="calculatedOutcomeDisplay.includes('勝利') ? '預計結果' : '提示'"
            :type="getOutcomeAlertType(calculatedOutcomeDisplay)"
            class="mt-4 mb-3 fs-6 text-center"
            style="font-size: 1rem; font-weight: bold;"
            :show-icon="true"
        >
          {{ calculatedOutcomeDisplay }}
        </n-alert>

        <n-divider style="margin-top: 1.5rem; margin-bottom: 1.5rem;"/>


        <n-space justify="center" class="mt-4 action-buttons">
          <router-link to="/" v-slot="{ navigate }">
            <n-button @click="navigate" size="large" ghost>返回排行榜</n-button>
          </router-link>
          <n-button
              type="primary"
              attr-type="submit"
              strong
              size="large"
              :loading="submitting"
              :disabled="submitting || !matchForm.side_a_outcome"
          >
            <template #icon v-if="!submitting">
              <n-icon :component="SaveIcon"/>
            </template>
            {{ submitting ? '提交中...' : '儲存比賽結果' }}
          </n-button>
        </n-space>
      </n-form>
    </n-card>
  </div>
</template>

<script setup>
import {computed, onMounted, reactive, ref, watch} from 'vue';
import {useRouter} from 'vue-router';
import axios from 'axios'; // 或您的 apiClient
import {
  NAlert,
  NButton,
  NCard,
  NDatePicker,
  NDivider,
  NForm,
  NFormItem,
  NFormItemGi,
  NH1,
  NH5,
  NIcon,
  NInputNumber,
  NSelect,
  NSpace,
  useMessage
} from 'naive-ui';
import {
  ClipboardOutline as ClipboardIcon,
  PeopleOutline as PeopleIcon,
  SaveOutline as SaveIcon,
} from '@vicons/ionicons5';
// import '../assets/css/record-match-naive.css'; // 新的 CSS 檔案 (如果需要大量自訂)

const router = useRouter();
const message = useMessage(); // Naive UI message API
const allActiveMembers = ref([]);

const matchForm = reactive({
  match_date: new Date().toISOString().split('T')[0],
  match_type: 'DOUBLES',
  match_format: 'NINE_GAME_SET',
  side_a_player1_id: null, // 改為 null 以便 clearable
  side_a_player2_id: null,
  side_b_player1_id: null,
  side_b_player2_id: null,
  side_a_games_won: null,
  side_b_games_won: null,
  side_a_outcome: '',
  match_notes: ''
});

const submitting = ref(false);
const submitMessage = ref('');
const submitStatus = ref(''); // 'success' or 'error'
const calculatedOutcomeDisplay = ref('');
const formRef = ref(null); // Ref for NForm

const matchTypeOptions = [
  {label: '雙打', value: 'DOUBLES'},
  {label: '單打', value: 'SINGLES'}
];

const matchFormatOptions = ref([
  {
    label: '搶七 (先到7分勝2分)',  // 顯示給使用者的文字
    value: 'TIEBREAK',             // 實際綁定和提交的值
    // gamesToWin 和 needsTwoClear 可以保留，用於其他邏輯
    meta: {gamesToWin: 7, needsTwoClear: true}
  },
  {
    label: '五局制 (先贏3局)',
    value: 'FIVE_GAME_SET',
    meta: {gamesToWin: 3, needsTwoClear: false}
  },
  {
    label: '七局制 (先贏4局)',
    value: 'SEVEN_GAME_SET',
    meta: {gamesToWin: 4, needsTwoClear: false}
  },
  {
    label: '九局制 (先贏5局)',
    value: 'NINE_GAME_SET',
    meta: {gamesToWin: 5, needsTwoClear: false}
  },
  // 您可以根據需要增加更多賽制
]);

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

onMounted(async () => {
  try {
    const response = await axios.get(`${apiBaseUrl}/members`, {
      params: {all: 'false'} // 只獲取活躍成員 (假設後端 all=false 意指活躍)
    });
    allActiveMembers.value = response.data.map(m => ({
      ...m,
      nameWithScore: `${m.display_name || m.name} (${m.score})` // 為下拉選單準備顯示文字
    })) || [];
  } catch (error) { /* ... */
  }
  determineWinnerFrontend();
});

watch(() => matchForm.match_format, () => { /* ... (保持不變) ... */
});
watch(() => matchForm.match_type, (newType) => { /* ... (保持不變) ... */
});
watch([() => matchForm.side_a_games_won, () => matchForm.side_b_games_won],
    determineWinnerFrontend, {deep: false});

function determineWinnerFrontend() { /* ... (與之前版本邏輯幾乎相同) ... */
}

// 表單驗證規則 (Naive UI)
const formRules = {
  match_date: [{required: true, message: '比賽日期為必填', type: 'string', trigger: 'change'}],
  match_type: [{required: true, message: '比賽類型為必填', trigger: 'change'}],
  match_format: [{required: true, message: '賽制為必填', trigger: 'change'}],
  side_a_player1_id: [{required: true, message: 'A方球員1為必填', type: 'number', trigger: 'change'}],
  side_b_player1_id: [{required: true, message: 'B方球員1為必填', type: 'number', trigger: 'change'}],
  side_a_player2_id: [{
    validator: (rule, value) => {
      if (matchForm.match_type === 'DOUBLES' && !value) {
        return new Error('雙打模式下，A方球員2為必填');
      }
      return true;
    },
    trigger: 'change'
  }],
  side_b_player2_id: [{
    validator: (rule, value) => {
      if (matchForm.match_type === 'DOUBLES' && !value) {
        return new Error('雙打模式下，B方球員2為必填');
      }
      return true;
    },
    trigger: 'change'
  }],
  side_a_games_won: [
    {required: true, type: 'number', message: 'A方局數為必填', trigger: ['input', 'blur']},
    {type: 'number', min: 0, message: '局數不能為負', trigger: ['input', 'blur']}
  ],
  side_b_games_won: [
    {required: true, type: 'number', message: 'B方局數為必填', trigger: ['input', 'blur']},
    {type: 'number', min: 0, message: '局數不能為負', trigger: ['input', 'blur']}
  ],
};

async function handleRecordMatch() {
  formRef.value?.validate(async (validationErrors) => {
    if (!validationErrors) {
      clearMessages();
      // 前端邏輯驗證 (例如球員不重複等)
      let logicalErrors = [];
      const players = [
        matchForm.side_a_player1_id, matchForm.side_a_player2_id,
        matchForm.side_b_player1_id, matchForm.side_b_player2_id
      ].filter(id => id !== null && id !== ''); // 過濾掉空值
      if (new Set(players).size !== players.length) {
        logicalErrors.push("同一場比賽中，球員不能重複。");
      }
      if (!matchForm.side_a_outcome) {
        logicalErrors.push("無法根據比分確定勝負，請檢查比分或賽制規則。");
      }
      // ... 其他邏輯驗證 ...

      if (logicalErrors.length > 0) {
        submitMessage.value = `請修正以下問題：\n- ${logicalErrors.join('\n- ')}`;
        submitStatus.value = 'error';
        message.error(submitMessage.value, {duration: 5000, closable: true});
        return;
      }

      submitting.value = true;
      const payload = { /* ... (與之前版本 payload 邏輯相同) ... */};
      try {
        const response = await axios.post(`${apiBaseUrl}/matches/record`, payload);
        // ... (成功處理)
        message.success(response.data.message || '比賽結果已成功儲存！');
        router.push('/'); // 成功後跳轉
      } catch (err) {
        // ... (錯誤處理)
        const errorData = err.response?.data;
        submitMessage.value = errorData?.error || errorData?.message || err.message || "提交失敗。";
        message.error(submitMessage.value);
      } finally {
        submitting.value = false;
      }
    } else {
      message.error("請修正表單中的紅色提示錯誤。");
    }
  });
}

function getSelectedIdAsNumber(idString) {

  if (idString === null || idString === undefined || idString === '') return null;

  const num = parseInt(idString);

  return isNaN(num) ? null : num;

}

const availableSideAPlayer1 = computed(() => {

  const b1 = getSelectedIdAsNumber(matchForm.side_b_player1_id);

  const b2 = getSelectedIdAsNumber(matchForm.side_b_player2_id);

  return allActiveMembers.value.filter(m => m.id !== b1 && m.id !== b2);

});


const availableSideAPlayer2 = computed(() => {

  if (matchForm.match_type !== 'DOUBLES') return [];

  const a1 = getSelectedIdAsNumber(matchForm.side_a_player1_id);

  const b1 = getSelectedIdAsNumber(matchForm.side_b_player1_id);

  const b2 = getSelectedIdAsNumber(matchForm.side_b_player2_id);

  return allActiveMembers.value.filter(m => m.id !== a1 && m.id !== b1 && m.id !== b2);

});


const availableSideBPlayer1 = computed(() => {

  const a1 = getSelectedIdAsNumber(matchForm.side_a_player1_id);

  const a2 = getSelectedIdAsNumber(matchForm.side_a_player2_id);

  return allActiveMembers.value.filter(m => m.id !== a1 && m.id !== a2);

});


const availableSideBPlayer2 = computed(() => {

  if (matchForm.match_type !== 'DOUBLES') return [];

  const a1 = getSelectedIdAsNumber(matchForm.side_a_player1_id);

  const a2 = getSelectedIdAsNumber(matchForm.side_a_player2_id);

  const b1 = getSelectedIdAsNumber(matchForm.side_b_player1_id);

  return allActiveMembers.value.filter(m => m.id !== a1 && m.id !== a2 && m.id !== b1);

});


// 輔助：根據結果顯示不同類型的 Alert
function getOutcomeAlertType(outcomeText) {
  if (!outcomeText) return 'info';
  if (outcomeText.includes('勝利')) return 'success';
  if (outcomeText.includes('平手') || outcomeText.includes('不明確')) return 'warning';
  return 'info';
}
</script>

<style scoped>
.record-match-page {
  max-width: 900px; /* 稍微加寬 */
  margin: auto;
}

.page-main-title.n-h1 {
  font-weight: 600;
  color: var(--text-color-1);
}

.title-icon {
  color: var(--primary-color);
  margin-right: 10px;
  vertical-align: -4px;
}

.form-card.n-card {
  margin-top: 1.5rem;
  border-radius: var(--border-radius-large, 12px);
}

.team-section {
  padding: 15px;
  border: 1px solid #eee;
  border-radius: var(--border-radius, 8px);
  margin-bottom: 1rem; /* 手機上堆疊時的間距 */
}

@media (min-width: 992px) {
  /* lg 及以上，兩欄並排 */
  .team-a-section {
    border-right: 1px solid var(--divider-color, #eee) !important;
    padding-right: 24px !important;
  }

  .team-b-section {
    padding-left: 24px !important;
  }
}

.team-title.n-h5 {
  margin-bottom: 1.2rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #efefef;
  font-weight: 600;
}

.team-title .n-icon {
  vertical-align: -2px;
}

.text-primary {
  color: var(--primary-color) !important;
}

/* Naive UI info color 更合適 */
.text-error {
  color: var(--error-color) !important;
}

/* Naive UI error color */

.n-input-number, .n-select, .n-date-picker {
  /* width: 100%; /* 已在模板中 style="width:100%" */
}

.action-buttons .n-button {
  min-width: 160px; /* 按鈕最小寬度 */
  font-weight: 500;
}
</style>