<template>
  <div id="app-container">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <div class="container-fluid">
        <router-link class="navbar-brand" to="/">TKUST 網球隊戰績 (Vue)</router-link>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav ms-auto">
            <li class="nav-item">
              <router-link class="nav-link" active-class="active" to="/">排行榜</router-link>
            </li>
<!--            <li class="nav-item">-->
<!--              <router-link class="nav-link" active-class="active" to="/match/record">記錄比賽</router-link>-->
<!--            </li>-->
            <li class="nav-item">
              <router-link class="nav-link" active-class="active" to="/members/add">新增成員</router-link>
            </li>
            {/* ... 其他登入/登出連結 (如果已實作) ... */}
          </ul>
        </div>
      </div>
    </nav>

    <main role="main" class="container mt-4 flex-shrink-0">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <footer class="footer mt-auto py-3 bg-light">
      {/* ... footer 內容 ... */}
    </footer>
  </div>
</template>

<script setup>
// 在 Vue 3 <script setup> 中，不需要特別的腳本來做這些基本佈局
// 如果您需要 Bootstrap 的 JavaScript 功能，請確保在 main.js 中匯入了 'bootstrap/dist/js/bootstrap.bundle.min.js'
import 'bootstrap/dist/js/bootstrap.bundle.min.js';
</script>

<style>
/* 全域或 App 特定樣式 */
html, body {
  height: 100%;
}

#app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

main {
  flex: 1 0 auto; /* 讓 main 區域可以擴展，並將 footer 推到底部 */
}

.footer {
  flex-shrink: 0; /* 防止 footer 在內容不足時縮小 */
}

/* 簡單的頁面切換過渡效果 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>