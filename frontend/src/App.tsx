import { useState } from "react";
import { Link, NavLink, Outlet, ScrollRestoration, useOutletContext } from "react-router";
import { API_ORIGIN } from "./api";

type Theme = "light" | "dark";

export const useTheme = () => useOutletContext<Theme>();

function Logo() {
  return (
    <div className="nav-logo-icon" aria-hidden="true">
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <path d="M7 1C7 1 2 4.5 2 8.5C2 11.2 4.2 13 7 13C9.8 13 12 11.2 12 8.5C12 4.5 7 1 7 1Z" stroke="white" strokeWidth="1.4" />
        <path d="M7 6V10M5 8H9" stroke="white" strokeWidth="1.4" strokeLinecap="round" />
      </svg>
    </div>
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

export default function App() {
  const [theme, setTheme] = useState<Theme>(() => (document.documentElement.dataset.theme === "light" ? "light" : "dark"));

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
      <div className="orb orb-1" />
      <div className="orb orb-2" />

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
        <Outlet context={theme} />
      </main>

      <footer>
        <div className="footer-inner">
          <div className="footer-logo">
            <Logo />
            <span>EcoWeb Auditor</span>
          </div>
          <p className="footer-text">
            BSc (Hons) Software Engineering · Final Year Project<br />
            Wilson Francis Remoshan (2541691) · University of Bedfordshire<br />
            Carbon calculations use the{" "}
            <a href="https://sustainablewebdesign.org/" target="_blank" rel="noreferrer">Sustainable Web Design</a> model.
          </p>
          <div className="footer-links">
            <Link to="/">Auditor</Link>
            <Link to="/about">About</Link>
            <a href={`${API_ORIGIN}/docs`} target="_blank" rel="noreferrer">API Docs</a>
          </div>
        </div>
      </footer>

      <ScrollRestoration />
    </>
  );
}
