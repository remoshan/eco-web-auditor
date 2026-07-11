"""
app/services/predictor.py
──────────────────────────
Loads the trained ML model (produced by scripts/train_model.py) and
exposes a function to predict CO2 emissions from page-level features.

This is used to:
  1. Cross-validate the SWD formula's output against an independently
     trained model (research objective — model validation)
  2. Provide an estimate when scraping is incomplete (e.g. some assets
     could not be sized)

If no trained model exists yet, predict_co2() returns None and the
API gracefully omits the ml_prediction field — the app still works
fully via the SWD formula alone.
"""

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
ML_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ml")
MODEL_PATH    = os.path.join(ML_DIR, "model.joblib")
SCALER_PATH   = os.path.join(ML_DIR, "scaler.joblib")
FEATURES_PATH = os.path.join(ML_DIR, "feature_columns.json")
INFO_PATH     = os.path.join(ML_DIR, "model_info.json")

# ── Lazy-loaded globals ──────────────────────────────────────────────────────
_model = None
_scaler = None
_feature_columns: Optional[list[str]] = None
_model_info: Optional[dict] = None
_load_attempted = False


def _load_artifacts() -> bool:
    """Load model artifacts from disk. Returns True if successful."""
    global _model, _scaler, _feature_columns, _model_info, _load_attempted

    _load_attempted = True

    if not (os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH)
            and os.path.exists(FEATURES_PATH)):
        logger.info(
            "ML model artifacts not found in %s — "
            "predictions will be unavailable until scripts/train_model.py is run.",
            ML_DIR,
        )
        return False

    try:
        import joblib  # Imported here so the app doesn't hard-fail if missing
        _model = joblib.load(MODEL_PATH)
        _scaler = joblib.load(SCALER_PATH)

        with open(FEATURES_PATH) as f:
            _feature_columns = json.load(f)

        if os.path.exists(INFO_PATH):
            with open(INFO_PATH) as f:
                _model_info = json.load(f)

        logger.info(
            "Loaded ML model '%s' (R²=%.4f, %d features)",
            _model_info.get("model_name", "unknown") if _model_info else "unknown",
            _model_info.get("r2_score", 0.0) if _model_info else 0.0,
            len(_feature_columns),
        )
        return True

    except Exception as exc:
        logger.warning("Failed to load ML model artifacts: %s", exc)
        return False


def is_available() -> bool:
    """Check whether a trained model is loaded (loads it on first call)."""
    if not _load_attempted:
        _load_artifacts()
    return _model is not None


def get_model_info() -> Optional[dict]:
    """Return metadata about the loaded model (for the /api/model-info endpoint)."""
    if not _load_attempted:
        _load_artifacts()
    return _model_info


def build_feature_vector(audit_features: dict) -> Optional[list[float]]:
    """
    Build an ordered feature vector matching the training feature columns.

    Args:
        audit_features: dict containing at least the keys used during training
                         (see scripts/train_model.py FEATURE_COLUMNS)

    Returns:
        Ordered list of floats, or None if the model isn't loaded.
    """
    if not is_available():
        return None

    return [float(audit_features.get(col, 0) or 0) for col in _feature_columns]


def predict_co2(audit_features: dict) -> Optional[dict]:
    """
    Predict CO2 emissions (grams) using the trained ML model.

    Args:
        audit_features: dict with the same keys as FEATURE_COLUMNS in
                         scripts/train_model.py (computed during the audit)

    Returns:
        {
            "predicted_co2_grams": float,
            "model_name": str,
            "r2_score": float,
        }
        or None if no model is available.
    """
    if not is_available():
        return None

    try:
        vector = build_feature_vector(audit_features)
        scaled = _scaler.transform([vector])
        prediction = float(_model.predict(scaled)[0])

        # CO2 cannot be negative — clip just in case
        prediction = max(0.0, prediction)

        return {
            "predicted_co2_grams": round(prediction, 6),
            "model_name": _model_info.get("model_name", "unknown") if _model_info else "unknown",
            "r2_score": round(_model_info.get("r2_score", 0.0), 4) if _model_info else None,
        }
    except Exception as exc:
        logger.warning("ML prediction failed: %s", exc)
        return None
