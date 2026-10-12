import type { Asset } from "./api";

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(2)} MB`;
  return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
}

export function formatCO2(grams: number): string {
  if (grams < 0.001) return "< 0.001g";
  return grams < 1 ? `${grams.toFixed(3)}g` : `${grams.toFixed(2)}g`;
}

export function formatDate(iso: string): string {
  const d = new Date(iso);
  const diffMin = Math.floor((Date.now() - d.getTime()) / 60_000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffMin < 1440) return `${Math.floor(diffMin / 60)}h ago`;
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

export const ISSUES: Record<Asset["issues"][number], { label: string; detail: string }> = {
  uncompressed: { label: "Not compressed", detail: "Text files sent without Brotli or gzip" },
  legacy_format: { label: "Old image format", detail: "Images served as JPEG, PNG or GIF, not WebP or AVIF" },
  no_cache: { label: "Not cached", detail: "Files browsers can't reuse for at least a day" },
};

export const STATUS_COLOR: Record<Asset["status"], string> = { green: "var(--good)", amber: "var(--amber)", red: "var(--red)" };

export const gradeColor = (grade: string) => (grade.startsWith("A") || grade.startsWith("B") ? "var(--good)" : grade === "F" ? "var(--red)" : "var(--amber)");

export const TYPE_LABEL: Record<Asset["asset_type"], string> = { image: "IMG", script: "JS", css: "CSS", font: "FONT", media: "VID" };
