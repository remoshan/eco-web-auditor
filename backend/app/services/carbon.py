"""Implements the Sustainable Web Design (SWD) carbon calculation model.

Reference: Greenwood, T. (2021) Sustainable Web Design. A Book Apart.
https://sustainablewebdesign.org/

CO2 (g) = (data_bytes / 1,000,000,000) × 0.81 kWh/GB × 442 gCO2/kWh
"""

import math
from typing import Tuple

ENERGY_PER_GB: float = 0.81       # kWh per gigabyte transferred
CARBON_INTENSITY: float = 442.0   # gCO2 per kWh (global grid average, 2023)

# WebsiteCarbon.com grading methodology. Ordered best to worst; first match wins.
GRADE_THRESHOLDS: list[tuple[float, str, int]] = [
    (0.095, "A+", 96),
    (0.184, "A",  88),
    (0.338, "B+", 78),
    (0.493, "B",  65),
    (0.656, "C",  50),
    (0.857, "D",  35),
    (math.inf, "F", 10),
]

ASSET_STATUS_THRESHOLDS: dict[str, dict[str, int]] = {
    "image":  {"green": 50_000,   "amber": 300_000},
    "script": {"green": 30_000,   "amber": 150_000},
    "css":    {"green": 20_000,   "amber": 100_000},
    "font":   {"green": 50_000,   "amber": 150_000},
    "media":  {"green": 500_000,  "amber": 2_000_000},
    "other":  {"green": 30_000,   "amber": 150_000},
}

OPTIMIZATION_TIPS: dict[str, dict[str, str]] = {
    "image": {
        "red": (
            "Large image detected. Convert to WebP or AVIF (saves 60–85% size). "
            "Add loading='lazy' for below-the-fold images and use srcset for "
            "responsive images to avoid serving oversized files to mobile users."
        ),
        "amber": (
            "Consider converting to WebP or AVIF and compressing with Squoosh or "
            "ImageOptim. Add loading='lazy' if this image is not in the initial viewport."
        ),
        "green": (
            "Image is well optimised. Ensure srcset is used for responsive sizing "
            "and consider a CDN for faster global delivery."
        ),
    },
    "script": {
        "red": (
            "Critical JavaScript bundle. Enable tree-shaking and route-based "
            "code-splitting in your bundler. Audit dependencies with bundlephobia.com. "
            "Use async or defer attributes to prevent render-blocking."
        ),
        "amber": (
            "Consider minification, removing unused imports, and adding "
            "async/defer attributes. Ensure Brotli or Gzip compression is active."
        ),
        "green": (
            "Script is well-sized. Ensure it is deferred if non-critical "
            "and served with Brotli compression for best transfer efficiency."
        ),
    },
    "css": {
        "red": (
            "Stylesheet is critically large. Run PurgeCSS or equivalent to strip "
            "unused rules — production builds should typically be under 15 KB. "
            "Extract critical CSS inline and load the rest asynchronously."
        ),
        "amber": (
            "Run PurgeCSS to remove unused style rules. Consider splitting into "
            "critical (inline) CSS and a lazily-loaded secondary stylesheet."
        ),
        "green": (
            "Stylesheet is well optimised. Ensure minification is enabled "
            "in your build pipeline and that the file is Brotli-compressed."
        ),
    },
    "font": {
        "red": (
            "Large font file. Subset the font to only the characters you use "
            "with FontSquirrel or glyphhanger — this can reduce size by 70%+. "
            "Use WOFF2 format and add font-display: swap to avoid invisible text."
        ),
        "amber": (
            "Subset the font to your used character range to reduce size by 40–60%. "
            "Ensure WOFF2 format is used (best compression) and add font-display: swap."
        ),
        "green": (
            "Font is well-optimised. WOFF2 is the recommended format. "
            "Subsetting can reduce size further if specific glyphs are unused."
        ),
    },
    "media": {
        "red": (
            "Large media file. Host video content on a CDN (YouTube, Vimeo embed) "
            "rather than self-hosting. Use modern codecs (H.265 / AV1) and "
            "add the lazy loading attribute to defer off-screen media."
        ),
        "amber": (
            "Consider hosting video on a CDN and using lazy loading. "
            "Modern codecs (H.265, AV1) can reduce size by 30–50% vs H.264."
        ),
        "green": (
            "Media file is within an acceptable range. "
            "Ensure lazy loading is enabled to avoid unnecessary transfers."
        ),
    },
    "other": {
        "red":   "Large asset. Investigate necessity; enable Brotli/Gzip compression and set long-lived cache headers.",
        "amber": "Consider enabling server-side compression (Brotli or Gzip) for this asset type.",
        "green": "Asset is well-optimised. Ensure cache headers are set for repeat visitors.",
    },
}


def calculate_co2_grams(size_bytes: int) -> float:
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


def get_optimization_tip(asset_type: str, status: str) -> str:
    tips = OPTIMIZATION_TIPS.get(asset_type, OPTIMIZATION_TIPS["other"])
    return tips.get(status, tips["green"])


def get_real_world_comparison(co2_grams: float) -> str:
    """Assumes a UK average petrol car: ~150 gCO2/km."""
    metres_driven = (co2_grams / 150.0) * 1000.0
    if metres_driven >= 1000:
        return f"Equivalent to driving {metres_driven / 1000:.2f} km in a petrol car"
    elif metres_driven >= 1:
        return f"Equivalent to driving {int(metres_driven)} metres in a petrol car"
    return "Less than 1 metre driven in a petrol car per page load"


def calculate_annual_metrics(co2_per_visit: float, monthly_visits: int = 10_000) -> dict:
    annual_grams = co2_per_visit * monthly_visits * 12
    annual_kg = annual_grams / 1000
    trees_needed = annual_kg / 21.0  # a mature tree absorbs ~21 kg CO2/year

    return {
        "annual_grams": round(annual_grams, 2),
        "annual_kg": round(annual_kg, 3),
        "trees_to_offset": round(trees_needed, 1),
    }
