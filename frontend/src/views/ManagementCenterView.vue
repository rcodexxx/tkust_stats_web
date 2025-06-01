<template>
  <div class="team-management-page container-fluid mt-4 mb-5 px-md-4">
    <h1 class="mb-4 page-title text-center">團隊管理中心</h1>

    <ul class="nav nav-pills justify-content-center mb-4">
      <li class="nav-item">
        <button
            class="nav-link"
            :class="{ active: currentView === 'members' }"
            @click="setCurrentView('members')">
          <i class="bi bi-people-fill me-1"></i> 成員管理
        </button>
      </li>
      <li class="nav-item">
        <button
            class="nav-link"
            :class="{ active: currentView === 'organizations' }"
            @click="setCurrentView('organizations')">
          <i class="bi bi-building me-1"></i> 組織管理 (待開發)
        </button>
      </li>
    </ul>

    <div v-if="currentView === 'members'" class="member-management-section">
      <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center mb-3">
        <h2 class="h4 mb-2 mb-md-0">成員列表</h2>
        <div class="d-flex flex-column flex-sm-row gap-2 mt-2 mt-md-0">
          <input
              type="text"
              class="form-control form-control-sm search-input"
              v-model="searchTerm"
              placeholder="搜尋姓名、學號、組織..."
          >
          <!--          <router-link :to="{ name: 'AdminAddMember' }" class="btn btn-primary btn-sm flex-shrink-0">-->
          <!--            <i class="bi bi-person-plus-fill me-1"></i> 新增成員-->
          <!--          </router-link>-->
        </div>
      </div>

      <div v-if="loadingMembers" class="text-center my-5">
        <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;"></div>
      </div>
      <div v-if="memberError" class="alert alert-danger" role="alert">{{ memberError }}</div>

      <div class="table-responsive-custom" v-if="!loadingMembers && sortedAndFilteredMembers.length > 0">
        <table class="table table-hover table-bordered member-list-table-sticky" ref="memberTable">
          <thead class="table-dark">
          <tr>
            <th @click="sortBy('name')" class="sortable-header sticky-col sticky-left-0 col-name"
                ref="nameColumnHeader">
              名稱 (帳號)
              <i v-if="sortKey === 'name'" :class="getSortIconClass('name')"></i>
            </th>
            <th @click="sortBy('student_id')" class="sortable-header sticky-col sticky-left-1 col-student-id"
                :style="{ left: nameColumnWidth }">
              學號
              <i v-if="sortKey === 'student_id'" :class="getSortIconClass('student_id')"></i>
            </th>
            <th @click="sortBy('organization_name')" class="sortable-header col-organization">組織</th>
            <th @click="sortBy('score')" class="sortable-header col-score text-end">分數</th>
            <th @click="sortBy('mu')" class="sortable-header col-mu text-end">μ</th>
            <th @click="sortBy('user_role')" class="sortable-header col-role">角色</th>
            <th class="sticky-col sticky-right-0 col-actions text-center">操作</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="member in paginatedMembers" :key="member.id">
            <td class="sticky-col sticky-left-0 cell-name" ref="nameColumnCells">
              {{ member.name }}
              <small v-if="member.username" class="d-block text-muted">({{ member.username }})</small>
            </td>
            <td class="sticky-col sticky-left-1 cell-student-id" :style="{ left: nameColumnWidth }">
              {{ member.student_id || '-' }}
            </td>
            <td class="cell-organization">{{ member.organization_name || '-' }}</td>
            <td class="cell-score text-end">{{ member.score }}</td>
            <td class="cell-mu text-end">{{ member.mu?.toFixed(1) || '-' }}</td>
            <td class="cell-role">
        <span v-if="member.user_role" :class="getRoleBadgeClass(member.user_role)">
          {{ getRoleDisplay(member.user_role) }}
        </span>
              <span v-else class="badge bg-light text-dark">無帳號</span>
            </td>
            <td class="sticky-col sticky-right-0 cell-actions text-center">
              <button @click="editMember(member.id)" class="btn btn-sm btn-outline-primary me-1 py-0 px-1" title="編輯">
                <i class="bi bi-pencil-square"></i>
              </button>
              <button @click="confirmDeleteMember(member)" class="btn btn-sm btn-outline-danger py-0 px-1" title="刪除">
                <i class="bi bi-trash"></i>
              </button>
            </td>
          </tr>
          </tbody>
        </table>
      </div>

      <div v-if="!loadingMembers && sortedAndFilteredMembers.length === 0 && searchTerm && !memberError"
           class="alert alert-warning text-center">
        找不到符合搜尋條件 "{{ searchTerm }}" 的成員。
      </div>
      <p v-if="!loadingMembers && allFetchedMembers.length === 0 && !memberError" class="alert alert-info text-center">
        目前沒有成員資料。
      </p>

      <div v-if="totalPages > 1 && !loadingMembers" class="d-flex justify-content-center align-items-center mt-4">
        <nav aria-label="Member list pagination">
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
              <button v-if="pageNumber !== '...'" class="page-link" @click="goToPage(pageNumber)">{{
                  pageNumber
                }}
              </button>
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
      <div v-if="allFetchedMembers.length > 0 && totalPages > 0 && !loadingMembers" class="text-center mt-2 text-muted">
        <small>第 {{ currentPage }} / {{ totalPages }} 頁 (共 {{ sortedAndFilteredMembers.length }} 位符合條件成員，總
          {{ allFetchedMembers.length }} 位)</small>
      </div>
    </div>

    <div v-if="currentView === 'organizations'" class="organization-management-section">
      <h2 class="h4 mb-3">組織列表 (待實作)</h2>
      <p class="text-center text-muted p-5 border rounded">組織管理功能正在開發中...</p>
    </div>

    <div class="modal fade" id="deleteConfirmModal" tabindex="-1" aria-labelledby="deleteConfirmModalLabel"
         aria-hidden="true" ref="deleteModalElement">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="deleteConfirmModalLabel">確認刪除</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            您確定要刪除成員 "{{ memberToDelete.name }}" (ID: {{ memberToDelete.id }}) 嗎？<br>
            此操作通常會一併刪除其關聯的登入帳號，且可能無法復原！
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
            <button type="button" class="btn btn-danger" @click="executeDeleteMember">確認刪除</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {computed, onMounted, reactive, ref, watch} from 'vue';
import {useRouter} from 'vue-router';
import memberService from '../services/memberService'; // 確保路徑正確
import {Modal} from 'bootstrap';

// 匯入外部 CSS
import '../assets/css/team-management.css'; // 您的表格和 sticky 樣式

const router = useRouter();

const currentView = ref('members'); // 'members' 或 'organizations'
const allFetchedMembers = ref([]);
const loadingMembers = ref(true);
const memberError = ref(null);

const searchTerm = ref('');
const sortKey = ref('name'); // 預設按姓名排序
const sortOrders = reactive({});

const currentPage = ref(1);
const itemsPerPage = ref(10); // 每頁顯示條目數

// Sticky column 相關
const nameColumnWidth = ref('180px'); // 名稱列的預估或 CSS 設定寬度
const nameColumnHeader = ref(null); // ref for the name column header
const memberTable = ref(null); // ref for the table

// Modal 相關
const memberToDelete = ref({});
const deleteModalElement = ref(null);
let deleteModalInstance = null;

onMounted(async () => {
  await fetchMembers();
  if (deleteModalElement.value) {
    deleteModalInstance = new Modal(deleteModalElement.value);
  }
  // 初始計算第一列寬度 (如果需要動態計算)
  // await nextTick(); // 等待 DOM 更新
  // updateStickyColumnOffsets();
  // window.addEventListener('resize', updateStickyColumnOffsets);
});

// onBeforeUnmount(() => {
//   window.removeEventListener('resize', updateStickyColumnOffsets);
// });

// function updateStickyColumnOffsets() {
//   if (nameColumnHeader.value && memberTable.value?.offsetParent !== null) { // 確保表格可見
//     const firstColWidth = nameColumnHeader.value.offsetWidth;
//     nameColumnWidth.value = `${firstColWidth}px`;
//     // console.log("Name column width for sticky:", nameColWidth.value);
//   }
// }

watch(currentView, (newView) => {
  if (newView === 'members' && allFetchedMembers.value.length === 0) {
    fetchMembers();
  } else if (newView === 'members' && allFetchedMembers.value.length > 0) {
    // 如果已獲取數據，切換回來時重置分頁到第一頁
    currentPage.value = 1;
    // await nextTick();
    // updateStickyColumnOffsets();
  }
});

const initializeSortOrders = (sampleMember) => {
  if (sampleMember) {
    const keysToSort = ['name', 'student_id', 'organization_name', 'score', 'mu', 'user_role'];
    keysToSort.forEach(key => {
      if (Object.prototype.hasOwnProperty.call(sampleMember, key)) {
        sortOrders[key] = 'asc';
      }
    });
    // 設定預設排序
    if (sortOrders[sortKey.value]) {
      // sortOrders[sortKey.value] = 'asc'; // 已在上面循環中設定
    } else { // 如果預設 sortKey 不在 sampleMember 中 (不太可能)
      sortKey.value = 'name';
      if (sortOrders.name) sortOrders.name = 'asc';
    }
  }
};

async function fetchMembers() {
  loadingMembers.value = true;
  memberError.value = null;
  try {
    const response = await memberService.getAllMembers(false); // false 獲取所有成員
    allFetchedMembers.value = response.data || [];
    if (allFetchedMembers.value.length > 0) {
      initializeSortOrders(allFetchedMembers.value[0]);
    } else {
      // 清空 sortOrders 如果沒有成員
      for (const key in sortOrders) {
        delete sortOrders[key];
      }
    }
  } catch (err) {
    console.error("Error fetching members for mngmt:", err.response || err);
    memberError.value = err.response?.data?.error || err.message || "無法載入成員列表。";
    allFetchedMembers.value = [];
  } finally {
    loadingMembers.value = false;
    // await nextTick();
    // updateStickyColumnOffsets(); // 數據載入後更新 sticky 偏移
  }
}

const filteredMembers = computed(() => {
  if (!allFetchedMembers.value) return [];
  const term = searchTerm.value.toLowerCase().trim();
  if (!term) {
    return allFetchedMembers.value;
  }
  return allFetchedMembers.value.filter(member => {
    return (
        member.name?.toLowerCase().includes(term) ||
        (member.username && member.username.toLowerCase().includes(term)) ||
        (member.student_id && member.student_id.toLowerCase().includes(term)) ||
        (member.organization_name && member.organization_name.toLowerCase().includes(term)) ||
        (member.user_role && getRoleDisplay(member.user_role).toLowerCase().includes(term)) // 搜尋中文角色名
    );
  });
});

const sortedAndFilteredMembers = computed(() => {
  if (!filteredMembers.value) return [];
  const key = sortKey.value;
  if (!key || typeof sortOrders[key] === 'undefined') return filteredMembers.value;

  const orderMultiplier = sortOrders[key] === 'asc' ? 1 : -1;

  return [...filteredMembers.value].sort((a, b) => {
    let valA = a[key];
    let valB = b[key];

    if (valA == null && valB == null) return 0;
    if (valA == null) return 1 * orderMultiplier;
    if (valB == null) return -1 * orderMultiplier;

    if (key === 'user_role') { // 如果按角色排序，比較其中文顯示
      valA = getRoleDisplay(valA);
      valB = getRoleDisplay(valB);
    }

    if (typeof valA === 'string' && typeof valB === 'string') {
      return valA.localeCompare(valB, 'zh-Hant-TW') * orderMultiplier;
    }
    if (typeof valA === 'number' && typeof valB === 'number') {
      return (valA - valB) * orderMultiplier;
    }

    // 備用比較
    const strA = String(valA).toLowerCase();
    const strB = String(valB).toLowerCase();
    if (strA < strB) return -1 * orderMultiplier;
    if (strA > strB) return 1 * orderMultiplier;
    return 0;
  });
});

// 分頁邏輯
const totalPages = computed(() => Math.ceil(sortedAndFilteredMembers.value.length / itemsPerPage.value) || 1);

const paginatedMembers = computed(() => {
  if (!sortedAndFilteredMembers.value || sortedAndFilteredMembers.value.length === 0) return [];
  const startIndex = (currentPage.value - 1) * itemsPerPage.value;
  const endIndex = startIndex + itemsPerPage.value;
  return sortedAndFilteredMembers.value.slice(startIndex, endIndex);
});

function setCurrentView(view) {
  currentView.value = view;
  currentPage.value = 1; // 切換視圖時重置分頁
}

function nextPage() {
  if (currentPage.value < totalPages.value) currentPage.value++;
}

function prevPage() {
  if (currentPage.value > 1) currentPage.value--;
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

  const delta = 1; // 當前頁左右各顯示1個頁碼
  const range = [];
  const rangeWithDots = [];
  let l;

  for (let i = 1; i <= total; i++) {
    if (i === 1 || i === total || (i >= current - delta && i <= current + delta)) {
      range.push(i);
    }
  }
  // 去重並排序，確保順序正確且無重複（例如當 current 靠近首尾時）
  const uniqueSortedRange = [...new Set(range)].sort((a, b) => a - b);

  uniqueSortedRange.forEach((i) => {
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

function sortBy(key) {
  if (sortKey.value === key) {
    sortOrders[key] = sortOrders[key] === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    // 當切換到新的排序列時，預設為升序
    // sortOrders[key] = 'asc'; // 已在 initializeSortOrders 或下面邏輯中處理
    // 保留其他列的排序狀態，只改變當前點擊列
    if (typeof sortOrders[key] === 'undefined') { // 如果是第一次點擊此列排序
      sortOrders[key] = 'asc';
    } else { // 如果不是第一次，則切換
      sortOrders[key] = sortOrders[key] === 'asc' ? 'desc' : 'asc';
    }
  }
  currentPage.value = 1; // 排序後回到第一頁
}

function getSortIconClass(key) {
  if (sortKey.value !== key) return 'bi bi-arrow-down-up text-muted-light opacity-50';
  return sortOrders[key] === 'asc' ? 'bi bi-sort-up text-white' : 'bi bi-sort-down text-white';
}

function getRoleBadgeClass(roleName) {
  if (roleName === 'ADMIN') return 'badge bg-danger';
  if (roleName === 'CADRE') return 'badge bg-warning text-dark';
  if (roleName === 'PLAYER') return 'badge bg-info text-dark';
  return 'badge bg-secondary';
}

function getRoleDisplay(roleName) {
  if (roleName === 'ADMIN') return '管理員';
  if (roleName === 'CADRE') return '幹部';
  if (roleName === 'PLAYER') return '隊員';
  return roleName || 'N/A';
}

function editMember(memberId) {
  router.push({name: 'AdminEditMember', params: {id: memberId}});
}

function confirmDeleteMember(member) {
  memberToDelete.value = member;
  if (deleteModalInstance) {
    deleteModalInstance.show();
  }
}

async function executeDeleteMember() {
  if (!memberToDelete.value.id) return;
  // ... (之前的刪除邏輯，使用 submitMessage 和 submitStatus)
  try {
    await memberService.deleteMember(memberToDelete.value.id);
    alert(`成員 ${memberToDelete.value.name} 已成功刪除。`);
    fetchMembers();
  } catch (err) { /* ... */
  } finally { /* ... */
  }
}

// submitMessage and submitStatus are now only for delete confirmation feedback in this context
const submitMessage = ref('');
const submitStatus = ref('');

</script>

<style scoped>
/* 確保匯入了 team-management-table.css */
.search-input {
  max-width: 100%; /* 手機上滿寬 */
}

@media (min-width: 576px) {
  /* sm 及以上 */
  .search-input {
    max-width: 320px;
  }
}

.table-responsive-custom {
  /* 樣式已移至 team-management-table.css */
}

/* 其他特定於此視圖的樣式 */
.nav-pills .nav-link {
  border: 1px solid transparent;
}

.nav-pills .nav-link:not(.active):hover {
  border-color: #0d6efd; /* 淺藍色邊框 */
  background-color: transparent;
}
</style>