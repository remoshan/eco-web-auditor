import { useEffect, useRef, useState, type ChangeEvent } from "react";
import { Link, useNavigate } from "react-router";
import { clearHistory, exportHistory, importHistory, listHistory, type HistoryEntry } from "../history";
import { formatCO2, formatDate, gradeColor } from "../format";
import Dialog from "./Dialog";

export default function HistoryList() {
  const navigate = useNavigate();
  const [entries, setEntries] = useState<HistoryEntry[] | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [notice, setNotice] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    listHistory().then(setEntries, () => setEntries([]));
  }, []);

  function toggle(id: string, checked: boolean) {
    setSelected((prev) => (checked ? [...prev, id].slice(-2) : prev.filter((x) => x !== id)));
  }

  async function clear() {
    setConfirming(false);
    await clearHistory();
    setEntries([]);
    setSelected([]);
  }

  async function importFile(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    try {
      const count = await importHistory(JSON.parse(await file.text()));
      setEntries(await listHistory());
      setNotice(`Imported ${count} audit${count === 1 ? "" : "s"}. Audits older than 7 days are skipped.`);
    } catch (err) {
      setNotice(err instanceof SyntaxError ? "That file isn't valid JSON." : (err as Error).message);
    }
  }

  if (entries === null) return null;

  return (
    <section className="recent-section">
      <div className="results-inner">
        <div className="recent-header">
          <div>
            <div className="section-label">Audit History</div>
            <h2 className="recent-title">Recent Audits</h2>
            <p className="recent-sub">
              {notice ??
                (entries.length
                  ? "Saved in this browser for 7 days. Open one, or tick two to compare them."
                  : "No audits yet. Run your first one above, or import a history file.")}
            </p>
          </div>
          <div className="recent-actions">
            <input ref={fileInput} type="file" accept="application/json,.json" hidden onChange={importFile} />
            <button className="btn btn-ghost" onClick={() => fileInput.current?.click()}>Import</button>
            {entries.length > 0 && (
              <>
                <button className="btn btn-ghost" onClick={exportHistory}>Export</button>
                <button className="btn btn-ghost" onClick={() => setConfirming(true)}>Clear history</button>
                <button
                  className="btn btn-primary"
                  disabled={selected.length !== 2}
                  onClick={() => navigate(`/compare/${selected[0]}/${selected[1]}`)}
                >
                  Compare ({selected.length}/2)
                </button>
              </>
            )}
          </div>
        </div>

        <div className="recent-grid">
          {entries.map((a) => {
            const checked = selected.includes(a.id);
            return (
              <div className={`recent-row${checked ? " selected" : ""}`} key={a.id} onClick={() => navigate(`/audits/${a.id}`)}>
                <label className="compare-hit" onClick={(e) => e.stopPropagation()}>
                  <input
                    type="checkbox"
                    className="compare-check"
                    checked={checked}
                    onChange={(e) => toggle(a.id, e.target.checked)}
                    aria-label={`Select ${a.url} for comparison`}
                  />
                </label>
                <Link className="recent-url" to={`/audits/${a.id}`} title={a.url} onClick={(e) => e.stopPropagation()}>
                  {a.url}
                </Link>
                <div className="recent-co2">{formatCO2(a.total_co2)} CO₂</div>
                <div className="recent-co2">{a.page_weight_mb ? `${a.page_weight_mb} MB` : "< 0.01 MB"}</div>
                <div className="grade-chip" style={{ color: gradeColor(a.grade) }}>{a.grade}</div>
                <div className="recent-date">{formatDate(a.audited_at)}</div>
              </div>
            );
          })}
        </div>
      </div>

      <Dialog open={confirming} title="Clear audit history?" onClose={() => setConfirming(false)}>
        <p className="dialog-text">Every saved audit will be deleted from this browser. This can't be undone, so export your history first if you want a backup.</p>
        <div className="dialog-actions">
          <button className="btn btn-ghost" onClick={() => setConfirming(false)}>Cancel</button>
          <button className="btn btn-danger" onClick={clear}>Delete all</button>
        </div>
      </Dialog>
    </section>
  );
}
