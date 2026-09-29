import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, redirect } from "react-router";
import { RouterProvider } from "react-router/dom";
import App from "./App";
import Home from "./pages/Home";
import "./styles.css";

// Everything except the home page is split into its own chunk and fetched on first visit.
const router = createBrowserRouter([
  {
    Component: App,
    HydrateFallback: () => null,
    children: [
      { index: true, Component: Home },
      { path: "audits/:id", lazy: async () => ({ Component: (await import("./pages/AuditResult")).default }) },
      { path: "compare/:a/:b", lazy: async () => ({ Component: (await import("./pages/Compare")).default }) },
      { path: "about", lazy: async () => ({ Component: (await import("./pages/About")).default }) },
      { path: "*", loader: () => redirect("/") },
    ],
  },
]);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
);
