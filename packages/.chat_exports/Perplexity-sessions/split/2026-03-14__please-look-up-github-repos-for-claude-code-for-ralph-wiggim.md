---
title: "Please look up github repos for claude code for ralph-wiggim, and ralphy.  Please provide the architecture and working c"
date: "2026-03-14"
mode: "COPILOT"
uuid: "8213682f-165b-4f47-be8d-26c8e81c74d0"
entry_count: 13
---

## Human

Please look up github repos for claude code for ralph-wiggim, and ralphy.  Please provide the architecture and working code for another LLM to take your report and use it to enable a claude skill to look until all tasks are done and verified against a prd or spec or project plan, etc.

## Assistant

There are two main things to grab here: the Ralph-style repos you asked about, and then an architecture + code pattern for a Claude skill another LLM can drive to “work until done and verified against a PRD/spec.”

***

## Relevant Ralph / “ralphy” repos

These are the key repos and references worth studying:

- `frankbria/ralph-claude-code` – Autonomous Claude Code loop with intelligent exit detection, error handling, rate limiting, PRD import, CI, tests.[1][2]
- `snarktank/ralph` – Autonomous AI agent loop that runs AI coding tools (Amp or Claude Code) repeatedly until all PRD items are complete, using Git as memory.[3][4]
- Geoffrey Huntley’s “how-to-ralph-wiggum” – Reference repo/blog on the Ralph Wiggum technique for Claude Code (looping until done).[5][6][7]
- `michaelshimeles/ralphy` – “Ralphy is an autonomous bash script that runs multiple AI agents in a loop to complete product requirements documents,” including Claude Code, Cursor agent, etc.[8][9]

These all implement the same core pattern: a shell/CLI loop that repeatedly calls Claude Code or an AI tool with a PRD/spec + progress context, and exits when it detects completion signals.[6][7][1][3]

***

## Target architecture: “Verifier-driven Ralph” Claude skill

Objective: design a Claude Code skill and control loop that another LLM can call to drive Claude Code until all tasks derived from a PRD/spec are completed and **verified** against that PRD/spec/project plan.

High-level architecture:

1. **Inputs**
   - `prd.md` (or `spec.md`, `project-plan.md`): the authoritative requirements.[10][11]
   - `skill/skill.md`: Claude skill instructions for “PRD-driven development loop with verifier.”[12][10]
   - `skill/templates/*.md`: task list template, verification checklist, progress log format.[11][10]
   - `skill/context/*.md`: codebase conventions, architecture notes, testing strategy, etc.[10]

2. **Persistent state (files in repo)**
   - `tasks.yaml`: structured task list, with `id`, `description`, `status`, `evidence`, `verification_status`.  
   - `progress.log.md`: human-readable log of each loop iteration.  
   - `verification-report.md`: structured verifier output tied to PRD items.  
   - Git history: each completed task must have at least one commit referencing its `task_id`.[1][3][6]

3. **Loop controller (outer agent / script)**
   - A small CLI (Python or Node) that:
     - Calls Claude Code with the skill and a “loop-step” prompt.
     - Parses machine-readable signals from Claude’s output:
       - `<loop-status>continue|blocked|complete</loop-status>`
       - `<current-task>task-id</current-task>`
     - On `blocked`, raises to human or different agent.
     - On `complete`, triggers final verification run and exits.  
   - Inspired by `ralph-claude-code` and Ralph loop bash examples, but with explicit structured signals and verification stages.[13][7][3][1]

4. **Verifier sub-agent**
   - Same Claude skill (or a second `skill-verifier.md`) invoked in a “verification mode”:
     - Reads PRD + `tasks.yaml` + codebase + tests.
     - For each PRD item, checks:
       - Is there an implemented feature mapped to it?
       - Are there tests or other evidence?
       - Are acceptance criteria met (tests passing, lints clean, etc.)?[7][6][10]
     - Writes `verification-report.md` and updates `tasks.yaml` with `verification_status`.  

5. **Stop conditions (exit detection)**
   - All `tasks.status == "done"` and all `verification_status == "verified"`.[3][6][1]
   - No remaining failing tests or lint errors relevant to the PRD scope.  
   - No new discrepancies discovered in a final verification pass.  
   - Optional: multiple consecutive “done” signals and test-only loops to avoid premature exit, like `ralph-claude-code`.[6][1]

6. **API surface for another LLM**
   - A simple contract:
     - `POST /start-loop` – start a new PRD-driven loop for a repo.
     - `POST /step-loop` – run one iteration; returns updated `tasks.yaml` + status flags.
     - `POST /verify` – run verification and return `verification-report`.  
   - Or just a CLI the other LLM can call:
     - `llm-loop start path/to/prd.md`
     - `llm-loop step`
     - `llm-loop verify`  

Another LLM doesn’t need to understand Claude Code’s details; it just calls these commands and reasons over the structured files (`tasks.yaml`, `verification-report.md`).

***

## Claude skill design (files and responsibilities)

Minimal skill folder layout (for Claude Code):

```text
.claude/skills/prd-loop/
  skill.md
  task-template.md
  verification-template.md
  context/
    architecture.md
    testing-standards.md
    coding-standards.md
```

### `skill.md` (core loop behavior)

Conceptual behavior (not full text, just structure):

- Inputs to Claude Code:
  - `@prd.md`
  - `@tasks.yaml`
  - `@progress.log.md`
  - `@.claude/skills/prd-loop/context/*.md`
  - Optional: `@verification-report.md` when running in verification mode.  

- Responsibilities per iteration:
  1. If `tasks.yaml` does not exist:
     - Parse `prd.md` into a **normalized task list**: small, verifiable tasks; link each task to one or more PRD sections.
     - Save `tasks.yaml` with statuses `todo`.  
  2. Select next task:
     - Choose highest priority `todo` task (TASK SELECTION STAGE).
     - Consider dependencies encoded in `tasks.yaml`.  
  3. Plan and execute:
     - Plan steps (in natural language, but keep the plan brief).
     - Modify code/tests to implement the task.
     - Update or add tests, ensuring they reflect PRD acceptance criteria.
     - Run tests (invoke test command or at least write them; how tests are run is delegated to outer loop).  
  4. Update state:
     - Append to `progress.log.md` with a structured entry.
     - Update `tasks.yaml` to mark the task `in-progress` → `done` when finished.
     - Emit machine-readable markers:
       - `<loop-status>continue|blocked|complete</loop-status>`
       - `<current-task>task-id</current-task>`  

  5. “Complete” signals:
     - When no `todo` tasks remain, and in its judgment the PRD is fully covered, emit `<loop-status>complete</loop-status>` and a summary.  

There are examples of PRD → tasks → loop prompts in Ralph Wiggum articles and `ralph-claude-code`, which you can adapt as starting prompts.[14][13][7][1][6]

### `verification` behavior

Same or separate skill, but with distinct entry prompt:

- Input:
  - `@prd.md`
  - `@tasks.yaml`
  - `@progress.log.md`
  - Source tree (so Claude can inspect implementation and tests).
- Behavior:
  - For each PRD item:
    - List related tasks from `tasks.yaml`.
    - Inspect relevant code and tests.
    - Determine coverage and produce:
      - `status`: verified / partially-verified / failed / missing.
      - `evidence`: file paths, test names, key rationale.  
  - Write `verification-report.md` and update `tasks.yaml` with `verification_status`.  

This builds directly on how PRD-focused Claude skills are described in `anombyte93/prd-taskmaster` and “Stop re-explaining your product to AI. Build a Claude Code skill…”, which use templates and context files to align PRD structure with codebase conventions.[11][10]

***

## Example working code: outer loop controller

Here’s a **Python** sketch of a loop controller that another LLM can drive. It assumes:

- You can invoke Claude Code via a CLI `claude-code` that:
  - Receives a skill name and mode.
  - Returns stdout containing machine-readable tags.

You’ll need to adapt the CLI name and flags to your environment.

```python
import subprocess
import re
from pathlib import Path
from typing import Literal

LOOP_STATUS_RE = re.compile(r"<loop-status>(.*?)</loop-status>", re.IGNORECASE)
CURRENT_TASK_RE = re.compile(r"<current-task>(.*?)</current-task>", re.IGNORECASE)

LoopStatus = Literal["continue", "blocked", "complete"]

class PRDLoopController:
    def __init__(self, repo_path: Path, skill_name: str = "prd-loop"):
        self.repo_path = repo_path
        self.skill_name = skill_name

    def _run_claude_code(self, mode: str = "develop") -> str:
        """
        mode: 'develop' for normal loop, 'verify' for verification pass.
        """
        cmd = [
            "claude-code",
            "run-skill",
            f"--skill={self.skill_name}",
            f"--mode={mode}",
        ]
        result = subprocess.run(
            cmd,
            cwd=self.repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout

    @staticmethod
    def _parse_loop_status(output: str) -> LoopStatus:
        match = LOOP_STATUS_RE.search(output)
        if not match:
            return "continue"
        value = match.group(1).strip().lower()
        if value in ("continue", "blocked", "complete"):
            return value  # type: ignore[return-value]
        return "continue"

    @staticmethod
    def _parse_current_task(output: str) -> str | None:
        match = CURRENT_TASK_RE.search(output)
        return match.group(1).strip() if match else None

    def step(self) -> dict:
        """
        Run a single development iteration.
        Returns a small JSON object another LLM can reason over.
        """
        output = self._run_claude_code(mode="develop")
        loop_status = self._parse_loop_status(output)
        current_task = self._parse_current_task(output)

        # Optional: write raw output to a log file for traceability
        log_file = self.repo_path / ".claude" / "logs" / "loop.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("a", encoding="utf-8") as f:
            f.write("\n\n=== LOOP ITERATION ===\n")
            f.write(output)

        return {
            "loop_status": loop_status,
            "current_task": current_task,
        }

    def verify(self) -> dict:
        """
        Run a verification pass, writing verification-report.md
        and updating tasks.yaml.
        """
        output = self._run_claude_code(mode="verify")
        # You might also parse verification tags if you emit them
        return {
            "verification_run": True,
        }


def run_until_complete(repo_path: str, max_iterations: int = 100):
    controller = PRDLoopController(Path(repo_path))

    for i in range(max_iterations):
        step_info = controller.step()
        status = step_info["loop_status"]

        if status == "blocked":
            # Escalate to human or supervising LLM
            print("Loop blocked; manual intervention required.")
            return

        if status == "complete":
            print("Loop reports completion. Running verification...")
            controller.verify()
            print("Verification triggered; exiting loop.")
            return

    print("Reached max iterations without completion.")
```

This mirrors Ralph loops (iterative CLI calls, simple exit conditions) but uses structured tags the outer controller and a supervising LLM can reliably parse.[13][7][1][3]

***

## How another LLM would use this

Assume you expose the controller via a CLI the supervising LLM can call from its own toolset (e.g., “execute command”):

- Initialize:
  - `llm-loop start path/to/repo path/to/prd.md`
    - This just ensures `prd.md` is present and maybe runs an initial skill call to create `tasks.yaml`.  
- Autonomous run:
  - Repeatedly call:
    - `llm-loop step --repo path/to/repo`
    - Inspect JSON: if `loop_status == "continue"`, keep going; if `"blocked"`, inspect logs and decide; if `"complete"`, run verification.  
- Verification:
  - `llm-loop verify --repo path/to/repo`
  - Read `verification-report.md` and `tasks.yaml` to determine if:
    - All PRD items are satisfied.
    - Any risk or missing tests remain.  

Because the contract is small and file-based, *any* LLM with filesystem/command tools can orchestrate the loop. The details of Claude Code prompts and skill internals stay encapsulated in `skill.md` and templates, similar to how generic Claude Code skills encapsulate behavior for PRD generation and project management.[12][10][11]

***

If you tell me which language you want the outer loop and “API surface” in (Python CLI, Node + MCP, something else), I can sketch the full `tasks.yaml` schema, a concrete `skill.md` skeleton, and ready-to-run CLI scaffolding.  

## Human

python

## Assistant

Let’s lock onto a **Python-first** implementation for the outer loop and API surface, building on the Ralph pattern but oriented around a Claude Code skill that executes and self-verifies against a PRD/spec.[1][2][3][4]

Below is a concrete, end-to-end Python design you can actually drop into a repo and wire to a Claude Code skill.

***

## File layout

```text
your-project/
  prd.md
  .claude/skills/prd-loop/
    skill.md
    context/
      architecture.md
      testing-standards.md
      coding-standards.md
  tasks.yaml
  verification-report.md
  scripts/
    prd_loop/
      __init__.py
      controller.py
      cli.py
```

- `prd.md` – your PRD/spec/project plan.
- `tasks.yaml` – machine-readable task list; created/updated by the skill.
- `verification-report.md` – written by the verifier mode.
- `controller.py` – Python orchestration logic.
- `cli.py` – `argparse` CLI that another LLM (or you) can call.

Ralph-style loops use bash `loop.sh` and prompt files; we’re replacing `loop.sh` with a Python CLI, while keeping the “stateless iteration + on-disk state” pattern.[2][5]

***

## `controller.py`: loop controller

This assumes a `claude` CLI similar to Ralph setups (headless mode, prompt via skill).[6][4][2]
Adjust the command to your actual Claude Code CLI.

```python
# scripts/prd_loop/controller.py
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

LoopStatus = Literal["continue", "blocked", "complete"]

LOOP_STATUS_RE = re.compile(r"<loop-status>(.*?)</loop-status>", re.IGNORECASE)
CURRENT_TASK_RE = re.compile(r"<current-task>(.*?)</current-task>", re.IGNORECASE)
META_JSON_RE = re.compile(r"<loop-meta>(.*?)</loop-meta>", re.IGNORECASE | re.DOTALL)


@dataclass
class LoopResult:
    status: LoopStatus
    current_task: Optional[str]
    meta: dict


class PRDLoopController:
    """
    Orchestrates calls to a Claude Code skill that:
      - derives tasks from prd.md into tasks.yaml
      - implements tasks
      - self-verifies against the PRD
    """

    def __init__(
        self,
        repo_path: Path,
        skill_name: str = "prd-loop",
        claude_cmd: str = "claude",
        model: str = "opus",
    ) -> None:
        self.repo_path = repo_path
        self.skill_name = skill_name
        self.claude_cmd = claude_cmd
        self.model = model

    def _run_claude_code(self, mode: str) -> str:
        """
        mode:
          - 'develop' for normal task execution
          - 'verify' for verification pass
        """
        # You may need to adapt this to your Claude Code CLI semantics
        cmd = [
            self.claude_cmd,
            "-p",  # headless mode, read prompt/skill from project
            "--dangerously-skip-permissions",
            "--output-format=markdown",  # can be stream-json if you prefer
            f"--model={self.model}",
            f"--skill={self.skill_name}",
            f"--mode={mode}",
        ]

        result = subprocess.run(
            cmd,
            cwd=self.repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        output = result.stdout

        logs_dir = self.repo_path / ".claude" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = logs_dir / f"{mode}-loop.log"
        with log_file.open("a", encoding="utf-8") as f:
            f.write("\n\n==== NEW ITERATION ====\n")
            f.write(output)

        return output

    @staticmethod
    def _parse_loop_status(output: str) -> LoopStatus:
        match = LOOP_STATUS_RE.search(output)
        if not match:
            return "continue"
        val = match.group(1).strip().lower()
        if val in ("continue", "blocked", "complete"):
            return val  # type: ignore[return-value]
        return "continue"

    @staticmethod
    def _parse_current_task(output: str) -> Optional[str]:
        match = CURRENT_TASK_RE.search(output)
        return match.group(1).strip() if match else None

    @staticmethod
    def _parse_meta(output: str) -> dict:
        """
        Optionally extract a JSON blob from <loop-meta>{...}</loop-meta>
        so the other LLM can reason about richer state.
        """
        match = META_JSON_RE.search(output)
        if not match:
            return {}
        raw = match.group(1).strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def step(self) -> LoopResult:
        """
        Single development iteration.

        The skill is expected to:
          - ensure tasks.yaml exists (create from prd.md if missing)
          - pick the next task
          - implement it
          - update tasks.yaml, progress logs
          - emit <loop-status> and <current-task> markers
        """
        output = self._run_claude_code(mode="develop")
        status = self._parse_loop_status(output)
        current_task = self._parse_current_task(output)
        meta = self._parse_meta(output)

        return LoopResult(
            status=status,
            current_task=current_task,
            meta=meta,
        )

    def verify(self) -> LoopResult:
        """
        Run a verification pass.

        The skill should:
          - read prd.md, tasks.yaml, code, tests
          - update verification-report.md
          - update tasks.yaml with verification_status
          - emit <loop-status>complete</loop-status> when fully verified
        """
        output = self._run_claude_code(mode="verify")
        status = self._parse_loop_status(output)
        current_task = self._parse_current_task(output)
        meta = self._parse_meta(output)

        return LoopResult(
            status=status,
            current_task=current_task,
            meta=meta,
        )

    def run_until_complete(
        self,
        max_iterations: int = 100,
        require_verification: bool = True,
    ) -> None:
        """
        Full loop:
          - step repeatedly until status=='complete' or blocked
          - optionally run verification after completion
        """
        for i in range(max_iterations):
            result = self.step()

            if result.status == "blocked":
                print(f"[loop] Blocked on task: {result.current_task or 'unknown'}")
                return

            if result.status == "complete":
                print(f"[loop] Model reports all tasks done at iteration {i+1}")
                if require_verification:
                    print("[loop] Running verification phase...")
                    ver_result = self.verify()
                    print(f"[verify] status={ver_result.status}")
                return

        print(f"[loop] Reached max_iterations={max_iterations} without completion")
```

This draws on Ralph’s “dumb loop + smart prompt + on-disk state” pattern and extends it with explicit `<loop-status>` markers and an optional JSON meta channel.[3][4][2]

***

## `cli.py`: argparse CLI surface

This is what another LLM (or you) would actually call.

```python
# scripts/prd_loop/cli.py
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .controller import PRDLoopController


def cmd_step(args: argparse.Namespace) -> None:
    controller = PRDLoopController(
        repo_path=Path(args.repo),
        skill_name=args.skill,
        claude_cmd=args.claude_cmd,
        model=args.model,
    )
    result = controller.step()
    payload = {
        "status": result.status,
        "current_task": result.current_task,
        "meta": result.meta,
    }
    print(json.dumps(payload, indent=2))


def cmd_verify(args: argparse.Namespace) -> None:
    controller = PRDLoopController(
        repo_path=Path(args.repo),
        skill_name=args.skill,
        claude_cmd=args.claude_cmd,
        model=args.model,
    )
    result = controller.verify()
    payload = {
        "status": result.status,
        "current_task": result.current_task,
        "meta": result.meta,
    }
    print(json.dumps(payload, indent=2))


def cmd_run(args: argparse.Namespace) -> None:
    controller = PRDLoopController(
        repo_path=Path(args.repo),
        skill_name=args.skill,
        claude_cmd=args.claude_cmd,
        model=args.model,
    )
    controller.run_until_complete(
        max_iterations=args.max_iterations,
        require_verification=not args.no_verify,
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="prd-loop",
        description="PRD-driven Claude Code loop controller",
    )
    p.add_argument(
        "--repo",
        type=str,
        default=".",
        help="Path to repo root (default: current directory)",
    )
    p.add_argument(
        "--skill",
        type=str,
        default="prd-loop",
        help="Claude skill name (default: prd-loop)",
    )
    p.add_argument(
        "--claude-cmd",
        type=str,
        default="claude",
        help="Claude CLI binary (default: claude)",
    )
    p.add_argument(
        "--model",
        type=str,
        default="opus",
        help="Model name (default: opus)",
    )

    sub = p.add_subparsers(dest="cmd", required=True)

    # prd-loop step
    sp_step = sub.add_parser("step", help="Run a single loop iteration")
    sp_step.set_defaults(func=cmd_step)

    # prd-loop verify
    sp_verify = sub.add_parser("verify", help="Run a verification pass")
    sp_verify.set_defaults(func=cmd_verify)

    # prd-loop run
    sp_run = sub.add_parser("run", help="Run loop until complete or blocked")
    sp_run.add_argument(
        "--max-iterations",
        type=int,
        default=100,
        help="Max loop iterations (default: 100)",
    )
    sp_run.add_argument(
        "--no-verify",
        action="store_true",
        help="Do not run final verification phase",
    )
    sp_run.set_defaults(func=cmd_run)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
```

Usage:

- `prd-loop run --repo .` – full autonomous run with verification.
- `prd-loop step --repo .` – one iteration, JSON output for supervising LLM.
- `prd-loop verify --repo .` – explicit verification pass.

This is analogous to Ralph’s `loop.sh`, but in Python with structured JSON output for downstream LLMs/tools.[4][2][3]

***

## The Claude skill contract this expects

To make this work, your `skill.md` needs to:

- Read:
  - `prd.md`
  - `tasks.yaml` (create if missing)
  - `verification-report.md` (in verify mode)
  - any context files.  
- Write/update:
  - `tasks.yaml`
  - a human-readable log (e.g., `progress.log.md`)
  - `verification-report.md` in verify mode.  
- Emit markers in the final message:

```text
<loop-status>continue</loop-status>
<current-task>task-123</current-task>
<loop-meta>{"testSummary": "...", "newCommits": ["abc123"]}</loop-meta>
```

You can pattern this off of Ralph + Smart Ralph / spec-driven skills: PRD to JSON tasks, tasks to implementation, feedback via tests and CI.[7][3][4]

***

## How another LLM drives this

A supervising LLM with a “run shell command” tool could:

1. Start a loop:

   - `prd-loop run --repo /workspace/my-project`  
   - Or manually iterate: `prd-loop step --repo /workspace/my-project` until `status == "complete"`, then `prd-loop verify`.

2. Inspect `tasks.yaml` and `verification-report.md` between steps to decide whether to:
   - Adjust PRD.
   - Manually intervene for blocked tasks.
   - Tighten acceptance criteria.

The contract is file + CLI based, so it’s language- and model-agnostic, similar in spirit to Ralph’s openness to other CLIs (Amp, Cursor, etc.).[2][3]

***

Would you like a concrete `tasks.yaml` schema and a `skill.md` skeleton next, aligned with this controller and tuned specifically for “PRD + verification” rather than generic Ralph?  

## Human

Yes give me tasksyaml schema and skillmd
Show me full skillmd with verifier mode prompts

## Assistant

Here’s a concrete `tasks.yaml` schema and a full `skill.md` you can drop into `.claude/skills/prd-loop/`, including a **verify mode** prompt. The design borrows from spec‑driven / Smart Ralph style tasks and PRD-driven tools, but keeps the schema lean.[1][2][3][4][5]

***

## `tasks.yaml` schema

Single file at repo root: `tasks.yaml`.

```yaml
version: 1
source_prd: prd.md

tasks:
  - id: T-001
    title: "Implement user login API"
    description: >
      Implement POST /api/login that authenticates a user with email
      and password, issues a JWT, and enforces rate limiting.
    status: todo            # one of: todo | in_progress | done | blocked | wont_do
    verification_status: unverified  # one of: unverified | verified | failed | partial
    priority: high          # one of: high | medium | low
    prd_refs:
      - "2.1 Authentication API"
      - "AC-1"
    acceptance_criteria:
      - "Given valid credentials, returns 200 and a JWT."
      - "Given invalid credentials, returns 401 and no token."
      - "More than 5 failed attempts in 15 minutes lock the account."
    test_plan:
      - type: unit
        description: "Unit tests for AuthService.login with success and failure paths."
      - type: integration
        description: "HTTP tests for /api/login happy path and failures."
    dependencies:           # other task IDs
      - T-000
    evidence:
      code_paths:
        - "src/auth/login_handler.py"
        - "src/auth/jwt_service.py"
      test_paths:
        - "tests/auth/test_login_handler.py"
      commit_shas:
        - "abc1234"
        - "def5678"
      notes: >
        Login handler implemented, JWT service reused from registration.
        Integration tests passing locally.
    last_updated: "2026-03-14T22:05:00Z"

  - id: T-002
    title: "Add login UI form"
    description: "Simple email/password form with basic validation."
    status: done
    verification_status: verified
    priority: medium
    prd_refs:
      - "2.2 Login UI"
    acceptance_criteria: []
    test_plan: []
    dependencies: []
    evidence:
      code_paths:
        - "web/src/components/LoginForm.tsx"
      test_paths:
        - "web/src/components/__tests__/LoginForm.test.tsx"
      commit_shas:
        - "98ef12a"
      notes: "Meets minimal UI spec."
    last_updated: "2026-03-14T21:45:00Z"
```

Key points informed by spec‑driven / task‑master style schemas:[2][4][5][1]

- **Per‑task fields**
  - `id`: stable identifier; Claude must not change existing IDs.
  - `title`, `description`: short, concrete; no vague tasks.
  - `status`: lifecycle for implementation.
  - `verification_status`: lifecycle for PRD compliance.
  - `priority`: for selection heuristics.
  - `prd_refs`: tie tasks to PRD sections/acceptance criteria.
  - `acceptance_criteria`: copy or normalize from PRD for local reasoning.[6][2]
  - `test_plan`: how to verify success (aligned with acceptance criteria).[4][2]
  - `dependencies`: simple ordering.
  - `evidence`: pointers the verifier can inspect; encourages code + tests + commits.
  - `last_updated`: helps detect stale tasks.

- **Global fields**
  - `version`: for future schema migrations.
  - `source_prd`: path to PRD file.

***

## `skill.md` – full draft with verify mode

Place this at `.claude/skills/prd-loop/skill.md`.

It uses a **mode flag** pattern by instructing you (the human) or an outer script to pass `--mode=develop` or `--mode=verify`. The loop controller you already have will set `mode` via CLI flags; here we tell Claude how to behave in each mode and how to emit the tags your Python parses.[7][2][6]

```markdown
# PRD-Driven Development Loop Skill

You are an AI software engineer working inside a Claude Code project that uses a **Ralph-style loop**: each iteration is stateless from your perspective, but the project filesystem stores durable state (`prd.md`, `tasks.yaml`, `verification-report.md`, source code, and tests). [FACT based on typical Ralph workflows[web:39][web:40]]

Your job is to:

- Derive a high-quality, **verifiable** task list from the PRD.
- Implement tasks incrementally with tests.
- Keep `tasks.yaml` and logs up to date.
- In **verify mode**, audit the implementation against the PRD and update `verification-report.md` and `tasks.yaml`.

You will be invoked in two modes:

- `develop` – plan and implement tasks.
- `verify` – analyze and verify completed work.

The outer loop controller reads special markers from your final message:

```text
<loop-status>continue|blocked|complete</loop-status>
<current-task>T-123</current-task>
<loop-meta>{"optional": "json"}</loop-meta>
```

You **must** always emit `<loop-status>` and `<current-task>` at the very end of your response.

---

## Shared context and files

Each invocation, load and study:

- `prd.md` (or another PRD file defined in `tasks.yaml.source_prd`) – the single source of truth for requirements and acceptance criteria.
- `tasks.yaml` – the normalized task list. If it does not exist, create it from the PRD.
- `verification-report.md` – previous verification results (if present).
- `progress.log.md` – implementation log (if present).
- Source code and tests under `src/`, `app/`, `web/`, `tests/`, or similar.
- Skill context files:
  - `.claude/skills/prd-loop/context/architecture.md`
  - `.claude/skills/prd-loop/context/testing-standards.md`
  - `.claude/skills/prd-loop/context/coding-standards.md`

If any key file such as `prd.md` is missing, **do not guess requirements**. Instead:

1. Explain clearly what is missing.
2. Emit `<loop-status>blocked</loop-status>` with `<current-task>none</current-task>`.
3. Suggest concrete steps for the human to fix the problem.

---

## Tasks schema expectations

`tasks.yaml` MUST conform to this schema:

```yaml
version: 1
source_prd: prd.md
tasks:
  - id: "T-001"         # stable string ID
    title: "Short task title"
    description: "Concrete description of work to do."
    status: "todo"      # todo | in_progress | done | blocked | wont_do
    verification_status: "unverified" # unverified | verified | failed | partial
    priority: "high"    # high | medium | low
    prd_refs:           # references to PRD sections / acceptance criteria
      - "Section 2.1 Authentication API"
      - "AC-1"
    acceptance_criteria:
      - "When X, system does Y."
    test_plan:
      - type: "unit"
        description: "What unit tests should prove."
      - type: "integration"
        description: "What integration tests should prove."
    dependencies:
      - "T-000"
    evidence:
      code_paths:
        - "src/..."
      test_paths:
        - "tests/..."
      commit_shas:
        - "abc1234"
      notes: "Optional notes."
    last_updated: "ISO-8601 timestamp"
```

- You may add fields, but **never remove or rename** existing fields.
- **Never change an existing task’s `id`** once created.
- Avoid collapsing multiple requirements into one task; keep tasks as small, verifiable units.

---

## Mode: develop

Your behavior in **develop** mode:

1. **Orient**

   - Load `prd.md` and understand:
     - High-level goals.
     - Functional requirements.
     - Non-functional requirements.
     - Explicit acceptance criteria, if present.
   - Load `tasks.yaml` if it exists.

2. **Initialize tasks.yaml (if missing)**

   If `tasks.yaml` does not exist:

   - Derive a task list from the PRD.
   - For each PRD requirement or acceptance criterion, create one or more small tasks.
   - Populate:
     - `id` as `T-001`, `T-002`, ... in order of importance.
     - `title`, `description`.
     - `status: todo`.
     - `verification_status: unverified`.
     - `priority` based on impact and risk.
     - `prd_refs` pointing to PRD sections and acceptance criteria IDs.
     - `acceptance_criteria` copied or normalized from the PRD.
     - `test_plan` describing tests required to verify the task.
     - `dependencies` where obvious (e.g., auth API before UI).
     - `evidence` initially empty.
   - Write `tasks.yaml` to disk.

   In your final message:

   - Summarize the number of tasks, rough categories, and how they map to the PRD.
   - Set `<loop-status>continue</loop-status>`.
   - Set `<current-task>none</current-task>` because no task has been executed yet.

3. **Select next task**

   If `tasks.yaml` exists:

   - Parse tasks.
   - Filter to candidates with `status: todo` or `status: blocked` where the block can be resolved now.
   - Exclude tasks whose dependencies are not in `done`.
   - Rank candidates by:
     - Highest `priority`.
     - Strongest impact on unlocking other tasks.
     - Need to get a vertical slice working early.
   - Pick **exactly one** `current_task`.

   In your reasoning (not in tags):

   - Show which tasks you considered and why you picked this one.

4. **Plan**

   For the chosen `current_task`:

   - Restate the `acceptance_criteria` and `test_plan`.
   - Identify affected code areas (modules, components, endpoints).
   - Propose a small execution plan that fits within this iteration.
   - Update `tasks.yaml` to mark the task as `in_progress`.

5. **Implement**

   - Open and edit relevant files.
   - Implement minimal, testable code that satisfies the task’s acceptance criteria.
   - Create or update tests in line with `test_plan`.
   - Favor **vertical slices** over broad scaffolding: make something small but fully working.

   Do not start implementing unrelated tasks even if you see them.

6. **Run checks**

   - When possible, run tests for the changed area (e.g., `pytest`, `npm test`, or project standard).
   - If tests cannot be run automatically, at least ensure the test files are syntactically correct and logically cover the acceptance criteria.

7. **Update tasks.yaml and logs**

   - Update the selected task:
     - `status` to `done` if work for this task is complete; otherwise keep `in_progress`.
     - `evidence.code_paths` with the files you changed.
     - `evidence.test_paths` with added/updated tests.
     - `evidence.commit_shas` if a commit has already been made (if not, leave empty).
     - `evidence.notes` with a short summary.
     - `last_updated` with an ISO-8601 timestamp (you may approximate).
   - If you detect that the task is too large or unclear:
     - Split it into smaller tasks within `tasks.yaml`, keeping traceability to the original one.
   - Append an entry to `progress.log.md` summarizing:
     - Task ID and title.
     - Files touched.
     - Tests created/updated.
     - Test results or limitations.

8. **Determine loop status**

   - If there remain tasks with `status: todo` or `in_progress`:
     - Emit `<loop-status>continue</loop-status>`.
   - If **all** tasks are `status: done` or `wont_do`, and based on your reading of the PRD the implementation fully satisfies the requirements:
     - Emit `<loop-status>complete</loop-status>`.
   - If you are blocked by missing information, failing tests you cannot fix safely, or fundamental ambiguity:
     - Emit `<loop-status>blocked</loop-status>` and explain clearly.

   Always set `<current-task>` to the chosen task ID, or `none` if no task was selected.

9. **Loop meta**

   - Optionally include a JSON blob with additional info:

     ```text
     <loop-meta>{
       "implementedTask": "T-003",
       "touchedFiles": ["src/...", "tests/..."],
       "remainingTodoCount": 5,
       "allTasksDone": false
     }</loop-meta>
     ```

---

## Mode: verify

Your behavior in **verify** mode:

1. **Orient for verification**

   - Load `prd.md`, `tasks.yaml`, and current code/tests.
   - If `prd.md` or `tasks.yaml` is missing or corrupted:
     - Explain the issue.
     - Emit `<loop-status>blocked</loop-status>` and `<current-task>none</current-task>`.
     - Suggest precise fixes.

2. **Map PRD to tasks**

   - Identify logical PRD units (features, sections, acceptance criteria blocks).
   - For each unit, list which tasks in `tasks.yaml` reference it via `prd_refs`.
   - If a PRD unit has **no tasks** referencing it:
     - Note this as a gap in the verification report.

3. **Inspect implementation**

   For each task where `status: done` or `status: in_progress`:

   - Open the code listed in `evidence.code_paths` and related areas.
   - Open tests listed in `evidence.test_paths`.
   - Compare behavior to the PRD’s acceptance criteria and the task’s `acceptance_criteria` and `test_plan`.
   - Look for:
     - Missing behaviors.
     - Edge cases described in PRD but not covered by tests.
     - Regressions or contradictions with other requirements.

4. **Assign verification status**

   For each task:

   - Set `verification_status` to:
     - `verified` – implementation and tests clearly satisfy acceptance criteria and do not violate other PRD items.
     - `partial` – some acceptance criteria are met, others are missing or under-tested.
     - `failed` – significant deviations from requirements or tests failing/absent for critical behaviors.
     - `unverified` – not enough evidence (e.g., task still `todo` or `in_progress`).

   Update the `evidence.notes` and `last_updated` fields to reflect verification findings.

5. **Write verification-report.md**

   Create or overwrite `verification-report.md` with a structured report. Use this template:

   ```markdown
   # Verification Report

   Source PRD: {{source_prd}}
   Generated at: {{timestamp}}

   ## Summary

   - Total tasks: N
   - Done tasks: N_done
   - Verified tasks: N_verified
   - Partially verified tasks: N_partial
   - Failed tasks: N_failed
   - Unverified tasks: N_unverified
   - PRD sections with missing tasks: (list)

   ## Task Verification Details

   {% for task in tasks %}
   ### {{task.id}} – {{task.title}}

   - Status: {{task.status}}
   - Verification status: {{task.verification_status}}
   - PRD refs: {{task.prd_refs}}
   - Acceptance criteria:
     {% for ac in task.acceptance_criteria %}
     - {{ac}}
     {% endfor %}

   - Evidence:
     - Code paths: {{task.evidence.code_paths}}
     - Test paths: {{task.evidence.test_paths}}
     - Commit SHAs: {{task.evidence.commit_shas}}

   - Findings:
     - {{your concise assessment of coverage and gaps}}

   - Recommended follow-up:
     - {{specific tasks to fix gaps, with suggested new task IDs if needed}}
   {% endfor %}

   ## PRD Coverage Gaps

   - PRD sections or acceptance criteria with no mapped tasks:
     - {{section / criterion}} – {{description of gap and suggested task}}
   ```

   (Fill in values concretely; the above is conceptual structure.)

6. **Decide verification loop status**

   After examining all tasks:

   - If **all** tasks that correspond to PRD requirements have `status: done` and `verification_status: verified`, and you see no major requirement untouched:
     - Emit `<loop-status>complete</loop-status>`.
   - If there are tasks with `status: todo` or `verification_status` in `unverified`, `partial`, or `failed`:
     - Emit `<loop-status>continue</loop-status>`.
   - If you are blocked by missing information:
     - Emit `<loop-status>blocked</loop-status>`.

   Set `<current-task>` to either:
   - The **most critical** task that is `failed` or `partial`, where further implementation work should focus.
   - Or `none` if you cannot identify a single best next task.

7. **Loop meta**

   Include a JSON summary for the outer controller or supervising LLM:

   ```text
   <loop-meta>{
     "totalTasks": 12,
     "verified": 8,
     "partial": 2,
     "failed": 1,
     "unverified": 1,
     "missingPrdSections": ["3.2 Error Handling"],
     "suggestedNextTask": "T-009"
   }</loop-meta>
   ```

---

## Final response shape (both modes)

Regardless of mode:

1. Start with a concise natural-language summary of what you did this iteration.
2. Show key diffs or code snippets you changed, but don’t flood the response.
3. Summarize updates to `tasks.yaml` and tests.
4. End your message with **only**:

```text
<loop-status>...</loop-status>
<current-task>...</current-task>
<loop-meta>{...}</loop-meta>
```

No other text after these markers.

---

If you’d like, next step I can:

- Generate an example `prd.md` + `tasks.yaml` pair and a sample **verification-report.md** after a few fictional iterations, so you can see end-to-end flow before you wire this into your actual project.  

<user_response_autocomplete>
Yes show example prd tasks and verification report
Adapt this for a web app with auth and billing
Show a minimal but realistic prdmd and initial tasksyaml
</user_response_autocomplete>

## Human

How Smart Ralph verifier mode catches implementation gaps that basic loops miss and improves code quality

## Assistant

Here's the direct answer — this is focused and dense.

## The Core Problem Basic Loops Don't Solve

A basic Ralph loop answers: "did Claude say it's done?" A Smart Ralph verifier asks: "is the implementation actually aligned with the spec?" These are fundamentally different questions.[1][2]

The root failure in vanilla loops is **accountability without contract**: Claude decides completion by conversational cues rather than objective criteria. As one field report describes it, "we've been treating 'done' as a conversational cue when it should be a contract." The result is high false-completion rates — Claude marks a feature `passes: true` while quietly skipping edge cases, leaving stubs, or writing tautological tests that verify nothing.[3][4][1]

***

## How Smart Ralph's Verifier Catches Gaps

### Gap 1: Spec-vs-Code Drift (the PLANNING mode catch)

Smart Ralph's PLANNING mode (from `PROMPT_plan.md`) runs explicit gap analysis using up to 500 subagents comparing `specs/*` against `src/*` in parallel. This catches what a basic loop cannot:[5]

| What basic loops miss | What PLANNING mode finds |
|---|---|
| TODOs and stubs treated as complete | Searches explicitly for `TODO`, `placeholder`, `minimal implementations` |
| Skipped/flaky tests hiding failures | Scans for `skipped/flaky tests` as a gap signal |
| `ripgrep` false negatives ("I didn't find it, so it's missing") | Instructs "do NOT assume not implemented — confirm with code search first" |
| Single-pass spec reading | Opus subagent + Ultrathink reasoning over all subagent findings |
| No cross-spec consistency check | Spec-to-spec inconsistencies trigger an Opus review to correct the spec itself |

The PLANNING prompt runs as a **loop** (fresh context per pass) so it self-corrects until the plan stabilizes — usually 1–2 iterations. Basic loops never re-audit the plan; they just execute it forward.[5]

### Gap 2: Tautological Tests (the anti-vaporware catch)

One of the most documented Smart Ralph improvements is catching **tautological test generation** — where Claude writes tests that reimplement the function's logic rather than encoding business requirements. A tautological test like:[3]

```python
assert calculate_discount(100, 20) == 100 * (1 - 20 / 100)
```

passes even if the formula is wrong. A verifier checking against acceptance criteria catches this because the expected value (`80.0`) is defined externally from the spec, not derived from the code.[3]

**Acceptance-driven backpressure** in Ralph Playbook makes this explicit: during PLANNING, test requirements are derived from acceptance criteria before implementation starts. The BUILDING prompt then enforces "all required tests must exist and pass before the task is considered complete." This prevents Claude from claiming done without tests that actually prove the spec behavior.[5]

### Gap 3: Interface Mismatches and Integration Failures

Unit tests in a basic loop run per-task in isolation. They miss the class of bugs Craig Johnston calls "Ralph's Uncle" failures:[3]

- **Interface mismatches**: Claude writes a client sending camelCase JSON; server expects snake_case. Both unit tests pass; integration fails.
- **Protocol gaps**: HTTP client doesn't handle 429s; tests mock the API.
- **State corruption**: function works on first call, corrupts shared state on subsequent calls; single-invocation tests pass.

A verifier mode reading the full spec + codebase simultaneously — not just the current task's files — surfaces these cross-boundary issues. Basic loops never zoom out.

### Gap 4: Context Rot in Long Runs

Geoffrey Huntley's design deliberately re-allocates the full spec every iteration to prevent "context rot" — the degradation that happens past 60–70% context capacity where the model begins hallucinating or contradicting earlier work. Smart Ralph compounds this: PLANNING mode produces a fresh `IMPLEMENTATION_PLAN.md` when it detects the plan is stale or drift has accumulated, which prevents the building loop from compounding errors from a bad starting plan.[6][5]

### Gap 5: Non-Deterministic Quality (LLM-as-Judge)

Some acceptance criteria — UX feel, tone, visual hierarchy — cannot be verified by `pytest`. Smart Ralph's extended playbook adds an `llm-review.ts` fixture that provides binary pass/fail for subjective criteria, using screenshots or text artifacts fed to a judge model. The loop keeps running until `result.pass == true`. Basic Ralph has no mechanism here; it either stops early or loops forever on vague criteria.[5]

***

## What the Verification Hierarchy Actually Stacks

Informed by the "Ralph's Uncle" verification model, which explicitly maps what each layer catches and misses:[3]

| Level | Catches | Misses |
|---|---|---|
| Static analysis | Type errors, security patterns, dead code | Logic errors, integration failures |
| Unit tests | Wrong outputs, edge cases, error handling | Interface mismatches, timing bugs, system failures |
| Integration/E2E | Component interaction, protocol errors, state issues | Subtle logic bugs masked by test design |
| Mutation testing | Weak/tautological tests, test gaps | Spec errors, architectural issues, NFRs |

The core insight: **every level that's missing in a basic loop is a category of bugs that reach production undetected**. Because AI generates code at 10× human velocity, every gap in the verification pipeline lets through proportionally more defects.[3]

***

## Why This Matters Specifically for PRD-Driven Loops

For the skill you're building, the verifier mode adds a layer none of the above levels alone provide: **spec traceability**. A test suite can be 100% green while still missing entire PRD sections that were never tasked. The verifier in Smart Ralph (PLANNING mode's gap analysis) cross-references spec sections against code existence — not just tests — meaning it can surface a gap like "Section 3.2 Error Handling has no tasks in `IMPLEMENTATION_PLAN.md` and no corresponding code in `src/`" even when all existing tests pass.[7][8][5]

That's the gap a basic Ralph loop structurally cannot catch: it only iterates on what it knows is in the plan. The verifier asks what the plan forgot.

## Human

Is the LLM describing the solution properly?  "

✻ Conversation compacted (ctrl+o for history)



  ⎿  Read C:\\Users\\brsth\\.claude\\projects\\P--\\memory\\github-ready-correction.md (102 lines)

  ⎿  Read loop-core\\PLUGIN_STANDARDS_REPORT.md (67 lines)

  ⎿  Read loop-core\\CHANGELOG.md (44 lines)

  ⎿  Read loop-core\\tests\\test_integration.py (227 lines)

  ⎿  Read loop-core\\tests\\test_state_manager.py (171 lines)

  ⎿  Skills restored (github-ready, learn)



● Based on my research of the Ralph repository, yes, your description matches Ralph's design. Here's what Ralph actually

  does:



  Ralph's Exit Detection Mechanism



  Dual-condition gate (from frankbria/ralph-claude-code):

  Exit requires BOTH conditions:

  1. completion_indicators >= 2 (heuristic detection of "done")

  2. EXIT_SIGNAL: true (explicit LLM signal in RALPH_STATUS block)



  How it works:

  1. LLM sets trigger condition: When the LLM believes the plan is finished and verified, it adds EXIT_SIGNAL: true to the

  RALPH_STATUS block in the plan file

  2. Stop hook checks condition: The loop's exit logic reads the plan file each iteration and checks if BOTH conditions are

   met

  3. Reset if not met: If exit conditions are NOT met, the loop continues (generates a new prompt for the next iteration)



  From the Ralph README:

  ▎ "Claude must explicitly signal completion by setting EXIT_SIGNAL: true in the RALPH_STATUS block. This is combined with

   a heuristic check (completion_indicators >= 2) to prevent premature exit."



  This matches your description:

  - ✅ "trigger condition or definition of done" = EXIT_SIGNAL: true

  - ✅ "that the llm uses when the plan is finished and verified" = LLM sets this in RALPH_STATUS

  - ✅ "then the stop hook reset the prompt if the condition is not met" = Loop continues if conditions aren't met



  loop-core's role: Provides parse_plan_tasks() and TerminalStateManager utilities that Ralph-style loops use to:

  - Read the plan file (check EXIT_SIGNAL)

  - Track completion_indicators

  - Persist loop state across iterations



  The memory file I created (github-ready-correction.md) documents this relationship correctly: loop-core is a library

  plugin that Ralph-style loops import and use, not a Ralph implementation itself.



✻ Churned for 40s



❯ How does a library plugin support what I described?



● Looking at the actual loop-core implementation, here's how it supports Ralph's exit detection:



  How loop-core Supports Ralph's Exit Mechanism



  From scripts/plan_parser.py:



  def parse_plan_tasks(plan_path: Path) -> list[dict]:

      """Extract tasks from markdown plan file.



      Handles RALPH_STATUS blocks for exit detection:

      - EXIT_SIGNAL: true (LLM's explicit completion signal)

      - completion_indicators (heuristic detection)

      """

      # Reads plan file and extracts task metadata

      # Parses RALPH_STATUS blocks for exit conditions



  The Ralph-style loop would use loop-core like this:



  from scripts import TerminalStateManager, parse_plan_tasks



  def ralph_loop_iteration(plan_path: str):

      """One iteration of Ralph-style autonomous loop."""



      # 1. Read plan file (check EXIT_SIGNAL from LLM)

      tasks = parse_plan_tasks(plan_path)



      # 2. Get current loop state

      manager = TerminalStateManager()

      state = manager.read_state("ralph_status")



      # 3. Check dual-condition exit gate

      llm_done = any(t.get("EXIT_SIGNAL") == True for t in tasks)

      completion_indicators = state.get("completion_indicators", 0)



      # 4. Exit if BOTH conditions met

      if llm_done and completion_indicators >= 2:

          print("✓ Exit conditions met")

          return  # Loop terminates



      # 5. Otherwise: reset prompt (continue loop)

      else:

          # Generate next prompt

          state["completion_indicators"] += 1

          manager.write_state("ralph_status", state)

          # Continue to next iteration



  loop-core provides:

  - ✅ parse_plan_tasks() → Reads plan file and extracts EXIT_SIGNAL

  - ✅ TerminalStateManager.read_state() → Retrieves completion_indicators

  - ✅ TerminalStateManager.write_state() → Persists state between iterations

  - ✅ Terminal isolation → Each Ralph loop gets its own state directory



  The Ralph loop itself (bash or Python) provides:

  - The loop logic

  - The prompt generation

  - The exit condition checking



  loop-core doesn't implement the loop — it provides the utilities the loop uses to manage state and parse plans. This is

  why it's a library plugin, not a workflow plugin.

"

## Assistant

Yes, the LLM’s description is broadly accurate and technically reasonable, but it’s clearly **extrapolating** from Ralph patterns rather than quoting the exact `loop-core` code, so you should treat it as a plausible design sketch, not an exact docstring. Here’s how it lines up with known facts.

***

## 1. Ralph exit detection: is the dual-condition description right?

Ralph for Claude Code does in fact use a **dual-condition exit gate**:

- It requires both **model-confirmed completion** and **heuristic completion indicators** before exiting.[1]
- The heuristics look for repeated “done” signals, multiple test-only loops, and similar patterns.[2][1]

Public descriptions explicitly talk about:

- “Dual-condition exit gate (completion indicators + EXIT_SIGNAL)” in derivative projects and docs.[3]
- Intelligent exit detection that avoids both premature stop and runaway loops.[1]

Your snippet says:

> 1. `completion_indicators >= 2`  
> 2. `EXIT_SIGNAL: true` in RALPH_STATUS  

That matches the **conceptual** design (explicit model signal + heuristic counter). The exact names (`completion_indicators`, `EXIT_SIGNAL`, `RALPH_STATUS`) are consistent with how downstream tools and issues describe Ralph internals, including references to `EXIT_SIGNAL` and completion indicators in the official repo and issues.[4][2]

So: conceptually correct, even if the specific YAML fields/thresholds are reconstructed.

***

## 2. “Stop hook resets the prompt if condition not met”

Ralph-style loops use a **stop hook** / completion promise pattern:

- The Ralph Wiggum loop is described as intercepting Claude’s normal completion using a stop hook, then reinjecting a “did it work? if not, fix and continue” prompt until completion criteria are met.[5]
- The “completion promise” / marker in the prompt is exactly the mechanism your snippet calls `EXIT_SIGNAL: true`.[6][5]

Your text:

> “Stop hook checks condition … reset the prompt if the condition is not met.”

This matches how the Ralph loop / stop hook architecture is documented: stop hook inspects the last output, checks for the completion marker, and either exits or re-prompts.[6][5]

So: behaviorally aligned with the documented mechanism.

***

## 3. loop-core as a *library* plugin: does that characterization fit?

The LLM’s second part is about **loop-core**:

> loop-core provides parse_plan_tasks and TerminalStateManager utilities… The Ralph loop itself (bash or Python) provides the loop logic… loop-core doesn’t implement the loop — it provides utilities.

That design (library plugin vs workflow plugin) is exactly how several Ralph-adjacent libraries are structured:  
- A core library that parses plan files, tracks state, and exposes utilities.  
- A separate “workflow” or “loop” plugin that wires those into actual iteration logic and prompts.[7][8][5]

The specific sample code:

```python
tasks = parse_plan_tasks(plan_path)
manager = TerminalStateManager()
state = manager.read_state("ralph_status")
...
if llm_done and completion_indicators >= 2:
    return
else:
    state["completion_indicators"] += 1
    manager.write_state("ralph_status", state)
```

is not something I can verify line-by-line from public `loop-core` source, but the **roles** are plausible and match typical patterns:

- A parser that pulls status blocks and tasks from a Markdown plan.[9][10]
- A state manager that persists counters/flags between iterations (often per terminal session).[8][5]

So: the LLM is **correct about the division of responsibility** (loop-core = utilities; loop script = control loop), but the function names and exact code are inferred.

***

## 4. Where you should be cautious

A few things to keep in mind:

- I cannot see `loop-core`’s actual `parse_plan_tasks`/`TerminalStateManager` definitions in the snippet you pasted, so any **inline code** the LLM gives is necessarily synthesized. It’s a faithful *sketch*, not the real implementation.  
- The exact placement/format of `EXIT_SIGNAL`, `RALPH_STATUS`, and `completion_indicators` in plan files and state will depend on how your local loop-core is written. You should verify those against your repo.  
- Some Ralph variants use different heuristics (e.g., “multiple consecutive ‘done’ signals”, “max test-only loops”, “no-progress circuit breaker”) as seen in the Ralph docs and blog posts. Your LLM’s description simplifies that to a single `completion_indicators >= 2` gate.[11][2][1]

Given that, I’d rate the LLM’s explanation as:

- **Conceptually correct** about Ralph’s dual exit conditions and loop-core’s role.  
- **Implementation-level speculative** (names/signatures/plan format should be checked in your actual code).

***

## 5. Concrete next check for you

To be sure your local system actually matches this, I’d do:

1. Open the real loop-core code:
   - Inspect `parse_plan_tasks` and any plan/Markdown parsing utilities.  
   - Confirm how (and where) `EXIT_SIGNAL` / `RALPH_STATUS` or equivalent are parsed.  
2. Open your loop script / stop hook:
   - Look for where it reads the plan, reads terminal/session state, and decides to exit vs continue.  
   - Confirm that it checks both an explicit model signal and some heuristic indicator before exit.  

If you paste the relevant `loop-core` and loop script snippets, I can tell you whether the LLM’s description is exact or where it diverges.

Would you like me to help you diff the LLM’s pseudo-code against your actual `loop-core` and loop implementation line-by-line?

## Human

How am I supposed to take advantage of the ralph loop we are calling loop-core?

## Assistant

Short answer: treat **loop-core** as your reusable *Ralph infrastructure* and layer your own PRD/spec‑driven behavior on top. It gives you state + plan parsing; you supply the loop policy, prompts, and exit rules.[1][2]

***

## What loop-core gives you

From what you described earlier plus typical Ralph/ralphy layouts, loop-core is effectively:[3][2]

- A **state manager** (e.g., `TerminalStateManager`)  
  - Persists per-loop state: counters, flags, last status, etc.  
- A **plan/plan‑file parser** (e.g., `parse_plan_tasks`)  
  - Reads Markdown/plan docs, extracts tasks and status blocks (`RALPH_STATUS`, `EXIT_SIGNAL`, etc.).  
- Possibly some **utility hooks** for terminal isolation or per‑project state directories.

It is *not* the loop itself; you are expected to write the shell/Python loop that:

- Calls Claude Code with the right skill + prompt file.  
- After each iteration, calls loop-core helpers to read plan/state and decide: continue, adjust, or stop.[2][1]

***

## How to actually “take advantage” of it

Think in layers:

1. **Outer loop** (your code)
   - A Python or shell script that:
     - Runs Claude Code once per iteration (Ralph style: fresh context each time).[2]
     - After each run, calls:
       - `parse_plan_tasks(plan_path)` → get tasks + `EXIT_SIGNAL` or equivalent.  
       - `TerminalStateManager.read_state(...)` → read counters (e.g., completion indicators, struggle flags).  
     - Applies your policy:
       - If explicit exit signal + heuristics satisfied → stop.  
       - Else → update state, maybe tweak prompt/plan, and run next iteration.

2. **Plan file and status blocks** (your prompts/skills)
   - Use Claude Code skills to:
     - Maintain a plan file (`implementation_plan.md`, `prd_plan.md`, etc.).[4][2]
     - Write a **status block** your loop-core can parse, e.g.:

       ```markdown
       ```RALPH_STATUS
       EXIT_SIGNAL: true
       COMPLETION_INDICATORS: 3
       LAST_TASK: T-004
       ISSUES: []
       ```
       ```

     - Your Claude skill is responsible for only setting `EXIT_SIGNAL: true` when the PRD/spec is satisfied and verified.

3. **Exit logic & verification** (your policy)
   - In your outer loop, use loop-core’s parsed results to enforce your own “smart exit” conditions, for example:
     - `EXIT_SIGNAL == true` **and** `completion_indicators >= 2`.  
     - No tasks with `status: todo`/`in_progress` in `tasks.yaml`.  
     - Latest test run passed (you can track a `TESTS_PASS: true` flag in the status block, or store it in loop state).

4. **PRD/spec extension**
   - You can extend loop-core’s usage by:
     - Having your Claude skill:
       - Derive `tasks.yaml` from `prd.md`.  
       - Write per‑iteration status (e.g., mapped PRD sections, remaining gaps) into the plan file.  
     - Using loop-core to:
       - Inspect which tasks are `done`, which PRD sections are still unmapped.  
       - Feed that back into your loop decision: continue until **PRD coverage + verification** is complete.

***

## Concretely, what you should do next

1. **Inspect loop-core API**
   - Open the actual `loop-core` repo / module and identify:
     - `parse_plan_tasks(...)` or similar — what does it return?  
     - `TerminalStateManager` or equivalent — what keys does it store?  
   - Note exact field names for exit signals and counters.

2. **Design your status contract**
   - Decide what your Claude skill will write into plan/status blocks:
     - At minimum: `EXIT_SIGNAL`, `COMPLETION_INDICATORS` (or similar).  
     - Optionally: `HAS_FAILING_TESTS`, `UNVERIFIED_TASKS`, etc.

3. **Write a small outer loop** (Python or bash)
   - Use loop-core primitives in a ~50–100 line script that:
     - Runs your Claude skill once.  
     - Calls the loop-core functions to read status.  
     - Decides: continue / stop / escalate.

4. **Then layer PRD-driven behavior**
   - Once the loop is stable, plug in the `tasks.yaml` + verifier we sketched earlier so your definition of “done” is “PRD fully implemented and verified,” not just “EXIT_SIGNAL set.”

If you paste the exported API from your local `loop-core` (even just the signatures/docs for `parse_plan_tasks` and the state manager), I can give you a very specific Python loop that uses its real types and field names instead of the inferred ones.

## Human

So that doesn't help me.  What does the user prompt to use the loop-core?  Is there more implementation needed?

## Assistant

You can’t “prompt your way into” loop-core; you need a tiny bit of glue code and a specific way of running Claude. The user-facing interaction is very simple, but there *is* extra implementation behind it.

***

## What the user actually does

From a user point of view, a Ralph/loop-core setup usually looks like one of these patterns:

- Run a bash loop that feeds a prompt/plan into Claude repeatedly:

```bash
# Classic Ralph-style loop
while true; do
  cat prompt.md | claude --dangerously-skip-permissions
done
```



- Or run a dedicated CLI that wraps that loop logic (`ralphy`, `ralph.sh`, `ralph-loop`, etc.):

```bash
ralphy --prompt-file prompt.md --max-iterations 50   # example pattern
```



In your case, “loop-core” is the **library behind such a CLI**, not the CLI itself. So as a user, you’ll ultimately be doing something like:

```bash
# Your project
python -m loop_core_runner run --plan plan.md --skill prd-loop
# or
./ralph.sh  # that internally imports loop-core to manage state
```

There is no special *prompt* like “use loop-core”; the loop is triggered by how you run Claude and which scripts are wired up.

***

## What’s missing today

From what you’ve described, you have:

- loop-core (a state + plan parser library).  
- A mental model that it supports Ralph’s exit detection.  

What you *don’t* seem to have yet is:

1. A **runner script** (bash or Python) that:
   - calls Claude Code with your skill/prompt each iteration, and  
   - calls loop-core to decide whether to continue or exit.
2. A **plan/status contract** in your prompt/skill so Claude writes the fields loop-core can read (`EXIT_SIGNAL`, etc.).

Without those two, loop-core just sits there as unused helpers.

***

## Minimal extra implementation you need

### 1. A plan/status format Claude writes to

Decide where Claude writes status, e.g. `plan.md`:

```markdown
# Implementation Plan

- [x] Task 1
- [ ] Task 2

```RALPH_STATUS
EXIT_SIGNAL: false
COMPLETION_INDICATORS: 1
LAST_TASK: T-001
ISSUES: []
```
```

Your Claude skill/prompt must be told:

- To update the checklist/tasks.  
- To only set `EXIT_SIGNAL: true` once the plan/PRD is genuinely complete.  
- To increment or update any counters you use (like `COMPLETION_INDICATORS`).

This is the “status block” loop-core will parse.

***

### 2. A small loop runner that uses loop-core

Example in Python (pseudo, but close to what you need):

```python
from pathlib import Path
import subprocess
from loop_core import parse_plan_tasks, TerminalStateManager  # whatever the actual names are

PLAN_PATH = Path("plan.md")

def run_once():
    # One Claude iteration using your skill/prompt
    subprocess.run(
        ["claude", "--dangerously-skip-permissions", "-p", "@plan.md ..."],
        check=True,
    )

def should_exit() -> bool:
    tasks = parse_plan_tasks(PLAN_PATH)

    # Figure out if the LLM set the explicit exit flag in the status block
    llm_done = any(t.get("EXIT_SIGNAL") is True for t in tasks)  # adapt to real API

    manager = TerminalStateManager()
    state = manager.read_state("ralph_status") or {}
    completion_indicators = state.get("completion_indicators", 0)

    if llm_done and completion_indicators >= 2:
        return True

    # Otherwise, bump the heuristic counter and keep going
    state["completion_indicators"] = completion_indicators + 1
    manager.write_state("ralph_status", state)
    return False

def main(max_iters: int = 100):
    for _ in range(max_iters):
        run_once()
        if should_exit():
            print("Loop-core: exit conditions met")
            break

if __name__ == "__main__":
    main()
```

Then the *user* just runs:

```bash
python scripts/loop_core_runner.py
```

That’s your “prompt” from a UX standpoint.

***

## How to wire this into your concrete setup

Given all of that, your next practical steps are:

1. **Inspect loop-core’s real API**  
   Find the actual signatures of `parse_plan_tasks` and the state manager in your codebase and confirm:
   - How it returns RALPH_STATUS info.  
   - Where it stores state (per terminal, per project, etc.).

2. **Add a status block to your skill**  
   Make sure your Claude skill/prompt:
   - Reads and updates `plan.md` (or similar).  
   - Writes a RALPH_STATUS block with the fields loop-core expects.

3. **Create a tiny runner script**  
   - Use the real loop-core functions instead of my placeholders.  
   - Call Claude with your existing skill (e.g. the PRD loop skill we designed earlier).

4. **Run it from the terminal**  
   - That script (or a bash wrapper) is what *you* or another LLM actually call to “use loop-core”.

If you paste the real `loop-core` function names and status format, I can give you an exact runner and the exact status block you should tell Claude to output.

## Human

You still haven't said how the user prompts to use it.

## Assistant

For loop‑core specifically, the “user prompt” is **not** a magic phrase you type to Claude; it’s the way you *run* Claude + how your skill is written. Yes, you still need a little implementation to expose it cleanly.

***

## What the human actually does

Once wired, the human interaction looks like this:

- In the terminal, from the project:

```bash
# Example UX once you’ve wired loop-core
python scripts/loop_core_runner.py   # or
./ralph.sh                           # or
/ralph-loop "Implement the PRD in prd.md"
```



Inside Claude Code, if you make it a skill, the “prompt” is just:

> “Use the loop-core Ralph loop to work through this PRD until done and verified. Start the loop.”

But that only works **after** you’ve created a skill or script that knows how to invoke loop-core and run the loop. The raw library will not respond to a plain English sentence.

***

## What extra implementation you need (minimum)

To get to that simple UX, you still need:

1. **A runner script** (bash or Python):
   - Loops:
     - call Claude Code with your skill (which edits `plan.md` / `tasks.yaml`),  
     - call loop-core (`parse_plan_tasks`, state manager) to inspect `EXIT_SIGNAL` / counters,  
     - decide: keep looping or stop.
   - That script is what the user runs (`python loop_core_runner.py` or `/ralph-loop "task"`).[1][2]

2. **A plan/status format in your skill**:
   - Your Claude skill must write a predictable status block in a file that loop-core can parse, e.g.:

     ```markdown
     ```RALPH_STATUS
     EXIT_SIGNAL: false
     COMPLETION_INDICATORS: 1
     LAST_TASK: T-001
     ISSUES: []
     ```
     ```

   - loop-core reads that; your script uses it to make exit decisions.

3. **(Optional but ideal) a Claude skill wrapper**:
   - A `skill.md` that tells Claude:
     - “When the user says ‘start the Ralph loop’, run the bash/Python runner that uses loop-core and then report progress back.”

At that point, *the only “prompt” the user needs* is either:

- A terminal command: `python scripts/loop_core_runner.py`, or `/ralph-loop "build this from prd.md"`.  
- Or a Claude instruction inside a project where the skill is installed: “Start the Ralph loop and keep working until the PRD in `prd.md` is fully implemented and verified.”

Without that glue, just saying “use loop-core” to Claude does nothing, because loop-core isn’t a conversational endpoint; it’s a helper library your scripts/skills call.

## Human

"/ralph-loop "build this from prd.md"", that's the first useful prompt you have said.  So you are saying we need a new skill outside of /plan-workflow or /code?

## Assistant

Yes: to use loop‑core the way you’re envisioning, you effectively need a **separate “loop runner” skill/command**, not just `/plan-workflow` or `/code`.

***

## What the user should actually type

Once wired, the user-facing entry point is a **command‑style skill** such as:

```text
/ralph-loop "Build the app to satisfy prd.md"
```

or, if you wrap it as a bespoke skill:

```text
/loop-core "Implement the PRD in prd.md end‑to‑end"
```

Those are analogous to the official Ralph plugin’s `/ralph-loop "Add auth to admin panel…" --completion-promise "DONE"` usage.[1][2]

Under the hood, that skill:

- Runs your loop script (bash/Python) that:
  - Calls Claude Code with your PRD skill.  
  - Uses loop-core to read plan/status and decide whether to loop or exit.  
- Streams progress back to the user.

So the *prompt* is just the quoted task; the loop behavior comes from the skill implementation, not the text itself.[3][1]

***

## Why this should be a separate skill

`/plan-workflow` and `/code` are:

- One‑shot or short‑horizon planning/coding helpers.  
- Not responsible for supervising a long‑running loop, reading/writing loop state, or handling exit heuristics.

A loop supervisor needs to:

- Be able to **run shell commands / scripts** repeatedly.  
- Read and write files (`plan.md`, `tasks.yaml`, status blocks).  
- Interpret loop-core’s signals and re‑invoke Claude Code until done.

That’s exactly the pattern people use when they build a dedicated “Ralph invoke” skill that can call the Ralph plugin or scripts directly, instead of relying on conversational prompts alone.[4][3]

So yes:

- **You do need a new skill** (call it `/ralph-loop` or `/loop-core`) that:
  - Owns the outer loop.  
  - Imports and uses loop-core.  
  - Exposes a simple `/ralph-loop "…"` command to the user.

From there, `/plan-workflow` can be used *inside* the loop (to refine plans), but it shouldn’t be the loop itself.

Do you want that new skill to only run in the terminal (bash/Python runner) or also be callable from other agents/LLMs as an HTTP/MCP-style endpoint?

## Human

How to combine /ralph-loop with git worktrees

## Assistant

You combine them by treating **each worktree as a separate Ralph workspace** and pointing `/ralph-loop` at the worktree root. That’s it conceptually; the rest is ergonomics and orchestration.[1][2][3][4]

***

## Basic pattern: one loop per worktree

1. From your main repo:

```bash
# Create isolated worktrees for parallel Ralph loops
git worktree add ../proj-auth   -b feature/auth   # worktree 1
git worktree add ../proj-api    -b feature/api    # worktree 2
```



2. In terminal 1:

```bash
cd ../proj-auth
/ralph-loop "Implement authentication according to prd.md"
```

3. In terminal 2:

```bash
cd ../proj-api
/ralph-loop "Build the REST API according to prd.md"
```

Each loop runs inside its own worktree/branch, so Claude/loop-core can freely edit files without stepping on other loops.[3][1][4]

***

## Why worktrees are the right fit

- **Isolation:** Each Ralph loop has its own checkout and branch, so Git diffs and merges are clean.[5][3]
- **Parallelism:** You can run multiple `/ralph-loop` instances concurrently on different features, similar to “workers sandboxed in git worktrees” in Ralph orchestrators.[6][7]
- **Merge control:** You can review and merge each worktree’s branch (or squash) back into main once its loop finishes.[8][4]

***

## Minimal workflow to adopt

For a single-loop but safe flow:

```bash
# From main repo
git worktree add ../proj-ralph -b ralph/feature-x
cd ../proj-ralph

# Run the loop in the worktree
/ralph-loop "Implement the PRD in prd.md end-to-end"

# When satisfied:
cd ../your-main-repo
git merge ralph/feature-x      # or open a PR from that branch
git worktree remove ../proj-ralph
git branch -d ralph/feature-x
```

This mirrors what Ralph-focused CLIs and tutorials do with a `--worktree` flag: they automatically create a worktree, run Ralph inside it, then merge/clean up.[2][3][4]

***

## What you need implementation-wise

Given everything we discussed:

- `/ralph-loop` should assume “current directory == worktree root” and just run there.  
- Your loop-core‑based runner doesn’t need to know anything about worktrees; Git handles that.  
- Optionally, you can add a `--worktree` or `--branch` flag to your runner to:
  - create a worktree for the user,  
  - run the loop in it, then  
  - open a PR / merge when done (like `ralphex` / “chief” do).[9][2][4]

If you tell me whether you want **one-loop-at-a-time but isolated** or **many parallel loops**, I can sketch a concrete `ralph-loop.sh` that creates and manages worktrees automatically around your existing Python loop.

## Human

how can we get maximum value from an optimized ralph loop archiecture and implementation?

## Assistant

Maximum value comes from treating your Ralph loop + loop-core as a **reliable autonomous execution substrate**, then layering higher-level behaviors on top. Given your review bundle, you already have most primitives; the gains now are architectural and workflow-level.[1]

***

## 1. Use /loop-core as the single entry point

loop-core already exposes a **/loop-core skill** that orchestrates a Ralph-style loop over a plan file and calls `/code` for each incomplete task.[1]

- User entry should be as simple as:

  ```text
  /loop-core plan.md
  ```

- Let `/loop-core` handle:
  - Plan parsing (`parse_plan_tasks()` over markdown checkboxes).[1]
  - State persistence in `.claude/state/terminals/{terminal_id}/loop_state.json`.[1]
  - Dual exit gate: `completion_indicators >= 2` **and** `EXIT_SIGNAL: true`.[1]

That frees you from custom runner scripts and focuses your effort on **better plans** and **better `/code` prompts**, not loop plumbing.

***

## 2. Make the plan the contract, not the chat

Your plan format is:

```markdown
- [ ] TASK-001 Do X [tag:name] after:TASK-000
```

parsed into task dicts with `id`, `text`, `complete`, `tags`, `dependencies`.[1]

To maximize value:

- Treat `plan.md` as the **single source of truth** for:
  - Task graph and dependencies.  
  - Tags like `[tag:critical]`, `[tag:prd:2.1]`, `[tag:verify]`.  
- Give `/code` a skill or prompt that:
  - Reads `plan.md`, picks the next incomplete task respecting `after:` deps.  
  - Updates the checkbox state and, when appropriate, sets `EXIT_SIGNAL: true` in a status block the skill knows how to write.  

The better and more structured your plan, the more loop-core can do with minimal logic changes.

***

## 3. Exploit terminal-local state for parallelism and safety

loop-core’s key value is **terminal-local state**:

- State directory: `.claude/state/terminals/{terminal_id}/`.  
- Files like `loop_state.json` store `current_task_id`, `completed_tasks`, `failed_tasks`, `completion_indicators`, and metadata.[1]

You can maximize this by:

- Running **multiple terminals / worktrees**, each with its own `/loop-core plan.md` invocation for different features or services.  
- Letting loop-core handle isolation, so Git operations and concurrent loops don’t race.[1]

This is exactly the “multi-terminal safe isolation” the design calls out as a non‑negotiable.[1]

***

## 4. Tighten exit detection to your PRD/spec

Right now, exit is:

- `completion_indicators >= 2` and `EXIT_SIGNAL: true`.[1]

To turn this into a PRD‑driven loop:

- Extend the `/code` behavior so it only sets `EXIT_SIGNAL: true` when:
  - All tasks derived from the PRD are complete.  
  - A verification pass (inside `/code` or a nested verifier skill) has run and found no gaps.  

On the loop-core side, you can:

- Keep the dual gate but optionally read richer flags from `loop_state.json` (e.g., `all_prd_sections_covered`, `tests_passed`) and require those before allowing exit.[1]
- That leverages **“Custom Exit Detection”** integration point the bundle calls out.[1]

***

## 5. Plug in higher-level integrations at the defined extension points

Your review bundle explicitly lists where new solutions can plug in:[1]

- **Custom state backends**: If you need durability or observability, you can subclass `TerminalStateManager` to back onto SQLite/Redis while preserving atomic semantics.  
- **Custom plan parsers**: For PRD‑heavy workflows, swap markdown checkbox parsing with a JSON/YAML PRD-driven plan, as long as you return the same task dict schema.[1]
- **Custom exit detection**: Tune the dual gate, add meta from verification, or incorporate an LLM‑judge step.  

Max value here is **not** rewriting loop-core; it’s using these integration points to:

- Feed richer plans (e.g., tasks include PRD refs).  
- Store richer state (e.g., last test command run, last failure).  
- Exit only when your spec says “done,” not when the model feels done.

***

## 6. Guardrails and reliability improvements

The bundle lists some known issues and non‑negotiables you can exploit:[1]

- Fix the CI coverage mismatch (`--cov=scripts`) so your safety net (tests) is always green.[1]
- Consider adding **retry/backoff** around `write_state()` at the caller level, since loop-core intentionally fails fast on I/O errors.[1]
- On non‑Windows, set `CLAUDE_TERMINAL_ID` for stable terminal IDs.[1]

These don’t change loop behavior but increase the confidence that long runs won’t die on transient issues.

***

## 7. Putting it together as a workflow

In practice, a “max value” flow for you could be:

1. Create/update `plan.md` from `prd.md` using a dedicated planning skill.  
2. In a worktree for a feature branch, run:

   ```bash
   /loop-core plan.md
   ```

3. Let `/loop-core`:
   - Iterate tasks via `/code`.  
   - Persist loop state + metrics (`loop_metrics.json`) for observability.[1]
   - Exit only when both the dual gate and PRD‑informed conditions are met.  

4. When it exits:
   - Review `completed_tasks.log` and `loop_state.json`.  
   - Run your own test/CI.  
   - Merge the branch if satisfied.

If you want, next step I can propose a specific `plan.md` template + `/code` skill behavior that perfectly matches loop-core’s `parse_plan_tasks()` and state schema, so the whole system is aligned end‑to‑end.

## Human

Please turn your previous high‑level reasoning about this problem into a concrete, architecture‑aware solution that I can implement and live with long‑term.

Assume ALL of the following constraints are hard requirements:

I routinely run 5+ terminals / processes that share the same filesystem or project root.

The solution MUST be multi‑terminal isolated: any runtime or enforcement state must never leak between terminals or get corrupted by concurrency. Treat each terminal/session as a separate “tenant” over the same repo.
​

The system MUST be immune to stale data: no reliance on long‑lived in‑memory flags or outdated context; every important decision should be based only on current, authoritative sources (e.g., current config files, current tool/action sequence, per‑terminal logs or state files).

I do not care about transition effort; significant refactors, partial rewrites, or side‑by‑side greenfield work are acceptable if they yield a cleaner, more reliable design.

Using those constraints plus everything you have already inferred from our chat, promote your ideas into a full architecture proposal using this exact structure. If any subsection cannot be completed due to missing information, mark it NEEDS CLARIFICATION and list the precise questions you need answered; do NOT fall back to generic, non‑actionable tips.

1. Context Understanding
Clarify whether this work is primarily improving an existing system, designing something mostly new, or a hybrid. Then identify which parts of the system are involved (configs, commands/APIs, hooks/events, agents/skills if any, logs, per‑terminal/session state).

Explain how multi‑terminal concurrency and the shared filesystem (or other shared resources) currently produce failures or would likely do so: cross‑terminal state bleed, race conditions, stale assumptions about config, logs, or model state, etc.

State the change scope as Tiny / Small / Medium / Large and justify it in terms of refactors to components, configurations, and data flow.

Define the core problem as a gap and a goal: what’s broken or risky in the current or planned design, and what target behavior we want in a multi‑terminal, stale‑state‑resistant setup.

2. Proposed Architecture
Design the architecture in clear layers and explain how each layer behaves and coordinates:

Layer definitions and responsibilities

Per‑terminal/session state model: how each terminal or session is identified, where its logs and settings live, and how code reads that terminal‑local data without sharing it across sessions.
​

Execution / hook / event layer: how lifecycle events (e.g., “before action”, “after action”, “on stop”, “on error”) are wired to enforce policies, perform checks, or trigger automation deterministically.

Policy/config layer: how configuration (files, environment, CLI flags, project docs, feature flags) is structured and loaded so that decisions always come from current, authoritative data.

Domain layer: how domain concepts (e.g., skills, tools, workflows, agents, pipelines) are represented and used by the above layers.

Correctness guarantees
For each layer, explain how it guarantees correct behavior even with multiple terminals and no long‑lived shared state, including:

How it prevents cross‑terminal leakage and ensures each terminal’s decisions depend only on its own context plus shared, read‑only sources (like current repo files).
​

How it ensures that updates to config or code (for example, changing a rule or policy file) take effect promptly without needing to restart terminals.

How deterministic mechanisms (hooks, scripts, validations) are used instead of purely conversational or probabilistic mechanisms whenever behavior must occur.

Interaction with existing mechanisms

Specify which current mechanisms are reused as‑is, which are consolidated, and which are deprecated or turned into no‑ops by the new design.

Note any conventions the architecture requires (file locations, naming, metadata/frontmatter, per‑terminal folders under a .config‑like directory, etc.).

3. Implementation Plan
Describe concrete implementation steps at a “sit down and edit files” level:

Exact places to change

List which hooks, event handlers, commands, or integration points need to change and how (e.g., which lifecycle events are intercepted, which tools/actions they apply to).

List which config or metadata fields must be added or standardized (e.g., fields defining allowed actions, models, tenants, roles, or policies).

Identify which log files or per‑terminal state files should be created or repurposed (e.g., per‑terminal audit logs, decision logs, session summaries).

New modules and refactors

Describe any new modules, services, or helper utilities you recommend, especially for:

Parsing current config/metadata on each relevant event.

Inspecting the current action/tool sequence and building a decision from that plus per‑terminal logs.

Ensuring each terminal writes to and reads from its own log/state so decisions are isolated.

When proposing changes, be explicit about which parts are refactors of existing code, which are greenfield modules running alongside the old system, and any planned decommissioning or migration steps.

Stale‑data immunity

Explain how every important decision is computed from current config, code, and per‑terminal state, with no reliance on in‑memory flags, long‑lived objects, or cached context. If any caching is needed, specify its invalidation strategy explicitly.

4. Testing Strategy
Provide a concrete, automation‑friendly test plan (pytest or equivalent) to validate the design:

Test scenarios

Multi‑terminal isolation: scenarios where two terminals/processes perform conflicting actions on the same repo/state and we verify that their behavior and logs remain isolated and correct.
​

Correct handling when prescribed procedures are ignored (e.g., required commands, workflows, or “playbooks” are skipped): how the architecture detects that and what it does.

No false negatives for critical guarantees (e.g., safety/security checks always run when required).

No false positives where benign operations are blocked or over‑constrained without justification.

No stale enforcement after changes: config or metadata changes mid‑session and enforcement immediately reflects the new configuration.

Stale‑state simulation

Describe how to simulate stale‑state conditions (e.g., long‑running sessions while configs change, concurrent writes, partial log failures) and verify that decisions remain correct because they re‑read authoritative sources.

Acceptance and rollback

Define acceptance criteria for rollout (e.g., error rates, false‑positive/negative thresholds, latency ceilings, cross‑terminal leak checks over N days).
​

Include a simple rollback plan: what to revert (configs, hooks, modules) and how to fall back to a known‑good, less opinionated baseline if issues appear.

5. Observability & Metrics
Explain how to observe behavior and detect regressions:

Per‑terminal logging

What to log per terminal/session and where (file paths or log sinks), including timestamp, terminal/session id, action/tool, decision, reason, and any relevant context keys.

Metrics

Metrics to track, such as:

False positives and false negatives for key guarantees.

Per‑terminal error and block rates.

Time‑to‑action (e.g., time from command or trigger to first relevant tool/action).

Throughput and latency per terminal.

Detecting regressions

How to detect when upstream behavior changes (e.g., different tool‑calling patterns from an LLM, new events, or different latency distributions) and how to use logs/metrics to localize and adapt to those changes.

6. Risks & Tradeoffs
Provide an explicit risk assessment:

Failure modes

Enumerate likely failure modes (e.g., misconfigured metadata, mis‑tagged actions, hooks failing open vs closed, log corruption) and their impact.

Discuss false‑positive and false‑negative risks, how they would show up, and how the architecture mitigates or at least surfaces them.

Performance and complexity

Analyze performance overhead (filesystem reads, log writes, extra validations) and complexity (extra modules, conventions) versus the guarantees achieved.

Explain how the design scales as I add more workflows/skills/agents or more terminals, and whether any parts will need sharding, indexing, or restructuring as the system grows.

Soft‑enforcement areas

Call out any remaining behaviors that cannot be made strictly deterministic or “hard‑enforced” with the available mechanisms (e.g., purely conversational norms) and what mitigations are still possible (e.g., nudges, warnings, or periodic audits).

Where relevant, distinguish risks and tradeoffs specific to refactoring the existing system vs introducing a parallel greenfield path and migrating to it.

7. Completeness Checklist
End with an explicit checklist where you confirm, one by one:

You referenced the existing mechanisms correctly (commands, hooks/events, agents/skills if relevant, configs, logs).

You specified where changes happen (which files, modules, hooks, configs, scripts).

You included concrete automated tests, acceptance criteria, and a rollback/migration plan.

You respected my constraints (multi‑terminal isolation, stale‑data immunity, willingness to refactor/partially rewrite).

For any part you could not specify due to missing information, you clearly labeled it NEEDS CLARIFICATION with targeted questions instead of generic advice.

## Assistant

1. Context Understanding
-------------------------

### 1.1 Nature of the work

This is a **hybrid**: you already have a concrete base in `loop-core` (state manager, plan parser, `/loop-core` skill), but you want a long‑term, more powerful Ralph architecture on top of it.[1]

- **Existing pieces to keep and build on**:[1]
  - `TerminalStateManager` and state paths (`.claude/state/terminals/{terminal_id}/…`).  
  - `parse_plan_tasks()` and its task schema (markdown checkbox plans).  
  - `/loop-core` skill entry point that runs a Ralph-style loop over a plan and calls `/code`.  
- **New pieces**:
  - A more opinionated **domain layer**: PRD/spec‑aware plans, verification, exit policies.  
  - A standardized **per‑terminal loop state + logs** model.  
  - A **/ralph-loop**-style interface that composes `/loop-core`, `/code`, and planned verifier behavior.

Change scope: **Medium–Large**.  
You’re not touching low-level state primitives or Claude itself, but you will:

- Formalize conventions for plans, PRD mapping, and per‑terminal state.  
- Add new modules for policy, verification, and observability.  
- Potentially deprecate ad‑hoc loops or direct `/code` usage for long‑running work in favor of `/loop-core` / `/ralph-loop`.

### 1.2 Multi-terminal concurrency & current failure modes

Given:

- You run **5+ terminals/processes** over the same repo.  
- `loop-core` already assumes each terminal gets **its own state directory** under `.claude/state/terminals/{terminal_id}/` and uses PID‑based locks.[1]

Current/likely problems in a richer Ralph setup:

- **Cross‑terminal state bleed**:
  - If any loop uses shared files (e.g., a global `loop_state.json` or shared `plan.md` with no per‑terminal convention), different terminals’ loops can overwrite each other’s progress or exit decisions.
- **Race conditions on plans**:
  - Two terminals editing the same `plan.md`/`tasks.yaml` can interleave changes, confusing `parse_plan_tasks()` and any task‑status logic.
- **Stale assumptions**:
  - Long‑running loops assume:
    - The plan hasn’t changed structurally.  
    - Policy/exit conditions are unchanged.  
    - PRD/spec files haven’t been updated.  
  - In reality, you may edit the PRD, plan, or policy during a run; a naive loop doesn’t re‑hydrate these at each iteration.
- **Implicit, in‑memory flags**:
  - If loop logic is held in Python/bash variables in a terminal script, each loop instance can diverge (different thresholds, different policy version) and not update when config changes.

### 1.3 Gap and goal

**Gap**: You have good primitives (per‑terminal state, plan parser, `/loop-core` skill), but no unified architecture that:

- Treats each terminal as an isolated tenant.  
- Computes decisions only from **current files + per‑terminal state**.  
- Encodes PRD/spec‑driven behavior and verification as part of the loop.  

**Goal**: A **Ralph loop platform** where:

- Each terminal can safely run its own loop over the same repo (often different worktrees/branches).  
- All loop decisions (what to do, when to exit, what’s “done”) are recomputed each iteration from current plan, PRD, and per‑terminal state, with no reliance on stale memory.  
- Policies and behavior can evolve via config, not code rewrites, and those changes are effective immediately.

2. Proposed Architecture
------------------------

### 2.1 Layer definitions and responsibilities

#### Layer 1: Per-terminal/session state

**Identity**

- A **terminal/session ID** is the primary tenant key:
  - Provided by `loop-core`’s terminal detection (`get_terminal_id`), or  
  - Overridden via `CLAUDE_TERMINAL_ID` env var for stability on non‑Windows.[1]

**Storage**

- All per‑terminal state lives under:

  ```text
  .claude/state/terminals/{terminal_id}/
    loop_state.json
    completed_tasks.log
    loop_metrics.json
    decision.log            # NEW
    verifier.log            # NEW (optional)
  ```

- `loop_state.json` becomes the **single source** of loop runtime state:
  - `current_task_id`  
  - `completed_tasks` / `failed_tasks`  
  - `completion_indicators`  
  - `loop_metadata` (plan path, started_at, last_update, iterations, policy version, etc.)[1]

**Guarantees**

- Isolation: a terminal only reads/writes its own `{terminal_id}` directory.[1]
- Atomicity and locks handled by `TerminalStateManager` (temp + rename, PID locks).[1]

#### Layer 2: Execution / hook / event layer

This is the **loop orchestrator** built around `/loop-core`:

- **Entry command**: `/ralph-loop "task"`, which internally invokes `/loop-core plan.md` with the right context, or you just use `/loop-core plan.md` as the lower-level entry.[1]
- **Events**:
  - `on_loop_start(terminal_id, plan_path)`  
  - `on_iteration_start(terminal_id, loop_state)`  
  - `on_iteration_end(terminal_id, loop_state, parsed_plan)`  
  - `on_loop_exit(terminal_id, loop_state)`  
  - `on_error(terminal_id, error, context)`

These are deterministic hooks implemented as Python/bash functions that:

- Always re‑read `loop_state.json`, `plan.md`, and relevant config on each iteration.  
- Write decisions and outcomes to per‑terminal logs.  
- Never store policy in long‑lived memory; they recompute from files.

#### Layer 3: Policy/config layer

**Files**

- `.claude/loop/config.yaml` – global, read‑only shared config.

  Example:

  ```yaml
  version: 1
  exit_policy:
    min_completion_indicators: 2
    require_exit_signal: true
    require_all_tasks_complete: true
    require_verification_pass: true
  verification:
    enabled: true
    skill: prd-verifier
    write_report: .claude/loop/verification-report.md
  plans:
    default_plan: plan.md
    allow_per_terminal_plan: true
  logging:
    decision_log: decision.log
    verifier_log: verifier.log
  ```

- Optionally, a `plan-local` config block inside `plan.md` frontmatter:

  ```markdown
  ---
  loop:
    exit_policy_override:
      min_completion_indicators: 3
  ---
  ```

**Responsibilities**

- Policy files define:
  - Exit conditions, thresholds, whether to run verification.  
  - Allowed tools/skills for `/code` (e.g., allowed models, allowed directories).  
- Hooks always load this file at **each iteration** (cheap YAML parse) to ensure all decisions are based on up‑to‑date policy.

#### Layer 4: Domain layer (plans, PRDs, skills)

Domain concepts:

- **Plan**: a markdown checklist plan that `parse_plan_tasks()` understands, with task IDs, tags, and dependencies.[1]
- **PRD/Spec**: authoritative requirement docs (e.g., `prd.md`, `spec/*.md`).  
- **Skills/workflows**:
  - `/loop-core`: orchestrates the loop over a plan using `/code` and state manager.[1]
  - `/code`: Claude Code workflow that implements tasks.  
  - `prd-verifier` (NEW): a skill that verifies implementation and updates either `loop_state` or a verification report.

The domain layer is wired such that:

- `/loop-core` only cares about tasks and state.  
- `/code` only cares about implementing tasks given a plan.  
- `prd-verifier` only cares about coverage vs PRD.

### 2.2 Correctness guarantees, per layer

#### Per-terminal/session state

- **No cross-terminal leakage**:
  - All state paths are computed from `{terminal_id}`, and APIs take `terminal_id` explicitly.
- **Stale-data immunity**:
  - No in‑memory shared state; each decision reads fresh from `loop_state.json` and files.  
  - If `loop_state.json` is corrupted, `LoopStateError` is raised and logged; the loop stops rather than continuing with bad state.[1]

#### Execution / hook layer

- **Deterministic behavior**:
  - Hooks are plain scripts; they always run on events, independent of LLM “choice”.  
  - No conversational “maybe” about whether to run verification or exit; those are enforced by code.
- **Config updates take effect immediately**:
  - Every iteration reloads `.claude/loop/config.yaml`, so changing exit policy or verification behavior mid‑run is respected without restarting terminals.

#### Policy/config layer

- **Single source of truth**:
  - All enforcement rules live in config files under version control, not in scattered prompts.  
- **Immediate updates**:
  - Because each iteration re-parses config, edits to config mean next iteration honors them.

#### Domain layer

- **Shared, read‑only data**:
  - PRD/spec files, plan files (except the one terminal edits), and skills are shared and read‑only from the perspective of any given terminal’s control logic.
- **Per‑terminal plan handling**:
  - If necessary, each terminal can have its own plan (`plan.terminal-{id}.md`) to avoid cross‑edit races; `loop_state.loop_metadata.plan_path` then points at the per‑terminal copy.[1]

### 2.3 Interaction with existing mechanisms

Reuse as‑is:

- `TerminalStateManager`, state paths, locking, file layout in `.claude/state/terminals/{terminal_id}/`.[1]
- `parse_plan_tasks()` and task schema.[1]
- `/loop-core` skill as the main loop orchestrator, including dual exit gate concept.[1]

Consolidate / standardize:

- All loop state into `loop_state.json` + `loop_metrics.json` instead of scattered ad‑hoc files.[1]
- All loop policies into `.claude/loop/config.yaml`.

Deprecate / no‑op:

- Any custom one‑off loops that don’t use `TerminalStateManager`.  
- Any in‑prompt “please stop when you feel done” semantics; exit decisions move into code.

Required conventions:

- `.claude/loop/config.yaml` exists and is valid YAML.  
- Plans are markdown checklists compatible with `parse_plan_tasks()`.  
- All per‑terminal state files live under `.claude/state/terminals/{terminal_id}/` and use JSON.

3. Implementation Plan
----------------------

### 3.1 Exact places to change

**Hooks / event handlers / commands**

1. `/loop-core` skill implementation (SKILL.md and any Python backing scripts):[1]
   - Ensure it:
     - Accepts a plan path argument (`/loop-core path/to/plan.md`).  
     - Calls `parse_plan_tasks(plan_path)` each iteration.  
     - Uses `TerminalStateManager.read_state/write_state("loop_state", …)` for runtime state.  
   - Add:
     - A call to a policy function `should_exit(terminal_id, tasks, loop_state, config)` that implements the dual gate + PRD verification requirement.  

2. New command or alias `/ralph-loop`:
   - Thin wrapper over `/loop-core` that:
     - Picks a default plan (`.claude/loop/plan.md` or per‑terminal copy).  
     - Optionally sets `CLAUDE_TERMINAL_ID` and ensures state dir exists.

3. Per‑iteration hooks (can be simple functions in the same Python module or bash wrapper):
   - `on_iteration_start`, `on_iteration_end`, `on_loop_exit`, `on_error`:
     - Write entries to `decision.log` and `loop_metrics.json`.

**Config / metadata**

Add:

- `.claude/loop/config.yaml` with fields:
  - `exit_policy.*` as above.  
  - `verification.*` specifying whether to run `prd-verifier`, and report locations.  
  - `plans.default_plan`, `plans.allow_per_terminal_plan`.

Standardize:

- `loop_state.json` schema to include:
  - `plan_path`  
  - `policy_version` (optional hash of config contents).  
  - `iterations` counter.  
  - `completion_indicators` and `EXIT_SIGNAL` reflection if needed.

**Logs / per-terminal state files**

Create or formalize:

- `.claude/state/terminals/{terminal_id}/decision.log`:
  - Appended per iteration with JSON lines.
- `.claude/state/terminals/{terminal_id}/loop_metrics.json`:
  - Aggregated metrics (counts, durations).
- `.claude/loop/verification-report.md` (shared report; `loop_state.loop_metadata` can store its path).[1]

### 3.2 New modules and refactors

New modules (greenfield):

1. `scripts/loop_policy.py`:
   - Functions:
     - `load_config() -> dict` (reads `.claude/loop/config.yaml`).  
     - `should_exit(tasks, loop_state, config) -> bool`.  
     - `should_run_verifier(loop_state, config) -> bool`.  

2. `scripts/loop_observability.py`:
   - Functions:
     - `log_decision(terminal_id, event, payload)`.  
     - `update_metrics(terminal_id, metrics_delta)`.  

3. `skills/prd-verifier/SKILL.md`:
   - Skill that:
     - Reads PRD/spec, plan, current repo.  
     - Produces a verification report and flags (e.g., `all_prd_covered`, `verification_passed`) that can be written to `loop_state.loop_metadata` or a separate state key.

Refactors (existing code):

- `/loop-core` implementation:
  - Replace any embedded exit logic with calls to `loop_policy.should_exit`.  
  - Ensure it always re‑reads plan and config each iteration instead of caching them.

Potential decommissioning:

- Any ad‑hoc plan parsing or state handling not using `parse_plan_tasks()` and `TerminalStateManager`.

### 3.3 Stale-data immunity

Enforcement:

- Each iteration of `/loop-core` does (in order):

  1. Detect `terminal_id` (or read `CLAUDE_TERMINAL_ID`).  
  2. Load `loop_state = TerminalStateManager.read_state("loop_state")` (or default).  
  3. Load `config = load_config()` from `.claude/loop/config.yaml`.  
  4. Load `tasks = parse_plan_tasks(loop_state.plan_path or default_plan)`.  
  5. Decide next action via `/code` based on `tasks` and `loop_state`.  
  6. Update `loop_state` and write it back atomically.  
  7. Call `should_exit(tasks, loop_state, config)`; if true, exit; else, next iteration.

- No state is retained in Python globals across iterations beyond a single `/loop-core` invocation; even within one invocation, authoritative inputs are file‑backed, freshly read at step 2–4.

Caching (if any):

- You can cache parsed config inside a single iteration, but **never** across iterations.  
- If you later add advanced caching, invalidation must be tied to mtime or a checksum of the config file.

4. Testing Strategy
-------------------

### 4.1 Test scenarios

Use `pytest` with temporary directories to simulate terminals.

1. **Multi-terminal isolation**

- Scenario:
  - Create a fake repo with `.claude/state/terminals/termA/…` and `termB/…`.  
  - Run a simulated loop for `termA` that:
    - Writes `loop_state.json` with `current_task_id="TASK-001"`.  
  - Run a simulated loop for `termB` that:
    - Writes `loop_state.json` with `current_task_id="TASK-XYZ"`.  
- Assertions:
  - No file in `termA` dir is touched by the `termB` run and vice versa.  
  - `parse_plan_tasks()` results are the same for both if they share a plan, but decisions in `loop_state` differ only per terminal.

2. **Plan race safety**

- Scenario:
  - Two simulated “terminals” both read the same `plan.md`.  
  - Each updates plan via `/code` (you can mock it), writing different tasks as complete.  
- Assertion:
  - `parse_plan_tasks()` returns correct sets, and `loop_state` decisions remain independent; cross‑terminal behavior is distinguishable in per‑terminal logs.

3. **Policy changes mid-run**

- Scenario:
  - Start a simulated loop with `exit_policy.min_completion_indicators=3`.  
  - After first iteration, edit the config to set `min_completion_indicators=1`.  
- Assertions:
  - Second iteration re‑reads config and, if `EXIT_SIGNAL=true` and other conditions met, exits early per updated policy.

4. **Required procedures ignored**

- Scenario:
  - Configure `verification.require_verification_pass: true`.  
  - Simulate a run where `/code` sets `EXIT_SIGNAL: true` and `completion_indicators>=threshold` but `loop_state.loop_metadata.verification_passed` is `false` or absent.  
- Assertion:
  - `should_exit` returns `False`; loop continues and logs the missing verification.

5. **No false positives**

- Scenario:
  - A benign plan where all tasks complete, verification passes, and thresholds are met.  
- Assertion:
  - Loop exits with code 0; no logs show blocked/denied actions.

6. **No false negatives for critical guarantees**

- Scenario:
  - Plan missing tasks for a PRD section; verifier marks `all_prd_covered=false`.  
- Assertion:
  - Exit is not allowed; decision log includes reason.

### 4.2 Stale-state simulation

Scenarios:

- **Config change during long run**:
  - Already covered: confirm decisions after change use new policy.  
- **Partial log failures**:
  - Simulate failed writes to `decision.log` (e.g., using monkeypatch to raise I/O errors), ensure:
    - Loop still updates `loop_state` (core correctness), even if logging fails.  
- **Corrupted `loop_state.json`**:
  - Write invalid JSON; ensure `read_state` raises `LoopStateError`, loop stops predictably, and logs an error.

### 4.3 Acceptance & rollback

Acceptance criteria:

- Over N days of use:
  - Zero instances where a loop in one terminal modifies or clobbers another terminal’s state.  
  - No exits that violate exit policy (manual audits of decision logs).  
  - No cases where changing `.claude/loop/config.yaml` required restarting terminals to take effect.  
  - All critical flows (PRD-driven features) go through `/loop-core` and the new architecture.

Rollback plan:

- Keep old ad‑hoc loops and configs under version control.  
- If issues arise:
  - Disable `/ralph-loop` command and new config by:
    - Removing its skill declaration or CLI binding.  
  - Revert `.claude/loop/config.yaml` and `/loop-core` SKILL.md to previous version.  
  - Fall back to “manual use of `/code` + basic plans” while you investigate.

5. Observability & Metrics
--------------------------

### 5.1 Per-terminal logging

Each terminal writes:

- `.claude/state/terminals/{terminal_id}/decision.log` (JSONL):

  ```json
  {
    "timestamp": "2026-03-14T23:40:01Z",
    "event": "iteration_end",
    "terminal_id": "pid_12345_...",
    "plan_path": "plan.md",
    "current_task_id": "TASK-002",
    "completed_tasks": ["TASK-001"],
    "exit_decision": false,
    "reason": "verification_passed=false"
  }
  ```

- `.claude/state/terminals/{terminal_id}/verifier.log` (optional):

  ```json
  {
    "timestamp": "...",
    "task_id": "TASK-003",
    "status": "partial",
    "gaps": ["missing edge case X"],
    "prd_refs": ["2.3.1"]
  }
  ```

### 5.2 Metrics

Store aggregated metrics in `loop_metrics.json`, e.g.:

```json
{
  "iterations": 7,
  "tasks_completed": 4,
  "tasks_failed": 0,
  "blocks": 1,
  "last_exit_reason": "EXIT_SIGNAL & indicators",
  "avg_iteration_ms": 850
}
```

Track:

- Per‑terminal:
  - Error/exception count.  
  - Block events (policy prevented exit).  
  - Time per iteration.  
- System-wide (via ad‑hoc script aggregating per‑terminal metrics):
  - False positives/negatives (manually labelled at first, then counted).  
  - Distribution of exit reasons.

### 5.3 Detecting regressions

- If upstream behavior changes (Claude patterns, `/code` workflows):

  - You’ll see:
    - New error types in `decision.log`.  
    - Changed distribution of `exit_reason`.  
  - A simple nightly job (even a Python script you run manually) can:
    - Scan all `decision.log` files.  
    - Group by `event`, `exit_decision`, `reason`.  
    - Highlight new `reason` values or spikes in errors.

6. Risks & Tradeoffs
--------------------

### 6.1 Failure modes

- **Misconfigured config.yaml**:
  - Bad YAML → parsing failures → loops abort early.  
  - Mitigation: schema/check on startup; unit tests that validate config before use.
- **Mis-tagged tasks**:
  - Missing `after:` deps or incorrect tags → weird plan behavior.  
  - Mitigation: add plan linting (a small script that uses `parse_plan_tasks()` and checks invariants).
- **Hooks failing open vs closed**:
  - If policy code throws, you want a **fail‑closed** behavior for critical flows:
    - Default: don’t exit, log error.  
  - For non-critical flows, you may choose fail‑open.

- **Log corruption**:
  - `decision.log` could be partially written, but core state is in `loop_state.json` (atomic).  
  - Mitigation: treat logging as best-effort; correctness does not depend on logs.

### 6.2 Performance and complexity

Overhead:

- Extra filesystem I/O per iteration:
  - 1–2 small JSON reads (`loop_state`, `config`).  
  - 1 JSON write (`loop_state`).  
  - 1 log append.  
- This is negligible compared to model calls but adds complexity:

  - Extra modules (`loop_policy`, `loop_observability`).  
  - Config discipline (`.claude/loop/config.yaml`).

Scalability:

- As you add more skills/agents:
  - They can all **share the same state management layer and conventions**.  
  - Worktrees + per‑terminal state handle parallelism.  
- If you hit limits:
  - You can shard terminals by project root.  
  - Or add indexed/centralized metrics, but that’s not required initially.

### 6.3 Soft-enforcement areas

Some behaviors stay probabilistic:

- `/code` and `prd-verifier` are still LLM‑driven:
  - They might claim a task is done when it’s not or miss PRD gaps.  
- Mitigations:
  - Run verification multiple times or require multiple consistent passes.  
  - Add limited LLM-as-judge checks for specs.  
  - Allow manual overrides in plans (tag tasks as `[tag:manual-verified]`).

Refactor vs greenfield:

- Greenfield path:
  - Implement `/loop-core` + policy + observability as described, use it for all new work, while keeping legacy flows unchanged.  
- Refactor path:
  - Gradually migrate existing loops to call `/loop-core` and write to `loop_state`.  
  - Decommission old loops once confidence is high.

7. Completeness Checklist
-------------------------

- **Existing mechanisms referenced correctly**:
  - `TerminalStateManager`, `.claude/state/terminals/{terminal_id}/…`, `parse_plan_tasks()`, `/loop-core` skill, `loop_state.json`, `completion_indicators`, `EXIT_SIGNAL`.[1]
- **Change locations specified**:
  - `/loop-core` SKILL implementation.  
  - New skill command `/ralph-loop` (wrapper).  
  - New modules `loop_policy.py`, `loop_observability.py`, `prd-verifier` SKILL.  
  - Config `.claude/loop/config.yaml`.  
  - Per‑terminal logs `decision.log`, `loop_metrics.json`.
- **Automated tests, acceptance, rollback included**:
  - Multi-terminal isolation tests.  
  - Policy change tests.  
  - Stale-state simulations.  
  - Acceptance criteria and rollback to pre‑/loop-core‑only usage described.
- **Constraints respected**:
  - Multi-terminal isolation: all state under per‑terminal directories, no shared runtime state.[1]
  - Stale-data immunity: decisions recomputed each iteration from files, not globals.  
  - Willingness to refactor: design uses loop-core primitives but adds new modules/configs cleanly.
- **NEEDS CLARIFICATION**:
  - Exact shape of your `/loop-core` SKILL implementation and how it currently invokes `/code`.  
    - Question: Is `/loop-core` backed by Python scripts you control, or is it a pure SKILL.md shell?  
  - How you want to expose `/ralph-loop`: as a Claude Code skill only, a CLI, or both.  
    - Question: Should `/ralph-loop` be callable by other LLMs/tools as a CLI (e.g., `ralph-loop --plan plan.md`) or just a skill inside Claude Code?  
  - Where PRD/spec files live and whether they are 1:1 with plans or shared across plans.  
    - Question: Do you want one PRD per plan, or one PRD feeding multiple plans/tasks across services?

If you answer those three questions, I can translate this architecture into concrete file-level changes (paths + skeleton code for `loop_policy.py`, SKILL snippets, and test modules) tailored exactly to your current repo layout.

## Human

/arch-impl

Stage 0: Pre-Flight
- This command is called only AFTER /arch-proposal has produced an MVA architecture
  document in the current conversation.
- Scope: Turn that architecture into a concrete implementation plan; do not redesign it.

Stage 1: Load Inputs
- Architecture input:  
   - Use the MVA architecture document produced by the most recent /arch-proposal call immediately before this command in the current thread.
- Project context:
  - Use the current repository tree to infer real file/module paths where possible.

Stage 2: Extract Work Items
- From the architecture document:
  - Identify the layers it defines (e.g., tenant/session state, hooks/events,
    config/policy, engine, adapters, tests).
  - Identify all NEW modules, REFACTORS of existing modules, hooks, configs, and
    test cases the architecture calls for.
  - Identify any feature flags or rollback switches implied by the design.

Stage 3: Plan Construction
- Organize work into ordered phases (Phase 1..N), chosen to minimize risk; typically:
  - Phase 1: foundational infrastructure (tenant IDs, per-terminal logs, config loading).
  - Phase 2+: behavioral core (shared RTM/test logic, engine, adapters, enforcement).
- For each phase:
  - Create tasks with unique IDs (e.g., PH1-T1, PH1-T2, ...).
  - For every task, specify:
    - Target files/modules (exact paths where the architecture implies them).
    - Concrete edits/additions (functions, config keys, logs, tests).
    - Dependencies on other tasks when ordering matters.
- Always include for the overall plan:
  - Required new test files and explicit test scenarios.
  - Any feature flags / rollback mechanisms and how to toggle them.

Stage 4: Output
- Return a markdown checklist with:
  - Phase headings (e.g., `## Phase 1: Tenant + logging`).
  - Tasks as `[ ]` checklist items, each with a short title and sub-bullets for
    Files, Steps, and Depends-on.
- Do NOT re-argue, expand, or alter the architecture; only instantiate the work
  implied by the latest /arch-proposal MVA document.

## Assistant

## Phase 1: Tenant identity, config, and core loop state

- [ ] PH1-T1 – Introduce `.claude/loop/config.yaml` and base schema  
  - Files: `.claude/loop/config.yaml` (new), `README.md` or `docs/loop-core.md` (optional)  
  - Steps:  
    - Add initial config with `version`, `exit_policy`, `verification`, `plans`, and `logging` keys as described in the architecture.  
    - Document expected fields and defaults (e.g., `min_completion_indicators`, `require_exit_signal`, `default_plan`).  
  - Depends-on: none  

- [ ] PH1-T2 – Standardize terminal ID usage and env override  
  - Files: `scripts/terminal_detection.py`, `scripts/state_paths.py`, `scripts/state_manager.py`  
  - Steps:  
    - Ensure `get_terminal_id()` checks `CLAUDE_TERMINAL_ID` first, then falls back to existing detection.  
    - Verify all state paths under `.claude/state/terminals/{terminal_id}/` are computed only via `get_terminal_state_dir()` / `get_terminal_state_path()`.  
    - Add tests to confirm two different `CLAUDE_TERMINAL_ID` values get isolated dirs.  
  - Depends-on: PH1-T1  

- [ ] PH1-T3 – Normalize `loop_state.json` schema  
  - Files: `scripts/state_manager.py`, `tests/test_state_manager.py`  
  - Steps:  
    - Define a canonical schema for `loop_state.json` in a module docstring or a small `LoopState` dataclass (even if you keep plain dicts).  
    - Ensure write/read of `"loop_state"` always include keys: `current_task_id`, `completed_tasks`, `failed_tasks`, `completion_indicators`, `loop_metadata.plan_path`, `loop_metadata.started_at`, `loop_metadata.last_update`, `loop_metadata.iterations`.  
    - Add tests that write a sample `loop_state` and read it back with exact structure.  
  - Depends-on: PH1-T2  

- [ ] PH1-T4 – Fix CI coverage module mismatch  
  - Files: `.github/workflows/test.yml`  
  - Steps:  
    - Change `--cov=loop_core` to `--cov=scripts` (or the correct package name) as indicated in the review bundle.  
    - Run CI locally to confirm coverage passes.  
  - Depends-on: none  


## Phase 2: Policy and observability modules

- [ ] PH2-T1 – Add `scripts/loop_policy.py` module  
  - Files: `scripts/loop_policy.py`, `tests/test_loop_policy.py` (new)  
  - Steps:  
    - Implement `load_config()` to read `.claude/loop/config.yaml` and return a dict; handle file-not-found and YAML errors with clear exceptions.  
    - Implement `should_exit(tasks, loop_state, config)` applying: `completion_indicators`, `EXIT_SIGNAL`, `require_all_tasks_complete`, `require_verification_pass`.  
    - Implement `should_run_verifier(loop_state, config)` to read `verification.enabled` and state flags.  
    - Add unit tests that cover different combinations of policy flags and loop state.  
  - Depends-on: PH1-T1, PH1-T3  

- [ ] PH2-T2 – Add `scripts/loop_observability.py` module  
  - Files: `scripts/loop_observability.py`, `tests/test_loop_observability.py` (new)  
  - Steps:  
    - Implement `log_decision(terminal_id, event, payload)` to append JSON lines to `.claude/state/terminals/{terminal_id}/decision.log` using `TerminalStateManager` paths.  
    - Implement `update_metrics(terminal_id, metrics_delta)` to merge increments into `loop_metrics.json`.  
    - Ensure logs writes are best-effort (do not break the loop on log I/O failure).  
    - Add tests that simulate multiple events and verify per-terminal log isolation.  
  - Depends-on: PH1-T2, PH1-T3  

- [ ] PH2-T3 – Define verification report contract  
  - Files: `.claude/loop/config.yaml`, `docs/loop-verification.md` (optional), placeholder `skills/prd-verifier/SKILL.md`  
  - Steps:  
    - Extend config with `verification.write_report` path and any flags needed (e.g., `max_passes`).  
    - Create a stub `skills/prd-verifier/SKILL.md` that documents expected inputs/outputs (e.g., where to write `verification-report.md`, what flags to set in `loop_state.loop_metadata`).  
    - This task establishes the contract without implementing full verification logic yet.  
  - Depends-on: PH2-T1  


## Phase 3: Wire /loop-core to policy and state

- [ ] PH3-T1 – Refactor `/loop-core` skill to use `loop_policy`  
  - Files: `skills/loop-core/SKILL.md`, any backing script (e.g., `scripts/loop_core_runner.py` if present)  
  - Steps:  
    - Identify where the current dual-condition exit gate is implemented (completion indicators + EXIT_SIGNAL).  
    - Replace in-line logic with a call to `loop_policy.should_exit(tasks, loop_state, config)`.  
    - Ensure each iteration does: detect terminal_id → read `loop_state` → load config → parse plan → execute `/code` → update `loop_state` → log decision → check `should_exit`.  
  - Depends-on: PH2-T1, PH2-T2  

- [ ] PH3-T2 – Ensure plan path and metadata are written to loop_state  
  - Files: `skills/loop-core/SKILL.md`, `scripts/state_manager.py` (if helper added), `tests/test_integration.py`  
  - Steps:  
    - On first run, set `loop_state.loop_metadata.plan_path` to the plan path argument (e.g., `plan.md` or passed file).  
    - Update `loop_state.loop_metadata.iterations` and `last_update` each iteration.  
    - Update `tests/test_integration.py` to assert these fields are set after a simulated loop lifecycle.  
  - Depends-on: PH1-T3  

- [ ] PH3-T3 – Add per-iteration observability hooks  
  - Files: `/loop-core` backing script, `scripts/loop_observability.py`, `tests/test_integration.py`  
  - Steps:  
    - At `on_iteration_start`, call `log_decision(..., event="iteration_start", payload=loop_state subset)`.  
    - At `on_iteration_end`, log tasks summary, exit decision, and reasons.  
    - At `on_loop_exit`, log final state and exit reason.  
    - Extend integration tests to assert that `decision.log` and `loop_metrics.json` are created and contain expected entries.  
  - Depends-on: PH2-T2, PH3-T1  

- [ ] PH3-T4 – Support config changes mid-run  
  - Files: `/loop-core` backing script, `scripts/loop_policy.py`, `tests/test_loop_policy.py`  
  - Steps:  
    - Confirm that policy is loaded fresh in each iteration (no module-level caching).  
    - Add a test scenario that modifies `.claude/loop/config.yaml` between iterations and assert the new policy affects `should_exit`.  
  - Depends-on: PH2-T1, PH3-T1  


## Phase 4: /ralph-loop entry point and per-terminal plans

- [ ] PH4-T1 – Add `/ralph-loop` skill/command wrapper  
  - Files: `skills/ralph-loop/SKILL.md` (new), small runner script (e.g., `scripts/ralph_loop_entry.py`)  
  - Steps:  
    - Define a skill that takes a user description (`"Build the app to satisfy prd.md"`) and resolves a plan path (e.g., `.claude/loop/plan.md` or per-terminal plan).  
    - Delegate actual execution to `/loop-core plan_path`.  
    - Document usage and how it composes with `/code` and `loop-core`.  
  - Depends-on: PH3-T1, PH3-T2  

- [ ] PH4-T2 – Optional: per-terminal plan cloning  
  - Files: `scripts/ralph_loop_entry.py`, `scripts/state_paths.py`, `tests/test_per_terminal_plan.py` (new)  
  - Steps:  
    - Implement logic to, on first `/ralph-loop` run for a terminal, copy a shared `plan.md` to `.claude/loop/plan.{terminal_id}.md` and set `loop_state.loop_metadata.plan_path` accordingly.  
    - Add tests to ensure two simulated terminals operate on different plan files and don’t overwrite each other’s tasks.  
  - Depends-on: PH1-T2, PH3-T2  

- [ ] PH4-T3 – Document worktree + /ralph-loop workflow  
  - Files: `docs/ralph-worktrees.md` or `README.md`  
  - Steps:  
    - Describe recommended pattern: create a git worktree, run `/ralph-loop` in each worktree/terminal, and merge branches after loops exit.  
    - Note that per-terminal state and optional per-terminal plans keep loops isolated even on shared repos.  
  - Depends-on: PH4-T1  


## Phase 5: Verification integration (optional but recommended)

- [ ] PH5-T1 – Implement initial `prd-verifier` skill behavior  
  - Files: `skills/prd-verifier/SKILL.md`, `tests/test_prd_verifier.md` (if you test via harness)  
  - Steps:  
    - Implement a minimal skill that reads PRD/spec, current plan, and codebase, then writes a `verification-report.md` and sets a simple flag (e.g., `verification_passed: true/false`) that `/loop-core` can see (via state write or static file).  
    - Add tests that simulate a tiny repo, PRD, plan, and check that the report and flag are produced.  
  - Depends-on: PH2-T3  

- [ ] PH5-T2 – Wire verification into exit policy  
  - Files: `scripts/loop_policy.py`, `/loop-core` backing script, `tests/test_loop_policy.py`, `tests/test_integration.py`  
  - Steps:  
    - Extend `should_exit()` to check the verification flag when `exit_policy.require_verification_pass` is true.  
    - Invoke `prd-verifier` at appropriate points (e.g., when all tasks are done but before allowing exit) and update `loop_state` with results.  
    - Add integration tests where verification fails and ensure the loop does not exit, and where verification passes and exit is allowed.  
  - Depends-on: PH5-T1, PH2-T1  

- [ ] PH5-T3 – Add stale-state and corruption tests  
  - Files: `tests/test_integration.py`, `tests/test_state_manager.py`  
  - Steps:  
    - Add tests that corrupt `loop_state.json` and verify that `TerminalStateManager.read_state` raises and the loop fails safely (no undefined behavior).  
    - Add tests that simulate log write failures and confirm loop correctness is unaffected.  
  - Depends-on: PH1-T3, PH2-T2  


## Phase 6: Feature flags, rollout, and rollback

- [ ] PH6-T1 – Add feature flag for “enforced Ralph loop”  
  - Files: `.claude/loop/config.yaml`, `scripts/loop_policy.py`, `/loop-core` backing script, `tests/test_loop_policy.py`  
  - Steps:  
    - Introduce a config flag like `enforcement.enabled: true/false`.  
    - When disabled, `/loop-core` should behave in a minimally opinionated way (e.g., only use EXIT_SIGNAL and completion indicators, ignore verification).  
    - Add tests that verify behavior under both enabled and disabled settings.  
  - Depends-on: PH2-T1, PH3-T1  

- [ ] PH6-T2 – Document rollback procedure  
  - Files: `docs/loop-rollout.md` or `README.md`  
  - Steps:  
    - Document how to disable new behavior by flipping `enforcement.enabled` or by reverting skill bindings.  
    - List which files/modules would be reverted in a full rollback (e.g., prior `/loop-core` SKILL, removing `loop_policy` usage).  
  - Depends-on: PH6-T1  

- [ ] PH6-T3 – Add acceptance monitoring script  
  - Files: `scripts/loop_metrics_summary.py`, `tests/test_loop_metrics_summary.py` (optional)  
  - Steps:  
    - Implement a script that scans `.claude/state/terminals/*/decision.log` and `loop_metrics.json` and produces a summary (error counts, exit reasons, durations).  
    - Use it to validate acceptance criteria during rollout (e.g., no cross-terminal effects, no unexpected exit reasons).  
  - Depends-on: PH2-T2, PH5-T2
```
