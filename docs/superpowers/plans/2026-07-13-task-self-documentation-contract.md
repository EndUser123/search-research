# Task Self-Documentation Contract Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make task self-documentation useful for defect, design, research, decision, implementation, feature, and maintenance work without blocking valid non-defect tasks or allowing cross-terminal task-state contamination.

**Architecture:** Establish one package-owned SDLC task-documentation contract and parser. Keep `TaskCreate` non-blocking with concise advice, persist the parsed contract in the existing terminal-scoped task record, and make completion enforcement consume that persisted record rather than the transient `TaskUpdate` payload. Unknown and legacy tasks remain advisory during migration; explicitly typed tasks receive kind-specific validation.

**Tech Stack:** Python 3.14, pytest, Claude Code PreToolUse/PostToolUse/Stop hooks, JSON task state, package router dispatch.

## Global Constraints

- `P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/` is the canonical owner of SDLC task-documentation policy and validation code.
- `P:/.claude/hooks/` may retain only a thin compatibility adapter while the active dispatcher is migrated; it must not contain a second validator implementation.
- `cc-aca-observability` may record and advise on task metadata but must not own or redefine the SDLC contract.
- Do not add undocumented fields to the native `TaskCreate` or `TaskUpdate` tool schema. Task kind is carried in a documented description heading and persisted by the tracker.
- Do not use `P:/.claude/state/competence/last_task_type.json` as task-documentation authority: it is global, stale-prone, and currently backed by a missing registry file.
- Preserve existing terminal-scoped task-state identity and locking. Never read another terminal's task record to validate the current task.
- Do not edit `C:/Users/brsth/.claude/` files. Any runtime registration change must be made in the package source or the approved workspace settings source after an explicit checkpoint.
- The selected registration plan is workspace-owned: after a shadow smoke proves the package route, add a narrow `TaskCreate|TaskUpdate` matcher to `P:/.claude/settings.json` and remove those two entries from the local dispatcher in the same approved change. Do not add the package router to a broad `.*` matcher and do not edit the user settings file.
- Preserve all unrelated dirty changes in the current worktree. Use atomic `git mv` operations for any source relocation.
- Do not remove the existing `2026-07-12-task-lifecycle-hardening` work. Treat this plan as a dependent follow-up for the self-documentation contract.
- Before claiming completion, run focused contract tests, registered PreToolUse/PostToolUse/Stop smoke tests, and `git diff --check`.

## Current Authority Findings

- `P:/.claude/hooks/PreToolUse.py:909-914` dispatches `PreToolUse_task_self_doc_gate.py` for `TaskCreate` and `TaskUpdate`.
- `P:/.claude/hooks/PreToolUse_task_self_doc_gate.py:100-115` blocks `TaskCreate` using a lexical defect schema.
- `P:/.claude/hooks/__lib/task_self_doc_validator.py:27-58` defines the shared defect-oriented indicator lists.
- `P:/packages/.claude-marketplace/plugins/cc-aca-observability/__lib/posttooluse/task_tracker_hook.py:450-491` persists task records in terminal-scoped JSON files.
- `P:/packages/.claude-marketplace/plugins/cc-aca-observability/__lib/posttooluse/task_tracker_hook.py:791-810` emits a second advisory using the same validator.
- `P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/hooks/stop/Stop_task_completion_gate.py:198-225` validates persisted task data at Stop, but currently imports the local validator and allows missing state.
- `P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/__lib/router.py:29-43` does not dispatch the self-documentation gate, while the local PreToolUse dispatcher does. Registration must be consolidated only after the live settings merge is verified.
- The live matcher scope matters: `C:/Users/brsth/.claude/settings.json` invokes the `cc-aca-sdlc` PreToolUse router only for `^(?:Edit|Write|MultiEdit)$`, while `P:/.claude/settings.json` invokes the local `PreToolUse.py` under a broad `.*` matcher. Therefore a package hook added only to `cc-aca-sdlc/__lib/router.py` would not receive `TaskCreate` or `TaskUpdate`. The approved workspace-owned route is a separate narrow `TaskCreate|TaskUpdate` matcher in `P:/.claude/settings.json`, followed by removal of the corresponding local entries.
- The current `cc-aca-sdlc` router runs its TDD hook list for every event it receives. Both existing TDD hooks currently no-op for non-file tools, but the refactor must make that behavior explicit with tool-aware task/file dispatch (or a separately tested task-hook list), so a task event cannot acquire TDD side effects by accident.
- `P:/.claude/hooks/competence/task_type_registry.py:27` points to `P:/.claude/hooks/competence/templates/task_type_registry.json`, which is absent. Its fallback state writer at `P:/.claude/hooks/UserPromptSubmit_modules/competence_injector.py:314-340` writes one global `last_task_type.json`; neither is a safe current authority for task completion.
- `P:/.claude/settings.json` runs both the local `P:/.claude/hooks/PostToolUse.py` registry and the package `cc-aca-observability` PostToolUse router; the local registry imports `P:/.claude/hooks/posttooluse/task_tracker_hook.py`, while the package router imports its package copy. This is a duplicate task-tracker/advisory path and must be resolved before deleting the shared local validator.
- `C:/Users/brsth/.claude/settings.json` separately runs the package `cc-aca-sdlc` PreToolUse and Stop routers. `P:/.claude/settings.json` separately runs the legacy `cc-skills-sdlc` Stop router for `/go`. These are distinct routes; the `/go` continuation gate must not be removed as part of this refactor.
- The current worktree has unrelated/concurrent modifications in the local PreToolUse files, task tests, and both observability task-tracker/router files. Those files are not safe edit targets until their baseline and ownership are reconciled.
- The nested `cc-skills-sdlc` repository is itself dirty in `skills/task/SKILL.md`, `skills/task/references/implementation-details.md`, `skills/task/scripts/task_receipt.py`, `skills/task/scripts/task_verify.py`, and its tests. Those changes are concurrent work, not part of this refactor baseline.
- The complete current validator-consumer set is: local PreToolUse gate, local PostToolUse task tracker, package observability task tracker, package ACA-SDLC Stop gate, and local validator tests/catalog. The package `cc-skills-sdlc` task docs are additional stale documentation consumers.
- The global hooks audit is not a clean completion gate at this revision: it reports unrelated baseline failures in registration, syntax, dangling paths, and state GC. Use it for inventory only; completion evidence must use targeted dispatch/import/source-consumer checks for this feature.
- The local `PreToolUse.py` preserves an `advisory` response from a child hook, but its logger is configured with a file handler. The plan must not claim that an advisory is user-visible until a bounded registered subprocess smoke proves the actual Claude Code rendering path; otherwise the contract must rely on persisted state/Stop diagnostics rather than an invisible warning.
- The likely local rendering defect is pre-existing: `PreToolUse.py:1421` sends the advisory through `_logger.warning`, whose configured file handler is not equivalent to `sys.stderr.write()`. Changing that line to an explicitly supported stderr path could repair local advisory visibility, but it is outside this refactor because the selected active task route is the package hook via workspace settings. Track it as a separate local-dispatcher fix, not as an implicit prerequisite here.

## Claim Ledger for This Plan

| Claim | Type | Evidence | Verification method | Confidence | Falsifier | Action allowed |
|---|---|---|---|---|---|---|
| The current user-settings matcher does not send `TaskCreate`/`TaskUpdate` to the package SDLC router | verified_fact | `C:/Users/brsth/.claude/settings.json` uses `^(?:Edit|Write|MultiEdit)$`; P workspace settings route task events through local `PreToolUse.py` | Re-read both settings and run a registered task-event shadow smoke | high | A live task event reaches the package router through an existing matcher | Use the narrow workspace-owned matcher plan; revise if falsified |
| The old self-documentation gate falsely applies defect wording to an untyped design/research request | verified_fact | Current local gate and reproducible incident-shaped payload | Invoke the old route with the fixture and capture its decision/reason | high | Old route allows the fixture without defect-specific diagnostics | Preserve as regression evidence, not as permission to retain lexical validation |
| The package observability tracker can be safely extended without losing concurrent lifecycle changes | hypothesis | Current target file is dirty and its public state/lock seam has not yet been proven | Inspect the dirty diff and public APIs in the dedicated worktree | medium | No safe extension seam or conflict-free integration exists | Gather evidence or use the blocked fallback; do not edit blindly |
| A PreToolUse advisory is visible to the user | hypothesis | Local dispatcher preserves the field, but logger configuration includes a file handler | Registered harmless subprocess smoke capturing all output surfaces | low | No user-visible advisory appears | Use persisted-state/Stop diagnostics and keep creation non-blocking |
| Completion evidence is enforced by the new contract | design_requirement | Current table is not enforcement; revised contract defines phase-complete content rules | Unit tests for empty/placeholder/real evidence plus registered Stop smoke | pending | Placeholder completion passes or valid evidence fails | Fix parser/Stop consumer before any enforcement rollout |

## Safety Prerequisites Before Implementation

The implementation must not begin in the dirty parent worktree or the dirty nested `cc-skills-sdlc` repository. Create or use a dedicated worktree under `P:/.worktrees/` after recording the current parent revision, nested-repository revision, and exact dirty-file list. Do not copy the current dirty files into the worktree as if they were an authoritative baseline; either wait for the concurrent task-lifecycle changes to land or explicitly merge their revision into the refactor worktree.

Before the first code edit, produce a dispatch table with one row per event and these fields: settings file, matcher, command, resolved source path, package router list, cache path, and observed smoke result. The required rows are:

| Event | Required authority decision |
|---|---|
| PreToolUse `TaskCreate`/`TaskUpdate` | exactly one documentation-policy decision path; local router is compatibility only |
| PostToolUse `TaskCreate`/`TaskUpdate` | exactly one task-state writer; observability is the writer, local registry is removed or narrowed |
| Stop completion | exactly one self-documentation completion gate; `/go` continuation remains separate |

The add/remove gate is: add the package implementation and direct tests first; prove the new route; run both old and new routes in a bounded smoke harness; remove the old registration; re-run the same smoke harness; only then remove old source files. A source search alone is insufficient because the settings and versioned cache can retain a live copy.

## Contract

The native task description remains the transport because the native task schema is not extended. The first non-empty line may declare a kind:

```text
Task kind: defect|feature|design|research|decision|implementation|maintenance
```

The parser returns `unknown` when the heading is absent, malformed, or unsupported. It never guesses a strict kind from arbitrary prose.

The persisted contract has this exact shape:

```json
{
  "contract_version": 1,
  "task_kind": "design",
  "contract_source": "description_heading",
  "contract_status": "valid|invalid|unknown|legacy",
  "missing_fields": [],
  "parsed_at": "2026-07-13T00:00:00+00:00"
}
```

`TaskKind` never contains `legacy`; legacy is provenance of a persisted record. The status mapping is:

| Situation | `task_kind` | `contract_status` |
|---|---|---|
| Explicit supported heading with all required content valid for the phase | supported kind | `valid` |
| Explicit supported heading with missing, empty, or placeholder content | supported kind | `invalid` |
| Missing, malformed, or unsupported heading on a new task | `unknown` | `unknown` |
| Existing record has no `contract_version` | value inferred only from the record, otherwise `unknown` | `legacy` |

There is no valid `unknown`/`legacy` combination: `legacy` describes record age, while `unknown` describes an untyped new description. Unknown and legacy records are advisory-only during migration.

Required fields by kind:

| Kind | Required headings | Completion evidence |
|---|---|---|
| `defect` | `Problem`, `Situation`, `Symptom` | `Verification` or linked evidence |
| `feature` | `Goal`, `Scope`, `Acceptance` | `Verification` or acceptance evidence |
| `design` | `Goal`, `Context`, `Decision` | decision/rationale recorded |
| `research` | `Question`, `Scope`, `Evidence` | sources or evidence recorded |
| `decision` | `Decision`, `Options`, `Rationale` | chosen decision recorded |
| `implementation` | `Goal`, `Scope`, `Verification` | verification recorded |
| `maintenance` | `Change`, `Scope`, `Verification` | verification recorded |
| `unknown` (or a legacy record) | subject and non-empty description only | advisory only during migration |

Headings are structural (`^Heading:\s*\S`) and case-insensitive. Keyword presence in arbitrary prose is not sufficient. The parser must return field names and line-independent diagnostics so every hook renders the same message.

For each required heading, the parser stores the text after the first matching heading until the next recognized heading. Creation requires every required field to be non-empty. Completion additionally rejects content shorter than the contract minimum (8 non-whitespace characters) and obvious placeholders (`TBD`, `TODO`, `N/A`, `unknown`, `to be determined`, case-insensitive). Completion evidence is therefore enforced by content validation, not merely displayed in a table. The minimum and placeholder set are named constants covered by tests.

Performance and concurrency requirements: parsing is linear in description size, one-pass over at most 64 KiB of description text, and performs no model calls, subprocesses, or network access. A description over 64 KiB fails open with an `description_too_large` advisory and is not blocked by documentation policy. State writes use the existing terminal-scoped lock and timeout behavior; Stop re-reads state for each event and does not use an in-process cache. Add a two-terminal concurrent write test and a bounded parser timing smoke for the 64 KiB boundary.

## File Map

### Canonical policy and parser

- Create: `P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/__lib/task_documentation.py`
- Test: `P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/tests/test_task_documentation.py`

### Hook adapters and lifecycle consumers

- Create: `P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/hooks/pretool/PreToolUse_task_self_doc_gate.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/hooks/stop/Stop_task_completion_gate.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-aca-observability/__lib/posttooluse/task_tracker_hook.py`
- Modify: `P:/.claude/hooks/posttooluse/__init__.py` to retire the duplicate local task-tracker registration after the package route is proven
- Modify: `P:/.claude/hooks/posttooluse/task_tracker_hook.py` as a compatibility adapter or staged retirement target
- Modify: `P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/__lib/router.py`
- Modify: `P:/.claude/hooks/PreToolUse_task_self_doc_gate.py` as a compatibility adapter only
- Modify: `P:/.claude/hooks/__lib/task_self_doc_validator.py` as a compatibility import/alias only, then remove it after the migration gate passes

### Registration and regression coverage

- Modify: `P:/.claude/settings.json` only at the explicit runtime-registration checkpoint to add the narrow `TaskCreate|TaskUpdate` package route
- Modify: `P:/.claude/hooks/PreToolUse.py` to remove the old local validator from active dispatch after the package route is proven
- Modify: `P:/.claude/hooks/tests/test_task_hooks.py`
- Modify: `P:/.claude/hooks/tests/test_task_self_doc_gate.py`
- Create: `P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/tests/test_task_documentation_router.py`
- Create: `P:/packages/.claude-marketplace/plugins/cc-aca-observability/__lib/posttooluse/tests/test_task_contract_persistence.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/CLAUDE.md`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-aca-observability/CLAUDE.md`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/task/SKILL.md`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/task/references/implementation-details.md`

## Task 1: Freeze the live dispatch and state authority

**Files:**
- Test: `P:/.claude/hooks/tests/test_task_hooks.py`
- Test: `P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/tests/test_task_documentation_router.py`
- Inspect: `P:/.claude/hooks/PreToolUse.py`, `P:/.claude/hooks/PostToolUse.py`, `P:/.claude/hooks/posttooluse/__init__.py`, `P:/.claude/hooks/dispatch_manifest.json`, `P:/.claude/settings.json`, `C:/Users/brsth/.claude/settings.json`, `cc-skills-sdlc/__lib/router.py`, `cc-aca-sdlc/__lib/router.py`, and both installed cache paths

**Interfaces:**
- Produces a revision-pinned dispatch matrix for `TaskCreate`, `TaskUpdate`, PostToolUse tracking, and Stop completion.
- Does not change runtime behavior.

- [ ] Write a registration test that imports `P:/.claude/hooks/PreToolUse.py` and asserts the old local entry is present before migration.
- [ ] Write a package-router test that asserts the self-documentation hook is absent before migration and records the intended new entry.
- [ ] Write a duplicate-route test that identifies the local PostToolUse task tracker and package observability task tracker as separate consumers before migration.
- [ ] Record the registration decision explicitly: the package `cc-aca-sdlc` router remains on the existing user-settings `Edit|Write|MultiEdit` route; a new workspace-settings matcher `^(?:TaskCreate|TaskUpdate)$` invokes the same package router for task events; the broad local `.*` route remains for other tools only.
- [ ] Add a shadow/fixture invocation for the proposed task matcher before changing settings. It must show the package task hook receives `TaskCreate` and `TaskUpdate`, while the existing TDD hooks return allow without TDD diagnostics. Do not treat direct module invocation as proof of registration.
- [ ] In the implementation checkpoint, make the `P:/.claude/settings.json` narrow matcher addition and removal of `TaskCreate`/`TaskUpdate` from `P:/.claude/hooks/PreToolUse.py` one atomic change. Do not edit `C:/Users/brsth/.claude/settings.json` and do not attach `cc-aca-sdlc` to the broad `.*` matcher.
- [ ] Verify `cc-aca-sdlc` source and cache hashes, and run the cache tool with its explicit marketplace root:

```powershell
python P:\packages\.claude-marketplace\plugins\cc-skills-utils\scripts\plugin-audit-and-fix.py --marketplace-root P:\packages\.claude-marketplace --sync-dry-run cc-aca-sdlc
python P:\packages\.claude-marketplace\plugins\cc-skills-utils\scripts\plugin-audit-and-fix.py --marketplace-root P:\packages\.claude-marketplace --sync-dry-run cc-aca-observability
```

- [ ] Record the pre-edit hashes and dirty status for every target file. If a target is dirty, do not overwrite it; reconcile the concurrent change first.
- [ ] Record the nested `cc-skills-sdlc` repository status separately; its task documentation edits must be merged or excluded deliberately before updating those docs.
- [ ] Run:

```powershell
python -m pytest P:\.claude\hooks\tests\test_task_hooks.py -q
python P:\.claude\scripts\hooks_audit.py --packages P:\packages\.claude-marketplace\plugins
```

- [ ] Stop and update the dispatch matrix if both settings sources or a generated cache register the same hook more than once.
- [ ] Stop if the package router cannot distinguish task and file-tool hook lists without running TDD policy on task events; add a tool-aware dispatch seam and its regression test before activating the route.

## Task 2: Build the package-owned typed contract

**Files:**
- Create: `P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/__lib/task_documentation.py`
- Test: `P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/tests/test_task_documentation.py`

**Interfaces:**

```python
from dataclasses import dataclass
from typing import Literal

TaskKind = Literal[
    "defect", "feature", "design", "research",
    "decision", "implementation", "maintenance", "unknown",
]

@dataclass(frozen=True)
class TaskDocumentationResult:
    is_valid: bool
    task_kind: TaskKind
    contract_version: int
    contract_source: str
    contract_status: Literal["valid", "invalid", "unknown", "legacy"]
    missing_fields: tuple[str, ...]
    empty_fields: tuple[str, ...]
    completion_fields: tuple[str, ...]
    warnings: tuple[str, ...]

def parse_task_kind(description: str) -> tuple[TaskKind, str]: ...
def parse_sections(description: str) -> dict[str, str]: ...
def validate_task_documentation(subject: str, description: str, *, phase: Literal["create", "complete"]) -> TaskDocumentationResult: ...
def serialize_contract(result: TaskDocumentationResult, *, parsed_at: str) -> dict[str, object]: ...
```

- [ ] Write failing tests for all seven strict kinds, unknown kind, malformed heading, case-insensitive headings, empty description, placeholder completion content, the 64 KiB boundary, and the exact incident-shaped design request that caused the incident.
- [ ] Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\cc-aca-sdlc\tests\test_task_documentation.py -q
```

Expected: the new tests fail because the package-owned module does not exist.

- [ ] Implement structural heading parsing and kind-specific required-field validation. Do not carry forward the old `PROBLEM_INDICATORS`, `SITUATION_INDICATORS`, or `SYMPTOM_INDICATORS` lists.
- [ ] Implement section extraction and phase semantics: required headings must have non-empty content at creation; completion must also reject the named short/placeholder values and require the kind's completion evidence field. `Decision: to be determined` must fail completion; `Verification: pytest ...` must pass when the other required fields are valid.
- [ ] Implement migration behavior: a new untyped task has `task_kind="unknown"` and advisory-only status; a persisted record without `contract_version` is reported as `contract_status="legacy"`. Neither is a defect and neither blocks during migration.
- [ ] Implement the 64 KiB limit and `description_too_large` warning without invoking external work or blocking the native task operation.
- [ ] Run the same command and require all new tests to pass.

## Task 3: Persist the parsed contract in terminal-scoped task state

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-aca-observability/__lib/posttooluse/task_tracker_hook.py` only after the concurrent task-lifecycle diff is reconciled
- Test: `P:/packages/.claude-marketplace/plugins/cc-aca-observability/__lib/posttooluse/tests/test_task_contract_persistence.py`

**Interfaces:**

```python
def build_task_contract(subject: str, description: str) -> dict[str, object]: ...
def track_task_create(tool_input: dict, session_id: str, terminal_id: str) -> str | None: ...
```

- [ ] Write failing tests proving a successful `TaskCreate` stores `contract_version`, `task_kind`, `contract_source`, `contract_status`, and `missing_fields` in the same terminal-scoped task record.
- [ ] Write a collision test creating the same native task ID in two terminal state files and assert each record retains its own contract.
- [ ] Write a legacy-state test proving records without `contract_version` are read as `legacy`, not as `defect`.
- [ ] Write an upgrade-on-write test: a successful `TaskUpdate` whose status changes to `in_progress` or `completed` backfills contract metadata into a legacy record without changing subject or description; an idempotent update to the same status does not backfill; `TaskList`/`TaskGet` reads do not mutate state; an unparseable update leaves the record legacy.
- [ ] Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\cc-aca-observability\__lib\posttooluse\tests\test_task_contract_persistence.py -q
```

- [ ] Add `build_task_contract()` using the package-owned parser and persist its returned dictionary inside the existing `state["tasks"][task_id]` record.
- [ ] Preserve the existing file lock, terminal path, session ID, repository, baseline, and task ID behavior.
- [ ] At execution time, choose one safe branch before editing the dirty tracker: (A) merge the exact concurrent task-lifecycle revision into the dedicated worktree and test conflicts; (B) if the tracker exposes a verified public state-update/lock API, add a package-owned contract enricher through that seam without rewriting the dirty implementation; or (C) report this task blocked with the missing seam and do not edit the dirty tracker. Do not wait indefinitely or merge an unverified diff.
- [ ] Define the upgrade trigger in the implementation: only a status-changing `TaskUpdate` to `in_progress` or `completed` upgrades a legacy record; same-status/idempotent updates and read-only `TaskList`/`TaskGet` remain non-mutating. The upgrade records contract metadata but does not retroactively alter subject or description, and `completed` still relies on the Stop gate for completion enforcement.
- [ ] Verify the existing lock/timeout API before relying on it. Add the two-terminal collision/concurrency test and a parser timing smoke; do not introduce a new lock or cache as part of this plan.
- [ ] Run the focused persistence tests again.

## Task 4: Replace creation blocking with one concise advisory

**Files:**
- Create: `P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/hooks/pretool/PreToolUse_task_self_doc_gate.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/__lib/router.py`
- Test: `P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/tests/test_task_documentation_router.py`

**Interfaces:**

```python
def run(data: dict) -> dict | None:
    """Allow TaskCreate; return at most one structured advisory for invalid typed docs."""
```

- [ ] Write failing router smoke tests for: valid design creation, invalid typed design creation, untyped design creation, malformed JSON, non-task tools, and `TaskUpdate(status="in_progress")`.
- [ ] Run the router smoke tests and confirm the old package hook is not yet available.
- [ ] Implement the package hook so `TaskCreate` never returns `decision="block"` for documentation quality. It may return a `hookSpecificOutput.advisory` containing the missing typed fields; native tool-schema errors remain owned by Claude Code.
- [ ] Prove the response surface before relying on that advisory: invoke the real registered local dispatcher with a bounded harmless `TaskCreate` fixture, capture stdout/stderr and the diagnostics log, and verify what the user-facing Claude Code surface actually displays. The existing local dispatcher preserves `hookSpecificOutput.advisory`, but its logger uses a file handler; do not describe the advisory as visible until the smoke proves it. If PreToolUse advisories are not surfaced, keep creation non-blocking and report the warning through the supported persisted-state/Stop diagnostic path instead of inventing a response shape.
- [ ] Keep parameter alias correction only if the native tool accepts the corrected shape; do not mix parameter correction with documentation policy.
- [ ] Add `PreToolUse_task_self_doc_gate.py` to a task-specific PreToolUse hook list in `P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/__lib/router.py`, and dispatch that list only for `TaskCreate`/`TaskUpdate`. Keep the existing TDD list restricted to `Edit`/`Write`/`MultiEdit`; test that task events cannot trigger TDD diagnostics.
- [ ] Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\cc-aca-sdlc\tests\test_task_documentation_router.py -q
```

Expected: valid and untyped design tasks are allowed, and invalid typed tasks are advised rather than blocked.

## Task 5: Make completion validation consume persisted task state

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/hooks/stop/Stop_task_completion_gate.py`
- Test: `P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/tests/test_task_documentation_router.py`

- [ ] Write failing tests proving Stop validates a persisted `design` record using `Goal`, `Context`, and `Decision`, not defect keywords.
- [ ] Write a test proving `TaskUpdate(status="completed")` without a description does not fail at PreToolUse when the persisted task record is valid; completion validation belongs to Stop.
- [ ] Write a test proving a missing state record produces an explicit advisory/diagnostic and does not silently claim that documentation was verified. The existing task-lifecycle plan must decide whether the final policy is allow-with-warning or block-on-missing-state before production enforcement is enabled.
- [ ] Write a test proving legacy records are advisory-only during migration.
- [ ] Run:

```powershell
python -m pytest P:\packages\.claude-marketplace\plugins\cc-aca-sdlc\tests\test_task_documentation_router.py -q
```

- [ ] Replace the direct import of `task_self_doc_validator` with the package-owned contract module.
- [ ] Remove the PreToolUse completion-time lexical validation path; Stop reads the persisted task record and calls `validate_task_documentation(..., phase="complete")`.
- [ ] Keep `TASK_SELF_DOC_ENABLED` and `TASK_SELF_DOC_ADVISORY_ONLY` as compatibility controls, but document that they apply to the completion gate only.
- [ ] Run the focused Stop tests and verify the existing task-lifecycle hardening tests still pass.

## Task 6a: Move contract construction into the observability persistence boundary

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-aca-observability/__lib/posttooluse/task_tracker_hook.py` only after Task 3's branch decision permits it
- Test: `P:/packages/.claude-marketplace/plugins/cc-aca-observability/__lib/posttooluse/tests/test_task_contract_persistence.py`

- [ ] Change the package observability tracker from re-validating prose to persisting the contract summary returned by `build_task_contract()`; it must emit at most one advisory per successful `TaskCreate`.
- [ ] Preserve the existing task record fields and terminal-scoped state writer. Add upgrade-on-write behavior for legacy records only on a successful `TaskUpdate`; reads remain side-effect free.
- [ ] If the dirty tracker cannot be safely extended through its verified public state/lock seam, stop this subtask and report the blocked branch rather than modifying concurrent code.
- [ ] Run the focused persistence and concurrent-state tests.

## Task 6b: Convert local policy code to compatibility adapters

**Files:**
- Modify: `P:/.claude/hooks/PreToolUse_task_self_doc_gate.py`
- Modify: `P:/.claude/hooks/__lib/task_self_doc_validator.py`
- Modify: `P:/.claude/hooks/tests/test_task_self_doc_gate.py`
- Modify: `P:/.claude/hooks/tests/test_task_hooks.py`

- [ ] Keep the local modules importable as compatibility adapters that delegate to the package-owned parser/hook, or remove their task dispatch entries only in the same atomic settings change described in Task 1. They must not retain independent lexical validation.
- [ ] Add a source/identity test that fails if the local adapter and package module both contain independent contract rules.
- [ ] Run the existing local gate tests and the registered package-route smoke before changing any local registration.

## Task 6c: Retire the duplicate local PostToolUse registration

**Files:**
- Modify: `P:/.claude/hooks/posttooluse/__init__.py`
- Modify: `P:/.claude/hooks/posttooluse/task_tracker_hook.py` as a temporary adapter or staged retirement target
- Modify: `P:/.claude/hooks/PreToolUse.py`
- Modify: `P:/.claude/hooks/tests/test_task_hooks.py`

- [ ] After the package observability route passes the same TaskCreate/TaskUpdate state-write and advisory smoke cases, remove the local `TaskTrackerHook` registration from `P:/.claude/hooks/posttooluse/__init__.py`. Keep the local module importable until the source/cache and active-route migration gate passes.
- [ ] In the same approved registration change, remove only the local `TaskCreate`/`TaskUpdate` entries from `PreToolUse.py`; retain its other tool dispatches.
- [ ] Assert that the live P settings route has exactly one task-state writer and one documentation-policy decision path. The C user-settings route and the separate `/go` `cc-skills-sdlc` Stop route remain outside this change.
- [ ] Run:

```powershell
python -m pytest P:\.claude\hooks\tests\test_task_hooks.py P:\.claude\hooks\tests\test_task_self_doc_gate.py -q
python -m pytest P:\packages\.claude-marketplace\plugins\cc-aca-sdlc\tests P:\packages\.claude-marketplace\plugins\cc-aca-observability\__lib\posttooluse\tests -q
```

## Task 7: Remove the obsolete local implementation and document ownership

**Files:**
- Delete via `git mv`/atomic removal only after Task 6: `P:/.claude/hooks/PreToolUse_task_self_doc_gate.py`
- Delete via `git mv`/atomic removal only after Task 6: `P:/.claude/hooks/__lib/task_self_doc_validator.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/CLAUDE.md`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-aca-observability/CLAUDE.md`
- Test: `P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/tests/test_task_documentation_router.py`

- [ ] Add the SDLC ownership table to `cc-aca-sdlc/CLAUDE.md`: contract schema, parser, PreToolUse advisory, and Stop completion policy.
- [ ] Add the observability boundary to `cc-aca-observability/CLAUDE.md`: persist and report the contract; do not define policy.
- [ ] Keep the proposed package filename `PreToolUse_task_self_doc_gate.py`. The existing `PreToolUse_tdd95_gate.py` and `PreToolUse_tdd_contract_gate.py` use `tdd_` as a TDD policy-family prefix, not a package-wide naming requirement; `task_self_doc` matches the already-live local hook and avoids a risky rename during migration.
- [ ] Remove the compatibility files only after a source search proves every import and dispatch entry resolves to the package-owned implementation.
- [ ] Do not directly edit the dirty nested `cc-skills-sdlc` repository. At execution, either apply the documentation-only hunks in a separately isolated documentation patch after its current revision is reconciled, or defer those two docs and record the exact stale statements in the handoff. Do not mix them into the task-lifecycle implementation commit.
- [ ] Before removal, run these bounded import checks from both source and cache copies:

```powershell
python -c "import importlib.util; p='P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/hooks/stop/Stop_task_completion_gate.py'; s=importlib.util.spec_from_file_location('stop_gate',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(m.__file__)"
python -c "import importlib.util; p='C:/Users/brsth/.claude/plugins/cache/local/cc-aca-sdlc/0.1.11/hooks/stop/Stop_task_completion_gate.py'; s=importlib.util.spec_from_file_location('stop_gate_cache',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(m.__file__)"
```

  The second check is an inspection check only; the direct settings routes currently resolve to `P:/packages/...` source paths, so the cache must not be treated as the active source without a settings/configuration change.
- [ ] Run:

```powershell
rg.exe -n -i "task_self_doc_validator|PreToolUse_task_self_doc_gate|self_documentation_check" P:\.claude\hooks P:\packages\.claude-marketplace\plugins\cc-aca-sdlc P:\packages\.claude-marketplace\plugins\cc-aca-observability
python P:\.claude\scripts\hooks_audit.py --packages P:\packages\.claude-marketplace\plugins
```

Expected: only package-owned implementation references remain, plus intentional test and migration documentation references.

## Task 8: Full verification, migration controls, and handoff

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-aca-sdlc/CLAUDE.md` if the final runtime controls differ from the plan
- Test: all files listed in Tasks 2–7

- [ ] Run the exact incident-shaped smoke test through the registered PreToolUse path and verify it is allowed without adding false defect language.
- [ ] Use this reproducible incident-shaped fixture (it represents the failure mode; it is not asserted to be the entire original transcript):

```json
{
  "tool_name": "TaskCreate",
  "tool_input": {
    "subject": "Review additional SDLC decision steps",
    "description": "If there are additional SDLC decision steps or skill patterns that are important for an AI-first, long-session environment, add them explicitly and explain why they matter."
  }
}
```

  The old local gate currently blocks this with defect-specific `Problem`/`Situation`/`Symptom` wording. The new registered path must allow it as untyped/unknown, with no false defect classification; a separately typed design task must still receive design-specific diagnostics.
- [ ] Run typed defect, typed design, typed research, typed decision, typed implementation, legacy, malformed, and cross-terminal collision cases.
- [ ] Include a completion-content test proving `Decision: to be determined` is rejected for a complete typed decision/design record, while a real `Verification: pytest ...` or decision rationale is accepted.
- [ ] Run:

```powershell
python -m pytest P:\.claude\hooks\tests\test_task_hooks.py P:\.claude\hooks\tests\test_task_self_doc_gate.py -q
python -m pytest P:\packages\.claude-marketplace\plugins\cc-aca-sdlc\tests -q
python -m pytest P:\packages\.claude-marketplace\plugins\cc-aca-observability\__lib\posttooluse\tests -q
git -C P:\ diff --check
```

- [ ] Verify the package source revision, active settings registrations, router dispatch list, and any generated plugin cache separately. Do not report source correctness as runtime activation without this check.
- [ ] After an explicit release/configuration checkpoint, run `plugin-audit-and-fix.py --marketplace-root P:/packages/.claude-marketplace --bump cc-aca-sdlc` and verify the new installed cache path, source/cache hashes, and `installed_plugins.json`. Do not edit the cache or `installed_plugins.json` manually.
- [ ] Do not bump `cc-aca-observability` from this plan while its current task-tracker/router changes are dirty; release that concurrent change separately or reconcile it into a reviewed commit first.
- [ ] Keep unknown/legacy tasks advisory-only until a later, explicitly approved migration changes the default. Do not enable blocking for unknown task kinds in this plan.
- [ ] Record the final source-of-truth path, active registration path, environment bypasses, migration state, test commands, and remaining risks in the handoff.

## Critical Review Already Applied

The initial proposal was revised before approval for these reasons:

1. **Rejected:** using the existing competence task-type state as the validator authority. Its registry references a missing JSON file, and its fallback writes a global state record. That would introduce stale or cross-terminal classifications.
2. **Rejected:** adding an undocumented `task_kind` field to native `TaskCreate`. The native schema is outside this repository and unknown fields could create a second tool failure.
3. **Rejected:** keeping lexical keyword validation with a larger synonym list. This would preserve the same false-positive class and encourage misleading task descriptions.
4. **Rejected:** making both PreToolUse and Stop independently strict. They receive different data; independent enforcement caused the current mismatch. Stop must validate the persisted task record, while PreToolUse advises.
5. **Rejected:** deleting the local hook immediately. The current live settings merge has multiple potential dispatch paths; removal before an active-route smoke test could silently disable the policy or leave a duplicate copy active.
6. **Retained:** package ownership in `cc-aca-sdlc`, because the policy is SDLC workflow enforcement, while observability records the result. A dedicated plugin is not justified unless the dispatch audit proves cross-plugin dependency or lifecycle ownership cannot be kept clear.
7. **Corrected:** the package router cannot receive task events through the current user-settings matcher by itself. The plan now uses a narrow workspace-owned task matcher, keeps the user settings untouched, and requires tool-aware dispatch so TDD gates do not run on task events.
8. **Corrected:** completion evidence is now enforceable content, not a documentation-only table. Empty, short, and named placeholder values fail only at completion for explicitly typed tasks.
9. **Corrected:** persistence migration is split from local-hook retirement, with an explicit dirty-tracker fallback and no indefinite wait for concurrent work.
10. **Corrected:** advisory visibility is an evidence gate. The plan no longer assumes that a `hookSpecificOutput.advisory` emitted through a file-backed logger is user-visible.

## Rollback

- Before routing changes, record the current package and workspace revisions and copy only the affected source hashes into the handoff. Perform rollback in the dedicated `P:/.worktrees/` worktree, never by resetting or cleaning the dirty parent.
- Roll back the workspace registration first: remove the narrow `TaskCreate|TaskUpdate` package matcher from `P:/.claude/settings.json`, then restore the local `TaskCreate`/`TaskUpdate` entries in `P:/.claude/hooks/PreToolUse.py` from the recorded baseline. Do not edit `C:/Users/brsth/.claude/settings.json`.
- Restore compatibility adapters and package source from the literal baseline SHA recorded in Task 1's handoff with `git restore --source=BASELINE_SHA -- PATHS`, substituting only the recorded SHA and affected paths in the dedicated worktree. Restore the local PostToolUse registration only after confirming the package writer is no longer active. Do not delete or rewrite task-state JSON.
- Re-run the registered TaskCreate/TaskUpdate smoke, focused tests, and `git diff --check`; rollback is successful only when the original local route is active and no task records changed.
- Keep `TASK_SELF_DOC_BYPASS=true` as a session-scoped emergency bypass, not a permanent configuration change.
- The source and path arguments in that rollback command are resolved from the execution handoff; this is not permission to reset the shared parent or discard concurrent work.
