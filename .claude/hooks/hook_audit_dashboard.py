#!/usr/bin/env python3
"""
Hook Audit Dashboard - Unified hook behavioral compliance report.

Usage:
    python hook_audit_dashboard.py [subcommand] [--days N] [--terminal] [--all] [--turn TURN_ID]

Subcommands:
    (none)      Full dashboard (all metrics)
    blocks      Hook blocking events
    assumptions Assumption audit compliance
    attribution Error attribution compliance
    speculation Speculation gate compliance
    reasoning   Reasoning profile and THINK auto-routing metrics
    principles  Principle-based behavior monitoring (context_reuse, etc.)
    frameguard  FrameGuard systemic frame compliance (from DB)
    stats       Diagnostics DB hook stats and turn-scoped lookup
    health      Hook system health
    escalation  Escalation recommendations
    replay      Enforcement replay quality metrics
    loop-fix    Monitor hook loop patch signals (false positives, skips, causal slips, repair bypass)

Terminal Filtering (v2.1):
    --terminal  Filter to current terminal only
    --all       Show per-terminal breakdown
    --turn      Filter stats to a specific turn ID
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from collections import Counter
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

from cc_diagnostic_logger import query_hook_invocations


def _resolve_telemetry_path(hooks_dir: Path) -> Path:
    """Resolve telemetry path via shared state_paths contract (state lives outside code tree)."""
    try:
        sys.path.insert(0, str(hooks_dir / "__lib"))
        from state_paths import SHARED_DIR  # type: ignore[import-not-found]
        return SHARED_DIR / "stop_gate_telemetry.jsonl"
    except Exception:
        return hooks_dir / ".state" / "stop_gate_telemetry.jsonl"


def get_current_terminal_id() -> str:
    """Get current terminal ID for filtering."""
    try:
        from __lib.terminal_detection import detect_terminal_id

        return detect_terminal_id()
    except ImportError:
        return None


def run_script(name: str, args: list[str] = None) -> bool:
    """Run an analysis script and return success status."""
    script = HOOKS_DIR / name
    if not script.exists():
        print(f"  [!] Script not found: {name}")
        return False

    import shutil

    # Use pythonw.exe on Windows to prevent console flash
    python_exe = shutil.which("pythonw.exe") or sys.executable
    cmd = [python_exe, str(script)] + (args or [])
    try:
        result = subprocess.run(cmd, capture_output=False, timeout=30)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"  [!] Script timed out: {name}")
        return False
    except Exception as e:
        print(f"  [!] Error running {name}: {e}")
        return False


def dashboard(days: int, terminal_filter: str = None, show_all: bool = False):
    """Full dashboard - all metrics."""
    print("=" * 60)
    print("HOOK BEHAVIORAL COMPLIANCE DASHBOARD")
    filter_label = ""
    if terminal_filter:
        filter_label = f" (terminal: {terminal_filter[:20]}...)"
    elif show_all:
        filter_label = " (per-terminal)"
    print(f"Period: Last {days} days{filter_label}")
    print("=" * 60)

    print("\n" + "-" * 60)
    print("HOOK DB STATS")
    print("-" * 60)
    stats(days, terminal_filter, show_all, show_header=False)

    print("\n" + "-" * 60)
    print("ERROR ATTRIBUTION")
    print("-" * 60)
    run_script("analyze_error_attribution.py", ["--days", str(days)])

    print("\n" + "-" * 60)
    print("ASSUMPTION AUDIT")
    print("-" * 60)
    # Pass terminal args to assumption audit
    audit_args = [str(days)]
    if terminal_filter:
        audit_args.append("--terminal")
    elif show_all:
        audit_args.append("--all")
    run_script("analyze_assumption_audit.py", audit_args)

    print("\n" + "-" * 60)
    print("SPECULATION GATE")
    print("-" * 60)
    run_script("analyze_speculation.py", ["--days", str(days)])

    print("\n" + "-" * 60)
    print("REASONING PROFILES")
    print("-" * 60)
    reasoning(days, terminal_filter, show_all)

    print("\n" + "-" * 60)
    print("PRINCIPLES (Context Reuse, etc.)")
    print("-" * 60)
    principles(days, terminal_filter, show_all)

    print("\n" + "-" * 60)
    print("STYLE FRICTION")
    print("-" * 60)
    friction(days, terminal_filter, show_all)

    print("\n" + "-" * 60)
    print("BLOCKING EVENTS")
    print("-" * 60)
    run_script("analyze_blocks.py")

    print("\n" + "-" * 60)
    print("ENFORCEMENT REPLAY")
    print("-" * 60)
    replay(days, terminal_filter, show_all)

    print("\n" + "=" * 60)
    print("END OF DASHBOARD")
    print("=" * 60)


def blocks(days: int, terminal_filter: str = None, show_all: bool = False):
    """Hook blocking events analysis."""
    run_script("analyze_blocks.py")


def stats(
    days: int,
    terminal_filter: str = None,
    show_all: bool = False,
    turn_id: str | None = None,
    limit: int = 20,
    show_header: bool = True,
):
    """SQLite hook invocation stats and turn-scoped query helper."""
    if show_header:
        print("Hook Database Stats")
        print("-" * 40)

    db_path = HOOKS_DIR / "logs" / "diagnostics" / "diagnostics.db"
    filter_label = ""
    if turn_id:
        filter_label = f"turn: {turn_id}"
    elif terminal_filter:
        filter_label = f"terminal: {terminal_filter[:20]}..."
    elif show_all:
        filter_label = "per-terminal"

    print(f"  Database: {db_path}")
    if filter_label:
        print(f"  Scope: {filter_label}")

    rows = query_hook_invocations(
        days=days,
        turn_id=turn_id,
        terminal_id=terminal_filter,
        limit=max(limit, 1),
    )

    if not rows:
        print(f"  No hook invocations found in the last {days} days.")
        print("  Reminder: run /hook-obs stats --turn <turn-id> for a turn-scoped lookup.")
        return

    total = len(rows)
    injects = sum(1 for row in rows if row.get("action") == "inject")
    blocks = sum(1 for row in rows if row.get("action") == "block")
    warns = sum(1 for row in rows if row.get("action") == "warn")
    passes = sum(1 for row in rows if row.get("action") == "pass")
    unique_turns = len({row.get("turn_id") for row in rows if row.get("turn_id")})
    hook_counts = Counter(row.get("hook_name", "unknown") for row in rows)
    terminal_counts = Counter(row.get("terminal_id", "unknown") for row in rows)

    print(f"  Events: {total}")
    print(f"  Injects: {injects} | Blocks: {blocks} | Warns: {warns} | Passes: {passes}")
    print(f"  Distinct turns: {unique_turns}")

    print("\n  Top Hooks:")
    for hook_name, count in hook_counts.most_common(5):
        print(f"    {hook_name}: {count}")

    if show_all and not turn_id:
        print("\n  By Terminal:")
        for terminal, count in terminal_counts.most_common(5):
            label = terminal if terminal and terminal != "unknown" else "unknown"
            print(f"    {label}: {count}")

    print("\n  Recent Events:")
    for index, row in enumerate(rows[: min(limit, 10)], 1):
        timestamp = str(row.get("timestamp", ""))[:19]
        hook_name = row.get("hook_name", "unknown")
        action = row.get("action", "unknown")
        reason = row.get("reason", "") or ""
        scoped_turn = row.get("turn_id") or "no-turn"
        print(f"    {index}. [{timestamp}] {hook_name} {action} ({scoped_turn})")
        if reason:
            print(f"       {reason[:120]}")

    print("\n  Query Tip:")
    print("    /hook-obs stats --turn <turn-id>")


def ups_stats(days: int, terminal_filter: str = None, show_all: bool = False):
    """UserPromptSubmit hook fires from ups_execution_trace.jsonl."""
    print("UserPromptSubmit Hook Fires (UPS Trace)")
    print("-" * 40)

    trace_path = HOOKS_DIR / "logs" / "diagnostics" / "ups_execution_trace.jsonl"
    if not trace_path.exists():
        print("  No UPS trace found.")
        return

    import json
    from collections import Counter
    from datetime import datetime, timedelta

    cutoff = datetime.now() - timedelta(days=days)
    hook_counts: Counter = Counter()
    session_counts: Counter = Counter()
    recent_entries: list[dict] = []
    total_fires = 0

    try:
        for line in trace_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts_str = entry.get("ts", "")
            if not ts_str:
                continue
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if ts.tzinfo is not None:
                    ts = ts.astimezone().replace(tzinfo=None)
            except ValueError:
                continue
            if ts < cutoff:
                continue

            # Apply terminal filter if present
            entry_terminal = entry.get("terminal_id", "")
            if terminal_filter and entry_terminal != terminal_filter:
                continue

            hook_name = entry.get("hook_name", "unknown")
            session_id = entry.get("session_id", "unknown")
            result = entry.get("result", {})
            is_empty = result.get("is_empty", True) if result else True

            # Count non-empty injections
            if not is_empty:
                hook_counts[hook_name] += 1
                total_fires += 1
            session_counts[session_id] += 1
            recent_entries.append(entry)
    except Exception as e:
        print(f"  Error reading trace: {e}")
        return

    print(f"  Trace: {trace_path}")
    print(f"  Period: Last {days} days")
    if terminal_filter:
        print(f"  Terminal: {terminal_filter[:20]}...")
    print(f"  Total non-empty injections: {total_fires}")
    print(f"  Unique sessions: {len(session_counts)}")

    if not hook_counts:
        print("  No non-empty hook fires in this period.")
        return

    print("\n  Top Hooks (by injection count):")
    for hook, count in hook_counts.most_common(10):
        print(f"    {hook}: {count}")

    if show_all:
        print("\n  By Session:")
        for session, count in session_counts.most_common(10):
            print(f"    {session[:20]}...: {count}")

    # Recent non-empty fires
    recent_entries.sort(key=lambda e: e.get("ts", ""), reverse=True)
    non_empty = [e for e in recent_entries if not e.get("result", {}).get("is_empty", True)]
    if non_empty:
        print("\n  Most Recent Non-Empty Fires:")
        for i, entry in enumerate(non_empty[:5], 1):
            ts = entry.get("ts", "")[:19]
            hook = entry.get("hook_name", "unknown")
            tokens = entry.get("result", {}).get("tokens_added", 0)
            print(f"    {i}. [{ts}] {hook} ({tokens} tokens)")


def assumptions(days: int, terminal_filter: str = None, show_all: bool = False):
    """Assumption audit compliance."""
    # Use analyze_assumption_audit.py which supports terminal filtering
    args = [str(days)]
    if terminal_filter:
        args.append("--terminal")
    elif show_all:
        args.append("--all")
    run_script("analyze_assumption_audit.py", args)


def attribution(days: int, terminal_filter: str = None, show_all: bool = False):
    """Error attribution compliance."""
    run_script("analyze_error_attribution.py", ["--days", str(days)])


def speculation(days: int, terminal_filter: str = None, show_all: bool = False):
    """Speculation gate compliance."""
    args = ["--days", str(days)]
    run_script("analyze_speculation.py", args)


def reasoning(days: int, terminal_filter: str = None, show_all: bool = False):
    """Reasoning profile auto-routing metrics."""
    run_script("analyze_reasoning_profiles.py", ["--days", str(days)])


def principles(days: int, terminal_filter: str = None, show_all: bool = False):
    """Principle-based behavior monitoring - context_reuse, grounded_changes, etc."""
    print("Principle-Based Behavior Monitoring")
    print("-" * 40)

    log_file = Path("P:/.claude/logs/principle-events.jsonl")
    if not log_file.exists():
        print("  principle-events.jsonl not found (feature removed).")
        return

    import json
    from collections import defaultdict
    from datetime import datetime, timedelta

    cutoff = datetime.now() - timedelta(days=days)

    events = []
    principles_count = defaultdict(int)
    event_types_count = defaultdict(int)
    sessions = set()

    for line in log_file.read_text().splitlines():
        try:
            entry = json.loads(line)
            ts = datetime.fromisoformat(entry.get("ts", "").replace("Z", "+00:00"))
            if ts.tzinfo is not None:
                ts = ts.astimezone().replace(tzinfo=None)
            if ts > cutoff:
                events.append(entry)
                principle = entry.get("principle", "unknown")
                event_type = entry.get("event_type", "unknown")
                principles_count[principle] += 1
                event_types_count[event_type] += 1
                sessions.add(entry.get("session_id", "unknown"))
        except (json.JSONDecodeError, ValueError, KeyError):
            pass

    if not events:
        print(f"  No principle events in last {days} days.")
        return

    # Sort by timestamp (newest first)
    events.sort(key=lambda e: e.get("ts", ""), reverse=True)

    print(f"\n  Total violations: {len(events)}")
    print(f"  Unique sessions: {len(sessions)}")
    print(f"  Time period: Last {days} days")

    # Breakdown by principle
    print("\n  By Principle:")
    for principle, count in sorted(principles_count.items(), key=lambda x: -x[1]):
        print(f"    {principle}: {count}")

    # Breakdown by event type
    print("\n  By Event Type:")
    for event_type, count in sorted(event_types_count.items(), key=lambda x: -x[1]):
        print(f"    {event_type}: {count}")

    # Recent violations
    print("\n  Most Recent Violations (last 5):")
    for i, event in enumerate(events[:5], 1):
        ts = event.get("ts", "")[:19]  # Truncate to readable format
        principle = event.get("principle", "unknown")
        preview = event.get("assistant_preview", "")[:60]
        print(f"    {i}. [{ts}] {principle}")
        print(f'       "{preview}"')

    # Trend analysis (daily)
    print("\n  Daily Trend:")
    daily_counts = defaultdict(int)
    for event in events:
        ts = event.get("ts", "")[:10]  # Extract date
        daily_counts[ts] += 1

    for date in sorted(daily_counts.keys())[-7:]:  # Last 7 days
        print(f"    {date}: {daily_counts[date]} violations")

    # Context reuse specific analysis
    context_reuse_count = principles_count.get("context_reuse", 0)
    if context_reuse_count > 0:
        print("\n  Context Reuse Analysis:")
        print(f"    Total context_reuse violations: {context_reuse_count}")

        # Calculate daily average
        if daily_counts:
            avg_daily = sum(daily_counts.values()) / len(daily_counts)
            print(f"    Daily average: {avg_daily:.1f} violations/day")

        # Check if improving (compare recent vs older)
        if len(events) > 10:
            recent_half = events[: len(events) // 2]
            older_half = events[len(events) // 2 :]

            recent_context = sum(1 for e in recent_half if e.get("principle") == "context_reuse")
            older_context = sum(1 for e in older_half if e.get("principle") == "context_reuse")

            if recent_context < older_context:
                improvement = (older_context - recent_context) / older_context * 100
                print(f"    Trend: IMPROVING ({improvement:.0f}% reduction)")
            elif recent_context > older_context:
                regression = (recent_context - older_context) / older_context * 100
                print(f"    Trend: REGRESSING ({regression:.0f}% increase)")
            else:
                print("    Trend: STABLE")

        print("\n  Related:")
        print("    Monitor: Context summary injection hook (context_summary.py)")
        print(
            f"    Status: {'Active' if (HOOKS_DIR / 'UserPromptSubmit_modules' / 'context_summary.py').exists() else 'Not installed'}"
        )


def friction(days: int, terminal_filter: str = None, show_all: bool = False):
    """Style friction analysis - output-style tuning feedback."""
    print("Style Friction Analysis")
    print("-" * 40)

    log_file = Path("P:/.claude/logs/style_friction.jsonl")
    if not log_file.exists():
        print("  No friction events logged yet.")
        print("  Friction detector: STYLE_FRICTION_DETECTOR_ENABLED in settings.json")
        return

    import json
    from collections import defaultdict
    from datetime import datetime, timedelta

    cutoff = datetime.now() - timedelta(days=days)

    events = []
    for line in log_file.read_text().splitlines():
        try:
            entry = json.loads(line)
            ts = datetime.fromisoformat(entry.get("timestamp", "2000-01-01"))
            if ts > cutoff:
                events.append(entry)
        except (json.JSONDecodeError, ValueError):
            pass

    if not events:
        print(f"  No friction events in last {days} days.")
        return

    # Aggregate by type
    by_type = defaultdict(list)
    for e in events:
        by_type[e.get("friction_type", "unknown")].append(e)

    print(f"\n  Total friction events: {len(events)}")
    print("\n  Breakdown by type:")

    tuning_recommendations = []
    for ftype, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
        print(f"\n    {ftype}: {len(items)}")
        if items:
            rec = items[0].get("recommendation", "unknown")
            print(f"      Recommendation: {rec}")
            tuning_recommendations.append((ftype, len(items), rec))

    # Tuning advice
    if tuning_recommendations:
        print("\n  Tuning Advice:")
        total = len(events)
        for ftype, count, rec in tuning_recommendations:
            pct = count / total * 100
            if pct > 30:
                print(f"    ⚠️ {ftype} ({pct:.0f}%): Consider adjusting output-style")
                print(f"       → {rec}")
            elif pct > 10:
                print(f"    📊 {ftype} ({pct:.0f}%): Monitor")


def health(days: int, terminal_filter: str = None, show_all: bool = False):
    """Hook system health."""
    script = HOOKS_DIR / "scripts" / "hook_health_check.py"
    if script.exists():
        run_script("hook_health_check.py")
    else:
        # Fallback: basic health check
        print("Hook Health Check")
        print("-" * 40)

        # Check key log files exist
        logs = [
            ("Error Attribution", Path("P:/.claude/logs/error_attribution.jsonl")),
            ("Skill Enforcement (v4.0)", HOOKS_DIR / "logs/skill_first_enforcement.jsonl"),
            ("Assumption Audit", HOOKS_DIR / "logs/assumption_audit_v2.jsonl"),
            ("Blocks Log", HOOKS_DIR / "logs/constructional_blocks.jsonl"),
            ("Parallel Execution", HOOKS_DIR / "logs/parallel_execution.jsonl"),
        ]

        for name, path in logs:
            if path.exists():
                lines = len(path.read_text().splitlines())
                print(f"  ✓ {name}: {lines} entries")
            else:
                print(f"  ✗ {name}: not found")

        # Parallel execution health
        print("\n  Parallel Execution:")
        try:
            from hook_tracker import get_parallel_health

            ph = get_parallel_health()
            print(f"    Errors: {ph['error_count']}")
            print(f"    Auto-disables: {ph['auto_disable_count']}")
            if ph["auto_disable_count"] > 0:
                print("    ⚠ PARALLEL HAS BEEN AUTO-DISABLED")
        except ImportError:
            print("    (hook_tracker not available)")

        # Check state files
        state_dir = HOOKS_DIR / "state"
        if state_dir.exists():
            state_files = list(state_dir.glob("*.json"))
            print(f"\n  State files: {len(state_files)}")
            for sf in state_files[:5]:
                print(f"    - {sf.name}")
            if len(state_files) > 5:
                print(f"    ... and {len(state_files) - 5} more")

    # Hook Health Check Results (ENHANCED - show ALL failures, not just new)
    print("\n  Hook Health Check:")
    print("  " + "-" * 30)
    health_file = HOOKS_DIR / "logs" / "diagnostics" / "hook_health.json"

    if health_file.exists():
        try:
            health_data = json.loads(health_file.read_text())

            if health_data.get("status") == "fail":
                failures = health_data.get("failures", [])
                unchanged_count = health_data.get("unchanged_failure_count", 0)

                print("    ⚠️  Status: FAILING")
                print(f"    Total failing hooks: {len(failures)}")

                if failures:
                    print("\n    Failing hooks:")
                    for i, failure in enumerate(failures[:5], 1):
                        print(f"      {i}. {failure}")
                    if len(failures) > 5:
                        print(f"      ... and {len(failures) - 5} more")

                if unchanged_count > 0:
                    print(
                        f"\n    ⚠️  {unchanged_count} persistent failure(s) (unchanged from previous check)"
                    )

                print("\n    Next steps:")
                print(f"      Run: python {HOOKS_DIR / 'hook_diagnostics.py'}")
                print("      Or:  python hook_audit_dashboard.py health")
            else:
                print("    ✓ Status: PASS")
                print("    All hooks healthy")
        except Exception as e:
            print(f"    (Unable to read health report: {e})")
    else:
        print("    (No health check data available)")
        print(f"      Run: python {HOOKS_DIR / 'hook_health_check.py'}")

    # Router-level validator runtime health from hook decision logs
    print("\n  Validator Runtime Errors:")
    print("  " + "-" * 36)
    summary = summarize_router_runtime_errors(days)
    if summary["total"] == 0:
        print(f"    ✓ No HOOK_RUNTIME_ERROR/HOOK_NON_JSON_OUTPUT events in last {days} days")
    else:
        print(f"    Total: {summary['total']} events in last {days} days")
        print(f"    HOOK_RUNTIME_ERROR: {summary['runtime_error']}")
        print(f"    HOOK_NON_JSON_OUTPUT: {summary['non_json_output']}")
        if summary["by_hook"]:
            print("    Top hooks:")
            for hook_name, count in summary["by_hook"][:5]:
                print(f"      - {hook_name}: {count}")

    # UserPromptSubmit Module Errors (NEW)
    print("\n  UserPromptSubmit Module Errors:")
    print("  " + "-" * 40)
    ups_module_summary = summarize_ups_module_errors(days)
    if ups_module_summary["total"] == 0:
        print(f"    ✓ No UserPromptSubmit module failures in last {days} days")
    else:
        print(f"    Total: {ups_module_summary['total']} module failures")
        if ups_module_summary["by_hook"]:
            print("    Failed modules:")
            for hook_name, count in ups_module_summary["by_hook"][:5]:
                print(f"      - {hook_name}: {count}")
        if ups_module_summary["recent_error"]:
            recent = ups_module_summary["recent_error"]
            print("\n    Most recent error:")
            print(f"      Hook: {recent.get('hook')}")
            print(f"      Time: {recent.get('ts')}")
            print(f"      Exception: {recent.get('exception')[:100]}...")


def replay(days: int, terminal_filter: str = None, show_all: bool = False):
    """Replay enforcement metrics (before/after ladder quality)."""
    args = ["--days", str(days)]
    if terminal_filter:
        args.append("--terminal")
    elif show_all:
        args.append("--all")
    run_script("analyze_enforcement_replay.py", args)


def loop_fix(days: int, terminal_filter: str = None, show_all: bool = False):
    """Monitor hook loop patch signals from stop_gate_telemetry.jsonl.

    HIGH PRIORITY signals:
      1. New false positives in markdown-heavy explanations (warn_issued on allow)
      2. Unintended blocks during legitimate hook analysis (block_triggered)
      3. Skip rates for patched gates (repair_bypass in epistemic)

    LOW PRIORITY signals:
      4. Fresh causal system claims slipping through (has_causal_issues=false but
         decision=block means causal logic caught something not in telemetry)
      5. Epistemic repair bypass being abused (repair_bypass=true count)
    """
    print("=" * 60)
    print("HOOK LOOP FIX TELEMETRY MONITOR")
    print("=" * 60)
    print(f"Period: Last {days} days")
    print()

    telemetry_path = _resolve_telemetry_path(HOOKS_DIR)
    epistemic_path = HOOKS_DIR / "logs" / "diagnostics" / "epistemic_telemetry.jsonl"
    unverified_path = HOOKS_DIR / "logs" / "diagnostics" / "unverified_stance_decisions.jsonl"

    # --- Section 1: Gate skip/decision rates from stop_gate_telemetry ---
    print("HIGH PRIORITY #3: Gate Decision Rates (stop_gate_telemetry)")
    print("-" * 60)

    gate_stats: dict[str, dict] = {}
    cutoff_ts = (datetime.now() - timedelta(days=days)).timestamp()

    for log_path in [telemetry_path]:
        if not log_path.exists():
            continue
        try:
            with open(log_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    ts = entry.get("timestamp", 0)
                    if ts < cutoff_ts:
                        continue
                    gate = entry.get("gate_name", "unknown")
                    if gate not in gate_stats:
                        gate_stats[gate] = {"total": 0, "allow": 0, "warn": 0, "block": 0}
                    gate_stats[gate]["total"] += 1
                    decision = entry.get("decision", "allow")
                    if decision in gate_stats[gate]:
                        gate_stats[gate][decision] += 1
                    else:
                        gate_stats[gate]["allow"] += 1
                    # Extract extra for unverified_stance
                    extra = entry.get("extra", {}) or {}
                    gate_stats[gate].setdefault("warn_issued_count", 0)
                    gate_stats[gate].setdefault("block_triggered_count", 0)
                    if extra.get("warn_issued"):
                        gate_stats[gate]["warn_issued_count"] += 1
                    if extra.get("block_triggered"):
                        gate_stats[gate]["block_triggered_count"] += 1
        except Exception:
            pass
    if gate_stats:
        print(f"  Source: {telemetry_path}")
        print()
        print(f"  {'Gate':<28} {'Total':>6} {'Allow':>6} {'Warn':>6} {'Block':>6}  {'Warn%':>6}  {'Block%':>7}")
        print(f"  {'-'*28} {'-'*6} {'-'*6} {'-'*6} {'-'*6}  {'-'*6}  {'-'*7}")
        for gate, stats in sorted(gate_stats.items(), key=lambda x: -x[1]["total"]):
            total = stats["total"]
            allow = stats["allow"]
            warn = stats["warn"]
            block = stats["block"]
            warn_pct = warn / total * 100 if total else 0
            block_pct = block / total * 100 if total else 0
            print(
                f"  {gate:<28} {total:>6} {allow:>6} {warn:>6} {block:>6}  "
                f"{warn_pct:>5.1f}%  {block_pct:>6.1f}%"
            )
            if gate == "unverified_stance":
                warn_iss = stats.get("warn_issued_count", 0)
                blk_trig = stats.get("block_triggered_count", 0)
                if warn_iss or blk_trig:
                    print(
                        f"    └─ warns issued (FP signal): {warn_iss}  |  blocks triggered: {blk_trig}"
                    )
    else:
        print(f"  No gate telemetry entries in last {days} days.")
        print(f"  (File: {telemetry_path})")

    # --- Section 2: Epistemic repair bypass (LOW PRIORITY #5) ---
    print()
    print("LOW PRIORITY #5: Epistemic Repair Bypass (repair_bypass signal)")
    print("-" * 60)

    repair_bypass_count = 0
    epistemic_total = 0
    epistemic_blocks = 0
    epistemic_causal = 0
    epistemic_recent: list[dict] = []

    if epistemic_path.exists():
        try:
            with open(epistemic_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    ts = entry.get("timestamp", 0)
                    if ts < cutoff_ts:
                        continue
                    epistemic_total += 1
                    if entry.get("repair_bypass"):
                        repair_bypass_count += 1
                    if entry.get("decision") == "block":
                        epistemic_blocks += 1
                    if entry.get("has_causal_issues"):
                        epistemic_causal += 1
                    if len(epistemic_recent) < 5:
                        epistemic_recent.append(entry)
        except Exception as e:
            print(f"  Error reading epistemic telemetry: {e}")

    if epistemic_total > 0:
        print(f"  Source: {epistemic_path}")
        print(f"  Total validations: {epistemic_total}")
        print(f"  Blocks: {epistemic_blocks} ({epistemic_blocks/epistemic_total*100:.1f}%)")
        print(f"  Causal issues: {epistemic_causal}")
        print(f"  Repair bypasses: {repair_bypass_count}")
        if epistemic_recent and epistemic_recent[0].get("repair_bypass"):
            print(f"  ⚠️  Recent bypass detected — low PRIORITY but watch for abuse")
        if epistemic_recent:
            print(f"\n  Most recent epistemic entries:")
            for entry in epistemic_recent[:3]:
                ts = datetime.fromtimestamp(entry.get("timestamp", 0)).strftime("%m-%d %H:%M")
                decision = entry.get("decision", "?")
                bypass = " [BYPASS]" if entry.get("repair_bypass") else ""
                causal = " [CAUSAL]" if entry.get("has_causal_issues") else ""
                print(f"    [{ts}] {decision}{bypass}{causal}")
    else:
        print(f"  No epistemic telemetry entries in last {days} days.")
        print(f"  (File: {epistemic_path})")

    # --- Section 3: Unverified stance decisions ---
    print()
    print("HIGH PRIORITY #1-2: Unverified Stance (warn/block patterns)")
    print("-" * 60)

    stance_stats = {"total": 0, "pass": 0, "block": 0, "warn": 0, "system_claim": 0}
    stance_recent: list[dict] = []

    if unverified_path.exists():
        try:
            with open(unverified_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    ts = entry.get("timestamp", 0)
                    if ts < cutoff_ts:
                        continue
                    stance_stats["total"] += 1
                    outcome = entry.get("outcome", "pass")
                    stance_stats[outcome] = stance_stats.get(outcome, 0) + 1
                    claim_type = entry.get("claim_type", "")
                    if claim_type in ("system_claim", "sycophancy_inversion"):
                        stance_stats["system_claim"] += 1
                    if len(stance_recent) < 5:
                        stance_recent.append(entry)
        except Exception as e:
            print(f"  Error reading unverified stance decisions: {e}")

    if stance_stats["total"] > 0:
        print(f"  Source: {unverified_path}")
        print(f"  Total decisions: {stance_stats['total']}")
        print(f"  Pass: {stance_stats['pass']} | Block: {stance_stats['block']} | Warn: {stance_stats['warn']}")
        block_rate = stance_stats["block"] / stance_stats["total"] * 100
        print(f"  Block rate: {block_rate:.1f}%")
        if stance_stats["system_claim"]:
            print(f"  System-claim/sycophancy violations: {stance_stats['system_claim']}")
        if stance_recent:
            print(f"\n  Most recent decisions:")
            for entry in stance_recent[:3]:
                ts = datetime.fromtimestamp(entry.get("timestamp", 0)).strftime("%m-%d %H:%M")
                outcome = entry.get("outcome", "?")
                claim_type = entry.get("claim_type", "")
                claim_preview = entry.get("claim_text", "")[:50]
                print(f"    [{ts}] {outcome.upper()} [{claim_type}] {claim_preview}...")
    else:
        print(f"  No unverified stance decisions in last {days} days.")
        print(f"  (File: {unverified_path})")

    # --- Summary ---
    print()
    print("=" * 60)
    print("ACTIONABLE SIGNALS")
    print("=" * 60)

    signals = []
    # HIGH PRIORITY checks
    unv_gate = gate_stats.get("unverified_stance", {})
    warn_rate = unv_gate.get("warn", 0) / max(unv_gate.get("total", 1), 1) * 100
    if warn_rate > 20:
        signals.append(f"HIGH: Unverified stance warn rate {warn_rate:.0f}% — possible markdown FP")
    if unv_gate.get("block_triggered_count", 0) > 10:
        signals.append(
            f"HIGH: {unv_gate['block_triggered_count']} unverified_stance blocks "
            f"— check for unintended blocks on analysis turns"
        )
    # LOW PRIORITY checks
    if repair_bypass_count > epistemic_total * 0.1 and epistemic_total > 10:
        signals.append(
            f"LOW: {repair_bypass_count} epistemic repair bypasses ({repair_bypass_count/epistemic_total*100:.0f}%) "
            f"— watch for abuse"
        )
    causal_block = epistemic_causal / max(epistemic_blocks, 1) * 100
    if epistemic_blocks > 5 and causal_block < 30:
        signals.append(
            f"LOW: Only {causal_block:.0f}% of epistemic blocks are causal — "
            f"fresh causal claims may be slipping through"
        )

    if signals:
        for sig in signals:
            print(f"  • {sig}")
    else:
        print("  ✓ No actionable signals detected. Loop patch is healthy.")


def frameguard(days: int, terminal_filter: str = None, show_all: bool = False):
    """FrameGuard systemic frame compliance (from evidence.db)."""
    import sqlite3

    print("FrameGuard Systemic Frame Compliance")
    print("-" * 40)

    # Check database exists
    db_path = HOOKS_DIR / "session_data" / "evidence.db"
    if not db_path.exists():
        print(f"  Database not found: {db_path}")
        print("  FrameGuard may not be active yet.")
        return

    cutoff = datetime.now() - timedelta(days=days)

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Query frameguard table
        cursor.execute(
            """
            SELECT
                sessionid,
                terminalid,
                turn_id,
                created_at,
                needs_systemic_frame,
                trigger_reason,
                latent_questions_json,
                handled,
                handled_reason
            FROM frameguard
            WHERE datetime(created_at) > ?
            ORDER BY datetime(created_at) DESC
        """,
            (cutoff.isoformat(),),
        )

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            print(f"  No FrameGuard events in last {days} days.")
            return

        # Statistics
        total = len(rows)
        systemic = sum(1 for r in rows if r["needs_systemic_frame"])
        handled = sum(1 for r in rows if r["handled"])
        unhandled = sum(1 for r in rows if r["needs_systemic_frame"] and not r["handled"])

        print(f"\n  Total events: {total}")
        print(f"  Period: Last {days} days")
        print(f"  Systemic frames detected: {systemic} ({systemic / total * 100:.1f}% of all)")
        print(f"  Handled: {handled}")
        print(f"  Unhandled systemic: {unhandled}")

        # Breakdown by trigger reason
        print("\n  By Trigger Reason:")
        reasons = {}
        for r in rows:
            reason = r["trigger_reason"] or "unknown"
            reasons[reason] = reasons.get(reason, 0) + 1

        for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
            print(f"    {reason}: {count}")

        # Recent events
        print("\n  Most Recent Events (last 5):")
        for i, r in enumerate(rows[:5], 1):
            ts = r["created_at"][:19] if r["created_at"] else "unknown"
            systemic_flag = "SYSTEMIC" if r["needs_systemic_frame"] else "non-systemic"
            handled_flag = "OK" if r["handled"] else "MISSED"
            print(f"    {i}. [{ts}] {systemic_flag} {handled_flag}")
            print(f"       Turn: {r['turn_id'][:30]}...")
            print(f"       Reason: {r['trigger_reason'][:60]}...")

        # Daily trend
        print("\n  Daily Trend:")
        daily_counts = {}
        for r in rows:
            ts = r["created_at"][:10] if r["created_at"] else "unknown"
            daily_counts[ts] = daily_counts.get(ts, 0) + 1

        for date in sorted(daily_counts.keys())[-min(7, len(daily_counts)) :]:
            print(f"    {date}: {daily_counts[date]} events")

        # Compliance rate
        if systemic > 0:
            compliance_rate = (systemic - unhandled) / systemic * 100
            print(f"\n  Compliance Rate: {compliance_rate:.1f}%")
            print(f"    ({systemic - unhandled}/{systemic} systemic frames handled)")

    except sqlite3.Error as e:
        print(f"  Database error: {e}")
        print(f"  Try: python {HOOKS_DIR / 'evidence_store.py'} init_db")


def summarize_ups_module_errors(days: int) -> dict:
    """Summarize UserPromptSubmit module failures from ups_module_errors.jsonl."""
    error_log = HOOKS_DIR / "logs" / "diagnostics" / "ups_module_errors.jsonl"
    if not error_log.exists():
        return {
            "total": 0,
            "by_hook": [],
            "recent_error": None,
        }

    cutoff = datetime.now() - timedelta(days=days)
    total = 0
    by_hook = {}
    most_recent = None
    most_recent_ts = None

    for file_path in [error_log]:
        try:
            with open(file_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except Exception:
                        continue

                    ts = entry.get("timestamp", "") or entry.get("ts", "")
                    if not ts:
                        continue
                    try:
                        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                        if dt.tzinfo is not None:
                            dt = dt.astimezone().replace(tzinfo=None)
                        if dt < cutoff:
                            continue
                    except Exception:
                        continue

                    total += 1
                    hook_name = entry.get("hook", "unknown")
                    by_hook[hook_name] = by_hook.get(hook_name, 0) + 1

                    # Track most recent error
                    if most_recent is None or dt > most_recent_ts:
                        most_recent = entry
                        most_recent_ts = dt
        except Exception:
            continue

    by_hook_sorted = sorted(by_hook.items(), key=lambda x: -x[1])
    return {
        "total": total,
        "by_hook": by_hook_sorted,
        "recent_error": most_recent,
    }


def summarize_router_runtime_errors(days: int) -> dict:
    """Summarize router runtime/non-json validator issues from decision logs."""
    decisions_dir = HOOKS_DIR / "session_data"
    if not decisions_dir.exists():
        return {
            "total": 0,
            "runtime_error": 0,
            "non_json_output": 0,
            "by_hook": [],
        }

    cutoff = datetime.now() - timedelta(days=days)
    runtime_error = 0
    non_json_output = 0
    by_hook = {}

    for file_path in sorted(decisions_dir.glob("hook_decisions_*.jsonl")):
        try:
            with open(file_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except Exception:
                        continue

                    ts = entry.get("timestamp", "")
                    if not ts:
                        # Skip undated events for period-bounded metrics.
                        continue
                    try:
                        # Supports "...Z" format; compare in naive local wall-clock.
                        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                        if dt.tzinfo is not None:
                            dt = dt.astimezone().replace(tzinfo=None)
                        if dt < cutoff:
                            continue
                    except Exception:
                        # Skip malformed timestamps instead of inflating error counts.
                        continue

                    reason = str(entry.get("reason", ""))
                    hook_name = str(entry.get("hook_name", "unknown"))
                    matched = False
                    if "HOOK_RUNTIME_ERROR" in reason:
                        runtime_error += 1
                        matched = True
                    if "HOOK_NON_JSON_OUTPUT" in reason:
                        non_json_output += 1
                        matched = True
                    if matched:
                        by_hook[hook_name] = by_hook.get(hook_name, 0) + 1
        except Exception:
            continue

    by_hook_sorted = sorted(by_hook.items(), key=lambda x: -x[1])
    return {
        "total": runtime_error + non_json_output,
        "runtime_error": runtime_error,
        "non_json_output": non_json_output,
        "by_hook": by_hook_sorted,
    }


def escalation(days: int, terminal_filter: str = None, show_all: bool = False):
    """Escalation recommendations."""
    print("=" * 60)
    print("ESCALATION ANALYSIS")
    print("=" * 60)
    print("\nPhase 1 → Phase 2 escalation threshold: >30% non-compliance\n")

    # Check each Phase 1 hook
    hooks_status = []

    # Error Attribution
    log_file = Path("P:/.claude/logs/error_attribution.jsonl")
    if log_file.exists():
        entries = len(log_file.read_text().splitlines())
        # Can't determine compliance without transcript analysis
        hooks_status.append(
            {
                "name": "Error Attribution",
                "phase": 1,
                "entries": entries,
                "compliance": "Manual review needed",
                "action": "Review transcripts for source mentions",
            }
        )

    # Assumption Audit
    log_file = HOOKS_DIR / "logs/assumption_audit_v2.jsonl"
    if log_file.exists():
        import json

        complied = 0
        total = 0
        for line in log_file.read_text().splitlines():
            try:
                entry = json.loads(line)
                if entry.get("event") == "compliance_check":
                    total += 1
                    if entry.get("complied"):
                        complied += 1
            except json.JSONDecodeError:
                pass

        if total > 0:
            rate = complied / total
            action = "ESCALATE to Phase 2" if rate < 0.70 else "No action needed"
            hooks_status.append(
                {
                    "name": "Assumption Audit",
                    "phase": 1,
                    "entries": total,
                    "compliance": f"{rate:.0%}",
                    "action": action,
                }
            )

    # Speculation Gate
    spec_db = HOOKS_DIR / "speculation_violations.sqlite"
    if spec_db.exists():
        import sqlite3
        from datetime import datetime, timedelta

        conn = sqlite3.connect(str(spec_db))
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        cursor = conn.execute("SELECT COUNT(*) FROM violations WHERE timestamp > ?", (cutoff,))
        violations = cursor.fetchone()[0]
        conn.close()

        # Estimate compliance (heuristic: violations vs expected diagnostic responses)
        if violations == 0:
            rate = 1.0
            action = "No action needed"
        elif violations < 5:
            rate = 0.90
            action = "Monitor - low violation count"
        elif violations < 20:
            rate = 0.75
            action = "Review patterns - moderate violations"
        else:
            rate = 0.50
            action = "ESCALATE - high violation count"

        hooks_status.append(
            {
                "name": "Speculation Gate",
                "phase": 2,  # Already blocking
                "entries": violations,
                "compliance": f"{rate:.0%} (est.)",
                "action": action,
            }
        )

    # Print status
    print("Hook Status:")
    print("-" * 60)
    for h in hooks_status:
        print(f"\n{h['name']} (Phase {h['phase']})")
        print(f"  Entries: {h['entries']}")
        print(f"  Compliance: {h['compliance']}")
        print(f"  Action: {h['action']}")

    if not hooks_status:
        print("No Phase 1 hooks with sufficient data for analysis.")

    print("\n" + "-" * 60)
    print("Phase 2 (Already Enforcing):")
    print("  - Skill Enforcement: Blocks non-Skill tool use for slash commands")
    print("  - Empirical Claims: Blocks success claims without execution")
    print("  - Entity Correlation: Blocks claims about unread entities")
    print("  - Speculation Gate: Blocks diagnostic claims without source verification")


def main():
    parser = argparse.ArgumentParser(description="Hook Behavioral Compliance Audit")
    parser.add_argument(
        "subcommand",
        nargs="?",
        default="dashboard",
        choices=[
            "dashboard",
            "blocks",
            "assumptions",
            "attribution",
            "speculation",
            "reasoning",
            "principles",
            "frameguard",
            "stats",
            "ups",
            "friction",
            "health",
            "escalation",
            "replay",
            "loop-fix",
        ],
        help="Analysis type (default: dashboard)",
    )
    parser.add_argument("--days", type=int, default=7, help="Analysis period in days (default: 7)")
    parser.add_argument("--terminal", action="store_true", help="Filter to current terminal only")
    parser.add_argument(
        "--all", dest="show_all", action="store_true", help="Show per-terminal breakdown"
    )
    parser.add_argument("--turn", help="Filter to a specific turn ID")
    parser.add_argument("--limit", type=int, default=20, help="Limit recent stat rows (default: 20)")

    args = parser.parse_args()

    # Resolve terminal filter
    terminal_filter = None
    if args.terminal:
        terminal_filter = get_current_terminal_id()
        if not terminal_filter:
            print("Warning: Could not detect terminal ID, showing all")

    handlers = {
        "dashboard": dashboard,
        "blocks": blocks,
        "assumptions": assumptions,
        "attribution": attribution,
        "speculation": speculation,
        "reasoning": reasoning,
        "principles": principles,
        "frameguard": frameguard,
        "stats": stats,
        "ups": ups_stats,
        "friction": friction,
        "health": health,
        "escalation": escalation,
        "replay": replay,
        "loop-fix": loop_fix,
    }

    handler = handlers.get(args.subcommand, dashboard)
    if args.subcommand == "stats":
        handler(args.days, terminal_filter, args.show_all, args.turn, args.limit)
    else:
        handler(args.days, terminal_filter, args.show_all)


if __name__ == "__main__":
    main()
