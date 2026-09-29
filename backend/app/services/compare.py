"""Compares two audits: orders them by date and reports how each metric changed."""

import math

from app.schemas import AuditSummary

METRICS = [
    ("score", "Score", True),
    ("total_co2", "CO₂ per visit", False),
    ("annual_co2_kg", "Annual CO₂", False),
    ("total_bytes", "Page weight", False),
    ("request_count", "Requests", False),
]


def change_pct(older: float, newer: float) -> int | None:
    # Rounds half up, like the percentages people see elsewhere, not Python's half-to-even.
    return None if older == 0 else math.floor((newer - older) / older * 100 + 0.5)


def compare_row(key: str, label: str, older: float, newer: float, higher_is_better: bool) -> dict:
    pct = change_pct(older, newer)
    if older == newer or pct == 0:
        direction, verdict = "same", "same"
    else:
        direction = "up" if newer > older else "down"
        verdict = "better" if (newer > older) == higher_is_better else "worse"
    return {"key": key, "label": label, "older": older, "newer": newer,
            "change_pct": pct, "direction": direction, "verdict": verdict}


def compare_audits(a: AuditSummary, b: AuditSummary) -> dict:
    older, newer = sorted((a, b), key=lambda audit: audit.audited_at)

    metrics = [compare_row(key, label, getattr(older, key), getattr(newer, key), higher)
               for key, label, higher in METRICS]

    co2_by_name = [{c.name: c.total_co2 for c in audit.categories} for audit in (older, newer)]
    names = list(dict.fromkeys([*co2_by_name[0], *co2_by_name[1]]))
    categories = [compare_row("category", name, co2_by_name[0].get(name, 0), co2_by_name[1].get(name, 0), False)
                  for name in names]

    co2 = metrics[1]
    if co2["verdict"] == "same":
        summary = "Both audits have effectively the same carbon footprint per visit."
    else:
        amount = f"{abs(co2['change_pct'])}% " if co2["change_pct"] is not None else ""
        summary = f"Audit B emits {amount}{'less' if co2['verdict'] == 'better' else 'more'} CO₂ per visit than Audit A."

    side_fields = {"id", "url", "audited_at", "grade", "score", "total_co2"}
    return {
        "older": older.model_dump(include=side_fields),
        "newer": newer.model_dump(include=side_fields),
        "verdict": co2["verdict"],
        "summary": summary,
        "metrics": metrics,
        "categories": categories,
    }
