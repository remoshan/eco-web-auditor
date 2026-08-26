// Points at the deployed Render backend. Change for local development.
window.API_BASE = "https://ecoweb-auditor-api.onrender.com";

function applyTheme(theme) {
  const html = document.documentElement;
  if (theme === "light") {
    html.setAttribute("data-theme", "light");
  } else {
    html.removeAttribute("data-theme");
  }
  localStorage.setItem("ecoweb-theme", theme);
}

function toggleTheme() {
  const current = localStorage.getItem("ecoweb-theme") || "dark";
  applyTheme(current === "dark" ? "light" : "dark");
}

window.toggleTheme = toggleTheme;

document.addEventListener("DOMContentLoaded", () => {
  applyTheme(localStorage.getItem("ecoweb-theme") || "dark");

  const currentPage = window.location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".nav-links a").forEach((link) => {
    const href = link.getAttribute("href");
    if (href === currentPage || (currentPage === "" && href === "index.html")) {
      link.classList.add("active");
    }
  });
});

function formatBytes(bytes) {
  if (bytes === 0) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

function formatCO2(grams) {
  if (grams < 0.001) return "< 0.001g";
  if (grams < 1) return `${grams.toFixed(3)}g`;
  return `${grams.toFixed(2)}g`;
}

function statusColor(status) {
  return { green: "#34C759", amber: "#FF9F0A", red: "#FF3B30" }[status] ?? "#86868B";
}

function gradeColor(grade) {
  if (["A+", "A"].includes(grade)) return "#34C759";
  if (["B+", "B"].includes(grade)) return "#30D158";
  if (grade === "C") return "#FF9F0A";
  if (grade === "D") return "#FF6B30";
  return "#FF3B30";
}

function formatDate(iso) {
  const d = new Date(iso);
  const now = new Date();
  const diffMin = Math.floor((now - d) / 60_000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffMin < 1440) return `${Math.floor(diffMin / 60)}h ago`;
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

window.EcoUtil = { formatBytes, formatCO2, statusColor, gradeColor, formatDate };
