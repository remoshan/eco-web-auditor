import math

ENERGY_PER_GB = 0.81
CARBON_INTENSITY = 442.0
CAR_GRAMS_PER_KM = 150.0
MONTHLY_VISITS = 10_000
TREE_KG_PER_YEAR = 21.0

GRADE_THRESHOLDS = [(0.095, "A+", 96), (0.184, "A", 88), (0.338, "B+", 78), (0.493, "B", 65), (0.656, "C", 50),
                    (0.857, "D", 35), (math.inf, "F", 10)]
RATING_THRESHOLDS = [(80, "Sustainable"), (60, "Needs Work"), (0, "High Impact")]
ASSET_STATUS_THRESHOLDS = {
    "image": {"green": 50_000, "amber": 300_000},
    "script": {"green": 30_000, "amber": 150_000},
    "css": {"green": 20_000, "amber": 100_000},
    "font": {"green": 50_000, "amber": 150_000},
    "media": {"green": 500_000, "amber": 2_000_000},
}
SAVINGS_RATES = {
    "image": {"green": 0.0, "amber": 0.7, "red": 0.7},
    "script": {"green": 0.0, "amber": 0.3, "red": 0.5},
    "css": {"green": 0.0, "amber": 0.5, "red": 0.8},
    "font": {"green": 0.0, "amber": 0.5, "red": 0.7},
    "media": {"green": 0.0, "amber": 0.3, "red": 0.4},
}
OPTIMIZATION_TIPS = {
    "image": {
        "red": "Large image detected. Convert to WebP or AVIF (saves 60–85% size). Add loading='lazy' for below-the-fold images and use srcset for responsive images to avoid serving oversized files to mobile users.",
        "amber": "Consider converting to WebP or AVIF and compressing with Squoosh or ImageOptim. Add loading='lazy' if this image is not in the initial viewport.",
        "green": "Image is well optimised. Ensure srcset is used for responsive sizing and consider a CDN for faster global delivery.",
    },
    "script": {
        "red": "Critical JavaScript bundle. Enable tree-shaking and route-based code-splitting in your bundler. Audit dependencies with bundlephobia.com. Use async or defer attributes to prevent render-blocking.",
        "amber": "Consider minification, removing unused imports, and adding async/defer attributes. Ensure Brotli or Gzip compression is active.",
        "green": "Script is well-sized. Ensure it is deferred if non-critical and served with Brotli compression for best transfer efficiency.",
    },
    "css": {
        "red": "Stylesheet is critically large. Run PurgeCSS or equivalent to strip unused rules — production builds should typically be under 15 KB. Extract critical CSS inline and load the rest asynchronously.",
        "amber": "Run PurgeCSS to remove unused style rules. Consider splitting into critical (inline) CSS and a lazily-loaded secondary stylesheet.",
        "green": "Stylesheet is well optimised. Ensure minification is enabled in your build pipeline and that the file is Brotli-compressed.",
    },
    "font": {
        "red": "Large font file. Subset the font to only the characters you use with FontSquirrel or glyphhanger — this can reduce size by 70%+. Use WOFF2 format and add font-display: swap to avoid invisible text.",
        "amber": "Subset the font to your used character range to reduce size by 40–60%. Ensure WOFF2 format is used (best compression) and add font-display: swap.",
        "green": "Font is well-optimised. WOFF2 is the recommended format. Subsetting can reduce size further if specific glyphs are unused.",
    },
    "media": {
        "red": "Large media file. Host video content on a CDN (YouTube, Vimeo embed) rather than self-hosting. Use modern codecs (H.265 / AV1) and add the lazy loading attribute to defer off-screen media.",
        "amber": "Consider hosting video on a CDN and using lazy loading. Modern codecs (H.265, AV1) can reduce size by 30–50% vs H.264.",
        "green": "Media file is within an acceptable range. Ensure lazy loading is enabled to avoid unnecessary transfers.",
    },
}


def calculate_co2_grams(size_bytes: int) -> float:
    return round(size_bytes / 1e9 * ENERGY_PER_GB * CARBON_INTENSITY, 6)


def get_grade_and_score(co2_grams: float) -> tuple[str, int]:
    return next((grade, score) for threshold, grade, score in GRADE_THRESHOLDS if co2_grams <= threshold)


def get_rating(score: int) -> str:
    return next(label for minimum, label in RATING_THRESHOLDS if score >= minimum)


def get_asset_status(asset_type: str, size_bytes: int) -> str:
    limits = ASSET_STATUS_THRESHOLDS[asset_type]
    return "green" if size_bytes <= limits["green"] else "amber" if size_bytes <= limits["amber"] else "red"


def get_real_world_comparison(co2_grams: float) -> str:
    metres = co2_grams / CAR_GRAMS_PER_KM * 1000
    if metres >= 1000:
        return f"Equivalent to driving {metres / 1000:.2f} km in a petrol car"
    if metres >= 1:
        return f"Equivalent to driving {int(metres)} metres in a petrol car"
    return "Less than 1 metre driven in a petrol car per page load"


def calculate_annual_metrics(co2_per_visit: float) -> dict:
    annual_kg = co2_per_visit * MONTHLY_VISITS * 12 / 1000
    return {"annual_co2_kg": round(annual_kg, 3), "trees_to_offset": round(annual_kg / TREE_KG_PER_YEAR, 1)}


def methodology() -> dict:
    return {
        "energy_per_gb": ENERGY_PER_GB,
        "carbon_intensity": CARBON_INTENSITY,
        "car_grams_per_km": CAR_GRAMS_PER_KM,
        "monthly_visits": MONTHLY_VISITS,
        "tree_kg_per_year": TREE_KG_PER_YEAR,
        "grades": [{"grade": g, "max_co2": None if math.isinf(t) else t, "score": s} for t, g, s in GRADE_THRESHOLDS],
        "ratings": [{"min_score": m, "label": label} for m, label in RATING_THRESHOLDS],
        "asset_status": ASSET_STATUS_THRESHOLDS,
        "savings_rates": SAVINGS_RATES,
    }
