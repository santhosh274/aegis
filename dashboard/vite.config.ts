import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // tsconfig.tsbuildinfo (written by tsc -b) is not part of the app graph —
    // ignore it so type-check runs never trigger a full page reload.
    watch: {
      ignored: ["**/tsconfig.tsbuildinfo", "**/node_modules/.tmp/**"],
    },
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/ws": {
        target: "ws://127.0.0.1:8000",
        ws: true,
      },
    },
  },
});