import { get, set, delMany } from "idb-keyval";
import type { Audit } from "./api";

export type HistoryEntry = Pick<Audit, "id" | "url" | "grade" | "total_co2" | "page_weight_mb" | "audited_at">;

const INDEX_KEY = "history";
const MAX_ENTRIES = 50;
const MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000;
const reportKey = (id: string) => `audit:${id}`;
const readIndex = async () => (await get<HistoryEntry[]>(INDEX_KEY)) ?? [];

async function prune(entries: HistoryEntry[], changed: boolean): Promise<HistoryEntry[]> {
  const cutoff = Date.now() - MAX_AGE_MS;
  const kept = entries.filter((e) => Date.parse(e.audited_at) >= cutoff).slice(0, MAX_ENTRIES);
  if (changed || kept.length !== entries.length) {
    await set(INDEX_KEY, kept);
    await delMany(entries.filter((e) => !kept.includes(e)).map((e) => reportKey(e.id)));
  }
  return kept;
}

export const listHistory = async () => prune(await readIndex(), false);

export async function saveAudit(audit: Audit): Promise<void> {
  const { id, url, grade, total_co2, page_weight_mb, audited_at } = audit;
  await set(reportKey(id), audit);
  await prune([{ id, url, grade, total_co2, page_weight_mb, audited_at }, ...(await readIndex())], true);
}

export const loadAudit = (id: string) => get<Audit>(reportKey(id));

export async function clearHistory(): Promise<void> {
  const entries = await readIndex();
  await delMany([INDEX_KEY, ...entries.map((e) => reportKey(e.id))]);
}
