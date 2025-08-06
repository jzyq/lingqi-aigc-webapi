import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: "/aigc/admin/",
  server: {
    proxy: {
      '/aigc/admin/api': {
        target: 'http://localhost:8001', // Your backend server URL
        changeOrigin: true,
      },
    },
  },
})
