"""
carbon_module/carbon.py
────────────────────────
EXACT COPY of backend/app/services/carbon.py from the EcoWeb Auditor
project, used here in isolation so the test suite can run without
needing the full FastAPI app, database, or network stack.

If you ever change the real carbon.py, copy the changes here too so
the test suite stays in sync with production behaviour.
"""

import math
from typing import Tuple

# ── SWD Model Constants ───────────────────────────────────────────────────────
ENERGY_PER_GB: float = 0.81       # kWh per gigabyte transferred
CARBON_INTENSITY: float = 442.0   # gCO2 per kWh (global grid average, 2023)

# ── Grade Thresholds ──────────────────────────────────────────────────────────
GRADE_THRESHOLDS: list[tuple[float, str, int]] = [
    (0.095, "A+", 96),
    (0.184, "A",  88),
    (0.338, "B+", 78),
    (0.493, "B",  65),
    (0.656, "C",  50),
    (0.857, "D",  35),
    (math.inf, "F", 10),
]

# ── Asset Status Thresholds (in bytes) ────────────────────────────────────────
ASSET_STATUS_THRESHOLDS: dict[str, dict[str, int]] = {
    "image":  {"green": 50_000,   "amber": 300_000},
    "script": {"green": 30_000,   "amber": 150_000},
    "css":    {"green": 20_000,   "amber": 100_000},
    "font":   {"green": 50_000,   "amber": 150_000},
    "media":  {"green": 500_000,  "amber": 2_000_000},
    "other":  {"green": 30_000,   "amber": 150_000},
}


def calculate_co2_grams(size_bytes: int) -> float:
    """CO2 = (bytes / 10^9) * 0.81 kWh/GB * 442 gCO2/kWh"""
    if size_bytes <= 0:
        return 0.0
    gigabytes = size_bytes / 1_000_000_000
    energy_kwh = gigabytes * ENERGY_PER_GB
    co2_grams = energy_kwh * CARBON_INTENSITY
    return round(co2_grams, 6)


def get_grade_and_score(co2_grams: float) -> Tuple[str, int]:
    for threshold, grade, score in GRADE_THRESHOLDS:
        if co2_grams <= threshold:
            return grade, score
    return "F", 10


def get_asset_status(asset_type: str, size_bytes: int) -> str:
    thresholds = ASSET_STATUS_THRESHOLDS.get(
        asset_type, ASSET_STATUS_THRESHOLDS["other"]
    )
    if size_bytes <= thresholds["green"]:
        return "green"
    elif size_bytes <= thresholds["amber"]:
        return "amber"
    return "red"


def get_real_world_comparison(co2_grams: float) -> str:
    metres_driven = (co2_grams / 150.0) * 1000.0
    if metres_driven >= 1000:
        return f"Equivalent to driving {metres_driven / 1000:.2f} km in a petrol car"
    elif metres_driven >= 1:
        return f"Equivalent to driving {int(metres_driven)} metres in a petrol car"
    return "Less than 1 metre driven in a petrol car per page load"


def calculate_annual_metrics(co2_per_visit: float, monthly_visits: int = 10_000) -> dict:
    annual_grams = co2_per_visit * monthly_visits * 12
    annual_kg = annual_grams / 1000
    trees_needed = annual_kg / 21.0
    return {
        "annual_grams": round(annual_grams, 2),
        "annual_kg": round(annual_kg, 3),
        "trees_to_offset": round(trees_needed, 1),
    }
