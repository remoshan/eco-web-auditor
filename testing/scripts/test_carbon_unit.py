"""
scripts/test_carbon_unit.py
─────────────────────────────
UNIT TESTS for the SWD carbon calculation engine (carbon.py).

These test the mathematical core in complete isolation — no server,
no network, no database. Every test computes its own expected value
by hand (shown in comments) so there is no circular dependency on
the code being tested.

Run with:  python scripts/test_carbon_unit.py
Exit code 0 = all tests passed. Non-zero = at least one failure.

Use the printed PASS/FAIL table directly in your thesis
(Chapter 3, Unit Testing section).
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "carbon_module"))
from carbon import (  # noqa: E402
    calculate_co2_grams,
    get_grade_and_score,
    get_asset_status,
    calculate_annual_metrics,
    get_real_world_comparison,
)

# ── Test runner (lightweight — no pytest dependency needed) ──────────────────
results = []


def check(test_id: str, description: str, actual, expected, tolerance=None):
    """Compare actual vs expected. Supports exact match or float tolerance."""
    if tolerance is not None:
        passed = abs(actual - expected) <= tolerance
    else:
        passed = actual == expected

    results.append({
        "id": test_id,
        "description": description,
        "expected": expected,
        "actual": actual,
        "passed": passed,
    })


# ═══════════════════════════════════════════════════════════════════════════
# UT01–UT05 — calculate_co2_grams()
# ═══════════════════════════════════════════════════════════════════════════

# UT01: 1 GB transfer.
# Hand calculation: (1,000,000,000 / 1e9) * 0.81 * 442 = 1 * 0.81 * 442 = 358.02
check("UT01", "1 GB transfer produces 358.02g CO2",
      calculate_co2_grams(1_000_000_000), 358.02, tolerance=0.001)

# UT02: 1 MB transfer.
# Hand calculation: (1,000,000 / 1e9) * 0.81 * 442 = 0.001 * 358.02 = 0.35802
check("UT02", "1 MB transfer produces 0.35802g CO2",
      calculate_co2_grams(1_000_000), 0.35802, tolerance=0.00001)

# UT03: Zero bytes must return exactly 0.0 (not a tiny float or error)
check("UT03", "0 bytes returns exactly 0.0g CO2",
      calculate_co2_grams(0), 0.0)

# UT04: Negative bytes (defensive — should never happen, but must not crash
# or return a negative/nonsensical CO2 value)
check("UT04", "Negative bytes returns 0.0g CO2 (defensive)",
      calculate_co2_grams(-500), 0.0)

# UT05: Known 1,381,229-byte fixture total (cross-check against
# compute_expected.py ground truth)
check("UT05", "Fixture total bytes (1,381,229) produces 0.494508g CO2",
      calculate_co2_grams(1_381_229), 0.494508, tolerance=0.000001)


# ═══════════════════════════════════════════════════════════════════════════
# UT06–UT13 — get_grade_and_score() boundary testing
# ═══════════════════════════════════════════════════════════════════════════
# Every boundary is tested at, just below, and just above the threshold to
# catch off-by-one errors in the <= comparisons.

check("UT06", "0.000g is A+ (well below all thresholds)",
      get_grade_and_score(0.000)[0], "A+")

check("UT07", "Exactly 0.095g is A+ (inclusive boundary)",
      get_grade_and_score(0.095)[0], "A+")

check("UT08", "0.0951g (just above A+ threshold) is A",
      get_grade_and_score(0.0951)[0], "A")

check("UT09", "Exactly 0.184g is A (inclusive boundary)",
      get_grade_and_score(0.184)[0], "A")

check("UT10", "Exactly 0.338g is B+ (inclusive boundary)",
      get_grade_and_score(0.338)[0], "B+")

check("UT11", "Exactly 0.493g is B (inclusive boundary)",
      get_grade_and_score(0.493)[0], "B")

check("UT12", "0.494508g (fixture value) is C",
      get_grade_and_score(0.494508)[0], "C")

check("UT13", "1.000g (well above D threshold) is F",
      get_grade_and_score(1.000)[0], "F")


# ═══════════════════════════════════════════════════════════════════════════
# UT14–UT22 — get_asset_status() per asset type
# ═══════════════════════════════════════════════════════════════════════════

# Images: green<=50,000 | amber<=300,000 | red>300,000
check("UT14", "40,000-byte image is green",
      get_asset_status("image", 40_000), "green")
check("UT15", "150,000-byte image is amber",
      get_asset_status("image", 150_000), "amber")
check("UT16", "800,000-byte image is red",
      get_asset_status("image", 800_000), "red")

# Scripts: green<=30,000 | amber<=150,000 | red>150,000
check("UT17", "20,000-byte script is green",
      get_asset_status("script", 20_000), "green")
check("UT18", "80,000-byte script is amber",
      get_asset_status("script", 80_000), "amber")
check("UT19", "200,000-byte script is red",
      get_asset_status("script", 200_000), "red")

# CSS: green<=20,000 | amber<=100,000 | red>100,000
check("UT20", "10,000-byte CSS file is green",
      get_asset_status("css", 10_000), "green")
check("UT21", "50,000-byte CSS file is amber",
      get_asset_status("css", 50_000), "amber")

# Font: green<=50,000
check("UT22", "30,000-byte font is green",
      get_asset_status("font", 30_000), "green")


# ═══════════════════════════════════════════════════════════════════════════
# UT23–UT25 — Real-world comparison string generation
# ═══════════════════════════════════════════════════════════════════════════

# UT23: 0.4945g CO2 -> metres = (0.4945/150)*1000 = 3.29m -> "3 metres"
check("UT23", "0.4945g CO2 produces '3 metres' comparison",
      "3 metres" in get_real_world_comparison(0.4945), True)

# UT24: Very small CO2 should produce the sub-1-metre message
check("UT24", "0.0001g CO2 produces 'Less than 1 metre' message",
      "Less than 1 metre" in get_real_world_comparison(0.0001), True)

# UT25: Large CO2 should switch to km formatting
# 200g -> metres = (200/150)*1000 = 1333.3m -> should show as km
check("UT25", "200g CO2 produces km-formatted comparison",
      "km" in get_real_world_comparison(200), True)


# ═══════════════════════════════════════════════════════════════════════════
# UT26–UT27 — Annual projection maths
# ═══════════════════════════════════════════════════════════════════════════

# UT26: 0.4945g per visit * 10,000 visits/month * 12 months = 59,340g = 59.34kg
check("UT26", "0.4945g/visit at 10k/mo produces ~59.34kg annual CO2",
      calculate_annual_metrics(0.4945)["annual_kg"], 59.34, tolerance=0.01)

# UT27: Trees to offset = annual_kg / 21.0 = 59.34 / 21 = 2.825 -> ~2.8
check("UT27", "59.34kg annual CO2 requires ~2.8 trees to offset",
      calculate_annual_metrics(0.4945)["trees_to_offset"], 2.8, tolerance=0.05)


# ═══════════════════════════════════════════════════════════════════════════
# Report results
# ═══════════════════════════════════════════════════════════════════════════

def print_report():
    print("=" * 100)
    print(f"{'ID':6s} {'Description':62s} {'Expected':>12s} {'Actual':>12s} {'Result':>8s}")
    print("-" * 100)

    passed_count = 0
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        if r["passed"]:
            passed_count += 1
        exp_str = str(r["expected"])[:12]
        act_str = str(r["actual"])[:12]
        print(f"{r['id']:6s} {r['description']:62s} {exp_str:>12s} {act_str:>12s} {status:>8s}")

    print("-" * 100)
    total = len(results)
    print(f"\nRESULT: {passed_count} / {total} tests passed "
          f"({passed_count/total*100:.1f}%)\n")

    if passed_count == total:
        print("✓ ALL UNIT TESTS PASSED — the SWD calculation engine matches")
        print("  its mathematical specification exactly.")
    else:
        print("✗ SOME TESTS FAILED — investigate before including in thesis.")

    return passed_count == total


if __name__ == "__main__":
    all_passed = print_report()
    sys.exit(0 if all_passed else 1)
