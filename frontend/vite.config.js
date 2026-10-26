import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  plugins: [react()],
  server: {
    port: 5174,
    proxy: {
      '/api': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
    },
  },
  build: {
    target: 'es2020',
    cssCodeSplit: true,
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'three-core': ['three'],
          'three-fiber': ['@react-three/fiber'],
          'three-drei': ['@react-three/drei'],
          'firebase-app': ['firebase/app'],
          'firebase-auth': ['firebase/auth'],
          'firebase-firestore': ['firebase/firestore'],
          'firebase-storage': ['firebase/storage'],
          'firebase-messaging': ['firebase/messaging'],
          'ui-vendor': ['framer-motion', 'lucide-react', '@dnd-kit/core', '@dnd-kit/sortable'],
        },
      },
    },
    esbuild: false,
  },
})
