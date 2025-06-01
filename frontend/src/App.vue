<template>
  <n-config-provider :theme-overrides="themeOverrides" :locale="zhTW" :date-locale="dateZhTW" style="height: 100%;">
    <n-message-provider>
      <n-notification-provider>
        <n-dialog-provider>
          <n-layout style="height: 100vh;" :native-scrollbar="false">
            <n-layout-header bordered class="app-header">
              <div class="navbar-content">
                <router-link to="/" class="navbar-brand-custom">
                  TKU Soft Tennis Web
                </router-link>

                <n-menu
                    v-model:value="activeMenuKey"
                    mode="horizontal"
                    :options="menuOptions"
                    responsive
                    class="main-nav-menu"
                />

                <div class="user-actions-area">
                  <template v-if="authStore.isAuthenticated">
                    <n-dropdown
                        trigger="hover"
                        :options="userDropdownOptions"
                        @select="handleUserDropdownSelect"
                        placement="bottom-end"
                    >
                      <n-button quaternary class="user-display-button">
                        <template #icon>
                          <n-icon :component="PersonCircleOutlineIcon"/>
                        </template>
                        {{ authStore.userDisplayName }}
                        <small v-if="authStore.userRole" class="user-role-display-badge">
                          ({{ getRoleDisplay(authStore.userRole) }})
                        </small>
                        <n-icon size="14" class="dropdown-arrow-icon">
                          <ChevronDownIcon/>
                        </n-icon>
                      </n-button>
                    </n-dropdown>
                  </template>
                  <template v-else>
                    <n-space align="center">
                      <router-link :to="{ name: 'Register' }" v-slot="{ navigate }">
                        <n-button size="small" ghost @click="navigate">快速註冊</n-button>
                      </router-link>
                      <router-link :to="{ name: 'Login' }" v-slot="{ navigate }">
                        <n-button type="primary" size="small" @click="navigate">登入</n-button>
                      </router-link>
                    </n-space>
                  </template>
                </div>
              </div>
            </n-layout-header>

            <n-layout-content
                class="main-layout-content"
                content-style="padding: 20px; height: 100%;"
                :native-scrollbar="false"
            >
              <router-view v-slot="{ Component }">
                <transition name="fade" mode="out-in">
                  <component :is="Component"/>
                </transition>
              </router-view>
            </n-layout-content>

            <n-layout-footer bordered position="static" class="app-footer">
              &copy; {{ new Date().getFullYear() }}
            </n-layout-footer>
          </n-layout>
        </n-dialog-provider>
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import {computed, h, onMounted, ref, watch} from 'vue';
import {RouterLink, useRoute, useRouter} from 'vue-router';
import {useAuthStore} from './stores/authStore'; // 確保路徑正確
import {
  dateZhTW,
  NButton,
  NConfigProvider,
  NDialogProvider,
  NDropdown,
  NIcon,
  NLayout,
  NLayoutContent,
  NLayoutFooter,
  NLayoutHeader,
  NMenu,
  NMessageProvider,
  NNotificationProvider,
  NSpace,
  zhTW,
} from 'naive-ui';
import {
  ChevronDownOutline as ChevronDownIcon,
  ClipboardOutline as RecordMatchIcon,
  HomeOutline as HomeIcon,
  LogOutOutline as LogoutIcon,
  PeopleOutline as TeamManagementIcon,
  PersonCircleOutline as PersonCircleOutlineIcon,
  SettingsOutline as SettingsIcon
} from '@vicons/ionicons5';

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

const activeMenuKey = ref(route.name);

watch(() => route.name, (newName) => {
  activeMenuKey.value = newName;
});

const renderIcon = (icon) => () => h(NIcon, null, {default: () => h(icon)});
const renderRouterLink = (routeName, label) => () => h(RouterLink, {to: {name: routeName}}, {default: () => label});

const menuOptions = computed(() => [
  {
    label: renderRouterLink('Leaderboard', '排行榜'),
    key: 'Leaderboard', // 對應路由的 name
    icon: renderIcon(HomeIcon)
  },
  {
    label: renderRouterLink('RecordMatch', '記錄比賽'),
    key: 'RecordMatch',
    icon: renderIcon(RecordMatchIcon),
    show: authStore.isAuthenticated && (authStore.isCadre || authStore.isAdmin)
  },
  {
    label: renderRouterLink('ManagementCenter', '團隊管理'), // 假設管理中心的路由 name 是 TeamManagement
    key: 'ManagementCenter',
    icon: renderIcon(TeamManagementIcon),
    show: authStore.isAuthenticated && (authStore.isCadre || authStore.isAdmin || authStore.isCoach)
  },
]);

const userDropdownOptions = computed(() => [
  {
    label: () => h(RouterLink, {
      to: {name: 'EditProfile'},
      class: 'custom-dropdown-link'
    }, {default: () => '編輯個人資料'}),
    key: 'edit-profile', // key 用於 @select，但實際跳轉由 RouterLink 處理
    icon: renderIcon(SettingsIcon)
  },
  {type: 'divider', key: 'd1'},
  {
    label: '登出',
    key: 'logout', // 這個 key 會被 handleUserDropdownSelect 捕獲
    icon: renderIcon(LogoutIcon)
  }
]);

// 處理使用者下拉選單的點擊 (主要處理非 RouterLink 的情況，例如登出)
const handleUserDropdownSelect = (key) => {
  if (key === 'logout') {
    authStore.logoutAndRedirect();
  }
  // RouterLink 已經處理了 edit-profile 和 change-password 的跳轉
};

function getRoleDisplay(roleName) {
  if (roleName === 'ADMIN') return '管理員';
  if (roleName === 'CADRE') return '幹部';
  if (roleName === 'COACH') return '教練';
  if (roleName === 'PLAYER') return '隊員';
  return roleName;
}

onMounted(() => {
  if (authStore.accessToken && !authStore.user) {
    authStore.fetchCurrentUser();
  }
  activeMenuKey.value = route.name;
});

// Naive UI 主題覆蓋 (可選，根據您的喜好調整)
const themeOverrides = {
  common: {
    primaryColor: '#0d6efd', // 例如，使用一個類似 Bootstrap Primary 的藍色
    primaryColorHover: '#0b5ed7',
    primaryColorPressed: '#0a58ca',
    primaryColorSuppl: '#0d6efd', // 用於一些輔助元素
    bodyColor: "#f8f9fa", // 應用程式背景色
    textColorBase: '#212529', // 基本文字顏色
    fontSize: '14px',
  },
  Button: {
    // textColorPrimary: '#fff',
    // textColorGhostPrimary: 'var(--primary-color)', // 繼承 common 中的 primaryColor
    // textColorTextPrimary: 'var(--primary-color)',
  },
  Menu: {
    // itemColorHorizontal: 'transparent', // 水平選單項背景
    itemTextColorHorizontal: 'rgba(255, 255, 255, 0.75)', // Navbar 選單文字顏色
    itemIconColorHorizontal: 'rgba(255, 255, 255, 0.75)',
    itemTextColorHoverHorizontal: '#ffffff',
    itemIconColorHoverHorizontal: '#ffffff',
    itemTextColorActiveHorizontal: '#ffffff', // 選中項文字
    itemIconColorActiveHorizontal: '#ffffff',
    // itemColorActiveHorizontal: 'var(--primary-color-hover)', // 選中項背景（如果需要）
    // --n-item-text-color-active: var(--primary-color) !important;
  },
  Layout: {
    // headerColor: '#343a40', // Bootstrap .bg-dark 的顏色
    // footerColor: '#f8f9fa', // Bootstrap .bg-light
    // color: '#eef1f7' // content 背景色 (或用 bodyColor)
  },
  Dropdown: {
    // Naive UI Dropdown 樣式通常不錯，如有需要可在此覆蓋
    // optionTextColor: '#333',
  }
};
</script>

<style>
/* 全域樣式 - 確保這些樣式能正確應用 */
html, body, #app {
  height: 100%;
  margin: 0;
  overflow: hidden; /* 讓 n-layout-content 自己處理滾動 */
  background-color: var(--body-color); /* Naive UI 的背景色 */
}

.app-header {
  padding: 0 24px; /* 左右內邊距 */
  height: 60px; /* 固定 header 高度 */
  display: flex; /* 確保內部元素能用 flex 對齊 */
  align-items: center;
  background-color: #343a40; /* Bootstrap .bg-dark 顏色 */
}

.navbar-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.navbar-brand-custom {
  font-size: 1.25rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9) !important;
  text-decoration: none;
  margin-right: 1.5rem;
}

.navbar-brand-custom:hover {
  color: #fff !important;
}

.main-nav-menu.n-menu--horizontal {
  background-color: transparent !important;
  line-height: 60px; /* 與 header 高度匹配 */
  flex-grow: 1; /* 讓選單佔據可用空間 */
}

.main-nav-menu.n-menu--horizontal .n-menu-item {
  height: 60px !important;
}

.main-nav-menu.n-menu--horizontal .n-menu-item-content {
  padding: 0 10px !important;
  border-bottom: 3px solid transparent !important;
}

/* 使用 Naive UI 主題變數來設定選中項顏色 */
.main-nav-menu.n-menu--horizontal .n-menu-item--selected .n-menu-item-content {
  border-bottom-color: var(--primary-color) !important; /* 使用 themeOverrides 中的 primaryColor */
}

.main-nav-menu .n-menu-item-content__icon {
  margin-right: 6px !important;
}

.main-nav-menu .n-menu-item-content-header a {
  color: inherit !important;
  text-decoration: none !important;
  display: flex;
  align-items: center;
}


.user-actions-area {
  /* flex-shrink: 0; */ /* 確保使用者區域不被壓縮 */
}

.user-display-button.n-button { /* 為使用者名稱按鈕設定樣式 */
  color: rgba(255, 255, 255, 0.85);
  font-weight: 500;
}

.user-display-button.n-button:hover,
.user-display-button.n-button:focus {
  color: #ffffff;
  background-color: rgba(255, 255, 255, 0.1) !important;
}

.user-role-display-badge {
  font-size: 0.75em;
  opacity: 0.8;
  color: #0dcaf0; /* Naive UI info color 或 text-info */
}

.dropdown-arrow-icon {
  vertical-align: -0.125em; /* 微調箭頭圖示 */
}

.custom-dropdown-link, .custom-dropdown-link:hover { /* 用於 dropdown 中的 RouterLink */
  text-decoration: none;
  color: inherit; /* 繼承 dropdown item 的顏色 */
  display: block;
  width: 100%;
}


.main-layout-content.n-layout-content {
  background-color: #f8f9fa; /* 內容區域背景色 */
}

.app-footer.n-layout-footer {
  text-align: center;
  line-height: 1.5;
  background-color: #e9ecef;
  color: #6c757d;
  padding: 1rem 0; /* 調整 padding */
}

.app-footer .text-muted {
  color: #6c757d !important;
}

/* 頁面切換過渡效果 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.15s ease-in-out;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>