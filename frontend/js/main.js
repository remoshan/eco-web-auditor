/**
 * js/main.js
 * ──────────
 * Shared utilities used by both pages:
 *   - API base URL
 *   - Active nav link highlighting
 *   - Light / Dark theme toggle (persisted in localStorage)
 *   - Formatting helpers
 */

// ── API Configuration ─────────────────────────────────────────────────────────
// Change this if you run the backend on a different port or host.
window.API_BASE = "https://ecoweb-auditor-api.onrender.com";

// ── Theme Management ──────────────────────────────────────────────────────────

/**
 * Apply a theme to the document and persist the preference.
 * @param {"dark"|"light"} theme
 */
function applyTheme(theme) {
  const html = document.documentElement;
  if (theme === "light") {
    html.setAttribute("data-theme", "light");
  } else {
    html.removeAttribute("data-theme");
  }
  localStorage.setItem("ecoweb-theme", theme);
}

/**
 * Toggle between light and dark and update all toggle buttons on the page.
 */
function toggleTheme() {
  const current = localStorage.getItem("ecoweb-theme") || "dark";
  applyTheme(current === "dark" ? "light" : "dark");
}

// Expose globally so onclick attributes in HTML can call it
window.toggleTheme = toggleTheme;

// ── Active nav link ───────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  // 1. Restore saved theme on every page load (before paint to avoid flash)
  const saved = localStorage.getItem("ecoweb-theme") || "dark";
  applyTheme(saved);

  // 2. Highlight the correct nav link for the current page
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
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
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
  return { green: "#34C759", amber: "#FF9F0A", red: "#FF3B30" }[status] ?? "#86868B";
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
window.EcoUtil = { formatBytes, formatCO2, statusColor, gradeColor, formatDate };
