# ADR-20260321: Handoff Post-Restore Directive Enforcement

**Status:** Proposed (Refinements Applied: R-1, R-2, R-3, R-4 — Phase 0 Security Prerequisites Added)
**Date:** 2026-03-21
**Last Verified:** 2026-03-25
**Context:** Session transcript review of handoff problems from `03-21-2025 - handoff problems 0.txt`

---

## Current State Verification (2026-03-22)

**Verification Summary**: 1 of 5 problems FIXED. The ADR was never implemented except for Problem #3 fix.

| Problem | Status | Evidence |
|---------|--------|----------|
| #1: AI acts without directive | ⚠️ POTENTIALLY EXISTS | `IncrementalIndexUpdater` still exists in `P:\packages\search-research\` (8 files) |
| #2: Skill enforcement bypassed | ⚠️ NOT FIXED | No restoration state tracking exists in codebase |
| #3: Generic responses | ✅ FIXED (2026-03-22) | `source_session_id` now displayed in `build_restore_message()` at line 566 |
| #4: Pre-mortem skill invocation | ⚠️ NOT FIXED | No directive gate exists to prevent this |
| #5: Directive provenance | ❌ NOT IMPLEMENTED | `_extract_pending_directives()` function does not exist |

**Problem #3 FIX APPLIED** (2026-03-22 - CORRECTED):
- File: `P:\.claude\hooks\SessionStart_handoff_restore.py`
- Function: `_build_graceful_resume_message()` (local function, lines 103-149)
- Lines 136-147: Added source_session_id and transcript_path to restore message
- Result: Both fields are now displayed in restore messages
- Previous behavior: `source_session_id` and `transcript_path` were stored but not shown

**Code References Verified**:
- `SessionStart_handoff_restore.py` line 183: Calls `_build_graceful_resume_message(restore_decision.envelope)` ✅ ACTIVE
- `SessionStart_handoff_restore.py` lines 136-147: Outputs source_session_id and transcript_path ✅ FIXED
- `handoff_v2.py` lines 170, 204, 329, 359: source_session_id field exists in schema
- `handoff_v2.py` line 566: `build_restore_message()` NOT called by SessionStart (different function)
- `handoff_v2.py` line 607: `build_stale_hint()` outputs source_session_id (unchanged)

**Note**: ADR previously documented fix at `handoff_v2.py:566` but SessionStart actually calls the local `_build_graceful_resume_message()` function. Both functions now include the fix.
- No `restoration_pending.json` or `directive_required` files found in codebase
- No `_extract_pending_directives()` function found in `PreCompact_handoff_capture.py`

---

## Related ADRs

### ADR-20260322: Handoff Sync Fix (Status: Accepted, Implemented 2026-03-22)

**What it fixed**: PreCompact capture was failing silently due to two bugs:
1. `.claude/hooks/PreCompact_handoff_capture.py` was never updated from the canonical version in `packages/handoff/scripts/hooks/`
2. Marker path was wrong (`parent.parent` instead of `parent.parent.parent`), causing compaction markers to be written to wrong directory

**Impact**: This ADR is a PREREQUISITE for ADR-20260321. The compaction marker bridge pattern must work for handoff context to be available after compaction.

**Implementation verification**:
- Both files now have correct marker path: `storage.handoff_file.parent.parent.parent / "hooks" / "state"` (3 parent calls)
- `.claude/hooks/PreCompact_handoff_capture.py` line 630: ✅ Correct
- `packages/handoff/scripts/hooks/PreCompact_handoff_capture.py` line 660: ✅ Correct

---

## Handoff Injector Architecture

**Two injector systems exist** (as of 2026-03-22):

| Injector | Location | Status | Pattern |
|----------|----------|--------|---------|
| **handoff_context_injector.py** | `.claude/hooks/UserPromptSubmit_modules/` | ⚠️ DEPRECATED | Loads handoff envelope directly from handoff state directory |
| **userpromptsubmit_task_injector.py** | `packages/handoff/scripts/hooks/` | ✅ ACTIVE | Uses compaction marker bridge pattern |

**Compaction Marker Bridge Pattern**:
```
PreCompact → writes {terminal_id}_handoff.json → writes compaction_marker_{terminal_id}.json
UserPromptSubmit → reads compaction_marker → loads handoff envelope → injects context → deletes marker
```

**Active injector details** (`userpromptsubmit_task_injector.py`):
- Reads markers from: `P:\.claude/hooks/state/compaction_marker_{terminal_id}.json`
- Loads envelopes from: `P:/packages/handoff/.claude/state/handoff/{terminal_id}_handoff.json`
- Uses terminal_id for marker lookup (matches PreCompact capture filename pattern)
- One-shot deletion: marker deleted after first injection, envelope persists until SessionStart restore

**Deprecated injector** (`handoff_context_injector.py`):
- Located at: `P:\.claude\hooks\UserPromptSubmit_modules\handoff_context_injector.py`
- Has three-way mismatch: wrong directory, wrong lookup key, wrong pattern
- Should be removed once active injector is confirmed stable

**Current state verification (2026-03-22)**:
- ✅ Compaction marker bridge pattern is FUNCTIONAL (ADR-20260322 fix applied)
- ✅ Handoff envelopes are being captured and restored
- ✅ Active injector (`userpromptsubmit_task_injector.py`) is registered and running
- ⚠️ Deprecated injector (`handoff_context_injector.py`) still exists but is not the primary path

---

## Problem Statement

Five distinct failure modes observed in handoff system during a single session:

1. **AI acts without user directive** — After compaction, the AI modified `search_backends` package (removed `IncrementalIndexUpdater` imports/exports) without being asked. The user never said "fix the broken import" — the AI inferred action from pre-mortem findings and acted unilaterally.

2. **Skill enforcement bypassed after restore** — User invoked `/chs` and AI responded with prose analysis instead of calling `Skill("chs")`. The skill enforcement hooks operate per-turn and do not maintain state across session restore.

3. **Generic responses instead of specific data** — User asked for specific file paths for the chat session chain. The AI gave generic paths instead of fetching actual data. It took 3+ attempts before the AI ran the Bash command to get the data.

4. **Pre-mortem skill not properly invoked** — User said "finish off using the skill" and AI called `Skill(pre-mortem)` incorrectly (bare string argument instead of Skill tool format).

5. **Handoff missing directive provenance** — User referenced a specific file path (`C:\Users\brsth\Downloads\03-21-2025 - handoff problems 0.txt`) but the handoff capture did not include this directive chain. The restore message had no record of the original file reference.

---

## Root Cause

The handoff system is **passive at restore time**. The envelope captures *what was happening* but provides no mechanism to prevent the AI from taking action on captured state without explicit user confirmation.

**Current Implementation** (as of 2026-03-22):
- `SessionStart_handoff_restore.py` line 201 calls `build_restore_message()` to generate restoration prompt
- `build_restore_message()` produces a restore message with session context but NO blocking mechanism
- The AI proceeds immediately without requiring user confirmation

**Historical Note**: Original ADR referenced `_build_graceful_resume_message()` in `SessionStart_handoff_restore.py`, but current code uses `build_restore_message()` from `handoff_v2.py`. The `_build_graceful_resume_message()` function exists at lines 103-144 but is NOT called in the main flow.

---

## Decision

Add a **post-restore directive gate** that requires explicit user confirmation before the AI takes any action on restored handoff state.

### Core Mechanism

1. **Restore-time blocking state**: After loading a handoff envelope, the SessionStart hook writes a directive state file `{terminal_id}_{session_id}_restoration_pending.json` containing:
   ```json
   {
     "restoration_id": "<uuid>",
     "source_session_id": "<original session>",
     "transcript_path": "<path to transcript>",
     "created_at": "<iso timestamp>",
     "directive_required": true,
     "session_id": "<session_id>"
   }
   ```

2. **PreToolUse directive gate**: A new PreToolUse hook (`PreToolUse_post_restore_directive_gate.py`) checks for the presence of `*_restoration_pending.json` for the current terminal. If present and `directive_required: true`, the gate blocks ALL tools except:
   - `Read` — allowed to inspect the transcript and evidence files
   - `Bash` with specific allowlist patterns (`ls`, `head`, `cat`, `file`, `stat`) — read-only diagnostics only; `python -c` is explicitly excluded as it allows arbitrary code execution and completely defeats the directive gate

3. **Explicit resume command**: The user must type a message satisfying ANY of:
   - Contains the word "resume" or "continue" (case-insensitive)
   - OR contains `--resume` flag anywhere in the message
   - **Operator precedence**: `contains "resume" OR contains "continue" OR contains "--resume"`
   - **Removed**: Question-pattern overlay (the AND-logic with `NOT is_question` was fragile — legitimate resumes with question overlay got blocked, e.g., "resume — but should I fix X first?")

4. **Resume detection in UserPromptSubmit**: A new hook (`UserPromptSubmit_modules/post_restore_directive_injector.py`) detects the resume pattern and sets `directive_required: false` in the state file, clearing the PreToolUse gate.

5. **Resume deadline with auto-extension**: If the restoration state file is older than 10 minutes without being cleared, it is automatically cleared and the session proceeds fresh. **HOWEVER**: The TTL counter is reset on ANY user interaction (every UserPromptSubmit event extends the deadline) — not just explicit resume. This prevents the 10-minute auto-unblock from racing user composition. Hard upper bound: 60 minutes after which auto-unblock fires regardless.

### Skill Enforcement Enhancement

**Do NOT create a new parallel tracking file.** The existing `pending_command_intent_{terminal_id}_{session_id}.json` mechanism in `PreToolUse_skill_pattern_gate.py` already provides session-scoped, terminal-aware skill enforcement tracking. Extend it instead:

- Extend existing `pending_command_intent` state schema with:
  - `skill_invoked: bool` field
  - `schema_version: 1` field (for cross-phase forward-compatibility — old readers detecting new writers degrade gracefully by skipping unknown fields)
- Reuse the existing Stop hook validation in `StopHook_skill_execution_gate.py` rather than creating duplicate enforcement
- The existing mechanism already handles session_id scoping via `os.getppid()` / `CLAUDE_SESSION_ID`

### Directive Provenance Tracking

Extend the handoff capture to extract and store **file path references** from user messages:

- When a user message contains a path (detected via `pathlib.Path` patterns or known extensions), store it in `pending_directives` in the handoff envelope
- At restore time, surface these paths explicitly in the restore message
- If the user references a path that was in a previous directive, it appears in the restore message with the label "Referenced:"

---

## Alternatives Considered

### Alternative A: No Enforcement (Current Behavior)
- **Favored**: Speed of resumption, simplicity
- **Degraded**: Reliability, user control
- **Fails when**: User expects to review before AI acts; AI infers action from captured state
- **ISO 25010**: -Reliability, -Security, +Performance Efficiency

### Alternative B: Strict Two-Phase Restore (Propose Then Execute)
- **Favored**: Reliability, user control
- **Degraded**: Speed of resumption, cognitive load
- **Fails when**: User wants seamless continuation; two-step interrupt disrupts flow
- **ISO 25010**: +Reliability, +Security, -Performance Efficiency, -Usability

### Alternative C: Opt-In Resume Confirmation (This Decision)
- **Favored**: Balance of control and flow
- **Degraded**: Slightly more complex than current behavior
- **Fails when**: User never types resume; session times out but handoff is still relevant
- **ISO 25010**: +Reliability, +Security, +Usability, -Performance Efficiency (minimal)

---

## Implementation Plan

### Phase 0: Security Prerequisites

**Status**: NOT STARTED (added R-4)

**Prerequisite for**: All subsequent phases — this must be implemented first to prevent TOCTOU races and bypass vulnerabilities.

**Source**: Adversarial security findings from `/planning sprightly-cooking-squid.md` review.

#### SEC-001: Add FileLock to State File Operations (CRITICAL)

**Finding**: State file read/write has no FileLock protection — TOCTOU race between terminals.

**Required change**:
- [ ] Use `filelock.FileLock` context manager for ALL read/write operations on `*_restoration_pending.json`
- [ ] State file location: `P:\.claude\state\handoff\{terminal_id}_restoration_pending.json`
- [ ] Lock file location: `P:\.claude\state\handoff\{terminal_id}_restoration_pending.lock`
- [ ] Lock timeout: 5 seconds (fail-fast on contention)

**Implementation**:
```python
from filelock import FileLock

lock_path = state_path.with_suffix('.lock')
with FileLock(lock_path, timeout=5):
    state_path.write_text(json.dumps(state))
```

#### SEC-003: Fix Bash Allowlist to Parse Full Command (HIGH)

**Finding**: `ls; python -c` passes allowlist — only `argv[0]` is checked.

**Required change**:
- [ ] Parse full command string, not just argv[0]
- [ ] Split on `;`, `|`, `&&`, `||` and validate each segment
- [ ] Reject commands containing dangerous patterns (`python -c`, `eval`, `exec`, `subprocess`)
- [ ] Check BEFORE shell interpretation

**Note**: The ADR originally proposed allowing `ls`, `head`, `cat`, `file`, `stat` — but SEC-003 shows this allowlist bypass is exploitable. Full command parsing is required.

#### SEC-004: Include session_id in State File Path (HIGH)

**Finding**: State file uses `{terminal_id}_restoration_pending.json` — terminals with same terminal_id share state.

**Required change**:
- [ ] Rename state file to `{terminal_id}_{session_id}_restoration_pending.json`
- [ ] Both `terminal_id` AND `session_id` must match for gate activation
- [ ] Get session_id from `os.getppid()` / `CLAUDE_SESSION_ID` environment variable

#### QUAL-002: Specify Hook Execution Order (MEDIUM)

**Finding**: Within-turn execution order undefined — UserPromptSubmit injector clears directive but PreToolUse gate checks state.

**Required change**:
- [ ] Document explicit execution order in hook files
- [ ] UserPromptSubmit injector runs BEFORE PreToolUse gate (per turn lifecycle)
- [ ] State clearing happens in injector, not gate — gate only reads state
- [ ] Add execution order comment in both files

---

### Phase 1: Core Directive Gate (renumbered from Phase 1)

**Status**: NOT STARTED (as of 2026-03-22)

**Files to create**:
- [ ] `P:\.claude\hooks\PreToolUse_post_restore_directive_gate.py` (new file)
- [ ] `P:\.claude\hooks\UserPromptSubmit_modules\post_restore_directive_injector.py` (new file)

**Files to modify**:
- [ ] `P:\.claude\hooks\PreToolUse.py` — Add to UNIVERSAL or TOOL_HOOKS dispatch chain
- [ ] `P:\.claude\hooks\UserPromptSubmit_modules\registry.py` — Register injector hook
- [ ] `P:\packages\handoff\scripts\hooks\SessionStart_handoff_restore.py` — Add restoration state file management after line 201

**Specific locations**:
- `PreToolUse.py`: Add to dispatch chain after line ~50 (in UNIVERSAL or TOOL_HOOKS section)
- `SessionStart_handoff_restore.py`: After `build_restore_message()` call at line 201, add state file write
- State file location: `P:\.claude\state\handoff\{terminal_id}_{session_id}_restoration_pending.json` (per SEC-004)

### Phase 2: Skill Enforcement Enhancement (renumbered from Phase 2)

**Status**: NOT STARTED (as of 2026-03-22)

**Current mechanism** (verified location):
- File: `P:\.claude\hooks\PreToolUse\PreToolUse_skill_pattern_gate.py`
- Lines 471-514: Stateful skill-first gate reads `pending_command_intent_{terminal_id}.json`
- State file schema: `{"schema_version": 1, "skill": str, "prompt": str, "timestamp": str, "session_id": str, "terminal_id": str, "skill_invoked": bool}`

**Required changes**:
- [ ] Extend `pending_command_intent` schema with `skill_invoked: bool` field
- [ ] Update `StopHook_skill_execution_gate.py` to validate skill_invoked after restore
- [ ] **Do NOT create new parallel tracking file** — reuse existing `pending_command_intent_{terminal_id}_{session_id}.json`

**Note**: The state file is `{terminal_id}.json` (not session-scoped). Session scoping is handled via content validation, not filename.

### Phase 3: Directive Provenance (renumbered from Phase 3)

**Status**: PARTIALLY COMPLETE (Problem #3 fixed 2026-03-22)

**FIXED (2026-03-22)**:
- [x] `source_session_id` now displayed in `build_restore_message()` at line 566
- [x] Users will now see the source session ID in handoff restore messages

**Remaining work** (verified locations):
- Capture file: `P:\.claude\hooks\PreCompact_handoff_capture.py`
- Function `build_resume_snapshot()` at lines 589-605 creates envelope
- Restore function: `build_restore_message()` at lines 544-617 in `handoff_v2.py`

**Required changes**:
- [ ] Create `_extract_pending_directives()` function in `PreCompact_handoff_capture.py`
- [ ] Add `pending_directives: list[str]` field to resume_snapshot schema
- [ ] Add path pattern matching for user messages using allowlist (`.py`, `.md`, `.txt`, `.json`, `.yaml`, `.yml`, `.toml`)
- [ ] Use `pathlib.Path` resolution to prevent traversal injection
- [ ] Surface paths in `build_restore_message()` at `handoff_v2.py:544-617` with "Referenced:" label
- [ ] **Note**: Original ADR referenced `_build_graceful_resume_message()`, but current code uses `build_restore_message()`. Add to the ACTIVE function.

### Phase 4: Testing and Rollback (renumbered from Phase 4)

**Status**: NOT STARTED (as of 2026-03-22)

**Required tests**:
- [ ] **TEST-001**: Unit test — gate blocks all non-allowlisted tools when `directive_required: true`; allows `Read` and allowlisted `Bash` patterns
- [ ] **TEST-002**: Unit test — resume detection clears `directive_required` when message contains "resume" or "continue" or `--resume`
- [ ] **TEST-003**: Unit test — TTL resets on any UserPromptSubmit event; 10-minute base deadline with 60-minute hard upper bound auto-clears stale state
- [ ] **TEST-004**: Integration test — multi-terminal isolation: Terminal A's gate does not affect Terminal B's tools
- [ ] **TEST-005**: Integration test — end-to-end: restore → block → resume → unblock flow
- [ ] Rollback: Delete gate files, remove from dispatch chain

**Test file location**:
- `P:\.claude\hooks\tests\test_post_restore_directive_gate.py` (new file)
- `P:\.claude\hooks\tests\test_post_restore_directive_injector.py` (new file)

---

## Multi-Terminal Safety

**Scope**: Multi-terminal safe across *different* terminals and *different sessions*. Within the *same* terminal and session, concurrent hook invocations share the same state and are not a concern.

- **Cross-terminal isolation**: State files use `{terminal_id}_{session_id}_restoration_pending.json` (per SEC-004). Both `terminal_id` AND `session_id` must match for gate activation — different terminals or sessions do not interfere.
- **Same-terminal safety**: All hook invocations within one terminal and session share the same state file; no concurrent access issue within a single terminal.
- **Stale state on crash**: If a terminal crashes during the directive-pending state, the state file persists. The 10-minute TTL deadline clears it automatically, but resets on ANY user interaction (hard upper bound: 60 minutes). A TTL reaper (independent cleanup check on `SessionStart`) removes orphaned state files older than the hard upper bound.
- **Fail-open on read error**: If `*_restoration_pending.json` cannot be read (permissions, corruption), the gate fails closed (blocks) as a security default — not silently open.

---

## Edge Case Considerations

### What if the user doesn't type "resume"?
The TTL deadline on `{terminal_id}_{session_id}_restoration_pending.json` (auto-extends on any user interaction, 10-minute base, 60-minute hard upper bound) automatically clears the blocking state. The session proceeds as fresh after timeout.

### What if multiple terminals restore the same handoff?
The `terminal_id` validation in `evaluate_for_restore()` ensures only the matching terminal's restore succeeds. Others get "terminal mismatch" and start fresh.

### What if skill enforcement state persists incorrectly across sessions?
This is addressed in Phase 2 by reusing the existing `pending_command_intent` mechanism, which uses session_id scoping (`os.getppid()` / `CLAUDE_SESSION_ID`). A new session gets a new session_id and fresh tracking.

### What if the user says "resume" but doesn't mean it as a directive?
Bare "resume" without other context triggers clearing — this is intentional. If the user says "I was just testing resume as a keyword", they can follow up with "actually don't continue that task" and the next tool call will be gated again if a new `*_restoration_pending.json` exists.

### What if path extraction produces false positives?
Path extraction uses a conservative allowlist: extensions (`.py`, `.md`, `.txt`, `.json`, `.yaml`, `.yml`, `.toml`). Additionally, ALL extracted paths are resolved via `pathlib.Path.resolve()` and validated against the project root before being stored — this prevents path traversal injection (e.g., `../../etc/passwd` would resolve outside project root and be rejected).

### What if the handoff envelope is corrupted or checksum fails?
`validate_envelope()` in `handoff_v2.py` raises `HandoffValidationError` on checksum mismatch. `evaluate_for_restore()` catches this and returns `RestoreDecision(ok=False, reason="invalid handoff")`. The session starts fresh.

### What if the state file cannot be read (permissions error)?
The directive gate fails closed — if the state file exists but cannot be read, all non-allowlisted tools are blocked. This is a security default: on read failure, assume directive is pending.

---

## Rollback Strategy

### Phase 0 Rollback
1. Remove FileLock usage from state file operations
2. Revert Bash allowlist to argv[0] only check
3. Remove session_id from state file path (revert to terminal_id only)

### Phase 1+ Rollback
1. Delete `PreToolUse_post_restore_directive_gate.py`
2. Delete `UserPromptSubmit_modules/post_restore_directive_injector.py`
3. Remove entries from dispatch chains in `PreToolUse.py` and UserPromptSubmit router
4. Remove restoration state management from `SessionStart_handoff_restore.py`
5. Revert `pending_command_intent` schema changes (Phase 2)

No schema migration required — the directive gate is additive and self-contained. Phase 2 changes reuse existing mechanisms, so rollback only requires reverting the schema extension.
