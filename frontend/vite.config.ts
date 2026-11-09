import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // Dev proxy: the browser only ever talks to Vite (localhost:5173).
    // Any request starting with /api is forwarded to Flask, with the /api prefix removed:
    //   GET /api/recipes/5  ->  GET http://127.0.0.1:5001/recipes/5
    // Because the browser sees a single origin, Flask doesn't need CORS headers.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
