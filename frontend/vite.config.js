// frontend/vite.config.js
import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
        },
    },
    server: {
        proxy: {
            '/api': {
                // --- 修正：將 target 的 port 從 5000 改為 8000 ---
                target: 'http://127.0.0.1:8000', // 您的 Flask 後端伺服器運行的正確 port
                changeOrigin: true, // 允許跨域

                // --- 代理事件監聽器 (您可以保留它們以供未來除錯) ---
                configure: (proxy, options) => {
                    proxy.on('error', (err, req, res) => {
                        console.error('代理錯誤:', err);
                    });
                    proxy.on('proxyReq', (proxyReq, req, res) => {
                        console.log(`正在代理請求: ${req.method} ${req.url} -> ${options.target.href}${proxyReq.path}`);
                    });
                    proxy.on('proxyRes', (proxyRes, req, res) => {
                        console.log(`收到代理回應: ${proxyRes.statusCode} ${req.url}`);
                    });
                },
            },
        },
    },
})
