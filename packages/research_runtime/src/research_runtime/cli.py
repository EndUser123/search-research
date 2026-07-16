"""Neutral invocation boundary for the research-runtime package.

Accepts an original request and verified identity, then:

1. Writes an immutable research-brief.v1.
2. Invokes capability routing.
3. Dispatches through platform adapters.
4. Writes immutable artifacts under P:/.artifacts/research/.
5. Returns machine-readable artifact references and status.

Usage:
    python -m research_runtime.cli run "my question"
    python -m research_runtime.cli run "my question" --platform codex --caller my-agent
    python -m research_runtime.cli validate path/to/artifact.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from research_runtime.brief import (
    ResearchBrief,
    BriefValidationError,
    build_brief,
    write_brief,
    TASK_CLASS_LOOKUP,
    TASK_CLASS_EXPLORATION,
    TASK_CLASS_IMPLEMENTATION,
    TASK_CLASS_DECISION_SUPPORT,
    VALID_TASK_CLASSES,
)
from research_runtime.router import TaskSignals, default_capabilities, recommend
from research_runtime.phase1 import run_phase1

ARTIFACT_ROOT = Path("P:/.artifacts/research")


def _session_id() -> tuple[str, bool]:
    """Best-effort session identity from env."""
    for var in ("CLAUDE_SESSION_ID", "TERMINAL_ID", "SESSION_ID"):
        val = os.environ.get(var, "").strip()
        if val:
            return val, True
    return f"anon-{uuid.uuid4().hex[:8]}", False


def _run_id() -> str:
    return f"rr-{uuid.uuid4().hex[:12]}"


def _resolve_workspace() -> str:
    """Return git workspace root or local project path."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
            cwd=os.getcwd(),
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return os.getcwd()


def cmd_run(args: argparse.Namespace) -> int:
    """Execute a complete research run from request to artifact."""
    request = args.request
    platform = args.platform
    caller = args.caller
    task_class = args.task_class

    # --- Identity ---
    if args.session_id:
        session = args.session_id
        session_verified = True
    else:
        raw_sid, session_verified = _session_id()
        session = raw_sid
    run = _run_id()
    workspace = _resolve_workspace()

    # --- 1. Build and write research-brief.v1 ---
    brief = build_brief(
        original_request=request,
        task_class=task_class,
        platform=platform,
        caller=caller,
        workspace=workspace,
        session_id=session,
        session_id_verified=session_verified,
        run_id=run,
    )
    brief_dir = ARTIFACT_ROOT / "briefs"
    brief_dir.mkdir(parents=True, exist_ok=True)
    brief_path = brief_dir / f"{run}.json"

    # Exclusive-create: if it exists (uuid collision ~0), fail.
    if brief_path.exists():
        print(f"ERROR: brief path already exists: {brief_path}", file=sys.stderr)
        return 2

    write_brief(brief, str(brief_path))
    print(f"BRIEF: {brief_path}")

    # --- 2. Derive capability signals from brief ---
    signals = TaskSignals(
        needs_current_web=True,
        needs_independent_recall=True,
        needs_primary_source_verification=bool(
            args.source_priority == "authoritative"
        ),
        requested_roles=frozenset(
            role.strip() for role in args.roles.split(",") if role.strip()
        ) if args.roles else frozenset(),
        decision_impact=args.impact,
        sensitivity=args.sensitivity,
        authorization_level="evidence_gathering",
        agent_selected=True,
        as_of=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )

    # --- 3. Invoke capability routing ---
    capabilities = default_capabilities()
    routing = recommend(signals, capabilities)

    if not routing.recommendations:
        print(f"WARN: no eligible lane — {routing.stop_reason}", file=sys.stderr)
        if routing.human_escalation:
            print(f"ESCALATION: {', '.join(routing.escalation_reasons)}", file=sys.stderr)
        # Return partial result — no run artifact, just brief.
        print(f"STATUS: no_eligible_lane")
        print(f"RUN: {run}")
        return 1

    recommended_lane = routing.recommendations[0]
    print(f"LANE: {recommended_lane.lane} (score={recommended_lane.score})")

    # Record planned queries in brief
    import json as _json
    brief_dict = brief.to_dict()
    brief_dict["planned_query_families"] = [
        f"{recommended_lane.lane}:{role}" for role in signals.requested_roles
    ] if signals.requested_roles else [f"{recommended_lane.lane}:default"]

    # Update brief JSON with query plan
    brief_path.write_text(
        _json.dumps(brief_dict, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    # --- 4. Execute through platform adapter ---
    artifact, artifact_path = run_phase1(
        question=request,
        query=request,
        requested_decision=task_class,
        workspace_revision=workspace,
        caller=caller,
        signals=signals,
        output_root=ARTIFACT_ROOT / "runs",
    )
    print(f"ARTIFACT: {artifact_path}")

    # --- 5. Return status ---
    print(f"STATUS: completed")
    print(f"RUN: {run}")
    print(f"PLATFORM: {platform}")
    print(f"CALLER: {caller}")
    print(f"SESSION: {session}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate an artifact against its schema."""
    path = Path(args.path)
    if not path.exists():
        print(f"ERROR: not found: {path}", file=sys.stderr)
        return 1

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: cannot read: {exc}", file=sys.stderr)
        return 1

    schema = data.get("schema", "")
    if not schema:
        print(f"ERROR: no schema field in {path}", file=sys.stderr)
        return 1

    errors: list[str] = []

    if schema == "research-brief.v1":
        from research_runtime.brief import brief_from_dict, BriefValidationError
        try:
            brief_from_dict(data)
        except BriefValidationError as exc:
            errors.extend(exc.errors)
    elif schema in ("research-run.v1",):
        from research_runtime.validator import validate
        try:
            validate(data)
        except Exception as exc:
            errors.append(str(exc))
    elif schema == "research-result.v1":
        from research_runtime.research_result import validate as validate_rr
        try:
            validate_rr(data)
        except Exception as exc:
            errors.append(str(exc))
    elif schema == "decision-request.v1":
        from research_runtime.decision_request import validate as validate_dr
        try:
            validate_dr(data)
        except Exception as exc:
            errors.append(str(exc))
    elif schema == "decision-result.v1":
        from research_runtime.decision_result import validate as validate_dres
        try:
            validate_dres(data)
        except Exception as exc:
            errors.append(str(exc))
    else:
        errors.append(f"unknown schema: {schema}")

    if errors:
        print(f"INVALID ({schema}):")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"VALID ({schema}): {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Provider-neutral research runtime (research-runtime)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # run
    run_p = sub.add_parser("run", help="Execute a complete research run")
    run_p.add_argument("request", help="Original research request")
    run_p.add_argument("--platform", default="claude-code",
                       choices=("claude-code", "codex", "opencode"),
                       help="Target platform identity")
    run_p.add_argument("--caller", default="cli",
                       help="Caller identity (skill name, agent name, etc.)")
    run_p.add_argument("--task-class", default=TASK_CLASS_LOOKUP,
                       choices=tuple(VALID_TASK_CLASSES),
                       help="Classification of the research task")
    run_p.add_argument("--source-priority", default="authoritative",
                       help="Source priority tier")
    run_p.add_argument("--roles", default="",
                       help="Comma-separated role identifiers")
    run_p.add_argument("--impact", default="low",
                       choices=("low", "medium", "high", "critical"),
                       help="Decision impact level")
    run_p.add_argument("--sensitivity", default="normal",
                       choices=("normal", "sensitive", "credentialed"),
                       help="Request sensitivity")
    run_p.add_argument("--session-id", default="",
                       help="Override session identity")
    run_p.set_defaults(func=cmd_run)

    # validate
    val_p = sub.add_parser("validate", help="Validate a research artifact")
    val_p.add_argument("path", help="Path to artifact JSON file")
    val_p.set_defaults(func=cmd_validate)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
