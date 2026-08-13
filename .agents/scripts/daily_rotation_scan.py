#!/usr/bin/env python3
"""Daily rotation scan — one scanner category per day.

Runs as a scheduled task. Surfaces 3-5 findings from today's rotated
category, applies adaptive thresholds (suppressed categories the operator
consistently ignores), and appends to the findings index.

Rotation:
  Monday:    defects (skill_scripts)
  Tuesday:   stale-refs (propagation)
  Wednesday: coverage (session_gaps)
  Thursday:  epistemic-debt (wiki concepts)
  Friday:    friction (critique log patterns)

The scan reads from the findings index and applies the adaptive threshold:
categories with <20% act-on rate get suppressed; categories with >80%
get amplified (lower threshold = more findings).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path("P:/.agents/scripts")))
from findings_index import query, act_on_rate  # noqa: E402

ROTATION = {
    0: {"name": "Monday", "category": "defects", "description": "Scanner defects (skill_scripts)"},
    1: {"name": "Tuesday", "category": "stale-refs", "description": "Stale references (propagation)"},
    2: {"name": "Wednesday", "category": "coverage", "description": "Test coverage gaps"},
    3: {"name": "Thursday", "category": "epistemic-debt", "description": "Epistemic debt (wiki concepts)"},
    4: {"name": "Friday", "category": "friction", "description": "Friction patterns (critique log)"},
}


def run_rotation() -> dict:
    """Run today's rotation scan and return results."""
    today = datetime.now().weekday()
    if today >= 5:  # Weekend — no scan
        return {"status": "skipped", "reason": "weekend"}

    rotation = ROTATION.get(today)
    if not rotation:
        return {"status": "skipped", "reason": "no rotation for weekday"}

    category = rotation["category"]

    # Adaptive threshold: check act-on rate for this category
    rate = act_on_rate(category=category, since_days=30)
    threshold_adjustment = "normal"

    if rate["total"] >= 10:  # Only adjust when we have enough data
        if rate["rate"] < 0.2:
            threshold_adjustment = "suppressed"
        elif rate["rate"] > 0.8:
            threshold_adjustment = "amplified"

    # Query recent findings for this category
    findings = query(category=category, since_days=7, limit=5 if threshold_adjustment != "amplified" else 10)

    return {
        "status": "complete",
        "day": rotation["name"],
        "category": category,
        "description": rotation["description"],
        "threshold": threshold_adjustment,
        "act_on_rate": rate,
        "findings_count": len(findings),
        "findings": [{"title": f.get("title", "?"), "severity": f.get("severity", "?")} for f in findings],
    }


if __name__ == "__main__":
    result = run_rotation()
    print(json.dumps(result, indent=2))
