import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router";
import { getMethodology, type Methodology } from "../api";
import { gradeColor } from "../format";

const STATS = [
  ["3.7%", "of global greenhouse gas emissions are caused by ICT infrastructure, equivalent to the aviation industry."],
  ["2×", "The internet's carbon footprint is expected to double by 2025 as video streaming, AI workloads, and cloud storage grow."],
  ["416 TWh", "Estimated annual electricity consumption of global data centres — more than the entire United Kingdom uses in a year."],
  ["83.9%", "of developers surveyed already prioritise loading speed — but fewer than 20% use a dedicated carbon auditing tool. (EcoWeb Auditor primary research, 2026)"],
];

const CAUSES: { title: string; colour: string; icon: ReactNode; text: ReactNode }[] = [
  {
    title: "Unoptimised Images",
    colour: "#0A84FF",
    icon: <><rect x="1.5" y="2.5" width="13" height="11" rx="2" /><circle cx="5.5" cy="6" r="1.2" fill="currentColor" /><path d="M1.5 11L5 7.5L7.5 10L10 8L14.5 12" /></>,
    text: "Images typically account for 50–60% of a page's total weight. A single uncompressed hero image in PNG format can exceed 5 MB — the equivalent of hundreds of text pages. Converting to WebP or AVIF typically reduces size by 60–85% with no visible quality loss.",
  },
  {
    title: "Bloated JavaScript",
    colour: "#FF9F0A",
    icon: <><rect x="1.5" y="1.5" width="13" height="13" rx="2" /><path d="M5.5 10.5C5.5 11.3 6 12 7 12C8 12 8.5 11.3 8.5 10.2V6H7.2V10.1C7.2 10.7 7 11 6.5 11" /><path d="M10 10.8C10.4 11.5 11.1 12 12 12" /><path d="M9.5 8.5C9.5 8.5 9.8 7.8 10.7 7.8C11.7 7.8 12 8.5 12 9C12 10.3 10 10 10 11" /></>,
    text: "Large vendor bundles are the second biggest contributor to page weight. Modern bundlers often ship 3× more code than the initial route needs. Tree-shaking, code-splitting, and removing unused dependencies can reduce bundle size by 40–70%.",
  },
  {
    title: "Unsubsetted Fonts",
    colour: "#BF5AF2",
    icon: <><path d="M3 13L6.5 3H9.5L13 13" /><path d="M4.5 9.5H11.5" /></>,
    text: <>Web fonts loaded without subsetting carry thousands of characters your page never uses. Subsetting a font to your actual character set reduces it by 60–80%. Always use WOFF2 format and add <code>font-display: swap</code>.</>,
  },
  {
    title: "Unpurged CSS",
    colour: "#34C759",
    icon: <><path d="M2 2.5L3.5 13.5L8 15L12.5 13.5L14 2.5H2Z" /><path d="M5 5.5H11M5.5 8.5H10.5M6.5 11.5H9.5" /></>,
    text: "Utility-first CSS frameworks like Tailwind ship hundreds of kilobytes of unused rules in development mode. A production build with PurgeCSS or Tailwind's built-in purge reduces a 300 KB stylesheet to under 10 KB.",
  },
];

const TIPS: [string, ReactNode][] = [
  ["Convert images to WebP or AVIF", <>WebP reduces file sizes by 25–35% vs JPEG; AVIF by 50%+. Use <code>picture</code> with <code>srcset</code> to serve the best format per browser. Tools: Squoosh, ImageOptim, Sharp (Node.js).</>],
  ["Lazy-load below-the-fold assets", <>Add <code>loading="lazy"</code> to all <code>&lt;img&gt;</code> and <code>&lt;iframe&gt;</code> elements not in the initial viewport. This defers transfers entirely until the user scrolls — assets never viewed are never downloaded.</>],
  ["Enable Brotli compression", <>Brotli compresses HTML, CSS, and JS 15–25% better than Gzip. Configure it in your web server or CDN. Verify with <code>curl -H "Accept-Encoding: br" -I &lt;url&gt;</code> and check for <code>content-encoding: br</code>.</>],
  ["Purge unused CSS", "Utility frameworks (Tailwind, Bootstrap) include thousands of unused rules in development. Run PurgeCSS or enable Tailwind's built-in purge in production. A 300 KB stylesheet can shrink to under 8 KB."],
  ["Tree-shake and code-split JavaScript", <>Import only the functions you use. Use dynamic <code>import()</code> to load route-specific bundles on demand. Audit third-party dependencies at <a href="https://bundlephobia.com" target="_blank" rel="noreferrer">bundlephobia.com</a> before adding them.</>],
  ["Subset web fonts", <>Use <code>glyphhanger</code> or FontSquirrel to generate a font file containing only the Unicode ranges your page actually uses. Combine with <code>font-display: swap</code> to prevent invisible text during load.</>],
  ["Use a CDN with edge caching", "Serving assets from a CDN node geographically close to the user reduces transfer distance, network hops, and latency — all of which translate directly to lower energy consumption. Cloudflare, Fastly, and AWS CloudFront offer generous free tiers."],
  ["Set long-lived cache headers", <>Use <code>Cache-Control: max-age=31536000, immutable</code> on versioned static assets. Returning visitors download nothing — the most sustainable byte is the one never transferred.</>],
  ["Prefer SVG over raster for UI icons", "An SVG icon library weighs 8–15 KB in total. The same icons as PNG sprites can be 10–20× larger and cannot scale without blurring. Inline critical SVGs directly in HTML to eliminate HTTP requests."],
  ["Choose a green hosting provider", <>Check your host at <a href="https://www.thegreenwebfoundation.org/" target="_blank" rel="noreferrer">thegreenwebfoundation.org</a>. Providers that run on 100% renewable energy (Hetzner, OVH, GreenGeeks) can cut the carbon intensity of your server traffic by up to 95%.</>],
];

const STACK = [
  ["Backend", "Python · FastAPI · httpx"],
  ["Scraper", "BeautifulSoup4 · SSRF-guarded fetches"],
  ["Frontend", "React · TypeScript · Vite"],
  ["History", "IndexedDB (stays in your browser)"],
  ["Charts", "Chart.js 4"],
  ["Carbon model", "Sustainable Web Design (SWD)"],
];

export default function About() {
  const [method, setMethod] = useState<Methodology | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    getMethodology(controller.signal).then(setMethod).catch(() => !controller.signal.aborted && setFailed(true));
    return () => controller.abort();
  }, []);

  const energy = method ? `${method.energy_per_gb} kWh/GB` : "…";
  const intensity = method ? `${method.carbon_intensity} gCO₂/kWh` : "…";

  return (
    <>
      <section className="about-hero">
        <div className="badge badge-green">The Internet &amp; Climate Change</div>
        <h1>The web has a<br /><span className="gradient-text">hidden carbon cost.</span></h1>
        <p>Every byte transferred across the internet consumes energy. EcoWeb Auditor makes that invisible cost visible — element by element.</p>
      </section>

      <section className="content-section">
        <div className="content-inner">
          <div className="section-label">The Scale</div>
          <h2 className="section-title">A problem as big as aviation.</h2>
          <p className="section-sub">
            Information and communications technology (ICT) is responsible for approximately 3.7% of global greenhouse gas emissions —
            comparable to the entire aviation industry. Unlike aviation, this impact is largely invisible to the people producing it.
          </p>
          <div className="stats-grid">
            {STATS.map(([num, desc]) => (
              <div className="card stat-card" key={num}>
                <div className="stat-number">{num}</div>
                <div className="stat-desc">{desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="content-section">
        <div className="content-inner">
          <div className="section-label">Root Causes</div>
          <h2 className="section-title">What makes a website carbon-heavy?</h2>
          <p className="section-sub">
            Every HTTP request, every kilobyte downloaded, and every render-blocking script demands energy — from your server, from the global
            network, and from the device in your visitor's hand.
          </p>
          <div className="two-col">
            <div className="stack">
              {CAUSES.map((c) => (
                <div className="card cause-card" key={c.title}>
                  <div className="cause-icon" style={{ color: c.colour, background: `${c.colour}1f`, borderColor: `${c.colour}40` }}>
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" aria-hidden="true">
                      {c.icon}
                    </svg>
                  </div>
                  <div>
                    <div className="item-title">{c.title}</div>
                    <div className="item-text">{c.text}</div>
                  </div>
                </div>
              ))}
            </div>
            <div className="card energy-chain">
              <div className="energy-title">The Energy Chain</div>
              {[
                ["1", "Origin Server", "Web servers consume electricity 24/7. Every request wakes CPUs and reads from disks. Larger files mean more compute time."],
                ["2", "Global Network", `Data travels through undersea cables, routers, and exchange points — all electricity-powered. The SWD model estimates ${energy} transferred globally.`],
                ["3", "End-User Device", "Parsing JavaScript, decoding images, and rendering layouts all tax the device's CPU and GPU — draining batteries and generating heat. Heavier pages demand more device energy."],
                ["∑", "Combined CO₂", `The SWD model sums these energy costs and converts to CO₂ using the global average grid carbon intensity of ${intensity}.`],
              ].map(([n, title, text]) => (
                <div className="chain-step" key={n}>
                  <div className={`chain-dot${n === "∑" ? " total" : ""}`}>{n}</div>
                  <div>
                    <div className="item-title">{title}</div>
                    <div className="item-text">{text}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="content-section">
        <div className="content-inner">
          <div className="section-label">The Calculation Method</div>
          <h2 className="section-title">Sustainable Web Design model.</h2>
          <p className="section-sub">
            EcoWeb Auditor uses the peer-reviewed{" "}
            <a href="https://sustainablewebdesign.org/" target="_blank" rel="noreferrer">Sustainable Web Design (SWD) model</a>{" "}
            developed by Wholegrain Digital and documented by Tom Greenwood in <em>Sustainable Web Design</em> (A Book Apart, 2021). It is the
            same methodology used by WebsiteCarbon.com.
          </p>

          <div className="formula-box">
            <div className="formula-text">CO₂ (g) = ( bytes ÷ 10⁹ ) × {energy} × {intensity}</div>
            <div className="formula-vars">
              <div className="formula-var"><strong>bytes</strong>Total data transferred in bytes — sum of all page assets</div>
              <div className="formula-var"><strong>{energy}</strong>Estimated energy to transfer 1 gigabyte across the global internet</div>
              <div className="formula-var"><strong>{intensity}</strong>Global average carbon intensity of electricity (2023 figure)</div>
              <div className="formula-var"><strong>Result</strong>Estimated grams of CO₂ produced per single page visit</div>
            </div>
          </div>

          <h3 className="grade-heading">Sustainability Grade Scale</h3>
          {failed && <div className="card empty-state">Couldn't load the grade scale from the server. Refresh to try again.</div>}
          <div className="stack">
            {method?.grades.map((g, i, all) => {
              const col = gradeColor(g.grade);
              const lower = all[i - 1]?.max_co2;
              const range = g.max_co2 == null ? `Above ${lower}g` : lower == null ? `Under ${g.max_co2}g` : `${lower} – ${g.max_co2}g`;
              return (
                <div className="card grade-row" key={g.grade}>
                  <div className="grade-letter" style={{ color: col }}>{g.grade}</div>
                  <div className="grade-bar" style={{ background: `${col}26` }}>
                    <div style={{ width: `${Math.round(((i + 1) / all.length) * 100)}%`, background: col }} />
                  </div>
                  <div className="grade-range">{range} CO₂ / visit</div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section className="content-section">
        <div className="content-inner">
          <div className="section-label">Developer Guide</div>
          <h2 className="section-title">10 ways to reduce your website's carbon footprint.</h2>
          <p className="section-sub">Each of these changes is also a performance improvement — faster pages and greener pages are the same page.</p>
          <div className="tips-grid">
            {TIPS.map(([title, desc], i) => (
              <div className="card tip-card" key={title}>
                <div className="tip-number">{String(i + 1).padStart(2, "0")}</div>
                <div className="tip-title">{title}</div>
                <div className="tip-desc">{desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="content-section">
        <div className="content-inner">
          <div className="section-label">About This Project</div>
          <h2 className="section-title">A BSc final year artefact.</h2>
          <div className="two-col">
            <div className="prose">
              <p>
                EcoWeb Auditor was built as the final-year artefact for a BSc (Hons) Software Engineering degree at the University of
                Bedfordshire (2026). The project was supervised by Ms. Rameesha Kankanamge.
              </p>
              <p>
                The research motivation arose from a clear gap in the existing tooling landscape: while tools like WebsiteCarbon.com provide
                useful aggregate scores, they act as "black boxes" — developers receive a grade but no information about which specific
                elements are responsible.
              </p>
              <p>
                Primary market research (n = 31 IT and Software Engineering professionals and students) confirmed this gap:{" "}
                <strong>90.3%</strong> of respondents stated they would use a tool that breaks down carbon impact at the individual element level.
              </p>
              <p>
                The stack reflects modern industry practice: Python and FastAPI for the async scraping and carbon engine, and React with
                TypeScript for the interface. Nothing is stored on the server — your audit history lives only in your own browser.
              </p>
            </div>
            <div className="stack">
              <div className="card info-card">
                <div className="section-label">Tech Stack</div>
                {STACK.map(([k, v]) => (
                  <div className="info-row" key={k}><span>{k}</span><span>{v}</span></div>
                ))}
                {method && (
                  <div className="info-row">
                    <span>ML cross-check</span>
                    <span>{method.ml_model.model_name} · R² {method.ml_model.r2_score}</span>
                  </div>
                )}
              </div>
              <div className="card info-card">
                <div className="section-label">Key References</div>
                <div className="references">
                  <div>Greenwood, T. (2021) <em>Sustainable Web Design.</em> A Book Apart.</div>
                  <div>Sustainable Web Design Model (2023) <a href="https://sustainablewebdesign.org" target="_blank" rel="noreferrer">sustainablewebdesign.org</a></div>
                  <div>
                    Preist, C., Schien, D. &amp; Blevis, E. (2016) Understanding and Mitigating the Effects of Device and Infrastructure Design on
                    the Carbon Footprint of Digital Services. <em>CHI 2016.</em>
                  </div>
                  <div>Climate Impact Partners (2023) Infographic: The Carbon Footprint of the Internet.</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="content-section cta">
        <div className="content-inner">
          <div className="badge badge-green">Ready to audit?</div>
          <h2 className="cta-title">Find out what your website<br />is really costing the planet.</h2>
          <p className="cta-sub">Paste any URL and get a full element-level carbon report in seconds. It's free.</p>
          <Link to="/" className="btn btn-primary btn-large">Start Auditing</Link>
        </div>
      </section>
    </>
  );
}
