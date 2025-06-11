// src/api/index.js
import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 您可以在這裡加入攔截器來自動附加 JWT token 等

export default apiClient
