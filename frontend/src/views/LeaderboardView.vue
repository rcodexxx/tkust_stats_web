<template>
  <div class="container mt-4">
    <h1>{{ title }}</h1>
    <p v-if="loading">正在載入排行榜...</p>
    <p v-if="error" class="text-danger">載入錯誤: {{ error }}</p>

    <div v-if="!loading && !error">
      <router-link to="/match/record" class="btn btn-success mb-3">記錄比賽結果</router-link>
      <table class="table table-hover" v-if="members.length > 0">
        <thead>
          <tr>
            <th scope="col">#</th>
            <th scope="col">球員</th>
            <th scope="col">分數</th>
            <th scope="col">習慣位置</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(member, index) in members" :key="member.id">
            <th scope="row">{{ index + 1 }}</th>
            <td>{{ member.name }}</td>
            <td>{{ member.score }}</td>
            <td>{{ member.preferred_position || '未指定' }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else>目前沒有球員資料。</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const title = ref('球隊排行榜 (Vue)');
const members = ref([]);
const loading = ref(true);
const error = ref(null);

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

onMounted(async () => {
  try {
    const response = await axios.get(`${apiBaseUrl}/leaderboard`);
    members.value = response.data;
  } catch (e) {
    error.value = e.message || '無法獲取排行榜數據';
    console.error(e);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
/* 您可以在這裡加入此組件特定的樣式 */
</style>