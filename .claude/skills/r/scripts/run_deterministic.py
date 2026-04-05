#!/usr/bin/env python3
"""
Deterministic remember/refine runner for /r.
"""

from __future__ import annotations

import argparse
import inspect
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Constants for git status checking
_GIT_TIMEOUT_SECONDS = 5
_GIT_EXIT_CODE_HAS_CHANGES = 1
_GIT_EXIT_CODE_CLEAN = 0
_STATUS_MODIFIED = "modified"
_ACTION_COMMIT_OR_STASH = "Commit or stash changes"


@dataclass
class TopicSelection:
    topic: str
    source: str
    confidence: float
    stale_context: bool = False
    stale_reason: str | None = None
    notes: list[str] | None = None


def _ensure_import_paths() -> None:
    for candidate in ("P:/__csf/src", "P:/__csf", "P:/"):
        if candidate not in sys.path:
            sys.path.insert(0, candidate)


def _extract_work_summary(ctx: dict[str, Any]) -> str:
    if not isinstance(ctx, dict):
        return ""
    if "work_summary" in ctx:
        return str(ctx.get("work_summary", "")).strip()
    analysis = ctx.get("analysis", {})
    if isinstance(analysis, dict):
        return str(analysis.get("work_summary", "")).strip()
    return ""


def read_q_context_compat(wt_session: str) -> dict[str, Any] | None:
    _ensure_import_paths()
    try:
        import lib.q_context as qmod
    except Exception:
        return None

    read_context = getattr(qmod, "read_context", None)
    if read_context is None:
        return None

    try:
        sig = inspect.signature(read_context)
        params = set(sig.parameters.keys())
    except Exception:
        params = set()

    try:
        if "session_id" in params or "check_stale" in params:
            raw = read_context(wt_session, check_stale=True)
            if raw is None:
                return None
            work_summary = _extract_work_summary(raw)
            stale = raw.get("stale", {}) if isinstance(raw, dict) else {}
            return {
                "work_summary": work_summary,
                "stale": {
                    "is_stale": bool(stale.get("is_stale", False)),
                    "reason": stale.get("reason"),
                },
            }

        raw = read_context()
        if raw is None:
            return None
        is_stale = False
        reason = None
        check_staleness = getattr(qmod, "check_staleness", None)
        if callable(check_staleness):
            try:
                is_stale = bool(check_staleness(raw))
                if is_stale:
                    reason = "q_context check_staleness() returned True"
            except Exception:
                is_stale = False
        return {
            "work_summary": _extract_work_summary(raw),
            "stale": {"is_stale": is_stale, "reason": reason},
        }
    except Exception:
        return None


def get_session_files_compat(wt_session: str) -> list[str]:
    _ensure_import_paths()
    try:
        from src.modules.session_management.session_activity_tracker import (
            get_session_files,
        )

        sid = f"wt_{wt_session[:8]}" if wt_session else None
        return get_session_files(session_id=sid, operation_filter=["edit", "write"])
    except Exception:
        return []


def check_uncommitted_changes(session_files: list[str]) -> list[dict[str, str]]:
    """Check git status for only the provided session files.

    This function checks each file for uncommitted changes by running
    ``git diff --quiet`` on the file. Git exit codes indicate status:
    - Exit code 1: File has uncommitted changes
    - Exit code 0: File is clean (no changes)

    Args:
        session_files: List of file paths to check (session-scoped).

    Returns:
        List of uncommitted changes. Each change is a dict with keys:
            - file_path: Path to the modified file
            - status: Status indicator (e.g., "modified")
            - action: Recommended action (e.g., "Commit or stash changes")

    Notes:
        - Non-existent files are silently skipped
        - Git timeouts and missing git are handled gracefully
        - Only checks for modifications to committed files (not untracked files)
    """
    changes = []

    for file_path in session_files:
        # Skip non-existent files
        if not Path(file_path).exists():
            continue

        # Check if file has uncommitted changes using git diff --quiet
        try:
            # Use git -C to run from the file's directory
            file_dir = str(Path(file_path).parent)
            result = subprocess.run(
                ["git", "-C", file_dir, "diff", "--quiet", "--", file_path],
                capture_output=True,
                timeout=_GIT_TIMEOUT_SECONDS,
            )

            if result.returncode == _GIT_EXIT_CODE_HAS_CHANGES:
                # File has uncommitted changes
                changes.append({
                    "file_path": file_path,
                    "status": _STATUS_MODIFIED,
                    "action": _ACTION_COMMIT_OR_STASH,
                })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Handle git timeout or git not found gracefully
            continue

    return changes


def scan_code_patterns(session_files: list[str]) -> list[dict[str, Any]]:
    """
    Scan session files for code patterns (TODO, FIXME, HACK, etc.).

    Args:
        session_files: List of file paths to scan

    Returns:
        List of code pattern findings with keys: pattern, file_path, line_number, line_content
    """
    # Pattern definitions from code_scanner.py
    pattern_definitions = {
        "TODO": r"TODO(?:|\s)",
        "FIXME": r"FIXME(?:|\s)",
        "HACK": r"HACK(?:|\s)",
        "XXX": r"XXX(?:|\s)",
        "NOTE": r"NOTE(?:|\s)",
        "NotImplementedError": r"raise\s+NotImplementedError",
    }

    findings = []

    for file_path in session_files:
        # Skip non-existent files
        if not Path(file_path).exists():
            continue

        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()
        except (OSError, UnicodeDecodeError):
            continue

        for pattern_name, pattern in pattern_definitions.items():
            for line_num, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    findings.append({
                        "pattern": pattern_name,
                        "file_path": file_path,
                        "line_number": line_num,
                        "line_content": line.strip(),
                    })

    return findings


def choose_topic(explicit_topic: str | None, wt_session: str) -> TopicSelection:
    notes: list[str] = []
    if explicit_topic and explicit_topic.strip():
        return TopicSelection(explicit_topic.strip(), "explicit", 1.0, notes=notes)

    qctx = read_q_context_compat(wt_session)
    if qctx:
        work_summary = str(qctx.get("work_summary", "")).strip()
        stale = qctx.get("stale", {})
        if stale.get("is_stale"):
            reason = str(stale.get("reason", "unknown"))
            notes.append(f"/q context is stale: {reason}")
            if work_summary:
                return TopicSelection(
                    work_summary,
                    "q_context_stale",
                    0.65,
                    stale_context=True,
                    stale_reason=reason,
                    notes=notes,
                )
        if work_summary:
            return TopicSelection(work_summary, "q_context", 0.9, notes=notes)

    files = get_session_files_compat(wt_session)
    if files:
        names = [f.split("/")[-1].split("\\")[-1] for f in files[:3]]
        return TopicSelection(
            f"Session work around: {', '.join(names)}",
            "session_activity",
            0.7,
            notes=notes,
        )

    return TopicSelection("General deterministic review", "fallback", 0.4, notes=notes)


def _risk_signals(text: str) -> list[str]:
    t = text.lower()
    mapping = {
        "architecture": ["architecture", "system design", "module boundary"],
        "migration": ["migration", "data move", "schema change"],
        "rewrite": ["rewrite", "rebuild", "replace core"],
        "security": ["auth", "permission", "security", "token", "secret"],
        "performance": ["performance", "latency", "slow", "hot path"],
    }
    found = []
    for label, patterns in mapping.items():
        if any(p in t for p in patterns):
            found.append(label)
    return found


def build_forgotten_items(topic: str, session_files: list[str]) -> list[dict[str, Any]]:
    lower_files = [f.lower() for f in session_files]
    items: list[dict[str, Any]] = []

    if not any(("test" in f or f.endswith("_test.py") or f.endswith("test.py")) for f in lower_files):
        items.append({"item": "Missing or unchanged tests for this change", "severity": "high"})
    if not any(("readme" in f or "changelog" in f or f.endswith(".md")) for f in lower_files):
        items.append({"item": "Documentation update may be missing", "severity": "medium"})
    if any(k in topic.lower() for k in ["migration", "schema", "deploy"]) and not any("rollback" in f for f in lower_files):
        items.append({"item": "Rollback plan/checklist may be missing", "severity": "high"})
    if any(k in topic.lower() for k in ["auth", "security", "token", "permission"]):
        items.append({"item": "Security edge-case verification may be incomplete", "severity": "high"})
    if not items:
        items.append({"item": "No obvious omissions detected from deterministic checks", "severity": "info"})
    return items


def build_deterministic_improvements(topic: str, session_files: list[str]) -> list[dict[str, Any]]:
    improvements: list[dict[str, Any]] = []
    improvements.append(
        {
            "title": "Add focused regression tests for changed paths",
            "category": "tests",
            "confidence": 0.9,
            "effort": "low",
        }
    )
    if any(f.endswith(".py") for f in session_files):
        improvements.append(
            {
                "title": "Run static checks on touched Python modules",
                "category": "quality",
                "confidence": 0.85,
                "effort": "low",
            }
        )
    if "performance" in topic.lower():
        improvements.append(
            {
                "title": "Add before/after measurement for hot path",
                "category": "performance",
                "confidence": 0.8,
                "effort": "medium",
            }
        )
    return improvements


def decide_escalation(topic: str, forgotten_items: list[dict[str, Any]]) -> dict[str, Any]:
    signals = _risk_signals(topic)
    high = [i for i in forgotten_items if i.get("severity") == "high"]
    should_escalate = len(signals) >= 2 or len(high) >= 2
    reason = "Multiple high-risk signals or omissions detected." if should_escalate else "Deterministic pass sufficient."
    return {"yes": should_escalate, "reason": reason, "signals": signals}


def build_payload(topic_meta: TopicSelection, topic: str, session_files: list[str]) -> dict[str, Any]:
    forgotten = build_forgotten_items(topic, session_files)
    improvements = build_deterministic_improvements(topic, session_files)
    escalation = decide_escalation(topic, forgotten)
    must_fix_now = [i for i in forgotten if i.get("severity") == "high"]
    can_do_soon = [i for i in improvements if i.get("effort") in ("low", "medium")]
    next_commands = ["/p", "/q"]
    if escalation["yes"]:
        next_commands.append("/s --mode heavy")
    else:
        next_commands.append("/code")

    # Scan for code patterns and uncommitted changes
    code_pattern_findings = scan_code_patterns(session_files)
    git_status_findings = check_uncommitted_changes(session_files)

    return {
        "topic": topic_meta.topic,
        "topic_source": topic_meta.source,
        "topic_confidence": topic_meta.confidence,
        "stale_context": topic_meta.stale_context,
        "stale_reason": topic_meta.stale_reason,
        "notes": topic_meta.notes or [],
        "forgotten_items": forgotten,
        "deterministic_improvements": improvements,
        "must_fix_now": must_fix_now,
        "can_do_soon": can_do_soon,
        "escalate_to_s_heavy": escalation,
        "next_commands": next_commands,
        "code_pattern_findings": code_pattern_findings,
        "git_status_findings": git_status_findings,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# /r Deterministic Report: {payload['topic']}",
        "",
        f"- Topic source: `{payload['topic_source']}` ({payload['topic_confidence']:.2f})",
        f"- Escalate to /s heavy: `{payload['escalate_to_s_heavy']['yes']}`",
        "",
        "## Forgotten Items",
    ]
    for item in payload["forgotten_items"]:
        lines.append(f"- [{item['severity']}] {item['item']}")
    lines.append("")
    lines.append("## Deterministic Improvements")
    for item in payload["deterministic_improvements"]:
        lines.append(f"- {item['title']} ({item['category']}, {item['effort']}, conf={item['confidence']:.2f})")
    lines.append("")

    # Code Pattern Findings
    if payload.get("code_pattern_findings"):
        lines.append("## Code Pattern Findings")
        for finding in payload["code_pattern_findings"]:
            lines.append(f"- [{finding['pattern']}] {finding['file_path']}:{finding['line_number']}")
            lines.append(f"  {finding['line_content']}")
        lines.append("")

    # Git Status Findings
    if payload.get("git_status_findings"):
        lines.append("## Uncommitted Changes")
        for finding in payload["git_status_findings"]:
            lines.append(f"- [{finding['status']}] {finding['file_path']}")
            lines.append(f"  Action: {finding['action']}")
        lines.append("")

    lines.append("## Next Commands")
    for cmd in payload["next_commands"]:
        lines.append(f"- {cmd}")
    return "\n".join(lines)


def render_text(payload: dict[str, Any]) -> str:
    lines = [
        f"/r Deterministic Report: {payload['topic']}",
        f"Source: {payload['topic_source']} ({payload['topic_confidence']:.2f})",
        f"Escalate to /s heavy: {payload['escalate_to_s_heavy']['yes']}",
        "",
        "Forgotten Items:",
    ]
    for item in payload["forgotten_items"]:
        lines.append(f"- [{item['severity']}] {item['item']}")
    lines.append("")
    lines.append("Deterministic Improvements:")
    for item in payload["deterministic_improvements"]:
        lines.append(f"- {item['title']} ({item['category']}, {item['effort']})")
    lines.append("")

    # Code Pattern Findings
    if payload.get("code_pattern_findings"):
        lines.append("Code Pattern Findings:")
        for finding in payload["code_pattern_findings"]:
            lines.append(f"- [{finding['pattern']}] {finding['file_path']}:{finding['line_number']}")
            lines.append(f"  {finding['line_content']}")
        lines.append("")

    # Git Status Findings
    if payload.get("git_status_findings"):
        lines.append("Uncommitted Changes:")
        for finding in payload["git_status_findings"]:
            lines.append(f"- [{finding['status']}] {finding['file_path']}")
            lines.append(f"  Action: {finding['action']}")
        lines.append("")

    lines.append("Next Commands: " + ", ".join(payload["next_commands"]))
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic remember/refine pass for /r.")
    parser.add_argument("--topic", default="")
    parser.add_argument("--output", choices=["json", "markdown", "text"], default="text")
    parser.add_argument("--strict-stale", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    wt_session = os.environ.get("WT_SESSION", "")
    topic_meta = choose_topic(args.topic, wt_session)
    if args.strict_stale and topic_meta.stale_context:
        print(
            json.dumps(
                {
                    "error": "stale_context",
                    "reason": topic_meta.stale_reason,
                    "recommendation": "Run /q to refresh context, then rerun /r.",
                },
                indent=2,
            )
        )
        return 2
    files = get_session_files_compat(wt_session)
    payload = build_payload(topic_meta, topic_meta.topic, files)

    if args.output == "json":
        print(json.dumps(payload, indent=2))
    elif args.output == "markdown":
        print(render_markdown(payload))
    else:
        print(render_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
