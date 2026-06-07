# Context Controller Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. This document is intentionally review-oriented: use it for architecture review first, then expand individual tasks into code-level execution steps after approval.

> **SUBSTRATE CORRECTION (2026-06-07 — verified against live repo).** Two facts invalidate the original "new durable state store" design and must be honored by any implementer:
> 1. **`P:/packages/handoff/` does not exist.** Handoff was consolidated into the snapshot plugin. Do not reference or depend on a standalone handoff package.
> 2. **Durable per-terminal task state already exists** in the snapshot plugin — do NOT build a parallel store. The handoff envelope (written by `PreCompact_snapshot_capture.py`, resolved via `SnapshotFileStorage` — canonical dir `.claude/.artifacts/{terminal_id}/snapshot/`, timestamped files resolved by mtime with an exact-name fallback; **do not assume a flat `state/handoff/` path**) already carries `resume_snapshot` = `{goal, current_task, active_files, ...}`, and is restored by `SessionStart_snapshot_restore.py` ("Handoff V2") plus the one-shot `handoff_task_injector` in `snapshot_UserPromptSubmit.py` (marker-gated, fires once post-compaction).
>
> **Consequence:** the context controller is a **policy layer that READS the existing handoff envelope** and adds only what handoff lacks — phase classification, context-health thresholds, compaction/fresh-session suggestions, and resume-context arbitration. It keeps a small *controller-only* state for health counters; it does **not** re-store goal/task/active_files. Net new code is roughly one policy module, not a four-file state subsystem. Injection must be **one-shot/event-gated** — a local per-prompt re-injector was removed on 2026-06-07 for re-injecting the same block every prompt for an hour; do not reintroduce that pattern.

**Goal:** Add an automatic/semi-automatic context controller that keeps Claude Code work state durable outside chat, restores compact state after compaction/session starts, retrieves relevant files on demand, suggests phase-boundary compaction or fresh sessions, and routes bounded work to subagents when useful.

**Architecture:** The context controller is a thin policy layer over existing hooks and the snapshot plugin. Snapshot's Handoff V2 remains the durable task-state store AND the compaction recovery mechanism — the controller does **not** own durable task state. The controller READS the existing handoff envelope and owns only: phase classification, context-health warnings, compaction/fresh-session suggestions, resume-context arbitration, and optional subagent recommendations. Its sole persisted state is a small controller-only policy record (health counters, phase), never a duplicate of goal/task/active_files.

**Tech Stack:** Python 3.14, Claude Code hooks, existing hook routers in `P:/.claude/settings.json`, JSON state files, pytest, snapshot plugin under `P:/packages/.claude-marketplace/plugins/snapshot`.

---

## Design Boundary

This plan is not prompt pruning. It reduces the need for prompt pruning by moving important state out of chat history and loading only compact, relevant context.

It complements these existing plans:

- `P:/docs/superpowers/plans/2026-06-07-snapshot-v3-router-resilience.md`
- `P:/docs/superpowers/plans/2026-06-07-bifrost-context-window-resilience.md`

It should not replace either one:

- Snapshot handles compaction checkpoint/restore.
- Bifrost context resilience handles oversized API requests.
- Context controller coordinates session-level policy.

## Problems This Solves

- Long sessions lose task state after compaction.
- Important decisions live only in transcript history.
- Claude Code loads too much stale context.
- Agents keep reading the same files instead of using a working-set manifest.
- Phase changes are implicit, so compaction happens too late.
- Subagents are useful but currently require manual judgment every time.

## Non-Goals

- Do not create a vector database in the first version.
- Do not auto-launch mutating subagents.
- Do not rewrite Claude Code internal compaction.
- Do not put runtime state inside package source directories.
- Do not inject full transcripts or large file contents as "context".

---

## Proposed Runtime Flow

```text
SessionStart
-> read snapshot handoff envelope (task state) + load controller policy.json
-> inject compact resume packet (one-shot)

UserPromptSubmit
-> classify prompt phase (update phase in policy.json)
-> read handoff envelope for task fields; read policy.json for health
-> maybe suggest compact/fresh session/subagent
-> inject bounded context only (event-gated, not every prompt)

PostToolUse
-> update ONLY policy counters: turn_count, large_outputs, phase_turns
-> debounce policy.json writes
-> does NOT record active files / changed files / tests — snapshot capture + breadcrumb tracker already own that

Stop
-> update policy counters / phase only
-> does NOT write task next_step or a checkpoint (snapshot owns task state)

PreCompact
-> snapshot plugin captures the compaction handoff (sole owner of the durable task checkpoint)
-> context controller writes ONLY its policy.json (no task checkpoint, no envelope write)
```

## State Contract

**Task state is NOT owned here.** Read it from the existing snapshot handoff envelope.

**Do NOT hardcode the envelope path.** The canonical location is `.claude/.artifacts/{terminal_id}/snapshot/`, and files are timestamped (`{terminal_id}_{timestamp}_handoff.json`) and resolved by mtime, with `{terminal_id}_handoff.json` used only as an exact-name fallback by the resolver — resolving "the newest envelope" is non-trivial. **Reuse the snapshot plugin's resolver:** `SnapshotFileStorage(project_root, terminal_id).load_handoff()` in `packages/.claude-marketplace/plugins/snapshot/scripts/hooks/__lib/snapshot_files.py` (verified API: `load_handoff()` / `load_raw_handoff()` / `save_handoff()` / `handoff_file`). If the controller cannot import the plugin lib, it must replicate the resolver's newest-match logic, not assume a flat path.

The envelope's `resume_snapshot` provides `goal`, `current_task`, `active_files`, etc. Treat it as **read-only** input; the controller never writes goal/task/active_files.

Controller-only policy state path (the ONLY file this system writes):

`P:/.claude/state/context-controller/{terminal_id}/policy.json`

Minimal controller-only shape (health + phase only — task fields intentionally absent, sourced from the handoff envelope at read time):

```json
{
  "schema_version": 1,
  "terminal_id": "console_x",
  "session_id": "session_x",
  "updated_at": "2026-06-07T00:00:00Z",
  "phase": "research",
  "context_health": {
    "turn_count": 0,
    "large_outputs": 0,
    "phase_turns": 0,
    "should_compact": false,
    "should_start_fresh": false
  }
}
```

> Note: `decisions`, `blockers`, `open_questions`, `verification`, `recent_changes` are out of scope for v1 unless a verified gap shows the handoff envelope does not already carry them. Do not re-implement state that `PreCompact_snapshot_capture.py` already captures — confirm by reading the envelope schema first.

Working-set: derive from existing signals, do not build a new tracker. Active files are already recorded by `P:/.claude/hooks/PostToolUse_breadcrumb_tracker.py` (verified) and surfaced in the handoff envelope's `active_files`. (An earlier draft cited `session_changes.py` — **that file does not exist anywhere under `P:/.claude`**; do not reference it. If an equivalent change-tracker is wanted, discovery must locate the real source first.) If a distinct working-set view is still needed after confirming the gap, it is a controller-only derived cache at:

`P:/.claude/state/context-controller/{terminal_id}/working_set.json`

Working-set shape:

```json
{
  "schema_version": 1,
  "files": [
    {
      "path": "P:/path/to/file.py",
      "reason": "active implementation target",
      "last_seen": "2026-06-07T00:00:00Z"
    }
  ],
  "docs": [],
  "evidence": []
}
```

## Policy

Automatic actions:

- Save/update **controller policy.json only** (health counters + phase).
- Read active files / errors / tests from the snapshot envelope + breadcrumb tracker — the controller does NOT record them itself.
- Inject compact resume context (event-gated, one-shot).
- Mark context health warnings.
- Suggest likely subagent use.

Semi-automatic actions:

- Ask/suggest before fresh-session handoff.
- Ask/suggest before manual `/compact`.
- Ask/suggest before expensive subagent fan-out.
- Ask/suggest before archiving or deleting old state.

Forbidden automatic actions:

- Do not delete state.
- Do not launch mutating subagents.
- Do not rewrite user prompts.
- Do not switch models/providers.
- Do not inject large file bodies.

---

## File Structure Target

Create (the policy layer — keep minimal; `working_set.py` is conditional on a proven gap):

- `P:/.claude/hooks/context_controller/__init__.py`
- `P:/.claude/hooks/context_controller/state.py`  (envelope **reader** + controller-only `policy.json`, NOT a task-state store)
- `P:/.claude/hooks/context_controller/policy.py`  (phase classification + context-health + suggestions — the real new value)
- `P:/.claude/hooks/context_controller/render.py`
- `P:/.claude/hooks/context_controller/working_set.py`  (ONLY if Phase 4 Pre-task 0 proves existing trackers insufficient; otherwise omit)
- `P:/.claude/hooks/context_controller/doctor.py`
- `P:/.claude/hooks/UserPromptSubmit_modules/context_controller_injector.py`  (one-shot/event-gated — never per-prompt re-injection)
- `P:/.claude/hooks/tests/test_context_controller_state.py`
- `P:/.claude/hooks/tests/test_context_controller_policy.py`
- `P:/.claude/hooks/tests/test_context_controller_hooks.py`
- `P:/docs/superpowers/specs/2026-06-07-context-controller.md`

Reuse (do NOT re-author, all verified to exist): terminal-id sanitization (`__lib/terminal_detection.py`), policy-write locking (`P:/.claude/hooks/__lib/file_lock.py`), atomic replace/retry primitive (`atomic_write_with_retry` in `P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/__lib/snapshot_store.py`), turn/phase signals (`__lib/turn_mode.py`, `skill_execution_state`), active-file tracking (`PostToolUse_breadcrumb_tracker.py`), and the snapshot envelope resolver (`SnapshotFileStorage` in `snapshot/scripts/hooks/__lib/snapshot_files.py`). Do NOT reference `session_changes.py` — it does not exist.

Modify:

- `P:/.claude/hooks/SessionStart.py`
- `P:/.claude/hooks/PostToolUse.py`
- `P:/.claude/hooks/Stop.py`
- `P:/.claude/hooks/UserPromptSubmit_modules/registry.py`
- optionally, a separate context-controller PreCompact policy hook registration if Phase 5 proves one is needed

Review only:

- `P:/.claude/settings.json`
- `P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/snapshot_PreCompact.py`
- `P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/__lib/snapshot_files.py`
- `P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/__lib/snapshot_v2.py`

---

## Phase 1: Handoff Envelope Reader + Controller Policy State

Purpose:

Read the EXISTING snapshot handoff envelope (task state) and persist a small controller-only policy record (health counters, phase). No new task-state store. No hook integration yet.

Pre-task (mandatory discovery):

0. Read `PreCompact_snapshot_capture.py` and `__lib/snapshot_files.py` (`SnapshotFileStorage`), then load one live envelope via `SnapshotFileStorage(project_root, terminal_id).load_handoff()` to confirm the actual `resume_snapshot` schema before writing any reader. Do not assume field names, and do not hardcode a flat `state/handoff/` path.

Tasks:

1. Add `context_controller/state.py` as a **reader/adapter**, not a store.
2. Reuse existing terminal-id sanitization (`__lib/terminal_detection.py` / snapshot's `_sanitize_terminal_id`) — do not re-author.
3. Implement `read_handoff_envelope(terminal_id)` (read-only) and `load_policy_state` / `save_policy_state` / `update_policy_state` for the controller-only `policy.json`.
4. Reuse `P:/.claude/hooks/__lib/file_lock.py` for policy-write locking and `atomic_write_with_retry` from `P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/__lib/snapshot_store.py` for Windows-safe atomic replacement — do not re-implement `.tmp`+`os.replace`.
5. Add tests for envelope read (present/missing/corrupt envelope → fail-open), terminal isolation, and policy-state defaults.

Acceptance:

- The controller never writes goal/task/active_files; those come from the handoff envelope at read time.
- Writes never touch package source directories; only `policy.json` (and an optional derived `working_set.json`) is written.
- Two terminals cannot overwrite each other.
- Missing/corrupt envelope fails open (controller degrades to "no prior context"); corrupt `policy.json` resets to defaults.
- Tests pass without writing to live state roots unless explicitly configured.

Review questions:

- Confirmed: envelope schema actually contains the fields the renderer needs (verify in Pre-task 0).
- Should policy-state TTL match the handoff envelope TTL, or be independent?

## Phase 2: Phase And Context Policy

Purpose:

Classify session phase and decide whether to inject context, warn about context health, suggest compaction, suggest fresh session, or suggest subagent use.

Tasks:

1. Add `context_controller/policy.py`.
2. Define phases: `research`, `planning`, `implementation`, `review`, `debugging`, `handoff`, `general`.
3. Implement conservative prompt classification.
4. Implement context-health thresholds.
5. Implement subagent recommendation only as advisory metadata.
6. Add tests for phase classification and threshold decisions.

Initial thresholds:

- `phase_turns >= 12`: suggest checkpoint.
- `large_outputs >= 2`: suggest compact after checkpoint.
- `phase` changed from `research` to `planning` or `planning` to `implementation`: suggest fresh phase checkpoint.
- prompt contains read-only review/research markers: suggest subagent.

Acceptance:

- Policy never blocks a user prompt.
- Policy never launches a subagent.
- Policy output is structured and testable.
- False positives are advisory only.

Review questions:

- Are thresholds too aggressive for current usage?
- Should phase changes reset `phase_turns` automatically?

## Phase 3: Compact Rendering

Purpose:

Render small, machine-readable context packets for hook injection.

Render input model (explicit source contract — no field is invented):

| Field | Source | Rule |
|-------|--------|------|
| `goal`, `next_step`, `active_files`, `blockers`, `open_questions`, `recent_decisions`, `verification` | snapshot handoff envelope (`resume_snapshot`), **read-only** | If absent in the envelope, **omit** the line — do NOT synthesize it or persist it to `policy.json`. |
| `phase` | controller `policy.json` | Always available (defaults to `general`). |
| health hints (e.g. "consider /compact") | controller `policy.json` counters | Advisory text only. |

The renderer never writes state and never promotes a missing envelope field into new durable state.

Tasks:

1. Add `context_controller/render.py`.
2. Render sections per the input model above (envelope fields read-only; `phase`/health from `policy.json`).
3. Enforce max output length.
4. Add tests that long state is clipped, missing envelope fields are omitted (not fabricated), and required fields remain.

Target injected format:

```text
<context-controller>
goal: ...
phase: ...
next_step: ...
active_files:
- ...
blockers:
- ...
open_questions:
- ...
</context-controller>
```

Acceptance:

- Default injected context is under 1200 characters.
- Hard cap is 2000 characters.
- No raw transcript paths unless explicitly part of evidence.
- No full file contents.

Review questions:

- Should this render merge with snapshot's `<compact-restore>` format, or remain separate?
- Should `verification` include only latest test command or more history?

## Phase 4: Working-Set (Derive, Don't Rebuild)

Purpose:

Surface relevant files as references. **Active-file tracking already exists** — do not build a parallel tracker.

Pre-task (mandatory discovery):

0. Read `P:/.claude/hooks/PostToolUse_breadcrumb_tracker.py` (verified) and the handoff envelope's `active_files`. Confirm what is already captured before writing anything. (Do NOT look for `session_changes.py` — it does not exist; if a change-tracker beyond breadcrumbs is wanted, locate the real source via discovery first.) If existing signals are sufficient, this phase is a thin read-only view, not a new tracker.

Tasks (only if Pre-task 0 shows a real gap):

1. Add `context_controller/working_set.py` as a **derived read-only view** over breadcrumbs + envelope `active_files`.
2. Do NOT add a second PostToolUse file-tracking hook; consume the existing one's output.
3. If a derived cache is justified, store path, reason, last_seen — and document why the existing signals were insufficient.
4. Add tests for path normalization and terminal isolation.

Acceptance:

- No duplicate PostToolUse file-tracking hook is introduced.
- Paths are absolute or normalized `P:/...` paths.
- Working set is a reference view, derived from existing trackers.
- Tests cover Windows path variants.

Review questions:

- Did Pre-task 0 prove a gap, or do breadcrumbs + envelope `active_files` already suffice (in which case delete this phase)?
- Should docs and source files have separate limits?

## Phase 5: Hook Integration

Purpose:

Wire the controller into existing hooks without making it the only recovery path.

Tasks:

1. Add `UserPromptSubmit_modules/context_controller_injector.py` (event-gated, one-shot — never per-prompt re-injection).
2. Register the injector in `UserPromptSubmit_modules/registry.py` near existing context/handoff injectors.
3. Update `SessionStart.py` to inject compact context-controller context after snapshot restore, not before it.
4. Update `PostToolUse.py` to increment ONLY policy counters (`large_outputs`, `turn_count`). It must NOT record active files / tests / changed files — those are owned by snapshot capture + `PostToolUse_breadcrumb_tracker.py`.
5. Update `Stop.py` to update ONLY policy counters / phase. It must NOT write a task `next_step` or any task checkpoint.
6. Do NOT modify `snapshot_PreCompact.py` to write a controller "final checkpoint." Snapshot is the sole owner of the durable task checkpoint. If the controller needs a PreCompact tick, register a separate hook that writes ONLY `policy.json` and fails open (preserving snapshot's independence).

Ordering:

```text
SessionStart:
snapshot restore first (task state)
context-controller supplement second (policy/health only)

UserPromptSubmit:
context-controller advisory context (one-shot)
existing guards and routers remain authoritative

PreCompact:
snapshot capture first (sole task-state checkpoint)
context-controller policy.json write second (separate hook, fail-open, NO task checkpoint)
```

Acceptance:

- If context controller fails, hooks continue.
- Snapshot restore still works without context controller.
- Context controller state exists before manual `/compact`.
- Hook tests exercise the router path, not only direct function calls.

Review questions:

- Should context-controller injection happen before or after handoff context injection?
- Should `PreCompact` fail open even if context-controller checkpoint fails? Recommended: yes.

## Phase 6: Doctor And Diagnostics

Purpose:

Give operators and future agents one command to verify the system.

Tasks:

1. Add `context_controller/doctor.py`.
2. Check policy-state root exists/writable.
3. Check latest `policy.json` freshness.
4. Check working-set freshness **only if `working_set.json` exists** (Phase 4 may legitimately omit it); report `skipped` (not `fail`) when the file is absent.
5. Check that the controller can resolve the snapshot handoff envelope via `SnapshotFileStorage` (not a hardcoded path).
6. Check required hook registrations by inspecting live `P:/.claude/settings.json` and router registries.
7. Print JSON report.

Command:

```powershell
python P:\.claude\hooks\context_controller\doctor.py
```

Acceptance:

- Doctor distinguishes `ok`, `warn`, and `fail`.
- Missing `PreCompact` is a fail.
- Stale state is a warn.
- Missing optional subagent policy is not a fail.

Review questions:

- Should doctor be exposed through an existing `cc-*` status command?
- Should it inspect snapshot doctor output too?

## Phase 7: Documentation And Review Packet

Purpose:

Make the behavior understandable to future agents and reviewers.

Tasks:

1. Create `P:/docs/superpowers/specs/2026-06-07-context-controller.md`.
2. Document state schema.
3. Document hook ordering.
4. Document automatic vs semi-automatic actions.
5. Document failure behavior.
6. Add reviewer prompt for another LLM.

Acceptance:

- Docs clearly say this is a policy layer, not the snapshot store.
- Docs clearly say runtime hook authority is `P:/.claude/settings.json` plus routers.
- Docs include rollback.

Reviewer prompt:

```text
Review this context-controller design for Claude Code. Focus on hook ordering,
failure isolation, state drift, over-injection risk, terminal isolation, and
whether the plan duplicates snapshot responsibilities. Do not rewrite the
architecture unless you find a concrete failure mode.
```

---

## Test Matrix

Run after implementation:

```powershell
python -m pytest P:\.claude\hooks\tests\test_context_controller_state.py -q -p no:cacheprovider
python -m pytest P:\.claude\hooks\tests\test_context_controller_policy.py -q -p no:cacheprovider
python -m pytest P:\.claude\hooks\tests\test_context_controller_hooks.py -q -p no:cacheprovider
python -m pytest P:\.claude\hooks\tests\test_sessionstart.py P:\.claude\hooks\tests\test_userpromptsubmit_inprocess.py -q -p no:cacheprovider
python P:\.claude\hooks\context_controller\doctor.py
```

Expected:

- All context-controller tests pass.
- Existing hook tests still pass.
- Doctor returns `ok` or only documented warnings.

## Rollback

Rollback must be low-risk:

1. Remove `context_controller_injector` registration from `UserPromptSubmit_modules/registry.py`.
2. Remove context-controller calls from `SessionStart.py`, `PostToolUse.py`, and `Stop.py`; remove any separate context-controller PreCompact policy hook registration if one was added.
3. Leave state files in `P:/.claude/state/context-controller` unless the user asks to delete them.
4. Snapshot V3 must continue working independently.

## Open Design Questions For Review

1. ~~Should context-controller state and snapshot state remain fully separate?~~ **RESOLVED (substrate correction):** snapshot's Handoff V2 is the single owner of task state; the controller reads the envelope and persists only its own `policy.json`. No new task-state store; snapshot does not import controller state.
2. Should phase classification be keyword-only at first, or should it call a cheap model?
3. Should fresh-session suggestions be shown as advisory text only, or written into a follow-up action file?
4. Should subagent recommendations remain advisory forever, or become auto-dispatch for read-only research later?
5. Is `1200` characters the right default injection budget?
6. Should context health use `/context` output if Claude Code exposes it, or rely only on local heuristics?

## Implementation Recommendation

Implement Phases 1-3 first and review before hook integration.

Rationale:

- State, policy, and rendering are easy to test in isolation.
- Hook integration has the highest blast radius.
- A reviewer can inspect the controller contract before it changes live behavior.

After Phases 1-3 pass review, implement Phases 4-6. Documentation can be updated throughout, but the review packet should be finalized after the doctor command exists.
