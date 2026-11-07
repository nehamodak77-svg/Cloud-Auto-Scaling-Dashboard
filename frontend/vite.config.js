import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxy: when React calls fetch('/api/...'), Vite forwards it to Flask (port 5001).
// This avoids CORS problems during development.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:5001',
    },
  },
})
