#!/usr/bin/env python3
"""
Judge Feedback System - Session Start Summary and First-Query Advisory.

Provides lightweight judge activity summaries for session start and first-query
advisory injection based on recent patterns.
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional

_HOOKS_DIR = Path(__file__).resolve().parent.parent

# Path to judge verdicts telemetry
_JUDGE_VERDICTS_PATH = _HOOKS_DIR / "logs" / "diagnostics" / "judge_verdicts.jsonl"

# Path for first-query advisory state (session-scoped)
_STATE_DIR = Path.home() / ".claude" / "state"

# Path for session quality history (threshold effectiveness tracking)
_SESSION_QUALITY_PATH = Path.home() / ".claude" / "artifacts" / "judge_session_quality.jsonl"
_SESSION_QUALITY_MAX = 10


def load_recent_judge_verdicts(hours: int = 24) -> list[dict]:
    """Load judge verdicts from the last N hours.

    Args:
        hours: Number of hours to look back.

    Returns:
        List of verdict dicts with timestamp, score, passes, issues, etc.
    """
    if not _JUDGE_VERDICTS_PATH.exists():
        return []

    cutoff = datetime.now().timestamp() - (hours * 3600)
    verdicts = []

    try:
        with open(_JUDGE_VERDICTS_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    v = json.loads(line)
                    if v.get("timestamp", 0) > cutoff:
                        verdicts.append(v)
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass

    return verdicts


def summarize_judge_activity(verdicts: list[dict]) -> dict:
    """Calculate summary statistics from verdicts.

    Args:
        verdicts: List of verdict dicts.

    Returns:
        Dict with total, blocks, avg_score, avg_latency, top_issues.
    """
    if not verdicts:
        return {
            "total": 0,
            "blocks": 0,
            "avg_score": 0.0,
            "avg_latency": 0.0,
            "top_issues": [],
        }

    total = len(verdicts)
    blocks = sum(1 for v in verdicts if not v.get("passes", True))
    scores = [v.get("score", 0.0) for v in verdicts]
    latencies = [v.get("latency_ms", 0.0) for v in verdicts]

    # Collect all issues
    all_issues: list[str] = []
    for v in verdicts:
        all_issues.extend(v.get("issues", []))

    top_issues = Counter(all_issues).most_common(3)

    return {
        "total": total,
        "blocks": blocks,
        "avg_score": sum(scores) / total if scores else 0.0,
        "avg_latency": sum(latencies) / len(latencies) if latencies else 0.0,
        "top_issues": top_issues,
    }


def format_session_start_judge_summary(summary: dict) -> Optional[str]:
    """Format judge summary for session start output.

    Returns None if nothing actionable, or a compact string (1-3 lines).
    """
    total = summary.get("total", 0)
    blocks = summary.get("blocks", 0)
    avg_score = summary.get("avg_score", 0.0)

    # Need minimum data before showing anything
    if total < 3:
        return None

    # Check if anything notable happened
    block_rate = blocks / total if total > 0 else 0
    top_issues = summary.get("top_issues", [])

    # Format output based on severity
    if blocks == 0 and avg_score > 0.75:
        # All good - minimal output
        return f"\U0001f3af Judge: {total} evals, 0 blocks, avg {avg_score:.2f} ✓"

    # Something notable happened
    output = f"\U0001f6a1 Judge Summary ({total}h): {total} evals, {blocks} blocks ({block_rate*100:.0f}%), avg {avg_score:.2f}"

    # Add top issue if any
    if top_issues:
        issue_name, issue_count = top_issues[0]
        output += f"\n   ⚠️ Top issue: {issue_name} ({issue_count}x)"

        # Add actionable suggestion based on issue
        if "investigate" in issue_name.lower():
            output += " — read files before asking"
        elif "evidence" in issue_name.lower():
            output += " — add file paths and line numbers"
        elif "short" in issue_name.lower():
            output += " — expand response detail"
        elif "hedg" in issue_name.lower():
            output += " — be more direct"

    return output


def should_inject_first_query_advisory(summary: dict, session_id: str) -> bool:
    """Check if first-query advisory should be injected.

    Trigger policies:
    - block_rate >= 15% (from recent patterns)
    - OR avg_score < 0.72
    - OR same_issue >= 3 times
    """
    if summary.get("total", 0) < 3:
        return False

    # Check state file for whether we've already shown this session
    state_file = _STATE_DIR / f"judge_advisory_{session_id}.json"
    if state_file.exists():
        return False  # Already shown this session

    block_rate = summary.get("blocks", 0) / summary.get("total", 1)
    avg_score = summary.get("avg_score", 0.0)
    top_issues = summary.get("top_issues", [])

    # Trigger conditions
    if block_rate >= 0.15:
        return True
    if avg_score < 0.72:
        return True
    if top_issues and top_issues[0][1] >= 3:
        return True

    return False


def build_first_query_advisory(summary: dict) -> Optional[str]:
    """Build advisory message for first user query.

    Returns None if no advisory needed, or a compact advisory string.
    """
    top_issues = summary.get("top_issues", [])
    if not top_issues:
        return None

    top_issue, count = top_issues[0]
    block_rate = summary.get("blocks", 0) / max(summary.get("total", 1), 1) * 100

    # Build compact advisory
    advisory = f"\U0001f6a1 Judge pattern: '{top_issue}' ({count}x, {block_rate:.0f}% block rate)"

    # Add specific guidance based on issue type
    if "investigate" in top_issue.lower():
        advisory += "\n   Tip: Read files before asking user questions"
    elif "evidence" in top_issue.lower():
        advisory += "\n   Tip: Cite specific file paths and line numbers"
    elif "short" in top_issue.lower():
        advisory += "\n   Tip: Expand responses with more detail"
    elif "hedg" in top_issue.lower():
        advisory += "\n   Tip: Lead with the answer, then explain"

    return advisory


def mark_advisory_shown(session_id: str) -> None:
    """Mark that first-query advisory has been shown for this session."""
    state_file = _STATE_DIR / f"judge_advisory_{session_id}.json"
    try:
        state_file.write_text(
            json.dumps({"session_id": session_id, "timestamp": time.time()}),
            encoding="utf-8"
        )
    except Exception:
        pass


def check_automation_effectiveness(
    verdicts: list[dict],
    min_window_count: int = 3,
    score_threshold: float = 0.72,
    block_threshold: float = 0.15,
) -> str | None:
    """Check for persistent poor judge outcomes across 24h windows.

    Derives persistence from verdict timestamps — no external state needed.
    A window is degraded when BOTH score < threshold AND block_rate >= threshold.

    Escalation levels:
      - None: metrics are healthy or first degradation
      - Degraded warning: current window degraded, but not yet persistent
      - Escalation: 3+ degraded windows in last 5
    """
    if len(verdicts) < 3:
        return None

    now = time.time()
    window_size = 86400  # 24 hours

    # Group verdicts into 24h windows going back up to 5 windows
    windows: dict[int, list[dict]] = {}
    for v in verdicts:
        ts = v.get("timestamp", 0)
        if now - ts > 5 * window_size:
            continue  # Skip if older than 5 windows
        wid = int(ts // window_size)
        windows.setdefault(wid, []).append(v)

    if len(windows) < min_window_count:
        return None

    # Sort windows newest-first
    sorted_windows = sorted(windows.keys(), reverse=True)

    # Count degraded windows
    degraded_windows = []
    for wid in sorted_windows[:5]:
        wv = windows[wid]
        total = len(wv)
        blocks = sum(1 for v in wv if not v.get("passes", True))
        scores = [v.get("score", 0.0) for v in wv]
        avg_score = sum(scores) / total if scores else 0.0
        block_rate = blocks / total if total > 0 else 0.0

        is_degraded = avg_score < score_threshold and block_rate >= block_threshold
        degraded_windows.append((wid, is_degraded, avg_score, block_rate, total))

    degraded_count = sum(1 for _, d, _, _, _ in degraded_windows if d)

    current_window_degraded = degraded_windows[0][1] if degraded_windows else False

    if degraded_count >= min_window_count:
        # Escalation: persistent degradation
        worst = min(degraded_windows, key=lambda x: x[2] if x[1] else 1.0)
        _, _, worst_score, worst_block, worst_total = worst
        return (
            f"\n\U0001f7e9 Judge automation degraded: {degraded_count} of last {min_window_count}+ windows "
            f"show avg score < {score_threshold} and block rate >= {block_threshold*100:.0f}%.\n"
            f"   Latest: score {worst_score:.2f}, block rate {worst_block*100:.0f}% ({worst_total} evals).\n"
            f"   \U0001fae1 Action: Review blocking patterns — check if self-investigation mode is active "
            f"or advisory thresholds need recalibration."
        )

    if current_window_degraded:
        # Degraded but not yet persistent
        _, _, cur_score, cur_block, cur_total = degraded_windows[0]
        return (
            f"\n\U0001f7e9 Judge quality degraded this window: "
            f"score {cur_score:.2f}, block rate {cur_block*100:.0f}% ({cur_total} evals).\n"
            f"   Not yet persistent — monitoring next window."
        )

    return None


def check_telemetry_schema_health(
    verdicts: list[dict],
    min_sample_size: int = 3,
    warn_threshold: float = 0.80,
) -> str | None:
    """Check schema completeness of recent verdicts and return maintenance note if needed.

    Args:
        verdicts: Recent judge verdicts (already filtered by recency)
        min_sample_size: Minimum verdicts needed before checking (align with summary gate)
        warn_threshold: Fraction of verdicts missing `issues` before warning (0.80 = 80%)

    Returns:
        Compact maintenance note string, or None if no action needed
    """
    if len(verdicts) < min_sample_size:
        return None

    missing_count = 0
    malformed_count = 0

    for v in verdicts:
        issues = v.get("issues")
        if issues is None:
            missing_count += 1
        elif not isinstance(issues, list):
            malformed_count += 1

    total = len(verdicts)
    unusable_count = missing_count + malformed_count
    unusable_ratio = unusable_count / total

    if unusable_ratio >= warn_threshold:
        return (
            f"\n\U0001f7e9 Maintenance note: Recent judge telemetry missing `issues` field "
            f"in {missing_count}/{total} verdicts"
            f"{f' ({malformed_count} malformed)' if malformed_count > 0 else ''}.\n"
            f"   Recurring-issue summaries may be incomplete. "
            f"Consider adding structured issue labels at verdict producer."
        )

    return None


def check_judge_integration_health(
    verdicts: list[dict],
    min_sample: int = 5,
    warn_threshold: float = 0.05,
    escalate_threshold: float = 0.10,
) -> str | None:
    """Check for external judge integration failures in recent verdicts.

    Detects when the external judge subprocess fails and the system falls back to
    heuristic evaluation or returns error verdicts. These failures are invisible to
    score-based checks because fail-open behavior makes them appear superficially healthy.

    Signal: model_used == "error" (set by the exception handler in external_judge.py)
    Note: model_used == "heuristic" is normal heuristic fallback, not an integration failure.

    Returns:
        None when healthy or insufficient data.
        Warning when error_rate >= warn_threshold.
        Escalation when error_rate >= escalate_threshold.
    """
    if len(verdicts) < min_sample:
        return None

    error_verdicts = [v for v in verdicts if v.get("model_used") == "error"]
    error_rate = len(error_verdicts) / len(verdicts)

    if error_rate >= escalate_threshold:
        # Grab first error string for operator context
        sample_error = ""
        for v in error_verdicts:
            err = v.get("error")
            if err:
                sample_error = str(err)[:80]
                break
        if sample_error:
            return (
                f"\n\U0001f7e9 Judge integration degraded: {error_rate*100:.1f}% error verdicts "
                f"({len(error_verdicts)}/{len(verdicts)}) in the last 24h.\n"
                f"   Sample error: {sample_error}.\n"
                f"   \U0001fae1 Action: Verify external judge subprocess, credentials, "
                f"and endpoint availability."
            )
        else:
            return (
                f"\n\U0001f7e9 Judge integration degraded: {error_rate*100:.1f}% error verdicts "
                f"({len(error_verdicts)}/{len(verdicts)}) in the last 24h.\n"
                f"   \U0001fae1 Action: Verify external judge subprocess, credentials, "
                f"and endpoint availability."
            )

    if error_rate >= warn_threshold:
        return (
            f"\n\U0001f7e9 Judge integration warning: {error_rate*100:.1f}% error verdicts "
            f"({len(error_verdicts)}/{len(verdicts)}) in the last 24h.\n"
            f"   External judge failures detected; verify subprocess and endpoint health."
        )

    return None


def record_session_quality(
    session_id: str,
    avg_score: float,
    block_rate: float,
) -> None:
    """Append current session quality to the session history log.

    Writes a JSON line to _SESSION_QUALITY_PATH using atomic .tmp rename.
    Keeps last _SESSION_QUALITY_MAX sessions; prunes oldest on overflow.

    Thresholds (0.72 score, 0.15 block rate, 3 consecutive sessions) are
    initial operational defaults — not derived from repo precedent.
    """
    entry = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "avg_score": avg_score,
        "block_rate": block_rate,
    }

    # Load existing entries
    existing: list[dict] = []
    if _SESSION_QUALITY_PATH.exists():
        try:
            with open(_SESSION_QUALITY_PATH, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        existing.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

    # Deduplicate: remove prior entry with same session_id (idempotent update)
    existing = [e for e in existing if e.get("session_id") != session_id]

    # Append new entry
    existing.append(entry)

    # Prune to bounded size (keep newest _SESSION_QUALITY_MAX)
    if len(existing) > _SESSION_QUALITY_MAX:
        existing = existing[-_SESSION_QUALITY_MAX:]

    # Atomic write via .tmp rename (Windows-safe)
    tmp = _SESSION_QUALITY_PATH.with_suffix(".tmp")
    try:
        tmp.write_text(
            "\n".join(json.dumps(e, ensure_ascii=False) for e in existing) + "\n",
            encoding="utf-8"
        )
        if _SESSION_QUALITY_PATH.exists():
            _SESSION_QUALITY_PATH.unlink()
        tmp.replace(_SESSION_QUALITY_PATH)
    except Exception:
        pass  # Fail-open: don't block session start on state errors


def check_threshold_effectiveness_escalation(
    session_id: str,
    current_avg_score: float,
    current_block_rate: float,
    poor_score_threshold: float = 0.72,
    poor_block_threshold: float = 0.15,
    consecutive_sessions_required: int = 3,
) -> str | None:
    """Check if poor quality persists across consecutive sessions despite advisories.

    Loads recent session quality log, appends current session via record_session_quality(),
    then counts consecutive sessions (newest-first) where:
      - avg_score < poor_score_threshold  OR
      - block_rate >= poor_block_threshold

    Escalation levels:
      - None: healthy or streak < consecutive_sessions_required
      - Warning: exactly consecutive_sessions_required consecutive poor sessions
      - Escalation: streak > consecutive_sessions_required
    """
    # Append current session to history
    record_session_quality(session_id, current_avg_score, current_block_rate)

    # Load recent sessions
    if not _SESSION_QUALITY_PATH.exists():
        return None

    sessions: list[dict] = []
    try:
        with open(_SESSION_QUALITY_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    sessions.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception:
        return None

    if len(sessions) < consecutive_sessions_required:
        return None

    # Count consecutive poor sessions from newest
    consecutive_poor = 0
    for s in reversed(sessions):
        avg = s.get("avg_score", 1.0)
        br = s.get("block_rate", 0.0)
        is_poor = avg < poor_score_threshold or br >= poor_block_threshold
        if is_poor:
            consecutive_poor += 1
        else:
            break  # streak broken

    # Count consecutive poor sessions from newest, collect trend data
    consecutive_poor = 0
    poor_sessions_trend: list[dict] = []
    for s in reversed(sessions):
        avg = s.get("avg_score", 1.0)
        br = s.get("block_rate", 0.0)
        is_poor = avg < poor_score_threshold or br >= poor_block_threshold
        if is_poor:
            consecutive_poor += 1
            poor_sessions_trend.append(s)
        else:
            break  # streak broken

    # Build compact trend line: [score/block%] → [score/block%] → ...
    trend_parts = [
        f"[{s.get('avg_score', 0):.2f}/{int(s.get('block_rate', 0) * 100)}%]"
        for s in reversed(poor_sessions_trend)
    ]
    trend_line = " → ".join(trend_parts)

    if consecutive_poor > consecutive_sessions_required:
        return (
            f"\n\U0001f7e9 Judge effectiveness degraded: Quality issues persist across "
            f"{consecutive_poor} consecutive sessions despite advisories.\n"
            f"   Recent sessions: {trend_line}\n"
            f"   \U0001fae1 Action: Review advisory strategy or recalibrate thresholds."
        )

    if consecutive_poor == consecutive_sessions_required:
        return (
            f"\n\U0001f7e9 Judge effectiveness warning: Quality issues persist across "
            f"{consecutive_poor} consecutive sessions despite advisories.\n"
            f"   📊 Recent trend: {trend_line}\n"
            f"   Consider: Review first-query advisory text or tighten reminder thresholds."
        )

    return None


def main() -> int:
    """Main entry point for standalone execution.

    Session start output disabled — verdicts kept as raw telemetry but
    no longer surfaced. Stop hooks enforce behavior directly; the Judge
    was a redundant post-hoc scoring layer with no consumer.
    """
    return 0
    try:  # noqa: unreachable — preserved for potential re-enablement
        verdicts = load_recent_judge_verdicts(hours=24)
        summary = summarize_judge_activity(verdicts)
        output = format_session_start_judge_summary(summary)

        if output:
            # Append schema health note if telemetry completeness is poor
            schema_note = check_telemetry_schema_health(verdicts)
            if schema_note:
                output += schema_note

            # Append integration health note if error verdicts detected
            integration_note = check_judge_integration_health(verdicts)
            if integration_note:
                output += integration_note

            # 5-day effectiveness check and session quality escalation removed.
            # The 24h summary above is sufficient. Functions remain in module.

            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": output
                }
            }))

        return 0

    except Exception:
        return 0


if __name__ == "__main__":
    sys.exit(main())