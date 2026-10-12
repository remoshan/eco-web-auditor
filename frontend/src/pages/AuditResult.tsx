import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router";
import type { Asset, Audit } from "../api";
import { downloadJson, listHistory, loadAudit, type HistoryEntry } from "../history";
import { ISSUES, STATUS_COLOR, TYPE_LABEL, formatBytes, formatCO2, formatDate, gradeColor } from "../format";
import { BackButton, Missing } from "../App";

export default function AuditResult() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const [audit, setAudit] = useState<Audit | null | undefined>(undefined);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let active = true;
    loadAudit(id)
      .then((a) => active && setAudit(a ?? null))
      .catch(() => active && setAudit(null));
    return () => {
      active = false;
    };
  }, [id]);

  if (audit === undefined) return <div className="page" />;
  if (audit === null) return <Missing text="This audit isn't saved in this browser. It may have expired after 7 days." />;

  const col = gradeColor(audit.grade);
  const link = `${location.origin}/?url=${encodeURIComponent(audit.url)}`;
  function copyLink() {
    navigator.clipboard.writeText(link).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }, () => prompt("Copy this link", link));
  }

  return (
    <div className="page">
      <div className="results-inner">
        <div className="results-header">
          <div className="results-header-start">
            <BackButton />
            <div className="results-url">
              Results for <span>{audit.url}</span>
            </div>
          </div>
          <div className="results-badges">
            {audit.green_hosting && (
              <a className={`host-pill${audit.green_hosting.green ? " green" : ""}`} href="https://www.thegreenwebfoundation.org/" target="_blank" rel="noreferrer">
                {audit.green_hosting.green ? `Green host${audit.green_hosting.hosted_by ? ` · ${audit.green_hosting.hosted_by}` : ""}` : "Not verified green"}
              </a>
            )}
            <div className="grade-pill" style={{ color: col }}>{audit.grade} Grade</div>
          </div>
        </div>

        <div className="results-actions">
          <button className="btn btn-ghost btn-small" onClick={() => navigate("/", { state: { rerun: audit.url } })}>Run again</button>
          <button className="btn btn-ghost btn-small" onClick={copyLink} aria-live="polite">{copied ? "Link copied" : "Copy link"}</button>
          <button className="btn btn-ghost btn-small" onClick={() => window.print()}>Download PDF</button>
          <button className="btn btn-ghost btn-small" onClick={() => downloadJson(`ecoweb-audit-${new URL(audit.url).hostname}.json`, audit)}>
            Download JSON
          </button>
        </div>

        <div className="metrics">
          <div className="card grade-card">
            <div className="metric-label">Grade</div>
            <div className="grade-big" style={{ color: col }}>{audit.grade}</div>
            <div className="grade-meta">Score {audit.score}/100 · {audit.rating}</div>
            <div className="meter"><div style={{ width: `${audit.score}%`, background: col }} /></div>
          </div>
          <div className="card metric-card">
            <div className="metric-label">Per-visit carbon</div>
            <div>
              <div className="metric-value">{formatCO2(audit.total_co2)}</div>
              <div className="metric-unit">CO₂ per page visit</div>
            </div>
            <div className="metric-foot">{audit.annual_co2_kg} kg CO₂/yr</div>
          </div>
          <div className="card metric-card">
            <div className="metric-label">Page weight</div>
            <div>
              <div className="metric-value">{audit.page_weight_mb} MB</div>
              <div className="metric-unit">transferred</div>
            </div>
            <div className="metric-foot">{audit.request_count} requests</div>
          </div>
          <div className="card metric-card">
            <div className="metric-label">Real-world equivalent</div>
            <div className="metric-comparison">{audit.comparison}</div>
            <div className="metric-foot">{audit.trees_to_offset} trees to offset annually</div>
          </div>
        </div>

        {audit.categories.length > 0 && (
          <div className="card block">
            <div className="chart-title">CO₂ by asset type</div>
            {audit.categories.map((c) => (
              <div className="breakdown-row" key={c.name}>
                <span>{c.name} · {c.count}</span>
                <div className="meter"><div style={{ width: `${c.percentage}%` }} /></div>
                <span>{formatCO2(c.total_co2)} · {c.percentage}%</span>
              </div>
            ))}
          </div>
        )}

        <SavingsCard audit={audit} />
        <DeliveryCard delivery={audit.delivery} />
        <Trend url={audit.url} currentId={audit.id} />
        <MLCard audit={audit} />
        <AssetList assets={audit.assets} />
      </div>
    </div>
  );
}

function MLCard({ audit }: { audit: Audit }) {
  const ml = audit.ml_prediction;
  const diff = ml.difference_pct;
  return (
    <div className="card split-card">
      <div className="split-text">
        <div className="chart-title">ML model cross-check</div>
        <p className="split-desc">
          An independently trained <b>{ml.model_name}</b> regression model (R² = <b>{ml.r2_score.toFixed(4)}</b>)
          predicts <strong className="green">{formatCO2(ml.predicted_co2_grams)}</strong> CO₂ for this page based on its
          element-level features, a difference of{" "}
          <strong className={ml.agreement === "divergent" ? "amber" : ml.agreement === "close" ? "green" : ""}>
            {diff == null ? "–" : `${diff > 0 ? "+" : ""}${diff}%`}
          </strong>{" "}
          from the SWD formula result.
        </p>
      </div>
      <div className="versus">
        <div className="section-label">SWD vs ML</div>
        <div className="versus-values">
          <div>
            <div className="versus-value">{formatCO2(audit.total_co2)}</div>
            <div className="versus-caption">SWD formula</div>
          </div>
          <div className="versus-vs">vs</div>
          <div>
            <div className="versus-value">{formatCO2(ml.predicted_co2_grams)}</div>
            <div className="versus-caption">ML model</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function SavingsCard({ audit }: { audit: Audit }) {
  const p = audit.potential;
  if (!p) return null;
  return (
    <div className="card split-card">
      <div className="split-text">
        <div className="chart-title">Potential savings</div>
        <p className="split-desc">
          {p.saving_pct > 0 ? (
            <>
              Fixing the flagged assets could cut <strong>{p.saving_pct}%</strong> of the page weight, saving{" "}
              <strong className="green">{formatCO2(audit.total_co2 - p.total_co2)}</strong> CO₂ per visit
              {p.grade === audit.grade ? `. The grade would stay ${p.grade}.` : <> and lifting the grade from <b>{audit.grade}</b> to <b>{p.grade}</b>.</>}
            </>
          ) : (
            "Every asset is already well-sized, so there is nothing flagged to fix."
          )}
        </p>
      </div>
      <div className="versus">
        <div className="section-label">Now vs fixed</div>
        <div className="versus-values">
          <div>
            <div className="versus-value" style={{ color: gradeColor(audit.grade) }}>{audit.grade}</div>
            <div className="versus-caption">{formatCO2(audit.total_co2)}</div>
          </div>
          <div className="versus-vs">→</div>
          <div>
            <div className="versus-value" style={{ color: gradeColor(p.grade) }}>{p.grade}</div>
            <div className="versus-caption">{formatCO2(p.total_co2)}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function DeliveryCard({ delivery }: { delivery?: Audit["delivery"] }) {
  if (!delivery) return null;
  return (
    <div className="card block">
      <div className="chart-title">Delivery checks</div>
      <div className="checks">
        {(Object.keys(ISSUES) as (keyof typeof ISSUES)[]).map((key) => (
          <div className="check" key={key}>
            <span className={`check-count ${delivery[key] ? "amber" : "green"}`}>{delivery[key]}</span>
            <span>
              <b>{ISSUES[key].label}</b>
              <span className="check-detail">{ISSUES[key].detail}</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Trend({ url, currentId }: { url: string; currentId: string }) {
  const [points, setPoints] = useState<HistoryEntry[]>([]);

  useEffect(() => {
    let active = true;
    listHistory().then((list) => active && setPoints(list.filter((e) => e.url === url).reverse()));
    return () => {
      active = false;
    };
  }, [url, currentId]);

  if (points.length < 2) return null;
  const values = points.map((p) => p.total_co2);
  const min = Math.min(...values);
  const range = Math.max(...values) - min || 1;
  const xy = values.map((v, i) => ({ x: `${2 + (i / (values.length - 1)) * 96}%`, y: 56 - ((v - min) / range) * 48 }));
  const first = points[0];
  const last = points[points.length - 1];

  return (
    <div className="card block">
      <div className="chart-title">CO₂ over time for this site</div>
      <svg className="trend-chart" role="img" aria-label={`CO₂ across ${points.length} audits of ${url}`}>
        {xy.slice(1).map((p, i) => <line key={points[i].id} x1={xy[i].x} y1={xy[i].y} x2={p.x} y2={p.y} />)}
        {xy.map((p, i) => <line className="point" key={points[i].id} x1={p.x} y1={p.y} x2={p.x} y2={p.y} />)}
      </svg>
      <div className="trend-foot">
        <span>{formatDate(first.audited_at)} · {formatCO2(first.total_co2)}</span>
        <span>{points.length} audits in the last 7 days</span>
        <span>{formatDate(last.audited_at)} · {formatCO2(last.total_co2)}</span>
      </div>
    </div>
  );
}

const FILTERS = [
  { key: "all", label: "All" },
  { key: "red", label: "Critical" },
  { key: "amber", label: "Moderate" },
  { key: "green", label: "Optimised" },
] as const;

function AssetList({ assets }: { assets: Asset[] }) {
  const [filter, setFilter] = useState<(typeof FILTERS)[number]["key"]>("all");
  const [open, setOpen] = useState<string | null>(null);
  const shown = filter === "all" ? assets : assets.filter((a) => a.status === filter);

  return (
    <div className="card">
      <div className="asset-header">
        <div>
          <h2 className="asset-title">Assets</h2>
          <div className="asset-subtitle">Tap any asset to see the issue and how to fix it</div>
        </div>
        <div className="filter-tabs" role="group" aria-label="Filter assets by status">
          {FILTERS.map(({ key, label }) => (
            <button key={key} className="filter-tab" aria-pressed={filter === key} onClick={() => setFilter(key)}>{label}</button>
          ))}
        </div>
      </div>

      <div className="asset-list">
        {shown.length === 0 && <div className="asset-empty">No assets in this category.</div>}
        {shown.map((a) => {
          const col = STATUS_COLOR[a.status];
          const isOpen = open === a.url;
          return (
            <div className={`asset-row${isOpen ? " open" : ""}`} key={a.url}>
              <button className="asset-row-main" aria-expanded={isOpen} onClick={() => setOpen(isOpen ? null : a.url)}>
                <span className="type-badge">{TYPE_LABEL[a.asset_type]}</span>
                <span className="asset-info">
                  <span className="asset-name">{a.name}</span>
                  <span className="asset-size">
                    {formatBytes(a.size_bytes)}
                    {a.issues?.map((i) => <span className="asset-issue" key={i}> · {ISSUES[i].label}</span>)}
                  </span>
                </span>
                <span className="asset-right">
                  <span className="asset-co2" style={{ color: col }}>{formatCO2(a.co2_grams)} CO₂</span>
                  <span className="status-dot" style={{ background: col }} />
                  <svg className="chevron" width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true">
                    <path d="M2 3.5L5 6.5L8 3.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>
              </button>
              <div className="asset-tip">
                <svg className="tip-icon" width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                  <circle cx="7" cy="7" r="5.5" stroke={col} strokeWidth="1.2" />
                  <path d="M7 5v2.5M7 9.5v.1" stroke={col} strokeWidth="1.2" strokeLinecap="round" />
                </svg>
                <span className="tip-text">
                  {a.optimization_tip}
                  {a.saving_co2_grams > 0 && <strong className="tip-saving"> Could save ≈ {formatCO2(a.saving_co2_grams)} CO₂ per visit.</strong>}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
