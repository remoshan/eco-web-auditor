# EcoWeb Auditor — Master Test Plan

**Student:** Wilson Francis Remoshan (2541691)
**Purpose:** Complete testing evidence for Thesis Chapter Three (Development and
Testing) and Chapter Five (Evaluation)

This kit gives you **four kinds of evidence**, matching exactly what the
Reflective Report already promised and what the university rubric rewards
(Implementation & Testing = 25%, Critical Analysis & Evaluation = 30%):

| # | Type | Proves | Goes in |
|---|---|---|---|
| 1 | Unit tests | The SWD maths itself is correct, in isolation | Chapter 3 |
| 2 | Integration/accuracy tests | The full system (scraper→engine→DB) is correct on known data | Chapter 3 & 5 |
| 3 | Real-world comparison | Your tool's output is reasonable against an industry benchmark | Chapter 5 |
| 4 | UAT + cross-browser | The tool is usable and works everywhere | Chapter 5 |

Work through this document **in order** — each section tells you exactly
what to run and what to paste into your thesis afterwards.

---

## Part 1 — Unit Testing (no server needed)

This tests the carbon calculation formulas in complete isolation — pure
maths, no network, no database. This is the fastest, most rigorous test
you have, because every expected value is hand-derived independently of
the code being tested.

### How to run it

```cmd
cd testing_kit
python scripts/test_carbon_unit.py
```

You should see `27 / 27 tests passed (100.0%)`. If anything fails, **stop
and tell me** — do not proceed to the thesis with a failing test.

### What to put in your thesis

Copy the printed PASS/FAIL table directly into **Chapter 3, Section "Unit
Testing"**. It already has the format thesis test-case tables use: ID,
Description, Expected, Actual, Result. A screenshot of the terminal output
showing `27/27 passed` is strong supporting evidence for Chapter 5 too.

---

## Part 2 — Integration / Accuracy Testing (needs your full stack running)

This is the most important evidence in the entire kit. It proves that your
**real, running system** — not just the formula in isolation — produces
exactly the output a hand calculation predicts, using a test page where
every byte is known and controlled by you.

### Step 1 — Compute the ground truth (optional — already done for you)

If you want to see how the expected numbers were derived:

```cmd
cd testing_kit
python scripts/compute_expected.py
```

This prints the hand-calculated answer key. The numbers are already
hard-coded into `test_accuracy_live.py`, so you don't strictly need to run
this — but it's good evidence to include in your thesis appendix showing
your working.

### Step 2 — Start three things, each in its own terminal

**Terminal 1 — Database** (already running as a service, nothing to do)

**Terminal 2 — Backend**
```cmd
cd backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

**Terminal 3 — Serve the fixture page**
```cmd
cd testing_kit\fixtures
python -m http.server 9000
```
Leave this running. Visit `http://localhost:9000/index.html` in your
browser to confirm you see the test page (it will look plain — that's
fine, it's not meant to be pretty, only byte-precise).

### Step 3 — Run the accuracy test (Terminal 4)

```cmd
cd testing_kit
python scripts/test_accuracy_live.py
```

You should see `12 / 12 tests passed`. This single script actually proves:

- **AT01–AT07**: Your live scraper correctly measured all 9 known-size
  assets, the SWD engine calculated the exact correct CO2 value, assigned
  the exact correct grade, and classified every single asset's
  green/amber/red status correctly.
- **AT08–AT09**: The system fails gracefully (HTTP 422, not a crash) on
  bad input — proves your error handling from `scraper.py` works.
- **AT10**: Health check works.
- **AT11–AT12**: The audit was genuinely persisted to PostgreSQL and can
  be retrieved — proves your database layer works end-to-end, not just
  the calculation.

### What to put in your thesis

- Screenshot the full terminal output showing `12/12 passed`
- Copy the results table into **Chapter 3** (as your primary test case
  table — this is the strongest evidence you have, since every "Test
  Data" value is a byte-precise fixture you engineered yourself)
- Reference it again in **Chapter 5, Evaluation**, explicitly stating:
  *"The system was validated against a controlled fixture with
  known asset sizes, achieving 100% accuracy across 12 automated test
  cases covering calculation correctness, error handling, and data
  persistence."*

---

## Part 3 — Real-World Accuracy Comparison (manual, ~15 minutes)

This is different from Part 2 — instead of testing against a byte-precise
fixture, this tests your tool's output against a recognised industry
benchmark (WebsiteCarbon.com, cited in your Literature Review) on real,
live websites. Differences are **expected and fine** — you're not trying
to match exactly, you're demonstrating your tool's output is *directionally
sound and reasonable* compared to an established tool.

### Step 1 — Audit these 5 sites in YOUR tool

Open your frontend (`http://127.0.0.1:5500/index.html`) and audit each of
these URLs. Record the CO2 and grade for each:

| URL | Your CO2 (g) | Your Grade |
|---|---|---|
| https://www.example.com | | |
| https://www.python.org | | |
| https://www.wikipedia.org | | |
| https://www.bbc.co.uk | | |
| https://www.gov.uk | | |

### Step 2 — Audit the SAME 5 sites on WebsiteCarbon.com

Go to **https://www.websitecarbon.com**, paste each URL, and record its
result:

| URL | WebsiteCarbon CO2 (g) | WebsiteCarbon Rating |
|---|---|---|
| https://www.example.com | | |
| https://www.python.org | | |
| https://www.wikipedia.org | | |
| https://www.bbc.co.uk | | |
| https://www.gov.uk | | |

### Step 3 — Combine into one comparison table for your thesis

| URL | EcoWeb CO2 | WebsiteCarbon CO2 | Difference | EcoWeb Grade | WC Rating | Same direction? |
|---|---|---|---|---|---|---|
| example.com | | | | | | |
| python.org | | | | | | |
| wikipedia.org | | | | | | |
| bbc.co.uk | | | | | | |
| gov.uk | | | | | | |

**"Same direction?"** means: does a site that scores worse on WebsiteCarbon
also score worse on EcoWeb Auditor, relative to the others? That relative
ordering consistency — not exact number matching — is your actual
accuracy claim.

### How to explain differences in your thesis (Chapter 5, Discussion)

Any gap is legitimate and expected — write something like:

> *"Minor discrepancies between EcoWeb Auditor and WebsiteCarbon.com are
> attributable to differences in measurement methodology: WebsiteCarbon
> uses the HTTP Archive dataset and does not always perform a live
> element-level scrape, whereas EcoWeb Auditor performs static HTML
> parsing (BeautifulSoup) without JavaScript execution, meaning
> dynamically-injected assets are not captured. This is a documented
> limitation of static parsing discussed in Section 2.1.3 of the
> Literature Review."*

This is honest, well-argued, and exactly the kind of "insight supported by
evidence" the Evaluation criterion rewards.

---

## Part 4 — User Acceptance Testing (UAT)

Fulfils the exact promise made in Contextual Report Section 4.2.5:
*"the conceptual evaluation will be carried out through presenting the
EcoWeb Auditor to the same group of people who completed the initial
survey."*

### Step 1 — Create the Google Form

Go to forms.google.com and create a new form titled:

**"EcoWeb Auditor — User Acceptance Testing Feedback"**

Copy these questions exactly:

```
── Section 1: Participant Background ──

Q1. What is your role?
    ○ Student   ○ Developer   ○ Other

Q2. How familiar are you with web development?
    ○ Beginner   ○ Intermediate   ○ Advanced

── Section 2: Usability (1 = Strongly Disagree, 5 = Strongly Agree) ──

Q3. The scanner interface was easy to understand and use.
    1 ─ 2 ─ 3 ─ 4 ─ 5

Q4. The carbon grade (A+ to F) clearly communicated the sustainability
    of the website.
    1 ─ 2 ─ 3 ─ 4 ─ 5

Q5. The asset breakdown helped me understand which elements caused the
    most emissions.
    1 ─ 2 ─ 3 ─ 4 ─ 5

Q6. The optimisation tips were actionable and relevant.
    1 ─ 2 ─ 3 ─ 4 ─ 5

Q7. The charts (pie and bar) made the data easier to understand.
    1 ─ 2 ─ 3 ─ 4 ─ 5

Q8. I would use this tool during my development workflow.
    1 ─ 2 ─ 3 ─ 4 ─ 5

── Section 3: Open-Ended ──

Q9.  What feature did you find most useful, and why?
     [long-answer text]

Q10. What would you improve or add to EcoWeb Auditor?
     [long-answer text]

── Section 4: Overall ──

Q11. Overall, how would you rate EcoWeb Auditor?
     ★ ─ ★★ ─ ★★★ ─ ★★★★ ─ ★★★★★
```

### Step 2 — Distribute it

Send it to **at least 5 people**, ideally from your original 31 survey
participants (LinkedIn / university groups), along with these instructions:

```
1. Open http://127.0.0.1:5500/index.html
2. Type https://www.bbc.co.uk in the search bar, click Audit Now
3. Explore the results — click on a few asset rows to see the tips
4. Visit the About page
5. Try switching between light and dark mode
6. Then fill in this 2-minute feedback form: [your form link]
```

### Step 3 — What to put in your thesis

Once responses come in, Google Forms auto-generates response charts —
screenshot these directly for **Chapter 5, Evaluation**. Report the mean
score for Q3–Q8, and quote 2–3 representative open-ended responses from
Q9/Q10 (with participant permission implied by anonymous submission).

---

## Part 5 — Cross-Browser & Responsive Testing

Quick manual pass — required by your Work Breakdown Structure.

### Browser matrix

Open `http://127.0.0.1:5500/index.html` in each and confirm it loads and
functions correctly:

| Browser | Scanner loads | Audit runs | Charts render | Dark/Light toggle | Result |
|---|---|---|---|---|---|
| Chrome | | | | | |
| Firefox | | | | | |
| Edge | | | | | |

### Responsive breakpoints

Resize your browser window (or use DevTools device toolbar, F12 → toggle
device toolbar):

| Width | Layout | Result |
|---|---|---|
| 1280px+ (Desktop) | Bento grid shows 4 columns | |
| 768px (Tablet) | Bento grid collapses to 2 columns | |
| 375px (Mobile) | All cards stack vertically | |

### Theme persistence

| Test | Result |
|---|---|
| Toggle to light mode, refresh page — light mode remembered? | |
| Toggle to light mode, navigate to About page — stays light? | |
| All text readable in light mode (no invisible/low-contrast text)? | |

Screenshot each browser/breakpoint for your thesis Chapter 5 appendix.

---

## Summary — What Goes Where in the Thesis

| Thesis Location | Evidence to include |
|---|---|
| Chapter 3.X — Unit Testing | Part 1 output table (27/27) |
| Chapter 3.Y — Integration Testing | Part 2 output table (12/12) + fixture screenshot |
| Chapter 4 — Results and Discussions | Screenshots of dashboard using real audits from Part 3 |
| Chapter 5 — Evaluation, Accuracy | Part 3 comparison table + discussion of differences |
| Chapter 5 — Evaluation, Usability | Part 4 UAT charts + quoted feedback |
| Chapter 5 — Evaluation, Compatibility | Part 5 browser/responsive tables |
| Appendix | Full raw test scripts (these .py files), ground truth calculation |

Once every part above has real filled-in numbers, come back and we'll
start drafting Chapter 1.
