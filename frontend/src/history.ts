import { get, set, setMany, getMany, delMany } from "idb-keyval";
import type { Audit } from "./api";

export type HistoryEntry = Pick<Audit, "id" | "url" | "grade" | "total_co2" | "page_weight_mb" | "audited_at">;

const INDEX_KEY = "history";
const MAX_ENTRIES = 50;
const MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000;
const reportKey = (id: string) => `audit:${id}`;
const readIndex = async () => (await get<HistoryEntry[]>(INDEX_KEY)) ?? [];

async function prune(entries: HistoryEntry[], changed: boolean): Promise<HistoryEntry[]> {
  const cutoff = Date.now() - MAX_AGE_MS;
  const kept = entries
    .filter((e) => Date.parse(e.audited_at) >= cutoff)
    .sort((a, b) => Date.parse(b.audited_at) - Date.parse(a.audited_at))
    .slice(0, MAX_ENTRIES);
  if (changed || kept.length !== entries.length) {
    await set(INDEX_KEY, kept);
    await delMany(entries.filter((e) => !kept.includes(e)).map((e) => reportKey(e.id)));
  }
  return kept;
}

async function store(audits: Audit[]): Promise<HistoryEntry[]> {
  const ids = new Set(audits.map((a) => a.id));
  await setMany(audits.map((a) => [reportKey(a.id), a]));
  const added = audits.map(({ id, url, grade, total_co2, page_weight_mb, audited_at }) => ({ id, url, grade, total_co2, page_weight_mb, audited_at }));
  const kept = await prune([...added, ...(await readIndex()).filter((e) => !ids.has(e.id))], true);
  return kept.filter((e) => ids.has(e.id));
}

export const listHistory = async () => prune(await readIndex(), false);

export const saveAudit = (audit: Audit) => store([audit]);

export const loadAudit = (id: string) => get<Audit>(reportKey(id));

export async function clearHistory(): Promise<void> {
  const entries = await readIndex();
  await delMany([INDEX_KEY, ...entries.map((e) => reportKey(e.id))]);
}

export function downloadJson(name: string, data: unknown): void {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
  link.download = name;
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href));
}

export async function exportHistory(): Promise<void> {
  const reports = await getMany<Audit | undefined>((await readIndex()).map((e) => reportKey(e.id)));
  downloadJson(`ecoweb-history-${new Date().toISOString().slice(0, 10)}.json`, reports.filter(Boolean));
}

export async function importHistory(data: unknown): Promise<number> {
  const isAudit = (a: Partial<Audit>) =>
    typeof a?.id === "string" && typeof a.url === "string" && Array.isArray(a.assets) && Array.isArray(a.categories) && !Number.isNaN(Date.parse(a.audited_at ?? ""));
  const audits = (Array.isArray(data) ? data : []).filter(isAudit);
  if (!audits.length) throw new Error("That file isn't an EcoWeb Auditor history export.");
  return (await store(audits)).length;
}
