<template>
  <div class="leaderboard-page pa-md-4">
    <div class="leaderboard-header mb-4">
      <n-h1 align="center" class="page-main-title">
        <n-icon :component="RankingIcon" size="32" style="vertical-align: -5px; margin-right: 10px;"/>
        排行榜
      </n-h1>
      <!--      <n-space justify="center" class="mt-3 mb-4"-->
      <!--               v-if="authStore.isAuthenticated && (authStore.isCadre || authStore.isAdmin)">-->
      <!--        <router-link :to="{name: 'RecordMatch'}" v-slot="{ navigate }">-->
      <!--          <n-button type="primary" strong round @click="navigate">-->
      <!--            <template #icon>-->
      <!--              <n-icon :component="PencilIcon"/>-->
      <!--            </template>-->
      <!--            記錄比賽結果-->
      <!--          </n-button>-->
      <!--        </router-link>-->
      <!--      </n-space>-->
    </div>

    <div class="leaderboard-content-wrapper">
      <n-spin :show="loading" size="large">
        <template #description>排行榜載入中...</template>
        <div v-if="!loading && error" class="mt-4">
          <n-alert title="錯誤" type="error" closable @close="error = null">
            載入排行榜時發生錯誤: {{ error }}
          </n-alert>
        </div>

        <div v-if="!loading && !error">
          <n-empty
              v-if="allMembersWithRank.length === 0"
              description="目前排行榜尚無資料，快去記錄第一場比賽吧！"
              class="py-5"
              size="huge"
          />

          <div class="leaderboard-list-naive" v-if="paginatedMembers.length > 0">
            <div class="leaderboard-entry-naive leaderboard-header-row-naive d-none d-md-flex">
              <div class="entry-rank">#</div>
              <div class="entry-player">球員 / 組織</div>
              <div class="entry-record">勝 - 敗</div>
              <div class="entry-score">分數</div>
            </div>

            <n-list hoverable clickable class="leaderboard-cards-list">
              <n-list-item v-for="(member) in paginatedMembers" :key="member.id">
                <n-card :class="['leaderboard-card-entry', getRankHighlightClass(member.rank)]" hoverable>
                  <div class="leaderboard-card-content">
                    <div class="entry-rank">
                      <span v-if="member.rank <= 3 && member.rank > 0" class="rank-icon-wrapper">
                        <n-icon :component="getRankIconComponent(member.rank)" :size="28"
                                :color="getRankIconColor(member.rank)"/>
                      </span>
                      <span v-else class="rank-number">{{ member.rank }}</span>
                    </div>

                    <div class="entry-details-middle">
                      <div class="entry-player">
                        <div class="player-name">{{ member.display_name || member.name }}</div>
                        <div class="player-org text-muted" v-if="member.organization_name">
                          {{ member.organization_name }}
                        </div>
                      </div>
                      <div class="entry-record">
                        <span class="wins">{{ member.wins }}</span> - <span class="losses">{{ member.losses }}</span>
                      </div>
                    </div>

                    <div class="entry-score">
                      <span class="score-number" :style="{ color: getScoreColor(member.rank) }">
                        {{ member.score }}
                      </span>
                      <span class="score-label"></span>
                    </div>
                  </div>
                </n-card>
              </n-list-item>
            </n-list>
          </div>
        </div>

        <div v-if="totalPages > 1 && !loading" class="d-flex justify-content-center mt-4 pt-2">
          <n-pagination
              v-model:page="currentPage"
              :item-count="allMembersWithRank.length"
              v-model:page-size="itemsPerPage"
              :page-sizes="[10, 20, 30, 50]"
              show-size-picker
              show-quick-jumper
          >
            <template #prefix="{ itemCount }">
              共 {{ itemCount }} 位球員
            </template>
          </n-pagination>
        </div>
        <div v-if="allMembersWithRank.length > 0 && totalPages <=1 && !loading" class="text-center mt-3 text-muted">
          <small>共 {{ allMembersWithRank.length }} 位球員</small>
        </div>
      </n-spin>
    </div>
  </div>
</template>

<script setup>
import {computed, onMounted, ref} from 'vue';
import {useAuthStore} from '@/stores/authStore';
import apiClient from "@/services/apiClient.js";
import {NAlert, NCard, NEmpty, NH1, NIcon, NList, NListItem, NPagination, NSpin} from 'naive-ui';
import {
  Medal as Rank3Icon,
  PodiumOutline as RankingIcon,
  ShieldSharp as Rank2Icon,
  TrophySharp as Rank1Icon,
} from '@vicons/ionicons5';

import '../assets/css/leaderboard.css';

const authStore = useAuthStore();
const allMembersWithRank = ref([]);
const loading = ref(true);
const error = ref(null);
const currentPage = ref(1);
const itemsPerPage = ref(10);
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

onMounted(async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await apiClient.get('/members', {
      params: {
        view: 'leaderboard'
      }
    });
    if (response && Array.isArray(response.data)) {
      // 後端已按分數排序，前端直接根據順序賦予 rank
      allMembersWithRank.value = response.data.map((member, index) => ({
        ...member,
        rank: index + 1
      }));
    } else {
      console.error("LeaderboardView: API response data is not an array or is missing!", response.data);
      error.value = 'API 回應數據格式不正確。';
      allMembersWithRank.value = [];
    }
  } catch (e) {
    error.value = e.response?.data?.error || e.message || '無法獲取排行榜數據';
    console.error("API請求錯誤:", e.response || e);
    allMembersWithRank.value = [];
  } finally {
    loading.value = false;
  }
});

const totalPages = computed(() => {
  if (!allMembersWithRank.value) return 0;
  return Math.ceil(allMembersWithRank.value.length / itemsPerPage.value) || 1;
});

const paginatedMembers = computed(() => {
  if (!allMembersWithRank.value || allMembersWithRank.value.length === 0) return [];
  const startIndex = (currentPage.value - 1) * itemsPerPage.value;
  const endIndex = startIndex + itemsPerPage.value;
  return allMembersWithRank.value.slice(startIndex, endIndex);
});

// 這些函數依賴 member.rank，現在可以正常工作
function getRankHighlightClass(memberRank) {
  if (memberRank === 1) return 'rank-card-first';
  if (memberRank === 2) return 'rank-card-second';
  if (memberRank === 3) return 'rank-card-third';
  return 'rank-card-other';
}

function getRankIconComponent(memberRank) {
  if (memberRank === 1) return Rank1Icon;
  if (memberRank === 2) return Rank2Icon;
  if (memberRank === 3) return Rank3Icon;
  return null;
}

function getRankIconColor(memberRank) { // 這是給圖標用的顏色
  if (memberRank === 1) return '#FFD700'; // 金色
  if (memberRank === 2) return '#C0C0C0'; // 銀色
  if (memberRank === 3) return '#CD7F32'; // 銅色
  return undefined;
}

const goldScoreColor = '#B8860B';
const silverScoreColor = '#696969';
const bronzeScoreColor = '#8B4513';
const defaultScoreColor = '#1f2937';

function getScoreColor(rank) {
  if (rank === 1) return goldScoreColor;
  if (rank === 2) return silverScoreColor;
  if (rank === 3) return bronzeScoreColor;
  return defaultScoreColor;
}
</script>