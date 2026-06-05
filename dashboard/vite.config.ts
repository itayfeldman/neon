import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/stock': 'http://localhost:8000',
      '/portfolio': 'http://localhost:8000',
      '/bonds': 'http://localhost:8000',
    },
  },
  optimizeDeps: {
    exclude: ['plotly.js', 'react-plotly.js'],
  },
})
