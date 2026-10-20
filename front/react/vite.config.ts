import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { resolve } from 'node:path';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: '/static/react/',
  build: {
    outDir: resolve(__dirname, '../static/react'),
    emptyOutDir: true,
    manifest: 'manifest.json',
    rollupOptions: { input: resolve(__dirname, 'index.html') },
  },
  server: { host: '127.0.0.1', port: 5173, strictPort: true },
});
