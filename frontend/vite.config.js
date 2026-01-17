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
    port: 5174,
    proxy: {
      // 🔴 后端端口 8080
      '/ws': {
        target: 'ws://localhost:8080',
        ws: true
      },
      '/api': 'http://localhost:8080'
    }
  }
})

