import { useState } from "react";
import { Link, NavLink, Outlet, ScrollRestoration } from "react-router";

function Logo() {
  return (
    <svg className="logo" width="26" height="26" viewBox="0 0 32 32" fill="currentColor" aria-hidden="true">
      <path d="M14.3 30.5C14.5 25 15.3 20 17.5 15.4L18.9 16C16.9 20.6 16.3 25.2 16.3 30.5Z M17.2 17.4C15.4 10.2 19.4 3.4 28.2 1.6C29.6 10.4 25.4 16.6 17.2 17.4Z M19.4 15.4Q22.6 10.4 25.6 5Q21 9.3 19.4 15.4Z M15.4 22C8.6 22 4.2 16.8 3.6 9.2C10.8 9.6 15.7 14.2 15.4 22Z M14.6 19.8Q12 14.6 7 12.2Q10.8 16 14.6 19.8Z" />
    </svg>
  );
}

export function BackButton() {
  return (
    <Link className="btn btn-ghost btn-small" to="/">
      <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true">
        <path d="M7 2L3 5L7 8" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      </svg>
      Back
    </Link>
  );
}

export function Missing({ text }: { text: string }) {
  return (
    <div className="page">
      <div className="results-inner">
        <div className="results-header"><BackButton /></div>
        <div className="card empty-state">{text}</div>
      </div>
    </div>
  );
}

export function RouteError() {
  return <Missing text="Something went wrong showing this page. Reload to try again. If it is an imported audit, the file may be damaged." />;
}

export default function App() {
  const [theme, setTheme] = useState(() => (document.documentElement.dataset.theme === "light" ? "light" : "dark"));

  function toggleTheme() {
    const next = theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem("ecoweb-theme", next);
    } catch {}
    setTheme(next);
  }

  return (
    <>
      <nav className="nav">
        <Link className="nav-logo" to="/">
          <Logo />
          <span className="nav-logo-text">EcoWeb Auditor</span>
        </Link>
        <div className="nav-links">
          <NavLink to="/" end>Auditor</NavLink>
          <NavLink to="/about">About</NavLink>
          <button className="theme-toggle" onClick={toggleTheme} aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}>
            {theme === "dark" ? (
              <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
                <path d="M13 9.5A6 6 0 0 1 5.5 2a6 6 0 1 0 7.5 7.5Z" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            ) : (
              <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
                <circle cx="7.5" cy="7.5" r="3" stroke="currentColor" strokeWidth="1.4" />
                <path d="M7.5 1v1.5M7.5 12.5V14M1 7.5h1.5M12.5 7.5H14M3.05 3.05l1.06 1.06M10.89 10.89l1.06 1.06M3.05 11.95l1.06-1.06M10.89 4.11l1.06-1.06" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
              </svg>
            )}
          </button>
        </div>
      </nav>

      <main>
        <Outlet />
      </main>

      <footer>
        <div className="footer-inner">
          <div>
            <div className="footer-logo">
              <Logo />
              <span>EcoWeb Auditor</span>
            </div>
            <p className="footer-text">
              Carbon calculations use the{" "}
              <a href="https://sustainablewebdesign.org/" target="_blank" rel="noreferrer">Sustainable Web Design</a> model.<br />
              Built by <a href="https://francis-remoshan.vercel.app/" target="_blank" rel="noreferrer">Francis Remoshan</a>.
            </p>
          </div>
          <div className="footer-links">
            <Link to="/">Auditor</Link>
            <Link to="/about">About</Link>
          </div>
        </div>
      </footer>

      <ScrollRestoration />
    </>
  );
}
