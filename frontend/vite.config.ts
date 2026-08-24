import { fileURLToPath, URL } from "node:url";

import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

const API_TARGET = process.env.VITE_API_TARGET ?? "http://localhost:8000";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  server: {
    port: 5173,
    // Same-origin in dev, so the httpOnly auth cookie behaves as it does in production.
    proxy: { "/api": { target: API_TARGET, changeOrigin: true } },
  },
});
