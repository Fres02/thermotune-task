import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // listen on 0.0.0.0 so the dev server is reachable from a Docker container
    port: 5173,
    watch: {
      // Docker Desktop on Windows doesn't reliably propagate native fs change
      // events through bind mounts -- fall back to polling so edits are seen.
      usePolling: true,
      interval: 300,
    },
  },
})
