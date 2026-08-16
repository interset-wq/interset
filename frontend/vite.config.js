import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// 构建产物输出到项目根目录 dist/，由 FastAPI 的 app.frontend 托管
export default defineConfig({
  plugins: [vue()],
  build: {
    outDir: "../dist",
    emptyOutDir: true,
  },
  server: {
    // 本地开发时把 /api 代理到 FastAPI 后端（生产环境同源，无需代理）
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
