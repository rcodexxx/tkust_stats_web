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
                        <small v-if="authStore.userRole" class="user-role-display">
                          {{ getRoleDisplay(authStore.userRole) }}
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
              &copy; {{ new Date().getFullYear() }} TKU Soft Tennis. All Rights Reserved.
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

// 任天堂風格主題覆蓋
const nintendoRed = '#E60012'; // 任天堂主紅色
const lightGreyText = '#888888'; // 導航連結文字淺灰色
const bodyBgColor = '#F5F5F5'; // Body 淺灰色背景

const themeOverrides = {
  common: {
    primaryColor: nintendoRed,
    primaryColorHover: '#CC0010', // 深一點的紅
    primaryColorPressed: '#B3000E', // 更深一點的紅
    primaryColorSuppl: nintendoRed,
    bodyColor: bodyBgColor, // 應用程式背景色
    textColorBase: '#333333', // 基本文字顏色
    fontSize: '14px',
  },
  Button: {
    textColorPrimary: '#FFFFFF', // 主要按鈕文字改為白色以搭配紅色背景
    // textColorGhostPrimary: nintendoRed, //  保持 ghost 按鈕文字為紅色
    // textColorTextPrimary: nintendoRed, // 保持 text 按鈕文字為紅色
  },
  Menu: {
    // itemColorHorizontal: 'transparent', // 水平選單項背景，由 CSS 控制
    itemTextColorHorizontal: lightGreyText, // Navbar 選單文字顏色
    itemIconColorHorizontal: lightGreyText, // Navbar 選單圖示顏色
    itemTextColorHoverHorizontal: nintendoRed, // Hover 時文字變紅
    itemIconColorHoverHorizontal: nintendoRed, // Hover 時圖示變紅
    itemTextColorActiveHorizontal: nintendoRed, // 選中項文字變紅
    itemIconColorActiveHorizontal: nintendoRed, // 選中項圖示變紅
    // itemColorActiveHorizontal: 'transparent', // 選中項背景由 CSS 的偽元素處理
  },
  Layout: {
    // headerColor: '#FFFFFF', // 由 CSS .app-header 控制
    // footerColor: '#E0E0E0', // 由 CSS .app-footer 控制
    // color: bodyBgColor // content 背景色
  },
  Dropdown: {
    optionTextColor: '#333333',
  }
};

</script>

<style>
/* 全域樣式 */
html, body, #app {
  height: 100%;
  margin: 0;
  overflow: hidden; /* 讓 n-layout-content 自己處理滾動 */
  background-color: var(--body-color, #F5F5F5); /* 使用 Naive UI 的 bodyColor 或預設淺灰 */
  font-family: 'Arial', 'Helvetica Neue', Helvetica, sans-serif; /* 一個常見的無襯線字體 */
}

.app-header {
  padding: 0 24px;
  height: 64px; /* 稍微增加一點高度以容納 "方塊" 感 */
  display: flex;
  align-items: center;
  background-color: #FFFFFF; /* Navbar 白色背景 */
  border-bottom: 1px solid #E0E0E0; /* Navbar 底部細線 */
}

.navbar-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.navbar-brand-custom {
  font-size: 1.15rem; /* 調整字體大小 */
  font-weight: bold; /* 加粗 */
  color: #FFFFFF !important; /* 白色文字 */
  background-color: var(--primary-color, #E60012); /* 任天堂紅背景 */
  text-decoration: none;
  margin-right: 2rem;
  padding: 10px 20px; /* 增加內邊距，使其有方塊感 */
  border-radius: 4px; /* 可選：輕微圓角 */
  white-space: nowrap; /* 防止文字換行 */
  transition: background-color 0.3s ease;
}

.navbar-brand-custom:hover {
  color: #FFFFFF !important;
  background-color: var(--primary-color-hover, #CC0010); /* Hover 時略深一點的紅 */
}

.main-nav-menu.n-menu--horizontal {
  background-color: transparent !important;
  line-height: normal; /* 移除固定行高，讓 padding 控制高度 */
  flex-grow: 1;
}

.main-nav-menu.n-menu--horizontal .n-menu-item {
  height: auto !important; /* 讓內容和 padding 決定高度 */
  margin: 0 4px; /* 連結之間的間距 */
}

.main-nav-menu.n-menu--horizontal .n-menu-item-content {
  padding: 12px 16px !important; /* 增加 padding 使連結有方塊感 */
  border-bottom: none !important; /* 移除原有的底部邊框 */
  position: relative; /* 為了偽元素定位 */
  overflow: hidden; /* 為了偽元素的滑動效果 */
  border-radius: 4px; /* 可選：輕微圓角 */
  transition: color 0.2s ease, background-color 0.2s ease;
}

/* 連結下方滑動的紅色條 */
.main-nav-menu.n-menu--horizontal .n-menu-item-content::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: -4px; /* 初始位置在方塊下方，準備向上滑入 */
  width: 100%;
  height: 4px; /* 紅色條的高度 */
  background-color: var(--primary-color, #E60012);
  transition: bottom 0.25s ease-in-out;
}

/* Hover 或選中時，紅色條滑入，文字顏色改變 */
.main-nav-menu.n-menu--horizontal .n-menu-item:hover .n-menu-item-content::after,
.main-nav-menu.n-menu--horizontal .n-menu-item--selected .n-menu-item-content::after {
  bottom: 0; /* 滑入到方塊底部 */
}

.main-nav-menu.n-menu--horizontal .n-menu-item:hover .n-menu-item-content-header,
.main-nav-menu.n-menu--horizontal .n-menu-item:hover .n-menu-item-content__icon,
.main-nav-menu.n-menu--horizontal .n-menu-item--selected .n-menu-item-content-header,
.main-nav-menu.n-menu--horizontal .n-menu-item--selected .n-menu-item-content__icon {
  color: var(--primary-color, #E60012) !important; /* 使用 themeOverrides 中定義的顏色 */
}


.main-nav-menu .n-menu-item-content__icon {
  margin-right: 8px !important; /* 圖示和文字間距 */
}

.main-nav-menu .n-menu-item-content-header a {
  color: inherit !important; /* 繼承父元素 .n-menu-item-content-header 的顏色 */
  text-decoration: none !important;
  display: flex;
  align-items: center;
}

.user-actions-area {
  /* flex-shrink: 0; */
}

.user-display-button.n-button {
  color: #555555; /* 在白色 navbar 上的使用者名稱顏色 */
  font-weight: 500;
}

.user-display-button.n-button:hover,
.user-display-button.n-button:focus {
  color: var(--primary-color, #E60012); /* Hover 時變紅 */
  background-color: rgba(0, 0, 0, 0.03) !important; /* 非常淡的背景表示 active */
}

/* 使用者 Role 文字樣式 (無括號) */
.user-role-display {
  font-size: 0.8em;
  opacity: 0.9;
  color: #777777; /* Role 文字顏色 */
  margin-left: 6px; /* 和使用者名稱的間距 */
}

.dropdown-arrow-icon {
  vertical-align: -0.125em;
}

.custom-dropdown-link, .custom-dropdown-link:hover {
  text-decoration: none;
  color: inherit;
  display: block;
  width: 100%;
}

.main-layout-content.n-layout-content {
  background-color: var(--body-color, #F5F5F5); /* 內容區域背景色 */
}

.app-footer.n-layout-footer {
  text-align: center;
  line-height: 1.5;
  background-color: #E0E0E0; /* Footer 背景色，比 body 略深 */
  color: #666666; /* Footer 文字顏色 */
  padding: 1rem 0;
  border-top: 1px solid #D0D0D0;
}

/* 頁面切換過渡效果 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.15s ease-in-out;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>