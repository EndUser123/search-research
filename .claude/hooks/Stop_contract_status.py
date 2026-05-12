#!/usr/bin/env python3
"""Stop hook: auto-prints contract system dashboard at session/turn end.

This hook surfaces contract writer + Stop statistics at optimal workflow
breakpoints without blocking the response.

Registration: Added to SIDE_EFFECTS in Stop.py (fire-and-forget subprocess).
Output is captured by the Stop aggregator for display to the user.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
TOOLS_DIR = HOOKS_DIR / "tools"
TELEMETRY_SCRIPT = TOOLS_DIR / "contract-telemetry-queries.py"

# Telemetry log paths (resolved from hook location, not home directory)
_WRITER_LOG = HOOKS_DIR / "logs" / "diagnostics" / "task_contract_writer_telemetry.jsonl"
_STOP_LOG = HOOKS_DIR / "logs" / "diagnostics" / "task_contract_telemetry.jsonl"

# Import the authoritative health module for anomaly detection
sys.path.insert(0, str(HOOKS_DIR / "__lib"))


def _load_events(path: Path) -> list[dict]:
    """Load JSONL events from a telemetry log file."""
    if not path.exists():
        return []
    events = []
    try:
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except (OSError, IOError):
        pass
    return events


def _load_log(path: Path) -> list[dict]:
    """Alias for _load_events for compatibility with contract-telemetry-queries patterns."""
    return _load_events(path)


def _age_hours(ts: float) -> float:
    """Return hours since timestamp."""
    now = datetime.now(timezone.utc).timestamp()
    return (now - ts) / 3600


def _green(s: str) -> str:
    return f"\033[92m{s}\033[0m"


def _yellow(s: str) -> str:
    return f"\033[93m{s}\033[0m"


def _red(s: str) -> str:
    return f"\033[91m{s}\033[0m"


def _bold(s: str) -> str:
    return f"\033[1m{s}\033[0m"


def get_writer_summary() -> str:
    """Get writer summary from telemetry."""
    events = _load_events(_WRITER_LOG)
    if not events:
        return "  No writer events recorded"

    active = [e for e in events if e.get("event") == "contract_active"]
    skipped = [e for e in events if e.get("event") == "contract_skip"]
    not_task = [e for e in skipped if e.get("reason") == "not_a_task_start"]

    total = len(events)
    active_count = len(active)
    skip_count = len(skipped)
    not_task_count = len(not_task)

    # Task class breakdown
    task_classes: dict[str, int] = {}
    for e in active:
        tc = e.get("task_class", "unknown")
        task_classes[tc] = task_classes.get(tc, 0) + 1

    # Recency
    if events:
        latest = max(e.get("timestamp", 0) for e in events)
        age = _age_hours(latest)
        age_str = f"{age:.1f}h ago" if age < 24 else f"{age / 24:.1f}d ago"
        recency = f"Last: {age_str}"
    else:
        recency = "No recent activity"

    lines = [
        f"  Contract Writer: {_bold(str(active_count))} contracts, "
        f"{_yellow(str(skip_count))} skips "
        f"({_red(str(not_task_count))} not-task-start)",
        f"    {recency}",
    ]

    if task_classes:
        tc_lines = "    Task classes: " + ", ".join(
            f"{tc}={n}" for tc, n in sorted(task_classes.items())
        )
        lines.append(tc_lines)

    return "\n".join(lines)


def get_stop_breakdown() -> str:
    """Get Stop gate breakdown from telemetry."""
    events = _load_events(_STOP_LOG)
    if not events:
        return "  No Stop events recorded"

    allowed = [e for e in events if e.get("decision") == "allow"]
    blocked = [e for e in events if e.get("decision") == "block"]
    silent = [e for e in events if e.get("event") == "silent"]

    # Silence reasons
    silence_reasons: dict[str, int] = {}
    for e in silent:
        reason = e.get("reason", "unknown")
        silence_reasons[reason] = silence_reasons.get(reason, 0) + 1

    # Gate breakdown
    gates: dict[str, dict] = {}
    for e in events:
        gate = e.get("gate", "unknown")
        if gate not in gates:
            gates[gate] = {"allow": 0, "block": 0, "silent": 0}
        decision = e.get("decision") or ("silent" if e.get("event") == "silent" else "allow")
        if decision in gates[gate]:
            gates[gate][decision] += 1

    total = len(events)
    lines = [
        f"  Contract Stop: {_bold(str(len(allowed)))} allow, "
        f"{_red(str(len(blocked)))} block, "
        f"{_yellow(str(len(silent)))} silent "
        f"(of {total} total)",
    ]

    # Show top silence reasons
    if silence_reasons:
        top_reasons = sorted(silence_reasons.items(), key=lambda x: -x[1])[:3]
        reasons_str = ", ".join(f"{r}={n}" for r, n in top_reasons)
        lines.append(f"    Silence reasons: {reasons_str}")

    # Show notable gates
    notable = [(g, d) for g, d in gates.items() if d["block"] > 0 or d["silent"] > 0]
    if notable:
        gate_str = ", ".join(
            f"{g}(B={d['block']},S={d['silent']})" for g, d in sorted(notable)
        )
        lines.append(f"    Notable gates: {gate_str}")

    return "\n".join(lines)


def get_anomaly_status() -> str:
    """Check for anomalies and return status line.

    Delegates to the authoritative contract_health module for all anomaly
    detection. The old ad-hoc skip-rate and uncertain-silence logic has been
    replaced by the tuned category-aware model in contract_health.py.
    """
    from contract_health import get_health_summary

    try:
        summary = get_health_summary(hooks_dir=HOOKS_DIR)
    except Exception:
        return "  " + _yellow("Health check unavailable")

    if summary.healthy:
        return "  " + _green("No anomalies detected")

    # Surface each alert from the authoritative health summary
    alert_parts = []
    for alert in summary.alerts:
        if "writer underperformance" in alert:
            alert_parts.append(_red(alert))
        elif "enforcement outcomes missing" in alert:
            alert_parts.append(_red(alert))
        elif "lookup failures" in alert or "import failures" in alert:
            alert_parts.append(_red(alert))
        elif "schema drift" in alert:
            alert_parts.append(_red(alert))
        elif "trivial analysis" in alert:
            alert_parts.append(_red(alert))
        else:
            alert_parts.append(_red(alert))

    return "  Anomalies: " + ", ".join(alert_parts)


def build_dashboard() -> str:
    """Build the full dashboard output."""
    lines = [
        "",
        "═" * 50,
        _bold(" Contract System Health "),
        "─" * 50,
        get_writer_summary(),
        get_stop_breakdown(),
        get_anomaly_status(),
        "─" * 50,
    ]

    # Call the telemetry script for more detailed output
    if TELEMETRY_SCRIPT.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(TELEMETRY_SCRIPT), "health"],
                capture_output=True,
                text=True,
                cwd=str(TOOLS_DIR),
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                lines.append(f"  Health: {result.stdout.strip()}")
        except (subprocess.TimeoutExpired, OSError):
            pass

    lines.append("═" * 50)
    return "\n".join(lines)


def main() -> None:
    """Main entry point - outputs dashboard to stdout."""
    output = build_dashboard()
    print(output)


if __name__ == "__main__":
    main()