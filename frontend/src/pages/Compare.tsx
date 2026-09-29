import { useEffect, useState } from "react";
import { useParams } from "react-router";
import { compareAudits, type CompareRow, type Comparison } from "../api";
import { loadAudit } from "../history";
import { formatBytes, formatCO2, formatDate, gradeColor } from "../format";
import { BackButton, Missing } from "../App";

const FORMAT: Record<CompareRow["key"], (v: number) => string> = {
  score: (v) => `${v}/100`,
  total_co2: formatCO2,
  annual_co2_kg: (v) => `${v} kg`,
  total_bytes: formatBytes,
  request_count: String,
  category: (v) => (v ? formatCO2(v) : "—"),
};

export default function Compare() {
  const { a = "", b = "" } = useParams();
  const [result, setResult] = useState<Comparison | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setResult(null);
    setError(null);
    Promise.all([loadAudit(a), loadAudit(b)])
      .then(([first, second]) => {
        if (!first || !second) throw new Error("One of these audits isn't saved in this browser any more.");
        return compareAudits(first, second, controller.signal);
      })
      .then(setResult)
      .catch((err: Error) => !controller.signal.aborted && setError(err.message));
    return () => controller.abort();
  }, [a, b]);

  if (error) return <Missing text={error} />;
  if (!result) return <div className="page" />;

  return (
    <div className="page">
      <div className="results-inner">
        <div className="results-header">
          <div className="results-header-start">
            <BackButton />
            <div className="results-url">Comparing <span>two audits</span></div>
          </div>
        </div>

        <div className="compare-heads">
          <Side tag="A · Older" side={result.older} />
          <div className="compare-vs">vs</div>
          <Side tag="B · Newer" side={result.newer} />
        </div>

        <div className={`compare-summary ${result.verdict === "better" ? "good" : result.verdict === "worse" ? "bad" : ""}`}>
          {result.summary}
        </div>

        <div className="card compare-table-wrap">
          <table className="compare-table">
            <thead>
              <tr><th>Metric</th><th>A</th><th>B</th><th>Change</th></tr>
            </thead>
            <tbody>
              {result.metrics.map((row) => <Row row={row} key={row.key} />)}
              {result.categories.length > 0 && (
                <tr className="compare-group"><td colSpan={4}>CO₂ by asset type</td></tr>
              )}
              {result.categories.map((row) => <Row row={row} key={row.label} />)}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function Side({ tag, side }: { tag: string; side: Comparison["older"] }) {
  return (
    <div className="card compare-head">
      <div className="section-label">{tag} · {formatDate(side.audited_at)}</div>
      <div className="compare-url" title={side.url}>{side.url}</div>
      <div className="compare-grade" style={{ color: gradeColor(side.grade) }}>{side.grade}</div>
      <div className="compare-sub">Score {side.score}/100 · {formatCO2(side.total_co2)} CO₂ per visit</div>
    </div>
  );
}

function Row({ row }: { row: CompareRow }) {
  const fmt = FORMAT[row.key];
  return (
    <tr>
      <td>{row.label}</td>
      <td>{fmt(row.older)}</td>
      <td>{fmt(row.newer)}</td>
      <td>
        {row.verdict === "same" ? (
          <span className="delta same">—</span>
        ) : (
          <span className={`delta ${row.verdict === "better" ? "good" : "bad"}`}>
            {row.direction === "up" ? "▲" : "▼"} {row.change_pct == null ? "new" : `${Math.abs(row.change_pct)}%`}
          </span>
        )}
      </td>
    </tr>
  );
}
