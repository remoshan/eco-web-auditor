"use strict";

const heroSection = document.getElementById("hero-section");
const loadingSection = document.getElementById("loading-section");
const resultsSection = document.getElementById("results-section");
const recentSection = document.getElementById("recent-section");
const urlInput = document.getElementById("url-input");
const searchWrap = document.getElementById("search-wrap");
const auditBtn = document.getElementById("audit-btn");

let currentAuditData = null;
let activeFilter = "all";
let loadTimer = null;

const LOADING_STEPS = [
  "Resolving DNS and connecting…",
  "Fetching page HTML…",
  "Parsing DOM and extracting assets…",
  "Measuring asset sizes…",
  "Applying SWD carbon model…",
  "Generating report…",
];

document.addEventListener("DOMContentLoaded", () => {
  loadRecentAudits();

  urlInput?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleAuditSubmit();
  });

  auditBtn?.addEventListener("click", handleAuditSubmit);
});

async function handleAuditSubmit() {
  const url = urlInput.value.trim();

  if (!url) {
    shakeSearchBar();
    return;
  }
  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    urlInput.value = "https://" + url;
  }

  const targetUrl = urlInput.value.trim();

  showLoading(targetUrl);
  startLoadingAnimation();

  try {
    const result = await callAuditApi(targetUrl);
    currentAuditData = result;
    stopLoadingAnimation();
    showResults(result);
    loadRecentAudits();
  } catch (err) {
    stopLoadingAnimation();
    showError(err.message || "An unexpected error occurred.");
    showHero();
  }
}

async function callAuditApi(url) {
  const response = await fetch(`${window.API_BASE}/api/audit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || `Server error (${response.status})`);
  }

  return data;
}

function showHero() {
  heroSection?.classList.remove("hidden");
  loadingSection?.classList.add("hidden");
  resultsSection?.classList.add("hidden");
}

function showLoading(url) {
  heroSection?.classList.add("hidden");
  loadingSection?.classList.remove("hidden");
  resultsSection?.classList.add("hidden");

  const loadingUrl = document.getElementById("loading-url");
  if (loadingUrl) loadingUrl.textContent = url;

  buildLoadingSteps();
}

function showResults(data) {
  loadingSection?.classList.add("hidden");
  resultsSection?.classList.remove("hidden");
  recentSection?.classList.remove("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });
  renderDashboard(data);
}

function buildLoadingSteps() {
  const container = document.getElementById("loading-steps");
  if (!container) return;

  container.innerHTML = LOADING_STEPS.map(
    (text, i) => `
    <div class="step-row" id="step-${i}">
      <div class="step-dot" id="step-dot-${i}">
        <svg class="check" width="8" height="8" viewBox="0 0 8 8" fill="none">
          <path d="M1.5 4L3.2 6L6.5 2" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <div class="pulse"></div>
      </div>
      <span class="step-text" id="step-text-${i}">${text}</span>
    </div>`
  ).join("");
}

function setStepState(index, state) {
  const dot = document.getElementById(`step-dot-${index}`);
  const text = document.getElementById(`step-text-${index}`);
  if (!dot) return;
  dot.classList.remove("done", "active");
  if (state) dot.classList.add(state);
  if (text) text.classList.toggle("lit", state !== null);
}

function startLoadingAnimation() {
  clearInterval(loadTimer);
  let step = 0;
  setStepState(0, "active");

  loadTimer = setInterval(() => {
    setStepState(step, "done");
    step++;
    if (step < LOADING_STEPS.length) {
      setStepState(step, "active");
    }
  }, 600);
}

function stopLoadingAnimation() {
  clearInterval(loadTimer);
  LOADING_STEPS.forEach((_, i) => setStepState(i, "done"));
}

function renderDashboard(data) {
  const { formatBytes, formatCO2, gradeColor, statusColor } = window.EcoUtil;

  const urlEl = document.getElementById("result-url");
  const gradePill = document.getElementById("result-grade-pill");
  if (urlEl) urlEl.textContent = data.url;
  if (gradePill) {
    const col = gradeColor(data.grade);
    gradePill.textContent = `${data.grade} Grade`;
    gradePill.style.background = `${col}18`;
    gradePill.style.border = `1px solid ${col}40`;
    gradePill.style.color = col;
  }

  const CIRC = 2 * Math.PI * 62;
  const filled = (data.score / 100) * CIRC;
  const col = gradeColor(data.grade);
  const label = data.score >= 80 ? "Sustainable"
    : data.score >= 60 ? "Needs Work"
      : "High Impact";

  setEl("gauge-arc", "stroke-dasharray", `${filled} ${CIRC}`);
  setEl("gauge-arc", "stroke", col);
  setEl("gauge-grade", "textContent", data.grade);
  setEl("gauge-score", "textContent", `Score ${data.score}/100`);
  const gaugeLabel = document.getElementById("gauge-label");
  if (gaugeLabel) { gaugeLabel.textContent = label; gaugeLabel.style.color = col; }

  setTxt("metric-co2", `${formatCO2(data.total_co2)}`);
  setTxt("metric-annual", `${data.annual_co2_kg} kg CO₂/yr`);
  setTxt("metric-weight", `${data.page_weight_mb} MB`);
  setTxt("metric-requests", `${data.request_count} requests`);
  setTxt("metric-comparison", data.comparison);
  setTxt("metric-trees", `${data.trees_to_offset} trees to offset annually`);

  renderMLCard(data);

  window.EcoCharts?.destroyAll();
  setTimeout(() => {
    window.EcoCharts?.renderPieChart("pie-chart", data.categories);
    window.EcoCharts?.renderBarChart("bar-chart", data.categories);
  }, 80);

  activeFilter = "all";
  renderAssets(data.assets, "all");
  setupFilterTabs(data.assets);
}

function renderMLCard(data) {
  const card = document.getElementById("ml-card");
  if (!card) return;

  const ml = data.ml_prediction;
  if (!ml) {
    card.classList.add("hidden");
    return;
  }

  const { formatCO2 } = window.EcoUtil;

  card.classList.remove("hidden");
  setTxt("ml-model-name", ml.model_name);
  setTxt("ml-r2", ml.r2_score != null ? ml.r2_score.toFixed(4) : "–");
  setTxt("ml-predicted", `${formatCO2(ml.predicted_co2_grams)}`);

  const diffEl = document.getElementById("ml-diff");
  if (diffEl) {
    const diff = ml.difference_pct;
    if (diff == null) {
      diffEl.textContent = "–";
    } else {
      const sign = diff > 0 ? "+" : "";
      diffEl.textContent = `${sign}${diff}%`;
      diffEl.style.color = Math.abs(diff) <= 15 ? "var(--green)" : "var(--amber)";
    }
  }

  setTxt("ml-swd-value", formatCO2(data.total_co2));
  setTxt("ml-model-value", formatCO2(ml.predicted_co2_grams));
}

const TYPE_META = {
  image: { label: "IMG", color: "#0A84FF" },
  script: { label: "JS", color: "#FF9F0A" },
  css: { label: "CSS", color: "#BF5AF2" },
  font: { label: "TTF", color: "#34C759" },
  media: { label: "VID", color: "#FF3B30" },
  other: { label: "?", color: "#86868B" },
};

function renderAssets(assets, filter) {
  const list = document.getElementById("asset-list");
  if (!list) return;

  const { formatBytes, formatCO2, statusColor } = window.EcoUtil;

  const filtered = filter === "all"
    ? assets
    : assets.filter((a) => a.status === filter);

  if (filtered.length === 0) {
    list.innerHTML = `<div style="font-size:13px;color:var(--text-sub);text-align:center;padding:24px 0;">
      No assets in this category.
    </div>`;
    return;
  }

  list.innerHTML = filtered.map((a) => {
    const col = statusColor(a.status);
    const meta = TYPE_META[a.asset_type] || TYPE_META.other;
    const id = `asset-${encodeURIComponent(a.url).slice(0, 30)}`;

    return `
    <div class="asset-row" id="${id}" onclick="toggleAsset('${id}')">
      <div class="asset-row-main">
        <span class="type-badge" style="color:${meta.color};background:${meta.color}18;border-color:${meta.color}35;">
          ${meta.label}
        </span>
        <div class="asset-info">
          <div class="asset-name">${escHtml(a.name)}</div>
          <div class="asset-size">${formatBytes(a.size_bytes)}</div>
        </div>
        <div class="asset-right">
          <span class="asset-co2" style="color:${col};">${formatCO2(a.co2_grams)} CO₂</span>
          <div class="status-dot" style="background:${col};box-shadow:0 0 5px ${col}90;"></div>
          <svg class="chevron" width="10" height="10" viewBox="0 0 10 10" fill="none">
            <path d="M2 3.5L5 6.5L8 3.5" stroke="#F5F5F7" stroke-width="1.4"
              stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
      </div>
      <div class="asset-tip">
        <svg class="tip-icon" width="14" height="14" viewBox="0 0 14 14" fill="none">
          <circle cx="7" cy="7" r="5.5" stroke="${col}" stroke-width="1.2"/>
          <path d="M7 5v2.5M7 9.5v.1" stroke="${col}" stroke-width="1.2" stroke-linecap="round"/>
        </svg>
        <span class="tip-text">${escHtml(a.optimization_tip || "No suggestion available.")}</span>
      </div>
    </div>`;
  }).join("");
}

window.toggleAsset = function (id) {
  document.getElementById(id)?.classList.toggle("open");
};

const TAB_CONFIG = [
  { key: "all", label: "All", cls: "active-all" },
  { key: "red", label: "Critical", cls: "active-red" },
  { key: "amber", label: "Moderate", cls: "active-amber" },
  { key: "green", label: "Optimised", cls: "active-green" },
];

function setupFilterTabs(assets) {
  const container = document.getElementById("filter-tabs");
  if (!container) return;

  container.innerHTML = TAB_CONFIG.map(
    ({ key, label, cls }) => `
    <button
      class="filter-tab ${key === "all" ? cls : ""}"
      data-filter="${key}"
      data-cls="${cls}"
      onclick="applyFilter('${key}', this, event)">
      ${label}
    </button>`
  ).join("");
}

window.applyFilter = function (filter, btn, event) {
  event?.stopPropagation();
  activeFilter = filter;

  document.querySelectorAll(".filter-tab").forEach((t) => {
    t.className = "filter-tab";
  });
  btn.classList.add(btn.dataset.cls);

  renderAssets(currentAuditData?.assets || [], filter);
};

async function loadRecentAudits() {
  try {
    const res = await fetch(`${window.API_BASE}/api/audits/recent?limit=8`);
    if (!res.ok) return;
    renderRecentAudits(await res.json());
  } catch (_) {
    // non-critical: history list just stays empty
  }
}

function renderRecentAudits(audits) {
  const grid = document.getElementById("recent-grid");
  if (!grid) return;

  const { formatCO2, gradeColor, formatDate } = window.EcoUtil;

  if (audits.length === 0) {
    grid.innerHTML = `<p style="font-size:13px;color:var(--text-sub);">No audits yet. Run your first one above!</p>`;
    return;
  }

  grid.innerHTML = audits.map((a) => {
    const col = gradeColor(a.grade);
    return `
    <div class="recent-row" onclick="loadAuditById(${a.audit_id})">
      <div class="recent-url" title="${escHtml(a.url)}">${escHtml(a.url)}</div>
      <div class="recent-co2 sub">${formatCO2(a.total_co2)} CO₂</div>
      <div class="recent-co2 sub">${a.page_weight_mb} MB</div>
      <div class="grade-chip"
        style="background:${col}18;border:1px solid ${col}40;color:${col}">
        ${a.grade}
      </div>
      <div class="recent-date sub">${formatDate(a.created_at)}</div>
    </div>`;
  }).join("");

  recentSection?.classList.remove("hidden");
}

window.loadAuditById = async function (id) {
  showLoading("Loading saved audit…");
  startLoadingAnimation();
  try {
    const res = await fetch(`${window.API_BASE}/api/audit/${id}`);
    if (!res.ok) throw new Error("Could not load audit.");
    const data = await res.json();
    currentAuditData = data;
    stopLoadingAnimation();
    showResults(data);
  } catch (err) {
    stopLoadingAnimation();
    showError(err.message);
    showHero();
  }
};

function setEl(id, attr, value) {
  const el = document.getElementById(id);
  if (!el) return;
  if (attr === "textContent") el.textContent = value;
  else el.setAttribute(attr, value);
}
function setTxt(id, text) { setEl(id, "textContent", text); }

function shakeSearchBar() {
  if (!searchWrap) return;
  searchWrap.style.boxShadow = "0 0 0 3px rgba(255,59,48,0.35)";
  setTimeout(() => (searchWrap.style.boxShadow = ""), 700);
}

function showError(msg) {
  const banner = document.getElementById("error-banner");
  if (banner) {
    banner.textContent = `⚠ ${msg}`;
    banner.classList.remove("hidden");
    setTimeout(() => banner.classList.add("hidden"), 6000);
  } else {
    alert(`Error: ${msg}`);
  }
}

function escHtml(str) {
  const d = document.createElement("div");
  d.textContent = str ?? "";
  return d.innerHTML;
}

window.goBack = function () {
  resultsSection?.classList.add("hidden");
  loadingSection?.classList.add("hidden");
  heroSection?.classList.remove("hidden");
  urlInput.value = "";
  currentAuditData = null;
  window.scrollTo({ top: 0, behavior: "smooth" });
};
