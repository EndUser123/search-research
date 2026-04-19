<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Please look up github repos for claude code for ralph-wiggim, and ralphy.  Please provide the architecture and working code for another LLM to take your report and use it to enable a claude skill to look until all tasks are done and verified against a prd or spec or project plan, etc.

There are two main things to grab here: the Ralph-style repos you asked about, and then an architecture + code pattern for a Claude skill another LLM can drive to “work until done and verified against a PRD/spec.”

***

## Relevant Ralph / “ralphy” repos

These are the key repos and references worth studying:

- `frankbria/ralph-claude-code` – Autonomous Claude Code loop with intelligent exit detection, error handling, rate limiting, PRD import, CI, tests.[^1_1][^1_2]
- `snarktank/ralph` – Autonomous AI agent loop that runs AI coding tools (Amp or Claude Code) repeatedly until all PRD items are complete, using Git as memory.[^1_3][^1_4]
- Geoffrey Huntley’s “how-to-ralph-wiggum” – Reference repo/blog on the Ralph Wiggum technique for Claude Code (looping until done).[^1_5][^1_6][^1_7]
- `michaelshimeles/ralphy` – “Ralphy is an autonomous bash script that runs multiple AI agents in a loop to complete product requirements documents,” including Claude Code, Cursor agent, etc.[^1_8][^1_9]

These all implement the same core pattern: a shell/CLI loop that repeatedly calls Claude Code or an AI tool with a PRD/spec + progress context, and exits when it detects completion signals.[^1_6][^1_7][^1_1][^1_3]

***

## Target architecture: “Verifier-driven Ralph” Claude skill

Objective: design a Claude Code skill and control loop that another LLM can call to drive Claude Code until all tasks derived from a PRD/spec are completed and **verified** against that PRD/spec/project plan.

High-level architecture:

1. **Inputs**
    - `prd.md` (or `spec.md`, `project-plan.md`): the authoritative requirements.[^1_10][^1_11]
    - `skill/skill.md`: Claude skill instructions for “PRD-driven development loop with verifier.”[^1_12][^1_10]
    - `skill/templates/*.md`: task list template, verification checklist, progress log format.[^1_11][^1_10]
    - `skill/context/*.md`: codebase conventions, architecture notes, testing strategy, etc.[^1_10]
2. **Persistent state (files in repo)**
    - `tasks.yaml`: structured task list, with `id`, `description`, `status`, `evidence`, `verification_status`.
    - `progress.log.md`: human-readable log of each loop iteration.
    - `verification-report.md`: structured verifier output tied to PRD items.
    - Git history: each completed task must have at least one commit referencing its `task_id`.[^1_1][^1_3][^1_6]
3. **Loop controller (outer agent / script)**
    - A small CLI (Python or Node) that:
        - Calls Claude Code with the skill and a “loop-step” prompt.
        - Parses machine-readable signals from Claude’s output:
            - `<loop-status>continue|blocked|complete</loop-status>`
            - `<current-task>task-id</current-task>`
        - On `blocked`, raises to human or different agent.
        - On `complete`, triggers final verification run and exits.
    - Inspired by `ralph-claude-code` and Ralph loop bash examples, but with explicit structured signals and verification stages.[^1_13][^1_7][^1_3][^1_1]
4. **Verifier sub-agent**
    - Same Claude skill (or a second `skill-verifier.md`) invoked in a “verification mode”:
        - Reads PRD + `tasks.yaml` + codebase + tests.
        - For each PRD item, checks:
            - Is there an implemented feature mapped to it?
            - Are there tests or other evidence?
            - Are acceptance criteria met (tests passing, lints clean, etc.)?[^1_7][^1_6][^1_10]
        - Writes `verification-report.md` and updates `tasks.yaml` with `verification_status`.
5. **Stop conditions (exit detection)**
    - All `tasks.status == "done"` and all `verification_status == "verified"`.[^1_3][^1_6][^1_1]
    - No remaining failing tests or lint errors relevant to the PRD scope.
    - No new discrepancies discovered in a final verification pass.
    - Optional: multiple consecutive “done” signals and test-only loops to avoid premature exit, like `ralph-claude-code`.[^1_6][^1_1]
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

There are examples of PRD → tasks → loop prompts in Ralph Wiggum articles and `ralph-claude-code`, which you can adapt as starting prompts.[^1_14][^1_13][^1_7][^1_1][^1_6]

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

This builds directly on how PRD-focused Claude skills are described in `anombyte93/prd-taskmaster` and “Stop re-explaining your product to AI. Build a Claude Code skill…”, which use templates and context files to align PRD structure with codebase conventions.[^1_11][^1_10]

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

This mirrors Ralph loops (iterative CLI calls, simple exit conditions) but uses structured tags the outer controller and a supervising LLM can reliably parse.[^1_13][^1_7][^1_1][^1_3]

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

Because the contract is small and file-based, *any* LLM with filesystem/command tools can orchestrate the loop. The details of Claude Code prompts and skill internals stay encapsulated in `skill.md` and templates, similar to how generic Claude Code skills encapsulate behavior for PRD generation and project management.[^1_12][^1_10][^1_11]

***

If you tell me which language you want the outer loop and “API surface” in (Python CLI, Node + MCP, something else), I can sketch the full `tasks.yaml` schema, a concrete `skill.md` skeleton, and ready-to-run CLI scaffolding.
<span style="display:none">[^1_15][^1_16][^1_17][^1_18][^1_19][^1_20][^1_21][^1_22][^1_23][^1_24][^1_25]</span>

<div align="center">⁂</div>

[^1_1]: https://github.com/frankbria/ralph-claude-code

[^1_2]: https://www.claude-hub.com/resource/github-cli-frankbria-ralph-claude-code-ralph-claude-code/

[^1_3]: https://github.com/snarktank/ralph

[^1_4]: https://www.youtube.com/watch?v=RQ57cUcGDGg

[^1_5]: https://github.com/ghuntley/how-to-ralph-wiggum

[^1_6]: https://paddo.dev/blog/ralph-wiggum-autonomous-loops/

[^1_7]: https://awesomeclaude.ai/ralph-wiggum

[^1_8]: https://shyft.ai/skills/ralphy

[^1_9]: https://github.com/michaelshimeles/ralphy

[^1_10]: https://designproject.io/blog/how-to-build-custom-claude-code-skills-and-why-your-team-needs-them/

[^1_11]: https://github.com/anombyte93/prd-taskmaster

[^1_12]: https://github.com/travisvn/awesome-claude-skills

[^1_13]: https://www.aihero.dev/tips-for-ai-coding-with-ralph-wiggum

[^1_14]: https://www.reddit.com/r/ClaudeAI/comments/1pxc31u/a_quick_guide_to_ralph_wiggum/

[^1_15]: https://www.linkedin.com/in/jesse-henson-ai

[^1_16]: https://www.linkedin.com/in/kunle-oshiyoye-915b22b1

[^1_17]: https://www.linkedin.com/in/richardortega

[^1_18]: https://www.linkedin.com/in/james-paynter

[^1_19]: https://www.linkedin.com/in/indragie

[^1_20]: https://www.linkedin.com/in/alistairisrael

[^1_21]: https://www.linkedin.com/in/roger-s-wells

[^1_22]: https://www.linkedin.com/in/austin-schenk-a88694140

[^1_23]: https://www.linkedin.com/in/steve-wall-agentic-engineer

[^1_24]: https://www.linkedin.com/in/staffan-greisz-1783b939

[^1_25]: https://github.com/SeanZoR/ralph-pilot


---

# python

Let’s lock onto a **Python-first** implementation for the outer loop and API surface, building on the Ralph pattern but oriented around a Claude Code skill that executes and self-verifies against a PRD/spec.[^2_1][^2_2][^2_3][^2_4]

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

Ralph-style loops use bash `loop.sh` and prompt files; we’re replacing `loop.sh` with a Python CLI, while keeping the “stateless iteration + on-disk state” pattern.[^2_2][^2_5]

***

## `controller.py`: loop controller

This assumes a `claude` CLI similar to Ralph setups (headless mode, prompt via skill).[^2_6][^2_4][^2_2]
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

This draws on Ralph’s “dumb loop + smart prompt + on-disk state” pattern and extends it with explicit `<loop-status>` markers and an optional JSON meta channel.[^2_3][^2_4][^2_2]

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

This is analogous to Ralph’s `loop.sh`, but in Python with structured JSON output for downstream LLMs/tools.[^2_4][^2_2][^2_3]

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

You can pattern this off of Ralph + Smart Ralph / spec-driven skills: PRD to JSON tasks, tasks to implementation, feedback via tests and CI.[^2_7][^2_3][^2_4]

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

The contract is file + CLI based, so it’s language- and model-agnostic, similar in spirit to Ralph’s openness to other CLIs (Amp, Cursor, etc.).[^2_2][^2_3]

***

Would you like a concrete `tasks.yaml` schema and a `skill.md` skeleton next, aligned with this controller and tuned specifically for “PRD + verification” rather than generic Ralph?
<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://github.com/frankbria/ralph-claude-code

[^2_2]: https://github.com/ClaytonFarr/ralph-playbook

[^2_3]: https://github.com/snarktank/ralph

[^2_4]: https://github.com/tzachbon/smart-ralph

[^2_5]: https://www.newline.co/@Dipen/ralph-wiggum-approach-using-claude-code--a7ce3ef8

[^2_6]: https://github.com/michaelshimeles/ralphy

[^2_7]: https://github.com/topics/ralph-loop

[^2_8]: https://paddo.dev/blog/ralph-wiggum-autonomous-loops/

[^2_9]: https://www.youtube.com/watch?v=eD4CEZ-_-sk

[^2_10]: https://stackoverflow.com/questions/209470/how-to-implement-common-bash-idioms-in-python

[^2_11]: https://www.reddit.com/r/ClaudeCode/comments/1qqlt3n/any_recommendations_for_a_good_ralph_wiggum_meta/

[^2_12]: https://www.reddit.com/r/ClaudeCode/comments/1qfjwpe/ralph_loop_claude_code_build_me_a_calculator_280/

[^2_13]: https://www.youtube.com/watch?v=6UESnxzLMCY

[^2_14]: https://github.com/michaelshimeles/ralphy/blob/main/ralphy.sh

[^2_15]: https://www.linkedin.com/posts/md-amanatullah12345_github-snarktankralph-ralph-is-an-autonomous-activity-7416562636730863616-ZUPV


---

# Yes give me tasksyaml schema and skillmd

Show me full skillmd with verifier mode prompts

Here’s a concrete `tasks.yaml` schema and a full `skill.md` you can drop into `.claude/skills/prd-loop/`, including a **verify mode** prompt. The design borrows from spec‑driven / Smart Ralph style tasks and PRD-driven tools, but keeps the schema lean.[^3_1][^3_2][^3_3][^3_4][^3_5]

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

Key points informed by spec‑driven / task‑master style schemas:[^3_2][^3_4][^3_5][^3_1]

- **Per‑task fields**
    - `id`: stable identifier; Claude must not change existing IDs.
    - `title`, `description`: short, concrete; no vague tasks.
    - `status`: lifecycle for implementation.
    - `verification_status`: lifecycle for PRD compliance.
    - `priority`: for selection heuristics.
    - `prd_refs`: tie tasks to PRD sections/acceptance criteria.
    - `acceptance_criteria`: copy or normalize from PRD for local reasoning.[^3_6][^3_2]
    - `test_plan`: how to verify success (aligned with acceptance criteria).[^3_4][^3_2]
    - `dependencies`: simple ordering.
    - `evidence`: pointers the verifier can inspect; encourages code + tests + commits.
    - `last_updated`: helps detect stale tasks.
- **Global fields**
    - `version`: for future schema migrations.
    - `source_prd`: path to PRD file.

***

## `skill.md` – full draft with verify mode

Place this at `.claude/skills/prd-loop/skill.md`.

It uses a **mode flag** pattern by instructing you (the human) or an outer script to pass `--mode=develop` or `--mode=verify`. The loop controller you already have will set `mode` via CLI flags; here we tell Claude how to behave in each mode and how to emit the tags your Python parses.[^3_7][^3_2][^3_6]

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
<span style="display:none">[^3_10][^3_11][^3_12][^3_13][^3_14][^3_15][^3_8][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://github.com/tzachbon/smart-ralph

[^3_2]: https://claytonfarr.github.io/ralph-playbook/

[^3_3]: https://ig.nore.me/2025/09/spec-workflow/

[^3_4]: https://docs.task-master.dev/capabilities/task-structure

[^3_5]: https://github.com/eyaltoledano/claude-task-master

[^3_6]: https://prg.sh/ramblings/Spec-Kit-+-Ralph-Wiggum---The-Workflow-Nobody's-Talking-About

[^3_7]: https://pasqualepillitteri.it/en/news/158/framework-ai-spec-driven-development-guide-bmad-gsd-ralph-loop

[^3_8]: https://mcpmarket.com/tools/skills/smart-ralph-development-workflow

[^3_9]: https://www.linkedin.com/posts/topisantakivi_a-recipe-for-spec-driven-development-so-activity-7422730557303816192-z_GQ

[^3_10]: https://www.linkedin.com/posts/mapocock_my-ralph-setup-has-evolved-a-lot-since-you-activity-7420103835718696961-nbwW

[^3_11]: https://github.com/eyaltoledano/claude-task-master/issues/707

[^3_12]: https://www.youtube.com/watch?v=_IK18goX4X8

[^3_13]: https://www.reddit.com/r/ClaudeCode/comments/1qm5vmh/my_ralph_wiggum_breakdown_just_got_endorsed_as/

[^3_14]: https://lobehub.com/pl/skills/tzachbon-smart-ralph-plugin-structure

[^3_15]: https://www.youtube.com/watch?v=RQ57cUcGDGg


---

# How Smart Ralph verifier mode catches implementation gaps that basic loops miss and improves code quality

Here's the direct answer — this is focused and dense.

## The Core Problem Basic Loops Don't Solve

A basic Ralph loop answers: "did Claude say it's done?" A Smart Ralph verifier asks: "is the implementation actually aligned with the spec?" These are fundamentally different questions.[^4_1][^4_2]

The root failure in vanilla loops is **accountability without contract**: Claude decides completion by conversational cues rather than objective criteria. As one field report describes it, "we've been treating 'done' as a conversational cue when it should be a contract." The result is high false-completion rates — Claude marks a feature `passes: true` while quietly skipping edge cases, leaving stubs, or writing tautological tests that verify nothing.[^4_3][^4_4][^4_1]

***

## How Smart Ralph's Verifier Catches Gaps

### Gap 1: Spec-vs-Code Drift (the PLANNING mode catch)

Smart Ralph's PLANNING mode (from `PROMPT_plan.md`) runs explicit gap analysis using up to 500 subagents comparing `specs/*` against `src/*` in parallel. This catches what a basic loop cannot:[^4_5]


| What basic loops miss | What PLANNING mode finds |
| :-- | :-- |
| TODOs and stubs treated as complete | Searches explicitly for `TODO`, `placeholder`, `minimal implementations` |
| Skipped/flaky tests hiding failures | Scans for `skipped/flaky tests` as a gap signal |
| `ripgrep` false negatives ("I didn't find it, so it's missing") | Instructs "do NOT assume not implemented — confirm with code search first" |
| Single-pass spec reading | Opus subagent + Ultrathink reasoning over all subagent findings |
| No cross-spec consistency check | Spec-to-spec inconsistencies trigger an Opus review to correct the spec itself |

The PLANNING prompt runs as a **loop** (fresh context per pass) so it self-corrects until the plan stabilizes — usually 1–2 iterations. Basic loops never re-audit the plan; they just execute it forward.[^4_5]

### Gap 2: Tautological Tests (the anti-vaporware catch)

One of the most documented Smart Ralph improvements is catching **tautological test generation** — where Claude writes tests that reimplement the function's logic rather than encoding business requirements. A tautological test like:[^4_3]

```python
assert calculate_discount(100, 20) == 100 * (1 - 20 / 100)
```

passes even if the formula is wrong. A verifier checking against acceptance criteria catches this because the expected value (`80.0`) is defined externally from the spec, not derived from the code.[^4_3]

**Acceptance-driven backpressure** in Ralph Playbook makes this explicit: during PLANNING, test requirements are derived from acceptance criteria before implementation starts. The BUILDING prompt then enforces "all required tests must exist and pass before the task is considered complete." This prevents Claude from claiming done without tests that actually prove the spec behavior.[^4_5]

### Gap 3: Interface Mismatches and Integration Failures

Unit tests in a basic loop run per-task in isolation. They miss the class of bugs Craig Johnston calls "Ralph's Uncle" failures:[^4_3]

- **Interface mismatches**: Claude writes a client sending camelCase JSON; server expects snake_case. Both unit tests pass; integration fails.
- **Protocol gaps**: HTTP client doesn't handle 429s; tests mock the API.
- **State corruption**: function works on first call, corrupts shared state on subsequent calls; single-invocation tests pass.

A verifier mode reading the full spec + codebase simultaneously — not just the current task's files — surfaces these cross-boundary issues. Basic loops never zoom out.

### Gap 4: Context Rot in Long Runs

Geoffrey Huntley's design deliberately re-allocates the full spec every iteration to prevent "context rot" — the degradation that happens past 60–70% context capacity where the model begins hallucinating or contradicting earlier work. Smart Ralph compounds this: PLANNING mode produces a fresh `IMPLEMENTATION_PLAN.md` when it detects the plan is stale or drift has accumulated, which prevents the building loop from compounding errors from a bad starting plan.[^4_6][^4_5]

### Gap 5: Non-Deterministic Quality (LLM-as-Judge)

Some acceptance criteria — UX feel, tone, visual hierarchy — cannot be verified by `pytest`. Smart Ralph's extended playbook adds an `llm-review.ts` fixture that provides binary pass/fail for subjective criteria, using screenshots or text artifacts fed to a judge model. The loop keeps running until `result.pass == true`. Basic Ralph has no mechanism here; it either stops early or loops forever on vague criteria.[^4_5]

***

## What the Verification Hierarchy Actually Stacks

Informed by the "Ralph's Uncle" verification model, which explicitly maps what each layer catches and misses:[^4_3]


| Level | Catches | Misses |
| :-- | :-- | :-- |
| Static analysis | Type errors, security patterns, dead code | Logic errors, integration failures |
| Unit tests | Wrong outputs, edge cases, error handling | Interface mismatches, timing bugs, system failures |
| Integration/E2E | Component interaction, protocol errors, state issues | Subtle logic bugs masked by test design |
| Mutation testing | Weak/tautological tests, test gaps | Spec errors, architectural issues, NFRs |

The core insight: **every level that's missing in a basic loop is a category of bugs that reach production undetected**. Because AI generates code at 10× human velocity, every gap in the verification pipeline lets through proportionally more defects.[^4_3]

***

## Why This Matters Specifically for PRD-Driven Loops

For the skill you're building, the verifier mode adds a layer none of the above levels alone provide: **spec traceability**. A test suite can be 100% green while still missing entire PRD sections that were never tasked. The verifier in Smart Ralph (PLANNING mode's gap analysis) cross-references spec sections against code existence — not just tests — meaning it can surface a gap like "Section 3.2 Error Handling has no tasks in `IMPLEMENTATION_PLAN.md` and no corresponding code in `src/`" even when all existing tests pass.[^4_7][^4_8][^4_5]

That's the gap a basic Ralph loop structurally cannot catch: it only iterates on what it knows is in the plan. The verifier asks what the plan forgot.
<span style="display:none">[^4_10][^4_11][^4_12][^4_13][^4_14][^4_15][^4_16][^4_17][^4_18][^4_19][^4_20][^4_21][^4_22][^4_23][^4_24][^4_25][^4_26][^4_27][^4_9]</span>

<div align="center">⁂</div>

[^4_1]: https://natesnewsletter.substack.com/p/my-honest-field-notes-on-the-verification

[^4_2]: https://claudefa.st/blog/guide/mechanics/ralph-wiggum-technique

[^4_3]: https://imti.co/ai-verified-development/

[^4_4]: https://adamtuttle.codes/blog/2026/my-ralph-workflow-for-claude-code/

[^4_5]: https://github.com/ClaytonFarr/ralph-playbook

[^4_6]: https://linearb.io/blog/ralph-loop-agentic-engineering-geoffrey-huntley

[^4_7]: https://github.com/ghuntley/how-to-ralph-wiggum

[^4_8]: https://ig.nore.me/2025/09/spec-workflow/

[^4_9]: https://www.reddit.com/r/ClaudeAI/comments/1qgccgs/25_claude_code_tips_from_11_months_of_intense_use/

[^4_10]: https://github.com/ghuntley/how-to-ralph-wiggum/blob/main/README.md

[^4_11]: https://paddo.dev/blog/ralph-wiggum-playbook/

[^4_12]: https://www.youtube.com/watch?v=_IK18goX4X8

[^4_13]: https://yuv.ai/blog/ralph-claude-code

[^4_14]: https://platform.uno/blog/ralph-wiggum-explained-stop-telling-ai-what-you-want-tell-it-what-blocks-you/

[^4_15]: https://www.reddit.com/r/ClaudeAI/comments/1rgl3qi/claude_straight_up_ignoring_spec_docs_no_matter/

[^4_16]: https://www.reddit.com/r/ClaudeCode/comments/1q9qjk4/the_ralphwiggum_loop/

[^4_17]: https://www.linkedin.com/posts/yaniv-fox-b864a1264_i-put-together-a-notebooklm-folder-to-make-activity-7415725275487043585-W0YC

[^4_18]: https://www.techrxiv.org/users/1024156/articles/1383980-llm-aided-verification-gap-detection-a-methodology-for-identifying-missing-checkers-in-uvm-testbenches

[^4_19]: https://www.linkedin.com/posts/cole-medin-727752184_i-was-wrong-about-ralph-wiggum-for-ai-coding-activity-7419908728084262912-4bJw

[^4_20]: https://pasqualepillitteri.it/en/news/158/framework-ai-spec-driven-development-guide-bmad-gsd-ralph-loop

[^4_21]: https://ghuntley.com/ralph/

[^4_22]: https://github.com/frankbria/ralph-claude-code

[^4_23]: https://daz.is/blog/how-i-work-with-ai-coding-agents/

[^4_24]: https://www.snowflake.com/en/engineering-blog/benchmarking-LLM-as-a-judge-RAG-triad-metrics/

[^4_25]: https://www.reddit.com/r/ClaudeAI/comments/1nwhdab/ralph_for_claude_code_autonomous_ai_development/

[^4_26]: https://codemanship.wordpress.com/category/a-i/

[^4_27]: https://www.linkedin.com/posts/aaronbalentine_aicoding-githubcopilot-claudecode-activity-7420439412498391040-a1wd

