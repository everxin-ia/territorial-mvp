import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // API Backend (local dev sin docker)
      "/signals": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/alerts": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/territories": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/alert-rules": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/export": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/health": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/debug": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
