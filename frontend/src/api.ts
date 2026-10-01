import type { components } from "./api-types";

type Schemas = components["schemas"];
export type Audit = Schemas["AuditResponse"];
export type Asset = Schemas["AssetInfo"];
export type Category = Schemas["CategoryBreakdown"];
export type Comparison = Schemas["CompareResponse"];
export type CompareRow = Schemas["CompareRow"];
export type Methodology = Schemas["Methodology"];

const LOCAL = import.meta.env.DEV || ["localhost", "127.0.0.1"].includes(location.hostname);
export const API_ORIGIN = LOCAL ? "" : "https://ecoweb-auditor-api.onrender.com";

async function request<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const init = body === undefined ? { signal } : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal };
  const res = await fetch(API_ORIGIN + path, init).catch((err) => {
    throw signal?.aborted ? err : new Error("Couldn't reach the server. Check your connection and try again.");
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(typeof data?.detail === "string" ? data.detail : `Server error (${res.status})`);
  return data as T;
}

export const runAudit = (url: string, refresh: boolean, signal?: AbortSignal) =>
  request<Audit>("/api/audit", { url, refresh }, signal);

export const compareAudits = (a: Audit, b: Audit, signal?: AbortSignal) =>
  request<Comparison>("/api/compare", { a: { ...a, assets: [] }, b: { ...b, assets: [] } }, signal);

export const getMethodology = (signal?: AbortSignal) => request<Methodology>("/api/methodology", undefined, signal);
