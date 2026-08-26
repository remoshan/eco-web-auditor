"""Loads the trained ML model from ml/ and predicts CO2 emissions from
page-level features, to cross-validate the SWD formula. If no model is
present, predict_co2() returns None and the API omits the ml_prediction field.
"""

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

ML_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ml")
MODEL_PATH    = os.path.join(ML_DIR, "model.joblib")
SCALER_PATH   = os.path.join(ML_DIR, "scaler.joblib")
FEATURES_PATH = os.path.join(ML_DIR, "feature_columns.json")
INFO_PATH     = os.path.join(ML_DIR, "model_info.json")

_model = None
_scaler = None
_feature_columns: Optional[list[str]] = None
_model_info: Optional[dict] = None
_load_attempted = False


def _load_artifacts() -> bool:
    global _model, _scaler, _feature_columns, _model_info, _load_attempted

    _load_attempted = True

    if not (os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH)
            and os.path.exists(FEATURES_PATH)):
        logger.info(
            "ML model artifacts not found in %s - "
            "predictions will be unavailable until scripts/train_model.py is run.",
            ML_DIR,
        )
        return False

    try:
        import joblib  # imported here so the app doesn't hard-fail if missing
        _model = joblib.load(MODEL_PATH)
        _scaler = joblib.load(SCALER_PATH)

        with open(FEATURES_PATH) as f:
            _feature_columns = json.load(f)

        if os.path.exists(INFO_PATH):
            with open(INFO_PATH) as f:
                _model_info = json.load(f)

        logger.info(
            "Loaded ML model '%s' (R2=%.4f, %d features)",
            _model_info.get("model_name", "unknown") if _model_info else "unknown",
            _model_info.get("r2_score", 0.0) if _model_info else 0.0,
            len(_feature_columns),
        )
        return True

    except Exception as exc:
        logger.warning("Failed to load ML model artifacts: %s", exc)
        return False


def is_available() -> bool:
    if not _load_attempted:
        _load_artifacts()
    return _model is not None


def get_model_info() -> Optional[dict]:
    if not _load_attempted:
        _load_artifacts()
    return _model_info


def build_feature_vector(audit_features: dict) -> Optional[list[float]]:
    if not is_available():
        return None
    return [float(audit_features.get(col, 0) or 0) for col in _feature_columns]


def predict_co2(audit_features: dict) -> Optional[dict]:
    if not is_available():
        return None

    try:
        vector = build_feature_vector(audit_features)
        scaled = _scaler.transform([vector])
        prediction = max(0.0, float(_model.predict(scaled)[0]))

        return {
            "predicted_co2_grams": round(prediction, 6),
            "model_name": _model_info.get("model_name", "unknown") if _model_info else "unknown",
            "r2_score": round(_model_info.get("r2_score", 0.0), 4) if _model_info else None,
        }
    except Exception as exc:
        logger.warning("ML prediction failed: %s", exc)
        return None
