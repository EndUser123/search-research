# ADR-20260324: Handoff Post-Restore Directive Enforcement — Architecture Evaluation

**Status:** Reviewed (Not Accepted — requires 3 refinements before acceptance)
**Date:** 2026-03-24
**Context:** Post-compaction handoff failure analysis, two failure patterns documented in `handoff problems 0.txt` and `handoff problems 1.txt`
**Research:** External validation via GitHub Issue #27319, Post-Compaction Hook pattern (Nick Porter), LangGraph.js schema versioning issue #536

---

## Decision

**ADR-20260321's core design (PreToolUse blocking gate at restore time) is APPROVED with 3 required refinements.**

### Core Architecture — APPROVED

- **PreToolUse gate is the correct interception layer** — intercepts mutation before it happens without blocking session startup
- **State file `*_restoration_pending.json`** scoped by `terminal_id` — correct multi-terminal isolation
- **Fail-closed on read error** — correct security default
- **10-minute TTL deadline** — sound safety net (but must extend on any user interaction)

### Three Required Refinements

| # | Issue | Required Fix |
|---|-------|-------------|
| **R-1** | Resume pattern AND-logic (keyword + NOT question) is fragile — legitimate resumes with question overlay get blocked | Simplify to OR: `--resume` flag OR explicit "resume"/"continue" keyword. Remove question-pattern overlay. |
| **R-2** | Phase 1/2 coupling via `pending_command_intent` schema extension creates cross-phase corruption risk | Add schema versioning to `pending_command_intent.json` so old readers detect new writers and degrade gracefully |
| **R-3** | TTL auto-unblock after 10 minutes defeats the directive gate intent if user is composing a thoughtful response | Extend TTL on ANY user interaction (not just explicit resume) — every UserPromptSubmit event resets the TTL counter. Hard upper bound: 60 minutes. |

---

## Problem Statement

Two distinct handoff failure patterns observed post-compaction:

**Pattern #0** (handoff problems 0.txt):
- AI misidentified the last task — responded to "please review this solution" instead of "please implement to the end"
- User corrected the AI at line 128
- Root cause: `_infer_next_step()` infers a single next step from transcript, but the transcript showed two distinct pending tasks

**Pattern #1** (handoff problems 1.txt):
- AI completed Task 1 (fixing `/code` skill continuous mode) but never resumed Task 2 (NotebookLM review)
- AI attributed failure to "distraction" — a reasoning failure, not a system failure
- Root cause: `pending_operations` captures at most one next step (line 251: `pending_operations[0]`), so multi-task sequences lose all but the first item

**Systemic root cause**: The handoff system is passive at restore time — it provides context but no blocking mechanism to prevent the AI from taking unilateral action on restored state.

### External Validation

The failure mode is not unique to this codebase:

**GitHub Issue #27319** (Claude Code, Feb 2026):
> "After context compaction, Claude Code frequently resurfaces plans that were already completed, shelved, or canceled — then presents them as a yes/no approval with no visible conversation history, forcing the user to approve blindly. ~50% of the time this results in the agent executing work that shouldn't happen."
> — Frequency: 4-8 times per session. Impact: Agent creates files, modifies projects based on canceled/shelved plans.

This confirms:
1. The problem is systemic to AI coding assistants post-compaction, not specific to this implementation
2. The "stale plan auto-resume" failure mode occurs at high frequency (~50% of compactions)
3. The "force-approve with no visible history" pattern validates the need for a directive gate that shows context before blocking

**Post-Compaction Hook Pattern** (Nick Porter, Mar 2026):
The `PostToolUse` hook with `compact` matcher fires after compaction; stdout is injected as a system message immediately. This validates that hook-based context injection works in production — and that CLAUDE.md alone is insufficient because it gets summarized. This reinforces the ADR's approach of using a separate state file + blocking gate rather than relying on prompt injection alone.

**LangGraph.js Issue #536**: "Support for State Schema Versioning & Migration" confirms R-2 is the correct approach — schema versioning for agent state files is a known gap in production agentic systems.

---

## Alternatives Considered

### Alternative A: SessionStart Returns `decision: "block"`

- **What**: `SessionStart_handoff_restore.py` returns `decision: "block"` instead of `decision: "approve"`, preventing session from starting
- **Favored**: Reliability, user control
- **Degraded**: User cannot see restore context, pending tasks, or transcript path before unblocking — blocks before context is visible
- **Fails when**: User needs to see what was in progress before deciding whether to continue
- **ISO 25010**: +Reliability, +Security, -Usability

### Alternative B: UserPromptSubmit Non-Blocking Directive Injection Only

- **What**: `UserPromptSubmit` injects directive into prompt but does not block tool execution
- **Favored**: Simplicity, no new state files
- **Degraded**: AI can ignore the injected directive and act unilaterally — same failure mode as today
- **Fails when**: AI infers action from captured state without waiting for user directive
- **ISO 25010**: +Performance Efficiency, -Reliability, -Security

### Alternative C: PreToolUse Blocking Gate with Resume Pattern (ADR-20260321 + Refinements) — SELECTED

- **What**: PreToolUse gate blocks all non-read-only tools when `*_restoration_pending.json` exists with `directive_required: true`. User must type "resume" or `--resume` to clear.
- **Favored**: Reliability, user control, visibility of restore context before action
- **Degraded**: Slightly more complex than current behavior, introduces TTL dependency
- **Fails when**: Resume pattern is too restrictive (false negatives); TTL races with user composition
- **Mitigated by**: R-1 (simplify resume pattern), R-3 (extend TTL on interaction)
- **ISO 25010**: +Reliability, +Security, +Usability, -Performance Efficiency (minimal — local file check only)

---

## Multi-Terminal Safety

**Status**: SAFE — well-designed.

- `*_restoration_pending.json` uses `{terminal_id}` in filename — cross-terminal isolation is automatic
- `evaluate_for_restore()` validates `terminal_id` before activating gate — only matching terminal unblocks
- 10-minute TTL handles crashed terminal recovery
- Fail-closed on read error — if state file can't be read, block all non-allowlisted tools

**No shared mutable state across terminals.**

---

## Integration Risks

### Risk 1: Resume Pattern False Negatives (HIGH)

**Scenario**: User types `"resume - but should I fix X first?"`

| Step | Detection | Result |
|------|-----------|--------|
| Contains "resume" | ✓ | Passes keyword check |
| Starts with "but should" | Question pattern matches | BLOCKED |

**Impact**: User explicitly used the resume keyword but the question overlay blocks them. After 10-minute TTL fires, AI proceeds anyway — the exact failure mode the ADR tries to prevent.

**Fix (R-1)**: Remove question-pattern overlay. Resume pattern = just the keyword OR `--resume` flag.

### Risk 2: Phase 1/2 Schema Coupling (MEDIUM)

**Scenario**: Phase 1 deployed, Phase 2 not yet deployed. A terminal crashes mid-session.

- Phase 1 writes `*_restoration_pending.json`
- Phase 2 extends `pending_command_intent.json` with `skill_invoked: bool` — but Phase 2 isn't deployed yet
- Old `pending_command_intent` reader encounters new schema → parse error or silent failure
- Skill enforcement tracking becomes inconsistent

**Fix (R-2)**: Add `"schema_version"` field to `pending_command_intent.json`. Readers check version before parsing; unknown versions degrade gracefully (skip extension fields).

### Risk 3: TTL Auto-Unblock Races User Composition (MEDIUM)

**Scenario**: User is composing a thoughtful multi-part resume message. At minute 9:30, they type `"resume -- here's what I want you to..."` but haven't finished. At minute 10:00, TTL fires. AI proceeds with partial context.

**Impact**: The resume message was in progress when TTL fired. AI proceeds without the user's full directive.

**Fix (R-3)**: Reset TTL counter on ANY user message received (not just resume pattern). Every turn the user takes extends the deadline. Hard cutoff still applies at some upper bound (e.g., 1 hour) to prevent permanent blocking.

---

## GoT Analysis

**Extracted Nodes**:
- Constraints: ["Must block tools after restore", "Must allow Read/read-only Bash", "Must unblock on explicit resume", "10-min TTL with extension", "Multi-terminal safe"]
- Ideas: ["PreToolUse gate", "UserPromptSubmit resume detector", "*_restoration_pending.json", "pending_command_intent schema versioning", "TTL reset on interaction"]
- Risks: ["Resume pattern false negative", "Phase 1/2 schema coupling", "TTL auto-unblock races composition"]
- Components: ["SessionStart_handoff_restore.py", "PreToolUse_post_restore_directive_gate.py", "post_restore_directive_injector.py", "pending_command_intent.json"]

**Edge Relationships**:
- "PreToolUse gate" supports "Must block tools" ✓
- "10-min TTL with extension" partially contradicts "Must unblock on explicit resume" — if user takes >10min composing, auto-unblock defeats intent (mitigated by R-3)
- "pending_command_intent schema versioning" enables "Phase 1/2 schema coupling" mitigation ✓
- "TTL reset on interaction" (R-3) contradicts "10-min TTL" — extends deadline, needs upper bound

**Cycles Detected**: None.

---

## Required Implementation Changes to ADR-20260321

### Phase 1 Changes

1. **Resume detector (R-1)**: Change from AND-logic to OR-logic:
   ```
   OLD: (contains resume AND NOT question) OR --resume OR (task_ref AND keyword)
   NEW: contains "resume" OR contains "continue" OR contains "--resume"
   REMOVE: question pattern overlay entirely
   ```

2. **TTL reset (R-3)**: Add TTL reset on any UserPromptSubmit:
   - Every user message to UserPromptSubmit resets the 10-minute counter
   - Add hard upper bound (e.g., 60 minutes) after which auto-unblock fires regardless

3. **UNIVERSAL ordering**: Explicitly specify gate position in PreToolUse UNIVERSAL array:
   ```
   After: PreToolUse_skill_pattern_gate.py
   Before: PreToolUse_risk_tier_gate.py
   ```

### Phase 2 Changes

4. **Schema versioning (R-2)**: Add to `pending_command_intent.json` schema:
   ```json
   {
     "schema_version": 1,
     "skill": "...",
     "skill_invoked": false
   }
   ```
   - Readers check `schema_version` before parsing extension fields
   - Unknown version → skip extension fields, operate on base schema

---

## Rollback Strategy (Unchanged from ADR-20260321)

1. Delete `PreToolUse_post_restore_directive_gate.py`
2. Delete `UserPromptSubmit_modules/post_restore_directive_injector.py`
3. Remove entries from dispatch chains in `PreToolUse.py` and UserPromptSubmit router
4. Remove restoration state management from `SessionStart_handoff_restore.py`
5. Revert `pending_command_intent` schema changes (Phase 2) — remove `skill_invoked` field

**No schema migration required** — Phase 2 changes are additive with versioning.

---

## Dependencies

- **PREREQUISITE**: ADR-20260322 (handoff sync fix) must be implemented first — PreCompact capture must work correctly for the directive gate to have valid state to gate
- **PARALLEL**: Phase 2 can be implemented alongside Phase 1 but tested independently before integration

---

## Edge Case Considerations

### What if the user doesn't type "resume" at all?
TTL extends on every user interaction (R-3). User can type questions, explore files with `Read`, use allowlisted `Bash` commands — all while TTL keeps extending. After hard upper bound (60 min), auto-unblock fires.

### What if multiple terminals restore the same handoff?
`terminal_id` validation in `evaluate_for_restore()` ensures only the matching terminal's restore succeeds. Others get "terminal mismatch" and start fresh — no gate activation.

### What if the user says "resume" but doesn't mean it as a directive?
Bare "resume" without other context triggers clearing — intentional. User can say "I was just typing resume as a test" and follow up with "actually don't continue that task". The next tool call would be gated again if a new `*_restoration_pending.json` exists.

### What if path extraction produces false positives?
Phase 3 uses conservative allowlist (`.py`, `.md`, `.txt`, `.json`, `.yaml`, `.yml`, `.toml`) plus `pathlib.Path.resolve()` validation against project root. Path traversal attempts resolve outside project root and are rejected.

### What if the state file cannot be read (permissions error)?
Fail-closed — if state file exists but can't be read, block all non-allowlisted tools. This is a security default.

### What if Phase 1 is deployed but Phase 2 isn't?
Schema versioning (R-2) prevents corruption. Old `pending_command_intent` readers see `schema_version: 1` and skip `skill_invoked` field. No parse error, no corruption.

---

## Consequences

**Positive**:
- AI cannot act unilaterally on restored state — eliminates Pattern #0 and #1 failures
- User sees full restore context before AI takes action
- Resume pattern is simple and unambiguous with R-1 fix
- TTL provides safety net without permanent blocking
- External validation: GitHub Issue #27319 confirms ~50% failure rate from this exact failure mode, validating the problem severity

**Negative**:
- Additional PreToolUse hook adds per-tool-call latency (local file read only — minimal)
- User must type "resume" to proceed — adds friction for seamless continuation
- Phase 1/2 coupling requires careful schema versioning discipline

**Mitigations**:
- R-1 removes fragile question-pattern overlay
- R-2 prevents schema corruption across phase deployments
- R-3 prevents TTL from racing thoughtful user composition

**Complementary Pattern — Context Essentials**:
The Post-Compaction Hook pattern (Nick Porter, Mar 2026) provides a complementary mechanism: a separate `context-essentials.md` file (~50 lines) re-injected via PostToolUse hook on `compact` matcher. This handles the "lost rules" problem — critical project conventions that get dropped from summarized context. The directive gate handles the "stale plan" problem. These two patterns are orthogonal and can coexist.

---

## Status After This Review

**NOT ACCEPTED** — return to author with 3 required refinements (R-1, R-2, R-3).

After refinements are applied, re-review with `/arch` or promote to **Accepted** if refinements are incorporated without substantive changes to the core design.
