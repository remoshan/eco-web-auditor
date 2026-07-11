# EcoWeb Auditor 🌿

> A tool for estimating and visualising the carbon footprint of web pages  
> via element-level analysis — using the Sustainable Web Design (SWD) model.

**BSc (Hons) Software Engineering · Final Year Project**  
Wilson Francis Remoshan (2541691) · University of Bedfordshire · 2026  
Supervisor: Ms. Rameesha Kankanamge

---

## Project Structure

```
ecoweb-auditor/
│
├── backend/                     # Python / FastAPI API server
│   ├── main.py                  # App entry point – run this
│   ├── requirements.txt         # pip dependencies
│   ├── .env.example             # Copy to .env and fill in your DB details
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
    ├── about.html               # About page – carbon facts & SWD model
    ├── css/
    │   └── main.css             # Full stylesheet (dark green theme)
    └── js/
        ├── main.js              # Shared utilities & nav highlighting
        ├── charts.js            # Chart.js pie & bar chart wrappers
        └── audit.js             # Audit form, loading, results rendering
```

---

## Prerequisites

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.11 or higher | https://python.org |
| PostgreSQL | 14 or higher | https://postgresql.org |
| pip | latest | bundled with Python |
| A modern browser | Chrome, Firefox, Edge | — |

---

## 1 · Set Up PostgreSQL

### Install PostgreSQL (if not already installed)

**Windows:**  
Download the installer from https://www.postgresql.org/download/windows/  
During setup, note the password you set for the `postgres` user.

**macOS (Homebrew):**
```bash
brew install postgresql@16
brew services start postgresql@16
```

**Ubuntu / Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### Create the database

Open a terminal / psql shell:

```bash
# Connect as the postgres superuser
psql -U postgres

# Inside psql, run:
CREATE DATABASE ecoweb_db;
\q
```

---

## 2 · Configure the Backend

```bash
# Navigate to the backend folder
cd ecoweb-auditor/backend

# Copy the example environment file
cp .env.example .env
```

Open `.env` in any text editor and set your database credentials:

```env
# Replace 'password' with your actual PostgreSQL password
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/ecoweb_db

# Leave the rest as-is for local development
ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000,null
SCRAPER_TIMEOUT=30
MAX_ASSETS_PER_PAGE=80
DEBUG=False
```

---

## 3 · Install Python Dependencies

```bash
# Still inside the backend/ folder

# (Recommended) Create a virtual environment first
python -m venv venv

# Activate the virtual environment
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

---

## 4 · Run the Backend API

```bash
# From inside backend/ with your venv active
uvicorn main:app --reload --port 8000
```

You should see output like:

```
INFO     EcoWeb Auditor – starting up
INFO     Database tables initialised successfully.
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

The frontend is plain HTML — no build step required.

**Option A · VS Code Live Server (recommended)**
1. Open the `ecoweb-auditor/frontend/` folder in VS Code
2. Install the **Live Server** extension (Ritwick Dey)
3. Right-click `index.html` → **Open with Live Server**
4. The site opens at `http://127.0.0.1:5500`

**Option B · Python built-in server**
```bash
cd ecoweb-auditor/frontend
python -m http.server 5500
# Visit http://localhost:5500
```

**Option C · Open directly (file://)**
Double-click `index.html`. Note: `backdrop-filter` (glassmorphism) may not
render in some browsers over `file://`. Use Live Server for the best experience.

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

## Troubleshooting

| Problem | Solution |
|---------|---------|
| `Connection refused` on audit | Make sure `uvicorn` is running on port 8000 |
| `asyncpg` auth error | Double-check `DATABASE_URL` password in `.env` |
| CORS error in browser | Ensure your frontend URL is in `ALLOWED_ORIGINS` |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` inside your venv |
| No assets found | Some sites block scrapers; try a different URL |
| Glassmorphism not showing | Open via Live Server, not `file://` |

---

## References

- Greenwood, T. (2021) *Sustainable Web Design.* A Book Apart.
- Sustainable Web Design Model (2023) https://sustainablewebdesign.org/
- Preist, C., Schien, D. & Blevis, E. (2016) *Understanding and Mitigating the Effects of Device and Infrastructure Design on the Carbon Footprint of Digital Services.* CHI 2016.
- FastAPI Documentation https://fastapi.tiangolo.com/
- PostgreSQL Documentation https://www.postgresql.org/docs/

---

*EcoWeb Auditor is a BSc final year project and is intended for educational and research use.*
