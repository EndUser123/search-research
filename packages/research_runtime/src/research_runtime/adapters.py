"""Platform adapters for Claude Code, Codex, and OpenCode.

Each adapter provides a `run_research(request, **kwargs)` function that:
1. Creates a research-brief.v1
2. Invokes capability routing
3. Uses platform-native provider execution
4. Writes immutable artifacts under P:\.artifacts\research\
5. Returns (artifact_paths, status)

Shared semantics, capability policy, normalisation, assessment, and artifacts
remain authoritative regardless of which adapter invokes them.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from research_runtime.brief import build_brief, write_brief
from research_runtime.router import TaskSignals, default_capabilities, recommend
from research_runtime.phase1 import run_phase1

ARTIFACT_ROOT = Path("P:/.artifacts/research")


def _session_id() -> str:
    for var in ("CLAUDE_SESSION_ID", "TERMINAL_ID", "SESSION_ID"):
        val = os.environ.get(var, "").strip()
        if val:
            return val
    return f"anon-{uuid.uuid4().hex[:8]}"


def _run_id() -> str:
    return f"rr-{uuid.uuid4().hex[:12]}"


def _resolve_workspace() -> str:
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


# ---------------------------------------------------------------------------
# Shared core — called by every adapter
# ---------------------------------------------------------------------------

def _execute_bounded_run(
    request: str,
    platform: str,
    caller: str,
    task_class: str = "lookup",
    *,
    signals_override: TaskSignals | None = None,
) -> dict[str, Any]:
    """Execute the shared research pipeline and return result metadata."""
    session = _session_id()
    run = _run_id()
    workspace = _resolve_workspace()

    # 1. Build and write immutable brief
    brief = build_brief(
        original_request=request,
        task_class=task_class,
        platform=platform,
        caller=caller,
        workspace=workspace,
        session_id=session,
        session_id_verified=_session_verified(),
        run_id=run,
    )
    brief_dir = ARTIFACT_ROOT / "briefs"
    brief_dir.mkdir(parents=True, exist_ok=True)
    brief_path = brief_dir / f"{run}.json"
    write_brief(brief, str(brief_path))

    # 2. Derive signals and route
    signals = signals_override or TaskSignals(
        needs_current_web=True,
        needs_independent_recall=True,
        agent_selected=True,
        as_of=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
    capabilities = default_capabilities()
    routing = recommend(signals, capabilities)

    if not routing.recommendations:
        return {
            "status": "no_eligible_lane",
            "run_id": run,
            "platform": platform,
            "caller": caller,
            "session_id": session,
            "brief_path": str(brief_path),
            "stop_reason": routing.stop_reason,
            "artifact_path": None,
        }

    # 3. Write bounded query plan into brief
    brief_dict = brief.to_dict()
    recommended_lane = routing.recommendations[0]
    brief_dict["planned_query_families"] = [recommended_lane.lane]
    (ARTIFACT_ROOT / "briefs" / f"{run}.json").write_text(
        json.dumps(brief_dict, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    # 4. Execute
    artifact, artifact_path = run_phase1(
        question=request,
        query=request,
        requested_decision=task_class,
        workspace_revision=workspace,
        caller=caller,
        signals=signals,
        output_root=ARTIFACT_ROOT / "runs",
    )

    return {
        "status": "completed",
        "run_id": run,
        "platform": platform,
        "caller": caller,
        "session_id": session,
        "brief_path": str(brief_path),
        "artifact_path": str(artifact_path),
        "recommended_lane": recommended_lane.lane,
    }


# ---------------------------------------------------------------------------
# Claude Code adapter
# ---------------------------------------------------------------------------

def run_claude(
    request: str,
    *,
    caller: str = "claude:/research",
    task_class: str = "lookup",
) -> dict[str, Any]:
    """Claude Code research adapter.

    Uses the shared research runtime.  The caller (SKILL.md or orchestration
    script) should invoke this via ``research_runtime.adapters.run_claude()``.
    """
    return _execute_bounded_run(request, "claude-code", caller, task_class)


# ---------------------------------------------------------------------------
# Codex adapter
# ---------------------------------------------------------------------------

def run_codex(
    request: str,
    *,
    caller: str = "codex:researcher",
    task_class: str = "lookup",
) -> dict[str, Any]:
    """Codex research adapter.

    Codex agents invoke this through a Python entrypoint (e.g. via
    ``codex run`` configured in their agent config).  Native Codex agent
    configuration (permissions, tools, agent type) wraps the call.
    """
    return _execute_bounded_run(request, "codex", caller, task_class)


# ---------------------------------------------------------------------------
# OpenCode adapter
# ---------------------------------------------------------------------------

def run_opencode(
    request: str,
    *,
    caller: str = "opencode:researcher",
    task_class: str = "lookup",
) -> dict[str, Any]:
    """OpenCode research adapter.

    OpenCode agents invoke this through a Python entrypoint.  Native OpenCode
    MCP providers (Exa, Brave, Perplexity) are re-used for provider execution
    while shared routing, assessment, and artifacts remain authoritative.
    """
    return _execute_bounded_run(request, "opencode", caller, task_class)


# ---------------------------------------------------------------------------
# CLI-invocable entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run research via platform adapter")
    parser.add_argument("platform", choices=("claude", "codex", "opencode"))
    parser.add_argument("request", help="Research request")
    args = parser.parse_args()

    adapters = {
        "claude": run_claude,
        "codex": run_codex,
        "opencode": run_opencode,
    }
    result = adapters[args.platform](args.request)
    print(json.dumps(result, indent=2))
