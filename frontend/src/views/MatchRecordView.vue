<template>
  <div class="container mt-4 mb-5 record-match-page">
    <h1 class="mb-4 text-center display-6 page-title">記錄校內排名賽結果</h1>

    <div v-if="submitMessage"
         :class="['alert', submitStatus === 'success' ? 'alert-success' : 'alert-danger', 'alert-dismissible', 'fade', 'show']"
         role="alert">
      <span style="white-space: pre-wrap;">{{ submitMessage }}</span>
      <button type="button" class="btn-close" @click="clearMessages" aria-label="Close"></button>
    </div>

    <form @submit.prevent="handleRecordMatch" class="needs-validation" novalidate>
      <div class="row g-3 mb-4">
        <div class="col-md-4">
          <label for="match_date" class="form-label">比賽日期*</label>
          <input type="date" class="form-control" id="match_date" v-model="matchForm.match_date" required>
        </div>
        <div class="col-md-4">
          <label for="match_type" class="form-label">比賽類型*</label>
          <select class="form-select" id="match_type" v-model="matchForm.match_type" required>
            <option value="DOUBLES">雙打</option>
            <option value="SINGLES">單打</option>
          </select>
        </div>
        <div class="col-md-4">
          <label for="match_format" class="form-label">賽制*</label>
          <select class="form-select" id="match_format" v-model="matchForm.match_format" required>
            <option value="" disabled>--選擇賽制--</option>
            <option v-for="format in matchFormats" :key="format.name" :value="format.name">
              {{ format.value }}
            </option>
          </select>
        </div>
      </div>

      <hr class="my-4">

      <div class="row g-3">
        <div class="col-lg-6 border-end-lg pe-lg-4 mb-3 mb-lg-0">
          <h5 class="text-primary mb-3"><i class="bi bi-people-fill me-1"></i>A 方隊伍</h5>
          <div class="mb-3">
            <label for="side_a_player1_id" class="form-label">A 方球員 1*</label>
            <select class="form-select" id="side_a_player1_id" v-model="matchForm.side_a_player1_id" required>
              <option value="" disabled>--選擇球員--</option>
              <option v-for="member in availableSideAPlayer1" :key="member.id" :value="member.id">{{ member.name }} ({{ member.score }})</option>
            </select>
          </div>
          <div class="mb-3" v-if="matchForm.match_type === 'DOUBLES'">
            <label for="side_a_player2_id" class="form-label">A 方球員 2*</label>
            <select class="form-select" id="side_a_player2_id" v-model="matchForm.side_a_player2_id" :required="matchForm.match_type === 'DOUBLES'">
              <option value="" disabled>--選擇球員--</option>
              <option v-for="member in availableSideAPlayer2" :key="member.id" :value="member.id">{{ member.name }} ({{ member.score }})</option>
            </select>
          </div>
          <div class="mb-3">
            <label for="side_a_games_won" class="form-label">A 方局數*</label>
            <input type="number" class="form-control score-input"
                   id="side_a_games_won" v-model.number="matchForm.side_a_games_won" min="0" required>
          </div>
        </div>

        <div class="col-lg-6 ps-lg-4">
          <h5 class="text-danger mb-3"><i class="bi bi-people me-1"></i>B 方隊伍</h5>
          <div class="mb-3">
            <label for="side_b_player1_id" class="form-label">B 方球員 1*</label>
            <select class="form-select" id="side_b_player1_id" v-model="matchForm.side_b_player1_id" required>
              <option value="" disabled>--選擇球員--</option>
              <option v-for="member in availableSideBPlayer1" :key="member.id" :value="member.id">{{ member.name }} ({{ member.score }})</option>
            </select>
          </div>
          <div class="mb-3" v-if="matchForm.match_type === 'DOUBLES'">
            <label for="side_b_player2_id" class="form-label">B 方球員 2*</label>
            <select class="form-select" id="side_b_player2_id" v-model="matchForm.side_b_player2_id" :required="matchForm.match_type === 'DOUBLES'">
              <option value="" disabled>--選擇球員--</option>
              <option v-for="member in availableSideBPlayer2" :key="member.id" :value="member.id">{{ member.name }} ({{ member.score }})</option>
            </select>
          </div>
          <div class="mb-3">
            <label for="side_b_games_won" class="form-label">B 方局數*</label>
            <input type="number" class="form-control score-input"
                   id="side_b_games_won" v-model.number="matchForm.side_b_games_won" min="0" required>
          </div>
        </div>
      </div>

      <div v-if="calculatedOutcomeDisplay" class="mt-4 mb-3 alert fs-5 text-center"
           :class="{'alert-success': calculatedOutcomeDisplay.includes('A方勝利'),
                      'alert-primary': calculatedOutcomeDisplay.includes('B方勝利'),
                      'alert-warning': !calculatedOutcomeDisplay.includes('勝利')}">
        <strong>{{ calculatedOutcomeDisplay }}</strong>
      </div>

      <hr class="my-4">
      <button type="submit" class="btn btn-primary btn-lg w-100"
              :disabled="submitting || !matchForm.side_a_outcome">
        <span v-if="submitting" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
        {{ submitting ? ' 提交中...' : '儲存比賽結果' }}
      </button>
      <router-link to="/" class="btn btn-outline-secondary btn-lg w-100 mt-2 mb-4">返回排行榜</router-link>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const allActiveMembers = ref([]);

const matchForm = reactive({
  match_date: new Date().toISOString().split('T')[0],
  match_type: 'DOUBLES',
  match_format: 'NINE_GAME_SET',
  side_a_player1_id: '',
  side_a_player2_id: null,
  side_b_player1_id: '',
  side_b_player2_id: null,
  side_a_games_won: null,
  side_b_games_won: null,
  side_a_outcome: '', // 將由 determineWinnerFrontend 設定
  match_notes: ''
});

const submitting = ref(false);
const submitMessage = ref('');
const submitStatus = ref('');
const calculatedOutcomeDisplay = ref(''); // 用於UI顯示，不直接提交

// 賽制選項
const matchFormats = ref([
  { name: 'TIEBREAK', value: '搶七 (先到7分勝2分)', gamesToWin: 7, needsTwoClear: true },
  { name: 'FIVE_GAME_SET', value: '五局制 (先贏3局)', gamesToWin: 3, needsTwoClear: false },
  { name: 'SEVEN_GAME_SET', value: '七局制 (先贏4局)', gamesToWin: 4, needsTwoClear: false },
  { name: 'NINE_GAME_SET', value: '九局制 (先贏5局)', gamesToWin: 5, needsTwoClear: false },
]);
// outcomesForSelect 已不再需要，因為不再有手動選擇最終結果的下拉選單

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

onMounted(async () => {
  try {
    const response = await axios.get(`${apiBaseUrl}/members`, {
        params: { active_only: true }
    });
    allActiveMembers.value = response.data;
  } catch (error) {
    console.error("Failed to load members:", error.response || error);
    submitMessage.value = "無法載入球員列表。";
    submitStatus.value = "error";
  }
  determineWinnerFrontend(); // 初始判斷一次
});

watch(() => matchForm.match_format, () => {
    matchForm.side_a_games_won = null;
    matchForm.side_b_games_won = null;
    determineWinnerFrontend();
});

watch(() => matchForm.match_type, (newType) => {
    if (newType === 'SINGLES') {
        matchForm.side_a_player2_id = null;
        matchForm.side_b_player2_id = null;
    }
    determineWinnerFrontend();
});

watch([() => matchForm.side_a_games_won, () => matchForm.side_b_games_won],
      determineWinnerFrontend,
      { deep: false }
);

// 前端即時判斷勝負的邏輯
function determineWinnerFrontend() {
  const gamesA = matchForm.side_a_games_won === null || matchForm.side_a_games_won === '' ? null : Number(matchForm.side_a_games_won);
  const gamesB = matchForm.side_b_games_won === null || matchForm.side_b_games_won === '' ? null : Number(matchForm.side_b_games_won);

  // 先重置，避免舊狀態殘留
  calculatedOutcomeDisplay.value = '';
  matchForm.side_a_outcome = '';


  if (gamesA === null || gamesB === null || !matchForm.match_format) {
    calculatedOutcomeDisplay.value = '請輸入雙方局數/分數並選擇賽制';
    return;
  }
  if (isNaN(gamesA) || isNaN(gamesB) || gamesA < 0 || gamesB < 0) {
    calculatedOutcomeDisplay.value = '請輸入有效的非負局數/分數';
    return;
  }

  let outcomeText = '比分未完成或結果不明確';
  let outcomeForApi = ''; // 'WIN' or 'LOSS' for side A
  let aWins = false;
  let bWins = false;

  const currentFormat = matchFormats.value.find(f => f.name === matchForm.match_format);
  if (!currentFormat) {
    calculatedOutcomeDisplay.value = '無效的賽制選擇';
    return;
  }

  const targetScore = currentFormat.gamesToWin;
  const needsTwoClear = currentFormat.needsTwoClear;

  if (needsTwoClear) { // 例如搶七
    if (gamesA >= targetScore && gamesA >= gamesB + 2) {
      aWins = true;
    } else if (gamesB >= targetScore && gamesB >= gamesA + 2) {
      bWins = true;
    } else if (gamesA === targetScore - 1 && gamesB === targetScore - 1) {
      outcomeText = `平手 (${gamesA}-${gamesB})，需淨勝2分`;
    } else if ((gamesA >= targetScore -1 || gamesB >= targetScore -1) && Math.abs(gamesA - gamesB) < 2) {
        outcomeText = `比賽進行中 (${gamesA}-${gamesB})，需淨勝2分`;
    } else if (gamesA === gamesB && gamesA >= targetScore -1) {
        outcomeText = `平手 (${gamesA}-${gamesB})，需淨勝2分`;
    }
  } else { // 不需要淨勝2局的局數制 (先達到目標局數者勝)
    if (gamesA >= targetScore && gamesA > gamesB) {
      aWins = true;
    } else if (gamesB >= targetScore && gamesB > gamesA) {
      bWins = true;
    } else if (gamesA === targetScore && gamesA === gamesB && gamesA >= targetScore){ // 雙方都達到但平手
        outcomeText = `局數 ${gamesA}:${gamesB} 平手，此賽制下結果不明確`;
    } else if (gamesA < targetScore && gamesB < targetScore) {
        outcomeText = '比分尚未達到獲勝條件';
    }
  }

  if (aWins) {
    outcomeText = `A方勝利 (${gamesA} : ${gamesB})`;
    outcomeForApi = 'WIN';
  } else if (bWins) {
    outcomeText = `B方勝利 (${gamesB} : ${gamesA})`; // A方失敗
    outcomeForApi = 'LOSS';
  }

  calculatedOutcomeDisplay.value = outcomeText;
  matchForm.side_a_outcome = outcomeForApi; // 直接設定，不再需要使用者手動確認
}


async function handleRecordMatch() {
  clearMessages(); // 清除舊的提示訊息

  // --- 前端基本驗證 (與之前類似，但更強調 side_a_outcome 由前端邏輯產生) ---
  const { match_date, match_type, match_format,
          side_a_player1_id, side_b_player1_id,
          side_a_games_won, side_b_games_won,
          side_a_outcome } = matchForm; // 直接從 matchForm 取 side_a_outcome
  let errors = [];
  // ... (之前的必填項和邏輯驗證，例如球員不重複等) ...
  if (!match_date) errors.push("比賽日期");
  if (!match_type) errors.push("比賽類型");
  if (!match_format) errors.push("賽制");
  if (!side_a_player1_id) errors.push("A方球員1");
  if (!side_b_player1_id) errors.push("B方球員1");
  if (side_a_games_won === null || side_a_games_won === '' || Number(side_a_games_won) < 0) errors.push("A方有效勝局/分數");
  if (side_b_games_won === null || side_b_games_won === '' || Number(side_b_games_won) < 0) errors.push("B方有效勝局/分數");

  if (match_type === 'DOUBLES') { /* ...雙打球員驗證... */ }
  // ... (球員不重複等其他驗證) ...

  // 最重要的：確保前端邏輯已判斷出明確的勝負結果
  if (!side_a_outcome) {
    errors.push("無法根據比分確定勝負，請檢查比分或賽制規則");
  }

  if (errors.length > 0) {
    submitMessage.value = `請填寫或修正以下欄位：${errors.join('、')}。`;
    submitStatus.value = 'error';
    submitting.value = false;
    return;
  }

  submitting.value = true;
  const payload = {
    match_date: matchForm.match_date,
    match_type: matchForm.match_type,
    match_format: matchForm.match_format,
    side_a_player1_id: parseInt(matchForm.side_a_player1_id),
    side_a_player2_id: matchForm.match_type === 'DOUBLES' && matchForm.side_a_player2_id ? parseInt(matchForm.side_a_player2_id) : null,
    side_b_player1_id: parseInt(matchForm.side_b_player1_id),
    side_b_player2_id: matchForm.match_type === 'DOUBLES' && matchForm.side_b_player2_id ? parseInt(matchForm.side_b_player2_id) : null,
    side_a_games_won: parseInt(matchForm.side_a_games_won),
    side_b_games_won: parseInt(matchForm.side_b_games_won),
    side_a_outcome: matchForm.side_a_outcome, // 直接使用由 determineWinnerFrontend 設定的值
    match_notes: matchForm.match_notes || null
  };

  try {
    const response = await axios.post(`${apiBaseUrl}/matches/record`, payload);
    submitMessage.value = response.data.message || '比賽結果已成功儲存！';
    submitStatus.value = 'success';

    // 重置表單
    Object.assign(matchForm, {
        match_date: new Date().toISOString().split('T')[0],
        match_type: 'DOUBLES',
        match_format: 'NINE_GAME_SET',
        side_a_player1_id: '', side_a_player2_id: null,
        side_b_player1_id: '', side_b_player2_id: null,
        side_a_games_won: null, side_b_games_won: null,
        side_a_outcome: '', match_notes: ''
    });
    calculatedOutcomeDisplay.value = '';

    setTimeout(() => {
        clearMessages();
        router.push('/');
    }, 2000);

  } catch (error) { /* ...錯誤處理... */ } finally { /* ... */ }
}

function clearMessages() {
  submitMessage.value = '';
  submitStatus.value = '';
}

// --- 下拉選單 ---
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

</script>

<style scoped>
.record-match-page { max-width: 800px; } /* 稍微縮小一點以適應內容 */
h5 { margin-top: 1.5rem; padding-bottom: 0.25rem; border-bottom: 1px solid #eee; font-weight: 600;}
.score-input { text-align: center; font-weight: bold; }
.page-title { color: #333; }
.form-label { font-weight: 500; }
.btn-close { /* 讓 alert 中的關閉按鈕更好看 */
    padding: 0.5rem;
}
/* 在較小螢幕上，左右兩欄球員選擇堆疊 */
@media (max-width: 991.98px) { /* lg斷點以下 */
    .border-end-lg {
        border-right: none !important;
    }
    .ps-lg-4 {
        padding-left: var(--bs-gutter-x) * .5 !important; /* 恢復預設 padding */
    }
    .col-lg-6.border-end-lg.pe-lg-4.mb-3.mb-lg-0 {
        margin-bottom: 1rem !important; /* 手機上堆疊時增加間距 */
    }
}
</style>