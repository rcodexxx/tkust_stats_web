// frontend/src/views/LeaderboardView.vue
<template>
  <div class="leaderboard-page container mt-4 mb-5">
    <h1 class="mb-4 text-center display-5 fw-bold page-title">球隊排行榜</h1>

    <div class="d-flex justify-content-center mb-4">
      <router-link to="/match/record" class="btn btn-lg btn-success shadow-sm custom-btn-green">
        <i class="bi bi-plus-circle-fill me-2"></i>記錄新的比賽結果
      </router-link>
    </div>

    <div v-if="loading" class="d-flex justify-content-center mt-5">
      <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
    <div v-if="error" class="alert alert-danger shadow-sm" role="alert">
      <i class="bi bi-exclamation-triangle-fill me-2"></i>載入排行榜時發生錯誤: {{ error }}
    </div>

    <div v-if="!loading && !error" class="leaderboard-container">
      <div v-if="allMembersWithRank.length === 0" class="alert alert-info m-3 text-center">
        目前排行榜尚無資料。
      </div>

      <div v-if="currentPage === 1 && paginatedMembers.length > 0 && paginatedMembers[0].rank === 1"
           class="leaderboard-card-first-place mb-4">
        <div class="banner">
          <img src="/trophy.svg" alt="Trophy" class="trophy-icon"> </div>
        <div class="first-place-details">
          <h2 class="name">{{ paginatedMembers[0].name }}</h2>
          <p class="score">分數: <strong>{{ paginatedMembers[0].score }}</strong></p>
          <p class="info"><small>組織: {{ paginatedMembers[0].organization_name || '-' }}</small></p>
          <p class="info"><small>習慣位置: {{ paginatedMembers[0].position || '-' }}</small></p>
        </div>
        <div class="ribbon">
          <span>#{{ paginatedMembers[0].rank }}</span>
        </div>
      </div>

      <div class="card shadow-lg leaderboard-card"
           :class="{'mt-4': !(currentPage === 1 && paginatedMembers.length > 0 && paginatedMembers[0].rank === 1) }"
           v-if="paginatedMembers.length > 0">
        <div class="card-body p-0">
          <table class="table table-hover table-striped align-middle mb-0" id="leaderboardTable">
            <thead class="table-dark text-uppercase">
              <tr>
                <th scope="col" class="text-center rank-col">#</th>
                <th scope="col" class="player-col">球員名稱</th>
                <th scope="col" class="organization-col">組織</th>
                <th scope="col" class="text-center score-col">分數</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(member, index) in paginatedMembers"
                  :key="member.id"
                  :class="getRankClass(member.rank)"
                  v-if="!(currentPage === 1 && index === 0 && member.rank === 1)">
                <td class="text-center fw-bold rank-col">
                  <span v-if="member.rank <= 3 && member.rank > 0" class="rank-icon">
                    <i :class="getRankIcon(member.rank)"></i>
                  </span>
                  <span v-else>{{ member.rank }}</span>
                </td>
                <td class="player-col">
                  <div class="d-flex align-items-center">
                    <div>
                      <span class="fw-bold player-name">{{ member.name }}</span>
                      <small v-if="member.student_id" class="d-block text-muted">{{ member.student_id }}</small>
                    </div>
                  </div>
                </td>
                <td class="organization-col">{{ member.organization_name || '-' }}</td>
                <td class="text-center score-col">
                  <span class="badge bg-primary rounded-pill fs-6 score-badge">{{ member.score }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-if="totalPages > 1" class="d-flex justify-content-center align-items-center mt-4 pt-3 border-top">
      <nav aria-label="Leaderboard pagination">
        <ul class="pagination mb-0">
          <li class="page-item" :class="{ disabled: currentPage === 1 }">
            <button class="page-link" @click="prevPage" :disabled="currentPage === 1">
              <i class="bi bi-chevron-left"></i> 上一頁
            </button>
          </li>
          <li v-for="pageNumber in visiblePageNumbers"
              :key="pageNumber"
              class="page-item"
              :class="{ active: pageNumber === currentPage, disabled: pageNumber === '...' }">
            <button v-if="pageNumber !== '...'" class="page-link" @click="goToPage(pageNumber)">{{ pageNumber }}</button>
            <span v-else class="page-link">...</span>
          </li>
          <li class="page-item" :class="{ disabled: currentPage === totalPages }">
            <button class="page-link" @click="nextPage" :disabled="currentPage === totalPages">
              下一頁 <i class="bi bi-chevron-right"></i>
            </button>
          </li>
        </ul>
      </nav>
    </div>
    <div v-if="allMembersWithRank.length > 0 && totalPages <=1" class="text-center mt-3 text-muted">
      共 {{ allMembersWithRank.length }} 位球員
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';
import '../assets/css/leaderboard.css'; // 匯入外部 CSS

const allMembersWithRank = ref([]);
const loading = ref(true);
const error = ref(null);

const currentPage = ref(1);
const itemsPerPage = ref(10); // 每頁顯示10位

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

onMounted(async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await axios.get(`${apiBaseUrl}/leaderboard`);
    let members = response.data.map(m => ({ ...m, score: Number(m.score) }))
                               .sort((a, b) => b.score - a.score); // 確保按分數降序排序

    // 計算排名 (並列排名，跳過名次)
    if (members.length > 0) {
      let rank = 1;
      members[0].rank = rank;
      for (let i = 1; i < members.length; i++) {
        if (members[i].score < members[i-1].score) {
          // 分數不同，名次等於當前是第幾個人 (i是索引，所以 i+1 是第幾個人)
          rank = i + 1;
        }
        // 如果分數相同，rank 保持與前一名相同
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

function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++;
  }
}

function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--;
  }
}

function goToPage(pageNumber) {
  if (pageNumber !== '...' && pageNumber >= 1 && pageNumber <= totalPages.value) {
    currentPage.value = pageNumber;
  }
}

const visiblePageNumbers = computed(() => {
  const total = totalPages.value;
  const current = currentPage.value;
  if (total <= 1) return [];

  const delta = 1;
  const
   left = current - delta;
  const right = current + delta + 1;
  const range = [];
  const rangeWithDots = [];
  let l;

  for (let i = 1; i <= total; i++) {
    if (i === 1 || i === total || (i >= left && i < right)) {
      range.push(i);
    }
  }

  range.forEach((i) => {
    if (l) {
      if (i - l === 2) {
        rangeWithDots.push(l + 1);
      } else if (i - l !== 1) {
        rangeWithDots.push('...');
      }
    }
    rangeWithDots.push(i);
    l = i;
  });

  return rangeWithDots;
});

function getRankClass(memberRank) {
  if (memberRank === 1) return 'table-gold rank-1';
  if (memberRank === 2) return 'table-silver rank-2';
  if (memberRank === 3) return 'table-bronze rank-3';
  return '';
}

function getRankIcon(memberRank) {
  if (memberRank === 1) return 'bi bi-trophy-fill';
  if (memberRank === 2) return 'bi bi-award-fill';
  if (memberRank === 3) return 'bi bi-medal-fill';
  return '';
}
</script>