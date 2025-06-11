<template>
  <n-config-provider
    :theme-overrides="themeOverrides"
    :locale="zhTW"
    :date-locale="dateZhTW"
    style="height: 100%"
  >
    <n-message-provider>
      <n-notification-provider>
        <n-dialog-provider>
          <n-layout style="height: 100vh" :native-scrollbar="false">
            <n-layout-header bordered class="app-header">
              <div class="navbar-content">
                <router-link v-if="!isMobile" to="/" class="navbar-brand-custom">
                  TKU Soft Tennis Web
                </router-link>

                <div v-if="isMobile" class="mobile-nav-trigger">
                  <n-button text @click="showMobileDrawer = true">
                    <n-icon size="28">
                      <MenuIcon />
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
                      placement="bottom-end"
                      @select="handleUserDropdownSelect"
                    >
                      <n-button quaternary class="user-display-button">
                        <template #icon>
                          <n-icon :component="PersonCircleOutlineIcon" />
                        </template>
                        {{ authStore.userDisplayName }}
                        <small v-if="authStore.userRole && !isMobile" class="user-role-display">
                          {{ getRoleDisplay(authStore.userRole) }}
                        </small>
                        <n-icon size="14" class="dropdown-arrow-icon">
                          <ChevronDownIcon />
                        </n-icon>
                      </n-button>
                    </n-dropdown>
                  </template>
                  <template v-else>
                    <n-space align="center" :wrap="false">
                      <router-link v-slot="{ navigate }" :to="{ name: 'Register' }">
                        <n-button size="small" ghost round @click="navigate"> 快速註冊 </n-button>
                      </router-link>
                      <router-link v-slot="{ navigate }" :to="{ name: 'Login' }">
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
              <n-spin :show="isInitializing" description="載入中...">
                <router-view v-slot="{ Component }">
                  <transition name="fade" mode="out-in">
                    <component :is="Component" />
                  </transition>
                </router-view>
              </n-spin>
            </n-layout-content>

            <n-layout-footer bordered position="static" class="app-footer">
              &copy; {{ currentYear }} TKU Soft Tennis. All Rights Reserved.
            </n-layout-footer>
          </n-layout>

          <n-drawer v-model:show="showMobileDrawer" :width="240" placement="left">
            <n-drawer-content title="選單" closable>
              <router-link to="/" class="mobile-drawer-brand" @click="handleMobileMenuClick">
                TKU Soft Tennis Web
              </router-link>
              <n-menu
                v-model:value="activeMenuKey"
                mode="vertical"
                :options="menuOptions"
                @update:value="handleMobileMenuClick"
              />
            </n-drawer-content>
          </n-drawer>
        </n-dialog-provider>
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { computed, h, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useAuthStore } from './stores/authStore'
import { useWindowSize } from '@vueuse/core'
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
  NSpin,
  zhTW
} from 'naive-ui'
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
} from '@vicons/ionicons5'
import { themeOverrides } from '@/config/theme'

// Constants
  const MOBILE_BREAKPOINT = 768

  // Stores and route
  const authStore = useAuthStore()
  const route = useRoute()

  // State
  const showMobileDrawer = ref(false)
  const activeMenuKey = ref(route.name)
  const isInitializing = ref(true)

  // 響應式設計
  const { width } = useWindowSize()
  const isMobile = computed(() => width.value < MOBILE_BREAKPOINT)

  // 當前年份
  const currentYear = computed(() => new Date().getFullYear())

  // 權限管理
  const hasManagementAccess = computed(
    () =>
      authStore.isAuthenticated &&
      (authStore.isCadre || authStore.isAdmin || authStore.isCoach)
  )

  // 角色顯示映射
  const roleDisplayMap = {
    ADMIN: '管理員',
    CADRE: '幹部',
    COACH: '教練',
    PLAYER: '隊員'
  }

  // Watch route changes
  watch(
    () => route.name,
    newName => {
      activeMenuKey.value = newName
    },
    { immediate: true }
  )

  // Helper functions
  const renderIcon = icon => () => h(NIcon, null, { default: () => h(icon) })

  const renderRouterLink = (routeName, label) => () =>
    h(RouterLink, { to: { name: routeName } }, { default: () => label })

  // Menu options
  const menuOptions = computed(() =>
    [
      {
        label: renderRouterLink('Leaderboard', '排行榜'),
        key: 'Leaderboard',
        icon: renderIcon(HomeIcon)
      },
      {
        label: renderRouterLink('RecordMatch', '記錄比賽'),
        key: 'RecordMatch',
        icon: renderIcon(RecordMatchIcon)
      },
      {
        label: renderRouterLink('MatchManagement', '比賽管理'),
        key: 'MatchManagement',
        icon: renderIcon(MatchManagementIcon),
        show: hasManagementAccess.value
      },
      {
        label: renderRouterLink('ManagementCenter', '團隊管理'),
        key: 'ManagementCenter',
        icon: renderIcon(TeamManagementIcon),
        show: hasManagementAccess.value
      }
    ].filter(option => option.show !== false)
  )

  // User dropdown options
  const userDropdownOptions = computed(() => [
    {
      label: () =>
        h(
          RouterLink,
          {
            to: { name: 'EditProfile' },
            class: 'custom-dropdown-link'
          },
          { default: () => '編輯個人資料' }
        ),
      key: 'edit-profile',
      icon: renderIcon(SettingsIcon)
    },
    { type: 'divider', key: 'd1' },
    {
      label: '登出',
      key: 'logout',
      icon: renderIcon(LogoutIcon)
    }
  ])

  // Event handlers
  const handleUserDropdownSelect = key => {
    if (key === 'logout') {
      authStore.logoutAndRedirect()
    }
  }

  const handleMobileMenuClick = () => {
    showMobileDrawer.value = false
  }

  // Helper functions
  function getRoleDisplay(roleName) {
    return roleDisplayMap[roleName] || roleName
  }

  // Lifecycle
  onMounted(async () => {
    try {
      if (authStore.accessToken && !authStore.user) {
        await authStore.fetchCurrentUser()
      }
      activeMenuKey.value = route.name
    } finally {
      isInitializing.value = false
    }
  })
</script>

<style scoped>
/* 如果有特定的樣式，可以在這裡加入 */
</style>