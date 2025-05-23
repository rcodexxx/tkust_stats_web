// frontend/src/views/AddMemberView.vue
<template>
  <div class="container mt-4">
    <h1>新增球隊成員</h1>
    <div v-if="message" :class="['alert', messageType === 'success' ? 'alert-success' : 'alert-danger']" role="alert">
      {{ message }}
    </div>
    <form @submit.prevent="submitNewMember">
      <div class="mb-3">
        <label for="name" class="form-label">姓名*</label>
        <input type="text" class="form-control" id="name" v-model="memberData.name" required>
      </div>
      <div class="mb-3">
        <label for="student_id" class="form-label">學號 (可選)</label>
        <input type="text" class="form-control" id="student_id" v-model="memberData.student_id">
      </div>
      <div class="mb-3">
        <label for="gender" class="form-label">性別</label>
        <select class="form-select" id="gender" v-model="memberData.gender">
          <option value="">--請選擇--</option>
          <option value="MALE">男性</option>
          <option value="FEMALE">女性</option>
        </select>
      </div>
      <div class="mb-3">
        <label for="position" class="form-label">習慣位置</label>
        <select class="form-select" id="position" v-model="memberData.position">
          <option value="">--請選擇--</option>
          <option value="BACK">後排</option>
          <option value="FRONT">前排</option>
          <option value="VERSATILE">皆可</option>
        </select>
      </div>
      <button type="submit" class="btn btn-primary" :disabled="submitting">
        {{ submitting ? '提交中...' : '新增成員' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue';
import axios from 'axios'; // 或您封裝的 apiService
import { useRouter } from 'vue-router';

const router = useRouter();
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

const memberData = reactive({
  name: '',
  student_id: '',
  gender: '', // 前端將傳送 Enum 的 NAME (大寫)
  position: '', // 前端將傳送 Enum 的 NAME (大寫)
});

const message = ref('');
const messageType = ref(''); // 'success' or 'danger'
const submitting = ref(false);

// 假設您有一個地方儲存登入後的 token，例如 Pinia store 或 localStorage
// const authToken = localStorage.getItem('authToken'); // 簡化示例

async function submitNewMember() {
  message.value = '';
  messageType.value = '';
  if (submitting.value) return;
  submitting.value = true;

  if (!memberData.name) {
      message.value = '姓名為必填欄位。';
      messageType.value = 'danger';
      submitting.value = false;
      return;
  }

  const payload = {
    name: memberData.name,
    student_id: memberData.student_id || null,
    gender: memberData.gender || null,
    position: memberData.position || null,
  };

  try {
    const response = await axios.post(`${apiBaseUrl}/members`, payload, {
      // headers: { // 如果需要認證
      //   'Authorization': `Bearer ${authToken}`
      // }
    });
    message.value = response.data.message || '成員已成功新增！';
    messageType.value = 'success';

    // 可選：延遲後跳轉
    setTimeout(() => {
      router.push('/'); // 跳轉到排行榜
    }, 1500);

  } catch (e) {
    message.value = e.response?.data?.error || e.response?.data?.details || e.message || '新增成員時發生錯誤';
    messageType.value = 'danger';
    // 處理詳細錯誤 (如果後端回傳了 details 物件)
    if (e.response?.data?.details && typeof e.response.data.details === 'object') {
        let detailedErrors = [];
        for (const field in e.response.data.details) {
            detailedErrors.push(`${field}: ${e.response.data.details[field]}`);
        }
        message.value = `輸入驗證失敗：\n${detailedErrors.join('\n')}`;
    }
    console.error(e.response || e);
  } finally {
    submitting.value = false;
  }
}
</script>