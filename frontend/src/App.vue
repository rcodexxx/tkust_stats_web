<template>
  <div id="app-container" class="d-flex flex-column vh-100">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark flex-shrink-0">
      <div class="container-fluid">
        <router-link class="navbar-brand" to="/">HOME</router-link>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"
                aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav ms-auto align-items-center">}
            <!--            <li class="nav-item">-->
            <!--              <router-link class="nav-link" active-class="active" to="/">排行榜</router-link>-->
            <!--            </li>-->
            <template v-if="authStore.isAuthenticated">
              <li class="nav-item" v-if="authStore.isCadre || authStore.isAdmin">
                <router-link class="nav-link" active-class="active" to="/match/record">記錄比賽</router-link>
              </li>
              <li class="nav-item" v-if="authStore.isAdmin">
                <router-link class="nav-link" active-class="active" to="/members/add">新增成員</router-link>
              </li>
              <!--              <li class="nav-item">-->
              <!--                <router-link class="nav-link" active-class="active" to="/my-profile">我的資料</router-link>-->
              <!--              </li>-->
              <li class="nav-item dropdown">
                <a class="nav-link dropdown-toggle" href="#" id="navbarUserDropdown" role="button"
                   data-bs-toggle="dropdown" aria-expanded="false">
                  {{ authStore.userDisplayName }}
                  <small v-if="authStore.userRole" class="text-info">({{ authStore.userRole }})</small>
                </a>
                <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="navbarUserDropdown">
                  <li>
                    <router-link class="dropdown-item" to="/profile/edit">編輯個人資料</router-link>
                  </li>
                  <!--                  <li>-->
                  <!--                    <router-link class="dropdown-item" to="/profile/change-password">修改密碼</router-link>-->
                  <!--                  </li>-->
                  <li>
                    <hr class="dropdown-divider">
                  </li>
                  <li>
                    <button class="dropdown-item" @click="handleLogout">登出</button>
                  </li>
                </ul>
              </li>
            </template>
            <template v-else>
              <li class="nav-item">
                <router-link class="nav-link btn btn-primary btn-sm" :to="{ name: 'Login' }">登入</router-link>
              </li>
            </template>
          </ul>
        </div>
      </div>
    </nav>

    <main role="main" class="container-fluid mt-4 flex-grow-1 overflow-auto main-content-scrollable">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component"/>
        </transition>
      </router-view>
    </main>

    <footer class="footer mt-auto py-3 bg-light flex-shrink-0">
      <div class="container text-center">
        <span class="text-muted">&copy; {{ new Date().getFullYear() }} TKUST Tennis Team Stats.</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import {useAuthStore} from './stores/authStore'; // 匯入您的 auth store
import 'bootstrap/dist/js/bootstrap.bundle.min.js'; // 確保 Bootstrap JS 已載入 (為了 Navbar dropdown)
import {onMounted} from 'vue'; // 如果需要在 App.vue 掛載時執行操作

const authStore = useAuthStore();

const handleLogout = () => {
  authStore.logoutAndRedirect(); // 調用 store 中的登出 action
};

// (可選) 如果您希望在應用程式/App.vue 掛載時，檢查並恢復登入狀態
// 這通常在 router.beforeEach 或 main.js 中做更合適，但也可以在這裡做一次
onMounted(() => {
  if (authStore.accessToken && !authStore.user) { // 如果有 token 但 store 中沒有 user 資訊
    authStore.fetchCurrentUser(); // 嘗試從後端獲取使用者資訊
  }
});
</script>

<style>
/* 全域或 App 特定樣式 */
html, body {
  height: 100%;
  margin: 0;
  overflow-y: hidden; /* 阻止 body 本身的垂直滾動條，滾動由 main 控制 */
  overflow-x: auto; /* 允許 body 水平滾動，如果內容真的超出 */
}

#app-container {
  /* display: flex; flex-direction: column; vh-100; 已在 template 中 */
}

.main-content-scrollable { /* 主要內容區域，允許垂直滾動 */
  overflow-y: auto;
  overflow-x: hidden; /* 通常不希望主要內容區域水平滾動 */
  flex-grow: 1;
  padding-bottom: 2rem; /* 給底部內容一些空間，避免緊貼 footer */
}

.footer {
  /* flex-shrink: 0; 已在 template 中 */
}

/* 頁面切換過渡效果 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease-in-out; /* 加快一點過渡 */
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* 導覽列中 active 連結的樣式 (Bootstrap 通常已處理，但可以加強) */
.navbar-nav .nav-link.active {
  font-weight: bold;
  /* color: #0d6efd !important;  Bootstrap primary color */
}

.navbar-brand {
  font-weight: 500;
}

/* 為下拉選單中的按鈕移除預設樣式 */
.dropdown-item.btn, button.dropdown-item {
  background-color: transparent;
  border: none;
  color: var(--bs-dropdown-link-color); /* 使用 Bootstrap dropdown item 的顏色 */
  text-align: left; /* 確保文字靠左 */
  width: 100%; /* 讓按鈕填滿寬度 */
  padding: var(--bs-dropdown-item-padding-y) var(--bs-dropdown-item-padding-x); /* 使用 Bootstrap padding */
}

.dropdown-item.btn:hover, button.dropdown-item:hover {
  background-color: var(--bs-dropdown-link-hover-bg);
  color: var(--bs-dropdown-link-hover-color);
}
</style>