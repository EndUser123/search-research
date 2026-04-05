#!/usr/bin/env python3
"""
Hook Audit Dashboard - Unified hook behavioral compliance report.

Usage:
    python hook_audit_dashboard.py [subcommand] [--days N] [--terminal] [--all]

Subcommands:
    (none)      Full dashboard (all metrics)
    blocks      Hook blocking events
    assumptions Assumption audit compliance
    attribution Error attribution compliance
    speculation Speculation gate compliance
    reasoning   Reasoning profile and THINK auto-routing metrics
    principles  Principle-based behavior monitoring (context_reuse, etc.)
    frameguard  FrameGuard systemic frame compliance (from DB)
    health      Hook system health
    escalation  Escalation recommendations
    replay      Enforcement replay quality metrics

Terminal Filtering (v2.1):
    --terminal  Filter to current terminal only
    --all       Show per-terminal breakdown
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))


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
        print("  No principle events logged yet.")
        print("  Monitor: principle_monitor.py Stop hook")
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
            "friction",
            "health",
            "escalation",
            "replay",
        ],
        help="Analysis type (default: dashboard)",
    )
    parser.add_argument("--days", type=int, default=7, help="Analysis period in days (default: 7)")
    parser.add_argument("--terminal", action="store_true", help="Filter to current terminal only")
    parser.add_argument(
        "--all", dest="show_all", action="store_true", help="Show per-terminal breakdown"
    )

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
        "friction": friction,
        "health": health,
        "escalation": escalation,
        "replay": replay,
    }

    handler = handlers.get(args.subcommand, dashboard)
    handler(args.days, terminal_filter, args.show_all)


if __name__ == "__main__":
    main()
