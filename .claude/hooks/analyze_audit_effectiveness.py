#!/usr/bin/env python3
r"""
Analyze Audit Effectiveness

Analyzes hook_decisions.jsonl and audit_outcomes.jsonl to measure:
- False positive rate (safe claims that were blocked)
- True positive rate (violations that were caught)
- Oscillation rate (CC getting stuck in audit loops)

Run with: python P:\.claude\hooks\analyze_audit_effectiveness.py
"""

import json
import logging as _li
import sys
from collections import defaultdict
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent
_LOG_DIR = _HOOKS_DIR / "logs" / "diagnostics"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_logger = _li.getLogger(__name__)
_handler = _li.FileHandler(_LOG_DIR / "hook_stderr.log", encoding="utf-8")
_handler.setFormatter(_li.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(_li.WARNING)

HOOKS_DIR = Path("P:/.claude/hooks")
SESSION_DATA_DIR = HOOKS_DIR / "session_data"


def load_jsonl(file_path: Path) -> list:
    """Load entries from a JSONL file."""
    if not file_path.exists():
        return []

    entries = []
    try:
        with open(file_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    except Exception as e:
        _logger.error(f"Error reading {file_path}: {e}")

    return entries


def get_all_decision_logs() -> list:
    """Load all hook_decisions_*.jsonl files."""
    entries = []
    pattern = "hook_decisions_*.jsonl"

    if SESSION_DATA_DIR.exists():
        for file_path in SESSION_DATA_DIR.glob(pattern):
            entries.extend(load_jsonl(file_path))

    return entries


def main() -> int:
    """Run the audit effectiveness analysis and report metrics.

    Loads hook decision logs and audit outcomes, then calculates:
    - False positive rate (safe claims that were blocked)
    - True positive rate (violations that were caught)
    - Oscillation rate (CC getting stuck in audit loops)

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    print("=" * 60)
    print("ASSUMPTION AUDIT EFFECTIVENESS ANALYSIS")
    print("=" * 60)
    print()

    # Load data
    decisions = get_all_decision_logs()
    outcomes = load_jsonl(SESSION_DATA_DIR / "audit_outcomes.jsonl")

    print(f"Total hook decisions logged: {len(decisions)}")
    print(f"Audit outcomes tracked: {len(outcomes)}")
    print()

    if not decisions and not outcomes:
        print(
            "No data found. Run hooks with DECISION_LOG_ENABLED=true to generate logs."
        )
        print("Log location:", SESSION_DATA_DIR)
        return 0

    # Analyze outcomes
    if outcomes:
        print("=" * 60)
        print("AUDIT OUTCOME BREAKDOWN")
        print("=" * 60)

        outcome_counts = defaultdict(int)
        for outcome in outcomes:
            outcome_counts[outcome["outcome_type"]] += 1

        total_outcomes = len(outcomes)
        for outcome_type, count in sorted(outcome_counts.items(), key=lambda x: -x[1]):
            percentage = (count / total_outcomes) * 100 if total_outcomes > 0 else 0
            print(f"  {outcome_type}: {count} ({percentage:.1f}%)")

        # False positive analysis
        false_positives = [o for o in outcomes if o["outcome_type"] == "proceeded"]
        true_positives = [o for o in outcomes if o["outcome_type"] == "used_tools"]
        oscillations = [o for o in outcomes if o["outcome_type"] == "blocked_again"]

        print()
        print("EFFECTIVENESS METRICS:")
        print(
            f"  False positive rate (blocked but safe): {len(false_positives)}/{total_outcomes} ({len(false_positives) / total_outcomes * 100:.1f}%)"
            if total_outcomes > 0
            else ""
        )
        print(
            f"  True positive rate (blocked & fixed): {len(true_positives)}/{total_outcomes} ({len(true_positives) / total_outcomes * 100:.1f}%)"
            if total_outcomes > 0
            else ""
        )
        print(
            f"  Oscillation rate (stuck in loops): {len(oscillations)}/{total_outcomes} ({len(oscillations) / total_outcomes * 100:.1f}%)"
            if total_outcomes > 0
            else ""
        )

        # Top false positive patterns
        if false_positives:
            print()
            print("TOP FALSE POSITIVE PATTERNS:")
            for fp in sorted(
                false_positives,
                key=lambda x: len(x.get("response_text", "")),
                reverse=True,
            )[:5]:
                response = fp.get("response_text", "")[:60]
                claim_type = fp.get("claim_type", "unknown")
                print(f"  - [{claim_type}] {response}...")

    # Analyze hook decisions
    if decisions:
        print()
        print("=" * 60)
        print("HOOK DECISION BREAKDOWN")
        print("=" * 60)

        hook_counts = defaultdict(int)
        block_counts = defaultdict(int)

        for decision in decisions:
            hook_name = decision.get("hook_name", "unknown")
            hook_counts[hook_name] += 1
            if decision.get("decision") == "block":
                block_counts[hook_name] += 1

        print(f"{'Hook':<30} {'Blocks':<10} {'Total':<10}")
        print("-" * 60)
        for hook_name in sorted(hook_counts.keys()):
            blocks = block_counts.get(hook_name, 0)
            total = hook_counts[hook_name]
            print(f"{hook_name:<30} {blocks:<10} {total:<10}")

    # Recommendations
    print()
    print("=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)

    if outcomes:
        total = len(outcomes)
        fp_rate = len(false_positives) / total if total > 0 else 0
        osc_rate = len(oscillations) / total if total > 0 else 0
        tp_rate = len(true_positives) / total if total > 0 else 0

        if fp_rate > 0.3:
            print("⚠️  False positive rate > 30%")
            print("   Consider:")
            print("   1. Add more SAFE_RESPONSE_PATTERNS for detected types")
            print(
                "   2. Improve audit prompt to better distinguish empirical vs knowledge"
            )
            print()

        if osc_rate > 0:
            print("⚠️  Oscillations detected")
            print("   The audit prompt may not guide CC correctly.")
            print("   Review and improve AUDIT_PROMPT wording.")
            print()

        if tp_rate > 0.5:
            print("✓ System working effectively")
            print("  CC successfully fixes violations after audit.")
            print()
    else:
        print("No outcome data available yet.")
        print("Generate data by running hooks and triggering audits.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
