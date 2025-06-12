<template>
  <div class="management-center-page">
    <n-h1 align="center" class="page-main-title"> 團隊管理中心 </n-h1>

    <n-tabs
      v-model:value="currentView"
      type="line"
      animated
      justify-content="center"
      class="management-tabs"
    >
      <n-tab-pane name="members" tab="成員">
        <template #tab>
          <n-icon :component="PeopleIcon" size="18" class="tab-icon" />
          成員
        </template>
      </n-tab-pane>
      <n-tab-pane name="organizations" tab="組織">
        <template #tab>
          <n-icon :component="BuildingIcon" size="18" class="tab-icon" />
          組織
        </template>
      </n-tab-pane>
    </n-tabs>

    <div class="search-section">
      <n-input v-model:value="searchTerm" :placeholder="searchPlaceholder" clearable size="medium" class="search-input">
        <template #prefix>
          <n-icon :component="SearchIcon" />
        </template>
      </n-input>
    </div>

    <div class="management-content-area">
      <MemberManagement v-if="currentView === 'members'" :search-term-prop="searchTerm" />
      <OrganizationManagement
        v-if="currentView === 'organizations'"
        :search-term-prop="searchTerm"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { NH1, NIcon, NInput, NTabPane, NTabs } from 'naive-ui'
import {
  BusinessOutline as BuildingIcon,
  PeopleOutline as PeopleIcon,
  SearchOutline as SearchIcon
} from '@vicons/ionicons5'
import MemberManagement from '@/components/management/MemberManagement.vue'
import OrganizationManagement from '@/components/management/OrganizationManagement.vue'

const currentView = ref('members') // 預設顯示成員管理
  const searchTerm = ref('')

  const searchPlaceholder = computed(() => {
    if (currentView.value === 'members') {
      return '搜尋成員...'
    } else if (currentView.value === 'organizations') {
      return '搜尋組織...'
    }
    return '搜尋...'
  })
</script>

<style scoped>
/* === 品牌色彩系統（任天堂風格紅色） === */
:root {
  --brand-primary: #e53e3e;
  --brand-secondary: #c53030;
  --brand-light: #fed7d7;
  --brand-dark: #9b2c2c;
}

/* === 主要容器 === */
.management-center-page {
  max-width: 1600px;
  margin: 0 auto;
  padding: 2rem;
  background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
  min-height: 100vh;
}

/* === 頁面標題 === */
.page-main-title {
  font-weight: 700;
  font-size: 2.5rem;
  margin-bottom: 2rem;
  color: #2c3e50;
  background: linear-gradient(135deg, var(--brand-primary), var(--brand-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  position: relative;
}

.page-main-title::after {
  content: '';
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 120px;
  height: 4px;
  background: linear-gradient(90deg, var(--brand-primary), var(--brand-secondary));
  border-radius: 2px;
}

/* === 標籤頁樣式 === */
.management-tabs {
  margin-bottom: 2rem;
}

.management-tabs .n-tabs-nav {
  background: white;
  border-radius: 12px;
  padding: 0.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
}

.management-tabs .n-tabs-tab {
  padding: 0.75rem 2rem;
  font-size: 1rem;
  font-weight: 600;
  color: #64748b;
  border-radius: 8px;
  transition: all 0.2s ease;
  margin: 0 0.25rem;
}

.management-tabs .n-tabs-tab:hover {
  color: var(--brand-primary);
  background-color: #f8fafc;
}

.management-tabs .n-tabs-tab--active {
  color: var(--brand-primary);
  background-color: var(--brand-light);
  font-weight: 700;
}

.management-tabs .n-tabs-tab-pad {
  display: none;
}

.management-tabs .n-tabs-bar {
  display: none;
}

.tab-icon {
  margin-right: 0.5rem;
}

/* === 搜尋區域 === */
.search-section {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  display: flex;
  justify-content: flex-end;
}

.search-input {
  max-width: 400px;
  width: 100%;
}

.search-input .n-input__input-el {
  border-radius: 8px;
}

.search-input .n-input--focus {
  border-color: var(--brand-primary);
  box-shadow: 0 0 0 2px rgba(229, 62, 62, 0.1);
}

/* === 內容區域 === */
.management-content-area {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  animation: fadeIn 0.3s ease-out;
}

/* === 表格樣式統一（應用到子組件） === */
.management-content-area :deep(.n-data-table) {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

.management-content-area :deep(.n-data-table .n-data-table-thead .n-data-table-th) {
  background-color: #f8fafc;
  font-weight: 600;
  color: #374151;
  font-size: 0.875rem;
  padding: 1rem 0.75rem;
  border-bottom: 1px solid #e5e7eb;
}

.management-content-area :deep(.n-data-table .n-data-table-tbody .n-data-table-tr) {
  transition: background-color 0.2s ease;
  border-bottom: 1px solid #f1f5f9;
}

.management-content-area :deep(.n-data-table .n-data-table-tbody .n-data-table-tr:hover) {
  background-color: #f8fafc;
}

.management-content-area :deep(.n-data-table .n-data-table-tbody .n-data-table-td) {
  padding: 0.875rem 0.75rem;
  font-weight: 500;
  color: #374151;
}

/* === 按鈕樣式統一 === */
.management-content-area :deep(.n-button--primary) {
  background-color: var(--brand-primary);
  border-color: var(--brand-primary);
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.management-content-area :deep(.n-button--primary:hover) {
  background-color: var(--brand-secondary);
  border-color: var(--brand-secondary);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(229, 62, 62, 0.3);
}

.management-content-area :deep(.n-button) {
  border-radius: 8px;
  transition: all 0.2s ease;
}

.management-content-area :deep(.n-button:hover) {
  transform: translateY(-1px);
}

/* === 操作按鈕區域 === */
.management-content-area :deep(.table-actions-header) {
  margin-bottom: 1.5rem;
  display: flex;
  justify-content: flex-end;
}

/* === 錯誤和空狀態樣式 === */
.management-content-area :deep(.n-alert--error) {
  border-radius: 8px;
  border: 1px solid #fecaca;
  background-color: #fef2f2;
}

.management-content-area :deep(.n-empty) {
  padding: 2rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px dashed #cbd5e1;
  margin: 1rem 0;
}

/* === 載入動畫 === */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* === 響應式設計 === */
@media (max-width: 1200px) {
  .management-center-page {
    padding: 1.5rem;
  }
}

@media (max-width: 768px) {
  .management-center-page {
    padding: 1rem;
  }

  .page-main-title {
    font-size: 2rem;
    margin-bottom: 1.5rem;
  }

  .management-tabs .n-tabs-tab {
    padding: 0.625rem 1.5rem;
    font-size: 0.9rem;
  }

  .search-section {
    padding: 1rem;
  }

  .search-input {
    max-width: none;
  }

  .management-content-area {
    padding: 1.5rem;
  }

  .management-content-area :deep(.n-data-table .n-data-table-thead .n-data-table-th) {
    font-size: 0.75rem;
    padding: 0.75rem 0.5rem;
  }

  .management-content-area :deep(.n-data-table .n-data-table-tbody .n-data-table-td) {
    padding: 0.75rem 0.5rem;
    font-size: 0.875rem;
  }
}

@media (max-width: 480px) {
  .page-main-title {
    font-size: 1.75rem;
  }

  .management-tabs .n-tabs-tab {
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
  }

  .tab-icon {
    margin-right: 0.25rem;
  }

  .search-section {
    padding: 0.75rem;
  }

  .management-content-area {
    padding: 1rem;
  }
}
</style>