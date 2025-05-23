// frontend/src/services/apiClient.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL, // 從 .env.local 讀取 API 基礎 URL
  timeout: 10000, // 請求超時 (毫秒)
  headers: {
    'Content-Type': 'application/json',
    // 'Accept': 'application/json', // 通常不需要明確設定
  }
});

// (可選) 設定請求攔截器 (Request Interceptor) - 例如自動加入認證 Token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken'); // 假設 Token 存在 localStorage
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// (可選) 設定回應攔截器 (Response Interceptor) - 例如處理全局錯誤或 Token 失效
apiClient.interceptors.response.use(
  (response) => {
    // 任何在 2xx 範圍內的狀態碼都會觸發此函數。
    // 在這裡可以對回應數據做一些處理
    return response;
  },
  (error) => {
    // 任何超出 2xx 範圍的狀態碼都會觸發此函數。
    if (error.response) {
      // 請求已發出，且伺服器以狀態碼回應
      console.error('API Error Response:', error.response.data);
      if (error.response.status === 401) {
        // 例如：Token 失效或未授權，可以導向到登入頁面
        // import router from '@/router'; // 需要注意這裡直接 import router 的潛在問題
        // router.push('/login');
        console.error('Unauthorized, redirecting to login might be needed.');
      }
    } else if (error.request) {
      // 請求已發出，但沒有收到回應 (例如網路錯誤)
      console.error('API No Response:', error.request);
    } else {
      // 設定請求時發生了一些事情，觸發了錯誤
      console.error('API Error Message:', error.message);
    }
    return Promise.reject(error); // 將錯誤繼續傳播下去，讓調用方也能處理
  }
);

export default apiClient;