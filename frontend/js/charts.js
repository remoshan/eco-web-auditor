/**
 * js/charts.js
 * ────────────
 * Chart.js wrapper functions for the results dashboard.
 * Requires Chart.js loaded from CDN before this script.
 *
 * Exports (on window.EcoCharts):
 *   renderPieChart(canvasId, categories)
 *   renderBarChart(canvasId, categories)
 *   destroyAll()   – call before re-rendering on a new audit
 */

(function () {
  "use strict";

  // Keep references so we can destroy charts before re-rendering
  const _instances = {};

  // Colour palette matching the CSS custom properties
  const PALETTE = ["#0A84FF", "#FF9F0A", "#BF5AF2", "#34C759", "#FF3B30", "#30D158"];

  // Shared Chart.js tooltip style — reads CSS variables so it adapts to theme
  function getTooltipStyle() {
    const isDark = document.documentElement.getAttribute("data-theme") !== "light";
    return {
      backgroundColor: isDark ? "rgba(10, 14, 10, 0.94)" : "rgba(255, 255, 255, 0.96)",
      borderColor:     isDark ? "rgba(255,255,255,0.08)"  : "rgba(0,0,0,0.10)",
      borderWidth:     1,
      titleColor:      isDark ? "#F5F5F7" : "#1a1a1a",
      bodyColor:       isDark ? "#86868B" : "#555a55",
      cornerRadius:    10,
      padding:         10,
      titleFont: { family: "-apple-system, BlinkMacSystemFont, sans-serif", size: 12, weight: "600" },
      bodyFont:  { family: "-apple-system, BlinkMacSystemFont, sans-serif", size: 11 },
      displayColors: false,
    };
  }

  /**
   * Destroy a named chart instance if it exists.
   * @param {string} name
   */
  function destroy(name) {
    if (_instances[name]) {
      _instances[name].destroy();
      delete _instances[name];
    }
  }

  /** Destroy all chart instances (call before re-rendering). */
  function destroyAll() {
    Object.keys(_instances).forEach(destroy);
  }

  /**
   * Render a doughnut/pie chart showing CO2 share by asset category.
   *
   * @param {string} canvasId   - <canvas> element id
   * @param {Array}  categories - Array of CategoryBreakdown objects from the API
   */
  function renderPieChart(canvasId, categories) {
    destroy("pie");
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const labels = categories.map((c) => c.name);
    const data   = categories.map((c) => parseFloat(c.percentage.toFixed(1)));
    const colors = categories.map((_, i) => PALETTE[i % PALETTE.length]);

    _instances["pie"] = new Chart(canvas, {
      type: "doughnut",
      data: {
        labels,
        datasets: [
          {
            data,
            backgroundColor: colors,
            borderWidth: 0,
            hoverOffset: 5,
          },
        ],
      },
      options: {
        responsive: false,
        cutout: "60%",
        plugins: {
          legend: { display: false },
          tooltip: {
            ...getTooltipStyle(),
            callbacks: {
              label: (ctx) => ` ${ctx.parsed}% of total CO₂`,
            },
          },
        },
      },
    });

    // Build legend separately so we can show CO2 grams alongside percentage
    buildPieLegend(canvasId, categories, colors);
  }

  /**
   * Build the custom legend next to the pie chart.
   */
  function buildPieLegend(canvasId, categories, colors) {
    const legendId = canvasId.replace("chart", "legend");
    const legend = document.getElementById(legendId);
    if (!legend) return;

    legend.innerHTML = categories
      .map(
        (c, i) => `
        <div class="legend-row">
          <div class="legend-dot" style="background:${colors[i]};box-shadow:0 0 5px ${colors[i]}80"></div>
          <span class="legend-name">${c.name}</span>
          <span class="legend-val">${c.percentage}%</span>
        </div>`
      )
      .join("");
  }

  /**
   * Render a bar chart showing CO2 grams per asset category.
   *
   * @param {string} canvasId   - <canvas> element id
   * @param {Array}  categories - Array of CategoryBreakdown objects from the API
   */
  function renderBarChart(canvasId, categories) {
    destroy("bar");
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const labels = categories.map((c) => c.name);
    const data   = categories.map((c) => parseFloat(c.total_co2.toFixed(4)));
    const colors = categories.map((_, i) => PALETTE[i % PALETTE.length]);

    _instances["bar"] = new Chart(canvas, {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: "CO₂ (g)",
            data,
            backgroundColor: colors,
            borderRadius: 7,
            borderSkipped: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            ...getTooltipStyle(),
            callbacks: {
              label: (ctx) => ` ${ctx.parsed.y}g CO₂`,
            },
          },
        },
        scales: {
          x: {
            grid:   { display: false },
            border: { display: false },
            ticks: {
              color: document.documentElement.getAttribute("data-theme") === "light" ? "#555a55" : "#86868B",
              font: { family: "-apple-system, BlinkMacSystemFont, sans-serif", size: 10 },
            },
          },
          y: {
            grid:   { color: document.documentElement.getAttribute("data-theme") === "light" ? "rgba(0,0,0,0.06)" : "rgba(255,255,255,0.04)" },
            border: { display: false },
            ticks: {
              color: document.documentElement.getAttribute("data-theme") === "light" ? "#555a55" : "#86868B",
              font: { family: "-apple-system, BlinkMacSystemFont, sans-serif", size: 10 },
              callback: (v) => `${v}g`,
            },
          },
        },
      },
    });
  }

  // ── Public API ──────────────────────────────────────────────────────────────
  window.EcoCharts = { renderPieChart, renderBarChart, destroyAll };
})();
