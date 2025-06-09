<template>
  <div class="record-match-page container-fluid mt-4 mb-5 px-md-4">
    <n-h1 align="center" class="page-main-title mb-4">
      <n-icon :component="ClipboardIcon" size="32" class="title-icon"/>
      記錄賽果
    </n-h1>

    <n-card :bordered="false" class="form-card">
      <n-form
          ref="formRef"
          :model="matchForm"
          :rules="formRules"
          label-placement="top"
          @submit.prevent="handleRecordMatch"
      >
        <!-- 比賽基本資訊 -->
        <n-grid :x-gap="15" :y-gap="20" cols="1 s:3" responsive="screen" align-items="start">
          <n-form-item-gi label="比賽日期" path="match_date">
            <n-date-picker
                v-model:value="matchForm.match_date_ts"
                type="date"
                placeholder="選擇比賽日期"
                style="width:100%"
            />
          </n-form-item-gi>
          <n-form-item-gi label="比賽類型" path="match_type">
            <n-select v-model:value="matchForm.match_type" :options="matchTypeOptions"/>
          </n-form-item-gi>
          <n-form-item-gi label="賽制" path="match_format">
            <n-select v-model:value="matchForm.match_format" :options="matchFormatOptions"/>
          </n-form-item-gi>
        </n-grid>

        <n-divider style="margin-top: 1.5rem; margin-bottom: 1.5rem;"/>

        <!-- 對戰視覺區塊 -->
        <n-grid cols="1 s:2" x-gap="24" y-gap="24" responsive="screen" align-items="center"
                class="match-visual-grid mb-3">
          <!-- A隊卡片 -->
          <n-gi>
            <n-card :bordered="true" :class="['team-card', matchForm.side_a_outcome === 'WIN' ? 'highlight-win' : '']">
              <n-h4 class="mb-2">A隊</n-h4>
              <!-- A隊球員選擇 -->
              <div class="player-entry">
                <n-form-item path="player1_id" :show-label="false" class="player-select-form-item">
                  <n-select
                      v-model:value="matchForm.player1_id"
                      :options="availablePlayersFor('a1')"
                      placeholder="選擇球員 1*" filterable clearable
                      label-field="name" value-field="id" class="player-select-control"
                  />
                </n-form-item>
                <div class="player-score-display">
                  <span v-if="getPlayerById(matchForm.player1_id)"
                        class="score-value">{{ getPlayerById(matchForm.player1_id).score }} <span
                      class="score-unit">分</span></span>
                  <span v-else class="score-placeholder">-</span>
                </div>
              </div>
              <div class="player-entry mt-2" v-if="matchForm.match_type === 'doubles'">
                <n-form-item path="player2_id" :show-label="false" class="player-select-form-item">
                  <n-select
                      v-model:value="matchForm.player2_id"
                      :options="availablePlayersFor('a2')"
                      placeholder="選擇球員 2*" filterable clearable
                      label-field="name" value-field="id" class="player-select-control"
                  />
                </n-form-item>
                <div class="player-score-display">
                  <span v-if="getPlayerById(matchForm.player2_id)"
                        class="score-value">{{ getPlayerById(matchForm.player2_id).score }} <span
                      class="score-unit">分</span></span>
                  <span v-else class="score-placeholder">-</span>
                </div>
              </div>
              <!-- A隊得分 -->
              <n-form-item path="a_games" :show-label="false" class="score-form-item-wrapper mt-3">
                <div class="score-input-slider-group">
                  <n-input-number
                      class="score-input-number"
                      :class="{ 'winning-score': matchForm.side_a_outcome === 'WIN' }"
                      v-model:value="matchForm.a_games"
                      :min="0" :max="scoreInputMax" placeholder="局數"
                  />
                  <n-slider
                      class="score-slider"
                      :class="{ 'winning-score-slider': matchForm.side_a_outcome === 'WIN' }"
                      v-model:value="matchForm.a_games"
                      :min="0" :max="scoreInputMax" :step="1"
                  />
                </div>
              </n-form-item>
            </n-card>
          </n-gi>

          <!-- B隊卡片 -->
          <n-gi>
            <n-card :bordered="true" :class="['team-card', matchForm.side_a_outcome === 'LOSS' ? 'highlight-win' : '']">
              <n-h4 class="mb-2">B隊</n-h4>
              <!-- B隊球員選擇 -->
              <div class="player-entry">
                <n-form-item path="player3_id" :show-label="false" class="player-select-form-item">
                  <n-select
                      v-model:value="matchForm.player3_id"
                      :options="availablePlayersFor('b3')"
                      placeholder="選擇球員 1*" filterable clearable
                      label-field="name" value-field="id" class="player-select-control"
                  />
                </n-form-item>
                <div class="player-score-display">
                  <span v-if="getPlayerById(matchForm.player3_id)"
                        class="score-value">{{ getPlayerById(matchForm.player3_id).score }} <span
                      class="score-unit"></span></span>
                  <span v-else class="score-placeholder">-</span>
                </div>
              </div>
              <div class="player-entry mt-2" v-if="matchForm.match_type === 'doubles'">
                <n-form-item path="player4_id" :show-label="false" class="player-select-form-item">
                  <n-select
                      v-model:value="matchForm.player4_id"
                      :options="availablePlayersFor('b4')"
                      placeholder="選擇球員 2*" filterable clearable
                      label-field="name" value-field="id" class="player-select-control"
                  />
                </n-form-item>
                <div class="player-score-display">
                  <span v-if="getPlayerById(matchForm.player4_id)"
                        class="score-value">{{ getPlayerById(matchForm.player4_id).score }}
                    <span class="score-unit"></span>
                  </span>
                  <span v-else class="score-placeholder">-</span>
                </div>
              </div>
              <!-- B隊得分 -->
              <n-form-item path="b_games" :show-label="false" class="score-form-item-wrapper mt-3">
                <div class="score-input-slider-group">
                  <n-input-number
                      class="score-input-number"
                      :class="{ 'winning-score': matchForm.side_a_outcome === 'LOSS' }"
                      v-model:value="matchForm.b_games"
                      :min="0" :max="scoreInputMax" placeholder="局數"
                  />
                  <n-slider
                      class="score-slider"
                      :class="{ 'winning-score-slider': matchForm.side_a_outcome === 'LOSS' }"
                      v-model:value="matchForm.b_games"
                      :min="0" :max="scoreInputMax" :step="1"
                  />
                </div>
              </n-form-item>
            </n-card>
          </n-gi>
        </n-grid>

        <n-space justify="center" class="mt-4 action-buttons">
          <n-button @click="goBack" size="large" ghost>返回排行榜</n-button>
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
import apiClient from '@/services/apiClient';
import "@/assets/css/match-record.css"
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
  NIcon,
  NInputNumber,
  NSelect,
  NSlider,
  NSpace,
  useMessage
} from 'naive-ui';
import {
  CheckmarkCircleOutline as WinIcon,
  ClipboardOutline as ClipboardIcon,
  SaveOutline as SaveIcon
} from '@vicons/ionicons5';

// --- Hooks ---
const router = useRouter();
const message = useMessage();

// --- State ---
const formRef = ref(null);
const allActiveMembers = ref([]);
const submitting = ref(false);

const matchForm = reactive({
  match_date_ts: new Date().getTime(),
  match_type: 'doubles',
  match_format: 'games_9',
  player1_id: null, player2_id: null,
  player3_id: null, player4_id: null,
  a_games: 0, b_games: 0,
  side_a_outcome: '',
  match_notes: ''
});

// --- Options & Rules ---
const matchTypeOptions = [{label: '雙打', value: 'doubles'}, {label: '單打', value: 'singles'}];
// --- 修正：為賽制選項加入 meta 資料 ---
const matchFormatOptions = [
  {label: '五局制', value: 'games_5', meta: {gamesToWin: 3}},
  {label: '七局制', value: 'games_7', meta: {gamesToWin: 4}},
  {label: '九局制', value: 'games_9', meta: {gamesToWin: 5}},
];

const formRules = {
  match_date_ts: [{type: 'number', required: true, message: '比賽日期為必填'}],
  match_type: [{required: true, message: '比賽類型為必填'}],
  match_format: [{required: true, message: '賽制為必填'}],
  player1_id: [{required: true, type: 'number', message: 'A隊球員1為必填'}],
  player3_id: [{required: true, type: 'number', message: 'B隊球員1為必填'}],
  a_games: [{required: true, type: 'number', message: 'A隊局數為必填'}],
  b_games: [{required: true, type: 'number', message: 'B隊局數為必填'}],
  player2_id: [{
    trigger: ['blur', 'change'],
    validator: (rule, value) => {
      if (matchForm.match_type === 'doubles' && !value) {
        return new Error('雙打時，A隊球員2為必填');
      }
      return true;
    }
  }],
  player4_id: [{
    trigger: ['blur', 'change'],
    validator: (rule, value) => {
      if (matchForm.match_type === 'doubles' && !value) {
        return new Error('雙打時，B隊球員2為必填');
      }
      return true;
    }
  }],
};

// --- Computed Properties ---
const scoreInputMax = computed(() => {
  const selectedFormat = matchFormatOptions.find(opt => opt.value === matchForm.match_format);
  return selectedFormat?.meta?.gamesToWin ?? 9;
});

const matchResultDisplay = computed(() => {
  if (matchForm.side_a_outcome === 'WIN') return 'A隊 勝利！';
  if (matchForm.side_a_outcome === 'LOSS') return 'B隊 勝利！';
  return null;
});

const getPlayerById = (playerId) => {
  if (!playerId) return null;
  return allActiveMembers.value.find(m => m.id === playerId);
};

const availablePlayersFor = (slotKey) => {
  const selectedIds = new Set([
    matchForm.player1_id, matchForm.player2_id,
    matchForm.player3_id, matchForm.player4_id
  ].filter(id => id != null));

  let currentId = null;
  if (slotKey === 'a1') currentId = matchForm.player1_id;
  if (slotKey === 'a2') currentId = matchForm.player2_id;
  if (slotKey === 'b3') currentId = matchForm.player3_id;
  if (slotKey === 'b4') currentId = matchForm.player4_id;

  return allActiveMembers.value.filter(m => !selectedIds.has(m.id) || m.id === currentId);
};

// --- Watchers ---
// --- 修正：監聽分數變化以計算勝負 ---
watch([() => matchForm.a_games, () => matchForm.b_games, () => matchForm.match_format], () => {
  const gamesToWin = scoreInputMax.value;
  const gamesA = matchForm.a_games;
  const gamesB = matchForm.b_games;

  // 只有當其中一方達到勝利局數，且分數不相同時，才確定勝負
  if (gamesA === gamesToWin && gamesA > gamesB) {
    matchForm.side_a_outcome = 'WIN';
  } else if (gamesB === gamesToWin && gamesB > gamesA) {
    matchForm.side_a_outcome = 'LOSS';
  } else {
    matchForm.side_a_outcome = '';
  }
}, {deep: true});

watch(() => matchForm.match_type, (newType) => {
  if (newType === 'singles') {
    matchForm.player2_id = null;
    matchForm.player4_id = null;
  }
});

// --- Methods ---
async function fetchActiveMembers() {
  try {
    const response = await apiClient.get('/members', {params: {all: 'false'}});
    allActiveMembers.value = response.data.map(m => ({
      id: m.id,
      name: m.name || m.display_name,
      score: m.score,
    }));
  } catch (error) {
    message.error("獲取球員列表失敗。");
  }
}

const handleRecordMatch = () => {
  formRef.value?.validate(async (validationErrors) => {
    if (validationErrors) {
      message.error("請修正表單中的錯誤。");
      return;
    }
    // --- 修正：根據新的賽制規則進行驗證 ---
    const gamesToWin = scoreInputMax.value;
    if (matchForm.a_games < gamesToWin && matchForm.b_games < gamesToWin) {
      message.error(`比賽尚未結束，需要有一方達到 ${gamesToWin} 局才能儲存。`);
      return;
    }
    if (matchForm.a_games === matchForm.b_games) {
      message.error("比賽分數不能相同，請確認勝負。");
      return;
    }

    submitting.value = true;
    try {
      const formatDate = (timestamp) => {
        if (!timestamp) return null;
        const date = new Date(timestamp);
        return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
      };

      const payload = {
        match_date: formatDate(matchForm.match_date_ts),
        match_type: matchForm.match_type,
        match_format: matchForm.match_format,
        player1_id: matchForm.player1_id,
        player2_id: matchForm.match_type === 'doubles' ? matchForm.player2_id : null,
        player3_id: matchForm.player3_id,
        player4_id: matchForm.match_type === 'doubles' ? matchForm.player4_id : null,
        a_games: matchForm.a_games,
        b_games: matchForm.b_games,
        match_notes: matchForm.match_notes || null
      };

      const response = await apiClient.post('/match-records', payload);
      message.success(response.data.message || '比賽結果已成功儲存！');

      setTimeout(() => {
        router.push({name: 'Leaderboard'});
      }, 1500);
    } catch (err) {
      const errorData = err.response?.data;
      if (errorData?.details) {
        let errorMsg = "輸入數據有誤：\n" + Object.values(errorData.details).flat().join('\n');
        message.error(errorMsg, {duration: 7000, closable: true});
      } else {
        message.error(errorData?.message || "提交失敗，請稍後再試。");
      }
    } finally {
      submitting.value = false;
    }
  });
};

onMounted(fetchActiveMembers);

// --- UI Helpers ---
function getWinnerTagType() {
  return 'success';
}

function getWinnerIcon() {
  return WinIcon;
}

function goBack() {
  router.push({name: 'ManagementCenter'});
}
</script>

<style scoped>
/* 您的 CSS 樣式保持不變 */

</style>
