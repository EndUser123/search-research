"""Write check-state.md — the durable /check receipt consumed by /close.

Problem (audit 2026-07-29, Intervention 1): check-state.md was written by the
parent LLM, not a script. Only ~3 of ~24+ /check runs produced the receipt.
A /check FAIL without the receipt is invisible to close_accounting.py.

This script mechanizes the write. The orchestrator LLM still determines the
verdict (judgment), but the receipt format (mechanical) is produced here.

Consumer contract (close_accounting.py:557-560):
    session_re = r"^\\*\\*Session:\\*\\*\\s*([^\\s]+)"
    verdict_re = r"^\\*\\*Verdict:\\*\\*\\s*CHECK\\s+(PASS|FAIL)\\b(?:\\s*\\((\\d+)\\s*/\\s*(\\d+)[^)]*\\))?"

The output MUST contain exactly these two lines for the consumer to detect it:
    **Session:** <session-id>
    **Verdict:** CHECK <PASS|FAIL> (<passed>/<total> verifiers)

Input: JSON file with session_id, run_dir, verdict, verifiers[], test_results, issues[]
Output: <run_dir>/check-state.md (atomic write via os.replace)
Exit: 0 on success, 1 on contract violation (missing session_id or verdict)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def render_check_state(
    session_id: str,
    verdict: str,
    verifiers: list[dict],
    test_results: str = "",
    issues: list[dict] | None = None,
) -> str:
    """Render check-state.md content matching the close_accounting consumer contract.

    Args:
        session_id: The Grok session ID this /check run belongs to.
        verdict: "PASS" or "FAIL".
        verifiers: List of {concern, verdict, finding} dicts.
        test_results: Free-text test summary.
        issues: List of {severity, description} dicts.

    Returns:
        The full check-state.md content as a string.
    """
    verdict = verdict.upper().strip()
    total = len(verifiers)
    passed = sum(1 for v in verifiers if v.get("verdict", "").upper() == "PASS")

    lines = [
        "# /check state",
        f"**Session:** {session_id}",
        f"**Verdict:** CHECK {verdict} ({passed}/{total} verifiers)",
        "",
    ]

    # Verifiers section
    lines.append("## Verifiers")
    if verifiers:
        for v in verifiers:
            v_verdict = v.get("verdict", "?").upper()
            concern = v.get("concern", "?")
            finding = v.get("finding", "")
            entry = f"- **{concern}** — {v_verdict}"
            if finding:
                entry += f": {finding}"
            lines.append(entry)
    else:
        lines.append("(no verifier results recorded)")
    lines.append("")

    # Test results section
    lines.append("## Test results")
    lines.append(test_results if test_results else "(not applicable)")
    lines.append("")

    # Issues section
    lines.append("## Issues found during check")
    if issues:
        for issue in issues:
            severity = issue.get("severity", "?")
            description = issue.get("description", "")
            lines.append(f"- [{severity}] {description}")
    else:
        lines.append("none")

    return "\n".join(lines) + "\n"


def write_check_state(data: dict) -> Path:
    """Validate input, render, and atomically write check-state.md.

    Args:
        data: Dict with keys: session_id, run_dir, verdict, verifiers,
              test_results (optional), issues (optional).

    Returns:
        Path to the written check-state.md.

    Raises:
        ValueError: if session_id or verdict is missing/invalid.
    """
    session_id = data.get("session_id", "")
    if not session_id or not session_id.strip():
        raise ValueError("session_id is required (cannot be empty)")

    verdict = data.get("verdict", "").upper().strip()
    if verdict not in ("PASS", "FAIL"):
        raise ValueError(f"verdict must be PASS or FAIL, got: {verdict!r}")

    run_dir = Path(data.get("run_dir", ""))
    if not run_dir or not run_dir.is_dir():
        raise ValueError(f"run_dir must be an existing directory, got: {run_dir}")

    verifiers = data.get("verifiers", [])
    if not isinstance(verifiers, list):
        verifiers = []

    test_results = data.get("test_results", "")
    issues = data.get("issues", [])
    if not isinstance(issues, list):
        issues = []

    content = render_check_state(session_id, verdict, verifiers, test_results, issues)

    target = run_dir / "check-state.md"
    tmp = run_dir / f"check-state.tmp.{os.getpid()}"
    tmp.write_text(content, encoding="utf-8")
    os.replace(str(tmp), str(target))
    return target


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Write check-state.md receipt for /close consumption."
    )
    parser.add_argument(
        "--json",
        dest="json_file",
        required=True,
        help="Path to JSON file with session_id, run_dir, verdict, verifiers[]",
    )
    args = parser.parse_args(argv)

    try:
        data = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"error: cannot read JSON input: {exc}", file=sys.stderr)
        return 1

    try:
        target = write_check_state(data)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"check-state written: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
