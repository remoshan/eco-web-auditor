import type { components } from "./api-types";

type Schemas = components["schemas"];
export type Audit = Schemas["AuditResponse"];
export type Asset = Schemas["AssetInfo"];
export type Category = Schemas["CategoryBreakdown"];
export type Comparison = Schemas["CompareResponse"];
export type CompareRow = Schemas["CompareRow"];
export type Methodology = Schemas["Methodology"];

// Locally the Vite server proxies to the backend; the deployed site calls Render directly.
const LOCAL = import.meta.env.DEV || ["localhost", "127.0.0.1"].includes(location.hostname);
export const API_ORIGIN = LOCAL ? "" : "https://ecoweb-auditor-api.onrender.com";

async function request<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  let res: Response;
  try {
    res = await fetch(API_ORIGIN + path, {
      method: body === undefined ? "GET" : "POST",
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    });
  } catch (err) {
    if (signal?.aborted) throw err;
    throw new Error("Couldn't reach the server. Check your connection and try again.");
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(typeof data?.detail === "string" ? data.detail : `Server error (${res.status})`);
  return data as T;
}

export const runAudit = (url: string, signal?: AbortSignal) => request<Audit>("/api/audit", { url }, signal);

// Assets aren't part of a comparison, so they're left out of the upload.
export const compareAudits = (a: Audit, b: Audit, signal?: AbortSignal) =>
  request<Comparison>("/api/compare", { a: { ...a, assets: [] }, b: { ...b, assets: [] } }, signal);

export const getMethodology = (signal?: AbortSignal) => request<Methodology>("/api/methodology", undefined, signal);
