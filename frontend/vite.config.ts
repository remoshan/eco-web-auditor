import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const backend = "http://localhost:8000";

// The dev and preview servers forward API calls to the local backend, so no CORS setup is needed locally.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    proxy: { "/api": backend, "/docs": backend, "/openapi.json": backend },
  },
});
