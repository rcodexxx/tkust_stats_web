// frontend/vite.config.js
import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path' // 1. 匯入 Node.js 的 path 模組

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            // 2. 設定 '@' 別名指向 'src' 資料夾
            '@': path.resolve(__dirname, './src'),
        }
    }
})