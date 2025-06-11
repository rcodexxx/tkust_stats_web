<template>
  <div class="management-center-page container-fluid mt-4 mb-5 px-md-4">
    <n-h1 align="center" class="page-main-title mb-4"> 團隊管理中心 </n-h1>

    <n-tabs
      v-model:value="currentView"
      type="line"
      animated
      justify-content="center"
      class="mb-4 management-tabs"
    >
      <n-tab-pane name="members" tab="成員">
        <template #tab>
          <n-icon :component="PeopleIcon" size="18" class="me-1" />
          成員
        </template>
      </n-tab-pane>
      <n-tab-pane name="organizations" tab="組織">
        <template #tab>
          <n-icon :component="BuildingIcon" size="18" class="me-1" />
          組織
        </template>
      </n-tab-pane>
    </n-tabs>

    <div class="common-search-bar mb-4">
      <n-input v-model:value="searchTerm" :placeholder="searchPlaceholder" clearable size="medium">
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
  .management-center-page {
    padding-bottom: 3rem;
    background-color: var(--body-color); /* 來自 App.vue themeOverrides */
  }

  .page-main-title {
    color: var(--text-color-1); /* 來自 App.vue themeOverrides */
    font-weight: 600;
  }

  .common-search-bar {
    max-width: 450px; /* 搜尋框最大寬度 */
    /* ***** 新增/修改的樣式 ***** */
    margin-left: auto; /* 使其靠右 */
    margin-right: 0; /* 確保右側沒有額外 margin */
  }

  .management-tabs {
    border-bottom: 1px solid var(--border-color, #efefef); /* Naive UI 預設邊框色 */
  }

  .management-tabs .n-tabs-tab {
    /* 調整頁籤樣式 */
    padding: 10px 20px;
    font-size: 1rem;
  }

  .management-content-area {
    background-color: var(--card-color, #fff); /* 來自 App.vue themeOverrides */
    padding: 20px;
    border-radius: var(--border-radius, 8px); /* 來自 App.vue themeOverrides */
    box-shadow: var(--box-shadow-2); /* 來自 App.vue themeOverrides */
  }
</style>
