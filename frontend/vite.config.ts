import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

const backend = "http://localhost:8000";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.svg", "apple-touch-icon-180x180.png"],
      manifest: {
        name: "EcoWeb Auditor",
        short_name: "EcoWeb",
        description: "Estimate the carbon footprint of any web page, element by element.",
        theme_color: "#060c06",
        background_color: "#060c06",
        display: "standalone",
        icons: [
          { src: "pwa-192x192.png", sizes: "192x192", type: "image/png" },
          { src: "pwa-512x512.png", sizes: "512x512", type: "image/png" },
          { src: "maskable-icon-512x512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
        ],
      },
      workbox: { navigateFallback: "/index.html", navigateFallbackDenylist: [/^\/api/, /^\/docs/, /^\/openapi\.json/] },
    }),
  ],
  server: { host: true, proxy: { "/api": backend, "/docs": backend, "/openapi.json": backend } },
});
