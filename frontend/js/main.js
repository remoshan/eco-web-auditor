/**
 * js/main.js
 * ──────────
 * Shared utilities used by both pages:
 *   - API base URL configuration
 *   - Active nav link highlighting
 *   - Formatting helpers
 */

// ── API Configuration ─────────────────────────────────────────────────────────
// Change this if you run the backend on a different port or host.
window.API_BASE = "http://localhost:8000";

// ── Active nav link ───────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const currentPage = window.location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".nav-links a").forEach((link) => {
    const href = link.getAttribute("href");
    if (href === currentPage || (currentPage === "" && href === "index.html")) {
      link.classList.add("active");
    }
  });
});

// ── Formatting helpers ────────────────────────────────────────────────────────

/**
 * Format bytes into a human-readable string (B, KB, MB, GB).
 * @param {number} bytes
 * @returns {string}
 */
function formatBytes(bytes) {
  if (bytes === 0) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024)
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

/**
 * Format a CO2 value in grams with sensible precision.
 * @param {number} grams
 * @returns {string}
 */
function formatCO2(grams) {
  if (grams < 0.001) return "< 0.001g";
  if (grams < 1) return `${grams.toFixed(3)}g`;
  return `${grams.toFixed(2)}g`;
}

/**
 * Return the hex colour associated with a status string.
 * @param {"green"|"amber"|"red"} status
 * @returns {string}
 */
function statusColor(status) {
  return (
    { green: "#34C759", amber: "#FF9F0A", red: "#FF3B30" }[status] ?? "#86868B"
  );
}

/**
 * Return the hex colour for a sustainability grade.
 * @param {string} grade  e.g. "A+", "B", "F"
 * @returns {string}
 */
function gradeColor(grade) {
  if (["A+", "A"].includes(grade)) return "#34C759";
  if (["B+", "B"].includes(grade)) return "#30D158";
  if (grade === "C") return "#FF9F0A";
  if (grade === "D") return "#FF6B30";
  return "#FF3B30";
}

/**
 * Format an ISO date string to a readable relative or short date.
 * @param {string} iso
 * @returns {string}
 */
function formatDate(iso) {
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now - d;
  const diffMin = Math.floor(diffMs / 60_000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffMin < 1440) return `${Math.floor(diffMin / 60)}h ago`;
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

// ── Expose to other scripts ───────────────────────────────────────────────────
window.EcoUtil = {
  formatBytes,
  formatCO2,
  statusColor,
  gradeColor,
  formatDate,
};
