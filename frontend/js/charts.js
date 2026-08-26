// Requires Chart.js to be loaded from the CDN before this script.

(function () {
  "use strict";

  const _instances = {};
  const PALETTE = ["#0A84FF", "#FF9F0A", "#BF5AF2", "#34C759", "#FF3B30", "#30D158"];

  function getTooltipStyle() {
    const isDark = document.documentElement.getAttribute("data-theme") !== "light";
    return {
      backgroundColor: isDark ? "rgba(10, 14, 10, 0.94)" : "rgba(255, 255, 255, 0.96)",
      borderColor: isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.10)",
      borderWidth: 1,
      titleColor: isDark ? "#F5F5F7" : "#1a1a1a",
      bodyColor: isDark ? "#86868B" : "#555a55",
      cornerRadius: 10,
      padding: 10,
      titleFont: { family: "-apple-system, BlinkMacSystemFont, sans-serif", size: 12, weight: "600" },
      bodyFont: { family: "-apple-system, BlinkMacSystemFont, sans-serif", size: 11 },
      displayColors: false,
    };
  }

  function destroy(name) {
    if (_instances[name]) {
      _instances[name].destroy();
      delete _instances[name];
    }
  }

  function destroyAll() {
    Object.keys(_instances).forEach(destroy);
  }

  function renderPieChart(canvasId, categories) {
    destroy("pie");
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const labels = categories.map((c) => c.name);
    const data = categories.map((c) => parseFloat(c.percentage.toFixed(1)));
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

    buildPieLegend(canvasId, categories, colors);
  }

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

  function renderBarChart(canvasId, categories) {
    destroy("bar");
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const labels = categories.map((c) => c.name);
    const data = categories.map((c) => parseFloat(c.total_co2.toFixed(4)));
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
            grid: { display: false },
            border: { display: false },
            ticks: {
              color: document.documentElement.getAttribute("data-theme") === "light" ? "#555a55" : "#86868B",
              font: { family: "-apple-system, BlinkMacSystemFont, sans-serif", size: 10 },
            },
          },
          y: {
            grid: { color: document.documentElement.getAttribute("data-theme") === "light" ? "rgba(0,0,0,0.06)" : "rgba(255,255,255,0.04)" },
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

  window.EcoCharts = { renderPieChart, renderBarChart, destroyAll };
})();
