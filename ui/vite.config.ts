import fs from 'fs'
import path from 'path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// In container builds the shared UI is at /mees-shared-ui,
// in local dev it's at ../../mees-shared-ui
const sharedUiPath = fs.existsSync('/mees-shared-ui/src')
  ? '/mees-shared-ui/src'
  : path.resolve(__dirname, '../../mees-shared-ui/src')

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@mees/shared-ui': sharedUiPath,
    },
    dedupe: ['react', 'react-dom', '@tanstack/react-query'],
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8200',
        changeOrigin: true,
      },
    },
  },
})
