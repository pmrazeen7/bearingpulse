import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const backend = env.BACKEND_URL || "http://localhost:8000";
  const proxy = Object.fromEntries(["/api", "/docs", "/openapi.json"].map((path) => [path, { target: backend, changeOrigin: true }]));
  return {
    plugins: [react()],
    server: { host: "0.0.0.0", port: 3000, proxy },
    preview: { host: "0.0.0.0", port: 3000, proxy },
    build: {
      sourcemap: false,
      rollupOptions: {
        output: { manualChunks: { react: ["react", "react-dom", "react-router-dom"], icons: ["lucide-react"] } },
      },
    },
    test: {
      environment: "jsdom",
      setupFiles: ["./src/test/setup.js"],
      globals: true,
      css: false,
    },
  };
});
