# ADR-20260328: Handoff Lifecycle Phase Field

**Status:** Proposed
**Date:** 2026-03-28
**Decomposed by:** N/A

## Context

Post-compaction Claude immediately resumes implementing solutions that were still in discussion/planning — unapproved, unfinished, or not agreed to.

The existing handoff system (`packages/handoff`) captures task state (goal, files, decisions) but does not capture **conversation lifecycle state** — where in the discuss → plan → approve → implement flow the session was when compaction fired.

### Current Behavior

`PreCompact_handoff_capture.py:166-180` detects planning sessions via `detect_planning_session()`:
- Covers `/plan-workflow` and `/arch` invocations
- Sets `awaiting_approval` blocker when detected
- Restore message then warns post-compaction Claude to ask before proceeding

### Gaps

| Scenario | Current Capture | Problem |
|----------|----------------|---------|
| Verbal discussion (no slash command) | Goal extracted, no phase marker | Post-compaction Claude sees a goal and resumes implementation |
| Partial agreement ("do X but not Y") | Decision regex may catch "must"/"avoid" | Nuanced "agreed on approach A, haven't approved implementation" missed |
| Implementation started prematurely | `active_files` edits look like "resume work" | No signal that work was unauthorized |

### Research Basis

Queried 3 NotebookLM notebooks (256+ sources total: Context/Memory/Search, Skills/Agentic Coding, Agentic Engineering Playbook). Key finding from community reports:

> "Post-compaction performance degrades 30-50%. CLAUDE.md instructions are re-injected with a 'may or may not be relevant' disclaimer, demoting rules to suggestions. Claude loses track of what it was doing."

The "compaction amnesia" problem is well-documented. The handoff package already implements the gold-standard pattern (PreCompact + SessionStart hook loop). The lifecycle phase field closes the remaining gap: **not just what was being done, but whether it should be done at all.**

## Decision

Add a `lifecycle_phase` field to the `resume_snapshot` schema in the V2 handoff envelope.

### Field Specification

**Name:** `lifecycle_phase`
**Type:** `string` (enum)
**Values:** `discussing` | `planning` | `approved` | `implementing` | `reviewing`
**Default:** `implementing` (safe default — existing behavior unchanged)
**Optional:** Yes (backward compatible — older envelopes without it fall through to default)

### Detection Logic

```
if awaiting_approval blocker exists:
    lifecycle_phase = "planning"
elif no active_files edits AND no pending operations:
    lifecycle_phase = "discussing"
elif active_files edits exist AND recent user message was a question:
    lifecycle_phase = "discussing"  # override — questions imply discussion
elif pending_operations exist AND no blockers:
    lifecycle_phase = "implementing"
else:
    lifecycle_phase = "implementing"  # safe default
```

Detection is **deterministic** (no LLM calls, no external services) — consistent with the hook design constraints in CLAUDE.md (hooks must be standalone, local-only, no API calls).

### Restore Behavior

The restore message builder (`build_restore_message_dynamic`) adds an explicit directive based on `lifecycle_phase`:

| Phase | Restore Directive |
|-------|------------------|
| `discussing` | "IMPORTANT: This task was in DISCUSSION. Do NOT implement anything. Continue the conversation where it left off." |
| `planning` | "Plan exists but NOT approved. Ask user for approval before proceeding with implementation." |
| `approved` | "User approved this plan. Resume implementation." |
| `implementing` | "Resume implementation." |
| `reviewing` | "Implementation complete, under review. Wait for user feedback before making changes." |

### Schema Change

Add to `resume_snapshot` in `handoff_v2.py`:
- Add `lifecycle_phase` to `OPTIONAL_SNAPSHOT_FIELDS` set
- Add validation: if present, must be one of `VALID_LIFECYCLE_PHASES`
- No change to checksum computation (optional field)

### Files Changed

| File | Change |
|------|--------|
| `scripts/hooks/__lib/handoff_v2.py` | Add `VALID_LIFECYCLE_PHASES`, add to `OPTIONAL_SNAPSHOT_FIELDS`, add validation |
| `scripts/hooks/PreCompact_handoff_capture.py` | Add `detect_lifecycle_phase()` function, pass to `build_resume_snapshot()` |
| `scripts/hooks/__lib/dynamic_sections.py` | Add lifecycle-phase-aware restore directive to restore message builder |

## Rationale

The existing `awaiting_approval` blocker covers `/plan` and `/arch` but misses verbal discussion. Adding a single enum field with deterministic detection:

1. **Closes the gap** — post-compaction Claude gets an explicit "do not implement" signal for discussion/planning phases
2. **Is backward compatible** — optional field, default preserves current behavior
3. **Adds no dependencies** — detection uses data already extracted (blockers, active_files, user messages)
4. **Is deterministic** — no LLM calls, no regex complexity, no external services

### Tradeoffs

| Quality | Improved | Degraded |
|---------|----------|----------|
| Reliability | Post-compaction respects conversation state | None — default preserves existing behavior |
| Maintainability | One enum + one function + validation | Minimal — 3 files, ~50 lines total |
| Performance | Negligible — detection reuses already-extracted data | None |

## Multi-Terminal Safety

- **Safe.** The `lifecycle_phase` field is stored inside the per-terminal handoff envelope. Each terminal gets its own phase. No shared mutable state introduced.
- Detection uses per-terminal data (blockers, active_files from that terminal's transcript only).

## Enhancement: Incremental State Accumulation

### Problem

All handoff data is extracted at compact time by scanning the entire transcript. This means:

1. **Decisions that lived only in conversation are at risk** — if the transcript is large or noisy, the regex-based decision scanner may miss them
2. **Phase transitions are inferred, not recorded** — we guess the lifecycle phase from the final state, not from the actual progression
3. **The PreCompact hook does heavy work** — transcript.py is 2,744 lines because it parses everything at once

### Research Basis

From the NotebookLM research (3 notebooks, 256+ sources):

> "Write design decisions incrementally to a persistent log file as they happen, not at session end. This ensures state is safely on disk before auto-compaction can discard the reasoning behind it."

> "Decisions that live only in the conversation will be lost. Every time a design decision is made, write a 1-3 line entry immediately."

### Design: Per-Terminal Incremental JSONL

Add a lightweight `PostToolUse` hook that appends detected state transitions to a per-terminal JSONL file (`{terminal}_accumulated.jsonl`) as they happen during the session.

**What gets appended incrementally:**

| Event | Trigger | JSONL Entry |
|-------|---------|-------------|
| Decision detected | Assistant message matches DECISION_PATTERNS | `{"type":"decision","kind":"constraint","summary":"...","ts":"..."}` |
| File modified | Edit/Write tool completes | `{"type":"file_edit","path":"...","ts":"..."}` |
| Phase transition | Lifecycle phase changes (e.g., discussing→implementing) | `{"type":"phase_transition","from":"discussing","to":"implementing","ts":"..."}` |

**Why PostToolUse, not a new event:**

- PostToolUse fires after every tool call — Edit, Write, Bash, etc.
- The hook sees the tool result and the current conversation context
- No new hook registration needed — just add another listener to the existing PostToolUse router
- Consistent with the hook design constraints (local-only, deterministic, no API calls)

**How PreCompact uses accumulated state:**

Instead of scanning the entire transcript, the PreCompact hook:
1. Reads `{terminal}_accumulated.jsonl` (already-built decisions list, file history, phase transitions)
2. Supplements with transcript-only data (goal extraction, pending operations)
3. The final `lifecycle_phase` comes from the last `phase_transition` entry in the JSONL, not from inference at compact time

**Benefits:**

1. **Decisions are safely on disk before compaction** — even if compaction discards the conversation, decisions survive in the JSONL
2. **Phase is recorded, not inferred** — we track actual transitions (user said "go ahead" → phase_transition to `approved`) rather than guessing from the final state
3. **PreCompact becomes lighter** — reads a JSONL instead of parsing 2,744 lines of transcript logic
4. **Debugging is easier** — the JSONL is a chronological record of what the hook observed

**JSONL format (one line per event):**

```jsonl
{"type":"phase_transition","from":"discussing","to":"planning","ts":"2026-03-28T10:30:00Z","trigger":"/arch invoked"}
{"type":"decision","kind":"constraint","summary":"Must use SQLite not Redis","ts":"2026-03-28T10:31:00Z"}
{"type":"file_edit","path":"P:/packages/handoff/scripts/hooks/__lib/handoff_v2.py","ts":"2026-03-28T10:35:00Z"}
{"type":"phase_transition","from":"planning","to":"approved","ts":"2026-03-28T10:40:00Z","trigger":"user: go ahead"}
{"type":"phase_transition","from":"approved","to":"implementing","ts":"2026-03-28T10:41:00Z","trigger":"first Edit tool"}
```

**Phase transition detection (deterministic, no LLM):**

| Transition | Detection |
|------------|-----------|
| → `discussing` | First user message in session (no edits yet) |
| → `planning` | `/plan`, `/arch`, or "plan"/"design" in user message while phase is `discussing` |
| → `approved` | User message matches approval patterns: "go ahead", "looks good", "implement it", "yes do it", or explicit `/plan` approval |
| → `implementing` | First Edit/Write tool call after `approved` phase |
| → `reviewing` | Stop/completion signal after `implementing` |

**Storage location:** Same as handoff files — `.claude/state/handoff/{terminal}_accumulated.jsonl`

**Cleanup:** JSONL is truncated on new session start (old data is stale). The PreCompact hook reads and consumes it. Old JSONL files are cleaned up by the existing `cleanup_old_handoffs()` function.

### Multi-Terminal Safety (Incremental)

- **Safe.** Each terminal gets its own `{terminal}_accumulated.jsonl`. No shared state.
- Append-only writes (no read-modify-write cycles, no locking needed for append).
- Phase transitions are per-terminal — terminal A in `discussing` doesn't affect terminal B in `implementing`.

### Rollback (Incremental)

- Remove the PostToolUse listener
- Remove JSONL reading from PreCompact
- System falls back to current behavior (full transcript scan at compact time)
- Orphaned JSONL files are harmless (ignored by code that doesn't read them)

## Implementation Plan

### Phase 1: Lifecycle Phase Field (Core)

1. Add `VALID_LIFECYCLE_PHASES` constant and validation to `handoff_v2.py`
2. Add `detect_lifecycle_phase()` function to `PreCompact_handoff_capture.py`
3. Update `build_restore_message_dynamic()` in `dynamic_sections.py` to emit phase-aware directives
4. Add backward compatibility test (envelope without `lifecycle_phase` → default to `implementing`)
5. Add unit tests for each detection path
6. Add integration test: simulate compaction during discussion, verify restore says "do not implement"

### Phase 2: Incremental State Accumulation (Enhancement)

7. Create `PostToolUse_handoff_accumulator.py` — lightweight listener that appends to `{terminal}_accumulated.jsonl`
8. Register in PostToolUse hook router
9. Add `read_accumulated_state()` to `handoff_files.py` — reads JSONL, returns decisions + phase transitions
10. Update PreCompact hook to read accumulated state first, supplement with transcript scan
11. Update `detect_lifecycle_phase()` to prefer the last `phase_transition` from JSONL over inference
12. Add cleanup for JSONL files in existing `cleanup_old_handoffs()`
13. Add unit tests for accumulator (append, phase transition detection, truncation on new session)
14. Add integration test: decisions written during session survive compaction via JSONL

## Rollback

Remove the field from the three files listed above. Old envelopes with `lifecycle_phase` are harmless (ignored by code that doesn't check it). New envelopes without it fall through to the existing behavior.

## Consequences

- **Positive:** Post-compaction Claude will no longer immediately implement unapproved solutions during discussion/planning phases
- **Positive:** The phase is explicit in the handoff file, making debugging restore behavior easier
- **Negative:** None identified — the field is optional and defaults to existing behavior
