import { useEffect, useRef, useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router";
import { runAudit, serverAwake } from "../api";
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
  const location = useLocation();
  const [url, setUrl] = useState("");
  const [scanning, setScanning] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [shake, setShake] = useState(false);
  const [waking, setWaking] = useState(false);
  const abort = useRef<AbortController | null>(null);

  useEffect(() => () => abort.current?.abort(), []);

  useEffect(() => {
    const timer = setTimeout(() => setWaking(true), 2000);
    serverAwake.then(() => {
      clearTimeout(timer);
      setWaking(false);
    });
    return () => clearTimeout(timer);
  }, []);

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

  useEffect(() => {
    const rerun = (location.state as { rerun?: string } | null)?.rerun;
    const target = rerun ?? new URLSearchParams(location.search).get("url");
    if (!target) return;
    navigate("/", { replace: true });
    setUrl(target);
    start(target, !!rerun);
  }, []);

  async function start(target: string, refresh = false) {
    const controller = new AbortController();
    abort.current = controller;
    setError(null);
    setScanning(target);
    try {
      const audit = await runAudit(target, refresh, controller.signal);
      await saveAudit(audit);
      navigate(`/audits/${audit.id}`);
    } catch (err) {
      if (controller.signal.aborted) return;
      setError(err instanceof Error ? err.message : "An unexpected error occurred.");
      setScanning(null);
    }
  }

  function submit(e: FormEvent) {
    e.preventDefault();
    if (url.trim()) start(url.trim());
    else setShake(true);
  }

  if (scanning) return <Loading url={scanning} waking={waking} />;

  return (
    <>
      {error && <div className="error-banner" role="alert">{error}</div>}

      <section className="hero">
        <h1 className="hero-title">Your website has a<br />carbon footprint.</h1>
        <p className="hero-sub">
          Audit every image, script and stylesheet. See which elements cost the most CO₂ and how to fix them.
        </p>

        <form className={`search-wrap${shake ? " shake" : ""}`} onSubmit={submit}>
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
        {waking && <Note text={WAKING} />}

      </section>

      <HistoryList />
    </>
  );
}

const WAKING = "Waking the server from sleep. The first audit can take up to a minute.";

function Note({ text }: { text: string }) {
  return <p className="waking" role="status">{text}</p>;
}

function Loading({ url, waking }: { url: string; waking: boolean }) {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setStep((s) => s + 1), 600);
    return () => clearInterval(timer);
  }, []);

  return (
    <section className="loading-section" aria-live="polite">
      <div className="loading-inner">
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
                      <path d="M1.5 4L3.2 6L6.5 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                  {state === "active" && <div className="pulse" />}
                </div>
                <span className={`step-text${state ? " lit" : ""}`}>{text}</span>
              </div>
            );
          })}
        </div>
        {(waking || step > 20) && <Note text={waking ? WAKING : "Still working. Large pages, or a server that has just restarted, can take up to a minute."} />}
      </div>
    </section>
  );
}
