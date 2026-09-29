import { useEffect, useRef } from "react";
import {
  ArcElement, BarController, BarElement, CategoryScale, Chart, DoughnutController, LinearScale, Tooltip,
  type ChartConfiguration,
} from "chart.js";
import type { Category } from "../api";
import { useTheme } from "../App";

Chart.register(ArcElement, BarController, BarElement, CategoryScale, DoughnutController, LinearScale, Tooltip);

const PALETTE = ["#0A84FF", "#FF9F0A", "#BF5AF2", "#34C759", "#FF3B30", "#30D158"];
const FONT = { family: "-apple-system, BlinkMacSystemFont, sans-serif" };
const colours = (categories: Category[]) => categories.map((_, i) => PALETTE[i % PALETTE.length]);

// Creates the chart on mount and destroys it on unmount or when the data/theme changes.
function useChart(build: (css: (name: string) => string) => ChartConfiguration, deps: unknown[]) {
  const canvas = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const style = getComputedStyle(document.documentElement);
    const chart = new Chart(canvas.current!, build((name) => style.getPropertyValue(name).trim()));
    return () => chart.destroy();
  }, deps);
  return canvas;
}

function tooltip(dark: boolean) {
  return {
    backgroundColor: dark ? "rgba(10, 14, 10, 0.94)" : "rgba(255, 255, 255, 0.96)",
    borderColor: dark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.10)",
    borderWidth: 1,
    titleColor: dark ? "#F5F5F7" : "#1a1a1a",
    bodyColor: dark ? "#86868B" : "#555a55",
    cornerRadius: 10,
    padding: 10,
    titleFont: { ...FONT, size: 12, weight: 600 as const },
    bodyFont: { ...FONT, size: 11 },
    displayColors: false,
  };
}

export function PieChart({ categories }: { categories: Category[] }) {
  const theme = useTheme();
  const canvas = useChart(() => ({
    type: "doughnut",
    data: {
      labels: categories.map((c) => c.name),
      datasets: [{ data: categories.map((c) => c.percentage), backgroundColor: colours(categories), borderWidth: 0, hoverOffset: 5 }],
    },
    options: {
      responsive: false,
      cutout: "60%",
      plugins: { tooltip: { ...tooltip(theme === "dark"), callbacks: { label: (ctx) => ` ${ctx.parsed}% of total CO₂` } } },
    },
  }), [categories, theme]);

  return (
    <div className="pie-inner">
      <canvas ref={canvas} width="148" height="148" role="img" aria-label="Share of CO₂ by asset type" />
      <div className="pie-legend">
        {categories.map((c, i) => (
          <div className="legend-row" key={c.name}>
            <div className="legend-dot" style={{ background: PALETTE[i % PALETTE.length] }} />
            <span className="legend-name">{c.name}</span>
            <span className="legend-val">{c.percentage}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function BarChart({ categories }: { categories: Category[] }) {
  const theme = useTheme();
  const canvas = useChart((css) => {
    const ticks = { color: css("--text-sub"), font: { ...FONT, size: 10 } };
    return {
      type: "bar",
      data: {
        labels: categories.map((c) => c.name),
        datasets: [{ data: categories.map((c) => c.total_co2), backgroundColor: colours(categories), borderRadius: 7, borderSkipped: false }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { tooltip: { ...tooltip(theme === "dark"), callbacks: { label: (ctx) => ` ${ctx.parsed.y}g CO₂` } } },
        scales: {
          x: { grid: { display: false }, border: { display: false }, ticks },
          y: { grid: { color: css("--border") }, border: { display: false }, ticks: { ...ticks, callback: (v) => `${v}g` } },
        },
      },
    };
  }, [categories, theme]);

  return (
    <div className="bar-wrap">
      <canvas ref={canvas} role="img" aria-label="Grams of CO₂ per asset type" />
    </div>
  );
}
