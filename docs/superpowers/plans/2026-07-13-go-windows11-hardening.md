# `/go` Windows 11 Execution Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing `/go` workflow reliable on Windows 11 by aligning its documentation, launcher, state bootstrap, worktree root, and retry behavior without changing task selection, dispatch modes, completion tokens, or SDLC gates.

**Architecture:** Keep `skills/go/scripts/orchestrate.py` as the execution authority. Add a short Windows PowerShell entrypoint that delegates to the existing Python orchestrator, centralize the Windows worktree-root default, and preserve the current disk-backed run-context and dispatch contracts. Replace manual shell bootstrap instructions with one tested invocation path; do not rewrite the orchestrator or remove existing compatibility scripts until active consumers are proven.

**Tech Stack:** Windows 11, PowerShell 7, Python 3.14, pytest, Git worktrees, Claude Code skill/hook dispatch.

## Global Constraints

- Windows 11 is the only supported platform; do not add Linux, macOS, WSL, or POSIX portability abstractions.
- `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/` is the canonical source repository; do not edit `C:/Users/brsth/.claude/plugins/cache/` or generated cache copies.
- `P:/.worktrees` is the desired default worktree root; preserve `GO_WORKTREE_ROOT` as an explicit override and do not move or delete existing worktrees automatically.
- `P:/.claude/.artifacts/{TERMINAL_ID}/go` remains the normal project-scoped artifact location; preserve `run_context.py` disk-authority and stale-run recovery semantics.
- Preserve all existing `/go` input precedence, dispatch modes (`pi`, `local`, `claude`), plan-readiness checks, task contracts, completion tokens, continuation gates, and rollback controls.
- Do not edit the dirty parent worktree. Execute implementation in a dedicated worktree under `P:/.worktrees` after recording the source revision and status.
- Do not make production settings or plugin-cache changes in this plan. Runtime registration/release remains an explicit human checkpoint.
- Every implementation task must have a focused failing test, a minimal fix, and a focused passing test before the next task begins.

## Verified Current State and Root Cause

- `skills/go/scripts/orchestrate.py:create_worktree()` already uses `GO_WORKTREE_ROOT` and currently defaults to `P:/worktrees`; it creates worktrees with an argument-array `subprocess.run` call and Python UUIDs.
- `skills/go/scripts/orchestrate.py:ensure_runtime_env()` already creates/reuses run IDs and state directories through Python.
- `skills/go/scripts/run_context.py` already provides disk-backed run identity and stale-run handling.
- `skills/go/SKILL.md` still contains a manual Bash bootstrap using `uuidgen`, `export`, `mkdir -p`, and `.claude/worktrees`, which does not match the Windows-native Python implementation.
- `skills/go/scripts/go-safe.sh` is also Bash-oriented and uses `uuidgen` as a fallback. It may remain as a compatibility artifact until active consumers are audited, but it must not remain the normative Windows entrypoint.
- The incident transcript shows `/go` setup commands being composed as long Bash/PowerShell blocks, triggering unavailable-command, malformed-path, directory-policy, and command-length failures before task execution.
- The existing `P:/.claude/hooks/PreToolUse.py` skill-first gate is intentional and should remain enforced; the fix is to make the `/go` invocation path call `Skill("go")` before any bootstrap tool call, not to weaken the gate.

## Non-Goals

- Do not redesign `/go` task acquisition, classification, worker dispatch, verification, review, PR-artifact, or continuation phases.
- Do not replace the existing run-state schema with a new state store.
- Do not remove the skill-first gate, delegation gate, Stop continuation gate, or worktree safety gate.
- Do not change the default dispatch from `pi`.
- Do not convert `/go` into a general cross-platform launcher.

## File Map

### Windows entry and bootstrap

- Create: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/go-safe.ps1` — short Windows-native wrapper that delegates to `orchestrate.py`.
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/go-safe.sh` — retain compatibility, remove its normative status, and add a clear Windows delegation note only if existing tests require the file.
- Create: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/record_go_baseline.py` — bounded baseline artifact writer so agents do not compose oversized inline shell commands.
- Create: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/go_paths.py` — the single source for Windows `/go` path defaults.

### Orchestrator defaults and documentation

- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/orchestrate.py` — centralize the Windows default worktree root and preserve the environment override.
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/worktree_safety.py` — use the same centralized default when no override is supplied.
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/SKILL.md` — remove the manual Bash bootstrap as the prescribed path and document the Windows-native entry.
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/CLAUDE.md` — document the source-of-truth relationship between the skill text, PowerShell wrapper, and Python orchestrator.

### Regression coverage

- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/tests/test_go_safe.py` — test Windows wrapper contract and no-POSIX bootstrap assumptions.
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/tests/test_orchestrate_dispatch.py` — test dispatch preservation and wrapper argument forwarding.
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/tests/test_run_context.py` — preserve run identity and stale-state behavior.
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/tests/test_worktree_lifecycle.py` — test root selection, retry idempotency, and existing-worktree safety.
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/tests/test_worktree_safety.py` — test the shared default-root contract.
- Create: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/tests/test_record_go_baseline.py` — test bounded baseline capture.
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/tests/test_windows_entrypoint.py` — test the PowerShell wrapper without invoking a real worker.

## Claim Ledger

| Claim | Type | Evidence | Falsifier | Action allowed |
|---|---|---|---|---|
| The Python orchestrator already owns worktree creation and run initialization | verified_fact | `orchestrate.py:create_worktree()` and `ensure_runtime_env()` | Active runtime invokes a different source path | Align docs/wrapper to the resolved runtime path |
| The skill documentation can send an executor down a non-Windows Bash path | verified_fact | `SKILL.md` contains `uuidgen`, `export`, `mkdir -p`, and `.claude/worktrees` instructions | Active cached skill differs and is proven authoritative | Update the authoritative source and cache only through release controls |
| A PowerShell wrapper can preserve `/go` behavior | hypothesis | Orchestrator exposes a normal CLI and owns environment setup | Wrapper changes argv, exit codes, or completion output in integration tests | Keep wrapper behind an opt-in checkpoint and investigate |
| Changing the default root to `P:/.worktrees` is behavior-safe | hypothesis | Existing `GO_WORKTREE_ROOT` override and worktree metadata are independent of root value | A golden test or active worktree inventory shows a required dependency on `P:/worktrees` | Keep `P:/worktrees` as default and use explicit configuration instead |
| The skill-first gate is not itself the component to remove | verified_fact | `PreToolUse.py` explicitly blocks non-`Skill` tools for pending slash intent | A live `/go` invocation calls Skill first but still blocks the first valid orchestrator call | Fix the gate integration or state identity, not the gate policy |

## Review Disposition and Safe Execution Order

The critical review identified two root-cause gaps and six tightening items. This revision accepts the failure-mode analysis, command-composition audit, worktree inventory, disk-backed retry tests, skill-first test clarification, positive documentation assertion, plugin checklist reference, and measurable success criteria. It does not add an arbitrary runtime command-length limit: the host tool parser can reject a command before `go-safe.ps1` or `orchestrate.py` starts, so the enforceable mitigation is to eliminate normative long inline commands and test the bounded entrypoints. It also does not delete `go-safe.sh` solely because the platform is Windows; Windows Git Bash and repository tests are still possible consumers and must be audited first.

The canonical execution order is:

| Order | Task | Gate before proceeding |
|---:|---|---|
| 1 | 0.5 failure matrix | Every technical failure has one mapped fix and one verification |
| 2 | 1 baseline | Active source/cache path and dirty state are revision-pinned |
| 3 | 4 bounded baseline script | Baseline capture works without source mutation |
| 4 | 3 worktree-root inventory/default | No active run is silently split between roots |
| 5 | 2 PowerShell wrapper | Wrapper forwards arguments and exit codes |
| 6 | 2A command-composition audit | Every authoritative setup path uses a bounded entrypoint |
| 7 | 5 documentation/compatibility decision | Windows source-of-truth docs and `go-safe.sh` disposition are explicit |
| 8 | 6 retry and skill-first coverage | Disk-backed resume and Skill-first invariants pass |
| 9 | 7 final verification | Metrics, tests, cache checklist, and rollback evidence pass |

Do not skip Tasks 0.5, 1, or 3 before changing the default root. If task numbering changes during implementation, update this table in the same change.

## Task 0.5: Classify the incident failure modes before changing code

**Files:**
- Create: `P:/tmp/go-windows11-failure-mode-matrix.json`
- Inspect: `P:/docs/superpowers/plans/2026-07-13-go-windows11-hardening.md`
- Inspect: the incident transcript supplied with this task

**Interfaces:**
- Produces a failure matrix with fields `failure_id`, `observed_evidence`, `failure_class`, `current_owner`, `planned_fix`, `verification`, and `unmapped`.
- Does not change source or runtime configuration.

- [ ] Record each distinct technical failure from the incident transcript in this matrix:

| Failure ID | Observed evidence | Failure class | Planned fix | Verification |
|---|---|---|---|---|
| `FM-01` | `uuidgen: command not found` and Bash `export`/`mkdir -p` bootstrap | Wrong shell/platform bootstrap | Tasks 2, 4, and 5 make PowerShell/Python the normative path | `go-safe.ps1 --help` and baseline-script tests pass on Windows 11 |
| `FM-02` | Directory policy received `P:\$GO_STATE_DIR` | Malformed state-path interpolation plus policy rejection | Tasks 2 and 4 stop manual state construction; `orchestrate.py` owns state paths | Preflight writes a valid artifact path or returns a structured failure |
| `FM-03` | Command parser reported maximum supported length of 965 bytes | Host command-composition limit | Task 2A replaces long inline blocks with checked-in scripts; no post-start length guard is claimed | All normative `/go` examples invoke a short script or Python command |
| `FM-04` | Skill-first gate required `Skill("go")` before Bash | Correct policy gate reached through an invalid sequence | Task 6 tests the valid Skill-first sequence and preserves the block for invalid sequences | Integration test shows Skill first allows the subsequent orchestrator call |
| `FM-05` | Manual worktree path differed from the Python orchestrator's configured root | Finding: documentation/runtime source divergence | Tasks 3 and 5 centralize and document `P:/.worktrees` | Source and active-cache path audit agree, or release is held |

- [ ] Classify transcript artifacts such as user interruption, repeated display blocks, and model apologies as observational context rather than technical failures unless a reproducible runtime mechanism is found.
- [ ] Stop if any technical failure lacks one planned fix and one executable verification. This matrix is the required epistemic checkpoint before implementation.

## Task 1: Freeze the active `/go` source, cache, and behavior baseline

**Files:**
- Test evidence: `P:/tmp/go-windows11-hardening-baseline.json`
- Inspect: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/SKILL.md`
- Inspect: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/orchestrate.py`
- Inspect: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/run_context.py`
- Inspect: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/worktree_safety.py`
- Inspect: `C:/Users/brsth/.claude/plugins/cache/local/cc-skills-sdlc/`

**Interfaces:**
- Produces a revision-pinned source/cache/registration report.
- Does not change runtime behavior.

- [ ] Record the package repository root, current branch, HEAD SHA, status, active worktrees, and nested repository status from PowerShell:

```powershell
$repo = 'P:\packages\.claude-marketplace\plugins\cc-skills-sdlc'
git -C $repo rev-parse --show-toplevel
git -C $repo rev-parse HEAD
git -C $repo status --short
git -C $repo worktree list --porcelain
```

- [ ] Locate the active installed `cc-skills-sdlc` cache path from the actual settings/plugin registry. Do not infer it from a version number in old transcripts.
- [ ] Capture source hashes for `SKILL.md`, `orchestrate.py`, `run_context.py`, `worktree_safety.py`, `go-safe.sh`, and the active cache copies.
- [ ] Run the existing focused baseline suites:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\skills\go\tests\test_go_safe.py -q
python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\skills\go\tests\test_orchestrate_dispatch.py -q
python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\skills\go\tests\test_run_context.py -q
python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\skills\go\tests\test_worktree_lifecycle.py -q
```

- [ ] Stop if the active runtime resolves to a cache copy whose source revision is not identified. The worker must fix the canonical package source first and defer cache release to the final checkpoint.
- [ ] Commit the baseline report only if the repository’s existing evidence policy requires a tracked artifact; otherwise retain it under `P:\tmp` and include its path in the handoff.

## Task 2: Add the Windows-native wrapper without changing the orchestrator

**Files:**
- Create: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/go-safe.ps1`
- Create: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/tests/test_windows_entrypoint.py`

**Interfaces:**
- PowerShell entrypoint accepts all `/go` arguments unchanged and returns the Python orchestrator exit code.
- The wrapper does not create state, choose a run ID, create a worktree, or reinterpret task arguments.

- [ ] Write the failing wrapper contract test. It must assert that the wrapper source contains no `uuidgen`, `export`, `mkdir -p`, `/tmp`, `cut`, or `tr`, and that it invokes `orchestrate.py` through an argument array.
- [ ] Implement the wrapper with this behavior:

```powershell
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $ArgumentList
)

$ErrorActionPreference = 'Stop'
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$orchestrator = Join-Path $scriptRoot 'orchestrate.py'
if (-not (Test-Path -LiteralPath $orchestrator -PathType Leaf)) {
    throw "Missing /go orchestrator: $orchestrator"
}

$python = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $python) {
    throw 'Python is required to run /go on Windows 11.'
}

& $python.Source $orchestrator @ArgumentList
exit $LASTEXITCODE
```

- [ ] Run the wrapper tests and verify argument preservation with a mocked Python executable; expected result is the exact argv sequence reaches `orchestrate.py` and the wrapper returns the child exit code.
- [ ] Verify the `--help` smoke is side-effect-free from the actual source: `argparse` handles `--help` before `main()` calls `orchestrate()`, so the command must exit `0` without creating a run, state directory, worktree, or worker process. If the active cache differs from this source behavior, stop and reconcile the source/cache revision before changing the wrapper.
- [ ] Add a PowerShell smoke command that invokes `--help` only; do not dispatch a worker:

```powershell
& 'P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\skills\go\scripts\go-safe.ps1' --help
if ($LASTEXITCODE -ne 0) { throw "go-safe.ps1 --help failed with $LASTEXITCODE" }
```

- [ ] Do not delete or rewrite `go-safe.sh` in this task. Existing consumers must remain available until Task 5’s consumer audit and compatibility decision pass.

## Task 2A: Remove normative long inline command composition

**Files:**
- Inspect: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/SKILL.md`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/GO-QUICK-REFERENCE.md`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/IMPLEMENTATION-GUIDE.md`
- Create: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/tests/test_command_composition_docs.py`

**Interfaces:**
- Documentation examples use one bounded PowerShell script, one Python entrypoint, or one existing orchestrator command per code block.
- No documentation step requires an agent to assemble environment setup, hashing, worktree creation, and dispatch into one inline command.

- [ ] Search every `/go` guide and reference for multi-command setup blocks, direct `git worktree add` recipes, manual `TERMINAL_ID`/`RUN_ID` construction, and inline baseline/hash loops:

```powershell
rg -n -S "uuidgen|export |mkdir -p|git worktree add|TERMINAL_ID=|RUN_ID=|GO_STATE_DIR=|Get-FileHash|ConvertTo-Json" P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\skills\go
```

- [ ] Classify every hit as authoritative instruction, compatibility note, test fixture, or historical evidence. Do not silently rewrite historical evidence.
- [ ] Replace authoritative multi-command setup with either `go-safe.ps1`, `record_go_baseline.py`, `orchestrate.py`, or `worktree_safety.py` using the exact interfaces defined in this plan.
- [ ] Write a positive documentation test that requires each authoritative Windows setup section to contain exactly one wrapper/orchestrator invocation and forbids an authoritative block from manually assigning run identity or creating a worktree.
- [ ] Do not add a generic command-length guard to `/go`: the host parser may reject an oversized tool call before the child process starts, so only command composition in the checked-in workflow can be controlled here.
- [ ] Run the documentation audit test and repeat the search. Any remaining authoritative multi-command block is an explicit stop condition.

## Task 3: Centralize the Windows worktree-root default

**Files:**
- Create: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/go_paths.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/orchestrate.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/worktree_safety.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/tests/test_worktree_lifecycle.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/tests/test_worktree_safety.py`

**Interfaces:**
- Add one shared constant or helper named `DEFAULT_GO_WORKTREE_ROOT` with value `Path('P:/.worktrees')` in the package-owned helper chosen by the existing import topology.
- `GO_WORKTREE_ROOT` remains the highest-precedence override.

The helper is `go_paths.py` and has this exact interface:

```python
from pathlib import Path
import os

DEFAULT_GO_WORKTREE_ROOT = Path('P:/.worktrees')

def go_worktree_root() -> Path:
    return Path(os.environ.get('GO_WORKTREE_ROOT', str(DEFAULT_GO_WORKTREE_ROOT)))
```

- [ ] Write failing tests for: no override selects `P:/.worktrees`; `GO_WORKTREE_ROOT=P:/worktrees` selects the override; an existing worktree is never moved; and two distinct run IDs receive distinct paths.
- [ ] Before changing the default, inventory both the filesystem and Git metadata for the old root. Run this from PowerShell and save the output with the baseline:

```powershell
$oldRoot = 'P:\worktrees'
Write-Output "=== old-root directories ==="
if (Test-Path -LiteralPath $oldRoot) {
    Get-ChildItem -LiteralPath $oldRoot -Directory | Select-Object -ExpandProperty FullName
} else {
    Write-Output '(directory absent)'
}
Write-Output "=== parent-repository worktrees ==="
git -C P:\ worktree list --porcelain
Write-Output "=== cc-skills-sdlc worktrees ==="
git -C P:\packages\.claude-marketplace\plugins\cc-skills-sdlc worktree list --porcelain
Write-Output "=== active go state references ==="
rg -n -S 'P:[/\\]worktrees|worktree.*P:[/\\]worktrees|"worktree"' P:\.claude\.artifacts P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\.go-orphan-quarantine 2>$null
```

- [ ] Classify every old-root worktree as active, completed, orphaned, or unrelated. If an active `/go` run references `P:/worktrees`, stop and retain `GO_WORKTREE_ROOT=P:/worktrees` for that run; do not move it while changing the default for future runs. If the old root contains no active worktree, record that fact before proceeding.
- [ ] Add `go_paths.py` with the interface above and tests for the default and override. Do not create a second copy of the default in either consumer.
- [ ] Implement the smallest shared-default change. Preserve branch naming, target-repository resolution, lifecycle registration, and the `git worktree add` argument list.
- [ ] Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\skills\go\tests\test_worktree_lifecycle.py P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\skills\go\tests\test_worktree_safety.py -q
```

- [ ] Run a disposable real worktree smoke in a dedicated temporary repository, not `P:`:

```powershell
$sandbox = Join-Path $env:TEMP ('go-worktree-test-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $sandbox | Out-Null
git -C $sandbox init
Set-Content -LiteralPath (Join-Path $sandbox 'README.md') -Value 'go worktree smoke'
git -C $sandbox add README.md
git -C $sandbox -c user.name='go-test' -c user.email='go-test@example.invalid' commit -m 'baseline' | Out-Null
$worktreeRoot = Join-Path $sandbox '.worktrees'
$stateDir = Join-Path $sandbox '.state'
python P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\skills\go\scripts\worktree_safety.py --state-dir $stateDir start --task-id GO-WIN-SMOKE --title 'Windows worktree smoke' --objective 'Verify root selection' --repo-root $sandbox --worktree-root $worktreeRoot --dry-run
Remove-Item -LiteralPath $sandbox -Recurse -Force
```

## Task 4: Replace the manual baseline/state bootstrap with a bounded script

**Files:**
- Create: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/record_go_baseline.py`
- Create: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/tests/test_record_go_baseline.py`

**Interfaces:**
- Command: `python record_go_baseline.py --repo P:/ --output P:/tmp/go-windows11-hardening-baseline.json`.
- Output is JSON containing `repo`, `branch`, `head`, `status`, `worktrees`, `target_hashes`, `terminal_id`, and `created_at`.
- The script is read-only with respect to source code and writes only the requested output artifact.

- [ ] Write failing tests for a temporary Git repository: output includes HEAD/status/worktrees; target hashes are SHA-256; missing optional target files are recorded as `missing`; output parent directories are created; source files are not modified.
- [ ] Implement the script using `pathlib`, `subprocess.run([...], check=False, capture_output=True, text=True)`, and `hashlib.sha256`; do not invoke a shell or depend on Bash utilities.
- [ ] Define the default target list in code as the exact current `/go` authority files:

```python
DEFAULT_TARGETS = (
    'packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/SKILL.md',
    'packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/orchestrate.py',
    'packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/run_context.py',
    'packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/worktree_safety.py',
    'packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/go-safe.sh',
)
```

- [ ] Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\skills\go\tests\test_record_go_baseline.py -q
python P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\skills\go\scripts\record_go_baseline.py --repo P:\ --output P:\tmp\go-windows11-hardening-baseline.json
Get-Content -LiteralPath P:\tmp\go-windows11-hardening-baseline.json -Raw | ConvertFrom-Json | Select-Object repo,branch,head,created_at
```

- [ ] Replace the plan’s manual long inline hash/state command with this script in the `/go` documentation. The worker must not construct a multi-command bootstrap string longer than the host command parser limit.

## Task 5: Align `/go` documentation and compatibility scripts

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/SKILL.md`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/CLAUDE.md`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/go-safe.sh` only if the compatibility note requires a source change
- Test: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/tests/test_skill_metadata.py`
- Test: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/tests/test_go_safe.py`

**Interfaces:**
- The normative Windows invocation is `go-safe.ps1`, which delegates directly to `orchestrate.py`.
- `SKILL.md` must describe the Python orchestrator as the authority for IDs, state, preflight, worktrees, and dispatch.

- [ ] Write a failing documentation test that locates the authoritative Windows environment/setup section and requires exactly one PowerShell code block whose executable entry is `go-safe.ps1`; require that the section states that `orchestrate.py` owns IDs, state, and worktrees. Do not use a global token deny-list as the primary test, because compatibility notes and historical evidence may legitimately mention old commands.
- [ ] Replace the required environment block with a Windows-native block:

```powershell
$env:GO_WORKTREE_ROOT = 'P:/.worktrees'
& 'P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\skills\go\scripts\go-safe.ps1' --help
```

- [ ] Document that callers normally invoke the `/go` skill, not the wrapper directly; the wrapper is for deterministic Windows diagnostics and tests.
- [ ] Document that `orchestrate.py` owns terminal ID, run ID, artifact directory, plan/task acquisition, worktree creation, dispatch, and completion output. The wrapper must not duplicate those responsibilities.
- [ ] Resolve the `go-safe.sh` disposition with an explicit consumer audit:

```powershell
rg -n -S "go-safe\.sh|bash.*go-safe|sh.*go-safe" P:\packages\.claude-marketplace\plugins\cc-skills-sdlc P:\.claude C:\Users\brsth\.claude\settings.json 2>$null
```

  If the audit finds no active Windows invocation and no test requires the file as a compatibility fixture, delete `skills/go/scripts/go-safe.sh` and its dedicated tests, then rerun the source search. If it finds an active Windows Git-Bash or test consumer, retain the script as compatibility-only, document that PowerShell is normative, and add a test covering that consumer. Do not keep the file solely because a dead-code test asserts its presence.
- [ ] Run the documentation and compatibility tests.

## Task 6: Add idempotent retry and skill-first integration coverage

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/tests/test_worktree_lifecycle.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/tests/test_run_context.py`
- Modify: `P:/.claude/hooks/tests/test_skill_enforcer_gate_integration.py`
- Inspect only: `P:/.claude/hooks/PreToolUse.py`

**Interfaces:**
- Existing `/go` state markers and run-context files remain authoritative.
- A retry with the same active run ID must resume or report the existing state rather than create a duplicate worktree or silently mint a conflicting run.

- [ ] Add a test that writes a valid `current-run_{terminal_id}.json` and `active-task_{run_id}.json` to a temporary state directory, starts two independent Python processes with different environment dictionaries, and asserts `run_context.resolve(state_dir)` recovers the same disk-authoritative run. Do not rely on environment variables surviving across PowerShell or Bash tool calls.
- [ ] Add a worktree test that retries after a simulated `git worktree add` failure and asserts no orphaned state is reported as active.
- [ ] Add a skill-first integration test for the sequence: pending `/go` intent → first `Skill('go')` call allowed → subsequent `go-safe.ps1 --help` or orchestrator call allowed. Also test that a non-Skill Bash call remains blocked while the intent is pending.
- [ ] Treat the skill-first test as an invariant test, expected to pass without changing `_SKILL_FIRST_ALLOWED`, pending-intent identity, or block semantics. If it fails, classify whether the failure is source/cache divergence, state-path identity, or an actual gate defect before changing code.
- [ ] Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\skills\go\tests\test_run_context.py P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\skills\go\tests\test_worktree_lifecycle.py -q
python -m pytest P:\.claude\hooks\tests\test_skill_enforcer_gate_integration.py -q
```

## Task 7: Verification, rollout checkpoint, and rollback

**Files:**
- Inspect all changed files from Tasks 1–6.
- Create: `P:/tmp/go-windows11-hardening-final.json` only if the evidence workflow requires an external handoff artifact.

**Success metrics:**
- Four reproducible technical failure fixtures (`FM-01` through `FM-04`) complete with the intended diagnostic or successful preflight and no unclassified failure.
- Ten consecutive no-worker Windows preflight invocations complete without shell-language, malformed-state-path, or command-composition failure.
- Ten consecutive disk-backed retry/resume invocations reuse the same run context and create zero duplicate active worktrees.
- Existing focused `/go` tests remain passing, and completion-token output is byte-for-byte unchanged for the established fixtures.

- [ ] Run all focused suites:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\skills\go\tests\test_go_safe.py P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\skills\go\tests\test_windows_entrypoint.py P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\skills\go\tests\test_record_go_baseline.py -q
python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\skills\go\tests\test_orchestrate_dispatch.py P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\skills\go\tests\test_run_context.py P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\skills\go\tests\test_worktree_lifecycle.py P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\skills\go\tests\test_worktree_safety.py -q
python -m pytest P:\.claude\hooks\tests\test_skill_enforcer_gate_integration.py -q
git -C P:\packages\.claude-marketplace\plugins\cc-skills-sdlc diff --check
```

- [ ] Run a no-worker preflight through the Windows wrapper and verify it exits cleanly without creating a worker worktree:

```powershell
$env:GO_WORKTREE_ROOT = 'P:/.worktrees'
& 'P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\skills\go\scripts\go-safe.ps1' --preflight-only --prompt 'verify the go Windows bootstrap without changing files'
$code = $LASTEXITCODE
Remove-Item Env:GO_WORKTREE_ROOT
if ($code -ne 0) { throw "Windows /go preflight failed with exit code $code" }
```

- [ ] Verify unchanged behavior for the existing completion tokens by testing the orchestrator’s established fixtures; no token names may change.
- [ ] Re-run the package mutation checklist from `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/CLAUDE.md`: source/cache rebuild or sync is step 3 and final commit-scope inspection is step 6. Record both results; do not claim runtime activation from source tests alone.
- [ ] Search active settings and package source for direct invocation of `go-safe.sh`, the old `.claude/worktrees` path, and manual `uuidgen` bootstrap instructions. Classify every hit as active, compatibility-only, test fixture, cache, or stale documentation.
- [ ] At the human checkpoint, decide whether to set `GO_WORKTREE_ROOT=P:/.worktrees` in the active workspace environment. Do not edit user settings or release the plugin cache in the same change.
- [ ] If rollback is required, revert only the changed canonical package files in the dedicated worktree, unset `GO_WORKTREE_ROOT`, and re-run the baseline focused suites. Do not delete existing worktrees or state artifacts.
- [ ] Report the final source revision, active cache revision, wrapper path, worktree root, tests, intentionally untouched files, and any remaining cache-release requirement.

## Completion Criteria

The plan is complete only when:

- The Windows wrapper forwards arguments and exit codes without duplicating orchestration logic.
- The canonical Python orchestrator remains the sole owner of run IDs, state, worktrees, task selection, dispatch, and completion tokens.
- The failure matrix contains no unmapped technical failure, and every mapped fix has an executable verification result.
- The documented bootstrap contains no normative POSIX commands.
- `P:/.worktrees` is selected when no override is present, while an explicit `GO_WORKTREE_ROOT` override still works.
- Repeated initialization/resume does not create duplicate active runs or worktrees.
- The skill-first gate still blocks pre-Skill mutation and allows the valid Skill-first sequence.
- Focused tests and `git diff --check` pass.
- No active cache or production settings are changed without the explicit human checkpoint.
