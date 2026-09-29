import { useEffect, useRef, useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { runAudit } from "../api";
import { saveAudit } from "../history";
import HistoryList from "../components/HistoryList";

const LOADING_STEPS = [
  "Resolving DNS and connecting…",
  "Fetching page HTML…",
  "Parsing DOM and extracting assets…",
  "Measuring asset sizes…",
  "Applying SWD carbon model…",
  "Generating report…",
];

export default function Home() {
  const navigate = useNavigate();
  const [url, setUrl] = useState("");
  const [scanning, setScanning] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [shake, setShake] = useState(false);
  const abort = useRef<AbortController | null>(null);

  useEffect(() => () => abort.current?.abort(), []);

  useEffect(() => {
    if (!error) return;
    const timer = setTimeout(() => setError(null), 6000);
    return () => clearTimeout(timer);
  }, [error]);

  useEffect(() => {
    if (!shake) return;
    const timer = setTimeout(() => setShake(false), 700);
    return () => clearTimeout(timer);
  }, [shake]);

  async function submit(e: FormEvent) {
    e.preventDefault();
    const target = url.trim();
    if (!target) return setShake(true);

    abort.current = new AbortController();
    setError(null);
    setScanning(target);
    try {
      const audit = await runAudit(target, abort.current.signal);
      await saveAudit(audit);
      navigate(`/audits/${audit.id}`);
    } catch (err) {
      if (abort.current.signal.aborted) return;
      setError(err instanceof Error ? err.message : "An unexpected error occurred.");
      setScanning(null);
    }
  }

  if (scanning) return <Loading url={scanning} />;

  return (
    <>
      {error && <div className="error-banner" role="alert">⚠ {error}</div>}

      <section className="hero">
        <div className="badge badge-green">Digital Sustainability Audit · SWD Model</div>
        <h1 className="hero-title">
          Your website has a<br />
          <span className="gradient-text">carbon footprint.</span>
        </h1>
        <p className="hero-sub">
          Audit every image, script, and stylesheet. Discover exactly which elements are costing the planet — and how to fix them.
        </p>

        <form className={`search-wrap${shake ? " shake" : ""}`} onSubmit={submit}>
          <svg className="search-icon" width="15" height="15" viewBox="0 0 15 15" fill="none" aria-hidden="true">
            <circle cx="6.5" cy="6.5" r="5" stroke="currentColor" strokeWidth="1.4" />
            <path d="M10 10L13 13" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
          </svg>
          <input
            type="text"
            inputMode="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://yourwebsite.com"
            autoComplete="off"
            autoCapitalize="off"
            spellCheck={false}
            aria-label="Website URL to audit"
          />
          <button className="btn btn-primary" type="submit">Audit Now</button>
        </form>

        <div className="stats-strip">
          {[
            ["3.7%", "of global GHG emissions from ICT"],
            ["90.3%", "of developers want element-level data"],
            ["83.9%", "already optimise for loading speed"],
            ["A+–F", "sustainability grade per page"],
          ].map(([val, lbl]) => (
            <div className="stat-item" key={val}>
              <div className="stat-val">{val}</div>
              <div className="stat-lbl">{lbl}</div>
            </div>
          ))}
        </div>
      </section>

      <HistoryList />
    </>
  );
}

// ponytail: steps advance on a timer, not real progress; stream progress from the backend (SSE) if needed.
function Loading({ url }: { url: string }) {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setStep((s) => Math.min(s + 1, LOADING_STEPS.length)), 600);
    return () => clearInterval(timer);
  }, []);

  return (
    <section className="loading-section" aria-live="polite">
      <div className="loading-inner">
        <div className="loading-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <circle cx="12" cy="12" r="9" stroke="white" strokeWidth="2" strokeDasharray="6 4" />
          </svg>
        </div>
        <div className="section-label">Scanning</div>
        <div className="loading-url">{url}</div>
        <div className="loading-steps">
          {LOADING_STEPS.map((text, i) => {
            const state = i < step ? "done" : i === step ? "active" : "";
            return (
              <div className="step-row" key={text}>
                <div className={`step-dot ${state}`}>
                  {state === "done" && (
                    <svg width="8" height="8" viewBox="0 0 8 8" fill="none">
                      <path d="M1.5 4L3.2 6L6.5 2" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                  {state === "active" && <div className="pulse" />}
                </div>
                <span className={`step-text${state ? " lit" : ""}`}>{text}</span>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
