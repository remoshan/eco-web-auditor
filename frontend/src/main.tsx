import { StrictMode, type ComponentType } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, redirect } from "react-router";
import { RouterProvider } from "react-router/dom";
import App, { RouteError } from "./App";
import Home from "./pages/Home";
import "./styles.css";

const RELOAD_KEY = "chunk-reload";

const page = (load: () => Promise<{ default: ComponentType }>) => () =>
  load().then(
    (module) => ({ Component: module.default }),
    (err) => {
      try {
        if (Date.now() - Number(sessionStorage.getItem(RELOAD_KEY)) > 10_000) {
          sessionStorage.setItem(RELOAD_KEY, String(Date.now()));
          const next = router.state.navigation.location;
          location.assign(next ? router.createHref(next) : location.href);
          return new Promise<never>(() => {});
        }
      } catch {}
      throw err;
    },
  );

const router = createBrowserRouter([
  {
    Component: App,
    HydrateFallback: () => null,
    children: [
      {
        ErrorBoundary: RouteError,
        children: [
          { index: true, Component: Home },
          { path: "audits/:id", lazy: page(() => import("./pages/AuditResult")) },
          { path: "compare/:a/:b", lazy: page(() => import("./pages/Compare")) },
          { path: "about", lazy: page(() => import("./pages/About")) },
          { path: "*", loader: () => redirect("/") },
        ],
      },
    ],
  },
]);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
);
