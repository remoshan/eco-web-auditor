# EcoWeb Auditor — ML Research Component

This document explains the **research component** of the EcoWeb Auditor
project: training a machine learning model on real audit data to
cross-validate the Sustainable Web Design (SWD) formula.

---

## Research Question

> Can page-level features extracted during an element-level audit
> (asset counts, sizes, type breakdowns) independently predict a
> webpage's carbon footprint with accuracy consistent with the
> Sustainable Web Design model?

If yes, this validates two things:
1. The SWD formula's reliance on data-transfer size is well-founded
2. EcoWeb Auditor's element-level breakdown captures the features
   that actually drive carbon emissions

---

## Workflow Overview

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│ 1. collect_dataset.py│ ──▶ │ 2. train_model.py     │ ──▶ │ 3. FastAPI loads     │
│  Audits ~70 real      │    │  Trains 4 regression  │    │  model.joblib on     │
│  websites, saves to   │    │  models, picks best,  │    │  startup. New audits │
│  ml/dataset.csv        │    │  saves plots/report   │    │  show ml_prediction  │
└─────────────────────┘     └──────────────────────┘     └─────────────────────┘
```

---

## Step 1 — Collect the Dataset

From the `backend/` folder with your venv active:

```bash
python scripts/collect_dataset.py
```

This audits ~70 curated websites (news sites, e-commerce, government,
universities, green-tech, minimal sites) and saves:

- `ml/dataset.csv` — one row per website, with ~25 numeric features
  plus the target variable `total_co2_grams`
- `ml/raw_audits.jsonl` — full raw scrape results for inspection

**This takes several minutes** (1.5s delay between requests to be
polite to servers). You can edit the `WEBSITES` list in
`scripts/collect_dataset.py` to add/remove sites — **aim for 100+ rows**
for a more robust model. More diverse sites (especially very light and
very heavy pages) improve the model's ability to generalise.

---

## Step 2 — Train the Model

```bash
python scripts/train_model.py
```

This will:

1. Load `ml/dataset.csv`
2. Generate exploratory plots in `ml/plots/`:
   - `co2_distribution.png` — histogram of CO2 across your dataset
   - `grade_distribution.png` — bar chart of A+–F grade counts
   - `correlation_heatmap.png` — feature correlation matrix
   - `weight_vs_co2.png` — sanity check (should be near-linear)
3. Train **4 models**: Linear Regression, Ridge Regression, Random
   Forest, and Gradient Boosting
4. Evaluate each with **MAE, RMSE, R², and 5-fold cross-validation**
5. Save the best model's:
   - `predicted_vs_actual.png` — scatter plot of predictions
   - `feature_importance.png` — which features matter most (tree models)
6. Save artifacts:
   - `ml/model.joblib` — the trained model
   - `ml/scaler.joblib` — feature scaler
   - `ml/feature_columns.json` — ordered feature list
   - `ml/model_info.json` — metrics summary
   - `ml/evaluation_report.txt` — full text report for your thesis

---

## Step 3 — Use in the App

**No extra steps needed.** The next time you restart the backend
(`uvicorn main:app --reload`), it will automatically detect
`ml/model.joblib` and load it.

From then on, every `/api/audit` response includes an `ml_prediction`
object:

```json
{
  "...": "...",
  "ml_prediction": {
    "predicted_co2_grams": 0.412,
    "model_name": "Random Forest",
    "r2_score": 0.9823,
    "difference_pct": 3.1
  }
}
```

The frontend automatically shows a **"ML Model Cross-Validation"** card
on the results dashboard comparing the SWD formula result against the
ML model's independent prediction.

If no model has been trained yet, `ml_prediction` is simply `null` and
the card stays hidden — **the rest of the app works exactly as before.**

---

## Interpreting Results for Your Thesis

Check `ml/evaluation_report.txt` after training. Key numbers to discuss:

| Metric | What it means |
|---|---|
| **R² Score** | How much variance in CO2 the model explains. >0.95 = excellent, >0.80 = good |
| **MAE** | Average error in grams CO2 — directly comparable to your grade thresholds |
| **CV R² (±std)** | Cross-validated R² — checks the model isn't overfitting to your specific 70 sites |
| **Feature Importance** | Which asset types/metrics most influence CO2 — useful to discuss in relation to your survey finding that 61.3% of developers correctly identify images as the top energy consumer |

### Suggested thesis structure

1. **Methodology**: Describe the feature engineering (Section 4.2.4 of
   your contextual report — "Data Analysis")
2. **Results**: Include the model comparison table and
   `predicted_vs_actual.png`
3. **Discussion**: If R² is high, argue this validates the SWD model's
   simplicity (size → energy → CO2) as sufficient for developer tooling
   without needing more complex environmental models
4. **Limitations**: Dataset size (~70-100 sites), geographic bias
   (mostly UK/global sites), static-scraping-only features

---

## Re-training with More Data

To improve the model over time:

1. Add more URLs to `WEBSITES` in `scripts/collect_dataset.py`
2. Re-run `python scripts/collect_dataset.py` (it appends to the JSONL
   but **overwrites** `dataset.csv` — back it up first if you want to
   keep snapshots for comparison)
3. Re-run `python scripts/train_model.py`
4. Restart the backend — the new model loads automatically

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `FileNotFoundError: ml/dataset.csv` | Run `collect_dataset.py` first |
| Many "Failed" rows during collection | Some sites block scrapers — this is normal, aim for >70% success rate |
| `ml_prediction` is always `null` | Check `ml/model.joblib` exists; check startup logs for "Loaded ML model" message |
| Low R² (<0.5) | Collect more diverse data — add very light (text-only) and very heavy (video-rich) sites |
| `ModuleNotFoundError: sklearn` | Run `pip install -r requirements.txt` again — ML packages were added |
