<template>
  <div id="app-container">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <div class="container-fluid">
        <router-link class="navbar-brand" to="/">HOME</router-link>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"
                aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav ms-auto">
            <!--            <li class="nav-item">-->
            <!--              <router-link class="nav-link" active-class="active" to="/">排行榜</router-link>-->
            <!--            </li>-->
            <!--            <li class="nav-item">-->
            <!--              <router-link class="nav-link" active-class="active" to="/match/record">記錄比賽</router-link>-->
            <!--            </li>-->
<!--            <li class="nav-item">-->
<!--              <router-link class="nav-link" active-class="active" to="/members/add">新增成員</router-link>-->
<!--            </li>-->
<!--            <li class="nav-item">-->
<!--              <router-link to="/match/record" class="btn btn-lg btn-success shadow-sm custom-btn-green">-->
<!--                <i class="bi bi-plus-circle-fill me-4"></i>Record Match-->
<!--              </router-link>-->
<!--            </li>-->
          </ul>
        </div>
      </div>
    </nav>

    <main role="main" class="container mt-4 flex-shrink-0">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component"/>
        </transition>
      </router-view>
    </main>

    <footer class="footer mt-auto py-3 bg-light">
      <div class="container text-center">
        <span class="text-muted">&copy; {{ new Date().getFullYear() }} TKU Tennis Team Stats.</span>
      </div>
    </footer>
  </div>
</template>

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
  flex: 1 0 auto;
}

.footer {
  flex-shrink: 0;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>