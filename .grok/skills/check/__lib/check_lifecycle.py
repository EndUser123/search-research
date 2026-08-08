"""Durable /check run lifecycle: STARTED → verifier results → FINALIZED.

This module ensures every initialized /check run leaves durable evidence
that /close can detect — including runs that fail, are interrupted, or
never finalize. The prior implementation depended on the orchestrator LLM
remembering to write check-state.md; ~3 of ~24+ runs produced one. This
module makes the lifecycle mechanical.

Three functions, called at three fixed points in the /check SKILL.md:

1. ``start_run(session_id, run_dir)`` — called immediately after runDir
   creation. Writes ``check-run.json`` with status ``RUNNING``.

2. ``write_verifier_result(run_dir, index, concern, verdict, issues)``
   — called after each verifier returns. Writes a structured JSON result
   the finalizer can read and validate.

3. ``finalize_run(run_dir)`` — called on EVERY terminal path. Reads the
   manifest + verifier results, derives the verdict mechanically, writes
   ``check-state.md`` (PASS/FAIL) or marks INCOMPLETE, and updates
   ``check-run.json`` atomically.

Design invariants:
- The finalizer DERIVES the verdict from per-verifier results. It never
  trusts an aggregate LLM-supplied verdict. A supplied verdict is an
  optional consistency assertion only.
- A zero-verifier run produces INCOMPLETE, not PASS (no explicit
  zero-verifier PASS path is proven in the /check contract).
- Missing, malformed, or unreadable verifier results produce INCOMPLETE,
  never PASS.
- Every function writes atomically (tmp + os.replace).
- The manifest is the authoritative lifecycle record; the receipt is the
  /close-consumable artifact derived from it.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- Constants ---

MANIFEST_SCHEMA_VERSION = "1"
MANIFEST_FILENAME = "check-run.json"
RECEIPT_FILENAME = "check-state.md"
RESULTS_SUBDIR = "results"

# Run statuses
STATUS_RUNNING = "RUNNING"
STATUS_COMPLETE = "COMPLETE"
STATUS_INCOMPLETE = "INCOMPLETE"
STATUS_FINALIZE_FAILED = "FINALIZE_FAILED"

# Recognized verifier verdicts (subset of CHECK_VERDICTS from event_model.py)
VALID_VERIFIER_VERDICTS = frozenset({"PASS", "FAIL"})


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_write_json(path: Path, data: dict) -> None:
    """Write JSON atomically: tmp file + os.replace."""
    tmp = path.with_suffix(f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(str(tmp), str(path))


def _atomic_write_text(path: Path, text: str) -> None:
    """Write text atomically: tmp file + os.replace."""
    tmp = path.with_suffix(f".tmp.{os.getpid()}")
    tmp.write_text(text, encoding="utf-8")
    os.replace(str(tmp), str(path))


# ---------------------------------------------------------------------------
# 1. Start run — manifest creation
# ---------------------------------------------------------------------------


def start_run(session_id: str, run_dir: str | Path) -> Path:
    """Create the run manifest immediately after runDir creation.

    Args:
        session_id: The authoritative session ID (same one used throughout /check).
        run_dir: The run directory path (must exist).

    Returns:
        Path to the written check-run.json.

    Raises:
        ValueError: if session_id is empty or run_dir doesn't exist.
    """
    if not session_id or not session_id.strip():
        raise ValueError("session_id is required (cannot be empty)")
    run_dir = Path(run_dir)
    if not run_dir.is_dir():
        raise ValueError(f"run_dir must be an existing directory: {run_dir}")

    run_id = run_dir.name  # timestamp-based dir name from SKILL.md Step 0
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "session_id": session_id,
        "run_id": run_id,
        "run_dir": str(run_dir),
        "status": STATUS_RUNNING,
        "started_at": _utc_now(),
        "finalized_at": None,
        "receipt_path": None,
        "failure": None,
    }
    manifest_path = run_dir / MANIFEST_FILENAME
    _atomic_write_json(manifest_path, manifest)
    return manifest_path


# ---------------------------------------------------------------------------
# 2. Write verifier result — structured per-verifier evidence
# ---------------------------------------------------------------------------


def write_verifier_result(
    run_dir: str | Path,
    index: int,
    concern: str,
    verdict: str,
    issues: list[dict] | None = None,
) -> Path:
    """Write a structured verifier result file.

    Called after each verifier subagent returns. The orchestrator extracts
    the structured verdict from the verifier's output (using
    output_validator.validate_verifier_output) and writes it here so the
    finalizer has durable evidence to derive from.

    Args:
        run_dir: The run directory.
        index: Verifier index (0-based, matches spawn order).
        concern: The concern name (e.g., "harvest store").
        verdict: "PASS" or "FAIL" (validated).
        issues: Optional list of issue dicts {severity, description}.

    Returns:
        Path to the written result file.

    Raises:
        ValueError: if verdict is not PASS or FAIL.
    """
    verdict = verdict.upper().strip()
    if verdict not in VALID_VERIFIER_VERDICTS:
        raise ValueError(f"verifier verdict must be PASS or FAIL, got: {verdict!r}")

    run_dir = Path(run_dir)
    results_dir = run_dir / RESULTS_SUBDIR
    results_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "index": index,
        "concern": concern,
        "verdict": verdict,
        "issues": issues or [],
        "recorded_at": _utc_now(),
    }
    path = results_dir / f"verifier-{index}.json"
    _atomic_write_json(path, result)
    return path


# ---------------------------------------------------------------------------
# 3. Finalize run — derive verdict, write receipt, update manifest
# ---------------------------------------------------------------------------


def _read_verifier_results(run_dir: Path) -> tuple[list[dict], list[str]]:
    """Read all verifier-*.json result files.

    Returns (results, errors). Errors are non-fatal parse/read failures
    that contribute to INCOMPLETE status.
    """
    results_dir = run_dir / RESULTS_SUBDIR
    if not results_dir.is_dir():
        return [], ["results directory does not exist"]

    results = []
    errors = []
    for path in sorted(results_dir.glob("verifier-*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                errors.append(f"{path.name}: not a JSON object")
                continue
            if "verdict" not in data or data["verdict"] not in VALID_VERIFIER_VERDICTS:
                errors.append(
                    f"{path.name}: verdict missing/invalid "
                    f"({data.get('verdict', '?')})"
                )
                continue
            results.append(data)
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"{path.name}: {type(exc).__name__}: {exc}")

    return results, errors


def derive_verdict(verifier_results: list[dict]) -> tuple[str, int, int, str | None]:
    """Derive the final verdict from structured verifier results.

    Args:
        verifier_results: List of verifier result dicts, each with at least
            {"verdict": "PASS"|"FAIL", "concern": str}.

    Returns:
        (verdict, passed_count, total_count, failure_reason)
        - verdict: "PASS", "FAIL", or "INCOMPLETE"
        - failure_reason: None for PASS/FAIL; reason string for INCOMPLETE
    """
    if not verifier_results:
        return "INCOMPLETE", 0, 0, "no verifier results found"

    passed = sum(1 for r in verifier_results if r.get("verdict") == "PASS")
    total = len(verifier_results)

    if passed == total:
        return "PASS", passed, total, None

    # At least one FAIL
    return "FAIL", passed, total, None


def render_receipt(
    session_id: str,
    verdict: str,
    passed: int,
    total: int,
    verifier_results: list[dict],
    issues: list[dict] | None = None,
) -> str:
    """Render check-state.md matching the close_accounting.py consumer contract."""
    lines = [
        "# /check state",
        f"**Session:** {session_id}",
        f"**Verdict:** CHECK {verdict} ({passed}/{total} verifiers)",
        "",
    ]
    lines.append("## Verifiers")
    for r in verifier_results:
        v = r.get("verdict", "?")
        concern = r.get("concern", "?")
        entry = f"- **{concern}** — {v}"
        # Include issue descriptions for FAIL verdicts
        r_issues = r.get("issues", [])
        if r_issues:
            descs = [i.get("description", "?")[:80] for i in r_issues[:3]]
            entry += f": {'; '.join(descs)}"
        lines.append(entry)
    lines.append("")

    lines.append("## Test results")
    lines.append("(see verifier results above)")
    lines.append("")

    lines.append("## Issues found during check")
    all_issues = issues or []
    for r in verifier_results:
        all_issues.extend(r.get("issues", []))
    if all_issues:
        for issue in all_issues:
            sev = issue.get("severity", "?")
            desc = issue.get("description", "")
            lines.append(f"- [{sev}] {desc}")
    else:
        lines.append("none")

    return "\n".join(lines) + "\n"


def finalize_run(run_dir: str | Path) -> dict:
    """Derive final verdict from verifier results, write receipt, update manifest.

    Called on EVERY terminal path after verifiers have returned. Reads the
    manifest and all verifier result files, derives the verdict mechanically,
    writes check-state.md for PASS/FAIL, and updates check-run.json.

    For INCOMPLETE: no check-state.md is written, but the manifest is
    updated to INCOMPLETE with a failure reason. /close detects this via
    check-run.json.

    Returns:
        Dict with keys: manifest_path, receipt_path (or None), verdict,
        passed, total, status, failure_reason.

    Raises:
        FileNotFoundError: if manifest doesn't exist.
    """
    run_dir = Path(run_dir)
    manifest_path = run_dir / MANIFEST_FILENAME

    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest not found: {manifest_path}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        # Manifest corrupted — write a FINALIZE_FAILED marker if possible
        manifest = {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "session_id": "UNKNOWN",
            "run_id": run_dir.name,
            "run_dir": str(run_dir),
            "status": STATUS_FINALIZE_FAILED,
            "started_at": None,
            "finalized_at": _utc_now(),
            "receipt_path": None,
            "failure": f"manifest unreadable: {exc}",
        }
        try:
            _atomic_write_json(manifest_path, manifest)
        except OSError:
            pass  # best effort
        return {
            "manifest_path": str(manifest_path),
            "receipt_path": None,
            "verdict": "INCOMPLETE",
            "passed": 0,
            "total": 0,
            "status": STATUS_FINALIZE_FAILED,
            "failure_reason": f"manifest unreadable: {exc}",
        }

    session_id = manifest.get("session_id", "")

    # Read and validate verifier results
    verifier_results, result_errors = _read_verifier_results(run_dir)

    # Derive verdict
    verdict, passed, total, incomplete_reason = derive_verdict(verifier_results)

    # CORR-001 fix: if derivation returned PASS/FAIL but there were read errors
    # (malformed/missing verifier results), promote to INCOMPLETE. The module's
    # invariant (docstring lines 29-31) states: "Missing, malformed, or unreadable
    # verifier results produce INCOMPLETE, never PASS."
    if result_errors and verdict in ("PASS", "FAIL"):
        verdict = "INCOMPLETE"
        incomplete_reason = (
            f"verifier result errors despite {passed}/{total} valid: "
            f"{'; '.join(result_errors[:3])}"
        )

    # Combine errors with INCOMPLETE reason
    if verdict == "INCOMPLETE" and result_errors and incomplete_reason:
        incomplete_reason = (
            f"{incomplete_reason}; read errors: {'; '.join(result_errors[:3])}"
        )
    elif verdict == "INCOMPLETE" and result_errors:
        incomplete_reason = (
            f"{incomplete_reason}; read errors: {'; '.join(result_errors[:3])}"
        )

    # Collect all issues for the receipt
    all_issues = []
    for r in verifier_results:
        all_issues.extend(r.get("issues", []))

    receipt_path = None
    final_status = STATUS_COMPLETE

    if verdict in ("PASS", "FAIL"):
        # Write the receipt
        try:
            receipt_text = render_receipt(
                session_id, verdict, passed, total, verifier_results, all_issues
            )
            receipt_path = run_dir / RECEIPT_FILENAME
            _atomic_write_text(receipt_path, receipt_text)
        except OSError as exc:
            # Receipt write failed — mark as FINALIZE_FAILED
            verdict = "INCOMPLETE"
            final_status = STATUS_FINALIZE_FAILED
            incomplete_reason = f"receipt write failed: {exc}"
            receipt_path = None
    else:
        # INCOMPLETE — no receipt, but manifest records the state
        final_status = STATUS_INCOMPLETE

    # Update manifest atomically
    manifest["status"] = final_status
    manifest["finalized_at"] = _utc_now()
    manifest["receipt_path"] = str(receipt_path) if receipt_path else None
    manifest["verdict"] = verdict
    manifest["verifiers_passed"] = passed
    manifest["verifiers_total"] = total
    if verdict == "INCOMPLETE":
        manifest["failure"] = incomplete_reason

    try:
        _atomic_write_json(manifest_path, manifest)
    except OSError as exc:
        # CORR-002 fix: manifest update failed after receipt was written.
        # Delete the receipt so close scanner doesn't double-count it
        # (receipt as passed/failed AND manifest as RUNNING/incomplete).
        if receipt_path and receipt_path.exists():
            try:
                receipt_path.unlink()
            except OSError:
                pass  # best effort — the FINALIZE_FAILED status is the signal
        return {
            "manifest_path": str(manifest_path),
            "receipt_path": str(receipt_path) if receipt_path else None,
            "verdict": verdict,
            "passed": passed,
            "total": total,
            "status": STATUS_FINALIZE_FAILED,
            "failure_reason": f"manifest update failed: {exc}",
        }

    return {
        "manifest_path": str(manifest_path),
        "receipt_path": str(receipt_path) if receipt_path else None,
        "verdict": verdict,
        "passed": passed,
        "total": total,
        "status": final_status,
        "failure_reason": incomplete_reason if verdict == "INCOMPLETE" else None,
    }


def read_manifest(run_dir: str | Path) -> dict | None:
    """Read check-run.json. Returns None if not found or unreadable."""
    manifest_path = Path(run_dir) / MANIFEST_FILENAME
    if not manifest_path.exists():
        return None
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


# ---------------------------------------------------------------------------
# CLI entry points (for SKILL.md invocation)
# ---------------------------------------------------------------------------


def _cmd_start(args):
    manifest_path = start_run(args.session, args.run_dir)
    print(f"manifest written: {manifest_path}")
    return 0


def _cmd_verifier_result(args):
    issues = json.loads(args.issues) if args.issues else []
    path = write_verifier_result(
        args.run_dir, args.index, args.concern, args.verdict, issues
    )
    print(f"verifier result written: {path}")
    return 0


def _cmd_finalize(args):
    result = finalize_run(args.run_dir)
    print(
        f"finalized: verdict={result['verdict']} status={result['status']} "
        f"passed={result['passed']}/{result['total']}"
    )
    if result.get("receipt_path"):
        print(f"receipt: {result['receipt_path']}")
    if result.get("failure_reason"):
        print(f"failure: {result['failure_reason']}", file=sys.stderr)
    # Nonzero exit on INCOMPLETE or FINALIZE_FAILED so the orchestrator
    # knows finalization did not produce a clean PASS/FAIL receipt.
    if result["status"] in (STATUS_INCOMPLETE, STATUS_FINALIZE_FAILED):
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Durable /check run lifecycle manager."
    )
    sub = parser.add_subparsers(dest="cmd")

    p_start = sub.add_parser("start", help="Write run manifest at /check start")
    p_start.add_argument("--session", required=True)
    p_start.add_argument("--run-dir", required=True)
    p_start.set_defaults(func=_cmd_start)

    p_vr = sub.add_parser("verifier-result", help="Write a structured verifier result")
    p_vr.add_argument("--run-dir", required=True)
    p_vr.add_argument("--index", type=int, required=True)
    p_vr.add_argument("--concern", required=True)
    p_vr.add_argument("--verdict", required=True, choices=["PASS", "FAIL"])
    p_vr.add_argument("--issues", default="", help="JSON array of issue dicts")
    p_vr.set_defaults(func=_cmd_verifier_result)

    p_fin = sub.add_parser(
        "finalize", help="Derive verdict and write receipt + update manifest"
    )
    p_fin.add_argument("--run-dir", required=True)
    p_fin.set_defaults(func=_cmd_finalize)

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
