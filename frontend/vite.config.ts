import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // Ensure asset paths resolve correctly when served by FastAPI at '/'
  base: '/',
  server: {
    port: 5173,
    open: true,
  },
  preview: {
    port: 5173,
  },
  // Rely on Vite's default chunking to avoid execution order issues
  build: {},
});
