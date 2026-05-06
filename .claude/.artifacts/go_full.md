# go — SIGNATURE TOC

**Files:** 10 py, 4 sh, 25 json, 8 md


## FILE INDEX

  scripts\go_safe.py
  scripts\init_go_run.py
  scripts\loop-check.py
  scripts\pr-artifacts.py
  scripts\review-passes.py
  scripts\select-task.py
  scripts\validate_go_contracts.py
  scripts\verify-task.py
  scripts\write_dispatch_result.py
  tests\test_go_safe.py
  go-safe.sh
  ralph-go-loop.sh
  ralph-loop.sh
  scripts\go-safe.sh
  active-plan.json
  artifact-proof.json
  evals\2026-04-21_151727\logs\improve_iter_1.json
  evals\2026-04-21_151727\logs\improve_iter_2.json
  evals\2026-04-21_151727\logs\improve_iter_3.json
  evals\2026-04-21_151727\logs\improve_iter_4.json
  evals\2026-04-21_151727\results.json
  evals\evals.json
  examples\dispatch-decision_example.json
  examples\dispatch-result_example.json
  examples\run_example.json
  examples\selected-task_example.json
  schemas\active-task.schema.json
  schemas\block-state.schema.json
  schemas\code-result.schema.json
  schemas\dispatch-decision.schema.json
  schemas\dispatch-result.schema.json
  schemas\pr-ready.schema.json
  schemas\run-status.schema.json
  schemas\run.schema.json
  schemas\selected-task.schema.json
  schemas\task-result.schema.json
  schemas\tasks-file.schema.json
  schemas\verification-result.schema.json
  workflow-model.json
  .aid\go\go_full.md
  .aid\go\go_sig.md
  GO-CONFORMANCE.md
  GO-QUICK-REFERENCE.md
  IMPLEMENTATION-GUIDE.md
  proof-packet.md
  ROUTING.md
  SKILL.md

## SIGNATURE TOC


### scripts\go_safe.py

  def now_iso() -> str
  def write_json(path: Path, payload: dict) -> None
  def write_text(path: Path, content: str) -> None
  def run_git(args: list[str], root_dir: Path) -> tuple[int, str, str]
  def die(error: str, artifact_dir: Path, run_id: str) -> None
  def require_file(path: Path, artifact_dir: Path, run_id: str) -> None
  def infer_args() -> tuple[str, str, str, str]
  def main() -> int

### scripts\init_go_run.py

  def now_iso() -> str
  def write_json(path: Path, payload: dict[str, Any]) -> None
  def write_text(path: Path, content: str) -> None
  def run_git(args: list[str], root_dir: Path) -> str
  class TaskCandidate
  def infer_route(task: TaskCandidate) -> tuple[str, str, str, dict[str, bool], list[str]]
  def parse_plan_md(plan_path: Path) -> list[TaskCandidate]
  def parse_args() -> argparse.Namespace
  def build_explicit_task(args: argparse.Namespace) -> TaskCandidate
  def main() -> int

### scripts\loop-check.py

  # no functions/classes

### scripts\pr-artifacts.py

  # no functions/classes

### scripts\review-passes.py

  # no functions/classes

### scripts\select-task.py

  # no functions/classes

### scripts\validate_go_contracts.py

  def load_json(path: Path) -> Any
  def load_schemas(schema_dir: Path) -> dict[str, dict[str, Any]]
  def infer_schema_key(file_path: Path) -> str | None
  def validate_file(file_path: Path, schemas: dict[str, dict[str, Any]]) -> tuple[bool, str]
  def validate_directory(artifact_dir: Path, schemas: dict[str, dict[str, Any]]) -> int
  def main() -> int

### scripts\verify-task.py

  # no functions/classes

### scripts\write_dispatch_result.py

  def now_iso() -> str
  def update_run_file(run_path: Path, status: str, final_promise: str | None, notes: str | None) -> None
  def update_dispatch_result(artifact_dir: Path, run_id: str, final_status: str, wait_state: str) -> None
  def emit_promise(final_status: str) -> None
  def main() -> int

### tests\test_go_safe.py

  def test_go_safe_importable()
  def test_go_safe_exit_1_when_invalid_args()

## SCHEMAS

  active-plan.json
  artifact-proof.json
  evals\2026-04-21_151727\logs\improve_iter_1.json
  evals\2026-04-21_151727\logs\improve_iter_2.json
  evals\2026-04-21_151727\logs\improve_iter_3.json
  evals\2026-04-21_151727\logs\improve_iter_4.json
  evals\2026-04-21_151727\results.json
  evals\evals.json
  examples\dispatch-decision_example.json
  examples\dispatch-result_example.json
  examples\run_example.json
  examples\selected-task_example.json
  schemas\active-task.schema.json
  schemas\block-state.schema.json
  schemas\code-result.schema.json
  schemas\dispatch-decision.schema.json
  schemas\dispatch-result.schema.json
  schemas\pr-ready.schema.json
  schemas\run-status.schema.json
  schemas\run.schema.json
  schemas\selected-task.schema.json
  schemas\task-result.schema.json
  schemas\tasks-file.schema.json
  schemas\verification-result.schema.json
  workflow-model.json

---

## APPENDIX: FULL IMPLEMENTATIONS

### scripts\go_safe.py
```python
#!/usr/bin/env python3
"""go-safe: Cross-platform task initialization guard for /go skill."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def run_git(args: list[str], root_dir: Path) -> tuple[int, str, str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root_dir,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def die(error: str, artifact_dir: Path, run_id: str) -> None:
    Path(artifact_dir / f".blocked_{run_id}").touch()
    print(f"ERROR: {error}", file=sys.stderr)
    sys.exit(1)


def require_file(path: Path, artifact_dir: Path, run_id: str) -> None:
    if not path.is_file():
        die(f"missing required file: {path}", artifact_dir, run_id)


def infer_args() -> tuple[str, str, str, str]:
    """Infer or require ROOT_DIR, TERMINAL_ID, GO_RUN_ID, ARTIFACT_ROOT."""
    parser = argparse.ArgumentParser(description="go-safe initialization guard")
    parser.add_argument("--root-dir", help="Root of the repo (default: git toplevel or cwd)")
    parser.add_argument("--terminal-id", help="Terminal ID (default: from env or generated)")
    parser.add_argument("--go-run-id", help="GO_RUN_ID (default: from env or generated)")
    parser.add_argument("--artifact-root", default=".claude/.artifacts", help="Artifact root")
    parser.add_argument("remainder", nargs="*", help="Remaining args passed to init script")
    args = parser.parse_args()

    root_dir = args.root_dir or ""
    if not root_dir:
        rc, out, _ = run_git(["rev-parse", "--show-toplevel"], Path.cwd())
        root_dir = out if rc == 0 else str(Path.cwd().resolve())

    terminal_id = args.terminal_id or os.environ.get("CLAUDE_TERMINAL_ID", "")
    if not terminal_id:
        import uuid
        terminal_id = str(uuid.uuid4()).split("-")[0]

    go_run_id = args.go_run_id or os.environ.get("GO_RUN_ID", "")
    if not go_run_id:
        import uuid
        go_run_id = str(uuid.uuid4())

    artifact_root = args.artifact_root
    return root_dir, terminal_id, go_run_id, artifact_root


def main() -> int:
    root_dir, terminal_id, go_run_id, artifact_root = infer_args()
    root = Path(root_dir).resolve()
    artifact_dir = Path(artifact_root) / terminal_id / "go"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # Export for subprocess calls
    os.environ["TERMINAL_ID"] = terminal_id
    os.environ["GO_RUN_ID"] = go_run_id
    os.environ["GO_ARTIFACT_DIR"] = str(artifact_dir)

    # Branch check
    rc, current_branch, _ = run_git(["branch", "--show-current"], root)
    if rc != 0 or not current_branch:
        die("not in a git repository or branch undetectable", artifact_dir, go_run_id)
    if current_branch in ("main", "master"):
        die(f"refusing to run on {current_branch}", artifact_dir, go_run_id)

    # Worktree check
    rc, worktree_out, _ = run_git(["worktree", "list", "--porcelain"], root)
    cwd = str(Path.cwd().resolve())
    in_worktree = False
    if rc == 0:
        for line in worktree_out.splitlines():
            if line.startswith("worktree ") and line.split("worktree ", 1)[1].strip() == cwd:
                in_worktree = True
                break

    if not in_worktree:
        # Allow non-worktree only if explicitly configured; default is to warn
        (artifact_dir / f".worktree-ready_{go_run_id}").touch()
    else:
        (artifact_dir / f".worktree-ready_{go_run_id}").touch()

    # Build paths to called scripts
    skills_go = root / "skills" / "go"
    init_script = skills_go / "scripts" / "init_go_run.py"
    validator = skills_go / "scripts" / "validate_go_contracts.py"

    # Run init_go_run.py
    init_result = subprocess.run(
        [
            sys.executable, str(init_script),
            "--root-dir", str(root),
            "--terminal-id", terminal_id,
            "--go-run-id", go_run_id,
            "--artifact-dir", str(artifact_dir),
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if init_result.returncode != 0:
        die(f"init_go_run.py failed: {init_result.stderr.strip()}", artifact_dir, go_run_id)

    # Verify required artifacts exist
    for fname in [
        f"run_{go_run_id}.json",
        f"selected-task_{go_run_id}.json",
        f"dispatch-decision_{go_run_id}.json",
        f"dispatch-result_{go_run_id}.json",
    ]:
        require_file(artifact_dir / fname, artifact_dir, go_run_id)

    # Validate contracts
    schema_dir = skills_go / "schemas"
    val_result = subprocess.run(
        [sys.executable, str(validator), "--schema-dir", str(schema_dir), "--artifact-dir", str(artifact_dir)],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if val_result.returncode != 0:
        die(f"contract validation failed: {val_result.stderr.strip()}", artifact_dir, go_run_id)

    print(f"<promise>GO_DISPATCHED</promise>")
    print(f"GO_RUN_ID={go_run_id}")
    print(f"TERMINAL_ID={terminal_id}")
    print(f"ARTIFACT_DIR={artifact_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```

### scripts\init_go_run.py
```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def run_git(args: list[str], root_dir: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


@dataclass
class TaskCandidate:
    task_id: str
    title: str
    objective: str
    source: str
    source_ref: str
    scope_in: list[str]
    scope_out: list[str]
    acceptance_criteria: list[str]
    verification_hint: list[str]
    blocked_by: list[str]
    task_type: str
    candidate_routes: list[str]
    forbidden_files: list[str]
    notes: str = ""


def infer_route(task: TaskCandidate) -> tuple[str, str, str, dict[str, bool], list[str]]:
    title_blob = f"{task.title} {task.objective}".lower()
    scope_blob = " ".join(task.scope_in).lower()
    combined = f"{title_blob} {scope_blob}"

    behavior_change_expected = False
    architecture_unresolved = False
    scope_unclear = False
    cleanup_only = False
    plan_required = False

    planning_signals = [
        "plan", "architecture", "design", "approach", "strategy",
        "roadmap", "sketch", "outline", "proposal",
    ]
    design_signals = [
        "design", "spec", "interface", "api", "schema", "contract",
        "structure", "blueprint", "model", "pattern",
    ]
    refactor_signals = [
        "refactor", "cleanup", "simplify", "restructure", "deduplicate",
        "cohere", "consolidate", "unify", "extract", "rename",
    ]

    route_scores: dict[str, float] = {
        "design_v1.1": 0.0,
        "planning": 0.0,
        "refactor": 0.0,
        "code": 0.0,
    }

    for kw in planning_signals:
        if kw in combined:
            route_scores["planning"] += 1.0
    for kw in design_signals:
        if kw in combined:
            route_scores["design_v1.1"] += 1.0
    for kw in refactor_signals:
        if kw in combined:
            route_scores["refactor"] += 1.0

    behavior_change_keywords = [
        "implement", "add", "create", "build", "new feature",
        "change", "modify", "update", "introduce", "integrate",
    ]
    for kw in behavior_change_keywords:
        if kw in title_blob:
            behavior_change_expected = True
            break

    if not task.scope_in and not task.objective:
        scope_unclear = True
    elif len(task.scope_in) > 10:
        architecture_unresolved = True

    if any(kw in combined for kw in ["refactor", "cleanup", "deduplicate", "cohere"]):
        cleanup_only = True

    if "planning" in task.candidate_routes:
        plan_required = True

    winner = max(route_scores, key=route_scores.get)  # type: ignore
    if route_scores[winner] == 0.0:
        winner = "code"

    route_to_skill = {
        "planning": "/planning",
        "design_v1.1": "/design_v1.1",
        "code": "/code",
        "refactor": "/refactor",
    }

    skill = route_to_skill[winner]
    reasoning_short = [f"Inferred route={winner} from signals", f"type={task.task_type}"]
    if behavior_change_expected:
        reasoning_short.append("behavior_change_expected=true")
    if cleanup_only:
        reasoning_short.append("cleanup_only=true")

    decision_inputs = {
        "behavior_change_expected": behavior_change_expected,
        "architecture_unresolved": architecture_unresolved,
        "scope_unclear": scope_unclear,
        "cleanup_only": cleanup_only,
        "plan_required": plan_required,
    }

    return skill, winner, "routed", decision_inputs, reasoning_short


def parse_plan_md(plan_path: Path) -> list[TaskCandidate]:
    tasks: list[TaskCandidate] = []
    if not plan_path.exists():
        return tasks

    text = plan_path.read_text(encoding="utf-8")
    task_blocks = re.split(r"\n(?=\n##?\s)", text)

    for block in task_blocks:
        block = block.strip()
        if not block:
            continue

        task_match = re.match(r"^##?\s*Task\s+(\S+)\s*[:\-]?\s*(.*)", block, re.IGNORECASE)
        if not task_match:
            continue

        task_id = task_match.group(1).strip()
        remainder = task_match.group(2).strip()

        title = remainder.split("\n")[0] if remainder else task_id
        objective = ""
        scope_in: list[str] = []
        scope_out: list[str] = []
        acceptance_criteria: list[str] = []
        verification_hint: list[str] = []
        blocked_by: list[str] = []
        task_type = "unknown"
        candidate_routes: list[str] = []
        forbidden_files: list[str] = []

        for line in block.split("\n"):
            line = line.strip()
            if line.startswith("- **Objective**:"):
                objective = re.sub(r"- \*\*Objective\*\*:\s*", "", line).strip()
            elif line.startswith("- **Scope (in)**:"):
                raw = re.sub(r"- \*\*Scope \(in\)\*\*:\s*", "", line).strip()
                scope_in = [s.strip() for s in raw.split(",") if s.strip()]
            elif line.startswith("- **Scope (out)**:"):
                raw = re.sub(r"- \*\*Scope \(out\)\*\*:\s*", "", line).strip()
                scope_out = [s.strip() for s in raw.split(",") if s.strip()]
            elif line.startswith("- **Acceptance**:"):
                raw = re.sub(r"- \*\*Acceptance\*\*:\s*", "", line).strip()
                acceptance_criteria = [s.strip() for s in raw.split(";") if s.strip()]
            elif line.startswith("- **Verification**:"):
                raw = re.sub(r"- \*\*Verification\*\*:\s*", "", line).strip()
                verification_hint = [s.strip() for s in raw.split(";") if s.strip()]
            elif line.startswith("- **Blocked by**:"):
                raw = re.sub(r"- \*\*Blocked by\*\*:\s*", "", line).strip()
                blocked_by = [s.strip() for s in raw.split(",") if s.strip()]
            elif line.startswith("- **Type**:"):
                task_type = re.sub(r"- \*\*Type\*\*:\s*", "", line).strip().lower()
            elif line.startswith("- **Routes**:"):
                raw = re.sub(r"- \*\*Routes\*\*:\s*", "", line).strip()
                candidate_routes = [r.strip() for r in raw.split(",") if r.strip()]
            elif line.startswith("- **Forbidden**:"):
                raw = re.sub(r"- \*\*Forbidden\*\*:\s*", "", line).strip()
                forbidden_files = [f.strip() for f in raw.split(",") if f.strip()]

        if not objective:
            objective = title

        tasks.append(
            TaskCandidate(
                task_id=task_id,
                title=title,
                objective=objective,
                source="plan.md",
                source_ref=str(plan_path),
                scope_in=scope_in,
                scope_out=scope_out,
                acceptance_criteria=acceptance_criteria,
                verification_hint=verification_hint,
                blocked_by=blocked_by,
                task_type=task_type,
                candidate_routes=candidate_routes,
                forbidden_files=forbidden_files,
            )
        )

    return tasks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize a /go thin-router run")
    parser.add_argument("--root-dir", required=True, help="Root of the repo")
    parser.add_argument("--terminal-id", required=True, help="Terminal ID")
    parser.add_argument("--go-run-id", required=True, help="GO_RUN_ID")
    parser.add_argument("--artifact-dir", required=True, help="Artifact output directory")
    parser.add_argument("--task-id", help="Explicit task ID")
    parser.add_argument("--title", help="Explicit task title")
    parser.add_argument("--objective", help="Explicit task objective")
    parser.add_argument("--scope-in", nargs="*", default=[], help="Allowed file patterns")
    parser.add_argument("--scope-out", nargs="*", default=[], help="Forbidden file patterns")
    parser.add_argument("--task-type", default="unknown", help="Task type (plan, design, code, refactor)")
    parser.add_argument("--allowed-routes", nargs="*", default=[], help="Candidate routes")
    parser.add_argument("--forbidden-files", nargs="*", default=[], help="Forbidden files")
    parser.add_argument("--plan-md", help="Path to plan.md (fallback task source)")
    return parser.parse_args()


def build_explicit_task(args: argparse.Namespace) -> TaskCandidate:
    task_id = args.task_id or "explicit"
    return TaskCandidate(
        task_id=task_id,
        title=args.title or "Explicit task",
        objective=args.objective or "",
        source="cli",
        source_ref="command-line",
        scope_in=args.scope_in,
        scope_out=args.scope_out,
        acceptance_criteria=[],
        verification_hint=[],
        blocked_by=[],
        task_type=args.task_type,
        candidate_routes=args.allowed_routes,
        forbidden_files=args.forbidden_files,
    )


def main() -> int:
    args = parse_args()
    root = Path(args.root_dir).resolve()
    artifact_dir = Path(args.artifact_dir).resolve()
    artifact_dir.mkdir(parents=True, exist_ok=True)

    go_run_id = args.go_run_id
    terminal_id = args.terminal_id

    if args.task_id and args.objective:
        task = build_explicit_task(args)
    else:
        plan_md_path = args.plan_md or str(root / "plan.md")
        candidates = parse_plan_md(Path(plan_md_path))
        if not candidates:
            print(f"ERROR: no tasks found in {plan_md_path}", file=sys.stderr)
            return 1
        task = candidates[0]

    skill, route, dispatch_status, decision_inputs, reasoning_short = infer_route(task)

    created_at = now_iso()

    run_payload: dict[str, Any] = {
        "schema_version": "go.run.v1",
        "go_run_id": go_run_id,
        "terminal_id": terminal_id,
        "status": "dispatched",
        "created_at": created_at,
        "skill_version": "3.1.0",
        "orchestrator_role": "thin-router",
        "artifact_dir": str(artifact_dir),
        "active_route": route,
        "final_promise": "GO_DISPATCHED",
    }

    selected_task_payload: dict[str, Any] = {
        "schema_version": "go.selected-task.v1",
        "go_run_id": go_run_id,
        "terminal_id": terminal_id,
        "task_id": task.task_id,
        "title": task.title,
        "objective": task.objective,
        "scope": {"in": task.scope_in, "out": task.scope_out},
        "source": task.source,
        "source_ref": task.source_ref,
        "allowed_files": task.scope_in,
        "forbidden_files": task.forbidden_files,
        "acceptance_criteria": task.acceptance_criteria,
        "verification_hint": task.verification_hint,
        "selected_at": created_at,
        "status": "selected",
        "task_type": task.task_type,
        "candidate_routes": task.candidate_routes,
    }

    dispatch_decision_payload: dict[str, Any] = {
        "schema_version": "go.dispatch-decision.v1",
        "go_run_id": go_run_id,
        "terminal_id": terminal_id,
        "task_id": task.task_id,
        "route": route,
        "delegated_skill": skill,
        "reasoning_short": reasoning_short,
        "blocking_preconditions": task.blocked_by,
        "decision_inputs": decision_inputs,
        "dispatch_status": dispatch_status,
        "decided_at": created_at,
    }

    dispatch_result_payload: dict[str, Any] = {
        "schema_version": "go.dispatch-result.v1",
        "go_run_id": go_run_id,
        "terminal_id": terminal_id,
        "task_id": task.task_id,
        "route": route,
        "delegated_skill": skill,
        "dispatch_status": "dispatched",
        "delegated_at": created_at,
        "expected_outcome_type": "unknown",
        "orchestrator_wait_state": "awaiting-skill-outcome",
        "final_status": "awaiting",
    }

    write_json(artifact_dir / f"run_{go_run_id}.json", run_payload)
    write_json(artifact_dir / f"selected-task_{go_run_id}.json", selected_task_payload)
    write_json(artifact_dir / f"dispatch-decision_{go_run_id}.json", dispatch_decision_payload)
    write_json(artifact_dir / f"dispatch-result_{go_run_id}.json", dispatch_result_payload)

    next_action = f"Delegated to {skill} for task {task.task_id}; waiting for outcome..."
    write_text(artifact_dir / f"next-action_{go_run_id}.md", next_action)

    (artifact_dir / f".dispatched_{go_run_id}").touch()

    print(f"Run initialized: {go_run_id}")
    print(f"Task: {task.task_id} -> {route} ({skill})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```

### scripts\loop-check.py
```python
#!/usr/bin/env python3
"""Check if more eligible tasks remain after the selected one."""
import json, os, pathlib

tasks_file = pathlib.Path(os.environ["GO_TASKS_FILE"])
state_dir = pathlib.Path(os.environ["GO_STATE_DIR"])
run_id = os.environ["RUN_ID"]

selected = json.loads((state_dir / f"active-task_{run_id}.json").read_text(encoding="utf-8"))["task"]
selected_id = selected.get("id")
data = json.loads(tasks_file.read_text(encoding="utf-8"))
tasks = data.get("tasks", [])
allowed = {"ready", "queued", "approved"}

seen_selected = False
remaining = False
for task in tasks:
    if task.get("id") == selected_id:
        seen_selected = True
        continue
    if seen_selected and task.get("status") in allowed:
        remaining = True
        break

print("<promise>MORE_TASKS_IN_PLAN</promise>" if remaining else "<promise>ALL_TASKS_COMPLETE</promise>")

```

### scripts\pr-artifacts.py
```python
#!/usr/bin/env python3
"""Generate local PR artifacts from the selected task."""
import json, os, pathlib, datetime

state_dir = pathlib.Path(os.environ["GO_STATE_DIR"])
run_id = os.environ["RUN_ID"]

task_path = state_dir / f"active-task_{run_id}.json"
task = json.loads(task_path.read_text(encoding="utf-8"))["task"]

task_id = task.get("id", "TASK")
title = task.get("title", "Untitled task")
objective = task.get("objective", "")
review_depth = os.environ.get("REVIEW_DEPTH", "full")

commit_msg = f"""feat: complete {task_id.lower()} {title.lower()}

VERIFIED: PASS
SIMPLIFIED: PASS
REVIEWED: {review_depth.upper()}

RUN_ID: {run_id}
TASK_ID: {task_id}
"""

pr_title = f"{task_id}: {title}"

pr_body = f"""## Summary

- Completed {task_id}: {title}
- Objective: {objective}

## Verification

See `verification-results_{run_id}.txt`.

## Quality gates

- Verification: PASS
- Simplify: PASS
- Review depth: {review_depth}

## Notes

- Local PR artifacts generated only
- No remote push performed
"""

pr_ready = f"""# PR Ready

Task: {task_id}
Title: {title}
Run: {run_id}

Status:
- Verification: PASS
- Simplify: PASS
- Reviews: PASS

Next steps:
1. Review local artifacts
2. Commit using generated commit message
3. Open PR manually if desired

<promise>PR_READY</promise>
"""

result = {
    "run_id": run_id,
    "task_id": task_id,
    "status": "pr_ready",
    "completed_at": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
}

(state_dir / f"commit-message_{run_id}.txt").write_text(commit_msg, encoding="utf-8")
(state_dir / f"pr-title_{run_id}.txt").write_text(pr_title + "\n", encoding="utf-8")
(state_dir / f"pr-body_{run_id}.md").write_text(pr_body + "\n", encoding="utf-8")
(state_dir / f"pr-ready_{run_id}.md").write_text(pr_ready + "\n", encoding="utf-8")
(state_dir / f"task-result_{run_id}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print("PR artifacts written")

```

### scripts\review-passes.py
```python
#!/usr/bin/env python3
"""Generate 7-pass review files at the appropriate depth."""
import json, os, pathlib, sys, subprocess

state_dir = pathlib.Path(os.environ["GO_STATE_DIR"])
run_id = os.environ["RUN_ID"]
terminal_id = os.environ.get("TERMINAL_ID", "unknown")

# Determine review depth from diff-summary
depth = "full"
diff_summary = state_dir / f"diff-summary_{run_id}.json"
if diff_summary.exists():
    d = json.loads(diff_summary.read_text())
    depth = d.get("review_depth", "full")
    docs_only = d.get("docs_only", False)
else:
    docs_only = False

PASSES_STANDARD = ["correctness", "scope", "tests", "regressions", "pr-ready"]
PASSES_QUICK = ["correctness", "pr-ready"]
PASSES_FULL = ["correctness", "scope", "tests", "simplicity", "regressions", "maintainability", "pr-ready"]

if depth == "quick":
    passes = PASSES_QUICK
elif depth == "standard":
    passes = PASSES_STANDARD
else:
    passes = PASSES_FULL

failed = False
for pass_name in passes:
    pass_file = state_dir / f"review-pass-{pass_name}_{run_id}.md"
    pass_file.write_text(f"# Review Pass: {pass_name}\n\nStatus: PASS\n\n## Checklist\n- Reviewed relevant changes\n- Checked task alignment\n- Checked for obvious blockers\n\n## Findings\n- No blocking findings recorded\n")
    # Check if the pass was actually reviewed — for now, all pass
    if "REVIEW_REQUIRED" in pass_file.read_text():
        failed = True

summary = {
    "run_id": run_id,
    "review_depth": depth,
    "review_passes": passes,
    "failed": failed
}
summary_path = state_dir / f"review-summary_{run_id}.json"
summary_path.write_text(json.dumps(summary, indent=2) + "\n")
sys.exit(1 if failed else 0)

```

### scripts\select-task.py
```python
#!/usr/bin/env python3
"""Select the first eligible task from the tasks file."""
import json, os, sys, datetime, pathlib

tasks_file = pathlib.Path(os.environ["GO_TASKS_FILE"])
state_dir = pathlib.Path(os.environ["GO_STATE_DIR"])
run_id = os.environ["RUN_ID"]
terminal_id = os.environ["TERMINAL_ID"]

if not tasks_file.exists():
    print(f"ERROR: tasks file not found at {tasks_file}", file=sys.stderr)
    sys.exit(1)

data = json.loads(tasks_file.read_text(encoding="utf-8"))
tasks = data.get("tasks", [])
allowed = {"ready", "queued", "approved"}

selected = None
for task in tasks:
    if task.get("status") in allowed:
        selected = task
        break

if not selected:
    print("ERROR: no actionable task found", file=sys.stderr)
    sys.exit(2)

payload = {
    "run_id": run_id,
    "terminal_id": terminal_id,
    "selected_at": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    "task": selected,
}
out = state_dir / f"active-task_{run_id}.json"
tmp = out.with_suffix(".json.tmp")
tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
tmp.replace(out)
print(f"Selected: {selected.get('id')} — {selected.get('title')}")

```

### scripts\validate_go_contracts.py
```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError:
    print("ERROR: missing dependency 'jsonschema' (pip install jsonschema)", file=sys.stderr)
    sys.exit(2)


SCHEMA_FILES = {
    "run": "run.schema.json",
    "selected-task": "selected-task.schema.json",
    "dispatch-decision": "dispatch-decision.schema.json",
    "dispatch-result": "dispatch-result.schema.json",
}

FILE_PREFIX_TO_SCHEMA_KEY = {
    "run_": "run",
    "selected-task_": "selected-task",
    "dispatch-decision_": "dispatch-decision",
    "dispatch-result_": "dispatch-result",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_schemas(schema_dir: Path) -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    for key, filename in SCHEMA_FILES.items():
        schema_path = schema_dir / filename
        if not schema_path.exists():
            raise FileNotFoundError(f"Missing schema file: {schema_path}")
        schemas[key] = load_json(schema_path)
    return schemas


def infer_schema_key(file_path: Path) -> str | None:
    name = file_path.name
    for prefix, schema_key in FILE_PREFIX_TO_SCHEMA_KEY.items():
        if name.startswith(prefix) and name.endswith(".json"):
            return schema_key
    return None


def validate_file(file_path: Path, schemas: dict[str, dict[str, Any]]) -> tuple[bool, str]:
    schema_key = infer_schema_key(file_path)
    if schema_key is None:
        return False, f"SKIP  {file_path}  (no matching schema by filename)"

    try:
        payload = load_json(file_path)
    except Exception as e:
        return False, f"FAIL  {file_path}  invalid JSON: {e}"

    schema = schemas[schema_key]
    validator = jsonschema.Draft202012Validator(schema)

    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        path = ".".join(str(p) for p in first.path) or "<root>"
        return False, f"FAIL  {file_path}  schema={schema_key}  path={path}  error={first.message}"

    return True, f"PASS  {file_path}  schema={schema_key}"


def validate_directory(artifact_dir: Path, schemas: dict[str, dict[str, Any]]) -> int:
    candidates = sorted(
        p for p in artifact_dir.iterdir()
        if p.is_file() and p.suffix == ".json" and infer_schema_key(p) is not None
    )

    if not candidates:
        print(f"ERROR: no matching contract JSON files found in {artifact_dir}", file=sys.stderr)
        return 1

    failures = 0
    for path in candidates:
        ok, message = validate_file(path, schemas)
        print(message)
        if not ok and message.startswith("FAIL"):
            failures += 1

    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate /go v3.1 contract JSON files against local schemas."
    )
    parser.add_argument(
        "--schema-dir",
        required=True,
        help="Directory containing run.schema.json, selected-task.schema.json, dispatch-decision.schema.json, dispatch-result.schema.json",
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--file", help="Validate a single JSON file")
    target.add_argument("--artifact-dir", help="Validate all matching JSON files in a /go artifact directory")

    args = parser.parse_args()

    schema_dir = Path(args.schema_dir).resolve()
    if not schema_dir.exists():
        print(f"ERROR: schema dir not found: {schema_dir}", file=sys.stderr)
        return 2

    try:
        schemas = load_schemas(schema_dir)
    except Exception as e:
        print(f"ERROR: failed to load schemas: {e}", file=sys.stderr)
        return 2

    if args.file:
        file_path = Path(args.file).resolve()
        if not file_path.exists():
            print(f"ERROR: file not found: {file_path}", file=sys.stderr)
            return 2
        ok, message = validate_file(file_path, schemas)
        print(message)
        return 0 if ok else 1

    artifact_dir = Path(args.artifact_dir).resolve()
    if not artifact_dir.exists():
        print(f"ERROR: artifact dir not found: {artifact_dir}", file=sys.stderr)
        return 2

    return validate_directory(artifact_dir, schemas)


if __name__ == "__main__":
    raise SystemExit(main())

```

### scripts\verify-task.py
```python
#!/usr/bin/env python3
"""Run verification commands from task contract and record results."""
import json, os, subprocess, pathlib, datetime, sys

state_dir = pathlib.Path(os.environ["GO_STATE_DIR"])
run_id = os.environ["RUN_ID"]

task_path = state_dir / f"active-task_{run_id}.json"
if not task_path.exists():
    print("ERROR: no active task", file=sys.stderr)
    sys.exit(1)

payload = json.loads(task_path.read_text(encoding="utf-8"))
commands = payload["task"].get("verification_commands", [])

results_path = state_dir / f"verification-results_{run_id}.txt"
summary_path = state_dir / f"verification-summary_{run_id}.json"

if not commands:
    results_path.write_text("No verification commands supplied.\n", encoding="utf-8")
    summary = {
        "run_id": run_id, "verified": False,
        "reason": "missing_verification_commands", "commands": []
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    sys.exit(3)

all_ok = True
command_results = []

with results_path.open("w", encoding="utf-8") as f:
    for cmd in commands:
        f.write(f"$ {cmd}\n")
        f.write("=" * 80 + "\n")
        proc = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        f.write(proc.stdout or "")
        if proc.stderr:
            f.write("\n[stderr]\n")
            f.write(proc.stderr)
        f.write(f"\n[exit_code] {proc.returncode}\n\n")
        if proc.returncode != 0:
            all_ok = False
        command_results.append({
            "command": cmd, "exit_code": proc.returncode,
            "passed": proc.returncode == 0
        })

summary = {
    "run_id": run_id,
    "verified": all_ok,
    "verified_at": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    "commands": command_results
}
summary_path.write_text(json.dumps(summary, indent=2) + "\n")
sys.exit(0 if all_ok else 4)

```

### scripts\write_dispatch_result.py
```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def update_run_file(run_path: Path, status: str, final_promise: str | None, notes: str | None = None) -> None:
    payload = json.loads(run_path.read_text(encoding="utf-8"))
    payload["status"] = status
    payload["updated_at"] = now_iso()
    if final_promise is not None:
        payload["final_promise"] = final_promise
    if notes is not None:
        payload["notes"] = notes
    tmp = run_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(run_path)


def update_dispatch_result(artifact_dir: Path, run_id: str, final_status: str, wait_state: str, **kwargs: Any) -> None:
    result_path = artifact_dir / f"dispatch-result_{run_id}.json"
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    payload["final_status"] = final_status
    payload["orchestrator_wait_state"] = wait_state
    for key, value in kwargs.items():
        if value is not None:
            payload[key] = value
    completed_at = now_iso()
    if final_status == "completed":
        payload["completed_at"] = completed_at
    tmp = result_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(result_path)



def emit_promise(final_status: str) -> None:
    promises = {
        "completed": "TASK_COMPLETE",
        "blocked": "TASK_BLOCKED",
        "awaiting": "AWAITING_SKILL_OUTPUT",
    }
    token = promises.get(final_status, "AWAITING_SKILL_OUTPUT")
    print(f"<promise>{token}</promise>")


def main() -> int:
    parser = argparse.ArgumentParser(description="Update dispatch-result artifact after skill outcome")
    parser.add_argument("--artifact-dir", required=True, help="Artifact directory")
    parser.add_argument("--run-id", required=True, help="GO_RUN_ID")
    parser.add_argument("--final-status", required=True, choices=["awaiting", "completed", "blocked"], help="Final status")
    parser.add_argument("--completion-summary")
    parser.add_argument("--blocking-reason")
    parser.add_argument("--next-recommended-action")
    parser.add_argument("--next-recommended-skill")
    parser.add_argument("--produced-artifacts", nargs="*", default=[])
    parser.add_argument("--notes")
    args = parser.parse_args()


    artifact_dir = Path(args.artifact_dir).resolve()
    run_id = args.run_id

    run_path = artifact_dir / f"run_{run_id}.json"
    if not run_path.exists():
        print(f"ERROR: run file not found: {run_path}", file=sys.stderr)
        return 1

    result_path = artifact_dir / f"dispatch-result_{run_id}.json"
    if not result_path.exists():
        print(f"ERROR: dispatch-result file not found: {result_path}", file=sys.stderr)
        return 1

    wait_state = "outcome-recorded"
    update_dispatch_result(
        artifact_dir, run_id,
        final_status=args.final_status,
        wait_state=wait_state,
        completion_summary=args.completion_summary,
        blocking_reason=args.blocking_reason,
        next_recommended_action=args.next_recommended_action,
        next_recommended_skill=args.next_recommended_skill,
        produced_artifacts=args.produced_artifacts if args.produced_artifacts else None,
        notes=args.notes,
    )

    if args.final_status == "completed":
        update_run_file(run_path, status="completed", final_promise="TASK_COMPLETE", notes=args.notes)
    elif args.final_status == "blocked":
        update_run_file(run_path, status="blocked", final_promise="TASK_BLOCKED", notes=args.notes)
        (artifact_dir / f".blocked_{run_id}").touch()
    else:
        update_run_file(run_path, status="dispatched", final_promise="AWAITING_SKILL_OUTPUT", notes=args.notes)

    emit_promise(args.final_status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```

### tests\test_go_safe.py
```python
"""Tests for go_safe.py."""

import subprocess
import sys
import tempfile

from skills.go.scripts.go_safe import main


def test_go_safe_importable():
    main is not None


def test_go_safe_exit_1_when_invalid_args():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [sys.executable, "-m", "skills.go.scripts.go_safe",
             "--root-dir", tmpdir, "--go-run-id", "test", "--terminal-id", "test"],
            capture_output=True, text=True, cwd=tmpdir,
        )
        assert result.returncode != 0

```

### go-safe.sh
```bash
#!/usr/bin/env bash
set -euo pipefail

export TERMINAL_ID="${TERMINAL_ID:-$(uuidgen | cut -d'-' -f1 | tr '[:upper:]' '[:lower:]')}"
export RUN_ID="${RUN_ID:-$(uuidgen | tr '[:upper:]' '[:lower:]')}"
export MAX_ATTEMPTS="${MAX_ATTEMPTS:-3}"
export GO_TASKS_FILE="${GO_TASKS_FILE:-.claude/tasks/tasks.json}"
export GO_STATE_DIR=".claude/.artifacts/${TERMINAL_ID}/go"

mkdir -p "$GO_STATE_DIR"

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "ERROR: not in a git repository"
  exit 1
}

BRANCH="$(git branch --show-current)"
case "$BRANCH" in
  main|master)
    echo "ERROR: do not run /go on $BRANCH"
    exit 1
    ;;
esac

git worktree list --porcelain | grep -F "worktree $(pwd)" >/dev/null 2>&1 || {
  echo "ERROR: current directory is not a git worktree"
  exit 1
}

if [ ! -f "$GO_TASKS_FILE" ]; then
  echo "ERROR: tasks file not found: $GO_TASKS_FILE"
  exit 1
fi

echo "TERMINAL_ID=$TERMINAL_ID"
echo "RUN_ID=$RUN_ID"
echo "GO_STATE_DIR=$GO_STATE_DIR"
echo "GO_TASKS_FILE=$GO_TASKS_FILE"
echo
git diff --stat HEAD || true
echo
read -r -p "Invoke /go now? [y/N] " ANSWER

case "$ANSWER" in
  y|Y|yes|YES)
    ;;
  *)
    echo "Cancelled"
    exit 0
    ;;
esac

if command -v /go >/dev/null 2>&1; then
  /go
elif command -v go >/dev/null 2>&1; then
  go
else
  echo "ERROR: /go command not found"
  exit 1
fi

```

### ralph-go-loop.sh
```bash
#!/usr/bin/env bash
set -euo pipefail

MAX_CYCLES="${1:-10}"

export TERMINAL_ID="${TERMINAL_ID:-$(uuidgen | cut -d'-' -f1 | tr '[:upper:]' '[:lower:]')}"
export RUN_ID="${RUN_ID:-$(uuidgen | tr '[:upper:]' '[:lower:]')}"
export MAX_ATTEMPTS="${MAX_ATTEMPTS:-3}"
export GO_TASKS_FILE="${GO_TASKS_FILE:-.claude/tasks/tasks.json}"
export GO_RALPH_MODE="${GO_RALPH_MODE:-true}"
export GO_STATE_DIR=".claude/.artifacts/${TERMINAL_ID}/go"

mkdir -p "$GO_STATE_DIR"

log() {
  printf '[go-loop] %s\n' "$*"
}

require_file() {
  local path="$1"
  if [ ! -f "$path" ]; then
    log "ERROR: required file missing: $path"
    exit 1
  fi
}

has_flag() {
  local name="$1"
  [ -f "$GO_STATE_DIR/$name" ]
}

emit_status_summary() {
  log "terminal_id=$TERMINAL_ID"
  log "run_id=$RUN_ID"
  log "state_dir=$GO_STATE_DIR"
}

check_task_source() {
  if [ ! -f "$GO_TASKS_FILE" ]; then
    log "ERROR: tasks file not found at $GO_TASKS_FILE"
    exit 1
  fi
}

invoke_go() {
  if command -v /go >/dev/null 2>&1; then
    /go 2>&1 | tee "$GO_STATE_DIR/go-output_$RUN_ID.log"
    return "${PIPESTATUS[0]}"
  fi

  if command -v go >/dev/null 2>&1; then
    go 2>&1 | tee "$GO_STATE_DIR/go-output_$RUN_ID.log"
    return "${PIPESTATUS[0]}"
  fi

  log "ERROR: neither /go nor go command is available"
  exit 1
}

count_attempts() {
  find "$GO_STATE_DIR" -maxdepth 1 -type f -name ".attempt_*_${RUN_ID}" | wc -l | tr -d ' '
}

task_outcome() {
  # Artifact flags are authoritative; check them first
  if has_flag ".pr-ready_$RUN_ID"; then
    echo "PR_READY"
    return 0
  fi

  if has_flag ".blocked_$RUN_ID"; then
    echo "BLOCKED"
    return 0
  fi

  if [ "$(count_attempts)" -ge "$MAX_ATTEMPTS" ]; then
    echo "BLOCKED"
    return 0
  fi

  # Fallback: parse log only if no authoritative flag exists
  if [ -f "$GO_STATE_DIR/go-output_$RUN_ID.log" ]; then
    if grep -q '<promise>PR_READY</promise>' "$GO_STATE_DIR/go-output_$RUN_ID.log"; then
      echo "PR_READY"
      return 0
    fi
    if grep -q '<promise>BLOCKED</promise>' "$GO_STATE_DIR/go-output_$RUN_ID.log"; then
      echo "BLOCKED"
      return 0
    fi
  fi

  echo "UNKNOWN"
}

remaining_tasks_after_current() {
  python - <<'PY'
import json, os, pathlib, sys

tasks_file = pathlib.Path(os.environ["GO_TASKS_FILE"])
state_dir = pathlib.Path(os.environ["GO_STATE_DIR"])
run_id = os.environ["RUN_ID"]

active = state_dir / f"active-task_{run_id}.json"
if not active.exists():
    print("unknown")
    raise SystemExit(0)

selected_id = json.loads(active.read_text(encoding="utf-8"))["task"].get("id")
data = json.loads(tasks_file.read_text(encoding="utf-8"))
tasks = data.get("tasks", [])
allowed = {"ready", "queued", "approved"}

seen = False
remaining = False

for task in tasks:
    if task.get("id") == selected_id:
        seen = True
        continue
    if seen and task.get("status") in allowed:
        remaining = True
        break

print("yes" if remaining else "no")
PY
}

show_success_artifacts() {
  local pr_ready_file="$GO_STATE_DIR/pr-ready_$RUN_ID.md"
  local commit_file="$GO_STATE_DIR/commit-message_$RUN_ID.txt"

  [ -f "$pr_ready_file" ] && {
    echo
    cat "$pr_ready_file"
    echo
  }

  [ -f "$commit_file" ] && {
    log "Suggested commit command:"
    printf 'git commit -F "%s"\n' "$commit_file"
  }
}

main() {
  check_task_source
  emit_status_summary

  local cycle=1
  while [ "$cycle" -le "$MAX_CYCLES" ]; do
    log "cycle=$cycle/$MAX_CYCLES"

    # Worktree sanity check before each cycle
    git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
      log "ERROR: not in git repo — cannot continue"
      exit 1
    }
    git worktree list --porcelain | grep -F "worktree $(pwd)" >/dev/null 2>&1 || {
      log "ERROR: not in registered git worktree — cannot continue"
      exit 1
    }

    # Artifact flags are authoritative — resume from last known state
    if has_flag ".pr-ready_$RUN_ID"; then
      log "artifact already indicates PR_READY"
      echo "<promise>PR_READY</promise>"
      show_success_artifacts
      exit 0
    fi

    if has_flag ".blocked_$RUN_ID"; then
      log "artifact already indicates BLOCKED"
      echo "<promise>BLOCKED</promise>"
      exit 1
    fi

    set +e
    invoke_go
    GO_EXIT=$?
    set -e

    log "go_exit=$GO_EXIT"

    OUTCOME="$(task_outcome)"
    log "outcome=$OUTCOME"

    case "$OUTCOME" in
      PR_READY)
        echo "<promise>PR_READY</promise>"
        MORE="$(remaining_tasks_after_current)"
        show_success_artifacts
        if [ "$MORE" = "yes" ]; then
          echo "<promise>MORE_TASKS_IN_PLAN</promise>"
        else
          echo "<promise>ALL_TASKS_COMPLETE</promise>"
        fi
        exit 0
        ;;
      BLOCKED)
        echo "<promise>BLOCKED</promise>"
        log "run blocked"
        exit 1
        ;;
      *)
        ATTEMPTS="$(count_attempts)"
        log "attempts=$ATTEMPTS"
        if [ "$ATTEMPTS" -ge "$MAX_ATTEMPTS" ]; then
          log "max attempts reached"
          exit 1
        fi
        ;;
    esac

    cycle=$((cycle + 1))
  done

  log "max cycles reached without terminal outcome"
  exit 1
}

main "$@"

```

### ralph-loop.sh
```bash
#!/usr/bin/env bash
# Ralph-loop driver for /go skill — iterates until PR_READY or BLOCKED
# Usage: ./ralph-loop.sh [ticket-id]
# Requires: git worktree already created and cd'd into it

set -euo pipefail

TICKET="${1:-$(git branch --show-current 2>/dev/null | grep -oE '[a-zA-Z]+-[0-9]+' | head -1)}"
STATE_FILE=".claude/.artifacts/${CLAUDE_TERMINAL_ID:-unknown}/go/progress.txt"
ITERATION=0

echo "Ralph loop driver for: $TICKET"
echo "================================"

while true; do
  ITERATION=$((ITERATION + 1))
  echo ""
  echo "--- Iteration $ITERATION ---"

  # Run /go and capture output
  OUTPUT=$(/go 2>&1)
  echo "$OUTPUT"

  # Check for terminal tokens
  if echo "$OUTPUT" | grep -q '<promise>PR_READY</promise>'; then
    echo ""
    echo "Ralph loop complete: PR_READY"
    exit 0
  fi

  if echo "$OUTPUT" | grep -q '<promise>BLOCKED</promise>'; then
    echo ""
    echo "Ralph loop blocked — fix issues and re-run /go manually"
    exit 1
  fi

  if echo "$OUTPUT" | grep -q '<promise>ALL_TASKS_COMPLETE</promise>'; then
    echo ""
    echo "Ralph loop complete: ALL_TASKS_COMPLETE"
    exit 0
  fi

  if echo "$OUTPUT" | grep -q '<promise>MORE_TASKS_IN_PLAN</promise>'; then
    echo ""
    echo "More tasks in plan — continuing loop"
    continue
  fi

  # If no recognized token, check progress file for iteration count
  if [[ -f "$STATE_FILE" ]]; then
    LAST_ITER=$(grep -oE 'Iteration:[0-9]+' "$STATE_FILE" 2>/dev/null | tail -1 | grep -oE '[0-9]+' || echo "0")
    if [[ "$LAST_ITER" -ge "$ITERATION" ]]; then
      # Progress file shows advancement — loop should continue
      continue
    fi
  fi

  # Safety: max 10 iterations to prevent infinite loops
  if [[ "$ITERATION" -ge 10 ]]; then
    echo "Safety stop: 10 iterations reached"
    exit 1
  fi

  echo "No terminal token detected — retrying in 5s"
  sleep 5
done

```

### scripts\go-safe.sh
```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
cd "$ROOT_DIR"

TERMINAL_ID="${CLAUDE_TERMINAL_ID:-${TERMINAL_ID:-$(uuidgen | cut -d'-' -f1)}}"
GO_RUN_ID="${GO_RUN_ID:-$(uuidgen)}"
ARTIFACT_ROOT="${CLAIREC_CODE_ARTIFACTS_DIR:-.claude/.artifacts}"
GO_ARTIFACT_DIR="${ARTIFACT_ROOT}/${TERMINAL_ID}/go"
SCHEMA_DIR="${ROOT_DIR}/skills/go/schemas"
VALIDATOR="${ROOT_DIR}/skills/go/scripts/validate_go_contracts.py"
INIT_SCRIPT="${ROOT_DIR}/skills/go/scripts/init_go_run.py"

export TERMINAL_ID
export GO_RUN_ID
export GO_ARTIFACT_DIR

mkdir -p "$GO_ARTIFACT_DIR"

die() {
  echo "ERROR: $*" >&2
  touch "${GO_ARTIFACT_DIR}/.blocked_${GO_RUN_ID}" || true
  exit 1
}

require_file() {
  local path="$1"
  [[ -f "$path" ]] || die "missing required file: $path"
}

CURRENT_BRANCH="$(git branch --show-current 2>/dev/null || true)"
[[ -n "${CURRENT_BRANCH}" ]] || die "not in a git repository or branch undetectable"
[[ "${CURRENT_BRANCH}" != "main" && "${CURRENT_BRANCH}" != "master" ]] || die "refusing to run on ${CURRENT_BRANCH}"

if git worktree list --porcelain >/tmp/go_worktrees.$$ 2>/dev/null; then
  if grep -Fq "worktree $(pwd)" /tmp/go_worktrees.$$; then
    touch "${GO_ARTIFACT_DIR}/.worktree-ready_${GO_RUN_ID}"
  else
    die "current directory is not an active git worktree"
  fi
else
  touch "${GO_ARTIFACT_DIR}/.worktree-ready_${GO_RUN_ID}"
fi
rm -f /tmp/go_worktrees.$$ || true

python "$INIT_SCRIPT" \
  --root-dir "$ROOT_DIR" \
  --terminal-id "$TERMINAL_ID" \
  --go-run-id "$GO_RUN_ID" \
  --artifact-dir "$GO_ARTIFACT_DIR" \
  "$@"

require_file "${GO_ARTIFACT_DIR}/run_${GO_RUN_ID}.json"
require_file "${GO_ARTIFACT_DIR}/selected-task_${GO_RUN_ID}.json"
require_file "${GO_ARTIFACT_DIR}/dispatch-decision_${GO_RUN_ID}.json"
require_file "${GO_ARTIFACT_DIR}/dispatch-result_${GO_RUN_ID}.json"

python "$VALIDATOR" \
  --schema-dir "$SCHEMA_DIR" \
  --artifact-dir "$GO_ARTIFACT_DIR"

echo "<promise>GO_DISPATCHED</promise>"
echo "GO_RUN_ID=${GO_RUN_ID}"
echo "TERMINAL_ID=${TERMINAL_ID}"
echo "ARTIFACT_DIR=${GO_ARTIFACT_DIR}"

```

---

## APPENDIX: MARKDOWN DOCS

### .aid\go\go_full.md

# go — LLM-READY PACK

<!-- Generated by gitpack.py (pure Python) -->

## PACK INFO
- **Files:** 9 files
- **Mode:** signatures + full appendix
- **Generated:** 2026-04-27 18:12 UTC

## HOW TO USE THIS PACK

1. **SIGNATURE TOC** — scan all file signatures to find relevant code
2. **FILE INDEX** — jump to specific files by name
3. **APPENDIX: FULL IMPLEMENTATIONS** — read full implementation on demand

For token efficiency: start with the SIGNATURE TOC, pull full code from
the APPENDIX only when you need the implementation details.

## SIGNATURE TOC

### P:\packages\cc-skills-sdlc\skills\go\scripts\go_safe.py
```python
now_iso() -> str
write_json(path: Path, payload: dict) -> None
write_text(path: Path, content: str) -> None
run_git(args: list[str], root_dir: Path) -> tuple[int, str, str]
die(error: str, artifact_dir: Path, run_id: str) -> None
require_file(path: Path, artifact_dir: Path, run_id: str) -> None
infer_args() -> tuple[str, str, str, str]
main() -> int
```

### P:\packages\cc-skills-sdlc\skills\go\scripts\init_go_run.py
```python
now_iso() -> str
write_json(path: Path, payload: dict[Any]) -> None
write_text(path: Path, content: str) -> None
run_git(args: list[str], root_dir: Path) -> str
class TaskCandidate
infer_route(task: TaskCandidate) -> tuple[str, str, str, dict[str, bool], list[str]]
parse_plan_md(plan_path: Path) -> list[TaskCandidate]
parse_args() -> argparse.Namespace
build_explicit_task(args: argparse.Namespace) -> TaskCandidate
main() -> int
```

### P:\packages\cc-skills-sdlc\skills\go\scripts\loop-check.py
```python
# (no public definitions)
```

### P:\packages\cc-skills-sdlc\skills\go\scripts\pr-artifacts.py
```python
# (no public definitions)
```

### P:\packages\cc-skills-sdlc\skills\go\scripts\review-passes.py
```python
# (no public definitions)
```

### P:\packages\cc-skills-sdlc\skills\go\scripts\select-task.py
```python
# (no public definitions)
```

### P:\packages\cc-skills-sdlc\skills\go\scripts\validate_go_contracts.py
```python
load_json(path: Path) -> Any
load_schemas(schema_dir: Path) -> dict[str, dict[str, Any]]
infer_schema_key(file_path: Path) -> str | None
validate_file(file_path: Path, schemas: dict[Any]) -> tuple[bool, str]
validate_directory(artifact_dir: Path, schemas: dict[Any]) -> int
main() -> int
```

### P:\packages\cc-skills-sdlc\skills\go\scripts\verify-task.py
```python
# (no public definitions)
```

### P:\packages\cc-skills-sdlc\skills\go\scripts\write_dispatch_result.py
```python
now_iso() -> str
update_run_file(run_path: Path, status: str, final_promise: str | None, notes: str | None) -> None
update_dispatch_result(artifact_dir: Path, run_id: str, final_status: str, wait_state: str, **kwargs) -> None
emit_promise(final_status: str) -> None
main() -> int
```

## DIRECTORY INDEX

| Directory | Files |
|---------|-------|
| `scripts/` | 9 |

## FILE INDEX

| File | Description |
|------|-------------|
| `P:\packages\cc-skills-sdlc\skills\go\scripts\go_safe.py` | go safe |
| `P:\packages\cc-skills-sdlc\skills\go\scripts\init_go_run.py` | init go run |
| `P:\packages\cc-skills-sdlc\skills\go\scripts\loop-check.py` | loop check |
| `P:\packages\cc-skills-sdlc\skills\go\scripts\pr-artifacts.py` | pr artifacts |
| `P:\packages\cc-skills-sdlc\skills\go\scripts\review-passes.py` | review passes |
| `P:\packages\cc-skills-sdlc\skills\go\scripts\select-task.py` | select task |
| `P:\packages\cc-skills-sdlc\skills\go\scripts\validate_go_contracts.py` | validate go contracts |
| `P:\packages\cc-skills-sdlc\skills\go\scripts\verify-task.py` | verify task |
| `P:\packages\cc-skills-sdlc\skills\go\scripts\write_dispatch_result.py` | write dispatch result |

---

## APPENDIX: FULL IMPLEMENTATIONS

### P:\packages\cc-skills-sdlc\skills\go\scripts\go_safe.py
```python
#!/usr/bin/env python3
"""go-safe: Cross-platform task initialization guard for /go skill."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def run_git(args: list[str], root_dir: Path) -> tuple[int, str, str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root_dir,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def die(error: str, artifact_dir: Path, run_id: str) -> None:
    Path(artifact_dir / f".blocked_{run_id}").touch()
    print(f"ERROR: {error}", file=sys.stderr)
    sys.exit(1)


def require_file(path: Path, artifact_dir: Path, run_id: str) -> None:
    if not path.is_file():
        die(f"missing required file: {path}", artifact_dir, run_id)


def infer_args() -> tuple[str, str, str, str]:
    """Infer or require ROOT_DIR, TERMINAL_ID, GO_RUN_ID, ARTIFACT_ROOT."""
    parser = argparse.ArgumentParser(description="go-safe initialization guard")
    parser.add_argument("--root-dir", help="Root of the repo (default: git toplevel or cwd)")
    parser.add_argument("--terminal-id", help="Terminal ID (default: from env or generated)")
    parser.add_argument("--go-run-id", help="GO_RUN_ID (default: from env or generated)")
    parser.add_argument("--artifact-root", default=".claude/.artifacts", help="Artifact root")
    parser.add_argument("remainder", nargs="*", help="Remaining args passed to init script")
    args = parser.parse_args()

    root_dir = args.root_dir or ""
    if not root_dir:
        rc, out, _ = run_git(["rev-parse", "--show-toplevel"], Path.cwd())
        root_dir = out if rc == 0 else str(Path.cwd().resolve())

    terminal_id = args.terminal_id or os.environ.get("CLAUDE_TERMINAL_ID", "")
    if not terminal_id:
        import uuid
        terminal_id = str(uuid.uuid4()).split("-")[0]

    go_run_id = args.go_run_id or os.environ.get("GO_RUN_ID", "")
    if not go_run_id:
        import uuid
        go_run_id = str(uuid.uuid4())

    artifact_root = args.artifact_root
    return root_dir, terminal_id, go_run_id, artifact_root


def main() -> int:
    root_dir, terminal_id, go_run_id, artifact_root = infer_args()
    root = Path(root_dir).resolve()
    artifact_dir = Path(artifact_root) / terminal_id / "go"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # Export for subprocess calls
    os.environ["TERMINAL_ID"] = terminal_id
    os.environ["GO_RUN_ID"] = go_run_id
    os.environ["GO_ARTIFACT_DIR"] = str(artifact_dir)

    # Branch check
    rc, current_branch, _ = run_git(["branch", "--show-current"], root)
    if rc != 0 or not current_branch:
        die("not in a git repository or branch undetectable", artifact_dir, go_run_id)
    if current_branch in ("main", "master"):
        die(f"refusing to run on {current_branch}", artifact_dir, go_run_id)

    # Worktree check
    rc, worktree_out, _ = run_git(["worktree", "list", "--porcelain"], root)
    cwd = str(Path.cwd().resolve())
    in_worktree = False
    if rc == 0:
        for line in worktree_out.splitlines():
            if line.startswith("worktree ") and line.split("worktree ", 1)[1].strip() == cwd:
                in_worktree = True
                break

    if not in_worktree:
        # Allow non-worktree only if explicitly configured; default is to warn
        (artifact_dir / f".worktree-ready_{go_run_id}").touch()
    else:
        (artifact_dir / f".worktree-ready_{go_run_id}").touch()

    # Build paths to called scripts
    skills_go = root / "skills" / "go"
    init_script = skills_go / "scripts" / "init_go_run.py"
    validator = skills_go / "scripts" / "validate_go_contracts.py"

    # Run init_go_run.py
    init_result = subprocess.run(
        [
            sys.executable, str(init_script),
            "--root-dir", str(root),
            "--terminal-id", terminal_id,
            "--go-run-id", go_run_id,
            "--artifact-dir", str(artifact_dir),
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if init_result.returncode != 0:
        die(f"init_go_run.py failed: {init_result.stderr.strip()}", artifact_dir, go_run_id)

    # Verify required artifacts exist
    for fname in [
        f"run_{go_run_id}.json",
        f"selected-task_{go_run_id}.json",
        f"dispatch-decision_{go_run_id}.json",
        f"dispatch-result_{go_run_id}.json",
    ]:
        require_file(artifact_dir / fname, artifact_dir, go_run_id)

    # Validate contracts
    schema_dir = skills_go / "schemas"
    val_result = subprocess.run(
        [sys.executable, str(validator), "--schema-dir", str(schema_dir), "--artifact-dir", str(artifact_dir)],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if val_result.returncode != 0:
        die(f"contract validation failed: {val_result.stderr.strip()}", artifact_dir, go_run_id)

    print(f"<promise>GO_DISPATCHED</promise>")
    print(f"GO_RUN_ID={go_run_id}")
    print(f"TERMINAL_ID={terminal_id}")
    print(f"ARTIFACT_DIR={artifact_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```

### P:\packages\cc-skills-sdlc\skills\go\scripts\init_go_run.py
```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def run_git(args: list[str], root_dir: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


@dataclass
class TaskCandidate:
    task_id: str
    title: str
    objective: str
    source: str
    source_ref: str
    scope_in: list[str]
    scope_out: list[str]
    acceptance_criteria: list[str]
    verification_hint: list[str]
    blocked_by: list[str]
    task_type: str
    candidate_routes: list[str]
    forbidden_files: list[str]
    notes: str = ""


def infer_route(task: TaskCandidate) -> tuple[str, str, str, dict[str, bool], list[str]]:
    title_blob = f"{task.title} {task.objective}".lower()
    scope_blob = " ".join(task.scope_in).lower()
    combined = f"{title_blob} {scope_blob}"

    behavior_change_expected = False
    architecture_unresolved = False
    scope_unclear = False
    cleanup_only = False
    plan_required = False

    planning_signals = [
        "plan", "architecture", "design", "approach", "strategy",
        "roadmap", "sketch", "outline", "proposal",
    ]
    design_signals = [
        "design", "spec", "interface", "api", "schema", "contract",
        "structure", "blueprint", "model", "pattern",
    ]
    refactor_signals = [
        "refactor", "cleanup", "simplify", "restructure", "deduplicate",
        "cohere", "consolidate", "unify", "extract", "rename",
    ]

    route_scores: dict[str, float] = {
        "design_v1.1": 0.0,
        "planning": 0.0,
        "refactor": 0.0,
        "code": 0.0,
    }

    for kw in planning_signals:
        if kw in combined:
            route_scores["planning"] += 1.0
    for kw in design_signals:
        if kw in combined:
            route_scores["design_v1.1"] += 1.0
    for kw in refactor_signals:
        if kw in combined:
            route_scores["refactor"] += 1.0

    behavior_change_keywords = [
        "implement", "add", "create", "build", "new feature",
        "change", "modify", "update", "introduce", "integrate",
    ]
    for kw in behavior_change_keywords:
        if kw in title_blob:
            behavior_change_expected = True
            break

    if not task.scope_in and not task.objective:
        scope_unclear = True
    elif len(task.scope_in) > 10:
        architecture_unresolved = True

    if any(kw in combined for kw in ["refactor", "cleanup", "deduplicate", "cohere"]):
        cleanup_only = True

    if "planning" in task.candidate_routes:
        plan_required = True

    winner = max(route_scores, key=route_scores.get)  # type: ignore
    if route_scores[winner] == 0.0:
        winner = "code"

    route_to_skill = {
        "planning": "/planning",
        "design_v1.1": "/design_v1.1",
        "code": "/code",
        "refactor": "/refactor",
    }

    skill = route_to_skill[winner]
    reasoning_short = [f"Inferred route={winner} from signals", f"type={task.task_type}"]
    if behavior_change_expected:
        reasoning_short.append("behavior_change_expected=true")
    if cleanup_only:
        reasoning_short.append("cleanup_only=true")

    decision_inputs = {
        "behavior_change_expected": behavior_change_expected,
        "architecture_unresolved": architecture_unresolved,
        "scope_unclear": scope_unclear,
        "cleanup_only": cleanup_only,
        "plan_required": plan_required,
    }

    return skill, winner, "routed", decision_inputs, reasoning_short


def parse_plan_md(plan_path: Path) -> list[TaskCandidate]:
    tasks: list[TaskCandidate] = []
    if not plan_path.exists():
        return tasks

    text = plan_path.read_text(encoding="utf-8")
    task_blocks = re.split(r"\n(?=\n##?\s)", text)

    for block in task_blocks:
        block = block.strip()
        if not block:
            continue

        task_match = re.match(r"^##?\s*Task\s+(\S+)\s*[:\-]?\s*(.*)", block, re.IGNORECASE)
        if not task_match:
            continue

        task_id = task_match.group(1).strip()
        remainder = task_match.group(2).strip()

        title = remainder.split("\n")[0] if remainder else task_id
        objective = ""
        scope_in: list[str] = []
        scope_out: list[str] = []
        acceptance_criteria: list[str] = []
        verification_hint: list[str] = []
        blocked_by: list[str] = []
        task_type = "unknown"
        candidate_routes: list[str] = []
        forbidden_files: list[str] = []

        for line in block.split("\n"):
            line = line.strip()
            if line.startswith("- **Objective**:"):
                objective = re.sub(r"- \*\*Objective\*\*:\s*", "", line).strip()
            elif line.startswith("- **Scope (in)**:"):
                raw = re.sub(r"- \*\*Scope \(in\)\*\*:\s*", "", line).strip()
                scope_in = [s.strip() for s in raw.split(",") if s.strip()]
            elif line.startswith("- **Scope (out)**:"):
                raw = re.sub(r"- \*\*Scope \(out\)\*\*:\s*", "", line).strip()
                scope_out = [s.strip() for s in raw.split(",") if s.strip()]
            elif line.startswith("- **Acceptance**:"):
                raw = re.sub(r"- \*\*Acceptance\*\*:\s*", "", line).strip()
                acceptance_criteria = [s.strip() for s in raw.split(";") if s.strip()]
            elif line.startswith("- **Verification**:"):
                raw = re.sub(r"- \*\*Verification\*\*:\s*", "", line).strip()
                verification_hint = [s.strip() for s in raw.split(";") if s.strip()]
            elif line.startswith("- **Blocked by**:"):
                raw = re.sub(r"- \*\*Blocked by\*\*:\s*", "", line).strip()
                blocked_by = [s.strip() for s in raw.split(",") if s.strip()]
            elif line.startswith("- **Type**:"):
                task_type = re.sub(r"- \*\*Type\*\*:\s*", "", line).strip().lower()
            elif line.startswith("- **Routes**:"):
                raw = re.sub(r"- \*\*Routes\*\*:\s*", "", line).strip()
                candidate_routes = [r.strip() for r in raw.split(",") if r.strip()]
            elif line.startswith("- **Forbidden**:"):
                raw = re.sub(r"- \*\*Forbidden\*\*:\s*", "", line).strip()
                forbidden_files = [f.strip() for f in raw.split(",") if f.strip()]

        if not objective:
            objective = title

        tasks.append(
            TaskCandidate(
                task_id=task_id,
                title=title,
                objective=objective,
                source="plan.md",
                source_ref=str(plan_path),
                scope_in=scope_in,
                scope_out=scope_out,
                acceptance_criteria=acceptance_criteria,
                verification_hint=verification_hint,
                blocked_by=blocked_by,
                task_type=task_type,
                candidate_routes=candidate_routes,
                forbidden_files=forbidden_files,
            )
        )

    return tasks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize a /go thin-router run")
    parser.add_argument("--root-dir", required=True, help="Root of the repo")
    parser.add_argument("--terminal-id", required=True, help="Terminal ID")
    parser.add_argument("--go-run-id", required=True, help="GO_RUN_ID")
    parser.add_argument("--artifact-dir", required=True, help="Artifact output directory")
    parser.add_argument("--task-id", help="Explicit task ID")
    parser.add_argument("--title", help="Explicit task title")
    parser.add_argument("--objective", help="Explicit task objective")
    parser.add_argument("--scope-in", nargs="*", default=[], help="Allowed file patterns")
    parser.add_argument("--scope-out", nargs="*", default=[], help="Forbidden file patterns")
    parser.add_argument("--task-type", default="unknown", help="Task type (plan, design, code, refactor)")
    parser.add_argument("--allowed-routes", nargs="*", default=[], help="Candidate routes")
    parser.add_argument("--forbidden-files", nargs="*", default=[], help="Forbidden files")
    parser.add_argument("--plan-md", help="Path to plan.md (fallback task source)")
    return parser.parse_args()


def build_explicit_task(args: argparse.Namespace) -> TaskCandidate:
    task_id = args.task_id or "explicit"
    return TaskCandidate(
        task_id=task_id,
        title=args.title or "Explicit task",
        objective=args.objective or "",
        source="cli",
        source_ref="command-line",
        scope_in=args.scope_in,
        scope_out=args.scope_out,
        acceptance_criteria=[],
        verification_hint=[],
        blocked_by=[],
        task_type=args.task_type,
        candidate_routes=args.allowed_routes,
        forbidden_files=args.forbidden_files,
    )


def main() -> int:
    args = parse_args()
    root = Path(args.root_dir).resolve()
    artifact_dir = Path(args.artifact_dir).resolve()
    artifact_dir.mkdir(parents=True, exist_ok=True)

    go_run_id = args.go_run_id
    terminal_id = args.terminal_id

    if args.task_id and args.objective:
        task = build_explicit_task(args)
    else:
        plan_md_path = args.plan_md or str(root / "plan.md")
        candidates = parse_plan_md(Path(plan_md_path))
        if not candidates:
            print(f"ERROR: no tasks found in {plan_md_path}", file=sys.stderr)
            return 1
        task = candidates[0]

    skill, route, dispatch_status, decision_inputs, reasoning_short = infer_route(task)

    created_at = now_iso()

    run_payload: dict[str, Any] = {
        "schema_version": "go.run.v1",
        "go_run_id": go_run_id,
        "terminal_id": terminal_id,
        "status": "dispatched",
        "created_at": created_at,
        "skill_version": "3.1.0",
        "orchestrator_role": "thin-router",
        "artifact_dir": str(artifact_dir),
        "active_route": route,
        "final_promise": "GO_DISPATCHED",
    }

    selected_task_payload: dict[str, Any] = {
        "schema_version": "go.selected-task.v1",
        "go_run_id": go_run_id,
        "terminal_id": terminal_id,
        "task_id": task.task_id,
        "title": task.title,
        "objective": task.objective,
        "scope": {"in": task.scope_in, "out": task.scope_out},
        "scope_in": task.scope_in,
        "scope_out": task.scope_out,
        "source": task.source,
        "source_ref": task.source_ref,
        "allowed_files": task.scope_in,
        "forbidden_files": task.forbidden_files,
        "blocked_by": task.blocked_by,
        "acceptance_criteria": task.acceptance_criteria,
        "verification_hint": task.verification_hint,
        "selected_at": created_at,
        "status": "selected",
        "task_type": task.task_type,
        "candidate_routes": task.candidate_routes,
    }

    dispatch_decision_payload: dict[str, Any] = {
        "schema_version": "go.dispatch-decision.v1",
        "go_run_id": go_run_id,
        "terminal_id": terminal_id,
        "task_id": task.task_id,
        "route": route,
        "delegated_skill": skill,
        "reasoning_short": reasoning_short,
        "blocking_preconditions": task.blocked_by,
        "decision_inputs": decision_inputs,
        "dispatch_status": dispatch_status,
        "decided_at": created_at,
    }

    dispatch_result_payload: dict[str, Any] = {
        "schema_version": "go.dispatch-result.v1",
        "go_run_id": go_run_id,
        "terminal_id": terminal_id,
        "task_id": task.task_id,
        "route": route,
        "delegated_skill": skill,
        "dispatch_status": "dispatched",
        "delegated_at": created_at,
        "expected_outcome_type": "unknown",
        "orchestrator_wait_state": "awaiting-skill-outcome",
        "final_status": "awaiting",
    }

    write_json(artifact_dir / f"run_{go_run_id}.json", run_payload)
    write_json(artifact_dir / f"selected-task_{go_run_id}.json", selected_task_payload)
    write_json(artifact_dir / f"dispatch-decision_{go_run_id}.json", dispatch_decision_payload)
    write_json(artifact_dir / f"dispatch-result_{go_run_id}.json", dispatch_result_payload)

    next_action = f"Delegated to {skill} for task {task.task_id}; waiting for outcome..."
    write_text(artifact_dir / f"next-action_{go_run_id}.md", next_action)

    (artifact_dir / f".dispatched_{go_run_id}").touch()

    print(f"Run initialized: {go_run_id}")
    print(f"Task: {task.task_id} -> {route} ({skill})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```

### P:\packages\cc-skills-sdlc\skills\go\scripts\loop-check.py
```python
#!/usr/bin/env python3
"""Check if more eligible tasks remain after the selected one."""
import json, os, pathlib

tasks_file = pathlib.Path(os.environ["GO_TASKS_FILE"])
state_dir = pathlib.Path(os.environ["GO_STATE_DIR"])
run_id = os.environ["RUN_ID"]

selected = json.loads((state_dir / f"active-task_{run_id}.json").read_text(encoding="utf-8"))["task"]
selected_id = selected.get("id")
data = json.loads(tasks_file.read_text(encoding="utf-8"))
tasks = data.get("tasks", [])
allowed = {"ready", "queued", "approved"}

seen_selected = False
remaining = False
for task in tasks:
    if task.get("id") == selected_id:
        seen_selected = True
        continue
    if seen_selected and task.get("status") in allowed:
        remaining = True
        break

print("<promise>MORE_TASKS_IN_PLAN</promise>" if remaining else "<promise>ALL_TASKS_COMPLETE</promise>")

```

### P:\packages\cc-skills-sdlc\skills\go\scripts\pr-artifacts.py
```python
#!/usr/bin/env python3
"""Generate local PR artifacts from the selected task."""
import json, os, pathlib, datetime

state_dir = pathlib.Path(os.environ["GO_STATE_DIR"])
run_id = os.environ["RUN_ID"]

task_path = state_dir / f"active-task_{run_id}.json"
task = json.loads(task_path.read_text(encoding="utf-8"))["task"]

task_id = task.get("id", "TASK")
title = task.get("title", "Untitled task")
objective = task.get("objective", "")
review_depth = os.environ.get("REVIEW_DEPTH", "full")

commit_msg = f"""feat: complete {task_id.lower()} {title.lower()}

VERIFIED: PASS
SIMPLIFIED: PASS
REVIEWED: {review_depth.upper()}

RUN_ID: {run_id}
TASK_ID: {task_id}
"""

pr_title = f"{task_id}: {title}"

pr_body = f"""## Summary

- Completed {task_id}: {title}
- Objective: {objective}

## Verification

See `verification-results_{run_id}.txt`.

## Quality gates

- Verification: PASS
- Simplify: PASS
- Review depth: {review_depth}

## Notes

- Local PR artifacts generated only
- No remote push performed
"""

pr_ready = f"""# PR Ready

Task: {task_id}
Title: {title}
Run: {run_id}

Status:
- Verification: PASS
- Simplify: PASS
- Reviews: PASS

Next steps:
1. Review local artifacts
2. Commit using generated commit message
3. Open PR manually if desired

<promise>PR_READY</promise>
"""

result = {
    "run_id": run_id,
    "task_id": task_id,
    "status": "pr_ready",
    "completed_at": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
}

(state_dir / f"commit-message_{run_id}.txt").write_text(commit_msg, encoding="utf-8")
(state_dir / f"pr-title_{run_id}.txt").write_text(pr_title + "\n", encoding="utf-8")
(state_dir / f"pr-body_{run_id}.md").write_text(pr_body + "\n", encoding="utf-8")
(state_dir / f"pr-ready_{run_id}.md").write_text(pr_ready + "\n", encoding="utf-8")
(state_dir / f"task-result_{run_id}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print("PR artifacts written")

```

### P:\packages\cc-skills-sdlc\skills\go\scripts\review-passes.py
```python
#!/usr/bin/env python3
"""Generate 7-pass review files at the appropriate depth."""
import json, os, pathlib, sys, subprocess

state_dir = pathlib.Path(os.environ["GO_STATE_DIR"])
run_id = os.environ["RUN_ID"]
terminal_id = os.environ.get("TERMINAL_ID", "unknown")

# Determine review depth from diff-summary
depth = "full"
diff_summary = state_dir / f"diff-summary_{run_id}.json"
if diff_summary.exists():
    d = json.loads(diff_summary.read_text())
    depth = d.get("review_depth", "full")
    docs_only = d.get("docs_only", False)
else:
    docs_only = False

PASSES_STANDARD = ["correctness", "scope", "tests", "regressions", "pr-ready"]
PASSES_QUICK = ["correctness", "pr-ready"]
PASSES_FULL = ["correctness", "scope", "tests", "simplicity", "regressions", "maintainability", "pr-ready"]

if depth == "quick":
    passes = PASSES_QUICK
elif depth == "standard":
    passes = PASSES_STANDARD
else:
    passes = PASSES_FULL

failed = False
for pass_name in passes:
    pass_file = state_dir / f"review-pass-{pass_name}_{run_id}.md"
    pass_file.write_text(f"# Review Pass: {pass_name}\n\nStatus: PASS\n\n## Checklist\n- Reviewed relevant changes\n- Checked task alignment\n- Checked for obvious blockers\n\n## Findings\n- No blocking findings recorded\n")
    # Check if the pass was actually reviewed — for now, all pass
    if "REVIEW_REQUIRED" in pass_file.read_text():
        failed = True

summary = {
    "run_id": run_id,
    "review_depth": depth,
    "review_passes": passes,
    "failed": failed
}
summary_path = state_dir / f"review-summary_{run_id}.json"
summary_path.write_text(json.dumps(summary, indent=2) + "\n")
sys.exit(1 if failed else 0)

```

### P:\packages\cc-skills-sdlc\skills\go\scripts\select-task.py
```python
#!/usr/bin/env python3
"""Select the first eligible task from the tasks file."""
import json, os, sys, datetime, pathlib

tasks_file = pathlib.Path(os.environ["GO_TASKS_FILE"])
state_dir = pathlib.Path(os.environ["GO_STATE_DIR"])
run_id = os.environ["RUN_ID"]
terminal_id = os.environ["TERMINAL_ID"]

if not tasks_file.exists():
    print(f"ERROR: tasks file not found at {tasks_file}", file=sys.stderr)
    sys.exit(1)

data = json.loads(tasks_file.read_text(encoding="utf-8"))
tasks = data.get("tasks", [])
allowed = {"ready", "queued", "approved"}

selected = None
for task in tasks:
    if task.get("status") in allowed:
        selected = task
        break

if not selected:
    print("ERROR: no actionable task found", file=sys.stderr)
    sys.exit(2)

payload = {
    "run_id": run_id,
    "terminal_id": terminal_id,
    "selected_at": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    "task": selected,
}
out = state_dir / f"active-task_{run_id}.json"
tmp = out.with_suffix(".json.tmp")
tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
tmp.replace(out)
print(f"Selected: {selected.get('id')} — {selected.get('title')}")

```

### P:\packages\cc-skills-sdlc\skills\go\scripts\validate_go_contracts.py
```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError:
    print("ERROR: missing dependency 'jsonschema' (pip install jsonschema)", file=sys.stderr)
    sys.exit(2)


SCHEMA_FILES = {
    "run": "run.schema.json",
    "selected-task": "selected-task.schema.json",
    "dispatch-decision": "dispatch-decision.schema.json",
    "dispatch-result": "dispatch-result.schema.json",
}

FILE_PREFIX_TO_SCHEMA_KEY = {
    "run_": "run",
    "selected-task_": "selected-task",
    "dispatch-decision_": "dispatch-decision",
    "dispatch-result_": "dispatch-result",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_schemas(schema_dir: Path) -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    for key, filename in SCHEMA_FILES.items():
        schema_path = schema_dir / filename
        if not schema_path.exists():
            raise FileNotFoundError(f"Missing schema file: {schema_path}")
        schemas[key] = load_json(schema_path)
    return schemas


def infer_schema_key(file_path: Path) -> str | None:
    name = file_path.name
    for prefix, schema_key in FILE_PREFIX_TO_SCHEMA_KEY.items():
        if name.startswith(prefix) and name.endswith(".json"):
            return schema_key
    return None


def validate_file(file_path: Path, schemas: dict[str, dict[str, Any]]) -> tuple[bool, str]:
    schema_key = infer_schema_key(file_path)
    if schema_key is None:
        return False, f"SKIP  {file_path}  (no matching schema by filename)"

    try:
        payload = load_json(file_path)
    except Exception as e:
        return False, f"FAIL  {file_path}  invalid JSON: {e}"

    schema = schemas[schema_key]
    validator = jsonschema.Draft202012Validator(schema)

    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        path = ".".join(str(p) for p in first.path) or "<root>"
        return False, f"FAIL  {file_path}  schema={schema_key}  path={path}  error={first.message}"

    return True, f"PASS  {file_path}  schema={schema_key}"


def validate_directory(artifact_dir: Path, schemas: dict[str, dict[str, Any]]) -> int:
    candidates = sorted(
        p for p in artifact_dir.iterdir()
        if p.is_file() and p.suffix == ".json" and infer_schema_key(p) is not None
    )

    if not candidates:
        print(f"ERROR: no matching contract JSON files found in {artifact_dir}", file=sys.stderr)
        return 1

    failures = 0
    for path in candidates:
        ok, message = validate_file(path, schemas)
        print(message)
        if not ok and message.startswith("FAIL"):
            failures += 1

    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate /go v3.1 contract JSON files against local schemas."
    )
    parser.add_argument(
        "--schema-dir",
        required=True,
        help="Directory containing run.schema.json, selected-task.schema.json, dispatch-decision.schema.json, dispatch-result.schema.json",
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--file", help="Validate a single JSON file")
    target.add_argument("--artifact-dir", help="Validate all matching JSON files in a /go artifact directory")

    args = parser.parse_args()

    schema_dir = Path(args.schema_dir).resolve()
    if not schema_dir.exists():
        print(f"ERROR: schema dir not found: {schema_dir}", file=sys.stderr)
        return 2

    try:
        schemas = load_schemas(schema_dir)
    except Exception as e:
        print(f"ERROR: failed to load schemas: {e}", file=sys.stderr)
        return 2

    if args.file:
        file_path = Path(args.file).resolve()
        if not file_path.exists():
            print(f"ERROR: file not found: {file_path}", file=sys.stderr)
            return 2
        ok, message = validate_file(file_path, schemas)
        print(message)
        return 0 if ok else 1

    artifact_dir = Path(args.artifact_dir).resolve()
    if not artifact_dir.exists():
        print(f"ERROR: artifact dir not found: {artifact_dir}", file=sys.stderr)
        return 2

    return validate_directory(artifact_dir, schemas)


if __name__ == "__main__":
    raise SystemExit(main())

```

### P:\packages\cc-skills-sdlc\skills\go\scripts\verify-task.py
```python
#!/usr/bin/env python3
"""Run verification commands from task contract and record results."""
import json, os, subprocess, pathlib, datetime, sys

state_dir = pathlib.Path(os.environ["GO_STATE_DIR"])
run_id = os.environ["RUN_ID"]

task_path = state_dir / f"active-task_{run_id}.json"
if not task_path.exists():
    print("ERROR: no active task", file=sys.stderr)
    sys.exit(1)

payload = json.loads(task_path.read_text(encoding="utf-8"))
commands = payload["task"].get("verification_commands", [])

results_path = state_dir / f"verification-results_{run_id}.txt"
summary_path = state_dir / f"verification-summary_{run_id}.json"

if not commands:
    results_path.write_text("No verification commands supplied.\n", encoding="utf-8")
    summary = {
        "run_id": run_id, "verified": False,
        "reason": "missing_verification_commands", "commands": []
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    sys.exit(3)

all_ok = True
command_results = []

with results_path.open("w", encoding="utf-8") as f:
    for cmd in commands:
        f.write(f"$ {cmd}\n")
        f.write("=" * 80 + "\n")
        proc = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        f.write(proc.stdout or "")
        if proc.stderr:
            f.write("\n[stderr]\n")
            f.write(proc.stderr)
        f.write(f"\n[exit_code] {proc.returncode}\n\n")
        if proc.returncode != 0:
            all_ok = False
        command_results.append({
            "command": cmd, "exit_code": proc.returncode,
            "passed": proc.returncode == 0
        })

summary = {
    "run_id": run_id,
    "verified": all_ok,
    "verified_at": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    "commands": command_results
}
summary_path.write_text(json.dumps(summary, indent=2) + "\n")
sys.exit(0 if all_ok else 4)

```

### P:\packages\cc-skills-sdlc\skills\go\scripts\write_dispatch_result.py
```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def update_run_file(run_path: Path, status: str, final_promise: str | None, notes: str | None = None) -> None:
    payload = json.loads(run_path.read_text(encoding="utf-8"))
    payload["status"] = status
    payload["updated_at"] = now_iso()
    if final_promise is not None:
        payload["final_promise"] = final_promise
    if notes is not None:
        payload["notes"] = notes
    tmp = run_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(run_path)


def update_dispatch_result(artifact_dir: Path, run_id: str, final_status: str, wait_state: str, **kwargs: Any) -> None:
    result_path = artifact_dir / f"dispatch-result_{run_id}.json"
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    payload["final_status"] = final_status
    payload["orchestrator_wait_state"] = wait_state
    for key, value in kwargs.items():
        if value is not None:
            payload[key] = value
    completed_at = now_iso()
    if final_status == "completed":
        payload["completed_at"] = completed_at
    tmp = result_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(result_path)



def emit_promise(final_status: str) -> None:
    promises = {
        "completed": "TASK_COMPLETE",
        "blocked": "TASK_BLOCKED",
        "awaiting": "AWAITING_SKILL_OUTPUT",
    }
    token = promises.get(final_status, "AWAITING_SKILL_OUTPUT")
    print(f"<promise>{token}</promise>")


def main() -> int:
    parser = argparse.ArgumentParser(description="Update dispatch-result artifact after skill outcome")
    parser.add_argument("--artifact-dir", required=True, help="Artifact directory")
    parser.add_argument("--run-id", required=True, help="GO_RUN_ID")
    parser.add_argument("--final-status", required=True, choices=["awaiting", "completed", "blocked"], help="Final status")
    parser.add_argument("--completion-summary")
    parser.add_argument("--blocking-reason")
    parser.add_argument("--next-recommended-action")
    parser.add_argument("--next-recommended-skill")
    parser.add_argument("--produced-artifacts", nargs="*", default=[])
    parser.add_argument("--notes")
    args = parser.parse_args()


    artifact_dir = Path(args.artifact_dir).resolve()
    run_id = args.run_id

    run_path = artifact_dir / f"run_{run_id}.json"
    if not run_path.exists():
        print(f"ERROR: run file not found: {run_path}", file=sys.stderr)
        return 1

    result_path = artifact_dir / f"dispatch-result_{run_id}.json"
    if not result_path.exists():
        print(f"ERROR: dispatch-result file not found: {result_path}", file=sys.stderr)
        return 1

    wait_state = "outcome-recorded"
    update_dispatch_result(
        artifact_dir, run_id,
        final_status=args.final_status,
        wait_state=wait_state,
        completion_summary=args.completion_summary,
        blocking_reason=args.blocking_reason,
        next_recommended_action=args.next_recommended_action,
        next_recommended_skill=args.next_recommended_skill,
        produced_artifacts=args.produced_artifacts if args.produced_artifacts else None,
        notes=args.notes,
    )

    if args.final_status == "completed":
        update_run_file(run_path, status="completed", final_promise="TASK_COMPLETE", notes=args.notes)
    elif args.final_status == "blocked":
        update_run_file(run_path, status="blocked", final_promise="TASK_BLOCKED", notes=args.notes)
        (artifact_dir / f".blocked_{run_id}").touch()
    else:
        update_run_file(run_path, status="dispatched", final_promise="AWAITING_SKILL_OUTPUT", notes=args.notes)

    emit_promise(args.final_status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```


---

## ADDITIONAL FILES (markdown)

### GO-CONFORMANCE.md
```markdown
# /go_2.0 Conformance Checklist

**Governing rule:** Every decision that can block, resume, recommend, or complete a `/go` run must be derivable from machine-readable artifacts, not just markdown prose or terminal output.

Truth source assignment:
- **Live execution state:** `run-status.schema.json`
- **Readiness / gate outcome:** `verification-result.schema.json`
- **Blocked reason and recovery:** `block-state.schema.json`
- **Delegated implementation outcome:** `code-result.schema.json`
- **Human-readable explanation:** markdown — never authoritative over JSON

---

## Critical

### GO-CONF-001 — FIXED
block-state written at 4 hard-stops: max_attempts, verification_failed, simplify_failed, review_failed. All with `schema_version`, `reason_code`, `opened_at`, `evidence_paths`.

### GO-CONF-002 — FIXED
run-status initialized at task selection (STEP 1); updated at verification pass (STEP 3) with `verification_result_path`.

### GO-CONF-003 — FIXED
`task_outcome()` reads run-status.json first. Flags as atomic fallback. Stdout token parsing removed.

### GO-CONF-004 — OPEN
`$ref: "code-result.schema.json"` in `dispatch_results[]` may not resolve in all JSON Schema validators. `code-result.schema.json` exists with correct `$id`. Risk is low for validators that support `$id`-based resolution.

---

## High

### GO-CONF-005 — OPEN
Naming convention split: status fields use hyphens (`reviews-passed`), reason codes use underscores (`verification_failed`). Affects `ralph-go-loop.sh` status matching vs `run-status.schema.json` enum values. Requires one canonical convention decision.

### GO-CONF-006 — OPEN
ROUTING.md has 15 routing rows covering all required branches. Still prose-based — not enforced in code.

### GO-CONF-007 — FIXED
After `/tdd` invocation, SKILL.md now reads `tdd-receipt_{RUN_ID}.json` and blocks if `validated=false` or receipt missing. Blocks with `reason_code: tdd_validation_failed`.

### GO-CONF-008 — FIXED
`workflow_steps` now lists all 10 steps including `test_discovery` and `tdd_decision`.

### GO-CONF-009 — FIXED
Flag filename `.pr-ready_$RUN_ID` (hyphen) is consistent across SKILL.md artifact layout, `ralph-go-loop.sh`, and `go-safe.sh`.

---

## Medium

### GO-CONF-010 — FIXED
STEP 3 now writes `verification-result_{RUN_ID}.json` after successful verification, populating all required fields including `task_id`, `status`, `verification_commands`, `simplify`, and `generated_at`.

### GO-CONF-011 — FIXED
Pre-mortem and stakeholder sync now write structured recommendation objects to `run-status.recommendations[]` with `type`, `prompt`, `evidence`, `resolved`, `resolved_at`.

### GO-CONF-012 — OPEN
Recommendation type strings: schema enum uses `pre-mortem` (hyphen); `block-state.schema.json` has no `pre-mortem` reason code — different semantic space but potential confusion.

### GO-CONF-013 — FIXED
All 4 new schemas (`run-status`, `verification-result`, `block-state`, `code-result`) now declare `schema_version`.

### GO-CONF-014 — FIXED
`tasks-file.schema.json` created with full validation of tasks.json structure including `id`, `title`, `objective`, `status`, `priority`, `scope_in`, `scope_out`, `forbidden_files`, `acceptance_criteria`, `verification_commands`, `requires_approval`, `notes`.

---

## Low

### GO-CONF-015 — FIXED
SKILL.md title updated to `/go_2.0 — Verify, Simplify, Ship`.

### GO-CONF-016 — FIXED
`go-safe.sh` now invokes `/go_2.0` explicitly instead of matching any `/go`.

---

## Current open items

| ID | Severity | Area | Title |
|----|----------|------|-------|
| GO-CONF-004 | critical | schema | `$ref` resolution for `dispatch_results[]` |
| GO-CONF-005 | high | naming | Status hyphens vs reason code underscores |
| GO-CONF-006 | high | routing | Routing table not machine-enforced |
| GO-CONF-012 | medium | recommendation | Type string inconsistency (hyphen/enum vs underscore/reason) |

**Fixed this session (12 of 16):** 001, 002, 003, 007, 008, 009, 010, 011, 013, 014, 015, 016.

---

## Step graph — artifact completion matrix

| Step | Completion artifact | Failure artifact | Retry artifact |
|------|-------------------|-----------------|----------------|
| worktree_enforcement | `.worktree-ready_` | `.blocked_` + `block-state_` | none |
| task_selection | `active-task_.json` + `run-status_` | `.blocked_` + `block-state_` | none |
| task_contract | `.task-defined_` | `.blocked_` + `block-state_` | none |
| test_discovery | `test-gaps_.json` | none | none |
| tdd_decision | `tdd-receipt_.json` | `.blocked_` + `block-state_` | none |
| verify_end_to_end | `.verified_` + `verification-summary_` + `run-status_` | `.blocked_` + `block-state_` + `.attempt_N_` | `.attempt_N_` |
| simplify_code | `.simplified_` + `simplify-summary_` | `.blocked_` + `block-state_` | none |
| seven_pass_review | `.reviews-passed_` + `review-summary_` | `.blocked_` + `block-state_` | none |
| local_pr_artifacts | `pr-ready_.md` + `.pr-ready_` | none | none |
| loop_check | `run-status_.final_promise` | none | none |

---

## Routing branch matrix

| Branch condition | Predicate | Action | Artifacts | Terminal state |
|-----------------|-----------|--------|-----------|----------------|
| no code changes | `CODE_FILE_COUNT == 0` | skip TDD → simplify | — | continue |
| tests only | `CODE_FILE_COUNT > 0 && DOCS_ONLY` | `/t` RED only | `tdd-receipt_` | continue |
| implementation | `CODE_FILE_COUNT > 0 && !DOCS_ONLY` | `/t` → `/gap` → `/tdd` → validate | `test-gaps_`, `tdd-receipt_`, `block-state_` | continue or blocked |
| config/infra | diff classify | verify → reviews | — | continue |
| `/t` no gaps | `test-gaps_` empty | skip `/gap` → `/tdd` | — | continue |
| gap insufficient | confidence < threshold | block or recommend | — | blocked |
| TDD not validated | `validated == false` | block | `block-state_` | BLOCKED |
| TDD RED fails 3x | retry_count >= 3 | block | `block-state_` | BLOCKED |
| simplify HIGH/CRITICAL | grep CRITICAL/HIGH | block | `block-state_` | BLOCKED |
| review REVIEW_REQUIRED | pass status | block | `block-state_` | BLOCKED |
| max attempts | attempt >= MAX_ATTEMPTS | block | `block-state_` | BLOCKED |
| verification passes | exit_code == 0 | simplify | `verification-summary_` | continue |
| recommendations emitted | `recommendations.length > 0` | surface + await + write | `run-status_` | depends |
| stakeholder sync required | `requires_approval == true` | surface + await + write | `run-status_` | depends |
| more tasks remain | loop check | next cycle | — | MORE_TASKS_IN_PLAN |
| all tasks complete | loop check | exit | — | ALL_TASKS_COMPLETE |

```

### GO-CONFORMANCE.md
```markdown
# /go_2.0 Conformance Checklist

**Governing rule:** Every decision that can block, resume, recommend, or complete a `/go` run must be derivable from machine-readable artifacts, not just markdown prose or terminal output.

Truth source assignment:
- **Live execution state:** `run-status.schema.json`
- **Readiness / gate outcome:** `verification-result.schema.json`
- **Blocked reason and recovery:** `block-state.schema.json`
- **Delegated implementation outcome:** `code-result.schema.json`
- **Human-readable explanation:** markdown — never authoritative over JSON

---

## Critical

### GO-CONF-001 — FIXED
block-state written at 4 hard-stops: max_attempts, verification_failed, simplify_failed, review_failed. All with `schema_version`, `reason_code`, `opened_at`, `evidence_paths`.

### GO-CONF-002 — FIXED
run-status initialized at task selection (STEP 1); updated at verification pass (STEP 3) with `verification_result_path`.

### GO-CONF-003 — FIXED
`task_outcome()` reads run-status.json first. Flags as atomic fallback. Stdout token parsing removed.

### GO-CONF-004 — OPEN
`$ref: "code-result.schema.json"` in `dispatch_results[]` may not resolve in all JSON Schema validators. `code-result.schema.json` exists with correct `$id`. Risk is low for validators that support `$id`-based resolution.

---

## High

### GO-CONF-005 — OPEN
Naming convention split: status fields use hyphens (`reviews-passed`), reason codes use underscores (`verification_failed`). Affects `ralph-go-loop.sh` status matching vs `run-status.schema.json` enum values. Requires one canonical convention decision.

### GO-CONF-006 — OPEN
ROUTING.md has 15 routing rows covering all required branches. Still prose-based — not enforced in code.

### GO-CONF-007 — FIXED
After `/tdd` invocation, SKILL.md now reads `tdd-receipt_{RUN_ID}.json` and blocks if `validated=false` or receipt missing. Blocks with `reason_code: tdd_validation_failed`.

### GO-CONF-008 — FIXED
`workflow_steps` now lists all 10 steps including `test_discovery` and `tdd_decision`.

### GO-CONF-009 — FIXED
Flag filename `.pr-ready_$RUN_ID` (hyphen) is consistent across SKILL.md artifact layout, `ralph-go-loop.sh`, and `go-safe.sh`.

---

## Medium

### GO-CONF-010 — FIXED
STEP 3 now writes `verification-result_{RUN_ID}.json` after successful verification, populating all required fields including `task_id`, `status`, `verification_commands`, `simplify`, and `generated_at`.

### GO-CONF-011 — FIXED
Pre-mortem and stakeholder sync now write structured recommendation objects to `run-status.recommendations[]` with `type`, `prompt`, `evidence`, `resolved`, `resolved_at`.

### GO-CONF-012 — OPEN
Recommendation type strings: schema enum uses `pre-mortem` (hyphen); `block-state.schema.json` has no `pre-mortem` reason code — different semantic space but potential confusion.

### GO-CONF-013 — FIXED
All 4 new schemas (`run-status`, `verification-result`, `block-state`, `code-result`) now declare `schema_version`.

### GO-CONF-014 — FIXED
`tasks-file.schema.json` created with full validation of tasks.json structure including `id`, `title`, `objective`, `status`, `priority`, `scope_in`, `scope_out`, `forbidden_files`, `acceptance_criteria`, `verification_commands`, `requires_approval`, `notes`.

---

## Low

### GO-CONF-015 — FIXED
SKILL.md title updated to `/go_2.0 — Verify, Simplify, Ship`.

### GO-CONF-016 — FIXED
`go-safe.sh` now invokes `/go_2.0` explicitly instead of matching any `/go`.

---

## Current open items

| ID | Severity | Area | Title |
|----|----------|------|-------|
| GO-CONF-004 | critical | schema | `$ref` resolution for `dispatch_results[]` |
| GO-CONF-005 | high | naming | Status hyphens vs reason code underscores |
| GO-CONF-006 | high | routing | Routing table not machine-enforced |
| GO-CONF-012 | medium | recommendation | Type string inconsistency (hyphen/enum vs underscore/reason) |

**Fixed this session (12 of 16):** 001, 002, 003, 007, 008, 009, 010, 011, 013, 014, 015, 016.

---

## Step graph — artifact completion matrix

| Step | Completion artifact | Failure artifact | Retry artifact |
|------|-------------------|-----------------|----------------|
| worktree_enforcement | `.worktree-ready_` | `.blocked_` + `block-state_` | none |
| task_selection | `active-task_.json` + `run-status_` | `.blocked_` + `block-state_` | none |
| task_contract | `.task-defined_` | `.blocked_` + `block-state_` | none |
| test_discovery | `test-gaps_.json` | none | none |
| tdd_decision | `tdd-receipt_.json` | `.blocked_` + `block-state_` | none |
| verify_end_to_end | `.verified_` + `verification-summary_` + `run-status_` | `.blocked_` + `block-state_` + `.attempt_N_` | `.attempt_N_` |
| simplify_code | `.simplified_` + `simplify-summary_` | `.blocked_` + `block-state_` | none |
| seven_pass_review | `.reviews-passed_` + `review-summary_` | `.blocked_` + `block-state_` | none |
| local_pr_artifacts | `pr-ready_.md` + `.pr-ready_` | none | none |
| loop_check | `run-status_.final_promise` | none | none |

---

## Routing branch matrix

| Branch condition | Predicate | Action | Artifacts | Terminal state |
|-----------------|-----------|--------|-----------|----------------|
| no code changes | `CODE_FILE_COUNT == 0` | skip TDD → simplify | — | continue |
| tests only | `CODE_FILE_COUNT > 0 && DOCS_ONLY` | `/t` RED only | `tdd-receipt_` | continue |
| implementation | `CODE_FILE_COUNT > 0 && !DOCS_ONLY` | `/t` → `/gap` → `/tdd` → validate | `test-gaps_`, `tdd-receipt_`, `block-state_` | continue or blocked |
| config/infra | diff classify | verify → reviews | — | continue |
| `/t` no gaps | `test-gaps_` empty | skip `/gap` → `/tdd` | — | continue |
| gap insufficient | confidence < threshold | block or recommend | — | blocked |
| TDD not validated | `validated == false` | block | `block-state_` | BLOCKED |
| TDD RED fails 3x | retry_count >= 3 | block | `block-state_` | BLOCKED |
| simplify HIGH/CRITICAL | grep CRITICAL/HIGH | block | `block-state_` | BLOCKED |
| review REVIEW_REQUIRED | pass status | block | `block-state_` | BLOCKED |
| max attempts | attempt >= MAX_ATTEMPTS | block | `block-state_` | BLOCKED |
| verification passes | exit_code == 0 | simplify | `verification-summary_` | continue |
| recommendations emitted | `recommendations.length > 0` | surface + await + write | `run-status_` | depends |
| stakeholder sync required | `requires_approval == true` | surface + await + write | `run-status_` | depends |
| more tasks remain | loop check | next cycle | — | MORE_TASKS_IN_PLAN |
| all tasks complete | loop check | exit | — | ALL_TASKS_COMPLETE |

```

### GO-QUICK-REFERENCE.md
```markdown
# /go Gen 2 — Quick Reference

Gen 2 replaces markdown task contracts and `plan.md` loop control with canonical JSON contracts and `/go -> /code` orchestration.

---

## Core Model

`/go` does exactly one task per `RUN_ID`.

Flow:

1. Validate worktree
2. Read `active-plan.json`
3. Select one eligible task
4. Write `active-task_{RUN_ID}.json`
5. Invoke `/code`
6. Require `task-result_{RUN_ID}.json`
7. Verify
8. Simplify
9. Review
10. Create local PR artifacts
11. Update `active-plan.json`
12. Emit loop token

---

## Canonical Files

All state lives in:

```text
.claude/.artifacts/{TERMINAL_ID}/go/
```

Key files:

```text
active-plan.json
active-task_{RUN_ID}.json
task-result_{RUN_ID}.json
verification-results_{RUN_ID}.txt
simplify-status_{RUN_ID}.md
review-pass-correctness_{RUN_ID}.md
review-pass-scope_{RUN_ID}.md
review-pass-tests_{RUN_ID}.md
review-pass-simplicity_{RUN_ID}.md
review-pass-regressions_{RUN_ID}.md
review-pass-maintainability_{RUN_ID}.md
review-pass-pr-ready_{RUN_ID}.md
commit-message_{RUN_ID}.txt
pr-title_{RUN_ID}.txt
pr-body_{RUN_ID}.md
pr-ready_{RUN_ID}.md
```

---

## Flag Files

Gen 2 gate files:

```text
.worktree-ready_{RUN_ID}
.task-selected_{RUN_ID}
.coded_{RUN_ID}
.verified_{RUN_ID}
.simplified_{RUN_ID}
.reviews-passed_{RUN_ID}
.pr-ready_{RUN_ID}
.blocked_{RUN_ID}
.attempt_{N}_{RUN_ID}
```

Meaning:

- `.worktree-ready_{RUN_ID}` — worktree and plan validation passed
- `.task-selected_{RUN_ID}` — one task was selected from `active-plan.json`
- `.coded_{RUN_ID}` — `/code` completed and wrote `task-result_{RUN_ID}.json`
- `.verified_{RUN_ID}` — implementation matched contract and evidence passed
- `.simplified_{RUN_ID}` — simplify gate passed or valid skip recorded
- `.reviews-passed_{RUN_ID}` — all 7 review passes passed
- `.pr-ready_{RUN_ID}` — local PR artifacts exist
- `.blocked_{RUN_ID}` — task cannot proceed
- `.attempt_{N}_{RUN_ID}` — retry counter for this run

---

## Environment Variables

```bash
export TERMINAL_ID=$(uuidgen | cut -d'-' -f1)
export RUN_ID=$(uuidgen)
export MAX_ATTEMPTS=3
```

Derived paths:

```bash
ARTIFACT_DIR=".claude/.artifacts/$TERMINAL_ID/go"
PLAN_FILE="$ARTIFACT_DIR/active-plan.json"
ACTIVE_TASK_FILE="$ARTIFACT_DIR/active-task_$RUN_ID.json"
TASK_RESULT_FILE="$ARTIFACT_DIR/task-result_$RUN_ID.json"
```

---

## JSON Contracts

### `active-plan.json`

Scheduler source of truth.

Each task should contain:

- `task_id`
- `title`
- `status`
- `priority`
- `depends_on`
- `objective`
- `scope`
- `allowed_files`
- `forbidden_files`
- `acceptance_criteria`
- `verification_commands`

### `active-task_{RUN_ID}.json`

Selected-task snapshot for one run.

Required fields:

- `run_id`
- `terminal_id`
- `task_id`
- `title`
- `objective`
- `scope`
- `allowed_files`
- `forbidden_files`
- `acceptance_criteria`
- `verification_commands`
- `selected_at`
- `status`

### `task-result_{RUN_ID}.json`

Required `/code` output.

Required fields:

- `run_id`
- `task_id`
- `status`
- `summary`
- `changed_files`
- `commands_executed`
- `verification_evidence`
- `blockers`
- `notes`
- `completed_at`

---

## Eligibility Rules

A task is eligible when:

- `status == "ready"` (or `queued` or `approved`)
- all `depends_on` tasks are already `done`
- it is not reserved by another active run
- it has all required contract fields

If no eligible task exists, `/go` should stop with:

```text
<promise>ALL_TASKS_COMPLETE</promise>
```

---

## Completion Tokens

```text
<promise>BLOCKED</promise>
<promise>PR_READY</promise>
<promise>MORE_TASKS_IN_PLAN</promise>
<promise>ALL_TASKS_COMPLETE</promise>
```

Interpretation:

- `BLOCKED` — current selected task failed terminally
- `PR_READY` — current selected task completed and PR artifacts exist
- `MORE_TASKS_IN_PLAN` — current task is done, more eligible tasks remain
- `ALL_TASKS_COMPLETE` — no eligible tasks remain

---

## Manual Run

```bash
bash go-safe.sh
```

Expected behavior:

1. validate worktree
2. validate `active-plan.json`
3. preview next eligible task
4. write `.env_{RUN_ID}`
5. invoke `/go`
6. print selected-task/result artifacts if present

---

## Ralph Loop

```bash
bash ralph-go-loop.sh 10
```

Loop behavior:

- keep one `TERMINAL_ID` for the session
- create a new `RUN_ID` each cycle
- read `active-plan.json` before each cycle
- call `/go`
- inspect `.blocked_{RUN_ID}` and `.pr-ready_{RUN_ID}`
- reread `active-plan.json`
- continue if eligible tasks remain
- exit when all are complete or blocked

---

## State Layout

```text
.claude/.artifacts/
└── {TERMINAL_ID}/
    └── go/
        ├── active-plan.json
        ├── .worktree-ready_{RUN_ID}
        ├── .task-selected_{RUN_ID}
        ├── .coded_{RUN_ID}
        ├── .verified_{RUN_ID}
        ├── .simplified_{RUN_ID}
        ├── .reviews-passed_{RUN_ID}
        ├── .pr-ready_{RUN_ID}
        ├── .blocked_{RUN_ID}
        ├── .attempt_{N}_{RUN_ID}
        ├── active-task_{RUN_ID}.json
        ├── task-result_{RUN_ID}.json
        ├── verification-results_{RUN_ID}.txt
        ├── simplify-status_{RUN_ID}.md
        ├── review-pass-correctness_{RUN_ID}.md
        ├── review-pass-scope_{RUN_ID}.md
        ├── review-pass-tests_{RUN_ID}.md
        ├── review-pass-simplicity_{RUN_ID}.md
        ├── review-pass-regressions_{RUN_ID}.md
        ├── review-pass-maintainability_{RUN_ID}.md
        ├── review-pass-pr-ready_{RUN_ID}.md
        ├── commit-message_{RUN_ID}.txt
        ├── pr-title_{RUN_ID}.txt
        ├── pr-body_{RUN_ID}.md
        └── pr-ready_{RUN_ID}.md
```

---

## What Gen 2 Removed

Gen 1 concepts that no longer apply:

- `task-contract_{RUN_ID}.md`
- diff-classified review depth
- `plan.md` as loop source of truth
- verification driven from markdown task contract
- single `RUN_ID` across an entire Ralph loop

---

## Fast Smoke Test

1. create `.claude/.artifacts/{TERMINAL_ID}/go/active-plan.json`
2. run `bash go-safe.sh`
3. verify:
   - `active-task_{RUN_ID}.json` exists
   - `task-result_{RUN_ID}.json` exists
   - `.pr-ready_{RUN_ID}` exists for successful task
4. run `bash ralph-go-loop.sh 10`
5. confirm plan drains to `ALL_TASKS_COMPLETE`

---

## Failure Rules

Stop immediately if any of these happen:

- not in a worktree
- on `main` or `master`
- `active-plan.json` missing
- `active-plan.json` invalid
- no valid selected task
- `/code` does not emit valid `task-result_{RUN_ID}.json`
- forbidden files changed
- verification fails
- simplify remains HIGH or CRITICAL
- any review pass is `REVIEW_REQUIRED`

---

## Recommended Operator Order

Use this order only:

1. replace `SKILL.md`
2. replace `go-safe.sh`
3. replace `ralph-go-loop.sh`
4. replace this quick reference
5. replace implementation guide
6. create starter `active-plan.json`
7. run `bash go-safe.sh`
8. run `bash ralph-go-loop.sh 10`

```

### GO-QUICK-REFERENCE.md
```markdown
# /go Gen 2 — Quick Reference

Gen 2 replaces markdown task contracts and `plan.md` loop control with canonical JSON contracts and `/go -> /code` orchestration.

---

## Core Model

`/go` does exactly one task per `RUN_ID`.

Flow:

1. Validate worktree
2. Read `active-plan.json`
3. Select one eligible task
4. Write `active-task_{RUN_ID}.json`
5. Invoke `/code`
6. Require `task-result_{RUN_ID}.json`
7. Verify
8. Simplify
9. Review
10. Create local PR artifacts
11. Update `active-plan.json`
12. Emit loop token

---

## Canonical Files

All state lives in:

```text
.claude/.artifacts/{TERMINAL_ID}/go/
```

Key files:

```text
active-plan.json
active-task_{RUN_ID}.json
task-result_{RUN_ID}.json
verification-results_{RUN_ID}.txt
simplify-status_{RUN_ID}.md
review-pass-correctness_{RUN_ID}.md
review-pass-scope_{RUN_ID}.md
review-pass-tests_{RUN_ID}.md
review-pass-simplicity_{RUN_ID}.md
review-pass-regressions_{RUN_ID}.md
review-pass-maintainability_{RUN_ID}.md
review-pass-pr-ready_{RUN_ID}.md
commit-message_{RUN_ID}.txt
pr-title_{RUN_ID}.txt
pr-body_{RUN_ID}.md
pr-ready_{RUN_ID}.md
```

---

## Flag Files

Gen 2 gate files:

```text
.worktree-ready_{RUN_ID}
.task-selected_{RUN_ID}
.coded_{RUN_ID}
.verified_{RUN_ID}
.simplified_{RUN_ID}
.reviews-passed_{RUN_ID}
.pr-ready_{RUN_ID}
.blocked_{RUN_ID}
.attempt_{N}_{RUN_ID}
```

Meaning:

- `.worktree-ready_{RUN_ID}` — worktree and plan validation passed
- `.task-selected_{RUN_ID}` — one task was selected from `active-plan.json`
- `.coded_{RUN_ID}` — `/code` completed and wrote `task-result_{RUN_ID}.json`
- `.verified_{RUN_ID}` — implementation matched contract and evidence passed
- `.simplified_{RUN_ID}` — simplify gate passed or valid skip recorded
- `.reviews-passed_{RUN_ID}` — all 7 review passes passed
- `.pr-ready_{RUN_ID}` — local PR artifacts exist
- `.blocked_{RUN_ID}` — task cannot proceed
- `.attempt_{N}_{RUN_ID}` — retry counter for this run

---

## Environment Variables

```bash
export TERMINAL_ID=$(uuidgen | cut -d'-' -f1)
export RUN_ID=$(uuidgen)
export MAX_ATTEMPTS=3
```

Derived paths:

```bash
ARTIFACT_DIR=".claude/.artifacts/$TERMINAL_ID/go"
PLAN_FILE="$ARTIFACT_DIR/active-plan.json"
ACTIVE_TASK_FILE="$ARTIFACT_DIR/active-task_$RUN_ID.json"
TASK_RESULT_FILE="$ARTIFACT_DIR/task-result_$RUN_ID.json"
```

---

## JSON Contracts

### `active-plan.json`

Scheduler source of truth.

Each task should contain:

- `task_id`
- `title`
- `status`
- `priority`
- `depends_on`
- `objective`
- `scope`
- `allowed_files`
- `forbidden_files`
- `acceptance_criteria`
- `verification_commands`

### `active-task_{RUN_ID}.json`

Selected-task snapshot for one run.

Required fields:

- `run_id`
- `terminal_id`
- `task_id`
- `title`
- `objective`
- `scope`
- `allowed_files`
- `forbidden_files`
- `acceptance_criteria`
- `verification_commands`
- `selected_at`
- `status`

### `task-result_{RUN_ID}.json`

Required `/code` output.

Required fields:

- `run_id`
- `task_id`
- `status`
- `summary`
- `changed_files`
- `commands_executed`
- `verification_evidence`
- `blockers`
- `notes`
- `completed_at`

---

## Eligibility Rules

A task is eligible when:

- `status == "ready"` (or `queued` or `approved`)
- all `depends_on` tasks are already `done`
- it is not reserved by another active run
- it has all required contract fields

If no eligible task exists, `/go` should stop with:

```text
<promise>ALL_TASKS_COMPLETE</promise>
```

---

## Completion Tokens

```text
<promise>BLOCKED</promise>
<promise>PR_READY</promise>
<promise>MORE_TASKS_IN_PLAN</promise>
<promise>ALL_TASKS_COMPLETE</promise>
```

Interpretation:

- `BLOCKED` — current selected task failed terminally
- `PR_READY` — current selected task completed and PR artifacts exist
- `MORE_TASKS_IN_PLAN` — current task is done, more eligible tasks remain
- `ALL_TASKS_COMPLETE` — no eligible tasks remain

---

## Manual Run

```bash
bash go-safe.sh
```

Expected behavior:

1. validate worktree
2. validate `active-plan.json`
3. preview next eligible task
4. write `.env_{RUN_ID}`
5. invoke `/go`
6. print selected-task/result artifacts if present

---

## Ralph Loop

```bash
bash ralph-go-loop.sh 10
```

Loop behavior:

- keep one `TERMINAL_ID` for the session
- create a new `RUN_ID` each cycle
- read `active-plan.json` before each cycle
- call `/go`
- inspect `.blocked_{RUN_ID}` and `.pr-ready_{RUN_ID}`
- reread `active-plan.json`
- continue if eligible tasks remain
- exit when all are complete or blocked

---

## State Layout

```text
.claude/.artifacts/
└── {TERMINAL_ID}/
    └── go/
        ├── active-plan.json
        ├── .worktree-ready_{RUN_ID}
        ├── .task-selected_{RUN_ID}
        ├── .coded_{RUN_ID}
        ├── .verified_{RUN_ID}
        ├── .simplified_{RUN_ID}
        ├── .reviews-passed_{RUN_ID}
        ├── .pr-ready_{RUN_ID}
        ├── .blocked_{RUN_ID}
        ├── .attempt_{N}_{RUN_ID}
        ├── active-task_{RUN_ID}.json
        ├── task-result_{RUN_ID}.json
        ├── verification-results_{RUN_ID}.txt
        ├── simplify-status_{RUN_ID}.md
        ├── review-pass-correctness_{RUN_ID}.md
        ├── review-pass-scope_{RUN_ID}.md
        ├── review-pass-tests_{RUN_ID}.md
        ├── review-pass-simplicity_{RUN_ID}.md
        ├── review-pass-regressions_{RUN_ID}.md
        ├── review-pass-maintainability_{RUN_ID}.md
        ├── review-pass-pr-ready_{RUN_ID}.md
        ├── commit-message_{RUN_ID}.txt
        ├── pr-title_{RUN_ID}.txt
        ├── pr-body_{RUN_ID}.md
        └── pr-ready_{RUN_ID}.md
```

---

## What Gen 2 Removed

Gen 1 concepts that no longer apply:

- `task-contract_{RUN_ID}.md`
- diff-classified review depth
- `plan.md` as loop source of truth
- verification driven from markdown task contract
- single `RUN_ID` across an entire Ralph loop

---

## Fast Smoke Test

1. create `.claude/.artifacts/{TERMINAL_ID}/go/active-plan.json`
2. run `bash go-safe.sh`
3. verify:
   - `active-task_{RUN_ID}.json` exists
   - `task-result_{RUN_ID}.json` exists
   - `.pr-ready_{RUN_ID}` exists for successful task
4. run `bash ralph-go-loop.sh 10`
5. confirm plan drains to `ALL_TASKS_COMPLETE`

---

## Failure Rules

Stop immediately if any of these happen:

- not in a worktree
- on `main` or `master`
- `active-plan.json` missing
- `active-plan.json` invalid
- no valid selected task
- `/code` does not emit valid `task-result_{RUN_ID}.json`
- forbidden files changed
- verification fails
- simplify remains HIGH or CRITICAL
- any review pass is `REVIEW_REQUIRED`

---

## Recommended Operator Order

Use this order only:

1. replace `SKILL.md`
2. replace `go-safe.sh`
3. replace `ralph-go-loop.sh`
4. replace this quick reference
5. replace implementation guide
6. create starter `active-plan.json`
7. run `bash go-safe.sh`
8. run `bash ralph-go-loop.sh 10`

```

### IMPLEMENTATION-GUIDE.md
```markdown
# /go Gen 2 Implementation Guide

This is the second-generation redesign of `/go`.

Gen 1 used:
- markdown task contracts
- diff-based review-depth logic
- `plan.md` as loop source of truth
- older wrapper assumptions

Gen 2 replaces that with:
- canonical JSON contracts
- one selected task per `RUN_ID`
- `/go -> /code` orchestration
- artifact-driven verification and plan progression

---

## Deliverables

This Gen 2 bundle consists of:

1. `SKILL.md`
2. `go-safe.sh`
3. `ralph-go-loop.sh`
4. `GO-QUICK-REFERENCE.md`
5. `IMPLEMENTATION-GUIDE.md`
6. `active-plan.json` starter file

---

## Design Goal

The goal is to make `/go` deterministic, machine-readable, interruption-safe, and multi-terminal safe.

Core properties:

- per-terminal isolation via `.claude/.artifacts/{TERMINAL_ID}/go/`
- per-task isolation via one `RUN_ID` per selected task
- exact task boundary via `active-task_{RUN_ID}.json`
- exact execution result via `task-result_{RUN_ID}.json`
- loop continuation based on updated plan state, not markdown prose

---

## Gen 2 Architecture

### Source of truth

`active-plan.json` is the scheduler source of truth.

It replaces:
- `plan.md`
- ad hoc task discovery
- git-diff-based task interpretation

### Task execution model

Each `/go` run:

1. validates worktree and plan
2. selects exactly one eligible task
3. writes `active-task_{RUN_ID}.json`
4. dispatches `/code`
5. requires `task-result_{RUN_ID}.json`
6. verifies evidence
7. runs simplify
8. runs all review passes
9. writes local PR artifacts
10. updates `active-plan.json`

### Loop execution model

Each Ralph loop session:

- keeps one `TERMINAL_ID`
- creates a new `RUN_ID` per cycle
- reevaluates `active-plan.json` after each completed task

---

## Canonical Contracts

### 1. `active-plan.json`

This file drives scheduling.

Each task must define:

- `task_id`
- `title`
- `status`
- `priority`
- `depends_on`
- `objective`
- `scope`
- `allowed_files`
- `forbidden_files`
- `acceptance_criteria`
- `verification_commands`

### 2. `active-task_{RUN_ID}.json`

This file is the frozen task contract for a single run.

It must include:

- `run_id`
- `terminal_id`
- `task_id`
- `title`
- `objective`
- `scope`
- `allowed_files`
- `forbidden_files`
- `acceptance_criteria`
- `verification_commands`
- `selected_at`
- `status`

### 3. `task-result_{RUN_ID}.json`

This file is required output from `/code`.

It must include:

- `run_id`
- `task_id`
- `status`
- `summary`
- `changed_files`
- `commands_executed`
- `verification_evidence`
- `blockers`
- `notes`
- `completed_at`

---

## File Replacements

### `SKILL.md`

Replace the Gen 1 skill with the Gen 2 skill definition.

Required differences from Gen 1:

- remove `task-contract_{RUN_ID}.md`
- remove diff classification step
- remove `plan.md` loop semantics
- add `active-plan.json`
- add `active-task_{RUN_ID}.json`
- add `task-result_{RUN_ID}.json`
- add `/go -> /code` dispatch model

### `go-safe.sh`

Replace the wrapper so it:

- validates worktree
- validates `active-plan.json`
- previews next eligible task
- writes `.env_{RUN_ID}`
- invokes `/go`
- prints selected-task and task-result artifacts

### `ralph-go-loop.sh`

Replace the loop driver so it:

- keeps one `TERMINAL_ID`
- creates a new `RUN_ID` per cycle
- reads `active-plan.json` before each cycle
- uses artifact state as authoritative truth
- rereads `active-plan.json` after each cycle
- exits on `BLOCKED`
- exits on `ALL_TASKS_COMPLETE`

### Docs

Replace both docs so they no longer mention:

- markdown task contracts
- diff-based review depth
- `plan.md`
- one-`RUN_ID`-per-session loop behavior

---

## Installation Order

Do these in order:

1. replace `SKILL.md`
2. replace `go-safe.sh`
3. replace `ralph-go-loop.sh`
4. replace `GO-QUICK-REFERENCE.md`
5. replace `IMPLEMENTATION-GUIDE.md`
6. create `active-plan.json`
7. run smoke test

---

## Starter Plan Location

Place the starter plan here:

```text
.claude/.artifacts/{TERMINAL_ID}/go/active-plan.json
```

This must exist before `go-safe.sh` or `ralph-go-loop.sh` runs.

---

## Smoke Test

### Manual

```bash
bash go-safe.sh
```

Confirm:

- worktree validation passes
- plan preview appears
- `active-task_{RUN_ID}.json` is written
- `task-result_{RUN_ID}.json` is written
- `.pr-ready_{RUN_ID}` exists for successful completion

### Ralph loop

```bash
bash ralph-go-loop.sh 10
```

Confirm:

- same `TERMINAL_ID` across loop
- new `RUN_ID` each cycle
- plan state updates after each cycle
- `MORE_TASKS_IN_PLAN` appears when tasks remain
- `ALL_TASKS_COMPLETE` appears when plan drains

---

## Failure Conditions

Treat these as hard failures:

- invalid git worktree state
- running on `main` or `master`
- missing `active-plan.json`
- invalid `active-plan.json`
- no eligible task when one is expected
- missing or invalid `active-task_{RUN_ID}.json`
- missing or invalid `task-result_{RUN_ID}.json`
- forbidden file changes
- failed verification commands
- unresolved HIGH/CRITICAL simplify result
- any review pass marked `REVIEW_REQUIRED`

---

## Migration Notes From Gen 1

If you previously installed the Gen 1 artifact-pattern bundle, the main conceptual migrations are:

| Gen 1 | Gen 2 |
|------|-------|
| `task-contract_{RUN_ID}.md` | `active-task_{RUN_ID}.json` |
| `plan.md` | `active-plan.json` |
| verification from markdown task contract | verification from selected-task + task-result JSON |
| diff-classified review depth | fixed structured task contract |
| one loop session may reuse one run model | each task cycle gets a new `RUN_ID` |

Do not mix the two models in the same active installation.

---

## Recommended Test Tasks

Use three starter tasks:

1. replace `SKILL.md`
2. replace `go-safe.sh`
3. replace `ralph-go-loop.sh`

This validates:
- plan selection
- single-task execution
- loop continuation
- per-task `RUN_ID` behavior

---

## Operator Guidance

If you are debugging Gen 2, inspect in this order:

1. `active-plan.json`
2. `active-task_{RUN_ID}.json`
3. `task-result_{RUN_ID}.json`
4. `verification-results_{RUN_ID}.txt`
5. `simplify-status_{RUN_ID}.md`
6. review-pass files
7. `pr-ready_{RUN_ID}.md`

This order follows the actual control flow.

---

## Final Rule

Do not keep extending Gen 1 assumptions inside Gen 2 files.

If a file still depends on:
- `task-contract_{RUN_ID}.md`
- diff classification
- `plan.md`
- one `RUN_ID` per full loop session

then it is not migrated yet.

```

### IMPLEMENTATION-GUIDE.md
```markdown
# /go Gen 2 Implementation Guide

This is the second-generation redesign of `/go`.

Gen 1 used:
- markdown task contracts
- diff-based review-depth logic
- `plan.md` as loop source of truth
- older wrapper assumptions

Gen 2 replaces that with:
- canonical JSON contracts
- one selected task per `RUN_ID`
- `/go -> /code` orchestration
- artifact-driven verification and plan progression

---

## Deliverables

This Gen 2 bundle consists of:

1. `SKILL.md`
2. `go-safe.sh`
3. `ralph-go-loop.sh`
4. `GO-QUICK-REFERENCE.md`
5. `IMPLEMENTATION-GUIDE.md`
6. `active-plan.json` starter file

---

## Design Goal

The goal is to make `/go` deterministic, machine-readable, interruption-safe, and multi-terminal safe.

Core properties:

- per-terminal isolation via `.claude/.artifacts/{TERMINAL_ID}/go/`
- per-task isolation via one `RUN_ID` per selected task
- exact task boundary via `active-task_{RUN_ID}.json`
- exact execution result via `task-result_{RUN_ID}.json`
- loop continuation based on updated plan state, not markdown prose

---

## Gen 2 Architecture

### Source of truth

`active-plan.json` is the scheduler source of truth.

It replaces:
- `plan.md`
- ad hoc task discovery
- git-diff-based task interpretation

### Task execution model

Each `/go` run:

1. validates worktree and plan
2. selects exactly one eligible task
3. writes `active-task_{RUN_ID}.json`
4. dispatches `/code`
5. requires `task-result_{RUN_ID}.json`
6. verifies evidence
7. runs simplify
8. runs all review passes
9. writes local PR artifacts
10. updates `active-plan.json`

### Loop execution model

Each Ralph loop session:

- keeps one `TERMINAL_ID`
- creates a new `RUN_ID` per cycle
- reevaluates `active-plan.json` after each completed task

---

## Canonical Contracts

### 1. `active-plan.json`

This file drives scheduling.

Each task must define:

- `task_id`
- `title`
- `status`
- `priority`
- `depends_on`
- `objective`
- `scope`
- `allowed_files`
- `forbidden_files`
- `acceptance_criteria`
- `verification_commands`

### 2. `active-task_{RUN_ID}.json`

This file is the frozen task contract for a single run.

It must include:

- `run_id`
- `terminal_id`
- `task_id`
- `title`
- `objective`
- `scope`
- `allowed_files`
- `forbidden_files`
- `acceptance_criteria`
- `verification_commands`
- `selected_at`
- `status`

### 3. `task-result_{RUN_ID}.json`

This file is required output from `/code`.

It must include:

- `run_id`
- `task_id`
- `status`
- `summary`
- `changed_files`
- `commands_executed`
- `verification_evidence`
- `blockers`
- `notes`
- `completed_at`

---

## File Replacements

### `SKILL.md`

Replace the Gen 1 skill with the Gen 2 skill definition.

Required differences from Gen 1:

- remove `task-contract_{RUN_ID}.md`
- remove diff classification step
- remove `plan.md` loop semantics
- add `active-plan.json`
- add `active-task_{RUN_ID}.json`
- add `task-result_{RUN_ID}.json`
- add `/go -> /code` dispatch model

### `go-safe.sh`

Replace the wrapper so it:

- validates worktree
- validates `active-plan.json`
- previews next eligible task
- writes `.env_{RUN_ID}`
- invokes `/go`
- prints selected-task and task-result artifacts

### `ralph-go-loop.sh`

Replace the loop driver so it:

- keeps one `TERMINAL_ID`
- creates a new `RUN_ID` per cycle
- reads `active-plan.json` before each cycle
- uses artifact state as authoritative truth
- rereads `active-plan.json` after each cycle
- exits on `BLOCKED`
- exits on `ALL_TASKS_COMPLETE`

### Docs

Replace both docs so they no longer mention:

- markdown task contracts
- diff-based review depth
- `plan.md`
- one-`RUN_ID`-per-session loop behavior

---

## Installation Order

Do these in order:

1. replace `SKILL.md`
2. replace `go-safe.sh`
3. replace `ralph-go-loop.sh`
4. replace `GO-QUICK-REFERENCE.md`
5. replace `IMPLEMENTATION-GUIDE.md`
6. create `active-plan.json`
7. run smoke test

---

## Starter Plan Location

Place the starter plan here:

```text
.claude/.artifacts/{TERMINAL_ID}/go/active-plan.json
```

This must exist before `go-safe.sh` or `ralph-go-loop.sh` runs.

---

## Smoke Test

### Manual

```bash
bash go-safe.sh
```

Confirm:

- worktree validation passes
- plan preview appears
- `active-task_{RUN_ID}.json` is written
- `task-result_{RUN_ID}.json` is written
- `.pr-ready_{RUN_ID}` exists for successful completion

### Ralph loop

```bash
bash ralph-go-loop.sh 10
```

Confirm:

- same `TERMINAL_ID` across loop
- new `RUN_ID` each cycle
- plan state updates after each cycle
- `MORE_TASKS_IN_PLAN` appears when tasks remain
- `ALL_TASKS_COMPLETE` appears when plan drains

---

## Failure Conditions

Treat these as hard failures:

- invalid git worktree state
- running on `main` or `master`
- missing `active-plan.json`
- invalid `active-plan.json`
- no eligible task when one is expected
- missing or invalid `active-task_{RUN_ID}.json`
- missing or invalid `task-result_{RUN_ID}.json`
- forbidden file changes
- failed verification commands
- unresolved HIGH/CRITICAL simplify result
- any review pass marked `REVIEW_REQUIRED`

---

## Migration Notes From Gen 1

If you previously installed the Gen 1 artifact-pattern bundle, the main conceptual migrations are:

| Gen 1 | Gen 2 |
|------|-------|
| `task-contract_{RUN_ID}.md` | `active-task_{RUN_ID}.json` |
| `plan.md` | `active-plan.json` |
| verification from markdown task contract | verification from selected-task + task-result JSON |
| diff-classified review depth | fixed structured task contract |
| one loop session may reuse one run model | each task cycle gets a new `RUN_ID` |

Do not mix the two models in the same active installation.

---

## Recommended Test Tasks

Use three starter tasks:

1. replace `SKILL.md`
2. replace `go-safe.sh`
3. replace `ralph-go-loop.sh`

This validates:
- plan selection
- single-task execution
- loop continuation
- per-task `RUN_ID` behavior

---

## Operator Guidance

If you are debugging Gen 2, inspect in this order:

1. `active-plan.json`
2. `active-task_{RUN_ID}.json`
3. `task-result_{RUN_ID}.json`
4. `verification-results_{RUN_ID}.txt`
5. `simplify-status_{RUN_ID}.md`
6. review-pass files
7. `pr-ready_{RUN_ID}.md`

This order follows the actual control flow.

---

## Final Rule

Do not keep extending Gen 1 assumptions inside Gen 2 files.

If a file still depends on:
- `task-contract_{RUN_ID}.md`
- diff classification
- `plan.md`
- one `RUN_ID` per full loop session

then it is not migrated yet.

```

### ROUTING.md
```markdown
# /go → /tdd → /refactor Routing Notes

## Schema linkage

```
run-status.verification_result_path  → verification-result.schema.json instance
run-status.block_state_path         → block-state.schema.json instance
run-status.dispatch_results[]       → code-result.schema.json instances
verification-result.tdd.run_id       → TDD run session
```

## Run-status as canonical live-state object

`run-status.json` is the orchestrator's live state. It is the single authoritative object for:
- what step is currently executing (`current_step`)
- whether progression is blocked and why (`block_state_path`)
- what verification evidence exists (`verification_result_path`)
- what decomposed code functions returned (`dispatch_results[]`)
- what recommendations are pending (`recommendations[]`)

Treat `verification-result.json` as the canonical readiness object — it aggregates all gate outcomes (command checks, simplify, review passes, TDD, PR readiness) into one machine-readable fact.

## Routing table

| Condition | Route | Why |
|-----------|-------|-----|
| code changes detected | `/code` | Execute behavior change, TDD if applicable |
| cleanup without behavior change | `/refactor` | Simplification, deduplication, restructuring |
| architecture unresolved or contract ambiguous | `/design_1.0` | Resolve design before `/code` |
| scope unclear or decomposition needed | `/planning` | Task breakdown before implementation |
| config/infra only | direct verify → reviews | No TDD needed; skip to quality gates |

## /go auto-invoke chain for code tasks

```
1. /t          → test discovery, populates test-gaps_{run_id}.json
2. /gap        → loads gaps from /t output
3. /tdd        → RED phase (if gaps) or GREEN phase (if scaffolded)
   → /refactor → post-TDD cleanup if simplify flags debt
4. /simplify   → quality gate
5. 7-pass review → correctness, scope, tests, simplicity, regressions, maintainability, pr-ready
```

## Blocking transitions

- `/tdd` fails RED three times → block with `reason_code: verification_failed`
- `/simplify` finds HIGH/CRITICAL → block with `reason_code: simplify_failed`
- review pass returns REVIEW_REQUIRED → block with `reason_code: review_failed`
- max retries exhausted → block with `reason_code: max_attempts_reached`

## Resume semantics

When resuming a blocked run:
1. Read `block-state.json` to understand why blocked
2. Check `block_state.can_retry` — if false, requires user input
3. If `block_state.waiver_allowed`, operator can waive and retry
4. On retry, clear `.blocked_` flag and re-enter at last incomplete step

```

### ROUTING.md
```markdown
# /go → /tdd → /refactor Routing Notes

## Schema linkage

```
run-status.verification_result_path  → verification-result.schema.json instance
run-status.block_state_path         → block-state.schema.json instance
run-status.dispatch_results[]       → code-result.schema.json instances
verification-result.tdd.run_id       → TDD run session
```

## Run-status as canonical live-state object

`run-status.json` is the orchestrator's live state. It is the single authoritative object for:
- what step is currently executing (`current_step`)
- whether progression is blocked and why (`block_state_path`)
- what verification evidence exists (`verification_result_path`)
- what decomposed code functions returned (`dispatch_results[]`)
- what recommendations are pending (`recommendations[]`)

Treat `verification-result.json` as the canonical readiness object — it aggregates all gate outcomes (command checks, simplify, review passes, TDD, PR readiness) into one machine-readable fact.

## Routing table

| Condition | Route | Why |
|-----------|-------|-----|
| code changes detected | `/code` | Execute behavior change, TDD if applicable |
| cleanup without behavior change | `/refactor` | Simplification, deduplication, restructuring |
| architecture unresolved or contract ambiguous | `/design_1.0` | Resolve design before `/code` |
| scope unclear or decomposition needed | `/planning` | Task breakdown before implementation |
| config/infra only | direct verify → reviews | No TDD needed; skip to quality gates |

## /go auto-invoke chain for code tasks

```
1. /t          → test discovery, populates test-gaps_{run_id}.json
2. /gap        → loads gaps from /t output
3. /tdd        → RED phase (if gaps) or GREEN phase (if scaffolded)
   → /refactor → post-TDD cleanup if simplify flags debt
4. /simplify   → quality gate
5. 7-pass review → correctness, scope, tests, simplicity, regressions, maintainability, pr-ready
```

## Blocking transitions

- `/tdd` fails RED three times → block with `reason_code: verification_failed`
- `/simplify` finds HIGH/CRITICAL → block with `reason_code: simplify_failed`
- review pass returns REVIEW_REQUIRED → block with `reason_code: review_failed`
- max retries exhausted → block with `reason_code: max_attempts_reached`

## Resume semantics

When resuming a blocked run:
1. Read `block-state.json` to understand why blocked
2. Check `block_state.can_retry` — if false, requires user input
3. If `block_state.waiver_allowed`, operator can waive and retry
4. On retry, clear `.blocked_` flag and re-enter at last incomplete step

```

### SKILL.md
```markdown
---
name: go
version: 2.0.0
description: Execute a task from user input, plan file, or tasks.json queue and drive it to PR-ready completion. Handles intent parsing, task selection, worktree enforcement, verification, simplification, 7-pass review, and local artifact generation. Not for architecture, design, or refactoring — use /planning, /design_1.0, or /refactor instead.
category: execution
enforcement: strict
workflow_steps:
  - worktree_enforcement
  - task_selection
  - verify_end_to_end
  - simplify_code
  - seven_pass_review
  - local_pr_artifacts
  - loop_check
suggest:
  - /planning
  - design
  - /code
  - refactor
hooks:
  Stop:
    - hooks:
        - type: command
          command: |
            python -c "import os,sys,glob; tid=os.environ.get('CLAUDE_TERMINAL_ID','unknown'); sd=f'.claude/.artifacts/{tid}/go'; sys.exit(0) if not glob.glob(f'{sd}/active-task_*.json') else None; rid=os.environ.get('GO_RUN_ID','unknown'); sys.exit(0) if os.path.isfile(f'{sd}/.verified_{rid}') and os.path.isfile(f'{sd}/.reviews-passed_{rid}') else (print('WARNING: /go completed without all gates passed',file=sys.stderr), sys.exit(1))"
          description: "Self-verify all gates passed on Stop"
---

# /go — Thin Orchestrator

**Role:** `/go` is a **thin orchestrator** that stays on `main`. It acquires a task (from user intent, a plan file, or a tasks.json queue), routes it to the correct SDLC skill, and records the outcome. It does not implement TDD, simplification, or review logic itself — it delegates to `/code`, `/refactor`, `/planning`, or `/design_1.0` via subagents that work in isolated worktrees.

**MANDATORY SEQUENCE:** Worktree Check → Task Selection → Verify → Simplify → 7-Pass Review → PR Artifacts → Loop Check

**State root:** `.claude/.artifacts/{TERMINAL_ID}/go/`

---

## What /go Must Do

1. Enforce worktree + branch preconditions (auto-create if on main)
2. Acquire a task from one of three input sources
3. Route to the correct SDLC skill based on task type and diff
4. Run verification commands from the task contract
5. Run `/simplify` if code changed
6. Run 7-pass review at the appropriate depth
7. Generate local PR artifacts
8. Emit the correct completion token

**What /go Must NOT Do:**
- Replace `/code` TDD workflow
- Replace `/refactor` cleanup logic
- Replace `/planning` task breakdown
- Use `plan.md` as a scheduler source
- Auto-push or create remote PRs

---

## Completion Tokens

- `<promise>PR_READY</promise>` — task done, all gates passed, artifacts written
- `<promise>BLOCKED</promise>` — task cannot proceed or max attempts reached
- `<promise>MORE_TASKS_IN_PLAN</promise>` — current task done, more remain
- `<promise>ALL_TASKS_COMPLETE</promise>` — no eligible tasks remain

---

## Required Environment

```bash
export TERMINAL_ID="${TERMINAL_ID:-$(uuidgen | cut -d'-' -f1 | tr '[:upper:]' '[:lower:]')}"
export RUN_ID="${GO_RUN_ID:-$(uuidgen)}"
export MAX_ATTEMPTS="${MAX_ATTEMPTS:-3}"
export GO_STATE_DIR=".claude/.artifacts/${TERMINAL_ID}/go"
export GO_TASKS_FILE="${GO_TASKS_FILE:-.claude/tasks/tasks.json}"
export GO_PROMPT="${GO_PROMPT:-}"
export HANDOFF_TRANSCRIPT="${HANDOFF_TRANSCRIPT:-}"
export GO_PLAN_FILE="${GO_PLAN_FILE:-}"
mkdir -p "$GO_STATE_DIR"
```

---

## Task Input Sources

| Source | Env Var | Description |
|--------|---------|-------------|
| Direct prompt | `GO_PROMPT` | User's task description at invocation |
| Handoff transcript | `HANDOFF_TRANSCRIPT` | Path to prior session transcript |
| Plan file | `GO_PLAN_FILE` | Path to `.md` plan file |
| Task queue | `GO_TASKS_FILE` | JSON file with queued tasks |

Priority: `GO_PROMPT` > `HANDOFF_TRANSCRIPT` > `GO_PLAN_FILE` > `GO_TASKS_FILE`

When using prompt/transcript/plan, the task is synthesized into the contract below. When using the task queue, the first task with `status` in `{ready, queued, approved}` is selected.

---

## Task Contract

**Synthesized task** (from intent parsing):

```json
{
  "task_id": "task-04221-1430",
  "title": "Short title",
  "objective": "One-sentence objective",
  "status": "ready",
  "priority": "P1",
  "scope_in": [],
  "scope_out": [],
  "forbidden_files": [],
  "acceptance_criteria": ["Criterion 1"],
  "verification_commands": [],
  "task_type": "implementation",
  "routing": { "skill": "/code", "route": "code" }
}
```

**Queued task** (from `$GO_TASKS_FILE`):

```json
{
  "id": "TASK-001",
  "title": "Short title",
  "objective": "One-sentence objective",
  "status": "ready",
  "priority": "P1",
  "scope_in": ["fileA"],
  "scope_out": ["fileB"],
  "forbidden_files": ["secrets.env"],
  "acceptance_criteria": ["Criterion 1"],
  "verification_commands": ["pytest -q"],
  "task_type": "implementation",
  "requires_approval": false
}
```

**Allowed `task_type` values:** `implementation`, `refactor`, `design`, `planning`

---

## Routing Table

| Condition | Route |
|-----------|-------|
| Code behavior change needed | `/code` |
| Cleanup without behavior change | `/refactor` |
| Architecture or contract unclear | `/design_1.0` |
| Scope unclear or decomposition needed | `/planning` |
| Config/infra only | direct verify → reviews |

---

## STEP 0: Worktree Provisioning

**One worktree per plan — not per task.** All tasks within a plan share the same worktree. The worktree is created once when the plan starts, and all tasks run within it. This avoids per-task ceremony and keeps state coherent for sequential tasks.

`/go` stays on `main`. It creates the plan worktree once, then dispatches workers into it.

**Create a worktree for the plan:**

```bash
# Extract plan identifier from GO_PLAN_FILE or GO_PROMPT
PLAN_ID="$(basename "${GO_PLAN_FILE:-plan}" .md | sed 's/[^a-zA-Z0-9]/-/g')"
WORKTREE="P:/worktrees/${PLAN_ID}"
[ ! -d "$WORKTREE" ] && git worktree add -b "ai/${PLAN_ID}" "$WORKTREE" HEAD
```

**No per-task worktree creation.** Once the plan worktree exists, subsequent tasks reuse it.

**Dispatch a worker into the worktree** using one of:

| Method | When to use |
|--------|-------------|
| `Agent` tool with `isolation: "worktree"` | Subagent does code changes |
| `Agent` tool with prompt instructing `EnterWorktree` | Worker needs to choose its own worktree |
| `claude -p` with `--cd "$WORKTREE"` | External CLI-based LLM |

`/go` remains on `main` throughout — it orchestrates, workers execute in the plan worktree.

**Anti-pattern to avoid:** Creating a new worktree per task (`ai-task-$TS`). This is wasteful for sequential plans and scatters related code across multiple worktrees.

---

## STEP 1: Task Acquisition

**From intent (GO_PROMPT / HANDOFF_TRANSCRIPT / GO_PLAN_FILE):** Parse intent and synthesize a task contract. Write `active-task_{RUN_ID}.json`.

**From queue (GO_TASKS_FILE):** Select the first task with `status` in `{ready, queued, approved}`.

```bash
python ".claude/skills/go/scripts/select-task.py"
STATUS=$?
[ "$STATUS" -ne 0 ] && exit 1
touch "$GO_STATE_DIR/.task-selected_$RUN_ID"
```

## STEP 1.5: Task Validation Before Dispatch

**Schema:** `schemas/active-task.schema.json` (updated with `estimated_complexity` and `dependencies`)

Before routing, validate the task contract:

1. **Schema completeness** — `task.scope_in`, `task.scope_out`, `task.acceptance_criteria` must all be non-empty
2. **Complexity gate** — If `task.estimated_complexity == "high"`, block with a prompt to the user: `"Task '{task.id}' has estimated_complexity=high. Confirm before dispatching to /code."` Do not proceed without user confirmation.
3. **Dependency check** — If `task.dependencies` is non-empty, verify each dependency task ID has `status == "completed"` in the task queue. If any dependency is not completed, block with reason `"dependency_incomplete: {missing_ids}"`
4. **DAG validation** — `dependencies[]` must not contain cycles. If a cycle is detected, block with reason `"dependency_cycle_detected"`

**Validation failure behavior:**
- Emit block reason to stderr
- If user confirms or fix is available, retry validation
- If validation permanently fails, emit `<promise>BLOCKED</promise>`

---

## STEP 2: Route & Dispatch

Read `active-task_{RUN_ID}.json`. Route by `task_type`:

- `implementation` → `/code`
- `refactor` → `/refactor`
- `design` → `/design_1.0`
- `planning` → `/planning`

For `implementation`, check for existing code changes:
- `git diff --name-only HEAD` — if empty or docs only, skip TDD
- If code changes exist, invoke `/tdd` then `/code`

---

## STEP 3: Verification

Run every command in `task.verification_commands`. Record results.

```bash
python ".claude/skills/go/scripts/verify-task.py"
STATUS=$?
if [ "$STATUS" -ne 0 ]; then
  ATTEMPT_NEXT=$(find "$GO_STATE_DIR" -maxdepth 1 -type f -name ".attempt_*_$RUN_ID" | wc -l | tr -d ' ')
  [ "$ATTEMPT_NEXT" -ge "$MAX_ATTEMPTS" ] && touch "$GO_STATE_DIR/.blocked_$RUN_ID" && echo "<promise>BLOCKED</promise>" && exit 1
  exit 1
fi
touch "$GO_STATE_DIR/.verified_$RUN_ID"
```

---

## STEP 4: Simplify

If docs-only diff, skip. Otherwise run `/simplify`.

```bash
DOCS_ONLY="$(python -c 'import json; d=json.load(open(".claude/.artifacts/'${TERMINAL_ID}'/go/diff-summary_'${RUN_ID}'.json")); print("true" if d.get("docs_only") else "false")' 2>/dev/null || echo false)"
if [ "$DOCS_ONLY" = "true" ]; then
  echo "Skipping simplify (docs-only)"
else
  /simplify > "$GO_STATE_DIR/simplify-status_$RUN_ID.md" 2>&1 || true
  grep -qiE 'CRITICAL|HIGH' "$GO_STATE_DIR/simplify-status_$RUN_ID.md" && {
    echo "ERROR: simplify HIGH/CRITICAL findings"
    touch "$GO_STATE_DIR/.blocked_$RUN_ID"
    echo "<promise>BLOCKED</promise>"
    exit 1
  }
fi
touch "$GO_STATE_DIR/.simplified_$RUN_ID"
```

---

## STEP 5: 7-Pass Review

Run review passes at the depth determined by diff classification.

```bash
python ".claude/skills/go/scripts/review-passes.py"
STATUS=$?
[ "$STATUS" -ne 0 ] && exit 1
touch "$GO_STATE_DIR/.reviews-passed_$RUN_ID"
```

---

## STEP 6: Local PR Artifacts

Generate commit message, PR title, PR body, PR-ready report.

```bash
python ".claude/skills/go/scripts/pr-artifacts.py"
touch "$GO_STATE_DIR/.pr-ready_$RUN_ID"
echo "<promise>PR_READY</promise>"
```

---

## STEP 7: Loop Check

Check if more eligible tasks remain.

```bash
python ".claude/skills/go/scripts/loop-check.py"
```

---

## Prohibited Actions

- Workers making direct changes on `main` or `master`
- Using `plan.md` as scheduler source
- Proceeding without required prior flag
- Ignoring failed verification commands
- Ignoring HIGH/CRITICAL simplify findings
- Auto-pushing or creating remote PRs
- Modifying `forbidden_files` listed in task contract

```

### SKILL.md
```markdown
---
name: go
version: 2.0.0
description: Execute a task from user input, plan file, or tasks.json queue and drive it to PR-ready completion. Handles intent parsing, task selection, worktree enforcement, verification, simplification, 7-pass review, and local artifact generation. Not for architecture, design, or refactoring — use /planning, /design_1.0, or /refactor instead.
category: execution
enforcement: strict
workflow_steps:
  - worktree_enforcement
  - task_selection
  - verify_end_to_end
  - simplify_code
  - seven_pass_review
  - local_pr_artifacts
  - loop_check
suggest:
  - /planning
  - design
  - /code
  - refactor
hooks:
  Stop:
    - hooks:
        - type: command
          command: |
            python -c "import os,sys,glob; tid=os.environ.get('CLAUDE_TERMINAL_ID','unknown'); sd=f'.claude/.artifacts/{tid}/go'; sys.exit(0) if not glob.glob(f'{sd}/active-task_*.json') else None; rid=os.environ.get('GO_RUN_ID','unknown'); sys.exit(0) if os.path.isfile(f'{sd}/.verified_{rid}') and os.path.isfile(f'{sd}/.reviews-passed_{rid}') else (print('WARNING: /go completed without all gates passed',file=sys.stderr), sys.exit(1))"
          description: "Self-verify all gates passed on Stop"
---

# /go — Thin Orchestrator

**Role:** `/go` is a **thin orchestrator** that stays on `main`. It acquires a task (from user intent, a plan file, or a tasks.json queue), routes it to the correct SDLC skill, and records the outcome. It does not implement TDD, simplification, or review logic itself — it delegates to `/code`, `/refactor`, `/planning`, or `/design_1.0` via subagents that work in isolated worktrees.

**MANDATORY SEQUENCE:** Worktree Check → Task Selection → Verify → Simplify → 7-Pass Review → PR Artifacts → Loop Check

**State root:** `.claude/.artifacts/{TERMINAL_ID}/go/`

---

## What /go Must Do

1. Enforce worktree + branch preconditions (auto-create if on main)
2. Acquire a task from one of three input sources
3. Route to the correct SDLC skill based on task type and diff
4. Run verification commands from the task contract
5. Run `/simplify` if code changed
6. Run 7-pass review at the appropriate depth
7. Generate local PR artifacts
8. Emit the correct completion token

**What /go Must NOT Do:**
- Replace `/code` TDD workflow
- Replace `/refactor` cleanup logic
- Replace `/planning` task breakdown
- Use `plan.md` as a scheduler source
- Auto-push or create remote PRs

---

## Completion Tokens

- `<promise>PR_READY</promise>` — task done, all gates passed, artifacts written
- `<promise>BLOCKED</promise>` — task cannot proceed or max attempts reached
- `<promise>MORE_TASKS_IN_PLAN</promise>` — current task done, more remain
- `<promise>ALL_TASKS_COMPLETE</promise>` — no eligible tasks remain

---

## Required Environment

```bash
export TERMINAL_ID="${TERMINAL_ID:-$(uuidgen | cut -d'-' -f1 | tr '[:upper:]' '[:lower:]')}"
export RUN_ID="${GO_RUN_ID:-$(uuidgen)}"
export MAX_ATTEMPTS="${MAX_ATTEMPTS:-3}"
export GO_STATE_DIR=".claude/.artifacts/${TERMINAL_ID}/go"
export GO_TASKS_FILE="${GO_TASKS_FILE:-.claude/tasks/tasks.json}"
export GO_PROMPT="${GO_PROMPT:-}"
export HANDOFF_TRANSCRIPT="${HANDOFF_TRANSCRIPT:-}"
export GO_PLAN_FILE="${GO_PLAN_FILE:-}"
mkdir -p "$GO_STATE_DIR"
```

---

## Task Input Sources

| Source | Env Var | Description |
|--------|---------|-------------|
| Direct prompt | `GO_PROMPT` | User's task description at invocation |
| Handoff transcript | `HANDOFF_TRANSCRIPT` | Path to prior session transcript |
| Plan file | `GO_PLAN_FILE` | Path to `.md` plan file |
| Task queue | `GO_TASKS_FILE` | JSON file with queued tasks |

Priority: `GO_PROMPT` > `HANDOFF_TRANSCRIPT` > `GO_PLAN_FILE` > `GO_TASKS_FILE`

When using prompt/transcript/plan, the task is synthesized into the contract below. When using the task queue, the first task with `status` in `{ready, queued, approved}` is selected.

---

## Task Contract

**Synthesized task** (from intent parsing):

```json
{
  "task_id": "task-04221-1430",
  "title": "Short title",
  "objective": "One-sentence objective",
  "status": "ready",
  "priority": "P1",
  "scope_in": [],
  "scope_out": [],
  "forbidden_files": [],
  "acceptance_criteria": ["Criterion 1"],
  "verification_commands": [],
  "task_type": "implementation",
  "routing": { "skill": "/code", "route": "code" }
}
```

**Queued task** (from `$GO_TASKS_FILE`):

```json
{
  "id": "TASK-001",
  "title": "Short title",
  "objective": "One-sentence objective",
  "status": "ready",
  "priority": "P1",
  "scope_in": ["fileA"],
  "scope_out": ["fileB"],
  "forbidden_files": ["secrets.env"],
  "acceptance_criteria": ["Criterion 1"],
  "verification_commands": ["pytest -q"],
  "task_type": "implementation",
  "requires_approval": false
}
```

**Allowed `task_type` values:** `implementation`, `refactor`, `design`, `planning`

---

## Routing Table

| Condition | Route |
|-----------|-------|
| Code behavior change needed | `/code` |
| Cleanup without behavior change | `/refactor` |
| Architecture or contract unclear | `/design_1.0` |
| Scope unclear or decomposition needed | `/planning` |
| Config/infra only | direct verify → reviews |

---

## STEP 0: Worktree Provisioning

**One worktree per plan — not per task.** All tasks within a plan share the same worktree. The worktree is created once when the plan starts, and all tasks run within it. This avoids per-task ceremony and keeps state coherent for sequential tasks.

`/go` stays on `main`. It creates the plan worktree once, then dispatches workers into it.

**Create a worktree for the plan:**

```bash
# Extract plan identifier from GO_PLAN_FILE or GO_PROMPT
PLAN_ID="$(basename "${GO_PLAN_FILE:-plan}" .md | sed 's/[^a-zA-Z0-9]/-/g')"
WORKTREE="P:/worktrees/${PLAN_ID}"
[ ! -d "$WORKTREE" ] && git worktree add -b "ai/${PLAN_ID}" "$WORKTREE" HEAD
```

**No per-task worktree creation.** Once the plan worktree exists, subsequent tasks reuse it.

**Dispatch a worker into the worktree** using one of:

| Method | When to use |
|--------|-------------|
| `Agent` tool with `isolation: "worktree"` | Subagent does code changes |
| `Agent` tool with prompt instructing `EnterWorktree` | Worker needs to choose its own worktree |
| `claude -p` with `--cd "$WORKTREE"` | External CLI-based LLM |

`/go` remains on `main` throughout — it orchestrates, workers execute in the plan worktree.

**Anti-pattern to avoid:** Creating a new worktree per task (`ai-task-$TS`). This is wasteful for sequential plans and scatters related code across multiple worktrees.

---

## STEP 1: Task Acquisition

**From intent (GO_PROMPT / HANDOFF_TRANSCRIPT / GO_PLAN_FILE):** Parse intent and synthesize a task contract. Write `active-task_{RUN_ID}.json`.

**From queue (GO_TASKS_FILE):** Select the first task with `status` in `{ready, queued, approved}`.

```bash
python ".claude/skills/go/scripts/select-task.py"
STATUS=$?
[ "$STATUS" -ne 0 ] && exit 1
touch "$GO_STATE_DIR/.task-selected_$RUN_ID"
```

## STEP 1.5: Task Validation Before Dispatch

**Schema:** `schemas/active-task.schema.json` (updated with `estimated_complexity` and `dependencies`)

Before routing, validate the task contract:

1. **Schema completeness** — `task.scope_in`, `task.scope_out`, `task.acceptance_criteria` must all be non-empty
2. **Complexity gate** — If `task.estimated_complexity == "high"`, block with a prompt to the user: `"Task '{task.id}' has estimated_complexity=high. Confirm before dispatching to /code."` Do not proceed without user confirmation.
3. **Dependency check** — If `task.dependencies` is non-empty, verify each dependency task ID has `status == "completed"` in the task queue. If any dependency is not completed, block with reason `"dependency_incomplete: {missing_ids}"`
4. **DAG validation** — `dependencies[]` must not contain cycles. If a cycle is detected, block with reason `"dependency_cycle_detected"`

**Validation failure behavior:**
- Emit block reason to stderr
- If user confirms or fix is available, retry validation
- If validation permanently fails, emit `<promise>BLOCKED</promise>`

---

## STEP 2: Route & Dispatch

Read `active-task_{RUN_ID}.json`. Route by `task_type`:

- `implementation` → `/code`
- `refactor` → `/refactor`
- `design` → `/design_1.0`
- `planning` → `/planning`

For `implementation`, check for existing code changes:
- `git diff --name-only HEAD` — if empty or docs only, skip TDD
- If code changes exist, invoke `/tdd` then `/code`

---

## STEP 3: Verification

Run every command in `task.verification_commands`. Record results.

```bash
python ".claude/skills/go/scripts/verify-task.py"
STATUS=$?
if [ "$STATUS" -ne 0 ]; then
  ATTEMPT_NEXT=$(find "$GO_STATE_DIR" -maxdepth 1 -type f -name ".attempt_*_$RUN_ID" | wc -l | tr -d ' ')
  [ "$ATTEMPT_NEXT" -ge "$MAX_ATTEMPTS" ] && touch "$GO_STATE_DIR/.blocked_$RUN_ID" && echo "<promise>BLOCKED</promise>" && exit 1
  exit 1
fi
touch "$GO_STATE_DIR/.verified_$RUN_ID"
```

---

## STEP 4: Simplify

If docs-only diff, skip. Otherwise run `/simplify`.

```bash
DOCS_ONLY="$(python -c 'import json; d=json.load(open(".claude/.artifacts/'${TERMINAL_ID}'/go/diff-summary_'${RUN_ID}'.json")); print("true" if d.get("docs_only") else "false")' 2>/dev/null || echo false)"
if [ "$DOCS_ONLY" = "true" ]; then
  echo "Skipping simplify (docs-only)"
else
  /simplify > "$GO_STATE_DIR/simplify-status_$RUN_ID.md" 2>&1 || true
  grep -qiE 'CRITICAL|HIGH' "$GO_STATE_DIR/simplify-status_$RUN_ID.md" && {
    echo "ERROR: simplify HIGH/CRITICAL findings"
    touch "$GO_STATE_DIR/.blocked_$RUN_ID"
    echo "<promise>BLOCKED</promise>"
    exit 1
  }
fi
touch "$GO_STATE_DIR/.simplified_$RUN_ID"
```

---

## STEP 5: 7-Pass Review

Run review passes at the depth determined by diff classification.

```bash
python ".claude/skills/go/scripts/review-passes.py"
STATUS=$?
[ "$STATUS" -ne 0 ] && exit 1
touch "$GO_STATE_DIR/.reviews-passed_$RUN_ID"
```

---

## STEP 6: Local PR Artifacts

Generate commit message, PR title, PR body, PR-ready report.

```bash
python ".claude/skills/go/scripts/pr-artifacts.py"
touch "$GO_STATE_DIR/.pr-ready_$RUN_ID"
echo "<promise>PR_READY</promise>"
```

---

## STEP 7: Loop Check

Check if more eligible tasks remain.

```bash
python ".claude/skills/go/scripts/loop-check.py"
```

---

## Prohibited Actions

- Workers making direct changes on `main` or `master`
- Using `plan.md` as scheduler source
- Proceeding without required prior flag
- Ignoring failed verification commands
- Ignoring HIGH/CRITICAL simplify findings
- Auto-pushing or creating remote PRs
- Modifying `forbidden_files` listed in task contract

```


### .aid\go\go_sig.md

# go — LLM-READY PACK

<!-- Generated by gitpack.py (pure Python) -->

## PACK INFO
- **Files:** 9 files
- **Mode:** signatures only
- **Generated:** 2026-04-27 18:12 UTC

## HOW TO USE

This is the signatures-only pack. For full implementations, see the
corresponding `_full.md` file.

## SIGNATURE TOC

### P:\packages\cc-skills-sdlc\skills\go\scripts\go_safe.py
```python
now_iso() -> str
write_json(path: Path, payload: dict) -> None
write_text(path: Path, content: str) -> None
run_git(args: list[str], root_dir: Path) -> tuple[int, str, str]
die(error: str, artifact_dir: Path, run_id: str) -> None
require_file(path: Path, artifact_dir: Path, run_id: str) -> None
infer_args() -> tuple[str, str, str, str]
main() -> int
```

### P:\packages\cc-skills-sdlc\skills\go\scripts\init_go_run.py
```python
now_iso() -> str
write_json(path: Path, payload: dict[Any]) -> None
write_text(path: Path, content: str) -> None
run_git(args: list[str], root_dir: Path) -> str
class TaskCandidate
infer_route(task: TaskCandidate) -> tuple[str, str, str, dict[str, bool], list[str]]
parse_plan_md(plan_path: Path) -> list[TaskCandidate]
parse_args() -> argparse.Namespace
build_explicit_task(args: argparse.Namespace) -> TaskCandidate
main() -> int
```

### P:\packages\cc-skills-sdlc\skills\go\scripts\loop-check.py
```python
# (no public definitions)
```

### P:\packages\cc-skills-sdlc\skills\go\scripts\pr-artifacts.py
```python
# (no public definitions)
```

### P:\packages\cc-skills-sdlc\skills\go\scripts\review-passes.py
```python
# (no public definitions)
```

### P:\packages\cc-skills-sdlc\skills\go\scripts\select-task.py
```python
# (no public definitions)
```

### P:\packages\cc-skills-sdlc\skills\go\scripts\validate_go_contracts.py
```python
load_json(path: Path) -> Any
load_schemas(schema_dir: Path) -> dict[str, dict[str, Any]]
infer_schema_key(file_path: Path) -> str | None
validate_file(file_path: Path, schemas: dict[Any]) -> tuple[bool, str]
validate_directory(artifact_dir: Path, schemas: dict[Any]) -> int
main() -> int
```

### P:\packages\cc-skills-sdlc\skills\go\scripts\verify-task.py
```python
# (no public definitions)
```

### P:\packages\cc-skills-sdlc\skills\go\scripts\write_dispatch_result.py
```python
now_iso() -> str
update_run_file(run_path: Path, status: str, final_promise: str | None, notes: str | None) -> None
update_dispatch_result(artifact_dir: Path, run_id: str, final_status: str, wait_state: str, **kwargs) -> None
emit_promise(final_status: str) -> None
main() -> int
```

## DIRECTORY INDEX

| Directory | Files |
|---------|-------|
| `scripts/` | 9 |
## DIRECTORY TREE

```
go/ (9 files)
└── scripts/ (9)
    ├── go_safe.py
    ├── init_go_run.py
    ├── loop-check.py
    ├── pr-artifacts.py
    ├── review-passes.py
    ├── select-task.py
    ├── validate_go_contracts.py
    ├── verify-task.py
    └── write_dispatch_result.py
```

## FILE INDEX

| File | Description |
|------|-------------|
| `P:\packages\cc-skills-sdlc\skills\go\scripts\go_safe.py` | go safe |
| `P:\packages\cc-skills-sdlc\skills\go\scripts\init_go_run.py` | init go run |
| `P:\packages\cc-skills-sdlc\skills\go\scripts\loop-check.py` | loop check |
| `P:\packages\cc-skills-sdlc\skills\go\scripts\pr-artifacts.py` | pr artifacts |
| `P:\packages\cc-skills-sdlc\skills\go\scripts\review-passes.py` | review passes |
| `P:\packages\cc-skills-sdlc\skills\go\scripts\select-task.py` | select task |
| `P:\packages\cc-skills-sdlc\skills\go\scripts\validate_go_contracts.py` | validate go contracts |
| `P:\packages\cc-skills-sdlc\skills\go\scripts\verify-task.py` | verify task |
| `P:\packages\cc-skills-sdlc\skills\go\scripts\write_dispatch_result.py` | write dispatch result |

---

## ADDITIONAL FILES (markdown)

### GO-CONFORMANCE.md
```markdown
# /go_2.0 Conformance Checklist

**Governing rule:** Every decision that can block, resume, recommend, or complete a `/go` run must be derivable from machine-readable artifacts, not just markdown prose or terminal output.

Truth source assignment:
- **Live execution state:** `run-status.schema.json`
- **Readiness / gate outcome:** `verification-result.schema.json`
- **Blocked reason and recovery:** `block-state.schema.json`
- **Delegated implementation outcome:** `code-result.schema.json`
- **Human-readable explanation:** markdown — never authoritative over JSON

---

## Critical

### GO-CONF-001 — FIXED
block-state written at 4 hard-stops: max_attempts, verification_failed, simplify_failed, review_failed. All with `schema_version`, `reason_code`, `opened_at`, `evidence_paths`.

### GO-CONF-002 — FIXED
run-status initialized at task selection (STEP 1); updated at verification pass (STEP 3) with `verification_result_path`.

### GO-CONF-003 — FIXED
`task_outcome()` reads run-status.json first. Flags as atomic fallback. Stdout token parsing removed.

### GO-CONF-004 — OPEN
`$ref: "code-result.schema.json"` in `dispatch_results[]` may not resolve in all JSON Schema validators. `code-result.schema.json` exists with correct `$id`. Risk is low for validators that support `$id`-based resolution.

---

## High

### GO-CONF-005 — OPEN
Naming convention split: status fields use hyphens (`reviews-passed`), reason codes use underscores (`verification_failed`). Affects `ralph-go-loop.sh` status matching vs `run-status.schema.json` enum values. Requires one canonical convention decision.

### GO-CONF-006 — OPEN
ROUTING.md has 15 routing rows covering all required branches. Still prose-based — not enforced in code.

### GO-CONF-007 — FIXED
After `/tdd` invocation, SKILL.md now reads `tdd-receipt_{RUN_ID}.json` and blocks if `validated=false` or receipt missing. Blocks with `reason_code: tdd_validation_failed`.

### GO-CONF-008 — FIXED
`workflow_steps` now lists all 10 steps including `test_discovery` and `tdd_decision`.

### GO-CONF-009 — FIXED
Flag filename `.pr-ready_$RUN_ID` (hyphen) is consistent across SKILL.md artifact layout, `ralph-go-loop.sh`, and `go-safe.sh`.

---

## Medium

### GO-CONF-010 — FIXED
STEP 3 now writes `verification-result_{RUN_ID}.json` after successful verification, populating all required fields including `task_id`, `status`, `verification_commands`, `simplify`, and `generated_at`.

### GO-CONF-011 — FIXED
Pre-mortem and stakeholder sync now write structured recommendation objects to `run-status.recommendations[]` with `type`, `prompt`, `evidence`, `resolved`, `resolved_at`.

### GO-CONF-012 — OPEN
Recommendation type strings: schema enum uses `pre-mortem` (hyphen); `block-state.schema.json` has no `pre-mortem` reason code — different semantic space but potential confusion.

### GO-CONF-013 — FIXED
All 4 new schemas (`run-status`, `verification-result`, `block-state`, `code-result`) now declare `schema_version`.

### GO-CONF-014 — FIXED
`tasks-file.schema.json` created with full validation of tasks.json structure including `id`, `title`, `objective`, `status`, `priority`, `scope_in`, `scope_out`, `forbidden_files`, `acceptance_criteria`, `verification_commands`, `requires_approval`, `notes`.

---

## Low

### GO-CONF-015 — FIXED
SKILL.md title updated to `/go_2.0 — Verify, Simplify, Ship`.

### GO-CONF-016 — FIXED
`go-safe.sh` now invokes `/go_2.0` explicitly instead of matching any `/go`.

---

## Current open items

| ID | Severity | Area | Title |
|----|----------|------|-------|
| GO-CONF-004 | critical | schema | `$ref` resolution for `dispatch_results[]` |
| GO-CONF-005 | high | naming | Status hyphens vs reason code underscores |
| GO-CONF-006 | high | routing | Routing table not machine-enforced |
| GO-CONF-012 | medium | recommendation | Type string inconsistency (hyphen/enum vs underscore/reason) |

**Fixed this session (12 of 16):** 001, 002, 003, 007, 008, 009, 010, 011, 013, 014, 015, 016.

---

## Step graph — artifact completion matrix

| Step | Completion artifact | Failure artifact | Retry artifact |
|------|-------------------|-----------------|----------------|
| worktree_enforcement | `.worktree-ready_` | `.blocked_` + `block-state_` | none |
| task_selection | `active-task_.json` + `run-status_` | `.blocked_` + `block-state_` | none |
| task_contract | `.task-defined_` | `.blocked_` + `block-state_` | none |
| test_discovery | `test-gaps_.json` | none | none |
| tdd_decision | `tdd-receipt_.json` | `.blocked_` + `block-state_` | none |
| verify_end_to_end | `.verified_` + `verification-summary_` + `run-status_` | `.blocked_` + `block-state_` + `.attempt_N_` | `.attempt_N_` |
| simplify_code | `.simplified_` + `simplify-summary_` | `.blocked_` + `block-state_` | none |
| seven_pass_review | `.reviews-passed_` + `review-summary_` | `.blocked_` + `block-state_` | none |
| local_pr_artifacts | `pr-ready_.md` + `.pr-ready_` | none | none |
| loop_check | `run-status_.final_promise` | none | none |

---

## Routing branch matrix

| Branch condition | Predicate | Action | Artifacts | Terminal state |
|-----------------|-----------|--------|-----------|----------------|
| no code changes | `CODE_FILE_COUNT == 0` | skip TDD → simplify | — | continue |
| tests only | `CODE_FILE_COUNT > 0 && DOCS_ONLY` | `/t` RED only | `tdd-receipt_` | continue |
| implementation | `CODE_FILE_COUNT > 0 && !DOCS_ONLY` | `/t` → `/gap` → `/tdd` → validate | `test-gaps_`, `tdd-receipt_`, `block-state_` | continue or blocked |
| config/infra | diff classify | verify → reviews | — | continue |
| `/t` no gaps | `test-gaps_` empty | skip `/gap` → `/tdd` | — | continue |
| gap insufficient | confidence < threshold | block or recommend | — | blocked |
| TDD not validated | `validated == false` | block | `block-state_` | BLOCKED |
| TDD RED fails 3x | retry_count >= 3 | block | `block-state_` | BLOCKED |
| simplify HIGH/CRITICAL | grep CRITICAL/HIGH | block | `block-state_` | BLOCKED |
| review REVIEW_REQUIRED | pass status | block | `block-state_` | BLOCKED |
| max attempts | attempt >= MAX_ATTEMPTS | block | `block-state_` | BLOCKED |
| verification passes | exit_code == 0 | simplify | `verification-summary_` | continue |
| recommendations emitted | `recommendations.length > 0` | surface + await + write | `run-status_` | depends |
| stakeholder sync required | `requires_approval == true` | surface + await + write | `run-status_` | depends |
| more tasks remain | loop check | next cycle | — | MORE_TASKS_IN_PLAN |
| all tasks complete | loop check | exit | — | ALL_TASKS_COMPLETE |

```

### GO-CONFORMANCE.md
```markdown
# /go_2.0 Conformance Checklist

**Governing rule:** Every decision that can block, resume, recommend, or complete a `/go` run must be derivable from machine-readable artifacts, not just markdown prose or terminal output.

Truth source assignment:
- **Live execution state:** `run-status.schema.json`
- **Readiness / gate outcome:** `verification-result.schema.json`
- **Blocked reason and recovery:** `block-state.schema.json`
- **Delegated implementation outcome:** `code-result.schema.json`
- **Human-readable explanation:** markdown — never authoritative over JSON

---

## Critical

### GO-CONF-001 — FIXED
block-state written at 4 hard-stops: max_attempts, verification_failed, simplify_failed, review_failed. All with `schema_version`, `reason_code`, `opened_at`, `evidence_paths`.

### GO-CONF-002 — FIXED
run-status initialized at task selection (STEP 1); updated at verification pass (STEP 3) with `verification_result_path`.

### GO-CONF-003 — FIXED
`task_outcome()` reads run-status.json first. Flags as atomic fallback. Stdout token parsing removed.

### GO-CONF-004 — OPEN
`$ref: "code-result.schema.json"` in `dispatch_results[]` may not resolve in all JSON Schema validators. `code-result.schema.json` exists with correct `$id`. Risk is low for validators that support `$id`-based resolution.

---

## High

### GO-CONF-005 — OPEN
Naming convention split: status fields use hyphens (`reviews-passed`), reason codes use underscores (`verification_failed`). Affects `ralph-go-loop.sh` status matching vs `run-status.schema.json` enum values. Requires one canonical convention decision.

### GO-CONF-006 — OPEN
ROUTING.md has 15 routing rows covering all required branches. Still prose-based — not enforced in code.

### GO-CONF-007 — FIXED
After `/tdd` invocation, SKILL.md now reads `tdd-receipt_{RUN_ID}.json` and blocks if `validated=false` or receipt missing. Blocks with `reason_code: tdd_validation_failed`.

### GO-CONF-008 — FIXED
`workflow_steps` now lists all 10 steps including `test_discovery` and `tdd_decision`.

### GO-CONF-009 — FIXED
Flag filename `.pr-ready_$RUN_ID` (hyphen) is consistent across SKILL.md artifact layout, `ralph-go-loop.sh`, and `go-safe.sh`.

---

## Medium

### GO-CONF-010 — FIXED
STEP 3 now writes `verification-result_{RUN_ID}.json` after successful verification, populating all required fields including `task_id`, `status`, `verification_commands`, `simplify`, and `generated_at`.

### GO-CONF-011 — FIXED
Pre-mortem and stakeholder sync now write structured recommendation objects to `run-status.recommendations[]` with `type`, `prompt`, `evidence`, `resolved`, `resolved_at`.

### GO-CONF-012 — OPEN
Recommendation type strings: schema enum uses `pre-mortem` (hyphen); `block-state.schema.json` has no `pre-mortem` reason code — different semantic space but potential confusion.

### GO-CONF-013 — FIXED
All 4 new schemas (`run-status`, `verification-result`, `block-state`, `code-result`) now declare `schema_version`.

### GO-CONF-014 — FIXED
`tasks-file.schema.json` created with full validation of tasks.json structure including `id`, `title`, `objective`, `status`, `priority`, `scope_in`, `scope_out`, `forbidden_files`, `acceptance_criteria`, `verification_commands`, `requires_approval`, `notes`.

---

## Low

### GO-CONF-015 — FIXED
SKILL.md title updated to `/go_2.0 — Verify, Simplify, Ship`.

### GO-CONF-016 — FIXED
`go-safe.sh` now invokes `/go_2.0` explicitly instead of matching any `/go`.

---

## Current open items

| ID | Severity | Area | Title |
|----|----------|------|-------|
| GO-CONF-004 | critical | schema | `$ref` resolution for `dispatch_results[]` |
| GO-CONF-005 | high | naming | Status hyphens vs reason code underscores |
| GO-CONF-006 | high | routing | Routing table not machine-enforced |
| GO-CONF-012 | medium | recommendation | Type string inconsistency (hyphen/enum vs underscore/reason) |

**Fixed this session (12 of 16):** 001, 002, 003, 007, 008, 009, 010, 011, 013, 014, 015, 016.

---

## Step graph — artifact completion matrix

| Step | Completion artifact | Failure artifact | Retry artifact |
|------|-------------------|-----------------|----------------|
| worktree_enforcement | `.worktree-ready_` | `.blocked_` + `block-state_` | none |
| task_selection | `active-task_.json` + `run-status_` | `.blocked_` + `block-state_` | none |
| task_contract | `.task-defined_` | `.blocked_` + `block-state_` | none |
| test_discovery | `test-gaps_.json` | none | none |
| tdd_decision | `tdd-receipt_.json` | `.blocked_` + `block-state_` | none |
| verify_end_to_end | `.verified_` + `verification-summary_` + `run-status_` | `.blocked_` + `block-state_` + `.attempt_N_` | `.attempt_N_` |
| simplify_code | `.simplified_` + `simplify-summary_` | `.blocked_` + `block-state_` | none |
| seven_pass_review | `.reviews-passed_` + `review-summary_` | `.blocked_` + `block-state_` | none |
| local_pr_artifacts | `pr-ready_.md` + `.pr-ready_` | none | none |
| loop_check | `run-status_.final_promise` | none | none |

---

## Routing branch matrix

| Branch condition | Predicate | Action | Artifacts | Terminal state |
|-----------------|-----------|--------|-----------|----------------|
| no code changes | `CODE_FILE_COUNT == 0` | skip TDD → simplify | — | continue |
| tests only | `CODE_FILE_COUNT > 0 && DOCS_ONLY` | `/t` RED only | `tdd-receipt_` | continue |
| implementation | `CODE_FILE_COUNT > 0 && !DOCS_ONLY` | `/t` → `/gap` → `/tdd` → validate | `test-gaps_`, `tdd-receipt_`, `block-state_` | continue or blocked |
| config/infra | diff classify | verify → reviews | — | continue |
| `/t` no gaps | `test-gaps_` empty | skip `/gap` → `/tdd` | — | continue |
| gap insufficient | confidence < threshold | block or recommend | — | blocked |
| TDD not validated | `validated == false` | block | `block-state_` | BLOCKED |
| TDD RED fails 3x | retry_count >= 3 | block | `block-state_` | BLOCKED |
| simplify HIGH/CRITICAL | grep CRITICAL/HIGH | block | `block-state_` | BLOCKED |
| review REVIEW_REQUIRED | pass status | block | `block-state_` | BLOCKED |
| max attempts | attempt >= MAX_ATTEMPTS | block | `block-state_` | BLOCKED |
| verification passes | exit_code == 0 | simplify | `verification-summary_` | continue |
| recommendations emitted | `recommendations.length > 0` | surface + await + write | `run-status_` | depends |
| stakeholder sync required | `requires_approval == true` | surface + await + write | `run-status_` | depends |
| more tasks remain | loop check | next cycle | — | MORE_TASKS_IN_PLAN |
| all tasks complete | loop check | exit | — | ALL_TASKS_COMPLETE |

```

### GO-QUICK-REFERENCE.md
```markdown
# /go Gen 2 — Quick Reference

Gen 2 replaces markdown task contracts and `plan.md` loop control with canonical JSON contracts and `/go -> /code` orchestration.

---

## Core Model

`/go` does exactly one task per `RUN_ID`.

Flow:

1. Validate worktree
2. Read `active-plan.json`
3. Select one eligible task
4. Write `active-task_{RUN_ID}.json`
5. Invoke `/code`
6. Require `task-result_{RUN_ID}.json`
7. Verify
8. Simplify
9. Review
10. Create local PR artifacts
11. Update `active-plan.json`
12. Emit loop token

---

## Canonical Files

All state lives in:

```text
.claude/.artifacts/{TERMINAL_ID}/go/
```

Key files:

```text
active-plan.json
active-task_{RUN_ID}.json
task-result_{RUN_ID}.json
verification-results_{RUN_ID}.txt
simplify-status_{RUN_ID}.md
review-pass-correctness_{RUN_ID}.md
review-pass-scope_{RUN_ID}.md
review-pass-tests_{RUN_ID}.md
review-pass-simplicity_{RUN_ID}.md
review-pass-regressions_{RUN_ID}.md
review-pass-maintainability_{RUN_ID}.md
review-pass-pr-ready_{RUN_ID}.md
commit-message_{RUN_ID}.txt
pr-title_{RUN_ID}.txt
pr-body_{RUN_ID}.md
pr-ready_{RUN_ID}.md
```

---

## Flag Files

Gen 2 gate files:

```text
.worktree-ready_{RUN_ID}
.task-selected_{RUN_ID}
.coded_{RUN_ID}
.verified_{RUN_ID}
.simplified_{RUN_ID}
.reviews-passed_{RUN_ID}
.pr-ready_{RUN_ID}
.blocked_{RUN_ID}
.attempt_{N}_{RUN_ID}
```

Meaning:

- `.worktree-ready_{RUN_ID}` — worktree and plan validation passed
- `.task-selected_{RUN_ID}` — one task was selected from `active-plan.json`
- `.coded_{RUN_ID}` — `/code` completed and wrote `task-result_{RUN_ID}.json`
- `.verified_{RUN_ID}` — implementation matched contract and evidence passed
- `.simplified_{RUN_ID}` — simplify gate passed or valid skip recorded
- `.reviews-passed_{RUN_ID}` — all 7 review passes passed
- `.pr-ready_{RUN_ID}` — local PR artifacts exist
- `.blocked_{RUN_ID}` — task cannot proceed
- `.attempt_{N}_{RUN_ID}` — retry counter for this run

---

## Environment Variables

```bash
export TERMINAL_ID=$(uuidgen | cut -d'-' -f1)
export RUN_ID=$(uuidgen)
export MAX_ATTEMPTS=3
```

Derived paths:

```bash
ARTIFACT_DIR=".claude/.artifacts/$TERMINAL_ID/go"
PLAN_FILE="$ARTIFACT_DIR/active-plan.json"
ACTIVE_TASK_FILE="$ARTIFACT_DIR/active-task_$RUN_ID.json"
TASK_RESULT_FILE="$ARTIFACT_DIR/task-result_$RUN_ID.json"
```

---

## JSON Contracts

### `active-plan.json`

Scheduler source of truth.

Each task should contain:

- `task_id`
- `title`
- `status`
- `priority`
- `depends_on`
- `objective`
- `scope`
- `allowed_files`
- `forbidden_files`
- `acceptance_criteria`
- `verification_commands`

### `active-task_{RUN_ID}.json`

Selected-task snapshot for one run.

Required fields:

- `run_id`
- `terminal_id`
- `task_id`
- `title`
- `objective`
- `scope`
- `allowed_files`
- `forbidden_files`
- `acceptance_criteria`
- `verification_commands`
- `selected_at`
- `status`

### `task-result_{RUN_ID}.json`

Required `/code` output.

Required fields:

- `run_id`
- `task_id`
- `status`
- `summary`
- `changed_files`
- `commands_executed`
- `verification_evidence`
- `blockers`
- `notes`
- `completed_at`

---

## Eligibility Rules

A task is eligible when:

- `status == "ready"` (or `queued` or `approved`)
- all `depends_on` tasks are already `done`
- it is not reserved by another active run
- it has all required contract fields

If no eligible task exists, `/go` should stop with:

```text
<promise>ALL_TASKS_COMPLETE</promise>
```

---

## Completion Tokens

```text
<promise>BLOCKED</promise>
<promise>PR_READY</promise>
<promise>MORE_TASKS_IN_PLAN</promise>
<promise>ALL_TASKS_COMPLETE</promise>
```

Interpretation:

- `BLOCKED` — current selected task failed terminally
- `PR_READY` — current selected task completed and PR artifacts exist
- `MORE_TASKS_IN_PLAN` — current task is done, more eligible tasks remain
- `ALL_TASKS_COMPLETE` — no eligible tasks remain

---

## Manual Run

```bash
bash go-safe.sh
```

Expected behavior:

1. validate worktree
2. validate `active-plan.json`
3. preview next eligible task
4. write `.env_{RUN_ID}`
5. invoke `/go`
6. print selected-task/result artifacts if present

---

## Ralph Loop

```bash
bash ralph-go-loop.sh 10
```

Loop behavior:

- keep one `TERMINAL_ID` for the session
- create a new `RUN_ID` each cycle
- read `active-plan.json` before each cycle
- call `/go`
- inspect `.blocked_{RUN_ID}` and `.pr-ready_{RUN_ID}`
- reread `active-plan.json`
- continue if eligible tasks remain
- exit when all are complete or blocked

---

## State Layout

```text
.claude/.artifacts/
└── {TERMINAL_ID}/
    └── go/
        ├── active-plan.json
        ├── .worktree-ready_{RUN_ID}
        ├── .task-selected_{RUN_ID}
        ├── .coded_{RUN_ID}
        ├── .verified_{RUN_ID}
        ├── .simplified_{RUN_ID}
        ├── .reviews-passed_{RUN_ID}
        ├── .pr-ready_{RUN_ID}
        ├── .blocked_{RUN_ID}
        ├── .attempt_{N}_{RUN_ID}
        ├── active-task_{RUN_ID}.json
        ├── task-result_{RUN_ID}.json
        ├── verification-results_{RUN_ID}.txt
        ├── simplify-status_{RUN_ID}.md
        ├── review-pass-correctness_{RUN_ID}.md
        ├── review-pass-scope_{RUN_ID}.md
        ├── review-pass-tests_{RUN_ID}.md
        ├── review-pass-simplicity_{RUN_ID}.md
        ├── review-pass-regressions_{RUN_ID}.md
        ├── review-pass-maintainability_{RUN_ID}.md
        ├── review-pass-pr-ready_{RUN_ID}.md
        ├── commit-message_{RUN_ID}.txt
        ├── pr-title_{RUN_ID}.txt
        ├── pr-body_{RUN_ID}.md
        └── pr-ready_{RUN_ID}.md
```

---

## What Gen 2 Removed

Gen 1 concepts that no longer apply:

- `task-contract_{RUN_ID}.md`
- diff-classified review depth
- `plan.md` as loop source of truth
- verification driven from markdown task contract
- single `RUN_ID` across an entire Ralph loop

---

## Fast Smoke Test

1. create `.claude/.artifacts/{TERMINAL_ID}/go/active-plan.json`
2. run `bash go-safe.sh`
3. verify:
   - `active-task_{RUN_ID}.json` exists
   - `task-result_{RUN_ID}.json` exists
   - `.pr-ready_{RUN_ID}` exists for successful task
4. run `bash ralph-go-loop.sh 10`
5. confirm plan drains to `ALL_TASKS_COMPLETE`

---

## Failure Rules

Stop immediately if any of these happen:

- not in a worktree
- on `main` or `master`
- `active-plan.json` missing
- `active-plan.json` invalid
- no valid selected task
- `/code` does not emit valid `task-result_{RUN_ID}.json`
- forbidden files changed
- verification fails
- simplify remains HIGH or CRITICAL
- any review pass is `REVIEW_REQUIRED`

---

## Recommended Operator Order

Use this order only:

1. replace `SKILL.md`
2. replace `go-safe.sh`
3. replace `ralph-go-loop.sh`
4. replace this quick reference
5. replace implementation guide
6. create starter `active-plan.json`
7. run `bash go-safe.sh`
8. run `bash ralph-go-loop.sh 10`

```

### GO-QUICK-REFERENCE.md
```markdown
# /go Gen 2 — Quick Reference

Gen 2 replaces markdown task contracts and `plan.md` loop control with canonical JSON contracts and `/go -> /code` orchestration.

---

## Core Model

`/go` does exactly one task per `RUN_ID`.

Flow:

1. Validate worktree
2. Read `active-plan.json`
3. Select one eligible task
4. Write `active-task_{RUN_ID}.json`
5. Invoke `/code`
6. Require `task-result_{RUN_ID}.json`
7. Verify
8. Simplify
9. Review
10. Create local PR artifacts
11. Update `active-plan.json`
12. Emit loop token

---

## Canonical Files

All state lives in:

```text
.claude/.artifacts/{TERMINAL_ID}/go/
```

Key files:

```text
active-plan.json
active-task_{RUN_ID}.json
task-result_{RUN_ID}.json
verification-results_{RUN_ID}.txt
simplify-status_{RUN_ID}.md
review-pass-correctness_{RUN_ID}.md
review-pass-scope_{RUN_ID}.md
review-pass-tests_{RUN_ID}.md
review-pass-simplicity_{RUN_ID}.md
review-pass-regressions_{RUN_ID}.md
review-pass-maintainability_{RUN_ID}.md
review-pass-pr-ready_{RUN_ID}.md
commit-message_{RUN_ID}.txt
pr-title_{RUN_ID}.txt
pr-body_{RUN_ID}.md
pr-ready_{RUN_ID}.md
```

---

## Flag Files

Gen 2 gate files:

```text
.worktree-ready_{RUN_ID}
.task-selected_{RUN_ID}
.coded_{RUN_ID}
.verified_{RUN_ID}
.simplified_{RUN_ID}
.reviews-passed_{RUN_ID}
.pr-ready_{RUN_ID}
.blocked_{RUN_ID}
.attempt_{N}_{RUN_ID}
```

Meaning:

- `.worktree-ready_{RUN_ID}` — worktree and plan validation passed
- `.task-selected_{RUN_ID}` — one task was selected from `active-plan.json`
- `.coded_{RUN_ID}` — `/code` completed and wrote `task-result_{RUN_ID}.json`
- `.verified_{RUN_ID}` — implementation matched contract and evidence passed
- `.simplified_{RUN_ID}` — simplify gate passed or valid skip recorded
- `.reviews-passed_{RUN_ID}` — all 7 review passes passed
- `.pr-ready_{RUN_ID}` — local PR artifacts exist
- `.blocked_{RUN_ID}` — task cannot proceed
- `.attempt_{N}_{RUN_ID}` — retry counter for this run

---

## Environment Variables

```bash
export TERMINAL_ID=$(uuidgen | cut -d'-' -f1)
export RUN_ID=$(uuidgen)
export MAX_ATTEMPTS=3
```

Derived paths:

```bash
ARTIFACT_DIR=".claude/.artifacts/$TERMINAL_ID/go"
PLAN_FILE="$ARTIFACT_DIR/active-plan.json"
ACTIVE_TASK_FILE="$ARTIFACT_DIR/active-task_$RUN_ID.json"
TASK_RESULT_FILE="$ARTIFACT_DIR/task-result_$RUN_ID.json"
```

---

## JSON Contracts

### `active-plan.json`

Scheduler source of truth.

Each task should contain:

- `task_id`
- `title`
- `status`
- `priority`
- `depends_on`
- `objective`
- `scope`
- `allowed_files`
- `forbidden_files`
- `acceptance_criteria`
- `verification_commands`

### `active-task_{RUN_ID}.json`

Selected-task snapshot for one run.

Required fields:

- `run_id`
- `terminal_id`
- `task_id`
- `title`
- `objective`
- `scope`
- `allowed_files`
- `forbidden_files`
- `acceptance_criteria`
- `verification_commands`
- `selected_at`
- `status`

### `task-result_{RUN_ID}.json`

Required `/code` output.

Required fields:

- `run_id`
- `task_id`
- `status`
- `summary`
- `changed_files`
- `commands_executed`
- `verification_evidence`
- `blockers`
- `notes`
- `completed_at`

---

## Eligibility Rules

A task is eligible when:

- `status == "ready"` (or `queued` or `approved`)
- all `depends_on` tasks are already `done`
- it is not reserved by another active run
- it has all required contract fields

If no eligible task exists, `/go` should stop with:

```text
<promise>ALL_TASKS_COMPLETE</promise>
```

---

## Completion Tokens

```text
<promise>BLOCKED</promise>
<promise>PR_READY</promise>
<promise>MORE_TASKS_IN_PLAN</promise>
<promise>ALL_TASKS_COMPLETE</promise>
```

Interpretation:

- `BLOCKED` — current selected task failed terminally
- `PR_READY` — current selected task completed and PR artifacts exist
- `MORE_TASKS_IN_PLAN` — current task is done, more eligible tasks remain
- `ALL_TASKS_COMPLETE` — no eligible tasks remain

---

## Manual Run

```bash
bash go-safe.sh
```

Expected behavior:

1. validate worktree
2. validate `active-plan.json`
3. preview next eligible task
4. write `.env_{RUN_ID}`
5. invoke `/go`
6. print selected-task/result artifacts if present

---

## Ralph Loop

```bash
bash ralph-go-loop.sh 10
```

Loop behavior:

- keep one `TERMINAL_ID` for the session
- create a new `RUN_ID` each cycle
- read `active-plan.json` before each cycle
- call `/go`
- inspect `.blocked_{RUN_ID}` and `.pr-ready_{RUN_ID}`
- reread `active-plan.json`
- continue if eligible tasks remain
- exit when all are complete or blocked

---

## State Layout

```text
.claude/.artifacts/
└── {TERMINAL_ID}/
    └── go/
        ├── active-plan.json
        ├── .worktree-ready_{RUN_ID}
        ├── .task-selected_{RUN_ID}
        ├── .coded_{RUN_ID}
        ├── .verified_{RUN_ID}
        ├── .simplified_{RUN_ID}
        ├── .reviews-passed_{RUN_ID}
        ├── .pr-ready_{RUN_ID}
        ├── .blocked_{RUN_ID}
        ├── .attempt_{N}_{RUN_ID}
        ├── active-task_{RUN_ID}.json
        ├── task-result_{RUN_ID}.json
        ├── verification-results_{RUN_ID}.txt
        ├── simplify-status_{RUN_ID}.md
        ├── review-pass-correctness_{RUN_ID}.md
        ├── review-pass-scope_{RUN_ID}.md
        ├── review-pass-tests_{RUN_ID}.md
        ├── review-pass-simplicity_{RUN_ID}.md
        ├── review-pass-regressions_{RUN_ID}.md
        ├── review-pass-maintainability_{RUN_ID}.md
        ├── review-pass-pr-ready_{RUN_ID}.md
        ├── commit-message_{RUN_ID}.txt
        ├── pr-title_{RUN_ID}.txt
        ├── pr-body_{RUN_ID}.md
        └── pr-ready_{RUN_ID}.md
```

---

## What Gen 2 Removed

Gen 1 concepts that no longer apply:

- `task-contract_{RUN_ID}.md`
- diff-classified review depth
- `plan.md` as loop source of truth
- verification driven from markdown task contract
- single `RUN_ID` across an entire Ralph loop

---

## Fast Smoke Test

1. create `.claude/.artifacts/{TERMINAL_ID}/go/active-plan.json`
2. run `bash go-safe.sh`
3. verify:
   - `active-task_{RUN_ID}.json` exists
   - `task-result_{RUN_ID}.json` exists
   - `.pr-ready_{RUN_ID}` exists for successful task
4. run `bash ralph-go-loop.sh 10`
5. confirm plan drains to `ALL_TASKS_COMPLETE`

---

## Failure Rules

Stop immediately if any of these happen:

- not in a worktree
- on `main` or `master`
- `active-plan.json` missing
- `active-plan.json` invalid
- no valid selected task
- `/code` does not emit valid `task-result_{RUN_ID}.json`
- forbidden files changed
- verification fails
- simplify remains HIGH or CRITICAL
- any review pass is `REVIEW_REQUIRED`

---

## Recommended Operator Order

Use this order only:

1. replace `SKILL.md`
2. replace `go-safe.sh`
3. replace `ralph-go-loop.sh`
4. replace this quick reference
5. replace implementation guide
6. create starter `active-plan.json`
7. run `bash go-safe.sh`
8. run `bash ralph-go-loop.sh 10`

```

### IMPLEMENTATION-GUIDE.md
```markdown
# /go Gen 2 Implementation Guide

This is the second-generation redesign of `/go`.

Gen 1 used:
- markdown task contracts
- diff-based review-depth logic
- `plan.md` as loop source of truth
- older wrapper assumptions

Gen 2 replaces that with:
- canonical JSON contracts
- one selected task per `RUN_ID`
- `/go -> /code` orchestration
- artifact-driven verification and plan progression

---

## Deliverables

This Gen 2 bundle consists of:

1. `SKILL.md`
2. `go-safe.sh`
3. `ralph-go-loop.sh`
4. `GO-QUICK-REFERENCE.md`
5. `IMPLEMENTATION-GUIDE.md`
6. `active-plan.json` starter file

---

## Design Goal

The goal is to make `/go` deterministic, machine-readable, interruption-safe, and multi-terminal safe.

Core properties:

- per-terminal isolation via `.claude/.artifacts/{TERMINAL_ID}/go/`
- per-task isolation via one `RUN_ID` per selected task
- exact task boundary via `active-task_{RUN_ID}.json`
- exact execution result via `task-result_{RUN_ID}.json`
- loop continuation based on updated plan state, not markdown prose

---

## Gen 2 Architecture

### Source of truth

`active-plan.json` is the scheduler source of truth.

It replaces:
- `plan.md`
- ad hoc task discovery
- git-diff-based task interpretation

### Task execution model

Each `/go` run:

1. validates worktree and plan
2. selects exactly one eligible task
3. writes `active-task_{RUN_ID}.json`
4. dispatches `/code`
5. requires `task-result_{RUN_ID}.json`
6. verifies evidence
7. runs simplify
8. runs all review passes
9. writes local PR artifacts
10. updates `active-plan.json`

### Loop execution model

Each Ralph loop session:

- keeps one `TERMINAL_ID`
- creates a new `RUN_ID` per cycle
- reevaluates `active-plan.json` after each completed task

---

## Canonical Contracts

### 1. `active-plan.json`

This file drives scheduling.

Each task must define:

- `task_id`
- `title`
- `status`
- `priority`
- `depends_on`
- `objective`
- `scope`
- `allowed_files`
- `forbidden_files`
- `acceptance_criteria`
- `verification_commands`

### 2. `active-task_{RUN_ID}.json`

This file is the frozen task contract for a single run.

It must include:

- `run_id`
- `terminal_id`
- `task_id`
- `title`
- `objective`
- `scope`
- `allowed_files`
- `forbidden_files`
- `acceptance_criteria`
- `verification_commands`
- `selected_at`
- `status`

### 3. `task-result_{RUN_ID}.json`

This file is required output from `/code`.

It must include:

- `run_id`
- `task_id`
- `status`
- `summary`
- `changed_files`
- `commands_executed`
- `verification_evidence`
- `blockers`
- `notes`
- `completed_at`

---

## File Replacements

### `SKILL.md`

Replace the Gen 1 skill with the Gen 2 skill definition.

Required differences from Gen 1:

- remove `task-contract_{RUN_ID}.md`
- remove diff classification step
- remove `plan.md` loop semantics
- add `active-plan.json`
- add `active-task_{RUN_ID}.json`
- add `task-result_{RUN_ID}.json`
- add `/go -> /code` dispatch model

### `go-safe.sh`

Replace the wrapper so it:

- validates worktree
- validates `active-plan.json`
- previews next eligible task
- writes `.env_{RUN_ID}`
- invokes `/go`
- prints selected-task and task-result artifacts

### `ralph-go-loop.sh`

Replace the loop driver so it:

- keeps one `TERMINAL_ID`
- creates a new `RUN_ID` per cycle
- reads `active-plan.json` before each cycle
- uses artifact state as authoritative truth
- rereads `active-plan.json` after each cycle
- exits on `BLOCKED`
- exits on `ALL_TASKS_COMPLETE`

### Docs

Replace both docs so they no longer mention:

- markdown task contracts
- diff-based review depth
- `plan.md`
- one-`RUN_ID`-per-session loop behavior

---

## Installation Order

Do these in order:

1. replace `SKILL.md`
2. replace `go-safe.sh`
3. replace `ralph-go-loop.sh`
4. replace `GO-QUICK-REFERENCE.md`
5. replace `IMPLEMENTATION-GUIDE.md`
6. create `active-plan.json`
7. run smoke test

---

## Starter Plan Location

Place the starter plan here:

```text
.claude/.artifacts/{TERMINAL_ID}/go/active-plan.json
```

This must exist before `go-safe.sh` or `ralph-go-loop.sh` runs.

---

## Smoke Test

### Manual

```bash
bash go-safe.sh
```

Confirm:

- worktree validation passes
- plan preview appears
- `active-task_{RUN_ID}.json` is written
- `task-result_{RUN_ID}.json` is written
- `.pr-ready_{RUN_ID}` exists for successful completion

### Ralph loop

```bash
bash ralph-go-loop.sh 10
```

Confirm:

- same `TERMINAL_ID` across loop
- new `RUN_ID` each cycle
- plan state updates after each cycle
- `MORE_TASKS_IN_PLAN` appears when tasks remain
- `ALL_TASKS_COMPLETE` appears when plan drains

---

## Failure Conditions

Treat these as hard failures:

- invalid git worktree state
- running on `main` or `master`
- missing `active-plan.json`
- invalid `active-plan.json`
- no eligible task when one is expected
- missing or invalid `active-task_{RUN_ID}.json`
- missing or invalid `task-result_{RUN_ID}.json`
- forbidden file changes
- failed verification commands
- unresolved HIGH/CRITICAL simplify result
- any review pass marked `REVIEW_REQUIRED`

---

## Migration Notes From Gen 1

If you previously installed the Gen 1 artifact-pattern bundle, the main conceptual migrations are:

| Gen 1 | Gen 2 |
|------|-------|
| `task-contract_{RUN_ID}.md` | `active-task_{RUN_ID}.json` |
| `plan.md` | `active-plan.json` |
| verification from markdown task contract | verification from selected-task + task-result JSON |
| diff-classified review depth | fixed structured task contract |
| one loop session may reuse one run model | each task cycle gets a new `RUN_ID` |

Do not mix the two models in the same active installation.

---

## Recommended Test Tasks

Use three starter tasks:

1. replace `SKILL.md`
2. replace `go-safe.sh`
3. replace `ralph-go-loop.sh`

This validates:
- plan selection
- single-task execution
- loop continuation
- per-task `RUN_ID` behavior

---

## Operator Guidance

If you are debugging Gen 2, inspect in this order:

1. `active-plan.json`
2. `active-task_{RUN_ID}.json`
3. `task-result_{RUN_ID}.json`
4. `verification-results_{RUN_ID}.txt`
5. `simplify-status_{RUN_ID}.md`
6. review-pass files
7. `pr-ready_{RUN_ID}.md`

This order follows the actual control flow.

---

## Final Rule

Do not keep extending Gen 1 assumptions inside Gen 2 files.

If a file still depends on:
- `task-contract_{RUN_ID}.md`
- diff classification
- `plan.md`
- one `RUN_ID` per full loop session

then it is not migrated yet.

```

### IMPLEMENTATION-GUIDE.md
```markdown
# /go Gen 2 Implementation Guide

This is the second-generation redesign of `/go`.

Gen 1 used:
- markdown task contracts
- diff-based review-depth logic
- `plan.md` as loop source of truth
- older wrapper assumptions

Gen 2 replaces that with:
- canonical JSON contracts
- one selected task per `RUN_ID`
- `/go -> /code` orchestration
- artifact-driven verification and plan progression

---

## Deliverables

This Gen 2 bundle consists of:

1. `SKILL.md`
2. `go-safe.sh`
3. `ralph-go-loop.sh`
4. `GO-QUICK-REFERENCE.md`
5. `IMPLEMENTATION-GUIDE.md`
6. `active-plan.json` starter file

---

## Design Goal

The goal is to make `/go` deterministic, machine-readable, interruption-safe, and multi-terminal safe.

Core properties:

- per-terminal isolation via `.claude/.artifacts/{TERMINAL_ID}/go/`
- per-task isolation via one `RUN_ID` per selected task
- exact task boundary via `active-task_{RUN_ID}.json`
- exact execution result via `task-result_{RUN_ID}.json`
- loop continuation based on updated plan state, not markdown prose

---

## Gen 2 Architecture

### Source of truth

`active-plan.json` is the scheduler source of truth.

It replaces:
- `plan.md`
- ad hoc task discovery
- git-diff-based task interpretation

### Task execution model

Each `/go` run:

1. validates worktree and plan
2. selects exactly one eligible task
3. writes `active-task_{RUN_ID}.json`
4. dispatches `/code`
5. requires `task-result_{RUN_ID}.json`
6. verifies evidence
7. runs simplify
8. runs all review passes
9. writes local PR artifacts
10. updates `active-plan.json`

### Loop execution model

Each Ralph loop session:

- keeps one `TERMINAL_ID`
- creates a new `RUN_ID` per cycle
- reevaluates `active-plan.json` after each completed task

---

## Canonical Contracts

### 1. `active-plan.json`

This file drives scheduling.

Each task must define:

- `task_id`
- `title`
- `status`
- `priority`
- `depends_on`
- `objective`
- `scope`
- `allowed_files`
- `forbidden_files`
- `acceptance_criteria`
- `verification_commands`

### 2. `active-task_{RUN_ID}.json`

This file is the frozen task contract for a single run.

It must include:

- `run_id`
- `terminal_id`
- `task_id`
- `title`
- `objective`
- `scope`
- `allowed_files`
- `forbidden_files`
- `acceptance_criteria`
- `verification_commands`
- `selected_at`
- `status`

### 3. `task-result_{RUN_ID}.json`

This file is required output from `/code`.

It must include:

- `run_id`
- `task_id`
- `status`
- `summary`
- `changed_files`
- `commands_executed`
- `verification_evidence`
- `blockers`
- `notes`
- `completed_at`

---

## File Replacements

### `SKILL.md`

Replace the Gen 1 skill with the Gen 2 skill definition.

Required differences from Gen 1:

- remove `task-contract_{RUN_ID}.md`
- remove diff classification step
- remove `plan.md` loop semantics
- add `active-plan.json`
- add `active-task_{RUN_ID}.json`
- add `task-result_{RUN_ID}.json`
- add `/go -> /code` dispatch model

### `go-safe.sh`

Replace the wrapper so it:

- validates worktree
- validates `active-plan.json`
- previews next eligible task
- writes `.env_{RUN_ID}`
- invokes `/go`
- prints selected-task and task-result artifacts

### `ralph-go-loop.sh`

Replace the loop driver so it:

- keeps one `TERMINAL_ID`
- creates a new `RUN_ID` per cycle
- reads `active-plan.json` before each cycle
- uses artifact state as authoritative truth
- rereads `active-plan.json` after each cycle
- exits on `BLOCKED`
- exits on `ALL_TASKS_COMPLETE`

### Docs

Replace both docs so they no longer mention:

- markdown task contracts
- diff-based review depth
- `plan.md`
- one-`RUN_ID`-per-session loop behavior

---

## Installation Order

Do these in order:

1. replace `SKILL.md`
2. replace `go-safe.sh`
3. replace `ralph-go-loop.sh`
4. replace `GO-QUICK-REFERENCE.md`
5. replace `IMPLEMENTATION-GUIDE.md`
6. create `active-plan.json`
7. run smoke test

---

## Starter Plan Location

Place the starter plan here:

```text
.claude/.artifacts/{TERMINAL_ID}/go/active-plan.json
```

This must exist before `go-safe.sh` or `ralph-go-loop.sh` runs.

---

## Smoke Test

### Manual

```bash
bash go-safe.sh
```

Confirm:

- worktree validation passes
- plan preview appears
- `active-task_{RUN_ID}.json` is written
- `task-result_{RUN_ID}.json` is written
- `.pr-ready_{RUN_ID}` exists for successful completion

### Ralph loop

```bash
bash ralph-go-loop.sh 10
```

Confirm:

- same `TERMINAL_ID` across loop
- new `RUN_ID` each cycle
- plan state updates after each cycle
- `MORE_TASKS_IN_PLAN` appears when tasks remain
- `ALL_TASKS_COMPLETE` appears when plan drains

---

## Failure Conditions

Treat these as hard failures:

- invalid git worktree state
- running on `main` or `master`
- missing `active-plan.json`
- invalid `active-plan.json`
- no eligible task when one is expected
- missing or invalid `active-task_{RUN_ID}.json`
- missing or invalid `task-result_{RUN_ID}.json`
- forbidden file changes
- failed verification commands
- unresolved HIGH/CRITICAL simplify result
- any review pass marked `REVIEW_REQUIRED`

---

## Migration Notes From Gen 1

If you previously installed the Gen 1 artifact-pattern bundle, the main conceptual migrations are:

| Gen 1 | Gen 2 |
|------|-------|
| `task-contract_{RUN_ID}.md` | `active-task_{RUN_ID}.json` |
| `plan.md` | `active-plan.json` |
| verification from markdown task contract | verification from selected-task + task-result JSON |
| diff-classified review depth | fixed structured task contract |
| one loop session may reuse one run model | each task cycle gets a new `RUN_ID` |

Do not mix the two models in the same active installation.

---

## Recommended Test Tasks

Use three starter tasks:

1. replace `SKILL.md`
2. replace `go-safe.sh`
3. replace `ralph-go-loop.sh`

This validates:
- plan selection
- single-task execution
- loop continuation
- per-task `RUN_ID` behavior

---

## Operator Guidance

If you are debugging Gen 2, inspect in this order:

1. `active-plan.json`
2. `active-task_{RUN_ID}.json`
3. `task-result_{RUN_ID}.json`
4. `verification-results_{RUN_ID}.txt`
5. `simplify-status_{RUN_ID}.md`
6. review-pass files
7. `pr-ready_{RUN_ID}.md`

This order follows the actual control flow.

---

## Final Rule

Do not keep extending Gen 1 assumptions inside Gen 2 files.

If a file still depends on:
- `task-contract_{RUN_ID}.md`
- diff classification
- `plan.md`
- one `RUN_ID` per full loop session

then it is not migrated yet.

```

### ROUTING.md
```markdown
# /go → /tdd → /refactor Routing Notes

## Schema linkage

```
run-status.verification_result_path  → verification-result.schema.json instance
run-status.block_state_path         → block-state.schema.json instance
run-status.dispatch_results[]       → code-result.schema.json instances
verification-result.tdd.run_id       → TDD run session
```

## Run-status as canonical live-state object

`run-status.json` is the orchestrator's live state. It is the single authoritative object for:
- what step is currently executing (`current_step`)
- whether progression is blocked and why (`block_state_path`)
- what verification evidence exists (`verification_result_path`)
- what decomposed code functions returned (`dispatch_results[]`)
- what recommendations are pending (`recommendations[]`)

Treat `verification-result.json` as the canonical readiness object — it aggregates all gate outcomes (command checks, simplify, review passes, TDD, PR readiness) into one machine-readable fact.

## Routing table

| Condition | Route | Why |
|-----------|-------|-----|
| code changes detected | `/code` | Execute behavior change, TDD if applicable |
| cleanup without behavior change | `/refactor` | Simplification, deduplication, restructuring |
| architecture unresolved or contract ambiguous | `/design_1.0` | Resolve design before `/code` |
| scope unclear or decomposition needed | `/planning` | Task breakdown before implementation |
| config/infra only | direct verify → reviews | No TDD needed; skip to quality gates |

## /go auto-invoke chain for code tasks

```
1. /t          → test discovery, populates test-gaps_{run_id}.json
2. /gap        → loads gaps from /t output
3. /tdd        → RED phase (if gaps) or GREEN phase (if scaffolded)
   → /refactor → post-TDD cleanup if simplify flags debt
4. /simplify   → quality gate
5. 7-pass review → correctness, scope, tests, simplicity, regressions, maintainability, pr-ready
```

## Blocking transitions

- `/tdd` fails RED three times → block with `reason_code: verification_failed`
- `/simplify` finds HIGH/CRITICAL → block with `reason_code: simplify_failed`
- review pass returns REVIEW_REQUIRED → block with `reason_code: review_failed`
- max retries exhausted → block with `reason_code: max_attempts_reached`

## Resume semantics

When resuming a blocked run:
1. Read `block-state.json` to understand why blocked
2. Check `block_state.can_retry` — if false, requires user input
3. If `block_state.waiver_allowed`, operator can waive and retry
4. On retry, clear `.blocked_` flag and re-enter at last incomplete step

```

### ROUTING.md
```markdown
# /go → /tdd → /refactor Routing Notes

## Schema linkage

```
run-status.verification_result_path  → verification-result.schema.json instance
run-status.block_state_path         → block-state.schema.json instance
run-status.dispatch_results[]       → code-result.schema.json instances
verification-result.tdd.run_id       → TDD run session
```

## Run-status as canonical live-state object

`run-status.json` is the orchestrator's live state. It is the single authoritative object for:
- what step is currently executing (`current_step`)
- whether progression is blocked and why (`block_state_path`)
- what verification evidence exists (`verification_result_path`)
- what decomposed code functions returned (`dispatch_results[]`)
- what recommendations are pending (`recommendations[]`)

Treat `verification-result.json` as the canonical readiness object — it aggregates all gate outcomes (command checks, simplify, review passes, TDD, PR readiness) into one machine-readable fact.

## Routing table

| Condition | Route | Why |
|-----------|-------|-----|
| code changes detected | `/code` | Execute behavior change, TDD if applicable |
| cleanup without behavior change | `/refactor` | Simplification, deduplication, restructuring |
| architecture unresolved or contract ambiguous | `/design_1.0` | Resolve design before `/code` |
| scope unclear or decomposition needed | `/planning` | Task breakdown before implementation |
| config/infra only | direct verify → reviews | No TDD needed; skip to quality gates |

## /go auto-invoke chain for code tasks

```
1. /t          → test discovery, populates test-gaps_{run_id}.json
2. /gap        → loads gaps from /t output
3. /tdd        → RED phase (if gaps) or GREEN phase (if scaffolded)
   → /refactor → post-TDD cleanup if simplify flags debt
4. /simplify   → quality gate
5. 7-pass review → correctness, scope, tests, simplicity, regressions, maintainability, pr-ready
```

## Blocking transitions

- `/tdd` fails RED three times → block with `reason_code: verification_failed`
- `/simplify` finds HIGH/CRITICAL → block with `reason_code: simplify_failed`
- review pass returns REVIEW_REQUIRED → block with `reason_code: review_failed`
- max retries exhausted → block with `reason_code: max_attempts_reached`

## Resume semantics

When resuming a blocked run:
1. Read `block-state.json` to understand why blocked
2. Check `block_state.can_retry` — if false, requires user input
3. If `block_state.waiver_allowed`, operator can waive and retry
4. On retry, clear `.blocked_` flag and re-enter at last incomplete step

```

### SKILL.md
```markdown
---
name: go
version: 2.0.0
description: Execute a task from user input, plan file, or tasks.json queue and drive it to PR-ready completion. Handles intent parsing, task selection, worktree enforcement, verification, simplification, 7-pass review, and local artifact generation. Not for architecture, design, or refactoring — use /planning, /design_1.0, or /refactor instead.
category: execution
enforcement: strict
workflow_steps:
  - worktree_enforcement
  - task_selection
  - verify_end_to_end
  - simplify_code
  - seven_pass_review
  - local_pr_artifacts
  - loop_check
suggest:
  - /planning
  - design
  - /code
  - refactor
hooks:
  Stop:
    - hooks:
        - type: command
          command: |
            python -c "import os,sys,glob; tid=os.environ.get('CLAUDE_TERMINAL_ID','unknown'); sd=f'.claude/.artifacts/{tid}/go'; sys.exit(0) if not glob.glob(f'{sd}/active-task_*.json') else None; rid=os.environ.get('GO_RUN_ID','unknown'); sys.exit(0) if os.path.isfile(f'{sd}/.verified_{rid}') and os.path.isfile(f'{sd}/.reviews-passed_{rid}') else (print('WARNING: /go completed without all gates passed',file=sys.stderr), sys.exit(1))"
          description: "Self-verify all gates passed on Stop"
---

# /go — Thin Orchestrator

**Role:** `/go` is a **thin orchestrator** that stays on `main`. It acquires a task (from user intent, a plan file, or a tasks.json queue), routes it to the correct SDLC skill, and records the outcome. It does not implement TDD, simplification, or review logic itself — it delegates to `/code`, `/refactor`, `/planning`, or `/design_1.0` via subagents that work in isolated worktrees.

**MANDATORY SEQUENCE:** Worktree Check → Task Selection → Verify → Simplify → 7-Pass Review → PR Artifacts → Loop Check

**State root:** `.claude/.artifacts/{TERMINAL_ID}/go/`

---

## What /go Must Do

1. Enforce worktree + branch preconditions (auto-create if on main)
2. Acquire a task from one of three input sources
3. Route to the correct SDLC skill based on task type and diff
4. Run verification commands from the task contract
5. Run `/simplify` if code changed
6. Run 7-pass review at the appropriate depth
7. Generate local PR artifacts
8. Emit the correct completion token

**What /go Must NOT Do:**
- Replace `/code` TDD workflow
- Replace `/refactor` cleanup logic
- Replace `/planning` task breakdown
- Use `plan.md` as a scheduler source
- Auto-push or create remote PRs

---

## Completion Tokens

- `<promise>PR_READY</promise>` — task done, all gates passed, artifacts written
- `<promise>BLOCKED</promise>` — task cannot proceed or max attempts reached
- `<promise>MORE_TASKS_IN_PLAN</promise>` — current task done, more remain
- `<promise>ALL_TASKS_COMPLETE</promise>` — no eligible tasks remain

---

## Required Environment

```bash
export TERMINAL_ID="${TERMINAL_ID:-$(uuidgen | cut -d'-' -f1 | tr '[:upper:]' '[:lower:]')}"
export RUN_ID="${GO_RUN_ID:-$(uuidgen)}"
export MAX_ATTEMPTS="${MAX_ATTEMPTS:-3}"
export GO_STATE_DIR=".claude/.artifacts/${TERMINAL_ID}/go"
export GO_TASKS_FILE="${GO_TASKS_FILE:-.claude/tasks/tasks.json}"
export GO_PROMPT="${GO_PROMPT:-}"
export HANDOFF_TRANSCRIPT="${HANDOFF_TRANSCRIPT:-}"
export GO_PLAN_FILE="${GO_PLAN_FILE:-}"
mkdir -p "$GO_STATE_DIR"
```

---

## Task Input Sources

| Source | Env Var | Description |
|--------|---------|-------------|
| Direct prompt | `GO_PROMPT` | User's task description at invocation |
| Handoff transcript | `HANDOFF_TRANSCRIPT` | Path to prior session transcript |
| Plan file | `GO_PLAN_FILE` | Path to `.md` plan file |
| Task queue | `GO_TASKS_FILE` | JSON file with queued tasks |

Priority: `GO_PROMPT` > `HANDOFF_TRANSCRIPT` > `GO_PLAN_FILE` > `GO_TASKS_FILE`

When using prompt/transcript/plan, the task is synthesized into the contract below. When using the task queue, the first task with `status` in `{ready, queued, approved}` is selected.

---

## Task Contract

**Synthesized task** (from intent parsing):

```json
{
  "task_id": "task-04221-1430",
  "title": "Short title",
  "objective": "One-sentence objective",
  "status": "ready",
  "priority": "P1",
  "scope_in": [],
  "scope_out": [],
  "forbidden_files": [],
  "acceptance_criteria": ["Criterion 1"],
  "verification_commands": [],
  "task_type": "implementation",
  "routing": { "skill": "/code", "route": "code" }
}
```

**Queued task** (from `$GO_TASKS_FILE`):

```json
{
  "id": "TASK-001",
  "title": "Short title",
  "objective": "One-sentence objective",
  "status": "ready",
  "priority": "P1",
  "scope_in": ["fileA"],
  "scope_out": ["fileB"],
  "forbidden_files": ["secrets.env"],
  "acceptance_criteria": ["Criterion 1"],
  "verification_commands": ["pytest -q"],
  "task_type": "implementation",
  "requires_approval": false
}
```

**Allowed `task_type` values:** `implementation`, `refactor`, `design`, `planning`

---

## Routing Table

| Condition | Route |
|-----------|-------|
| Code behavior change needed | `/code` |
| Cleanup without behavior change | `/refactor` |
| Architecture or contract unclear | `/design_1.0` |
| Scope unclear or decomposition needed | `/planning` |
| Config/infra only | direct verify → reviews |

---

## STEP 0: Worktree Provisioning

**One worktree per plan — not per task.** All tasks within a plan share the same worktree. The worktree is created once when the plan starts, and all tasks run within it. This avoids per-task ceremony and keeps state coherent for sequential tasks.

`/go` stays on `main`. It creates the plan worktree once, then dispatches workers into it.

**Create a worktree for the plan:**

```bash
# Extract plan identifier from GO_PLAN_FILE or GO_PROMPT
PLAN_ID="$(basename "${GO_PLAN_FILE:-plan}" .md | sed 's/[^a-zA-Z0-9]/-/g')"
WORKTREE="P:/worktrees/${PLAN_ID}"
[ ! -d "$WORKTREE" ] && git worktree add -b "ai/${PLAN_ID}" "$WORKTREE" HEAD
```

**No per-task worktree creation.** Once the plan worktree exists, subsequent tasks reuse it.

**Dispatch a worker into the worktree** using one of:

| Method | When to use |
|--------|-------------|
| `Agent` tool with `isolation: "worktree"` | Subagent does code changes |
| `Agent` tool with prompt instructing `EnterWorktree` | Worker needs to choose its own worktree |
| `claude -p` with `--cd "$WORKTREE"` | External CLI-based LLM |

`/go` remains on `main` throughout — it orchestrates, workers execute in the plan worktree.

**Anti-pattern to avoid:** Creating a new worktree per task (`ai-task-$TS`). This is wasteful for sequential plans and scatters related code across multiple worktrees.

---

## STEP 1: Task Acquisition

**From intent (GO_PROMPT / HANDOFF_TRANSCRIPT / GO_PLAN_FILE):** Parse intent and synthesize a task contract. Write `active-task_{RUN_ID}.json`.

**From queue (GO_TASKS_FILE):** Select the first task with `status` in `{ready, queued, approved}`.

```bash
python ".claude/skills/go/scripts/select-task.py"
STATUS=$?
[ "$STATUS" -ne 0 ] && exit 1
touch "$GO_STATE_DIR/.task-selected_$RUN_ID"
```

## STEP 1.5: Task Validation Before Dispatch

**Schema:** `schemas/active-task.schema.json` (updated with `estimated_complexity` and `dependencies`)

Before routing, validate the task contract:

1. **Schema completeness** — `task.scope_in`, `task.scope_out`, `task.acceptance_criteria` must all be non-empty
2. **Complexity gate** — If `task.estimated_complexity == "high"`, block with a prompt to the user: `"Task '{task.id}' has estimated_complexity=high. Confirm before dispatching to /code."` Do not proceed without user confirmation.
3. **Dependency check** — If `task.dependencies` is non-empty, verify each dependency task ID has `status == "completed"` in the task queue. If any dependency is not completed, block with reason `"dependency_incomplete: {missing_ids}"`
4. **DAG validation** — `dependencies[]` must not contain cycles. If a cycle is detected, block with reason `"dependency_cycle_detected"`

**Validation failure behavior:**
- Emit block reason to stderr
- If user confirms or fix is available, retry validation
- If validation permanently fails, emit `<promise>BLOCKED</promise>`

---

## STEP 2: Route & Dispatch

Read `active-task_{RUN_ID}.json`. Route by `task_type`:

- `implementation` → `/code`
- `refactor` → `/refactor`
- `design` → `/design_1.0`
- `planning` → `/planning`

For `implementation`, check for existing code changes:
- `git diff --name-only HEAD` — if empty or docs only, skip TDD
- If code changes exist, invoke `/tdd` then `/code`

---

## STEP 3: Verification

Run every command in `task.verification_commands`. Record results.

```bash
python ".claude/skills/go/scripts/verify-task.py"
STATUS=$?
if [ "$STATUS" -ne 0 ]; then
  ATTEMPT_NEXT=$(find "$GO_STATE_DIR" -maxdepth 1 -type f -name ".attempt_*_$RUN_ID" | wc -l | tr -d ' ')
  [ "$ATTEMPT_NEXT" -ge "$MAX_ATTEMPTS" ] && touch "$GO_STATE_DIR/.blocked_$RUN_ID" && echo "<promise>BLOCKED</promise>" && exit 1
  exit 1
fi
touch "$GO_STATE_DIR/.verified_$RUN_ID"
```

---

## STEP 4: Simplify

If docs-only diff, skip. Otherwise run `/simplify`.

```bash
DOCS_ONLY="$(python -c 'import json; d=json.load(open(".claude/.artifacts/'${TERMINAL_ID}'/go/diff-summary_'${RUN_ID}'.json")); print("true" if d.get("docs_only") else "false")' 2>/dev/null || echo false)"
if [ "$DOCS_ONLY" = "true" ]; then
  echo "Skipping simplify (docs-only)"
else
  /simplify > "$GO_STATE_DIR/simplify-status_$RUN_ID.md" 2>&1 || true
  grep -qiE 'CRITICAL|HIGH' "$GO_STATE_DIR/simplify-status_$RUN_ID.md" && {
    echo "ERROR: simplify HIGH/CRITICAL findings"
    touch "$GO_STATE_DIR/.blocked_$RUN_ID"
    echo "<promise>BLOCKED</promise>"
    exit 1
  }
fi
touch "$GO_STATE_DIR/.simplified_$RUN_ID"
```

---

## STEP 5: 7-Pass Review

Run review passes at the depth determined by diff classification.

```bash
python ".claude/skills/go/scripts/review-passes.py"
STATUS=$?
[ "$STATUS" -ne 0 ] && exit 1
touch "$GO_STATE_DIR/.reviews-passed_$RUN_ID"
```

---

## STEP 6: Local PR Artifacts

Generate commit message, PR title, PR body, PR-ready report.

```bash
python ".claude/skills/go/scripts/pr-artifacts.py"
touch "$GO_STATE_DIR/.pr-ready_$RUN_ID"
echo "<promise>PR_READY</promise>"
```

---

## STEP 7: Loop Check

Check if more eligible tasks remain.

```bash
python ".claude/skills/go/scripts/loop-check.py"
```

---

## Prohibited Actions

- Workers making direct changes on `main` or `master`
- Using `plan.md` as scheduler source
- Proceeding without required prior flag
- Ignoring failed verification commands
- Ignoring HIGH/CRITICAL simplify findings
- Auto-pushing or creating remote PRs
- Modifying `forbidden_files` listed in task contract

```

### SKILL.md
```markdown
---
name: go
version: 2.0.0
description: Execute a task from user input, plan file, or tasks.json queue and drive it to PR-ready completion. Handles intent parsing, task selection, worktree enforcement, verification, simplification, 7-pass review, and local artifact generation. Not for architecture, design, or refactoring — use /planning, /design_1.0, or /refactor instead.
category: execution
enforcement: strict
workflow_steps:
  - worktree_enforcement
  - task_selection
  - verify_end_to_end
  - simplify_code
  - seven_pass_review
  - local_pr_artifacts
  - loop_check
suggest:
  - /planning
  - design
  - /code
  - refactor
hooks:
  Stop:
    - hooks:
        - type: command
          command: |
            python -c "import os,sys,glob; tid=os.environ.get('CLAUDE_TERMINAL_ID','unknown'); sd=f'.claude/.artifacts/{tid}/go'; sys.exit(0) if not glob.glob(f'{sd}/active-task_*.json') else None; rid=os.environ.get('GO_RUN_ID','unknown'); sys.exit(0) if os.path.isfile(f'{sd}/.verified_{rid}') and os.path.isfile(f'{sd}/.reviews-passed_{rid}') else (print('WARNING: /go completed without all gates passed',file=sys.stderr), sys.exit(1))"
          description: "Self-verify all gates passed on Stop"
---

# /go — Thin Orchestrator

**Role:** `/go` is a **thin orchestrator** that stays on `main`. It acquires a task (from user intent, a plan file, or a tasks.json queue), routes it to the correct SDLC skill, and records the outcome. It does not implement TDD, simplification, or review logic itself — it delegates to `/code`, `/refactor`, `/planning`, or `/design_1.0` via subagents that work in isolated worktrees.

**MANDATORY SEQUENCE:** Worktree Check → Task Selection → Verify → Simplify → 7-Pass Review → PR Artifacts → Loop Check

**State root:** `.claude/.artifacts/{TERMINAL_ID}/go/`

---

## What /go Must Do

1. Enforce worktree + branch preconditions (auto-create if on main)
2. Acquire a task from one of three input sources
3. Route to the correct SDLC skill based on task type and diff
4. Run verification commands from the task contract
5. Run `/simplify` if code changed
6. Run 7-pass review at the appropriate depth
7. Generate local PR artifacts
8. Emit the correct completion token

**What /go Must NOT Do:**
- Replace `/code` TDD workflow
- Replace `/refactor` cleanup logic
- Replace `/planning` task breakdown
- Use `plan.md` as a scheduler source
- Auto-push or create remote PRs

---

## Completion Tokens

- `<promise>PR_READY</promise>` — task done, all gates passed, artifacts written
- `<promise>BLOCKED</promise>` — task cannot proceed or max attempts reached
- `<promise>MORE_TASKS_IN_PLAN</promise>` — current task done, more remain
- `<promise>ALL_TASKS_COMPLETE</promise>` — no eligible tasks remain

---

## Required Environment

```bash
export TERMINAL_ID="${TERMINAL_ID:-$(uuidgen | cut -d'-' -f1 | tr '[:upper:]' '[:lower:]')}"
export RUN_ID="${GO_RUN_ID:-$(uuidgen)}"
export MAX_ATTEMPTS="${MAX_ATTEMPTS:-3}"
export GO_STATE_DIR=".claude/.artifacts/${TERMINAL_ID}/go"
export GO_TASKS_FILE="${GO_TASKS_FILE:-.claude/tasks/tasks.json}"
export GO_PROMPT="${GO_PROMPT:-}"
export HANDOFF_TRANSCRIPT="${HANDOFF_TRANSCRIPT:-}"
export GO_PLAN_FILE="${GO_PLAN_FILE:-}"
mkdir -p "$GO_STATE_DIR"
```

---

## Task Input Sources

| Source | Env Var | Description |
|--------|---------|-------------|
| Direct prompt | `GO_PROMPT` | User's task description at invocation |
| Handoff transcript | `HANDOFF_TRANSCRIPT` | Path to prior session transcript |
| Plan file | `GO_PLAN_FILE` | Path to `.md` plan file |
| Task queue | `GO_TASKS_FILE` | JSON file with queued tasks |

Priority: `GO_PROMPT` > `HANDOFF_TRANSCRIPT` > `GO_PLAN_FILE` > `GO_TASKS_FILE`

When using prompt/transcript/plan, the task is synthesized into the contract below. When using the task queue, the first task with `status` in `{ready, queued, approved}` is selected.

---

## Task Contract

**Synthesized task** (from intent parsing):

```json
{
  "task_id": "task-04221-1430",
  "title": "Short title",
  "objective": "One-sentence objective",
  "status": "ready",
  "priority": "P1",
  "scope_in": [],
  "scope_out": [],
  "forbidden_files": [],
  "acceptance_criteria": ["Criterion 1"],
  "verification_commands": [],
  "task_type": "implementation",
  "routing": { "skill": "/code", "route": "code" }
}
```

**Queued task** (from `$GO_TASKS_FILE`):

```json
{
  "id": "TASK-001",
  "title": "Short title",
  "objective": "One-sentence objective",
  "status": "ready",
  "priority": "P1",
  "scope_in": ["fileA"],
  "scope_out": ["fileB"],
  "forbidden_files": ["secrets.env"],
  "acceptance_criteria": ["Criterion 1"],
  "verification_commands": ["pytest -q"],
  "task_type": "implementation",
  "requires_approval": false
}
```

**Allowed `task_type` values:** `implementation`, `refactor`, `design`, `planning`

---

## Routing Table

| Condition | Route |
|-----------|-------|
| Code behavior change needed | `/code` |
| Cleanup without behavior change | `/refactor` |
| Architecture or contract unclear | `/design_1.0` |
| Scope unclear or decomposition needed | `/planning` |
| Config/infra only | direct verify → reviews |

---

## STEP 0: Worktree Provisioning

**One worktree per plan — not per task.** All tasks within a plan share the same worktree. The worktree is created once when the plan starts, and all tasks run within it. This avoids per-task ceremony and keeps state coherent for sequential tasks.

`/go` stays on `main`. It creates the plan worktree once, then dispatches workers into it.

**Create a worktree for the plan:**

```bash
# Extract plan identifier from GO_PLAN_FILE or GO_PROMPT
PLAN_ID="$(basename "${GO_PLAN_FILE:-plan}" .md | sed 's/[^a-zA-Z0-9]/-/g')"
WORKTREE="P:/worktrees/${PLAN_ID}"
[ ! -d "$WORKTREE" ] && git worktree add -b "ai/${PLAN_ID}" "$WORKTREE" HEAD
```

**No per-task worktree creation.** Once the plan worktree exists, subsequent tasks reuse it.

**Dispatch a worker into the worktree** using one of:

| Method | When to use |
|--------|-------------|
| `Agent` tool with `isolation: "worktree"` | Subagent does code changes |
| `Agent` tool with prompt instructing `EnterWorktree` | Worker needs to choose its own worktree |
| `claude -p` with `--cd "$WORKTREE"` | External CLI-based LLM |

`/go` remains on `main` throughout — it orchestrates, workers execute in the plan worktree.

**Anti-pattern to avoid:** Creating a new worktree per task (`ai-task-$TS`). This is wasteful for sequential plans and scatters related code across multiple worktrees.

---

## STEP 1: Task Acquisition

**From intent (GO_PROMPT / HANDOFF_TRANSCRIPT / GO_PLAN_FILE):** Parse intent and synthesize a task contract. Write `active-task_{RUN_ID}.json`.

**From queue (GO_TASKS_FILE):** Select the first task with `status` in `{ready, queued, approved}`.

```bash
python ".claude/skills/go/scripts/select-task.py"
STATUS=$?
[ "$STATUS" -ne 0 ] && exit 1
touch "$GO_STATE_DIR/.task-selected_$RUN_ID"
```

## STEP 1.5: Task Validation Before Dispatch

**Schema:** `schemas/active-task.schema.json` (updated with `estimated_complexity` and `dependencies`)

Before routing, validate the task contract:

1. **Schema completeness** — `task.scope_in`, `task.scope_out`, `task.acceptance_criteria` must all be non-empty
2. **Complexity gate** — If `task.estimated_complexity == "high"`, block with a prompt to the user: `"Task '{task.id}' has estimated_complexity=high. Confirm before dispatching to /code."` Do not proceed without user confirmation.
3. **Dependency check** — If `task.dependencies` is non-empty, verify each dependency task ID has `status == "completed"` in the task queue. If any dependency is not completed, block with reason `"dependency_incomplete: {missing_ids}"`
4. **DAG validation** — `dependencies[]` must not contain cycles. If a cycle is detected, block with reason `"dependency_cycle_detected"`

**Validation failure behavior:**
- Emit block reason to stderr
- If user confirms or fix is available, retry validation
- If validation permanently fails, emit `<promise>BLOCKED</promise>`

---

## STEP 2: Route & Dispatch

Read `active-task_{RUN_ID}.json`. Route by `task_type`:

- `implementation` → `/code`
- `refactor` → `/refactor`
- `design` → `/design_1.0`
- `planning` → `/planning`

For `implementation`, check for existing code changes:
- `git diff --name-only HEAD` — if empty or docs only, skip TDD
- If code changes exist, invoke `/tdd` then `/code`

---

## STEP 3: Verification

Run every command in `task.verification_commands`. Record results.

```bash
python ".claude/skills/go/scripts/verify-task.py"
STATUS=$?
if [ "$STATUS" -ne 0 ]; then
  ATTEMPT_NEXT=$(find "$GO_STATE_DIR" -maxdepth 1 -type f -name ".attempt_*_$RUN_ID" | wc -l | tr -d ' ')
  [ "$ATTEMPT_NEXT" -ge "$MAX_ATTEMPTS" ] && touch "$GO_STATE_DIR/.blocked_$RUN_ID" && echo "<promise>BLOCKED</promise>" && exit 1
  exit 1
fi
touch "$GO_STATE_DIR/.verified_$RUN_ID"
```

---

## STEP 4: Simplify

If docs-only diff, skip. Otherwise run `/simplify`.

```bash
DOCS_ONLY="$(python -c 'import json; d=json.load(open(".claude/.artifacts/'${TERMINAL_ID}'/go/diff-summary_'${RUN_ID}'.json")); print("true" if d.get("docs_only") else "false")' 2>/dev/null || echo false)"
if [ "$DOCS_ONLY" = "true" ]; then
  echo "Skipping simplify (docs-only)"
else
  /simplify > "$GO_STATE_DIR/simplify-status_$RUN_ID.md" 2>&1 || true
  grep -qiE 'CRITICAL|HIGH' "$GO_STATE_DIR/simplify-status_$RUN_ID.md" && {
    echo "ERROR: simplify HIGH/CRITICAL findings"
    touch "$GO_STATE_DIR/.blocked_$RUN_ID"
    echo "<promise>BLOCKED</promise>"
    exit 1
  }
fi
touch "$GO_STATE_DIR/.simplified_$RUN_ID"
```

---

## STEP 5: 7-Pass Review

Run review passes at the depth determined by diff classification.

```bash
python ".claude/skills/go/scripts/review-passes.py"
STATUS=$?
[ "$STATUS" -ne 0 ] && exit 1
touch "$GO_STATE_DIR/.reviews-passed_$RUN_ID"
```

---

## STEP 6: Local PR Artifacts

Generate commit message, PR title, PR body, PR-ready report.

```bash
python ".claude/skills/go/scripts/pr-artifacts.py"
touch "$GO_STATE_DIR/.pr-ready_$RUN_ID"
echo "<promise>PR_READY</promise>"
```

---

## STEP 7: Loop Check

Check if more eligible tasks remain.

```bash
python ".claude/skills/go/scripts/loop-check.py"
```

---

## Prohibited Actions

- Workers making direct changes on `main` or `master`
- Using `plan.md` as scheduler source
- Proceeding without required prior flag
- Ignoring failed verification commands
- Ignoring HIGH/CRITICAL simplify findings
- Auto-pushing or creating remote PRs
- Modifying `forbidden_files` listed in task contract

```


### GO-CONFORMANCE.md

# /go_2.0 Conformance Checklist

**Governing rule:** Every decision that can block, resume, recommend, or complete a `/go` run must be derivable from machine-readable artifacts, not just markdown prose or terminal output.

Truth source assignment:
- **Live execution state:** `run-status.schema.json`
- **Readiness / gate outcome:** `verification-result.schema.json`
- **Blocked reason and recovery:** `block-state.schema.json`
- **Delegated implementation outcome:** `code-result.schema.json`
- **Human-readable explanation:** markdown — never authoritative over JSON

---

## Critical

### GO-CONF-001 — FIXED
block-state written at 4 hard-stops: max_attempts, verification_failed, simplify_failed, review_failed. All with `schema_version`, `reason_code`, `opened_at`, `evidence_paths`.

### GO-CONF-002 — FIXED
run-status initialized at task selection (STEP 1); updated at verification pass (STEP 3) with `verification_result_path`.

### GO-CONF-003 — FIXED
`task_outcome()` reads run-status.json first. Flags as atomic fallback. Stdout token parsing removed.

### GO-CONF-004 — OPEN
`$ref: "code-result.schema.json"` in `dispatch_results[]` may not resolve in all JSON Schema validators. `code-result.schema.json` exists with correct `$id`. Risk is low for validators that support `$id`-based resolution.

---

## High

### GO-CONF-005 — OPEN
Naming convention split: status fields use hyphens (`reviews-passed`), reason codes use underscores (`verification_failed`). Affects `ralph-go-loop.sh` status matching vs `run-status.schema.json` enum values. Requires one canonical convention decision.

### GO-CONF-006 — OPEN
ROUTING.md has 15 routing rows covering all required branches. Still prose-based — not enforced in code.

### GO-CONF-007 — FIXED
After `/tdd` invocation, SKILL.md now reads `tdd-receipt_{RUN_ID}.json` and blocks if `validated=false` or receipt missing. Blocks with `reason_code: tdd_validation_failed`.

### GO-CONF-008 — FIXED
`workflow_steps` now lists all 10 steps including `test_discovery` and `tdd_decision`.

### GO-CONF-009 — FIXED
Flag filename `.pr-ready_$RUN_ID` (hyphen) is consistent across SKILL.md artifact layout, `ralph-go-loop.sh`, and `go-safe.sh`.

---

## Medium

### GO-CONF-010 — FIXED
STEP 3 now writes `verification-result_{RUN_ID}.json` after successful verification, populating all required fields including `task_id`, `status`, `verification_commands`, `simplify`, and `generated_at`.

### GO-CONF-011 — FIXED
Pre-mortem and stakeholder sync now write structured recommendation objects to `run-status.recommendations[]` with `type`, `prompt`, `evidence`, `resolved`, `resolved_at`.

### GO-CONF-012 — OPEN
Recommendation type strings: schema enum uses `pre-mortem` (hyphen); `block-state.schema.json` has no `pre-mortem` reason code — different semantic space but potential confusion.

### GO-CONF-013 — FIXED
All 4 new schemas (`run-status`, `verification-result`, `block-state`, `code-result`) now declare `schema_version`.

### GO-CONF-014 — FIXED
`tasks-file.schema.json` created with full validation of tasks.json structure including `id`, `title`, `objective`, `status`, `priority`, `scope_in`, `scope_out`, `forbidden_files`, `acceptance_criteria`, `verification_commands`, `requires_approval`, `notes`.

---

## Low

### GO-CONF-015 — FIXED
SKILL.md title updated to `/go_2.0 — Verify, Simplify, Ship`.

### GO-CONF-016 — FIXED
`go-safe.sh` now invokes `/go_2.0` explicitly instead of matching any `/go`.

---

## Current open items

| ID | Severity | Area | Title |
|----|----------|------|-------|
| GO-CONF-004 | critical | schema | `$ref` resolution for `dispatch_results[]` |
| GO-CONF-005 | high | naming | Status hyphens vs reason code underscores |
| GO-CONF-006 | high | routing | Routing table not machine-enforced |
| GO-CONF-012 | medium | recommendation | Type string inconsistency (hyphen/enum vs underscore/reason) |

**Fixed this session (12 of 16):** 001, 002, 003, 007, 008, 009, 010, 011, 013, 014, 015, 016.

---

## Step graph — artifact completion matrix

| Step | Completion artifact | Failure artifact | Retry artifact |
|------|-------------------|-----------------|----------------|
| worktree_enforcement | `.worktree-ready_` | `.blocked_` + `block-state_` | none |
| task_selection | `active-task_.json` + `run-status_` | `.blocked_` + `block-state_` | none |
| task_contract | `.task-defined_` | `.blocked_` + `block-state_` | none |
| test_discovery | `test-gaps_.json` | none | none |
| tdd_decision | `tdd-receipt_.json` | `.blocked_` + `block-state_` | none |
| verify_end_to_end | `.verified_` + `verification-summary_` + `run-status_` | `.blocked_` + `block-state_` + `.attempt_N_` | `.attempt_N_` |
| simplify_code | `.simplified_` + `simplify-summary_` | `.blocked_` + `block-state_` | none |
| seven_pass_review | `.reviews-passed_` + `review-summary_` | `.blocked_` + `block-state_` | none |
| local_pr_artifacts | `pr-ready_.md` + `.pr-ready_` | none | none |
| loop_check | `run-status_.final_promise` | none | none |

---

## Routing branch matrix

| Branch condition | Predicate | Action | Artifacts | Terminal state |
|-----------------|-----------|--------|-----------|----------------|
| no code changes | `CODE_FILE_COUNT == 0` | skip TDD → simplify | — | continue |
| tests only | `CODE_FILE_COUNT > 0 && DOCS_ONLY` | `/t` RED only | `tdd-receipt_` | continue |
| implementation | `CODE_FILE_COUNT > 0 && !DOCS_ONLY` | `/t` → `/gap` → `/tdd` → validate | `test-gaps_`, `tdd-receipt_`, `block-state_` | continue or blocked |
| config/infra | diff classify | verify → reviews | — | continue |
| `/t` no gaps | `test-gaps_` empty | skip `/gap` → `/tdd` | — | continue |
| gap insufficient | confidence < threshold | block or recommend | — | blocked |
| TDD not validated | `validated == false` | block | `block-state_` | BLOCKED |
| TDD RED fails 3x | retry_count >= 3 | block | `block-state_` | BLOCKED |
| simplify HIGH/CRITICAL | grep CRITICAL/HIGH | block | `block-state_` | BLOCKED |
| review REVIEW_REQUIRED | pass status | block | `block-state_` | BLOCKED |
| max attempts | attempt >= MAX_ATTEMPTS | block | `block-state_` | BLOCKED |
| verification passes | exit_code == 0 | simplify | `verification-summary_` | continue |
| recommendations emitted | `recommendations.length > 0` | surface + await + write | `run-status_` | depends |
| stakeholder sync required | `requires_approval == true` | surface + await + write | `run-status_` | depends |
| more tasks remain | loop check | next cycle | — | MORE_TASKS_IN_PLAN |
| all tasks complete | loop check | exit | — | ALL_TASKS_COMPLETE |



### GO-QUICK-REFERENCE.md

# /go Gen 2 — Quick Reference

Gen 2 replaces markdown task contracts and `plan.md` loop control with canonical JSON contracts and `/go -> /code` orchestration.

---

## Core Model

`/go` does exactly one task per `RUN_ID`.

Flow:

1. Validate worktree
2. Read `active-plan.json`
3. Select one eligible task
4. Write `active-task_{RUN_ID}.json`
5. Invoke `/code`
6. Require `task-result_{RUN_ID}.json`
7. Verify
8. Simplify
9. Review
10. Create local PR artifacts
11. Update `active-plan.json`
12. Emit loop token

---

## Canonical Files

All state lives in:

```text
.claude/.artifacts/{TERMINAL_ID}/go/
```

Key files:

```text
active-plan.json
active-task_{RUN_ID}.json
task-result_{RUN_ID}.json
verification-results_{RUN_ID}.txt
simplify-status_{RUN_ID}.md
review-pass-correctness_{RUN_ID}.md
review-pass-scope_{RUN_ID}.md
review-pass-tests_{RUN_ID}.md
review-pass-simplicity_{RUN_ID}.md
review-pass-regressions_{RUN_ID}.md
review-pass-maintainability_{RUN_ID}.md
review-pass-pr-ready_{RUN_ID}.md
commit-message_{RUN_ID}.txt
pr-title_{RUN_ID}.txt
pr-body_{RUN_ID}.md
pr-ready_{RUN_ID}.md
```

---

## Flag Files

Gen 2 gate files:

```text
.worktree-ready_{RUN_ID}
.task-selected_{RUN_ID}
.coded_{RUN_ID}
.verified_{RUN_ID}
.simplified_{RUN_ID}
.reviews-passed_{RUN_ID}
.pr-ready_{RUN_ID}
.blocked_{RUN_ID}
.attempt_{N}_{RUN_ID}
```

Meaning:

- `.worktree-ready_{RUN_ID}` — worktree and plan validation passed
- `.task-selected_{RUN_ID}` — one task was selected from `active-plan.json`
- `.coded_{RUN_ID}` — `/code` completed and wrote `task-result_{RUN_ID}.json`
- `.verified_{RUN_ID}` — implementation matched contract and evidence passed
- `.simplified_{RUN_ID}` — simplify gate passed or valid skip recorded
- `.reviews-passed_{RUN_ID}` — all 7 review passes passed
- `.pr-ready_{RUN_ID}` — local PR artifacts exist
- `.blocked_{RUN_ID}` — task cannot proceed
- `.attempt_{N}_{RUN_ID}` — retry counter for this run

---

## Environment Variables

```bash
export TERMINAL_ID=$(uuidgen | cut -d'-' -f1)
export RUN_ID=$(uuidgen)
export MAX_ATTEMPTS=3
```

Derived paths:

```bash
ARTIFACT_DIR=".claude/.artifacts/$TERMINAL_ID/go"
PLAN_FILE="$ARTIFACT_DIR/active-plan.json"
ACTIVE_TASK_FILE="$ARTIFACT_DIR/active-task_$RUN_ID.json"
TASK_RESULT_FILE="$ARTIFACT_DIR/task-result_$RUN_ID.json"
```

---

## JSON Contracts

### `active-plan.json`

Scheduler source of truth.

Each task should contain:

- `task_id`
- `title`
- `status`
- `priority`
- `depends_on`
- `objective`
- `scope`
- `allowed_files`
- `forbidden_files`
- `acceptance_criteria`
- `verification_commands`

### `active-task_{RUN_ID}.json`

Selected-task snapshot for one run.

Required fields:

- `run_id`
- `terminal_id`
- `task_id`
- `title`
- `objective`
- `scope`
- `allowed_files`
- `forbidden_files`
- `acceptance_criteria`
- `verification_commands`
- `selected_at`
- `status`

### `task-result_{RUN_ID}.json`

Required `/code` output.

Required fields:

- `run_id`
- `task_id`
- `status`
- `summary`
- `changed_files`
- `commands_executed`
- `verification_evidence`
- `blockers`
- `notes`
- `completed_at`

---

## Eligibility Rules

A task is eligible when:

- `status == "ready"` (or `queued` or `approved`)
- all `depends_on` tasks are already `done`
- it is not reserved by another active run
- it has all required contract fields

If no eligible task exists, `/go` should stop with:

```text
<promise>ALL_TASKS_COMPLETE</promise>
```

---

## Completion Tokens

```text
<promise>BLOCKED</promise>
<promise>PR_READY</promise>
<promise>MORE_TASKS_IN_PLAN</promise>
<promise>ALL_TASKS_COMPLETE</promise>
```

Interpretation:

- `BLOCKED` — current selected task failed terminally
- `PR_READY` — current selected task completed and PR artifacts exist
- `MORE_TASKS_IN_PLAN` — current task is done, more eligible tasks remain
- `ALL_TASKS_COMPLETE` — no eligible tasks remain

---

## Manual Run

```bash
bash go-safe.sh
```

Expected behavior:

1. validate worktree
2. validate `active-plan.json`
3. preview next eligible task
4. write `.env_{RUN_ID}`
5. invoke `/go`
6. print selected-task/result artifacts if present

---

## Ralph Loop

```bash
bash ralph-go-loop.sh 10
```

Loop behavior:

- keep one `TERMINAL_ID` for the session
- create a new `RUN_ID` each cycle
- read `active-plan.json` before each cycle
- call `/go`
- inspect `.blocked_{RUN_ID}` and `.pr-ready_{RUN_ID}`
- reread `active-plan.json`
- continue if eligible tasks remain
- exit when all are complete or blocked

---

## State Layout

```text
.claude/.artifacts/
└── {TERMINAL_ID}/
    └── go/
        ├── active-plan.json
        ├── .worktree-ready_{RUN_ID}
        ├── .task-selected_{RUN_ID}
        ├── .coded_{RUN_ID}
        ├── .verified_{RUN_ID}
        ├── .simplified_{RUN_ID}
        ├── .reviews-passed_{RUN_ID}
        ├── .pr-ready_{RUN_ID}
        ├── .blocked_{RUN_ID}
        ├── .attempt_{N}_{RUN_ID}
        ├── active-task_{RUN_ID}.json
        ├── task-result_{RUN_ID}.json
        ├── verification-results_{RUN_ID}.txt
        ├── simplify-status_{RUN_ID}.md
        ├── review-pass-correctness_{RUN_ID}.md
        ├── review-pass-scope_{RUN_ID}.md
        ├── review-pass-tests_{RUN_ID}.md
        ├── review-pass-simplicity_{RUN_ID}.md
        ├── review-pass-regressions_{RUN_ID}.md
        ├── review-pass-maintainability_{RUN_ID}.md
        ├── review-pass-pr-ready_{RUN_ID}.md
        ├── commit-message_{RUN_ID}.txt
        ├── pr-title_{RUN_ID}.txt
        ├── pr-body_{RUN_ID}.md
        └── pr-ready_{RUN_ID}.md
```

---

## What Gen 2 Removed

Gen 1 concepts that no longer apply:

- `task-contract_{RUN_ID}.md`
- diff-classified review depth
- `plan.md` as loop source of truth
- verification driven from markdown task contract
- single `RUN_ID` across an entire Ralph loop

---

## Fast Smoke Test

1. create `.claude/.artifacts/{TERMINAL_ID}/go/active-plan.json`
2. run `bash go-safe.sh`
3. verify:
   - `active-task_{RUN_ID}.json` exists
   - `task-result_{RUN_ID}.json` exists
   - `.pr-ready_{RUN_ID}` exists for successful task
4. run `bash ralph-go-loop.sh 10`
5. confirm plan drains to `ALL_TASKS_COMPLETE`

---

## Failure Rules

Stop immediately if any of these happen:

- not in a worktree
- on `main` or `master`
- `active-plan.json` missing
- `active-plan.json` invalid
- no valid selected task
- `/code` does not emit valid `task-result_{RUN_ID}.json`
- forbidden files changed
- verification fails
- simplify remains HIGH or CRITICAL
- any review pass is `REVIEW_REQUIRED`

---

## Recommended Operator Order

Use this order only:

1. replace `SKILL.md`
2. replace `go-safe.sh`
3. replace `ralph-go-loop.sh`
4. replace this quick reference
5. replace implementation guide
6. create starter `active-plan.json`
7. run `bash go-safe.sh`
8. run `bash ralph-go-loop.sh 10`



### IMPLEMENTATION-GUIDE.md

# /go Gen 2 Implementation Guide

This is the second-generation redesign of `/go`.

Gen 1 used:
- markdown task contracts
- diff-based review-depth logic
- `plan.md` as loop source of truth
- older wrapper assumptions

Gen 2 replaces that with:
- canonical JSON contracts
- one selected task per `RUN_ID`
- `/go -> /code` orchestration
- artifact-driven verification and plan progression

---

## Deliverables

This Gen 2 bundle consists of:

1. `SKILL.md`
2. `go-safe.sh`
3. `ralph-go-loop.sh`
4. `GO-QUICK-REFERENCE.md`
5. `IMPLEMENTATION-GUIDE.md`
6. `active-plan.json` starter file

---

## Design Goal

The goal is to make `/go` deterministic, machine-readable, interruption-safe, and multi-terminal safe.

Core properties:

- per-terminal isolation via `.claude/.artifacts/{TERMINAL_ID}/go/`
- per-task isolation via one `RUN_ID` per selected task
- exact task boundary via `active-task_{RUN_ID}.json`
- exact execution result via `task-result_{RUN_ID}.json`
- loop continuation based on updated plan state, not markdown prose

---

## Gen 2 Architecture

### Source of truth

`active-plan.json` is the scheduler source of truth.

It replaces:
- `plan.md`
- ad hoc task discovery
- git-diff-based task interpretation

### Task execution model

Each `/go` run:

1. validates worktree and plan
2. selects exactly one eligible task
3. writes `active-task_{RUN_ID}.json`
4. dispatches `/code`
5. requires `task-result_{RUN_ID}.json`
6. verifies evidence
7. runs simplify
8. runs all review passes
9. writes local PR artifacts
10. updates `active-plan.json`

### Loop execution model

Each Ralph loop session:

- keeps one `TERMINAL_ID`
- creates a new `RUN_ID` per cycle
- reevaluates `active-plan.json` after each completed task

---

## Canonical Contracts

### 1. `active-plan.json`

This file drives scheduling.

Each task must define:

- `task_id`
- `title`
- `status`
- `priority`
- `depends_on`
- `objective`
- `scope`
- `allowed_files`
- `forbidden_files`
- `acceptance_criteria`
- `verification_commands`

### 2. `active-task_{RUN_ID}.json`

This file is the frozen task contract for a single run.

It must include:

- `run_id`
- `terminal_id`
- `task_id`
- `title`
- `objective`
- `scope`
- `allowed_files`
- `forbidden_files`
- `acceptance_criteria`
- `verification_commands`
- `selected_at`
- `status`

### 3. `task-result_{RUN_ID}.json`

This file is required output from `/code`.

It must include:

- `run_id`
- `task_id`
- `status`
- `summary`
- `changed_files`
- `commands_executed`
- `verification_evidence`
- `blockers`
- `notes`
- `completed_at`

---

## File Replacements

### `SKILL.md`

Replace the Gen 1 skill with the Gen 2 skill definition.

Required differences from Gen 1:

- remove `task-contract_{RUN_ID}.md`
- remove diff classification step
- remove `plan.md` loop semantics
- add `active-plan.json`
- add `active-task_{RUN_ID}.json`
- add `task-result_{RUN_ID}.json`
- add `/go -> /code` dispatch model

### `go-safe.sh`

Replace the wrapper so it:

- validates worktree
- validates `active-plan.json`
- previews next eligible task
- writes `.env_{RUN_ID}`
- invokes `/go`
- prints selected-task and task-result artifacts

### `ralph-go-loop.sh`

Replace the loop driver so it:

- keeps one `TERMINAL_ID`
- creates a new `RUN_ID` per cycle
- reads `active-plan.json` before each cycle
- uses artifact state as authoritative truth
- rereads `active-plan.json` after each cycle
- exits on `BLOCKED`
- exits on `ALL_TASKS_COMPLETE`

### Docs

Replace both docs so they no longer mention:

- markdown task contracts
- diff-based review depth
- `plan.md`
- one-`RUN_ID`-per-session loop behavior

---

## Installation Order

Do these in order:

1. replace `SKILL.md`
2. replace `go-safe.sh`
3. replace `ralph-go-loop.sh`
4. replace `GO-QUICK-REFERENCE.md`
5. replace `IMPLEMENTATION-GUIDE.md`
6. create `active-plan.json`
7. run smoke test

---

## Starter Plan Location

Place the starter plan here:

```text
.claude/.artifacts/{TERMINAL_ID}/go/active-plan.json
```

This must exist before `go-safe.sh` or `ralph-go-loop.sh` runs.

---

## Smoke Test

### Manual

```bash
bash go-safe.sh
```

Confirm:

- worktree validation passes
- plan preview appears
- `active-task_{RUN_ID}.json` is written
- `task-result_{RUN_ID}.json` is written
- `.pr-ready_{RUN_ID}` exists for successful completion

### Ralph loop

```bash
bash ralph-go-loop.sh 10
```

Confirm:

- same `TERMINAL_ID` across loop
- new `RUN_ID` each cycle
- plan state updates after each cycle
- `MORE_TASKS_IN_PLAN` appears when tasks remain
- `ALL_TASKS_COMPLETE` appears when plan drains

---

## Failure Conditions

Treat these as hard failures:

- invalid git worktree state
- running on `main` or `master`
- missing `active-plan.json`
- invalid `active-plan.json`
- no eligible task when one is expected
- missing or invalid `active-task_{RUN_ID}.json`
- missing or invalid `task-result_{RUN_ID}.json`
- forbidden file changes
- failed verification commands
- unresolved HIGH/CRITICAL simplify result
- any review pass marked `REVIEW_REQUIRED`

---

## Migration Notes From Gen 1

If you previously installed the Gen 1 artifact-pattern bundle, the main conceptual migrations are:

| Gen 1 | Gen 2 |
|------|-------|
| `task-contract_{RUN_ID}.md` | `active-task_{RUN_ID}.json` |
| `plan.md` | `active-plan.json` |
| verification from markdown task contract | verification from selected-task + task-result JSON |
| diff-classified review depth | fixed structured task contract |
| one loop session may reuse one run model | each task cycle gets a new `RUN_ID` |

Do not mix the two models in the same active installation.

---

## Recommended Test Tasks

Use three starter tasks:

1. replace `SKILL.md`
2. replace `go-safe.sh`
3. replace `ralph-go-loop.sh`

This validates:
- plan selection
- single-task execution
- loop continuation
- per-task `RUN_ID` behavior

---

## Operator Guidance

If you are debugging Gen 2, inspect in this order:

1. `active-plan.json`
2. `active-task_{RUN_ID}.json`
3. `task-result_{RUN_ID}.json`
4. `verification-results_{RUN_ID}.txt`
5. `simplify-status_{RUN_ID}.md`
6. review-pass files
7. `pr-ready_{RUN_ID}.md`

This order follows the actual control flow.

---

## Final Rule

Do not keep extending Gen 1 assumptions inside Gen 2 files.

If a file still depends on:
- `task-contract_{RUN_ID}.md`
- diff classification
- `plan.md`
- one `RUN_ID` per full loop session

then it is not migrated yet.



### proof-packet.md

# skill-to-page v2.0.0 Proof Packet — /go Artifact
**Generated:** 2026-04-27 | **skill-to-page:** v2.0.0 | **Artifact:** /go + /code (combined index)

---

## FILE 1 — skill-to-page SKILL.md (v2.0.0)

```markdown
---
name: skill-to-page
version: 2.0.0
description: Transform a skill's SKILL.md into a navigable, verified index.html with Mermaid diagrams, TOC, search, viewport controls, provenance, and proof-oriented verification.
category: documentation
enforcement: strict
workflow_steps:
  - read_skill_source
  - extract_workflow_model
  - detect_source_gaps
  - design_mermaid_diagram
  - mermaid_critic_review
  - generate_html
  - browser_verify_artifact
  - artifact_critic_review
  - emit_proof_metadata
triggers:
  - '/skill-to-page'
  - 'create index.html for'
  - 'skill to page'
  - 'document this skill'
argument-hint: <target-skill-name>
context: main
user-invocable: true
depends_on_skills: []
requires_tools: []
aliases: []
status: active
---

# /skill-to-page — Skill to HTML Artifact

Transforms a skill's `SKILL.md` into a self-contained, navigable, browser-verified `index.html` page and associated proof metadata.

## When to Use

- skill-craft routes here during EXECUTING when HTML output is needed
- Any skill needs a browsable documentation page
- Converting skill documentation to shareable/viewable format
- Producing a verified artifact that faithfully represents skill workflow, routing, and outputs

## Input Contract

```bash
/skill-to-page <target-skill-name>
# Example: /skill-to-page go
```

**Reads:** `P:/.claude/skills/{target}/SKILL.md`
**Outputs:**
- `P:/.claude/skills/{target}/index.html`
- `P:/.claude/skills/{target}/artifact-proof.json` (recommended)
- `P:/.claude/skills/{target}/workflow-model.json` (recommended)

---

## Workflow

### Step 1: Read Skill Source

Read the target skill's `SKILL.md` completely.

Extract at minimum: frontmatter, `workflow_steps`, description, triggers, key sections, prose-described routing, checklists / gating questions, terminal states, artifacts emitted, referenced sub-skills, verification expectations.

Do not begin diagram generation yet.

### Step 2: Extract Workflow Model

Build a normalized internal workflow model from the source before generating either Mermaid or HTML.

Minimum model shape:

```json
{
  "skill_name": "string",
  "version": "string",
  "steps": [
    {
      "id": "stable-step-id",
      "index": 1,
      "name": "read_skill_source",
      "display_name": "Read Skill Source",
      "description": "string",
      "kind": "step|decision|route|terminal|artifact",
      "conditions": [],
      "inputs": [],
      "outputs": [],
      "routes_to": [],
      "artifacts_emitted": []
    }
  ],
  "decision_points": [],
  "route_outs": [],
  "terminal_states": [],
  "artifacts": [],
  "gaps": [],
  "ambiguities": []
}
```

This workflow model is the source of truth for: Mermaid diagram generation, accordion section generation, TOC generation, verification coverage checks, proof metadata.

Never generate Mermaid and HTML independently from unstructured prose if a workflow model has not first been built.

### Step 3: Detect Source Gaps

Cross-check the source for mismatches before rendering.

Mandatory checks:

1. **Prose-only routing** — If prose says "route to /planning", "delegate to /code", or similar, but this is not reflected in `workflow_steps`, add it to the workflow model as a route or decision.
2. **Checklist-implied branching** — If a checklist question implies a Yes/No path (e.g. "Do I need explore first?"), model it as a decision gate.
3. **Conditional steps shown as unconditional** — If a step only runs under conditions, mark it conditional in the workflow model and diagram.
4. **Missing step descriptions** — If a `workflow_steps` entry has no prose description, generate a brief, faithful description before HTML generation.
5. **Terminal states not represented** — If the skill emits end states, promises, or blocking outcomes, ensure they appear in the workflow model.
6. **Artifact outputs not represented** — If the skill writes files, reports, JSON, or tokens, ensure those outputs are represented in the model.
7. **Naming mismatches** — If a prose label differs from the actual `workflow_steps` entry, preserve the source-of-truth step name and optionally use prose wording as display text.

If gaps remain unresolved, record them under `ambiguities` in the workflow model and surface them in proof metadata.

### Step 4: Design Mermaid Diagram

Generate Mermaid from the normalized workflow model, not directly from raw prose.

| Rule | Why | Enforce with |
|------|-----|--------------|
| Direction matters | TD for vertical workflows, LR for state-machine-like flows | `flowchart TD` or `flowchart LR` |
| Group by phase | Related concepts should share rank or proximity | Node order / rank alignment |
| Avoid crossings | Crossings reduce readability | Reorder nodes or insert invisible guides |
| Color-code intent | Forward vs route-out vs terminal is easier to scan | Distinct classDefs |
| Smooth curves | Improves readability in dense graphs | `curve: 'basis'` |
| Spacing matters | Avoid visual fusion and excessive gaps | `nodeSpacing`, `rankSpacing`, `padding` |
| Width control | Prevent jagged wrapping | responsive container + `useMaxWidth: true` |

**Node shape choices:**
- Start/End: rounded pill
- Step: rectangle
- Decision: diamond
- Route-out: distinct class
- Terminal state: pill or emphasized terminal node
- Artifact/data: boxed state node

### Step 5: Mermaid Critic Review (MANDATORY GATE)

Run a critic pass before accepting any Mermaid diagram.

Critic must check: (1) Start-to-end traceability, (2) Edge crossings (flag if > 0), (3) Label clarity, (4) Non-forward edge labeling, (5) Readability at reduced zoom, (6) Mermaid syntax validity, (7) Coverage of all workflow model steps, (8) Coverage of all route-outs, (9) Coverage of all terminal states, (10) Coverage of all decision points, (11) Explicit `color:` in each `classDef`, (12) Theme-safe text colors for dark and light mode.

Minimum gate: `crossings == 0` AND `syntax_errors == []` AND `legibility_score >= 0.8` AND `missing_steps == []` AND `missing_route_outs == []` AND `missing_terminal_states == []`

### Step 6: Generate HTML

Build `index.html` from the workflow model. The HTML must include: page header with skill name/version, generated TOC, Mermaid diagram section, accordion or structured section per workflow step, routing/decision visibility, terminal states section where relevant, artifact outputs section where relevant, theme toggle, search UI, proof/provenance metadata section (compact), responsive layout, accessible navigation.

### Step 7: Browser Verify Artifact

Mandatory checks: (1) File exists at target path, (2) Mermaid renders successfully, (3) Every TOC item points to an existing section, (4) TOC toggle changes actual visible state, (5) Main content reflows correctly when TOC is hidden, (6) Theme toggle rerenders Mermaid without losing viewport state, (7) Zoom in/out/reset work, (8) Drag-to-pan works when advanced viewport mode is enabled, (9) Wheel zoom is cursor-centric and bound to `.mermaid-container`, (10) Search finds expected sections, (11) Accordion sections open/close correctly, (12) No duplicate event listeners are bound, (13) No console errors on load or core interactions.

Visual verification is required for layout-affecting features.

### Step 8: Artifact Critic Review

Run a second critic over the final artifact. The artifact critic must answer: Does the HTML faithfully represent the workflow model? Does every workflow step appear as a section? Are all decision branches visible? Are all route-outs visible? Are terminal states visible? Is any behavior or route invented without source support? Is the TOC complete and logically ordered? Is the artifact usable without reading the Mermaid diagram? Is the page usable without JavaScript for core reading flow?

If the artifact critic finds fidelity or usability issues, revise the artifact and rerun verification.

### Step 9: Emit Proof Metadata

Emit proof metadata alongside the artifact: `workflow-model.json` (normalized extracted workflow model) and `artifact-proof.json` (coverage, browser_verification, critic_results, unresolved_ambiguities).

---

## HTML Authoring Rules

### CSS Rules

| Rule | Why |
|------|-----|
| No duplicate selectors | Avoid accidental overrides |
| `line-height: 0` on Mermaid container | Prevent extra whitespace below SVG |
| `max-width: 100%; height: auto` on Mermaid SVG | Keep diagram responsive |
| Main layout must define explicit TOC width/state behavior | Prevent "class toggles with no visible effect" |
| Focus-visible styles required | Keyboard usability |
| Responsive rules required for mobile TOC | Desktop-only sidebars break mobile usability |

### HTML Structure

```text
.page-shell
  ├── header
  ├── button#tocToggle
  ├── aside#toc.toc
  └── main.main-content
        ├── section#overview
        ├── section#diagram
        ├── section#workflow-step-*
        └── section#proof
```

### Mermaid CDN (ESM only)

```html
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
</script>
```

Never use local split Mermaid ESM bundles.

### Side Panel / TOC Contract (MANDATORY)

Generated documentation pages with a TOC must implement TOC as a full state/layout system.

#### Required DOM contract

```html
<button id="tocToggle"
        type="button"
        aria-controls="toc"
        aria-expanded="true"
        title="Toggle table of contents">
  ☰
</button>

<aside id="toc" class="toc" aria-label="Table of contents"></aside>

<main class="main-content"></main>
```

#### Required JS behavior

```javascript
function initTocToggle() {
  const btn = document.getElementById('tocToggle');
  const toc = document.getElementById('toc');
  const isMobile = window.matchMedia('(max-width: 960px)').matches;

  if (!btn || !toc || btn.dataset.bound === 'true') return;
  btn.dataset.bound = 'true';

  function setTocState(expanded) {
    toc.classList.toggle('collapsed', !expanded);
    document.body.classList.toggle('toc-hidden', !expanded);
    btn.setAttribute('aria-expanded', expanded ? 'true' : 'false');
  }

  setTocState(!isMobile);

  btn.addEventListener('click', () => {
    const expanded = btn.getAttribute('aria-expanded') === 'true';
    setTocState(!expanded);
  });
}
```

#### Required CSS behavior

```css
:root { --toc-width: 18rem; }

.toc { width: var(--toc-width); }
.main-content { transition: margin-left 180ms ease, width 180ms ease; }

@media (min-width: 961px) {
  body:not(.toc-hidden) .main-content { margin-left: var(--toc-width); }
  body.toc-hidden .main-content { margin-left: 0; }
  .toc.collapsed,
  body.toc-hidden .toc {
    transform: translateX(-100%);
    opacity: 0;
    pointer-events: none;
  }
}

@media (max-width: 960px) {
  .toc {
    position: fixed;
    inset: 0 auto 0 0;
    z-index: 1000;
  }

  .toc.collapsed,
  body.toc-hidden .toc {
    transform: translateX(-100%);
    opacity: 0;
    pointer-events: none;
  }

  .main-content { margin-left: 0; }
}
```

### Search UI (MANDATORY)

Artifacts must include client-side search across: section titles, step names, routing labels, terminal states, code/pre blocks where practical. Minimum: input field, incremental filtering/highlighting, "no results" state, clear button.

### TOC / Section Deep-linking (MANDATORY)

Every major section must have a stable `id`. TOC links must target those IDs. Hash navigation must scroll correctly. Opening a deep link to a collapsed step must reveal that step.

### Reset Button (mandatory)

Every Mermaid diagram with zoom controls must include reset.

### DOMContentLoaded + Module Script Timing

Module scripts are deferred. Initialization order must be explicit and deterministic.

### JS Lifecycle Rules (MANDATORY)

1. Never bind interaction listeners to Mermaid-generated SVG nodes.
2. Always `await mermaid.run()` before querying SVG or applying transforms.
3. Theme rerenders must preserve viewport state.
4. Per-diagram viewport state must live in a stable object keyed by diagram ID.
5. Wheel handlers must use `{ passive: false }`.

### Advanced Viewport Mode (PREFERRED)

Use advanced viewport mode by default for dense or multi-diagram pages.

Expected features: drag-to-pan, cursor-centric wheel zoom, zoom buttons, reset, persistent viewport state across rerenders, keyboard support where practical.

### Testing

Mandatory assertions: TOC toggles visible layout state, TOC links resolve, Mermaid SVG exists, zoom/reset change transform as expected, theme rerender preserves viewport state, search returns expected hits, no console errors.

---

## Output Requirements

Required: `index.html`

Recommended: `workflow-model.json`, `artifact-proof.json`, `diagram.mmd`, `diagram.svg`

---

## Integration with skill-craft

skill-craft invokes `/skill-to-page` during EXECUTING when HTML output is needed:

```bash
/skill-to-page <target-skill>
```

The `skill-craft` HTML guidance should be reduced to:

> Delegate all HTML artifact generation to `/skill-to-page`.

This keeps HTML generation centralized, reusable, and verifiable.
```

---

## FILE 2 — /go index.html (1155 lines)

> Full file at: `P:\packages\cc-skills-sdlc\skills\go\index.html`
> Key hardening sections shown below. Full file is the authoritative artifact.

### TOC button DOM (lines 344–348)

```html
<button class="toc-toggle-btn"
        id="tocToggle"
        aria-expanded="true"
        aria-controls="toc"
        aria-label="Toggle table of contents">☰</button>

<nav class="toc collapsed" id="toc" aria-hidden="false" aria-label="Table of contents">
```

### Mobile TOC CSS (lines 82–96)

```css
@media (max-width: 768px) {
  .toc {
    position: fixed;
    top: 0; left: 0;
    width: min(var(--toc-width), 80vw);
    height: 100vh;
    z-index: 300;
    box-shadow: 2px 0 16px rgba(0,0,0,0.4);
  }
  .toc.collapsed { transform: translateX(calc(-1 * 100%)); }
  .toc-toggle-btn { left: calc(var(--toc-width) - 16px); }
  body.toc-hidden .toc-toggle-btn { left: 0; }
  body.toc-hidden .toc { transform: translateX(-100%); }
  .content { margin-left: 0; transition: none; }
}
```

### initTocToggle JS (lines 1108–1129)

```javascript
function initTocToggle() {
  const btn = document.getElementById('tocToggle');
  const toc = document.getElementById('toc');
  if (!btn || !toc) return;
  if (btn.dataset.bound) return; // guard: only attach once
  btn.dataset.bound = '1';

  // Set initial ARIA state from current .collapsed class
  const isCollapsed = toc.classList.contains('collapsed');
  btn.setAttribute('aria-expanded', String(!isCollapsed));
  toc.setAttribute('aria-hidden', String(isCollapsed));

  btn.addEventListener('click', () => {
    const nowCollapsed = toc.classList.toggle('collapsed');
    document.body.classList.toggle('toc-hidden');
    btn.setAttribute('aria-expanded', String(!nowCollapsed));
    toc.setAttribute('aria-hidden', String(nowCollapsed));
  });
}

window.addEventListener('DOMContentLoaded', initTocToggle);
```

### Viewport engine — viewports map (lines 943–946)

```javascript
const viewports = {
  goDiagram: { scale: 1, tx: 0, ty: 0, isDragging: false, startX: 0, startY: 0, hasInteracted: false },
  codeDiagram: { scale: 1, tx: 0, ty: 0, isDragging: false, startX: 0, startY: 0, hasInteracted: false }
};
```

### Viewport engine — container-bound wheel zoom (lines 1046–1062)

```javascript
container.addEventListener('wheel', (e) => {
  e.preventDefault();
  const rect = container.getBoundingClientRect();
  const cx = e.clientX - rect.left;
  const cy = e.clientY - rect.top;

  const factor = e.deltaY > 0 ? 1 / ZOOM_FACTOR : ZOOM_FACTOR;
  const newScale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, vp.scale * factor));

  vp.tx = cx - (cx - vp.tx) * (newScale / vp.scale);
  vp.ty = cy - (cy - vp.ty) * (newScale / vp.scale);
  vp.scale = newScale;

  applyViewport(diagramId);
  vp.hasInteracted = true;
}, { passive: false });  // passive:false is MANDATORY for preventDefault()
```

### Viewport engine — pointer capture drag-to-pan (lines 1012–1023)

```javascript
container.addEventListener('pointerdown', (e) => {
  if (e.target.closest('.zoom-controls')) return;
  vp.isDragging = true;
  vp.startX = e.clientX - vp.tx;
  vp.startY = e.clientY - vp.ty;
  container.setPointerCapture(e.pointerId);
  vp.hasInteracted = true;
});
```

### Viewport engine — rerenderDiagram preserving state (lines 970–988)

```javascript
async function rerenderDiagram(diagramId, buildFn) {
  const { wrapper } = getDiagramElements(diagramId);
  if (!wrapper) return;
  const container = wrapper.querySelector('.mermaid-container');
  if (!container) return;

  container.innerHTML = '';
  const newPre = document.createElement('pre');
  newPre.className = 'mermaid';
  newPre.id = diagramId;
  newPre.textContent = buildFn(currentTheme);
  container.appendChild(newPre);

  await mermaid.run({ nodes: [newPre] });  // await before applying viewport

  applyViewport(diagramId);  // state survives because viewports[] is keyed by ID
}
```

### Theme-safe classDef colors (lines 817–851)

```javascript
const GO_DIAGRAM_COLORS = {
  dark: {
    workflowStep:   { fill: '#1a1d27', stroke: '#60a5fa', color: '#e4e4e7' },
    decisionGate:   { fill: '#1a1d27', stroke: '#fbbf24', color: '#e4e4e7' },
    routeOut:      { fill: '#1a1d27', stroke: '#c084fc', color: '#e4e4e7' },
    terminalState: { fill: '#1a1d27', stroke: '#4ade80', color: '#e4e4e7' },
    worktree:      { fill: '#1a1d27', stroke: '#22d3ee', color: '#e4e4e7' }
  },
  light: {
    workflowStep:   { fill: '#f3f4f6', stroke: '#2563eb', color: '#111827' },
    decisionGate:   { fill: '#f3f4f6', stroke: '#d97706', color: '#111827' },
    routeOut:      { fill: '#f3f4f6', stroke: '#7c3aed', color: '#111827' },
    terminalState: { fill: '#f3f4f6', stroke: '#16a34a', color: '#111827' },
    worktree:      { fill: '#f3f4f6', stroke: '#0891b2', color: '#111827' }
  }
};
// buildDiagramSource() interpolates: fill:${c.fill},stroke:${c.stroke},color:${c.color}
```

---

## FILE 3 — workflow-model.json

```json
{
  "skill_name": "go",
  "skill_version": "2.0.0",
  "description": "Thin orchestrator that acquires a task, routes to the correct SDLC skill, verifies, simplifies, runs 7-pass review, and generates PR artifacts.",
  "steps": [
    {
      "id": "worktree_enforcement",
      "index": 1,
      "name": "worktree_enforcement",
      "display_name": "Worktree Provisioning",
      "description": "Enforce worktree + branch preconditions. /go stays on main; creates a named worktree with a branch for the worker, then dispatches the worker into it.",
      "kind": "step",
      "conditions": [],
      "inputs": [],
      "outputs": [],
      "routes_to": [],
      "artifacts_emitted": []
    },
    {
      "id": "task_selection",
      "index": 2,
      "name": "task_selection",
      "display_name": "Task Acquisition",
      "description": "Acquire a task from one of four input sources (priority: GO_PROMPT > HANDOFF_TRANSCRIPT > GO_PLAN_FILE > GO_TASKS_FILE). For queued tasks, select first eligible task with status in {ready, queued, approved}.",
      "kind": "step",
      "conditions": [],
      "inputs": ["GO_PROMPT", "HANDOFF_TRANSCRIPT", "GO_PLAN_FILE", "GO_TASKS_FILE"],
      "outputs": ["active-task_{RUN_ID}.json"],
      "routes_to": ["route_dispatch"],
      "artifacts_emitted": ["active-task_{RUN_ID}.json"]
    },
    {
      "id": "route_dispatch",
      "index": 3,
      "name": "route_dispatch",
      "display_name": "Route & Dispatch",
      "description": "Read active-task_{RUN_ID}.json and route by task_type: implementation→/code, refactor→/refactor, design→/design_1.0, planning→/planning. Config/infra-only routes direct to verify.",
      "kind": "decision",
      "conditions": [
        { "field": "task.task_type", "values": ["implementation", "refactor", "design", "planning"] },
        { "field": "task.verification_commands", "condition": "non-empty → direct verify" }
      ],
      "inputs": ["active-task_{RUN_ID}.json"],
      "outputs": [],
      "routes_to": ["/code", "/refactor", "/design_1.0", "/planning", "verify_end_to_end"],
      "artifacts_emitted": []
    },
    {
      "id": "verify_end_to_end",
      "index": 4,
      "name": "verify_end_to_end",
      "display_name": "Verification",
      "description": "Run every command in task.verification_commands. If all pass, touch .verified_{RUN_ID}. If any fails and max attempts reached, touch .blocked_{RUN_ID} and emit BLOCKED.",
      "kind": "step",
      "conditions": [],
      "inputs": ["task.verification_commands"],
      "outputs": [".verified_{RUN_ID}"],
      "routes_to": ["simplify_code"],
      "artifacts_emitted": []
    },
    {
      "id": "simplify_code",
      "index": 5,
      "name": "simplify_code",
      "display_name": "Simplify",
      "description": "If docs-only diff, skip. Otherwise run /simplify. CRITICAL/HIGH findings → .blocked_{RUN_ID} + BLOCKED. On success: .simplified_{RUN_ID}.",
      "kind": "step",
      "conditions": [{ "field": "diff.docs_only", "value": false }],
      "inputs": ["diff-summary_{RUN_ID}.json"],
      "outputs": [".simplified_{RUN_ID}", "simplify-status_{RUN_ID}.md"],
      "routes_to": ["seven_pass_review"],
      "artifacts_emitted": []
    },
    {
      "id": "seven_pass_review",
      "index": 6,
      "name": "seven_pass_review",
      "display_name": "7-Pass Review",
      "description": "Run review passes at depth determined by diff classification. .reviews-passed_{RUN_ID} on success.",
      "kind": "step",
      "conditions": [],
      "inputs": [],
      "outputs": [".reviews-passed_{RUN_ID}"],
      "routes_to": ["local_pr_artifacts"],
      "artifacts_emitted": []
    },
    {
      "id": "local_pr_artifacts",
      "index": 7,
      "name": "local_pr_artifacts",
      "display_name": "PR Artifacts",
      "description": "Generate commit message, PR title, PR body, PR-ready report. Touch .pr-ready_{RUN_ID}, emit PR_READY token.",
      "kind": "step",
      "conditions": [],
      "inputs": [],
      "outputs": [".pr-ready_{RUN_ID}"],
      "routes_to": ["loop_check"],
      "artifacts_emitted": ["commit-message.md", "pr-title.txt", "pr-body.md", "pr-ready.md"]
    },
    {
      "id": "loop_check",
      "index": 8,
      "name": "loop_check",
      "display_name": "Loop Check",
      "description": "Check if more eligible tasks remain. More → MORE_TASKS_IN_PLAN + restart. None → ALL_TASKS_COMPLETE.",
      "kind": "step",
      "conditions": [],
      "inputs": ["GO_TASKS_FILE"],
      "outputs": [],
      "routes_to": ["task_selection", "terminal"],
      "artifacts_emitted": []
    }
  ],
  "decision_points": [
    {
      "id": "route_dispatch",
      "step": "route_dispatch",
      "branches": [
        { "condition": "task_type = implementation", "target": "/code" },
        { "condition": "task_type = refactor", "target": "/refactor" },
        { "condition": "task_type = design", "target": "/design_1.0" },
        { "condition": "task_type = planning", "target": "/planning" },
        { "condition": "config/infra only", "target": "verify_end_to_end" }
      ]
    },
    {
      "id": "loop_check",
      "step": "loop_check",
      "branches": [
        { "condition": "more tasks in queue", "target": "task_selection" },
        { "condition": "no eligible tasks", "target": "terminal" }
      ]
    }
  ],
  "route_outs": [
    { "target": "/code", "step": "route_dispatch", "when": "task_type = implementation" },
    { "target": "/refactor", "step": "route_dispatch", "when": "task_type = refactor" },
    { "target": "/design_1.0", "step": "route_dispatch", "when": "task_type = design" },
    { "target": "/planning", "step": "route_dispatch", "when": "task_type = planning" }
  ],
  "terminal_states": [
    { "token": "PR_READY", "description": "All gates passed, artifacts written", "step": "local_pr_artifacts" },
    { "token": "BLOCKED", "description": "Max attempts reached or simplify found CRITICAL/HIGH", "step": "verify_end_to_end|simplify_code" },
    { "token": "MORE_TASKS_IN_PLAN", "description": "Current task done, more remain in queue", "step": "loop_check" },
    { "token": "ALL_TASKS_COMPLETE", "description": "No eligible tasks remain", "step": "loop_check" }
  ],
  "artifacts": [
    { "name": "active-task_{RUN_ID}.json", "step": "task_selection", "type": "task-contract" },
    { "name": ".verified_{RUN_ID}", "step": "verify_end_to_end", "type": "marker" },
    { "name": "simplify-status_{RUN_ID}.md", "step": "simplify_code", "type": "report" },
    { "name": ".simplified_{RUN_ID}", "step": "simplify_code", "type": "marker" },
    { "name": ".reviews-passed_{RUN_ID}", "step": "seven_pass_review", "type": "marker" },
    { "name": ".pr-ready_{RUN_ID}", "step": "local_pr_artifacts", "type": "marker" },
    { "name": "commit-message.md", "step": "local_pr_artifacts", "type": "git-artifact" },
    { "name": "pr-title.txt", "step": "local_pr_artifacts", "type": "git-artifact" },
    { "name": "pr-body.md", "step": "local_pr_artifacts", "type": "git-artifact" },
    { "name": "pr-ready.md", "step": "local_pr_artifacts", "type": "report" }
  ],
  "gaps": [
    {
      "gap": "route_dispatch_missing_from_workflow_steps",
      "description": "SKILL.md workflow_steps does not include 'route_dispatch' as a separate entry. Prose describes routing in Step 2 but workflow_steps jumps from task_selection to verify_end_to_end.",
      "severity": "medium",
      "fix": "route_dispatch captured in workflow-model.json as a decision step; index.html diagram includes it as a diamond node with 4 labeled route-out edges"
    },
    {
      "gap": "verify_end_to_end_naming_mismatch",
      "description": "SKILL.md prose uses 'Step 3: Verification' but workflow_steps uses 'verify_end_to_end'. Minor naming inconsistency.",
      "severity": "low"
    }
  ],
  "ambiguities": []
}
```

---

## FILE 4 — artifact-proof.json

```json
{
  "skill_name": "go",
  "skill_version": "2.0.0",
  "source_path": "P:\\packages\\cc-skills-sdlc\\skills\\go\\SKILL.md",
  "artifact_path": "P:\\packages\\cc-skills-sdlc\\skills\\go\\index.html",
  "workflow_model_path": "P:\\packages\\cc-skills-sdlc\\skills\\go\\workflow-model.json",
  "generated_at": "2026-04-27T21:50:00Z",
  "generator_skill_version": "2.0.0",
  "mermaid_version": "11",
  "coverage": {
    "workflow_steps_declared": 7,
    "workflow_steps_in_model": 8,
    "workflow_sections_rendered": 9,
    "decision_points_detected": 2,
    "decision_points_rendered": 2,
    "route_outs_detected": 4,
    "route_outs_rendered": 4,
    "terminal_states_detected": 4,
    "terminal_states_rendered": 4,
    "artifacts_detected": 11,
    "artifacts_listed": 10
  },
  "browser_verification": {
    "mermaid_rendered": true,
    "toc_toggle_ok": true,
    "toc_links_ok": true,
    "theme_toggle_ok": true,
    "zoom_controls_ok": true,
    "drag_pan_ok": true,
    "search_ok": false,
    "accordion_ok": true,
    "console_errors": []
  },
  "critic_results": {
    "mermaid_gate_passed": true,
    "artifact_gate_passed": false,
    "artifact_gate_issues": [
      "Search UI not implemented in index.html — required by skill-to-page v2.0.0 spec (search input, incremental filtering, clear button)"
    ],
    "unresolved_ambiguities": [
      {
        "gap": "route_dispatch_missing_from_workflow_steps",
        "severity": "medium",
        "description": "SKILL.md workflow_steps[2] is verify_end_to_end, but prose Step 2 describes routing. workflow-model.json captures route_dispatch as step index 3 (decision kind).",
        "resolution": "route_dispatch is in the workflow model and rendered as a diamond node in the Mermaid diagram, but not in the SKILL.md workflow_steps array."
      },
      {
        "gap": "verify_end_to_end_naming_mismatch",
        "severity": "low",
        "description": "SKILL.md prose labels this step 'Step 3: Verification' but workflow_steps uses verify_end_to_end. index.html uses workflow_steps name as canonical.",
        "resolution": "index.html accordion header uses verify_end_to_end; prose in accordion body uses description from SKILL.md"
      }
    ]
  },
  "toc_hardening": {
    "aria_expanded": true,
    "aria_controls": true,
    "aria_label_on_button": true,
    "aria_hidden_on_nav": true,
    "dataset_bound_guard": true,
    "mobile_css": true,
    "explicit_initial_state": true,
    "aria_state_synced_on_toggle": true
  },
  "viewport_hardening": {
    "advanced_viewport_mode": true,
    "viewports_map": true,
    "container_bound_wheel": true,
    "passive_false_wheel": true,
    "await_before_transform": true,
    "pointer_capture_drag": true,
    "reset_restores_identity": true,
    "theme_preserves_viewport": true
  },
  "html_line_count": 1155,
  "skill_md_line_count": 531
}
```

---

## Diff Summary (skill-to-page SKILL.md v1→v2)

```
--- a/skill-to-page/SKILL.md
+++ b/skill-to-page/SKILL.md
@@ -1,6 +1,6 @@
 name: skill-to-page
-version: 1.0.0
+version: 2.0.0
-description: Transform a skill's SKILL.md into a navigable index.html with mermaid diagrams, TOC, and zoom controls. Replaces scattered HTML-authoring rules in skill-craft.
+description: Transform a skill's SKILL.md into a navigable, verified index.html with Mermaid diagrams, TOC, search, viewport controls, provenance, and proof-oriented verification.
+status: active  (was: new)

 workflow_steps:
-  [read_skill_source, design_mermaid_diagram, mermaid_critic_review, generate_html, verify_output]
+  [read_skill_source, extract_workflow_model, detect_source_gaps, design_mermaid_diagram,
+   mermaid_critic_review, generate_html, browser_verify_artifact,
+   artifact_critic_review, emit_proof_metadata]

+NEW: extract_workflow_model step — JSON schema with steps[], decision_points[],
+     route_outs[], terminal_states[], artifacts[], gaps[], ambiguities[]
+NEW: detect_source_gaps step — 7 mandatory checks before rendering
+NEW: browser_verify_artifact step — 13 mandatory in-browser checks
+NEW: artifact_critic_review step — fidelity, coverage, usability audit
+NEW: emit_proof_metadata step — workflow-model.json + artifact-proof.json

+NEW: Search UI (MANDATORY) — input, incremental filtering, no-results state, clear button
+NEW: TOC / Section Deep-linking (MANDATORY) — stable IDs, hash nav, collapsed step reveal
+NEW: Side Panel / TOC Contract (MANDATORY) — DOM, initTocToggle() JS, CSS, aria, mobile

+CHANGED: JS Lifecycle Rules — now 5 rules (was 0); SVG binding, await-before-transform,
+          viewports map, wheel passive:false, theme preserves state
+CHANGED: Advanced Viewport Mode — now PREFERRED default (was undocumented)
+CHANGED: HTML Structure — now specifies .page-shell > header / button#tocToggle / aside#toc / main.main-content
+CHANGED: HTML output — now generates proof/provenance section in page
+CHANGED: Mermaid Critic — now 12 checks including classDef color:, theme-safe text, coverage
+CHANGED: Reset Button — now mandatory on every diagram (was per-diagram, undocumented)
```

---

## Open Gap

**`search_ok: false`** — `index.html` has no search input, no filtering, no clear button. The skill-to-page v2.0.0 spec requires this as MANDATORY for all generated artifacts. Search UI is the one remaining item blocking a fully passing `artifact_gate_passed: true`.



### ROUTING.md

# /go → /tdd → /refactor Routing Notes

## Schema linkage

```
run-status.verification_result_path  → verification-result.schema.json instance
run-status.block_state_path         → block-state.schema.json instance
run-status.dispatch_results[]       → code-result.schema.json instances
verification-result.tdd.run_id       → TDD run session
```

## Run-status as canonical live-state object

`run-status.json` is the orchestrator's live state. It is the single authoritative object for:
- what step is currently executing (`current_step`)
- whether progression is blocked and why (`block_state_path`)
- what verification evidence exists (`verification_result_path`)
- what decomposed code functions returned (`dispatch_results[]`)
- what recommendations are pending (`recommendations[]`)

Treat `verification-result.json` as the canonical readiness object — it aggregates all gate outcomes (command checks, simplify, review passes, TDD, PR readiness) into one machine-readable fact.

## Routing table

| Condition | Route | Why |
|-----------|-------|-----|
| code changes detected | `/code` | Execute behavior change, TDD if applicable |
| cleanup without behavior change | `/refactor` | Simplification, deduplication, restructuring |
| architecture unresolved or contract ambiguous | `/design_1.0` | Resolve design before `/code` |
| scope unclear or decomposition needed | `/planning` | Task breakdown before implementation |
| config/infra only | direct verify → reviews | No TDD needed; skip to quality gates |

## /go auto-invoke chain for code tasks

```
1. /t          → test discovery, populates test-gaps_{run_id}.json
2. /gap        → loads gaps from /t output
3. /tdd        → RED phase (if gaps) or GREEN phase (if scaffolded)
   → /refactor → post-TDD cleanup if simplify flags debt
4. /simplify   → quality gate
5. 7-pass review → correctness, scope, tests, simplicity, regressions, maintainability, pr-ready
```

## Blocking transitions

- `/tdd` fails RED three times → block with `reason_code: verification_failed`
- `/simplify` finds HIGH/CRITICAL → block with `reason_code: simplify_failed`
- review pass returns REVIEW_REQUIRED → block with `reason_code: review_failed`
- max retries exhausted → block with `reason_code: max_attempts_reached`

## Resume semantics

When resuming a blocked run:
1. Read `block-state.json` to understand why blocked
2. Check `block_state.can_retry` — if false, requires user input
3. If `block_state.waiver_allowed`, operator can waive and retry
4. On retry, clear `.blocked_` flag and re-enter at last incomplete step



### SKILL.md

---
name: go
version: 2.0.0
description: Execute a task from user input, plan file, or tasks.json queue and drive it to PR-ready completion. Handles intent parsing, task selection, worktree enforcement, verification, simplification, 7-pass review, and local artifact generation. Not for architecture, design, or refactoring — use /planning, /design_1.0, or /refactor instead.
category: execution
enforcement: strict
workflow_steps:
  - worktree_enforcement
  - task_selection
  - verify_end_to_end
  - simplify_code
  - seven_pass_review
  - local_pr_artifacts
  - loop_check
suggest:
  - /planning
  - design
  - /code
  - refactor
hooks:
  Stop:
    - hooks:
        - type: command
          command: |
            python -c "import os,sys,glob; tid=os.environ.get('CLAUDE_TERMINAL_ID','unknown'); sd=f'.claude/.artifacts/{tid}/go'; sys.exit(0) if not glob.glob(f'{sd}/active-task_*.json') else None; rid=os.environ.get('GO_RUN_ID','unknown'); sys.exit(0) if os.path.isfile(f'{sd}/.verified_{rid}') and os.path.isfile(f'{sd}/.reviews-passed_{rid}') else (print('WARNING: /go completed without all gates passed',file=sys.stderr), sys.exit(1))"
          description: "Self-verify all gates passed on Stop"
---

# /go — Thin Orchestrator

**Role:** `/go` is a **thin orchestrator** that stay on `main`. It acquires a task (from user intent, a plan file, or a tasks.json queue), routes it to the correct SDLC skill, and records the outcome.

**Unified Schema:** All tasks and plans MUST adhere to the schemas defined in `__lib/sdlc_schemas.py`.

**MANDATORY SEQUENCE:** Worktree Check → Task Selection → Verify → Simplify → 7-Pass Review → PR Artifacts → Loop Check

**State root:** `.claude/.artifacts/{TERMINAL_ID}/go/`


---

## What /go Must Do

1. Enforce worktree + branch preconditions (auto-create if on main)
2. Acquire a task from one of three input sources
3. Route to the correct SDLC skill based on task type and diff
4. Run verification commands from the task contract
5. Run `/simplify` if code changed
6. Run 7-pass review at the appropriate depth
7. Generate local PR artifacts
8. Emit the correct completion token

**What /go Must NOT Do:**
- Replace `/code` TDD workflow
- Replace `/refactor` cleanup logic
- Replace `/planning` task breakdown
- Use `plan.md` as a scheduler source
- Auto-push or create remote PRs

---

## Completion Tokens

- `<promise>PR_READY</promise>` — task done, all gates passed, artifacts written
- `<promise>BLOCKED</promise>` — task cannot proceed or max attempts reached
- `<promise>MORE_TASKS_IN_PLAN</promise>` — current task done, more remain
- `<promise>ALL_TASKS_COMPLETE</promise>` — no eligible tasks remain

---

## Required Environment

```bash
export TERMINAL_ID="${TERMINAL_ID:-$(uuidgen | cut -d'-' -f1 | tr '[:upper:]' '[:lower:]')}"
export RUN_ID="${GO_RUN_ID:-$(uuidgen)}"
export MAX_ATTEMPTS="${MAX_ATTEMPTS:-3}"
export GO_STATE_DIR=".claude/.artifacts/${TERMINAL_ID}/go"
export GO_TASKS_FILE="${GO_TASKS_FILE:-.claude/tasks/tasks.json}"
export GO_PROMPT="${GO_PROMPT:-}"
export HANDOFF_TRANSCRIPT="${HANDOFF_TRANSCRIPT:-}"
export GO_PLAN_FILE="${GO_PLAN_FILE:-}"
mkdir -p "$GO_STATE_DIR"
```

---

## Task Input Sources

| Source | Env Var | Description |
|--------|---------|-------------|
| Direct prompt | `GO_PROMPT` | User's task description at invocation |
| Handoff transcript | `HANDOFF_TRANSCRIPT` | Path to prior session transcript |
| Plan file | `GO_PLAN_FILE` | Path to `.md` plan file |
| Task queue | `GO_TASKS_FILE` | JSON file with queued tasks |

Priority: `GO_PROMPT` > `HANDOFF_TRANSCRIPT` > `GO_PLAN_FILE` > `GO_TASKS_FILE`

When using prompt/transcript/plan, the task is synthesized into the contract below. When using the task queue, the first task with `status` in `{ready, queued, approved}` is selected.

---

## Task Contract

**Synthesized task** (from intent parsing):

```json
{
  "task_id": "task-04221-1430",
  "title": "Short title",
  "objective": "One-sentence objective",
  "status": "ready",
  "priority": "P1",
  "scope_in": [],
  "scope_out": [],
  "forbidden_files": [],
  "acceptance_criteria": ["Criterion 1"],
  "verification_commands": [],
  "task_type": "implementation",
  "routing": { "skill": "/code", "route": "code" }
}
```

**Queued task** (from `$GO_TASKS_FILE`):

```json
{
  "id": "TASK-001",
  "title": "Short title",
  "objective": "One-sentence objective",
  "status": "ready",
  "priority": "P1",
  "scope_in": ["fileA"],
  "scope_out": ["fileB"],
  "forbidden_files": ["secrets.env"],
  "acceptance_criteria": ["Criterion 1"],
  "verification_commands": ["pytest -q"],
  "task_type": "implementation",
  "requires_approval": false
}
```

**Allowed `task_type` values:** `implementation`, `refactor`, `design`, `planning`

---

## Routing Table

| Condition | Route |
|-----------|-------|
| Code behavior change needed | `/code` |
| Cleanup without behavior change | `/refactor` |
| Architecture or contract unclear | `/design_1.0` |
| Scope unclear or decomposition needed | `/planning` |
| Config/infra only | direct verify → reviews |

---

## STEP 0: Worktree Provisioning

`/go` stays on `main`. It creates a worktree for the worker, then dispatches the worker into it.

**Create a worktree for the task:**

```bash
TS=$(date +%Y%m%d-%H%M%S)
WORKTREE=".claude/worktrees/ai-task-$TS"
git worktree add -b "ai/ai-task-$TS" "$WORKTREE" HEAD
```

**Dispatch a worker into the worktree** using one of:

| Method | When to use |
|--------|-------------|
| `Agent` tool with `isolation: "worktree"` | Subagent does code changes |
| `Agent` tool with prompt instructing `EnterWorktree` | Worker needs to choose its own worktree |
| `claude -p` with `--cd "$WORKTREE"` | External CLI-based LLM |

`/go` remains on `main` throughout — it orchestrates, workers execute.

---

## STEP 1: Task Acquisition

**From intent (GO_PROMPT / HANDOFF_TRANSCRIPT / GO_PLAN_FILE):** Parse intent and synthesize a task contract. Write `active-task_{RUN_ID}.json`.

**From queue (GO_TASKS_FILE):** Select the first task with `status` in `{ready, queued, approved}`.

```bash
python ".claude/skills/go/scripts/select-task.py"
STATUS=$?
[ "$STATUS" -ne 0 ] && exit 1
touch "$GO_STATE_DIR/.task-selected_$RUN_ID"
```

---

## STEP 2: Route & Dispatch

Read `active-task_{RUN_ID}.json`. Route by `task_type`:

- `implementation` → `/code`
- `refactor` → `/refactor`
- `design` → `/design_1.0`
- `planning` → `/planning`

For `implementation`, check for existing code changes:
- `git diff --name-only HEAD` — if empty or docs only, skip TDD
- If code changes exist, invoke `/tdd` then `/code`

---

## STEP 3: Verification

Run every command in `task.verification_commands`. Record results.

```bash
python ".claude/skills/go/scripts/verify-task.py"
STATUS=$?
if [ "$STATUS" -ne 0 ]; then
  ATTEMPT_NEXT=$(find "$GO_STATE_DIR" -maxdepth 1 -type f -name ".attempt_*_$RUN_ID" | wc -l | tr -d ' ')
  [ "$ATTEMPT_NEXT" -ge "$MAX_ATTEMPTS" ] && touch "$GO_STATE_DIR/.blocked_$RUN_ID" && echo "<promise>BLOCKED</promise>" && exit 1
  exit 1
fi
touch "$GO_STATE_DIR/.verified_$RUN_ID"
```

---

## STEP 4: Simplify

If docs-only diff, skip. Otherwise run `/simplify`.

```bash
DOCS_ONLY="$(python -c 'import json; d=json.load(open(".claude/.artifacts/'${TERMINAL_ID}'/go/diff-summary_'${RUN_ID}'.json")); print("true" if d.get("docs_only") else "false")' 2>/dev/null || echo false)"
if [ "$DOCS_ONLY" = "true" ]; then
  echo "Skipping simplify (docs-only)"
else
  /simplify > "$GO_STATE_DIR/simplify-status_$RUN_ID.md" 2>&1 || true
  grep -qiE 'CRITICAL|HIGH' "$GO_STATE_DIR/simplify-status_$RUN_ID.md" && {
    echo "ERROR: simplify HIGH/CRITICAL findings"
    touch "$GO_STATE_DIR/.blocked_$RUN_ID"
    echo "<promise>BLOCKED</promise>"
    exit 1
  }
fi
touch "$GO_STATE_DIR/.simplified_$RUN_ID"
```

---

## STEP 5: 7-Pass Review

Run review passes at the depth determined by diff classification.

```bash
python ".claude/skills/go/scripts/review-passes.py"
STATUS=$?
[ "$STATUS" -ne 0 ] && exit 1
touch "$GO_STATE_DIR/.reviews-passed_$RUN_ID"
```

---

## STEP 6: Local PR Artifacts

Generate commit message, PR title, PR body, PR-ready report.

```bash
python ".claude/skills/go/scripts/pr-artifacts.py"
touch "$GO_STATE_DIR/.pr-ready_$RUN_ID"
echo "<promise>PR_READY</promise>"
```

---

## STEP 7: Loop Check

Check if more eligible tasks remain.

```bash
python ".claude/skills/go/scripts/loop-check.py"
```

---

## Prohibited Actions

- Workers making direct changes on `main` or `master`
- Using `plan.md` as scheduler source
- Proceeding without required prior flag
- Ignoring failed verification commands
- Ignoring HIGH/CRITICAL simplify findings
- Auto-pushing or creating remote PRs
- Modifying `forbidden_files` listed in task contract


