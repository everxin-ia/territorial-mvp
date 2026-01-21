import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/signals": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/alerts": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/territories": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/rules": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
