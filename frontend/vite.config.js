import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      // 🔴 后端固定端口 8000，不要修改
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      },
      '/api': 'http://localhost:8000'
    }
  }
})

