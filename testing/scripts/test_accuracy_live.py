"""
scripts/test_accuracy_live.py
────────────────────────────────
INTEGRATION / ACCURACY TEST.

Unlike test_carbon_unit.py (which tests the maths in isolation), this
script tests the FULL, REAL system end-to-end:

    your browser's request -> FastAPI -> scraper.py -> carbon.py -> DB -> response

It audits the local fixture page (fixtures/index.html) through your
actual running EcoWeb Auditor backend, then compares the tool's real
output against the ground truth computed by compute_expected.py.

PREREQUISITES — three things must be running at once:
  1. Your PostgreSQL database (already running as a Windows service)
  2. Your FastAPI backend:
       cd backend
       venv\\Scripts\\activate
       uvicorn main:app --reload --port 8000
  3. The fixture page served locally:
       cd testing_kit/fixtures
       python -m http.server 9000
     (leave this running in its own terminal)

Then, in a FOURTH terminal, run this script:
       python scripts/test_accuracy_live.py

Requires: pip install httpx  (already installed as part of the backend)
"""

import asyncio
import sys

import httpx

# ── Configuration ──────────────────────────────────────────────────────────
API_BASE = "http://localhost:8000"
FIXTURE_URL = "http://localhost:9000/index.html"

# Ground truth from compute_expected.py — DO NOT hand-edit without
# re-running compute_expected.py first, to keep these in sync.
EXPECTED = {
    "total_bytes": 1_381_229,
    "total_co2": 0.494508,
    "grade": "C",
    "score": 50,
    "request_count": 9,      # 3 images + 3 scripts + 2 css + 1 font
    "page_weight_mb": 1.32,
}

EXPECTED_ASSET_STATUS = {
    "image-green.jpg":  "green",
    "image-amber.jpg":  "amber",
    "image-red.jpg":    "red",
    "script-green.js":  "green",
    "script-amber.js":  "amber",
    "script-red.js":    "red",
    "style-green.css":  "green",
    "style-amber.css":  "amber",
    "font-green.woff2": "green",
}

# Tolerance for CO2 float comparison (accounts for negligible HTTP framing
# differences between environments — should be exact in practice)
CO2_TOLERANCE = 0.00005


results = []


def check(test_id, description, actual, expected, tolerance=None):
    if tolerance is not None:
        passed = abs(actual - expected) <= tolerance
    else:
        passed = actual == expected
    results.append({
        "id": test_id, "description": description,
        "expected": expected, "actual": actual, "passed": passed,
    })


async def run_fixture_test(client: httpx.AsyncClient):
    """AT01–AT07: Audit the local fixture and compare against ground truth."""
    print(f"Auditing fixture page: {FIXTURE_URL}")
    try:
        resp = await client.post(
            f"{API_BASE}/api/audit", json={"url": FIXTURE_URL}, timeout=30.0
        )
    except httpx.ConnectError:
        print("\n✗ COULD NOT CONNECT to the backend at", API_BASE)
        print("  Make sure `uvicorn main:app --reload --port 8000` is running.")
        sys.exit(1)

    if resp.status_code != 200:
        print(f"\n✗ Backend returned HTTP {resp.status_code}: {resp.text}")
        print("  Make sure `python -m http.server 9000` is running inside")
        print("  testing_kit/fixtures/ so the backend can reach the fixture.")
        sys.exit(1)

    data = resp.json()

    check("AT01", "Total bytes transferred matches ground truth exactly",
          data["total_bytes"], EXPECTED["total_bytes"])

    check("AT02", "Total CO2 matches ground truth (SWD formula)",
          data["total_co2"], EXPECTED["total_co2"], tolerance=CO2_TOLERANCE)

    check("AT03", "Sustainability grade matches ground truth",
          data["grade"], EXPECTED["grade"])

    check("AT04", "Score matches ground truth",
          data["score"], EXPECTED["score"])

    check("AT05", "Asset (request) count matches ground truth",
          data["request_count"], EXPECTED["request_count"])

    check("AT06", "Page weight (MB) matches ground truth",
          data["page_weight_mb"], EXPECTED["page_weight_mb"], tolerance=0.01)

    # AT07: Per-asset status — every single asset must be correctly classified
    actual_statuses = {a["name"]: a["status"] for a in data["assets"]}
    all_correct = all(
        actual_statuses.get(name) == expected_status
        for name, expected_status in EXPECTED_ASSET_STATUS.items()
    )
    check("AT07", "All 9 assets individually classified with correct status",
          all_correct, True)

    return data


async def run_error_handling_tests(client: httpx.AsyncClient):
    """AT08–AT10: Confirm the API fails gracefully on bad input."""

    # AT08: Malformed URL should be rejected with 422, not crash the server
    resp = await client.post(
        f"{API_BASE}/api/audit", json={"url": "not-a-valid-url"}, timeout=10.0
    )
    check("AT08", "Malformed URL returns HTTP 422 (not 500)",
          resp.status_code, 422)

    # AT09: Non-existent domain should fail cleanly, not hang or crash
    resp = await client.post(
        f"{API_BASE}/api/audit",
        json={"url": "https://this-domain-genuinely-does-not-exist-12345.com"},
        timeout=15.0,
    )
    check("AT09", "Unreachable domain returns HTTP 422 (not 500)",
          resp.status_code, 422)

    # AT10: Health check endpoint
    resp = await client.get(f"{API_BASE}/health", timeout=5.0)
    check("AT10", "Health check endpoint returns 200 OK",
          resp.status_code, 200)


async def run_persistence_tests(client: httpx.AsyncClient, audit_id: int):
    """AT11–AT12: Confirm the audit was actually saved to PostgreSQL."""

    # AT11: The audit we just ran should now appear when fetched by ID
    resp = await client.get(f"{API_BASE}/api/audit/{audit_id}", timeout=10.0)
    check("AT11", f"Saved audit #{audit_id} can be retrieved from the database",
          resp.status_code, 200)

    # AT12: It should also appear in the recent audits list
    resp = await client.get(f"{API_BASE}/api/audits/recent?limit=50", timeout=10.0)
    recent_ids = [a["audit_id"] for a in resp.json()]
    check("AT12", f"Audit #{audit_id} appears in /api/audits/recent",
          audit_id in recent_ids, True)


def print_report():
    print()
    print("=" * 100)
    print(f"{'ID':6s} {'Description':60s} {'Expected':>14s} {'Actual':>14s} {'Result':>8s}")
    print("-" * 100)

    passed_count = 0
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        if r["passed"]:
            passed_count += 1
        exp_str = str(r["expected"])[:14]
        act_str = str(r["actual"])[:14]
        print(f"{r['id']:6s} {r['description']:60s} {exp_str:>14s} {act_str:>14s} {status:>8s}")

    print("-" * 100)
    total = len(results)
    print(f"\nRESULT: {passed_count} / {total} tests passed "
          f"({passed_count/total*100:.1f}%)\n")
    return passed_count, total


async def main():
    async with httpx.AsyncClient() as client:
        fixture_data = await run_fixture_test(client)
        await run_error_handling_tests(client)
        await run_persistence_tests(client, fixture_data["audit_id"])

    passed, total = print_report()

    if passed == total:
        print("✓ ALL INTEGRATION TESTS PASSED.")
        print("  The live system (scraper + SWD engine + database) produces")
        print("  results that exactly match the hand-computed ground truth.")
        print("\n  This table is ready to paste into your thesis Chapter 3")
        print("  (Development and Testing) and referenced again in Chapter 5")
        print("  (Evaluation) as evidence of accuracy validation.")
    else:
        print("✗ SOME TESTS FAILED. Do not paste these results into your")
        print("  thesis until you've investigated the failure(s) above.")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    asyncio.run(main())
