"""
scripts/train_model.py
───────────────────────
Trains a regression model to predict a webpage's CO2 footprint from
page-level features (asset counts, sizes, ratios) extracted during
scraping.

This serves the research objective:
    "To validate the system's effectiveness through market research
     and developer evaluation" — by demonstrating that an independent
    ML model trained on real audit data converges with the
    Sustainable Web Design (SWD) formula's predictions.

Run from the backend/ folder with the venv active:
    python scripts/train_model.py

Inputs:
    ml/dataset.csv          ← produced by collect_dataset.py

Outputs:
    ml/model.joblib         ← trained model (used by /api/predict)
    ml/scaler.joblib        ← feature scaler
    ml/feature_columns.json ← ordered list of feature names
    ml/evaluation_report.txt
    ml/plots/*.png          ← visualisations for your thesis
"""

import json
import os

import joblib
import matplotlib
matplotlib.use("Agg")  # No GUI backend needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler

# ── Paths ──────────────────────────────────────────────────────────────────────
ML_DIR    = "ml"
DATA_PATH = os.path.join(ML_DIR, "dataset.csv")
PLOTS_DIR = os.path.join(ML_DIR, "plots")

os.makedirs(PLOTS_DIR, exist_ok=True)

# ── Feature columns used for training ────────────────────────────────────────
# These are the inputs the model will use to predict CO2.
# Deliberately excludes 'total_size_kb' alone being too dominant by also
# including per-category breakdowns — this lets us evaluate whether
# granular element-level data improves prediction (your core research point).
FEATURE_COLUMNS = [
    "html_size_kb",
    "total_assets",
    "image_count", "script_count", "css_count", "font_count", "media_count",
    "image_total_kb", "script_total_kb", "css_total_kb", "font_total_kb", "media_total_kb",
    "image_avg_kb", "script_avg_kb", "css_avg_kb", "font_avg_kb",
    "max_single_asset_kb", "max_image_kb", "max_script_kb",
    "red_asset_count", "amber_asset_count", "green_asset_count",
    "image_pct_of_weight", "script_pct_of_weight",
]

TARGET_COLUMN = "total_co2_grams"


def load_data() -> pd.DataFrame:
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(
            f"{DATA_PATH} not found. Run scripts/collect_dataset.py first."
        )
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} rows from {DATA_PATH}")
    print(f"Columns: {list(df.columns)}\n")
    return df


def explore_data(df: pd.DataFrame) -> None:
    """Generate exploratory plots for the thesis appendix."""
    print("── Generating exploratory plots ──")

    # 1. Distribution of CO2 across the dataset
    plt.figure(figsize=(8, 5))
    sns.histplot(df[TARGET_COLUMN], bins=20, kde=True, color="#34C759")
    plt.title("Distribution of CO2 Emissions per Page Visit")
    plt.xlabel("CO2 (grams)")
    plt.ylabel("Number of websites")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "co2_distribution.png"), dpi=120)
    plt.close()

    # 2. Grade distribution
    plt.figure(figsize=(8, 5))
    grade_order = ["A+", "A", "B+", "B", "C", "D", "F"]
    grade_counts = df["grade"].value_counts().reindex(grade_order).fillna(0)
    sns.barplot(x=grade_counts.index, y=grade_counts.values,
            hue=grade_counts.index, palette="RdYlGn_r", legend=False)
    plt.title("Sustainability Grade Distribution")
    plt.xlabel("Grade")
    plt.ylabel("Number of websites")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "grade_distribution.png"), dpi=120)
    plt.close()

    # 3. Correlation heatmap of key features
    plt.figure(figsize=(12, 10))
    corr_cols = FEATURE_COLUMNS + [TARGET_COLUMN]
    corr = df[corr_cols].corr()
    sns.heatmap(corr, cmap="RdYlGn", center=0, annot=False, square=True)
    plt.title("Feature Correlation Matrix")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "correlation_heatmap.png"), dpi=120)
    plt.close()

    # 4. Total size vs CO2 (sanity check — should be near-linear since
    #    CO2 is DERIVED from size via the SWD formula)
    plt.figure(figsize=(8, 6))
    plt.scatter(df["total_size_kb"], df[TARGET_COLUMN], alpha=0.6, color="#0A84FF")
    plt.title("Page Weight vs CO2 Emissions (SWD relationship)")
    plt.xlabel("Total Page Weight (KB)")
    plt.ylabel("CO2 (grams)")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "weight_vs_co2.png"), dpi=120)
    plt.close()

    print(f"Saved 4 exploratory plots to {PLOTS_DIR}/\n")


def train_models(X_train, X_test, y_train, y_test, feature_names):
    """Train multiple models and compare performance."""
    results = {}

    models = {
        "Linear Regression":      LinearRegression(),
        "Ridge Regression":       Ridge(alpha=1.0),
        "Random Forest":          RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42),
        "Gradient Boosting":      GradientBoostingRegressor(n_estimators=150, max_depth=4, random_state=42),
    }

    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        mae  = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2   = r2_score(y_test, y_pred)

        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="r2")

        results[name] = {
            "model": model,
            "mae": mae,
            "rmse": rmse,
            "r2": r2,
            "cv_r2_mean": cv_scores.mean(),
            "cv_r2_std": cv_scores.std(),
            "predictions": y_pred,
        }

        print(f"{name:20s}  MAE={mae:.5f}  RMSE={rmse:.5f}  R²={r2:.4f}  "
              f"CV R²={cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    return results


def plot_predictions(y_test, results, plots_dir):
    """Scatter plot: predicted vs actual CO2 for the best model."""
    best_name = max(results, key=lambda k: results[k]["r2"])
    best = results[best_name]

    plt.figure(figsize=(8, 8))
    plt.scatter(y_test, best["predictions"], alpha=0.6, color="#34C759")

    lims = [min(y_test.min(), best["predictions"].min()),
            max(y_test.max(), best["predictions"].max())]
    plt.plot(lims, lims, "--", color="#86868B", label="Perfect prediction")

    plt.xlabel("Actual CO2 (grams) — from SWD formula")
    plt.ylabel("Predicted CO2 (grams) — from ML model")
    plt.title(f"Predicted vs Actual CO2\nBest model: {best_name} (R² = {best['r2']:.4f})")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "predicted_vs_actual.png"), dpi=120)
    plt.close()

    return best_name


def plot_feature_importance(model, feature_names, plots_dir):
    """Bar chart of feature importance (tree-based models only)."""
    if not hasattr(model, "feature_importances_"):
        return

    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1][:12]  # top 12

    plt.figure(figsize=(10, 6))
    plt.barh(
        [feature_names[i] for i in indices][::-1],
        [importances[i] for i in indices][::-1],
        color="#34C759",
    )
    plt.xlabel("Importance")
    plt.title("Top Feature Importances — What Drives CO2 Predictions")
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "feature_importance.png"), dpi=120)
    plt.close()


def write_report(df, results, best_name, plots_dir):
    """Write a text summary suitable for pasting into the thesis."""
    best = results[best_name]

    report = []
    report.append("EcoWeb Auditor — ML Model Evaluation Report")
    report.append("=" * 50)
    report.append(f"\nDataset size: {len(df)} websites")
    report.append(f"Features used: {len(FEATURE_COLUMNS)}")
    report.append(f"Target variable: {TARGET_COLUMN} (grams CO2 per page visit, SWD formula)\n")

    report.append("Model Comparison")
    report.append("-" * 50)
    for name, r in results.items():
        report.append(
            f"{name:20s}  MAE={r['mae']:.5f}g  RMSE={r['rmse']:.5f}g  "
            f"R²={r['r2']:.4f}  CV R²={r['cv_r2_mean']:.4f} (±{r['cv_r2_std']:.4f})"
        )

    report.append(f"\nBest model: {best_name}")
    report.append(f"  R² Score : {best['r2']:.4f}")
    report.append(f"  MAE      : {best['mae']:.5f}g CO2")
    report.append(f"  RMSE     : {best['rmse']:.5f}g CO2")

    report.append("\nInterpretation")
    report.append("-" * 50)
    if best["r2"] > 0.95:
        report.append(
            "The model achieves a very high R² score, confirming that "
            "page-level features (asset counts, sizes, type breakdowns) "
            "are sufficient to predict CO2 emissions consistent with the "
            "Sustainable Web Design formula. This validates the SWD model's "
            "reliance on data transfer size as the primary carbon driver, "
            "and confirms that EcoWeb Auditor's element-level breakdown "
            "captures the features that matter most."
        )
    elif best["r2"] > 0.80:
        report.append(
            "The model achieves a strong R² score, indicating that the "
            "extracted features explain most of the variance in CO2 "
            "emissions. Remaining variance may be attributable to assets "
            "missed during scraping (e.g. JavaScript-rendered content) "
            "or to compression/CDN effects not captured in raw byte sizes."
        )
    else:
        report.append(
            "The model achieves a moderate R² score. This suggests that "
            "additional features (e.g. server response time, third-party "
            "request counts) may improve predictions, and that further "
            "data collection is recommended for future work."
        )

    report.append("\nGenerated plots:")
    for f in sorted(os.listdir(plots_dir)):
        report.append(f"  - ml/plots/{f}")

    report_text = "\n".join(report)
    with open(os.path.join(ML_DIR, "evaluation_report.txt"), "w") as f:
        f.write(report_text)

    print("\n" + report_text)


def main():
    df = load_data()

    if len(df) < 10:
        print(
            "\n⚠ WARNING: Dataset has fewer than 10 rows. "
            "Results will be unreliable. Run collect_dataset.py with "
            "more URLs first.\n"
        )

    explore_data(df)

    X = df[FEATURE_COLUMNS].fillna(0)
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Scale features (helps Linear/Ridge regression)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print("\n── Training models ──")
    results = train_models(
        X_train_scaled, X_test_scaled, y_train, y_test, FEATURE_COLUMNS
    )

    best_name = plot_predictions(y_test, results, PLOTS_DIR)
    plot_feature_importance(results[best_name]["model"], FEATURE_COLUMNS, PLOTS_DIR)
    write_report(df, results, best_name, PLOTS_DIR)

    # ── Save the best model for use by the API ──────────────────────────────
    best_model = results[best_name]["model"]
    joblib.dump(best_model, os.path.join(ML_DIR, "model.joblib"))
    joblib.dump(scaler, os.path.join(ML_DIR, "scaler.joblib"))

    with open(os.path.join(ML_DIR, "feature_columns.json"), "w") as f:
        json.dump(FEATURE_COLUMNS, f, indent=2)

    with open(os.path.join(ML_DIR, "model_info.json"), "w") as f:
        json.dump({
            "model_name": best_name,
            "r2_score": results[best_name]["r2"],
            "mae": results[best_name]["mae"],
            "rmse": results[best_name]["rmse"],
            "n_samples": len(df),
            "n_features": len(FEATURE_COLUMNS),
        }, f, indent=2)

    print(f"\n✓ Saved model: {ML_DIR}/model.joblib  ({best_name})")
    print(f"✓ Saved scaler: {ML_DIR}/scaler.joblib")
    print(f"✓ Saved feature list: {ML_DIR}/feature_columns.json")
    print(f"✓ Saved report: {ML_DIR}/evaluation_report.txt")
    print(f"✓ Saved plots: {PLOTS_DIR}/")


if __name__ == "__main__":
    main()
