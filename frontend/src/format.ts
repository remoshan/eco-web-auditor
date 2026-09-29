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

export const STATUS_COLOR: Record<string, string> = { green: "#34C759", amber: "#FF9F0A", red: "#FF3B30" };

export function gradeColor(grade: string): string {
  if (grade === "A+" || grade === "A") return "#34C759";
  if (grade === "B+" || grade === "B") return "#30D158";
  if (grade === "C") return "#FF9F0A";
  if (grade === "D") return "#FF6B30";
  return "#FF3B30";
}

export const TYPE_META: Record<Asset["asset_type"], { label: string; color: string }> = {
  image: { label: "IMG", color: "#0A84FF" },
  script: { label: "JS", color: "#FF9F0A" },
  css: { label: "CSS", color: "#BF5AF2" },
  font: { label: "TTF", color: "#34C759" },
  media: { label: "VID", color: "#FF3B30" },
};
