import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const backend = "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: { host: true, proxy: { "/api": backend, "/docs": backend, "/openapi.json": backend } },
});
