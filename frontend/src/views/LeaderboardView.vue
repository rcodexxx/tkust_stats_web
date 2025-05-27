// frontend/src/views/LeaderboardView.vue
<template>
  <div class="leaderboard-page-wrapper">
    <div class="leaderboard-header container pt-4 pb-3">
      <h1 class="text-center page-title">積分排行榜</h1>
    </div>

    <div class="leaderboard-content container">
      <div v-if="loading" class="d-flex justify-content-center my-5">
        <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>
      <div v-if="error" class="alert alert-danger shadow-sm my-4" role="alert">
        <i class="bi bi-exclamation-triangle-fill me-2"></i>載入排行榜時發生錯誤: {{ error }}
      </div>

      <div v-if="!loading && !error">
        <div v-if="paginatedMembers.length === 0 && allMembersWithRank.length > 0" class="alert alert-info text-center my-4">
          此頁無資料。
        </div>
        <div v-if="allMembersWithRank.length === 0" class="alert alert-light text-center my-4 text-muted">
          目前排行榜尚無資料，快去記錄第一場比賽吧！
        </div>

        <div class="leaderboard-list" v-if="paginatedMembers.length > 0">
          <div
            v-for="(member, indexOnPage) in paginatedMembers"
            :key="member.id"
            class="leaderboard-entry"
            :class="getRankHighlightClass(member.rank)"
          >
            <div class="entry-rank">
              <span v-if="member.rank <= 3 && member.rank > 0" class="rank-icon-wrapper">
                <i :class="getRankIconClass(member.rank)"></i>
              </span>
              <span v-else>{{ member.rank }}</span>
            </div>
            <div class="entry-player">
              <div class="player-name">{{ member.name }}</div>
              <div class="player-org text-muted" v-if="member.organization_name">
                {{ member.organization_name }}
              </div>
            </div>
            <div class="entry-score">
              {{ member.score }} <span class="score-label">分</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="totalPages > 1" class="d-flex justify-content-center align-items-center mt-4 pt-3">
        <nav aria-label="Leaderboard pagination">
          <ul class="pagination custom-pagination mb-0">
            <li class="page-item" :class="{ disabled: currentPage === 1 }">
              <button class="page-link" @click="prevPage" :disabled="currentPage === 1" aria-label="Previous">
                <span aria-hidden="true">&laquo;</span>
              </button>
            </li>
            <li v-for="pageNumber in visiblePageNumbers"
                :key="pageNumber"
                class="page-item"
                :class="{ active: pageNumber === currentPage, disabled: pageNumber === '...' }">
              <button v-if="pageNumber !== '...'" class="page-link" @click="goToPage(pageNumber)">{{ pageNumber }}</button>
              <span v-else class="page-link dots">...</span>
            </li>
            <li class="page-item" :class="{ disabled: currentPage === totalPages }">
              <button class="page-link" @click="nextPage" :disabled="currentPage === totalPages" aria-label="Next">
                <span aria-hidden="true">&raquo;</span>
              </button>
            </li>
          </ul>
        </nav>
      </div>
      <div v-if="allMembersWithRank.length > 0 && totalPages > 1" class="text-center mt-2 text-muted">
        <small>第 {{ currentPage }} / {{ totalPages }} 頁 (共 {{ allMembersWithRank.length }} 位球員)</small>
      </div>
       <div v-if="allMembersWithRank.length > 0 && totalPages <=1 && !loading" class="text-center mt-3 text-muted">
        <small>共 {{ allMembersWithRank.length }} 位球員</small>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';
import '../assets/css/leaderboard.css';

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
    const response = await axios.get(`${apiBaseUrl}/leaderboard`);
    if (!response) {
      console.error("LeaderboardView: API response object is undefined!");
      error.value = 'API 未返回有效的回應物件。';
      allMembersWithRank.value = [];
      loading.value = false;
      return; // 提前退出
    }
    if (typeof response.data === 'undefined') {
        console.error("LeaderboardView: response.data is undefined!");
        error.value = 'API 回應中缺少 data 屬性。';
        allMembersWithRank.value = [];
        loading.value = false;
        return; // 提前退出
    }

    console.log("LeaderboardView: API response object:", response);
    console.log("LeaderboardView: response.data raw content:", response.data);
    console.log("LeaderboardView: typeof response.data:", typeof response.data);
    console.log("LeaderboardView: Array.isArray(response.data):", Array.isArray(response.data));

    let members = response.data.map(m => ({ ...m, score: Number(m.score) }))
                               .sort((a, b) => b.score - a.score);
    if (members.length > 0) {
      let rank = 1;
      members[0].rank = rank;
      for (let i = 1; i < members.length; i++) {
        if (members[i].score < members[i-1].score) {
          rank = i + 1;
        }
        members[i].rank = rank;
      }
    }
    allMembersWithRank.value = members;
  } catch (e) {
    error.value = e.response?.data?.error || e.message || '無法獲取排行榜數據';
    console.error("API請求錯誤:", e.response || e);
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

function nextPage() { if (currentPage.value < totalPages.value) currentPage.value++; }
function prevPage() { if (currentPage.value > 1) currentPage.value--; }
function goToPage(pageNumber) {
  if (pageNumber !== '...' && pageNumber >= 1 && pageNumber <= totalPages.value) {
    currentPage.value = pageNumber;
  }
}

const visiblePageNumbers = computed(() => {
  const total = totalPages.value;
  const current = currentPage.value;
  if (total <= 1) return [];
  const delta = 2; // 當前頁碼左右各顯示2個頁碼（不含當前頁）
  const range = [];
  const rangeWithDots = [];
  let l;

  range.push(1); // 總是顯示第一頁
  for (let i = Math.max(2, current - delta); i <= Math.min(total - 1, current + delta); i++) {
    range.push(i);
  }
  if (total > 1) range.push(total); // 總是顯示最後一頁（如果總頁數大於1）

  const uniqueRange = [...new Set(range)].sort((a, b) => a - b);

  uniqueRange.forEach((i) => {
    if (l) {
      if (i - l === 2) {
        rangeWithDots.push(l + 1);
      } else if (i - l > 1) {
        rangeWithDots.push('...');
      }
    }
    rangeWithDots.push(i);
    l = i;
  });
  return rangeWithDots;
});


// 根據排名給予不同的高亮 class (用於背景或邊框)
function getRankHighlightClass(memberRank) {
  if (memberRank === 1) return 'rank-first';
  if (memberRank === 2) return 'rank-second';
  if (memberRank === 3) return 'rank-third';
  return 'rank-other';
}

// 根據排名給予不同的圖示 class (如果需要圖示)
function getRankIconClass(memberRank) {
  if (memberRank === 1) return 'bi bi-trophy-fill rank-icon-first';
  if (memberRank === 2) return 'bi bi-award-fill rank-icon-second';
  if (memberRank === 3) return 'bi bi-medal-fill rank-icon-third';
  return ''; // 其他排名不顯示圖示
}
</script>