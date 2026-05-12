#!/usr/bin/env python3
"""
Contract System Telemetry Queries — pure Python, no jq dependency.

Usage:
    python contract-telemetry-queries.py [command]

Commands:
    dashboard    — Full system health summary
    writer_summary    — Contract writer stats
    stop_breakdown     — Stop gate stats by event type
    writer_task_classes — Contracts by task classification
    recent_activity    — Last 10 events per system
    anomalies          — Flag anomalous patterns
    correlation        — Cross-system correlation
    health             — Quick health check
    help               — Show this message

Can also be sourced as a shell script that calls through to Python:
    source contract-telemetry-queries.sh  # wraps python call
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Paths ─────────────────────────────────────────────────────────────────────────
# Use the same convention as Stop.py: resolve from this script's location
# (not Path.home()) so it works when Claude runs hooks from P:/, not ~/.

_TOOLS_DIR = Path(__file__).resolve().parent  # P:/.claude/hooks/tools/
_HOOKS_DIR = _TOOLS_DIR.parent               # P:/.claude/hooks/
_WRITER_LOG = _HOOKS_DIR / "logs" / "diagnostics" / "task_contract_writer_telemetry.jsonl"
_STOP_LOG  = _HOOKS_DIR / "logs" / "diagnostics" / "task_contract_telemetry.jsonl"


# ── Readers ────────────────────────────────────────────────────────────────────────

def _load_log(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return events


def _age_hours(ts: float) -> float:
    return (datetime.now(timezone.utc).timestamp() - ts) / 3600


def _fmt_age(ts: float) -> str:
    h = _age_hours(ts)
    if h < 1:
        return f"{h * 60:.0f}m ago"
    if h < 24:
        return f"{h:.1f}h ago"
    return f"{h / 24:.1f}d ago"


# ── Formatters ───────────────────────────────────────────────────────────────

def _green(text: str) -> str:
    return f"\033[92m{text}\033[0m"


def _yellow(text: str) -> str:
    return f"\033[93m{text}\033[0m"


def _red(text: str) -> str:
    return f"\033[91m{text}\033[0m"


def _bold(text: str) -> str:
    return f"\033[1m{text}\033[0m"


def _section(title: str) -> None:
    print(f"\n{_bold('══ ' + title + ' ' + '═' * max(0, 60 - len(title)))}")


def _kv(key: str, value: Any) -> None:
    print(f"  {key:<30} {value}")


# ── Dashboard ────────────────────────────────────────────────────────────────

def dashboard() -> None:
    writer_events = _load_log(_WRITER_LOG)
    stop_events = _load_log(_STOP_LOG)

    print(_bold("\n╔══ CONTRACT SYSTEM HEALTH ══╗"))
    print(_bold("║  ") + " Pure Python · No jq needed  ".center(35) + _bold("║"))
    print(_bold("╚═════════════════════════════════╝"))

    # ── Volume ──
    _section("Volume")
    _kv("Writer events", len(writer_events))
    _kv("Stop events", len(stop_events))
    if writer_events:
        oldest_w = min(e["timestamp"] for e in writer_events)
        _kv("Writer oldest entry", _fmt_age(oldest_w))
    if stop_events:
        oldest_s = min(e["timestamp"] for e in stop_events)
        _kv("Stop oldest entry", _fmt_age(oldest_s))

    # ── Writer summary ──
    writer_summary()

    # ── Stop breakdown ──
    stop_breakdown()

    # ── Anomalies ──
    print()
    anomalies()


# ── Writer summary ───────────────────────────────────────────────────────────

def writer_summary() -> None:
    events = _load_log(_WRITER_LOG)
    _section("Contract Writer")

    if not events:
        _kv("Status", _green("No events — no contracts written yet"))
        return

    by_event: dict[str, int] = {}
    by_reason: dict[str, int] = {}
    by_class: dict[str, int] = {}

    for e in events:
        by_event[e.get("event", "?")] = by_event.get(e.get("event", "?"), 0) + 1
        if e.get("event") == "contract_skip":
            reason = e.get("reason", "unknown")
            by_reason[reason] = by_reason.get(reason, 0) + 1
        if "task_class" in e:
            tc = e.get("task_class", "?")
            by_class[tc] = by_class.get(tc, 0) + 1

    for k, v in sorted(by_event.items()):
        icon = "✓" if k == "contract_active" else "⚠" if k == "contract_skip" else "•"
        _kv(icon + " " + k, v)

    if by_reason:
        print(f"\n  {_yellow('Skip reasons:')}")
        for k, v in sorted(by_reason.items(), key=lambda x: -x[1]):
            _kv("  skip:" + k, v)

    if by_class:
        print(f"\n  {_yellow('Task classes:')}")
        for k, v in sorted(by_class.items(), key=lambda x: -x[1]):
            _kv("  " + k, v)


# ── Stop breakdown ────────────────────────────────────────────────────────────

def stop_breakdown() -> None:
    events = _load_log(_STOP_LOG)
    _section("Contract Stop Gate")

    if not events:
        _kv("Status", _green("No events — gate has not fired"))
        return

    by_event: dict[str, int] = {}
    by_reason: dict[str, int] = {}
    by_mode: dict[str, int] = {}

    for e in events:
        ev = e.get("event", "?")
        by_event[ev] = by_event.get(ev, 0) + 1
        if ev == "silent":
            reason = e.get("reason", "unknown")
            by_reason[reason] = by_reason.get(reason, 0) + 1
        if "turn_mode" in e:
            tm = e.get("turn_mode", "?")
            by_mode[tm] = by_mode.get(tm, 0) + 1

    for k, v in sorted(by_event.items(), key=lambda x: -x[1]):
        icon = _green("✓") if k == "auto_clear" else _red("✗") if k == "block" else _yellow("○") if k == "silent" else "•"
        _kv(f"{icon} {k}", v)

    if by_reason:
        print(f"\n  {_yellow('Silence reasons:')}")
        for k, v in sorted(by_reason.items(), key=lambda x: -x[1]):
            _kv("  " + k, v)

    if by_mode:
        print(f"\n  {_yellow('Turn modes:')}")
        for k, v in sorted(by_mode.items(), key=lambda x: -x[1]):
            _kv("  " + k, v)


# ── Task class breakdown ───────────────────────────────────────────────────────

def writer_task_classes() -> None:
    events = _load_log(_WRITER_LOG)
    _section("Task Classes (writer)")

    by_class: dict[str, int] = {}
    for e in events:
        if "task_class" in e:
            tc = e.get("task_class", "?")
            by_class[tc] = by_class.get(tc, 0) + 1

    if not by_class:
        print("  No task_class data found")
        return
    for k, v in sorted(by_class.items(), key=lambda x: -x[1]):
        _kv(k, v)


# ── Recent activity ───────────────────────────────────────────────────────────

def recent_activity(n: int = 10) -> None:
    writer_events = _load_log(_WRITER_LOG)
    stop_events = _load_log(_STOP_LOG)

    _section(f"Recent Activity (last {n} per system)")

    print(f"\n  {_bold('Contract Writer:')}")
    for e in writer_events[-n:]:
        ts = datetime.fromtimestamp(e["timestamp"], tz=timezone.utc).strftime("%H:%M")
        ev = e.get("event", "?")
        tc = e.get("task_class", "")
        print(f"    [{ts}] {ev}" + (f" ({tc})" if tc else ""))

    print(f"\n  {_bold('Stop Gate:')}")
    for e in stop_events[-n:]:
        ts = datetime.fromtimestamp(e["timestamp"], tz=timezone.utc).strftime("%H:%M")
        ev = e.get("event", "?")
        reason = e.get("reason", "")
        print(f"    [{ts}] {ev}" + (f" — {reason}" if reason else ""))


# ── Anomalies ─────────────────────────────────────────────────────────────────

def anomalies() -> None:
    writer_events = _load_log(_WRITER_LOG)
    stop_events = _load_log(_STOP_LOG)

    _section("Anomalies")

    alerts: list[tuple[str, str]] = []

    # Writer checks
    if writer_events:
        skips = [e for e in writer_events if e.get("event") == "contract_skip"]
        skip_reasons: dict[str, int] = {}
        for e in skips:
            r = e.get("reason", "unknown")
            skip_reasons[r] = skip_reasons.get(r, 0) + 1

        if skip_reasons.get("not_a_task_start", 0) > 10:
            alerts.append((_red("HIGH"), f"Writer: {skip_reasons['not_a_task_start']} non-task-start skips"))
        if len(skips) > len(writer_events) * 0.5 and len(writer_events) > 5:
            alerts.append((_yellow("MED"), "Writer: >50% skip rate — contracts may be under-triggering"))
    else:
        alerts.append((_yellow("INFO"), "Writer: no events yet"))

    # Stop checks
    if stop_events:
        silents = [e for e in stop_events if e.get("event") == "silent"]
        blocks = [e for e in stop_events if e.get("event") == "block"]
        uncertain = [e for e in silents if e.get("reason") == "uncertain_non_completion"]
        cleared = [e for e in stop_events if e.get("event") == "auto_clear"]

        if len(uncertain) > 5:
            alerts.append((_yellow("MED"), f"Stop: {len(uncertain)} uncertain silences — applicability guard may be over-conservative"))
        if len(blocks) == 0 and len(writer_events) > 3:
            alerts.append((_yellow("MED"), "Stop: zero blocks — gate may not be catching incomplete completions"))
        if len(cleared) == 0 and len(blocks) > 0:
            alerts.append((_green("OK"), "Stop: blocks firing, no auto-clears yet"))
    else:
        alerts.append((_yellow("INFO"), "Stop: no events yet"))

    if not alerts:
        print(f"  {_green('No anomalies detected')}")
        return

    for icon, msg in alerts:
        print(f"  {icon} {msg}")


# ── Correlation ───────────────────────────────────────────────────────────────

def correlation() -> None:
    writer_events = _load_log(_WRITER_LOG)
    stop_events = _load_log(_STOP_LOG)
    _section("Cross-System Correlation")

    if not writer_events:
        print("  No writer events — cannot correlate")
        return

    by_terminal: dict[str, dict[str, int]] = {}
    for e in writer_events:
        tid = e.get("terminal_id", "?")
        by_terminal.setdefault(tid, {"active": 0, "skip": 0, "replace": 0})
        ev = e.get("event", "?")
        if "active" in ev:
            by_terminal[tid]["active"] += 1
        elif ev == "contract_skip":
            by_terminal[tid]["skip"] += 1
        elif ev == "contract_replace":
            by_terminal[tid]["replace"] += 1

    print(f"\n  {_bold('Terminal activity:')}")
    for tid, counts in sorted(by_terminal.items(), key=lambda x: -(x[1]["active"] + x[1]["replace"])):
        short_tid = tid[:12] + "…" if len(tid) > 12 else tid
        print(f"    {short_tid:<14} active={counts['active']} replace={counts['replace']} skip={counts['skip']}")

    # Cross-ref: terminals with writer activity vs stop activity
    writer_tids = {e.get("terminal_id", "?") for e in writer_events}
    stop_tids = {e.get("terminal_id", "?") for e in stop_events}
    both = writer_tids & stop_tids
    print(f"\n  Terminals in both logs: {len(both)}")
    print(f"  Terminals in writer only: {len(writer_tids - stop_tids)}")
    print(f"  Terminals in stop only:  {len(stop_tids - writer_tids)}")


# ── Health ──────────────────────────────────────────────────────────────────────

def health() -> None:
    writer_events = _load_log(_WRITER_LOG)
    stop_events = _load_log(_STOP_LOG)

    # Quick health check: is system active?
    if not writer_events and not stop_events:
        print(_yellow("No telemetry events found — system has not been exercised yet"))
        return

    blocks = [e for e in stop_events if e.get("event") == "block"]
    clears = [e for e in stop_events if e.get("event") == "auto_clear"]
    silents = [e for e in stop_events if e.get("event") == "silent"]
    skips = [e for e in writer_events if e.get("event") == "contract_skip"]
    actives = [e for e in writer_events if e.get("event") == "contract_active"]

    if clears:
        print(_green(f"✅ Healthy: {len(clears)} auto-clear(s), {len(silents)} appropriate silences"))
    elif blocks:
        print(_yellow(f"⚠  Active: {len(blocks)} block(s), {len(silents)} silences"))
    elif actives:
        print(_yellow(f"⚠  Active: {len(actives)} contract(s) written, no blocks yet"))
    else:
        print(_yellow(f"⚠  Sparse: {len(skips)} skips, no completions yet"))


# ── CLI ───────────────────────────────────────────────────────────────────────

_COMMANDS: dict[str, Any] = {
    "dashboard": dashboard,
    "writer_summary": writer_summary,
    "writer_task_classes": writer_task_classes,
    "stop_breakdown": stop_breakdown,
    "recent_activity": recent_activity,
    "anomalies": anomalies,
    "correlation": correlation,
    "health": health,
    "help": lambda: print(__doc__),
}

_SHELL_WRAPPER = '''#!/usr/bin/env bash
# Contract telemetry shell wrapper — sources Python script via python3
# Usage: source contract-telemetry-queries.sh && dashboard
#   or:  bash /path/to/contract-telemetry-queries.sh [command]

SCRIPT_DIR="${BASH_SOURCE[0]%/*}"
[[ "$SCRIPT_DIR" == "${BASH_SOURCE[0]}" ]] && SCRIPT_DIR="."
CMD="${1:-dashboard}"
exec python3 "$SCRIPT_DIR/contract-telemetry-queries.py" "$CMD"
'''


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "dashboard"

    if cmd == "shell-wrapper":
        print(_SHELL_WRAPPER)
        return

    fn = _COMMANDS.get(cmd)
    if fn is None:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print("Available: " + ", ".join(_COMMANDS))
        sys.exit(1)

    try:
        fn()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
