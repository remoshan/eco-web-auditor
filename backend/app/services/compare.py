import math

from app.schemas import AuditSummary

METRICS = [("score", "Score", True), ("total_co2", "CO₂ per visit", False), ("annual_co2_kg", "Annual CO₂", False),
           ("total_bytes", "Page weight", False), ("request_count", "Requests", False)]


def compare_row(key: str, label: str, older: float, newer: float, higher_is_better: bool = False) -> dict:
    pct = None if older == 0 else math.floor((newer - older) / older * 100 + 0.5)
    same = older == newer or pct == 0
    return {"key": key, "label": label, "older": older, "newer": newer, "change_pct": pct,
            "direction": "same" if same else "up" if newer > older else "down",
            "verdict": "same" if same else "better" if (newer > older) == higher_is_better else "worse"}


def compare_audits(a: AuditSummary, b: AuditSummary) -> dict:
    older, newer = sorted((a, b), key=lambda audit: audit.audited_at)
    metrics = [compare_row(key, label, getattr(older, key), getattr(newer, key), higher)
               for key, label, higher in METRICS]
    before, after = ({c.name: c.total_co2 for c in audit.categories} for audit in (older, newer))
    categories = [compare_row("category", name, before.get(name, 0), after.get(name, 0))
                  for name in dict.fromkeys([*before, *after])]

    co2 = metrics[1]
    if co2["verdict"] == "same":
        summary = "Both audits have effectively the same carbon footprint per visit."
    else:
        amount = "" if co2["change_pct"] is None else f"{abs(co2['change_pct'])}% "
        summary = f"Audit B emits {amount}{'less' if co2['verdict'] == 'better' else 'more'} CO₂ per visit than Audit A."
    return {"older": older, "newer": newer, "verdict": co2["verdict"], "summary": summary, "metrics": metrics,
            "categories": categories}
