<template>
  <div class="record-match-page container-fluid mt-4 mb-5 px-md-4">
    <n-h1 align="center" class="page-main-title mb-4">
      <n-icon :component="ClipboardIcon" size="32" class="title-icon"/>
      記錄賽果
    </n-h1>

    <div v-if="matchForm.side_a_outcome" class="winner-display-section mt-2 mb-3 text-center">
      <n-tag :type="getWinnerTagType()" size="large" round>
        <template #icon>
          <n-icon :component="getWinnerIcon()"/>
        </template>
        {{ getWinnerDisplayText() }}
      </n-tag>
    </div>

    <n-divider style="margin-top: 1.5rem; margin-bottom: 1.5rem;"/>

    <n-card :bordered="false" class="form-card">
      <n-form
          ref="formRef"
          :model="matchForm"
          :rules="formRules"
          label-placement="top"
          require-mark-placement="right-hanging"
          @submit.prevent="handleRecordMatch"
      >
        <n-grid :x-gap="15" :y-gap="20" cols="1 s:3" responsive="screen" align-items="start">
          <n-gi :s="15" class="grid-cell">
            <n-form-item-gi label="比賽日期*" path="match_date">
              <n-date-picker
                  v-model:formatted-value="matchForm.match_date"
                  type="date"
                  value-format="yyyy-MM-dd"
                  placeholder="選擇比賽日期"
                  style="width:100%"
              />
            </n-form-item-gi>
          </n-gi>
          <n-gi :s="15" class="grid-cell">
            <n-form-item-gi label="比賽類型*" path="match_type">
              <n-select
                  v-model:value="matchForm.match_type"
                  :options="matchTypeOptions"
                  placeholder="選擇比賽類型"
              />
            </n-form-item-gi>
          </n-gi>
          <n-gi :s="15" class="grid-cell">
            <n-form-item-gi label="賽制" path="match_format">
              <n-select
                  v-model:value="matchForm.match_format"
                  :options="matchFormatOptions"
                  placeholder="選擇賽制"
              />
            </n-form-item-gi>
          </n-gi>

        </n-grid>

        <n-divider style="margin-top: 1.5rem; margin-bottom: 1.5rem;"/>

        <div class="match-details-grid-wrapper">
          <n-grid :x-gap="16" :y-gap="20" cols="1 s:4" responsive="screen" align-items="start"
                  class="match-details-grid">

            <n-gi :s="16" class="grid-cell team-a-players-cell">
              <n-h5 class="cell-title">A隊球員</n-h5>
              <div class="player-entry">
                <n-form-item path="side_a_player1_id" :show-label="false" class="player-select-form-item">
                  <n-select
                      v-model:value="matchForm.side_a_player1_id"
                      :options="availableSideAPlayer1"
                      placeholder="選擇球員 1" filterable clearable
                      label-field="displayNameOnly" value-field="id" class="player-select-control"
                  />
                </n-form-item>
                <div class="player-score-display">
                  <span v-if="selectedPlayerA1" class="score-value">{{ selectedPlayerA1.score }} <span
                      class="score-unit">分</span></span>
                  <span v-else class="score-placeholder">-</span>
                </div>
              </div>
              <div class="player-entry mt-2" v-if="matchForm.match_type === 'DOUBLES'">
                <n-form-item path="side_a_player2_id" :show-label="false" class="player-select-form-item">
                  <n-select
                      v-model:value="matchForm.side_a_player2_id"
                      :options="availableSideAPlayer2"
                      placeholder="選擇球員 2" filterable clearable
                      label-field="displayNameOnly" value-field="id" class="player-select-control"
                  />
                </n-form-item>
                <div class="player-score-display">
                  <span v-if="selectedPlayerA2" class="score-value">{{ selectedPlayerA2.score }} <span
                      class="score-unit">分</span></span>
                  <span v-else class="score-placeholder">-</span>
                </div>
              </div>
            </n-gi>

            <n-gi :s="16" class="grid-cell score-input-cell">
              <n-h5 class="cell-title text-center">A隊得分</n-h5>
              <n-form-item path="side_a_games_won" :show-label="false" class="score-form-item-wrapper">
                <div class="score-input-slider-group">
                  <n-input-number
                      class="score-input-number"
                      :class="{ 'winning-score': matchForm.side_a_outcome === 'WIN' }"
                      v-model:value="matchForm.side_a_games_won"
                      :min="0" :max="5" placeholder="分數"
                  />
                  <n-slider
                      class="score-slider"
                      :class="{ 'winning-score-slider': matchForm.side_a_outcome === 'WIN' }"
                      v-model:value="matchForm.side_a_games_won"
                      :min="0" :max="5" :step="1"
                  />
                </div>
              </n-form-item>
            </n-gi>

            <n-gi :s="16" class="grid-cell score-input-cell">
              <n-h5 class="cell-title text-center">B隊得分</n-h5>
              <n-form-item path="side_b_games_won" :show-label="false" class="score-form-item-wrapper">
                <div class="score-input-slider-group">
                  <n-input-number
                      class="score-input-number"
                      :class="{ 'winning-score': matchForm.side_a_outcome === 'LOSS' }"
                      v-model:value="matchForm.side_b_games_won"
                      :min="0" :max="5" placeholder="分數"
                  />
                  <n-slider
                      class="score-slider"
                      :class="{ 'winning-score-slider': matchForm.side_a_outcome === 'LOSS' }"
                      v-model:value="matchForm.side_b_games_won"
                      :min="0" :max="5" :step="1"
                  />
                </div>
              </n-form-item>
            </n-gi>

            <n-gi :s="16" class="grid-cell team-b-players-cell">
              <n-h5 class="cell-title text-right">B隊球員</n-h5>
              <div class="player-entry">
                <n-form-item path="side_b_player1_id" :show-label="false" class="player-select-form-item">
                  <n-select
                      v-model:value="matchForm.side_b_player1_id"
                      :options="availableSideBPlayer1"
                      placeholder="選擇球員 1" filterable clearable
                      label-field="displayNameOnly" value-field="id" class="player-select-control"
                  />
                </n-form-item>
                <div class="player-score-display">
                  <span v-if="selectedPlayerB1" class="score-value">{{ selectedPlayerB1.score }} <span
                      class="score-unit">分</span></span>
                  <span v-else class="score-placeholder">-</span>
                </div>
              </div>
              <div class="player-entry mt-2" v-if="matchForm.match_type === 'DOUBLES'">
                <n-form-item path="side_b_player2_id" :show-label="false" class="player-select-form-item">
                  <n-select
                      v-model:value="matchForm.side_b_player2_id"
                      :options="availableSideBPlayer2"
                      placeholder="選擇球員 2" filterable clearable
                      label-field="displayNameOnly" value-field="id" class="player-select-control"
                  />
                </n-form-item>
                <div class="player-score-display">
                  <span v-if="selectedPlayerB2" class="score-value">{{ selectedPlayerB2.score }} <span
                      class="score-unit">分</span></span>
                  <span v-else class="score-placeholder">-</span>
                </div>
              </div>
            </n-gi>
          </n-grid>
        </div>

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
import axios from 'axios';
import '../assets/css/match-record.css' // 假設您的 CSS 在此
import {
  NButton,
  NCard,
  NDatePicker,
  NDivider,
  NForm,
  NFormItem,
  NFormItemGi,
  NGi,
  NGrid,
  NH1,
  NH5,
  NIcon,
  NInputNumber,
  NSelect,
  NSlider,
  NSpace,
  NTag,
  useMessage
} from 'naive-ui';
import {
  CheckmarkCircleOutline as WinIcon,
  ClipboardOutline as ClipboardIcon,
  HelpCircleOutline as HelpCircleOutlineIcon,
  RemoveCircleOutline as DrawIcon,
  SaveOutline as SaveIcon
} from '@vicons/ionicons5';

const router = useRouter();
const message = useMessage();
const allActiveMembers = ref([]);

const matchForm = reactive({
  match_date: new Date().toISOString().split('T')[0],
  match_type: 'DOUBLES',
  match_format: 'NINE_GAME_SET',
  side_a_player1_id: null,
  side_a_player2_id: null,
  side_b_player1_id: null,
  side_b_player2_id: null,
  side_a_games_won: 0, // 確保初始值為數字0，以便input-number和slider正常工作
  side_b_games_won: 0, // 同上
  side_a_outcome: '', // 初始化為空，表示結果未定
  match_notes: ''
});

const submitting = ref(false);
const submitMessage = ref('');
const submitStatus = ref('');
const calculatedOutcomeDisplay = ref('請輸入比分以計算結果。'); // 給一個初始提示
const formRef = ref(null);

const matchTypeOptions = [
  {label: '雙打', value: 'DOUBLES'},
  {label: '單打', value: 'SINGLES'}
];

const matchFormatOptions = ref([
  // {label: '搶七', value: 'TIEBREAK', meta: {gamesToWin: 7, needsTwoClear: true, isPoints: true}}, // 添加 isPoints 標記
  {label: '五局三勝制', value: 'FIVE_GAME_SET', meta: {gamesToWin: 3, needsTwoClear: false}},
  {label: '七局四勝制', value: 'SEVEN_GAME_SET', meta: {gamesToWin: 4, needsTwoClear: false}},
  {label: '九局五勝制', value: 'NINE_GAME_SET', meta: {gamesToWin: 5, needsTwoClear: false}},
]);

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

const getScoreInputMax = () => {
  const selectedFormat = matchFormatOptions.value.find(opt => opt.value === matchForm.match_format);
  if (selectedFormat && selectedFormat.meta) {
    if (selectedFormat.meta.isPoints && selectedFormat.value === 'TIEBREAK') {
      return 15;
    }
    return selectedFormat.meta.gamesToWin > 0 ? selectedFormat.meta.gamesToWin : 5; // 一般局數的上限
  }
  return 5; // 預設最大5分
};


onMounted(async () => {
  try {
    const response = await axios.get(`${apiBaseUrl}/members`, {
      params: {all: 'false'}
    });
    allActiveMembers.value = response.data.map(m => ({
      ...m, // 保留所有原始屬性，包括 id 和 score
      displayNameOnly: m.display_name || m.name // 新增一個只包含名字的字段給 n-select 使用
    })) || [];
  } catch (error) {
    console.error("Failed to fetch members:", error);
    message.error("獲取球員列表失敗。");
  }
  determineWinnerFrontend(); // 頁面加載時根據初始值計算一次
});

// 監聽比分和賽制變化
watch([
  () => matchForm.side_a_games_won,
  () => matchForm.side_b_games_won,
  () => matchForm.match_format // 加入對賽制的監聽
], determineWinnerFrontend, {deep: true}); // deep: true 可能不需要，因為監聽的是基本類型和頂層對象

watch(() => matchForm.match_type, (newType) => {
  if (newType === 'SINGLES') {
    matchForm.side_a_player2_id = null;
    matchForm.side_b_player2_id = null;
  }
  // 可以考慮在類型改變時也重新計算勝負，如果適用
  // determineWinnerFrontend();
});


function determineWinnerFrontend() {
  const gamesA = parseInt(matchForm.side_a_games_won, 10);
  const gamesB = parseInt(matchForm.side_b_games_won, 10);
  const formatValue = matchForm.match_format;
  const selectedFormat = matchFormatOptions.value.find(opt => opt.value === formatValue);

  // 確保 gamesA 和 gamesB 是有效數字，否則視為0處理或保持現狀
  if (isNaN(gamesA) || isNaN(gamesB) || gamesA < 0 || gamesB < 0) {
    matchForm.side_a_outcome = ''; // 重置結果
    calculatedOutcomeDisplay.value = '請輸入有效的局數。';
    return;
  }
  if (!selectedFormat) {
    matchForm.side_a_outcome = '';
    calculatedOutcomeDisplay.value = '請選擇賽制。';
    return;
  }


  const gamesToWin = selectedFormat.meta.gamesToWin;
  const needsTwoClear = selectedFormat.meta.needsTwoClear;
  let outcome = '';
  let display = `A隊 ${gamesA} : ${gamesB} B隊`;

  // 檢查是否有一方達到勝利條件
  const aReachedWin = gamesA >= gamesToWin;
  const bReachedWin = gamesB >= gamesToWin;

  if (aReachedWin && bReachedWin) { // 雙方都達到或超過 gamesToWin
    if (needsTwoClear) {
      if (gamesA - gamesB >= 2) outcome = 'WIN';
      else if (gamesB - gamesA >= 2) outcome = 'LOSS';
      else display += ' (需淨勝)'; // 例如 7:6 in Tiebreak
    } else { // 不需要淨勝，但雙方都達標了 (例如：若gamesToWin=3, 比賽出現 3:3)
      if (gamesA > gamesB) outcome = 'WIN'; // 這種情況理論上不會發生，除非gamesToWin設錯
      else outcome = 'LOSS';
    }
  } else if (aReachedWin) { // 只有A隊達到 gamesToWin
    if (needsTwoClear) {
      if (gamesA - gamesB >= 2) outcome = 'WIN';
      else display += ' (需淨勝)';
    } else {
      outcome = 'WIN';
    }
  } else if (bReachedWin) { // 只有B隊達到 gamesToWin
    if (needsTwoClear) {
      if (gamesB - gamesA >= 2) outcome = 'LOSS';
      else display += ' (需淨勝)';
    } else {
      outcome = 'LOSS';
    }
  } else {
    // 雙方都未達到 gamesToWin
    display += ' (進行中)';
  }


  if (outcome === 'WIN') {
    display = `A隊 ${gamesA} : ${gamesB} B隊 (A隊勝利)`;
  } else if (outcome === 'LOSS') {
    display = `A隊 ${gamesA} : ${gamesB} B隊 (B隊勝利)`;
  }

  matchForm.side_a_outcome = outcome;
  calculatedOutcomeDisplay.value = display;
}


const formRules = {
  match_date: [{required: true, message: '比賽日期為必填', type: 'string', trigger: ['blur', 'change']}],
  match_type: [{required: true, message: '比賽類型為必填', trigger: ['blur', 'change']}],
  match_format: [{required: true, message: '賽制為必填', trigger: ['blur', 'change']}],
  side_a_player1_id: [{required: true, message: 'A隊球員1為必填', type: 'number', trigger: ['blur', 'change']}],
  side_b_player1_id: [{required: true, message: 'B隊球員1為必填', type: 'number', trigger: ['blur', 'change']}],
  side_a_player2_id: [{
    required: computed(() => matchForm.match_type === 'DOUBLES'), // 動態 required
    message: 'A隊球員2為必填',
    type: 'number',
    trigger: ['blur', 'change']
  }],
  side_b_player2_id: [{
    required: computed(() => matchForm.match_type === 'DOUBLES'), // 動態 required
    message: 'B隊球員2為必填',
    type: 'number',
    trigger: ['blur', 'change']
  }],
  side_a_games_won: [
    {required: true, type: 'number', message: 'A隊局數為必填', trigger: ['input', 'blur']},
    // max 規則會根據 getScoreInputMax() 動態變化，這裡的靜態 max:5 僅作基礎限制
    // 更精確的驗證可以在提交時或 watch 中處理
    {
      type: 'number',
      min: 0,
      max: computed(() => getScoreInputMax()),
      message: () => `局數必須介於 0 到 ${getScoreInputMax()} 之間`,
      trigger: ['input', 'blur']
    }
  ],
  side_b_games_won: [
    {required: true, type: 'number', message: 'B隊局數為必填', trigger: ['input', 'blur']},
    {
      type: 'number',
      min: 0,
      max: computed(() => getScoreInputMax()),
      message: () => `局數必須介於 0 到 ${getScoreInputMax()} 之間`,
      trigger: ['input', 'blur']
    }
  ],
};

async function handleRecordMatch() {
  formRef.value?.validate(async (validationErrors) => {
    if (!validationErrors) {
      clearMessages();
      let logicalErrors = [];
      const players = [
        matchForm.side_a_player1_id,
        matchForm.match_type === 'DOUBLES' ? matchForm.side_a_player2_id : null, // 只在雙打時檢查
        matchForm.side_b_player1_id,
        matchForm.match_type === 'DOUBLES' ? matchForm.side_b_player2_id : null  // 只在雙打時檢查
      ].filter(id => id !== null && id !== undefined && id !== '');

      if (new Set(players).size !== players.length) {
        logicalErrors.push("同一場比賽中，球員不能重複。");
      }

      // 再次調用 determineWinnerFrontend 以確保 outcome 是最新的
      determineWinnerFrontend();
      if (!matchForm.side_a_outcome) { // 'WIN', 'LOSS', 'DRAW' 之一
        logicalErrors.push("無法根據比分確定有效勝負，請檢查比分或賽制規則。");
      }

      // 檢查分數是否超過動態最大值 (雖然 input 已限制，但多一層保險)
      const maxScore = getScoreInputMax();
      if (matchForm.side_a_games_won > maxScore || matchForm.side_b_games_won > maxScore) {
        logicalErrors.push(`輸入的局數不能超過當前賽制允許的最大值 (${maxScore})。`);
      }


      if (logicalErrors.length > 0) {
        submitMessage.value = `請修正以下問題：\n- ${logicalErrors.join('\n- ')}`;
        submitStatus.value = 'error';
        // message.error(submitMessage.value, {duration: 5000, closable: true}); // 改用 n-alert 顯示
        return;
      }

      submitting.value = true;
      const payload = {
        match_date: matchForm.match_date,
        match_type: matchForm.match_type,
        match_format: matchForm.match_format,
        side_a_player1_id: getSelectedIdAsNumber(matchForm.side_a_player1_id),
        side_a_player2_id: matchForm.match_type === 'DOUBLES' ? getSelectedIdAsNumber(matchForm.side_a_player2_id) : null,
        side_b_player1_id: getSelectedIdAsNumber(matchForm.side_b_player1_id),
        side_b_player2_id: matchForm.match_type === 'DOUBLES' ? getSelectedIdAsNumber(matchForm.side_b_player2_id) : null,
        side_a_games_won: matchForm.side_a_games_won,
        side_b_games_won: matchForm.side_b_games_won,
        side_a_outcome: matchForm.side_a_outcome,
        match_notes: matchForm.match_notes
      };
      try {
        const response = await axios.post(`${apiBaseUrl}/matches/record`, payload);
        submitStatus.value = 'success';
        submitMessage.value = response.data.message || '比賽結果已成功儲存！將跳轉回排行榜...';
        message.success(submitMessage.value); // Naive UI message
        setTimeout(() => {
          router.push('/'); // 成功後跳轉
        }, 2000); // 延遲一點跳轉，讓用戶看到成功訊息
      } catch (err) {
        const errorData = err.response?.data;
        submitStatus.value = 'error';
        submitMessage.value = errorData?.error || errorData?.message || err.message || "提交失敗，請檢查網路或稍後再試。";
        // message.error(submitMessage.value); // 改用 n-alert 顯示
      } finally {
        submitting.value = false;
      }
    } else {
      submitStatus.value = 'error';
      submitMessage.value = "請修正表單中的紅色提示錯誤。";
      // message.error("請修正表單中的紅色提示錯誤。"); // 改用 n-alert 顯示
    }
  });
}

function getSelectedIdAsNumber(idString) {
  if (idString === null || idString === undefined || idString === '') return null;
  const num = parseInt(idString);
  return isNaN(num) ? null : num;
}

const selectedPlayerA1 = computed(() => getPlayerById(matchForm.side_a_player1_id));
const selectedPlayerA2 = computed(() => getPlayerById(matchForm.side_a_player2_id));
const selectedPlayerB1 = computed(() => getPlayerById(matchForm.side_b_player1_id));
const selectedPlayerB2 = computed(() => getPlayerById(matchForm.side_b_player2_id));

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

const getPlayerById = (playerId) => {
  if (!playerId) return null;
  return allActiveMembers.value.find(m => m.id === playerId);
};

function getOutcomeAlertType(outcomeText) {
  if (!outcomeText) return 'info';
  if (outcomeText.includes('A隊勝利')) return 'success';
  if (outcomeText.includes('B隊勝利')) return 'success'; // B隊勝利也用 success
  return 'error'; // 其他情況（如“請輸入有效局數”）可能是錯誤提示
}

function getWinnerTagType() {
  if (matchForm.side_a_outcome === 'WIN') return 'success';  // A隊勝利
  if (matchForm.side_a_outcome === 'LOSS') return 'error';   // B隊勝利 (A隊視角是LOSS)
  if (matchForm.side_a_outcome === 'DRAW') return 'warning'; // 平手
  return 'default';
}

function getWinnerIcon() {
  if (matchForm.side_a_outcome === 'WIN' || matchForm.side_a_outcome === 'LOSS') return WinIcon; // 無論誰贏都用 WinIcon
  if (matchForm.side_a_outcome === 'DRAW') return DrawIcon;
  return HelpCircleOutlineIcon;
}

function getWinnerDisplayText() {
  if (matchForm.side_a_outcome === 'WIN') return 'A隊 勝利！';
  if (matchForm.side_a_outcome === 'LOSS') return 'B隊 勝利！';
  if (matchForm.side_a_outcome === 'DRAW') return '雙方平手';
  return '結果未定';
}

function clearMessages() {
  submitMessage.value = '';
  submitStatus.value = '';
}
</script>
