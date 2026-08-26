# EcoWeb Auditor

> A tool for estimating and visualising the carbon footprint of web pages
> via element-level analysis — using the Sustainable Web Design (SWD) model.

---

## Project Structure

```
ecoweb-auditor/
│
├── backend/                     # Python / FastAPI API server
│   ├── main.py                  # App entry point – run this
│   ├── requirements.txt         # pip dependencies
│   ├── .env                     # Your local DB credentials (not committed)
│   └── app/
│       ├── config.py            # Pydantic Settings (reads from .env)
│       ├── database.py          # Async SQLAlchemy engine + session
│       ├── models/
│       │   └── audit.py         # ORM models: Audit, AuditAsset
│       ├── schemas/
│       │   └── audit.py         # Pydantic request/response schemas
│       ├── services/
│       │   ├── carbon.py        # SWD carbon calculation engine
│       │   └── scraper.py       # Async HTTP scraper + DOM parser
│       └── routes/
│           └── audit.py         # FastAPI route handlers (/api/*)
│
└── frontend/                    # Plain HTML / CSS / JS (no build step)
    ├── index.html               # Home page – scanner & results dashboard
    ├── about.html                # About page – carbon facts & SWD model
    ├── css/
    │   └── main.css             # Full stylesheet (dark green theme)
    └── js/
        ├── main.js               # Shared utilities & nav highlighting
        ├── charts.js             # Chart.js pie & bar chart wrappers
        └── audit.js              # Audit form, loading, results rendering
```

---

## Prerequisites

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.12 (newer versions may not have prebuilt wheels for scikit-learn yet) | https://python.org |
| PostgreSQL | 14 or higher (local) | https://postgresql.org |
| pip | latest | bundled with Python |
| A modern browser | Chrome, Firefox, Edge | — |

---

## 1 · Set Up a Database

**Option A — Local PostgreSQL**

```bash
# Connect as the postgres superuser
psql -U postgres

# Inside psql, run:
CREATE DATABASE ecoweb_db;
\q
```

---

## 2 · Configure the Backend

The defaults in `app/config.py` already assume a local Postgres server with
user `postgres`, password `password`, on `localhost:5432`, database
`ecoweb_db` — if that matches your setup, you can skip this step entirely.

Otherwise, create a `.env` file inside `ecoweb-auditor/backend/` and override
just what's different (usually only your Postgres password):

```env
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/ecoweb_db
```

---

## 3 · Install Python Dependencies

```bash
# Still inside the backend/ folder

# Create a virtual environment using Python 3.12 specifically.
# If "python" or "py" on your machine defaults to a newer version (e.g.
# 3.14), scikit-learn won't have a prebuilt wheel for it yet and the
# install below will fail trying to build it from source.
py -3.12 -m venv venv          # Windows, if you have the py launcher
# python3.12 -m venv venv      # macOS / Linux

# Activate the virtual environment
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# Install all dependencies (use the venv's own pip, not a bare `pip`,
# to avoid accidentally installing outside the virtual environment)
python -m pip install -r requirements.txt
```

---

## 4 · Run the Backend API

```bash
# From inside backend/ with your venv active
uvicorn main:app --reload --port 8000
```

You should see output like:

```
INFO     EcoWeb Auditor starting up
INFO     Database ready
INFO     Application startup complete.
INFO     Uvicorn running on http://127.0.0.1:8000
```

> **Tip:** Keep this terminal window open. The `--reload` flag auto-restarts
> the server when you edit Python files.

### Verify the API is running

Open your browser and visit:
- **Health check:** http://localhost:8000/health
- **Swagger UI (interactive docs):** http://localhost:8000/docs

---

## 5 · Open the Frontend

The frontend is plain HTML — no build step required. It automatically talks
to your local backend (`http://localhost:8000`) whenever it's served from
`localhost`/`127.0.0.1`, and to the deployed API otherwise — no manual
edits needed.

**Option A · Python built-in server**
```bash
cd ecoweb-auditor/frontend
python -m http.server 5500
# Visit http://localhost:5500
```

**Option B · Open directly (file://)**
Double-click `index.html`. Note: `backdrop-filter` (glassmorphism) may not
render in some browsers over `file://`.

---

## 6 · Run Your First Audit

1. Open the frontend in your browser
2. Paste any public URL into the search bar (e.g. `https://example.com`)
3. Click **Audit Now** (or press Enter)
4. Watch the loading sequence animate through the scraping steps
5. The results dashboard shows your grade, carbon metrics, charts, and asset breakdown
6. Click any asset row to expand its optimisation tip

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/audit` | Submit a URL for auditing |
| `GET`  | `/api/audits/recent` | List recent audits (default: 10) |
| `GET`  | `/api/audit/{id}` | Retrieve a specific audit by ID |
| `GET`  | `/api/model-info` | ML model status and evaluation metrics |
| `GET`  | `/health` | Health check |
| `GET`  | `/docs` | Swagger UI |

### Example request

```bash
curl -X POST http://localhost:8000/api/audit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

---

## The Carbon Calculation

EcoWeb Auditor uses the **Sustainable Web Design (SWD)** model:

```
CO₂ (grams) = (total_bytes ÷ 1,000,000,000) × 0.81 kWh/GB × 442 gCO₂/kWh
```

Where:
- `0.81 kWh/GB` = estimated energy to transfer 1 GB across the global internet
- `442 gCO₂/kWh` = global average carbon intensity of electricity (2023)

Each individual asset's CO₂ is calculated separately using the same formula,
enabling the element-level breakdown that differentiates this tool from
aggregate calculators like WebsiteCarbon.com.

An independently trained ML model (`backend/ml/`) cross-validates the SWD
formula's output — see the `ml_prediction` field in the audit response.

### Grade thresholds

| Grade | CO₂ per visit |
|-------|--------------|
| A+    | < 0.095g     |
| A     | 0.095–0.184g |
| B+    | 0.184–0.338g |
| B     | 0.338–0.493g |
| C     | 0.493–0.656g |
| D     | 0.656–0.857g |
| F     | > 0.857g     |

---

## Known Limitations

- **Static parsing only.** The scraper does not execute JavaScript, so
  dynamically-injected assets are not captured.
- **Certificate verification is enforced.** Sites with invalid or
  misconfigured TLS certificates will fail to audit rather than being
  fetched insecurely.

---

## Troubleshooting

| Problem | Solution |
|---------|---------|
| `Connection refused` on audit | Make sure `uvicorn` is running on port 8000 |
| `asyncpg` auth error | Double-check `DATABASE_URL` in `.env` |
| CORS error in browser | Ensure your frontend URL is in `ALLOWED_ORIGINS` |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` inside your venv |
| `pip install` fails building `scikit-learn` | Your venv is using a Python version too new for the pinned scikit-learn wheel — recreate it with `py -3.12 -m venv venv` |
| `'uvicorn' is not recognized` | Your venv has no packages installed yet (or wasn't actually activated when you ran `pip install`) — recreate the venv and reinstall |
| No assets found | Some sites block scrapers; try a different URL |
| Audit fails with a TLS/certificate error | The target site has an invalid certificate — see Known Limitations above |
| Glassmorphism not showing | Use `python -m http.server`, not `file://` |

---

## References

- Greenwood, T. (2021) *Sustainable Web Design.* A Book Apart.
- Sustainable Web Design Model (2023) https://sustainablewebdesign.org/
- Preist, C., Schien, D. & Blevis, E. (2016) *Understanding and Mitigating the Effects of Device and Infrastructure Design on the Carbon Footprint of Digital Services.* CHI 2016.
- FastAPI Documentation https://fastapi.tiangolo.com/
- PostgreSQL Documentation https://www.postgresql.org/docs/

---
