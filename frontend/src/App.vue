<template>
  <n-config-provider :theme-overrides="themeOverrides" :locale="zhTW" :date-locale="dateZhTW" style="height: 100%;">
    <n-message-provider>
      <n-notification-provider>
        <n-dialog-provider>
          <n-layout style="height: 100vh;" :native-scrollbar="false">
            <n-layout-header bordered class="app-header">
              <div class="navbar-content">
                <router-link to="/" class="navbar-brand-custom" v-if="!isMobile">
                  TKU Soft Tennis Web
                </router-link>

                <div class="mobile-nav-trigger" v-if="isMobile">
                  <n-button text @click="showMobileDrawer = true">
                    <n-icon size="28">
                      <MenuIcon/>
                    </n-icon>
                  </n-button>
                </div>


                <n-menu
                    v-if="!isMobile"
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
                        <small v-if="authStore.userRole && !isMobile" class="user-role-display">
                          {{ getRoleDisplay(authStore.userRole) }}
                        </small>
                        <n-icon size="14" class="dropdown-arrow-icon">
                          <ChevronDownIcon/>
                        </n-icon>
                      </n-button>
                    </n-dropdown>
                  </template>
                  <template v-else>
                    <n-space align="center" :wrap="false">
                      <router-link :to="{ name: 'Register' }" v-slot="{ navigate }">
                        <n-button size="small" ghost round @click="navigate">
                          快速註冊
                        </n-button>
                      </router-link>
                      <router-link :to="{ name: 'Login' }" v-slot="{ navigate }">
                        <n-button type="primary" size="small" round @click="navigate">
                          登入
                        </n-button>
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

          <n-drawer v-model:show="showMobileDrawer" :width="240" placement="left">
            <n-drawer-content title="選單" closable>
              <router-link to="/" class="mobile-drawer-brand" @click="showMobileDrawer = false">
                TKU Soft Tennis Web
              </router-link>
              <n-menu
                  v-model:value="activeMenuKey"
                  mode="vertical"
                  :options="menuOptions"
                  :on-update:value="() => showMobileDrawer = false"
              />
            </n-drawer-content>
          </n-drawer>

        </n-dialog-provider>
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import {computed, h, onMounted, ref, watch} from 'vue';
import {RouterLink, useRoute, useRouter} from 'vue-router';
import {useAuthStore} from './stores/authStore';
import {useWindowSize} from '@vueuse/core';
import '@/assets/css/main.css'
import {
  dateZhTW,
  NButton,
  NConfigProvider,
  NDialogProvider,
  NDrawer,
  NDrawerContent,
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
  ListCircleOutline as MatchManagementIcon,
  LogOutOutline as LogoutIcon,
  MenuOutline as MenuIcon,
  PeopleOutline as TeamManagementIcon,
  PersonCircleOutline as PersonCircleOutlineIcon,
  PodiumOutline as HomeIcon,
  SettingsOutline as SettingsIcon
} from '@vicons/ionicons5';

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

// --- 響應式設計相關 ---
const {width} = useWindowSize();
const isMobile = computed(() => width.value < 768); // 設定中斷點，可自行調整
const showMobileDrawer = ref(false);
// ---

const activeMenuKey = ref(route.name);

watch(() => route.name, (newName) => {
  activeMenuKey.value = newName;
}, {immediate: true});

const renderIcon = (icon) => () => h(NIcon, null, {default: () => h(icon)});
// 修改 renderRouterLink 以便在點擊後關閉抽屜
const renderRouterLink = (routeName, label) => () => h(
    RouterLink,
    {
      to: {name: routeName}, onClick: () => {
        if (isMobile.value) showMobileDrawer.value = false;
      }
    },
    {default: () => label}
);


const menuOptions = computed(() => [
  {
    label: renderRouterLink('Leaderboard', '排行榜'),
    key: 'Leaderboard',
    icon: renderIcon(HomeIcon)
  },
  {
    label: renderRouterLink('RecordMatch', '記錄比賽'),
    key: 'RecordMatch',
    icon: renderIcon(RecordMatchIcon),
    // show: authStore.isAuthenticated && (authStore.isCadre || authStore.isAdmin)
  },
  {
    label: renderRouterLink('MatchManagement', '比賽管理'), // 新增的選單項目
    key: 'MatchManagement',
    icon: renderIcon(MatchManagementIcon),
    show: authStore.isAuthenticated && (authStore.isCadre || authStore.isAdmin || authStore.isCoach) // 設定顯示權限
  },
  {
    label: renderRouterLink('ManagementCenter', '團隊管理'),
    key: 'ManagementCenter',
    icon: renderIcon(TeamManagementIcon),
    show: authStore.isAuthenticated && (authStore.isCadre || authStore.isAdmin || authStore.isCoach)
  },
].filter(option => option.show !== false)); // 過濾掉 show 為 false 的選項


const userDropdownOptions = computed(() => [
  {
    label: () => h(RouterLink, {
      to: {name: 'EditProfile'},
      class: 'custom-dropdown-link'
    }, {default: () => '編輯個人資料'}),
    key: 'edit-profile',
    icon: renderIcon(SettingsIcon)
  },
  {type: 'divider', key: 'd1'},
  {
    label: '登出',
    key: 'logout',
    icon: renderIcon(LogoutIcon)
  }
]);

const handleUserDropdownSelect = (key) => {
  if (key === 'logout') {
    authStore.logoutAndRedirect();
  }
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

const nintendoRed = '#E60012';
const lightGreyText = '#888888';
const bodyBgColor = '#F5F5F5';

const themeOverrides = {
  common: {
    primaryColor: nintendoRed,
    primaryColorHover: '#CC0010',
    primaryColorPressed: '#B3000E',
    primaryColorSuppl: nintendoRed,
    bodyColor: bodyBgColor,
    textColorBase: '#333333',
    fontSize: '14px',
  },
  Button: {
    textColorPrimary: '#FFFFFF',
  },
  Menu: {
    itemTextColorHorizontal: lightGreyText,
    itemIconColorHorizontal: lightGreyText,
    itemTextColorHoverHorizontal: nintendoRed,
    itemIconColorHoverHorizontal: nintendoRed,
    itemTextColorActiveHorizontal: nintendoRed,
    itemIconColorActiveHorizontal: nintendoRed,
    // --- 針對垂直 (Drawer) 選單的樣式 ---
    itemTextColorVertical: '#555555',
    itemIconColorVertical: '#555555',
    itemTextColorHoverVertical: nintendoRed,
    itemIconColorHoverVertical: nintendoRed,
    itemTextColorActiveVertical: nintendoRed,
    itemIconColorActiveVertical: nintendoRed,
    itemColorActive: 'rgba(230, 0, 18, 0.1)', // 垂直選單選中項背景色
  },
  Layout: {},
  Drawer: {
    titleTextColor: nintendoRed,
    titleFontSize: '1.2rem',
  },
  Dropdown: {
    optionTextColor: '#333333',
  }
};
</script>