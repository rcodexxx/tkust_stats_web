// frontend/src/views/RecordMatchView.vue
<template>
  <div class="container mt-4 mb-5 record-match-page">
    <h1 class="mb-4 text-center">記錄校內排名賽結果</h1>

    <div v-if="submitMessage"
         :class="['alert', submitStatus === 'success' ? 'alert-success' : 'alert-danger']"
         role="alert">
      {{ submitMessage }}
    </div>

    <form @submit.prevent="handleRecordMatch" class="needs-validation" novalidate>
      <div class="row g-3">
        <div class="col-md-4">
          <label for="match_date" class="form-label">比賽日期*</label>
          <input type="date" class="form-control" id="match_date" v-model="matchForm.match_date" required>
        </div>
        <div class="col-md-4">
          <label for="match_type" class="form-label">比賽類型*</label>
          <select class="form-select" id="match_type" v-model="matchForm.match_type" required
                  @change="resetPlayer2Selections">
            <option value="" disabled>--選擇類型--</option>
            <option value="SINGLES">單打</option>
            <option value="DOUBLES">雙打</option>
          </select>
        </div>
        <div class="col-md-4">
          <label for="match_format" class="form-label">賽制*</label>
          <select class="form-select" id="match_format" v-model="matchForm.match_format" required
                  @change="initializeScores">
            <option value="" disabled>--選擇賽制--</option>
            <option v-for="format in matchFormats" :key="format.name" :value="format.name">
              {{ format.value }}
            </option>
          </select>
        </div>
      </div>

      <hr class="my-3">
      <div class="row">
        <div class="col-md-6 border-end pe-3">
          <h5>A 方球員</h5>
          <div class="mb-3">
            <label for="side_a_player1_id" class="form-label">A 方球員 1*</label>
            <select class="form-select" id="side_a_player1_id" v-model="matchForm.side_a_player1_id" required>
              <option value="" disabled>--選擇球員--</option>
              <option v-for="member in availableSideAPlayer1" :key="member.id" :value="member.id">
                {{ member.name }} (現有分數: {{ member.score }})
              </option>
            </select>
          </div>
          <div class="mb-3" v-if="matchForm.match_type === 'DOUBLES'">
            <label for="side_a_player2_id" class="form-label">A 方球員 2*</label>
            <select class="form-select" id="side_a_player2_id" v-model="matchForm.side_a_player2_id"
                    :required="matchForm.match_type === 'DOUBLES'">
              <option value="" disabled>--選擇球員--</option>
              <option v-for="member in availableSideAPlayer2" :key="member.id" :value="member.id">
                {{ member.name }} (現有分數: {{ member.score }})
              </option>
            </select>
          </div>
        </div>
        <div class="col-md-6 ps-3">
          <h5>B 方球員</h5>
          <div class="mb-3">
            <label for="side_b_player1_id" class="form-label">B 方球員 1*</label>
            <select class="form-select" id="side_b_player1_id" v-model="matchForm.side_b_player1_id" required>
              <option value="" disabled>--選擇球員--</option>
              <option v-for="member in availableSideBPlayer1" :key="member.id" :value="member.id">
                {{ member.name }} (現有分數: {{ member.score }})
              </option>
            </select>
          </div>
          <div class="mb-3" v-if="matchForm.match_type === 'DOUBLES'">
            <label for="side_b_player2_id" class="form-label">B 方球員 2*</label>
            <select class="form-select" id="side_b_player2_id" v-model="matchForm.side_b_player2_id"
                    :required="matchForm.match_type === 'DOUBLES'">
              <option value="" disabled>--選擇球員--</option>
              <option v-for="member in availableSideBPlayer2" :key="member.id" :value="member.id">
                {{ member.name }} (現有分數: {{ member.score }})
              </option>
            </select>
          </div>
        </div>
      </div>

      <hr class="my-3">
      <h5>比分記錄</h5>
      <div v-for="(set, index) in scores" :key="index" class="row mb-2 align-items-center">
        <div class="col-auto">
          <label class="form-label">第 {{ index + 1 }} {{
              matchForm.match_format === 'NINE_GAME_PRO_SET' ? '局' : '盤'
            }}</label>
        </div>
        <div class="col">
          <input type="number" class="form-control form-control-sm score-input"
                 placeholder="A方局數" v-model.number="set.side_a" @input="determineWinner" min="0">
        </div>
        <div class="col-auto px-0 text-center">-</div>
        <div class="col">
          <input type="number" class="form-control form-control-sm score-input"
                 placeholder="B方局數" v-model.number="set.side_b" @input="determineWinner" min="0">
        </div>
      </div>

      <div v-if="calculatedOutcome" class="mt-3 mb-3 alert"
           :class="{'alert-success': calculatedOutcome === 'A方勝利', 'alert-info': calculatedOutcome === 'B方勝利', 'alert-warning': calculatedOutcome === '平手或未完成'}">
        <strong>初步判斷結果: {{ calculatedOutcome }}</strong>
      </div>

      <div class="mb-3 mt-3">
        <label for="final_outcome" class="form-label">最終確認 A 方比賽結果*</label>
        <select class="form-select" id="final_outcome" v-model="matchForm.side_a_outcome" required>
          <option value="" disabled>--請選擇最終結果--</option>
          <option value="WIN">A 方勝利</option>
          <option value="LOSS">A 方失敗 (B 方勝利)</option>
        </select>
      </div>

      <button type="submit" class="btn btn-primary btn-lg w-100 mt-3"
              :disabled="submitting || !matchForm.side_a_outcome">
        {{ submitting ? '提交中...' : '儲存比賽結果' }}
      </button>
    </form>
  </div>
</template>

// frontend/src/views/RecordMatchView.vue
<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios'; // 直接使用 axios，或確保 service 已正確建立和匯入

const router = useRouter();
const allActiveMembers = ref([]);

const matchForm = reactive({
  match_date: new Date().toISOString().split('T')[0],
  match_type: 'SINGLES',
  match_format: '',
  side_a_player1_id: '',
  side_a_player2_id: null,
  side_b_player1_id: '',
  side_b_player2_id: null,
  side_a_outcome: '',
  match_notes: ''
});

const scores = ref([]);

const submitting = ref(false);
const submitMessage = ref('');
const submitStatus = ref('');
const calculatedOutcome = ref('');

const matchFormats = ref([
  {name: 'FOUR_GAME_SET', value: '短盤搶四 (4局決勝)', setsToWin: 1, gamesToWinSet: 4, finalSetTiebreakTo: 0 },
  {name: 'SEVEN_POINT_TIEBREAK', value: '標準盤搶七 (6局決勝)', setsToWin: 1, gamesToWinSet: 6, finalSetTiebreakTo: 7 },
  {name: 'NINE_GAME_PRO_SET', value: '長盤九局五勝', setsToWin: 1, gamesToWinSet: 5, isProSet: true, proSetGames: 9 },
  {name: 'CUSTOM', value: '自訂/其他'}
]);

const outcomesForSelect = ref([ {name: 'WIN', value: 'A 方勝利'}, {name: 'LOSS', value: 'A 方失敗'}]);

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL; // <--- 確保定義了 apiBaseUrl

onMounted(async () => {
  try {
    console.log(`Workspaceing members from: ${apiBaseUrl}/members?active_only=true`); // 除錯日誌
    const memberResponse = await axios.get(`${apiBaseUrl}/members`, {
      params: {
        active_only: true // 明確要求只獲取活躍成員，與後端預設行為一致
      }
    });
    console.log("Members API response data:", memberResponse.data); // 除錯日誌

    if (Array.isArray(memberResponse.data)) {
      allActiveMembers.value = memberResponse.data;
      if (memberResponse.data.length === 0) {
        console.warn("No active members found from API for dropdowns.");
      }
    } else {
      console.error("API did not return an array for members:", memberResponse.data);
      allActiveMembers.value = [];
    }

  } catch (error) {
    console.error("Failed to load members for form:", error.response || error);
    // 可以在 UI 上顯示一個更友好的錯誤訊息
    // this.formError = "無法載入球員列表，請稍後再試。";
    allActiveMembers.value = []; // 確保出錯時是空陣列
  }
  // initializeScores(); // 如果這個函數依賴成員數據，則不應在此，或者需要等待
});

function initializeScores() {
  scores.value = [{side_a: null, side_b: null}];
  calculatedOutcome.value = '';
  matchForm.side_a_outcome = '';
}

watch(() => matchForm.match_format, initializeScores);

watch(() => matchForm.match_type, (newType) => {
  if (newType === 'SINGLES') {
    matchForm.side_a_player2_id = null;
    matchForm.side_b_player2_id = null;
  }
});

// --- 計算屬性來過濾下拉選單選項 (保持不變，但確保它們能正確處理 parseInt 後的 null/undefined) ---
// A 方球員1 的可選列表：所有活躍成員中，未被 B 方任何一個位置選中的成員
const availableSideAPlayer1 = computed(() => {
  return allActiveMembers.value.filter(member =>
      !((matchForm.side_b_player1_id && member.id === parseInt(matchForm.side_b_player1_id)) ||
        (matchForm.side_b_player2_id && member.id === parseInt(matchForm.side_b_player2_id)))
  );
});

// A 方球員2 的可選列表：所有活躍成員中，未被 A方球員1 選中，也未被 B 方任何一個位置選中的成員
const availableSideAPlayer2 = computed(() => {
  if (matchForm.match_type !== 'DOUBLES') return [];
  return allActiveMembers.value.filter(member =>
    member.id !== parseInt(matchForm.side_a_player1_id) && // 不能是 A1
    !((matchForm.side_b_player1_id && member.id === parseInt(matchForm.side_b_player1_id)) ||
      (matchForm.side_b_player2_id && member.id === parseInt(matchForm.side_b_player2_id))) // 也不能是 B 方的
  );
});

// B 方球員1 的可選列表：所有活躍成員中，未被 A 方任何一個位置選中的成員
const availableSideBPlayer1 = computed(() => {
  return allActiveMembers.value.filter(member =>
    member.id !== parseInt(matchForm.side_a_player1_id) &&
    (matchForm.match_type === 'SINGLES' || member.id !== parseInt(matchForm.side_a_player2_id)) // 如果是雙打，也不能是 A2
  );
});

// B 方球員2 的可選列表：所有活躍成員中，未被 A 方任何一個位置選中，也未被 B方球員1 選中的成員
const availableSideBPlayer2 = computed(() => {
  if (matchForm.match_type !== 'DOUBLES') return [];
  return allActiveMembers.value.filter(member =>
    member.id !== parseInt(matchForm.side_a_player1_id) &&
    member.id !== parseInt(matchForm.side_a_player2_id) &&
    member.id !== parseInt(matchForm.side_b_player1_id) // 也不能是 B1
  );
});


// --- 前端即時判斷勝負的邏輯 ---
function determineWinnerFrontend() {
  if (scores.value.length === 0 || !matchForm.match_format) {
    calculatedOutcome.value = '';
    matchForm.side_a_outcome = '';
    return;
  }
  const currentFormat = matchFormats.value.find(f => f.name === matchForm.match_format);
  if (!currentFormat) {
    calculatedOutcome.value = '請先選擇賽制';
    matchForm.side_a_outcome = '';
    return;
  }

  const set1 = scores.value[0]; // 假設目前只處理一盤
  if (set1.side_a === null || set1.side_b === null || set1.side_a < 0 || set1.side_b < 0) {
    calculatedOutcome.value = '請輸入有效局數';
    matchForm.side_a_outcome = '';
    return;
  }

  let sideAWinsSet = false;
  let sideBWinsSet = false;

  // 這裡的勝負判斷邏輯需要根據您的賽制規則非常仔細地實現
  // 以下是一個非常簡化的範例，您需要擴充它
  if (currentFormat.isProSet) { // 例如9局5勝 (先到5局且贏2局，或者打到8-8搶七到9)
      if (set1.side_a >= currentFormat.gamesToWinSet && set1.side_a >= set1.side_b + 2) { // gamesToWinSet 應該是5
          if (set1.side_a < currentFormat.proSetGames) sideAWinsSet = true; // 未到9局，但已滿足5勝且贏2
          else if (set1.side_a === currentFormat.proSetGames) sideAWinsSet = true; // 到達9局
      } else if (set1.side_b >= currentFormat.gamesToWinSet && set1.side_b >= set1.side_a + 2) {
          if (set1.side_b < currentFormat.proSetGames) sideBWinsSet = true;
          else if (set1.side_b === currentFormat.proSetGames) sideBWinsSet = true;
      }
      // 這裡簡化了 Pro Set 的複雜決勝局規則
  } else { // 普通盤數，例如4局或6局制
      const gamesToWin = currentFormat.gamesToWinSet; // 例如4局或6局
      const tiebreakAt = gamesToWin -1; // 例如3-3或5-5或6-6打搶七
      const finalSetTiebreakTo = currentFormat.finalSetTiebreakTo; // 搶七到幾分

      if (set1.side_a >= gamesToWin || set1.side_b >= gamesToWin) { // 至少有一方達到獲勝局數
          if (set1.side_a > set1.side_b && (set1.side_a >= gamesToWin && (set1.side_a >= set1.side_b + 2 || set1.side_a === gamesToWin +1 && set1.side_b === gamesToWin-1 && gamesToWin-1 === tiebreakAt ) ) ) {
             // 複雜的搶七判斷 (例如 7-5, 7-6(x))
             // 這裡的判斷需要非常小心，或簡化為只要分數高就贏
             if (set1.side_a > set1.side_b) sideAWinsSet = true;
          } else if (set1.side_b > set1.side_a && (set1.side_b >= gamesToWin && (set1.side_b >= set1.side_a + 2 || set1.side_b === gamesToWin+1 && set1.side_a === gamesToWin-1 && gamesToWin-1 === tiebreakAt))) {
             if (set1.side_b > set1.side_a) sideBWinsSet = true;
          }
          // 簡化判斷：如果分數都達到gamesToWin，例如6-6，則需要進一步的搶七分數
          // 如果沒有搶七，則先達到gamesToWin且贏2局者勝
          // 為簡化，這裡僅判斷是否達到gamesToWin且分數更高
          if (!sideAWinsSet && !sideBWinsSet) { // 如果還沒決出勝負
              if (set1.side_a >= gamesToWin && set1.side_a > set1.side_b) sideAWinsSet = true;
              else if (set1.side_b >= gamesToWin && set1.side_b > set1.side_a) sideBWinsSet = true;
          }
      }
  }

  if (sideAWinsSet) {
    calculatedOutcome.value = 'A方勝利';
    matchForm.side_a_outcome = 'WIN';
  } else if (sideBWinsSet) {
    calculatedOutcome.value = 'B方勝利 (A方失敗)';
    matchForm.side_a_outcome = 'LOSS';
  } else {
    calculatedOutcome.value = '比分未完成或平手';
    matchForm.side_a_outcome = '';
  }
}

watch(scores, determineWinnerFrontend, {deep: true});
watch(() => matchForm.match_format, determineWinnerFrontend);


async function handleRecordMatch() {
  // ... (前端基本驗證邏輯) ...
   if (!matchForm.side_a_outcome) {
      submitMessage.value = '請根據比分確認並選擇最終的A方比賽結果。';
      submitStatus.value = 'error';
      submitting.value = false;
      return;
  }

  submitting.value = true;
  let payload = { /* ... 準備 payload ... */ };
  // payload 中的 side_a_score_str 和 side_b_score_str 應該是最終的比分字串
  payload.side_a_score_str = scores.value.map(s => s.side_a ?? '_').join(',');
  payload.side_b_score_str = scores.value.map(s => s.side_b ?? '_').join(',');


  try {
    // 如果您還沒拆分 service，就直接用 axios
    const response = await axios.post(`${apiBaseUrl}/matches/record`, payload);
    // const response = await matchService.recordMatch(payload); // 如果已拆分
    submitMessage.value = response.data.message || '比賽結果已成功儲存！';
    submitStatus.value = 'success';
    // ... (重置表單等) ...
    setTimeout(() => router.push('/'), 1500);
  } catch (error) {
    console.error("Error recording match:", error.response || error);
    submitMessage.value = error.response?.data?.error || error.response?.data?.details || error.message || '記錄比賽時發生錯誤。';
    submitStatus.value = 'error';
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.record-match-page {
  max-width: 900px;
}

h5 {
  margin-top: 1.5rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid #eee;
}

.score-input {
  text-align: center;
}
</style>

<style scoped>
.record-match-page {
  max-width: 900px;
}

h5 {
  margin-top: 1.5rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid #eee;
}

.score-input {
  text-align: center;
}
</style>