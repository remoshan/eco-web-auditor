"""
scripts/compute_expected.py
─────────────────────────────
Computes the GROUND TRUTH expected output for fixtures/index.html by
applying the exact SWD formula to the exact, hand-controlled byte
sizes of every asset in the fixture.

This is the "answer key" — run this once to generate the numbers,
then compare them against what EcoWeb Auditor actually returns when
it audits the same fixture page. Any mismatch is a genuine bug.

Run with:  python scripts/compute_expected.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "carbon_module"))
from carbon import (  # noqa: E402
    calculate_co2_grams,
    get_grade_and_score,
    get_asset_status,
    get_real_world_comparison,
    calculate_annual_metrics,
)

# ── Known fixture asset sizes (must match fixtures/assets/*) ─────────────────
HTML_SIZE_BYTES = 1229  # measured via `wc -c fixtures/index.html`

ASSETS = [
    ("image-green.jpg",  "image",  40_000),
    ("image-amber.jpg",  "image", 150_000),
    ("image-red.jpg",    "image", 800_000),
    ("script-green.js",  "script", 20_000),
    ("script-amber.js",  "script", 80_000),
    ("script-red.js",    "script", 200_000),
    ("style-green.css",  "css",    10_000),
    ("style-amber.css",  "css",    50_000),
    ("font-green.woff2", "font",   30_000),
]


def main():
    print("=" * 72)
    print("GROUND TRUTH — EcoWeb Auditor Accuracy Test Fixture")
    print("=" * 72)

    print(f"\nHTML document size: {HTML_SIZE_BYTES:,} bytes\n")

    print(f"{'Asset':22s} {'Type':8s} {'Size (B)':>10s} {'CO2 (g)':>12s} {'Status':8s}")
    print("-" * 72)

    total_bytes = HTML_SIZE_BYTES
    asset_rows = []

    for name, atype, size in ASSETS:
        co2 = calculate_co2_grams(size)
        status = get_asset_status(atype, size)
        total_bytes += size
        asset_rows.append((name, atype, size, co2, status))
        print(f"{name:22s} {atype:8s} {size:>10,} {co2:>12.6f} {status:8s}")

    total_co2 = calculate_co2_grams(total_bytes)
    grade, score = get_grade_and_score(total_co2)
    comparison = get_real_world_comparison(total_co2)
    annual = calculate_annual_metrics(total_co2)
    page_weight_mb = round(total_bytes / (1024 * 1024), 2)

    print("-" * 72)
    print(f"\nTOTAL BYTES (HTML + 9 assets): {total_bytes:,} bytes  ({page_weight_mb} MB)")
    print(f"TOTAL CO2 PER VISIT:           {total_co2:.6f} g")
    print(f"GRADE:                         {grade}  (score: {score}/100)")
    print(f"COMPARISON:                    {comparison}")
    print(f"ANNUAL CO2 (10k visits/mo):    {annual['annual_kg']} kg  "
          f"({annual['trees_to_offset']} trees to offset)")

    print("\n" + "=" * 72)
    print("COPY THIS INTO YOUR THESIS TEST CASE TABLE (Expected Result column):")
    print("=" * 72)
    print(f"""
  Total bytes transferred : {total_bytes:,} bytes
  Total CO2 per visit     : {total_co2:.6f} g  (rounds to {round(total_co2, 4)} g)
  Sustainability grade    : {grade}
  Score                   : {score}/100
  Page weight             : {page_weight_mb} MB
  Asset count              : {len(ASSETS)}
  Per-asset status         : {[(r[0], r[4]) for r in asset_rows]}
""")


if __name__ == "__main__":
    main()
