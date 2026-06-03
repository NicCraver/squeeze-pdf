import vue from '@vitejs/plugin-vue'
import UnoCSS from 'unocss/vite'
import { defineConfig } from 'vite-plus'

export default defineConfig({
  plugins: [vue(), UnoCSS()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8765',
        changeOrigin: true,
      },
      '/api/ws': {
        target: 'http://127.0.0.1:8765',
        ws: true,
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../../backend/static',
    emptyOutDir: true,
  },
})
