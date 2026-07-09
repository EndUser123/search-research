"""Intent-distribution eval for the expanded golden corpus.

Closes FM-3: the 92% UNKNOWN figure was measured on a CHS monoculture
(23/26 session-retrieval variants). This runner classifies a corpus that
includes real code/concept/exploratory queries and reports the UNKNOWN share
on THAT population, plus per-intent backend coverage.

Exit code 1 when UNKNOWN share shifts > 10pp from the recorded baseline
(CI-friendly regression gate: a drift in the classifier or BACKEND_FOR_INTENT
that silently inflates UNKNOWN fan-out will break the gate loudly).

Usage:
    python -m core.chs.eval.intent_distribution_eval [--cases <path>]
        [--baseline <path>] [--update-baseline] [--json]

Baseline lives beside the corpus (intent_baseline.json) and records the
UNKNOWN share at the time the corpus was authored.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running both as `python -m core.chs.eval.intent_distribution_eval`
# (from plugin root) and directly. conftest adds plugin root for tests.
_PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from core.query_intent import classify_query_intent, BACKEND_FOR_INTENT, IntentType  # noqa: E402

DEFAULT_CASES = Path(__file__).parent / "golden_cases_intent.jsonl"
DEFAULT_BASELINE = Path(__file__).parent / "intent_baseline.json"
DRIFT_THRESHOLD_PP = 0.10  # 10 percentage points


def load_cases(path: Path = DEFAULT_CASES) -> list[dict]:
    cases: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def evaluate(cases: list[dict] | None = None) -> dict:
    """Classify every case; return the distribution + per-case detail.

    Returns:
        {
          "total": N,
          "unknown": k,
          "unknown_share": k/N,
          "by_intent": {"technical": 5, "unknown": 1, ...},
          "by_query_class": {"code": {"total":5,"unknown":0}, ...},
          "per_case": [{id, query, query_class, expected_intent, actual_intent,
                        match, expected_backends, actual_backends}, ...],
          "surprises": [<cases where actual != expected>],
        }
    """
    if cases is None:
        cases = load_cases()

    by_intent: dict[str, int] = {}
    by_class: dict[str, dict[str, int]] = {}
    per_case: list[dict] = []
    surprises: list[dict] = []
    unknown = 0

    for c in cases:
        result = classify_query_intent(c["query"])
        intent_val = result.intent.value
        allowed = BACKEND_FOR_INTENT.get(result.intent, set())
        actual_backends = sorted(allowed) if allowed else []  # empty = ALL (UNKNOWN)
        expected_intent = c.get("expected_intent", "")
        expected_backends = sorted(c.get("expected_backends", []))
        match = intent_val == expected_intent

        by_intent[intent_val] = by_intent.get(intent_val, 0) + 1
        if intent_val == IntentType.UNKNOWN.value:
            unknown += 1

        qc = c.get("query_class", "unclassified")
        bucket = by_class.setdefault(qc, {"total": 0, "unknown": 0})
        bucket["total"] += 1
        if intent_val == IntentType.UNKNOWN.value:
            bucket["unknown"] += 1

        row = {
            "id": c["id"],
            "query": c["query"],
            "query_class": qc,
            "expected_intent": expected_intent,
            "actual_intent": intent_val,
            "confidence": round(result.confidence, 3),
            "match": match,
            "expected_backends": expected_backends,
            "actual_backends": actual_backends,
        }
        per_case.append(row)
        if not match:
            surprises.append(row)

    total = len(cases)
    return {
        "total": total,
        "unknown": unknown,
        "unknown_share": round(unknown / total, 4) if total else 0.0,
        "by_intent": by_intent,
        "by_query_class": by_class,
        "per_case": per_case,
        "surprises": surprises,
    }


def load_baseline(path: Path = DEFAULT_BASELINE) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_baseline(unknown_share: float, total: int, path: Path = DEFAULT_BASELINE) -> None:
    payload = {
        "unknown_share": round(unknown_share, 4),
        "total": total,
        "note": "Authored-baseline UNKNOWN share on golden_cases_intent.jsonl. "
                "Gate fails when observed share drifts >10pp from this.",
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _render_text(report: dict) -> str:
    lines = []
    lines.append(f"Intent distribution on expanded corpus (n={report['total']})")
    lines.append(f"  UNKNOWN: {report['unknown']}/{report['total']} "
                 f"= {report['unknown_share']*100:.1f}%")
    lines.append("  by_intent:")
    for intent, n in sorted(report["by_intent"].items(), key=lambda kv: -kv[1]):
        lines.append(f"    {intent:14} {n}")
    lines.append("  by_query_class:")
    for qc, b in sorted(report["by_query_class"].items()):
        lines.append(f"    {qc:12} total={b['total']} unknown={b['unknown']}")
    if report["surprises"]:
        lines.append(f"  surprises (actual != expected): {len(report['surprises'])}")
        for s in report["surprises"]:
            lines.append(f"    {s['id']}: expected={s['expected_intent']} "
                         f"actual={s['actual_intent']} | {s['query'][:50]}")
    else:
        lines.append("  surprises: 0 (every case classified as its expected intent)")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    p.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    p.add_argument("--update-baseline", action="store_true",
                   help="Write the current UNKNOWN share as the baseline and exit 0.")
    p.add_argument("--json", action="store_true", help="Emit the report as JSON.")
    args = p.parse_args(argv)

    cases = load_cases(args.cases)
    report = evaluate(cases)

    if args.update_baseline:
        write_baseline(report["unknown_share"], report["total"], args.baseline)
        print(f"Baseline written: unknown_share={report['unknown_share']} "
              f"total={report['total']} -> {args.baseline}")
        return 0

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(_render_text(report))

    baseline = load_baseline(args.baseline)
    if baseline is None:
        # No baseline yet: do not fail, but tell the operator to seed one.
        print(f"\nNo baseline at {args.baseline}; run with --update-baseline to seed.")
        return 0

    drift = report["unknown_share"] - baseline["unknown_share"]
    if abs(drift) > DRIFT_THRESHOLD_PP:
        print(f"\nGATE FAIL: UNKNOWN share drifted {drift*100:+.1f}pp "
              f"(baseline={baseline['unknown_share']*100:.1f}%, "
              f"observed={report['unknown_share']*100:.1f}%, threshold=±10pp).")
        return 1

    print(f"\nGATE PASS: UNKNOWN share within ±10pp of baseline "
          f"(drift {drift*100:+.1f}pp).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
