# Snapshot V2 + Recall System Validation — LLM Evaluation Prompt

You are a validation engineer running 32 pass/fail tests on a Claude Code hook system.
Your goal: determine whether the Snapshot V2 (PreCompact/PostCompact) and Recall (correction recovery) systems work correctly.

---

## What These Systems Do

### Snapshot V2 (PreCompact → PostCompact)
The system uses a **handoff envelope** with `resumesnapshot` field containing:
- `goal`, `currenttask`, `progresspercent`, `progressstate`
- `blockers`, `activefiles`, `pendingoperations`, `nextstep`
- `n1transcriptpath` (transcript path for evidence freshness)
- `terminalid` (terminal isolation key)
- Checksum validation via `computechecksum()` / `validateenvelope()`
- Evidence freshness via `verifyevidencefreshness()` comparing file content hashes

**State files**:
- Marker: `.claude/hooks/state/compaction-marker-{terminalid}.json`
- Envelope: `.claude/hooks/state/handoff/{terminalid}-handoff.json`

### Recall (PostCompact + SessionStart)
- **PostCompact** (primary): Intra-session compaction, uses Handoff V2 envelope
- **SessionStart** (fallback): New session resume, only fires when PostCompact didn't run
- **MEMORY.md** corrections: pattern-matched, SHA256-hashed for deduplication

### Why This Matters
After context compaction, the system preserves: what the session was trying to do, where it was, what evidence files look like (via checksums), and which MEMORY.md corrections apply.

---

## Role: Validation Engineer

Execute all 32 tests in order. For each test:
1. Read the test procedure
2. Run the test (trigger /compact, inspect files, call functions directly)
3. Compare against pass/fail criteria
4. Document evidence: exact file paths, JSON excerpts, line numbers

Output one structured test report per test.

---

## Test Execution Order

### PHASE 1: SNAPSHOT V2 VALIDATION (18 tests, must pass before Phase 2)

Run S1.1 through S5.3 in order. S1.x must pass before S2.x.

---

**S1.1 — Required fields populated (CRITICAL)**

*Reference matrix: "Envelope contains non-null values for: goal, currenttask, progresspercent, progressstate, blockers, activefiles, pendingoperations, nextstep, n1transcriptpath"*

- Procedure: Trigger /compact, read the handoff envelope JSON at `~/.claude/hooks/state/handoff/{terminalid}-handoff.json`, inspect `resumesnapshot` field
- Pass: All 9 required fields present with non-empty, semantically correct values (not placeholders like "Unknown task" or null)
- Fail: Any required field is null, empty string, or contains placeholder/default value
- Evidence: Quote the `resumesnapshot` JSON showing all 9 required fields with values

---

**S1.2 — Goal extraction accuracy**

*Reference matrix: "Goal field reflects actual user intent, not meta-discussion or stale context"*

- Procedure: Compare `resumesnapshot.goal` against the last substantive user message in the transcript
- Pass: goal matches last substantive user message or slash-command, not "Unknown task" or meta-noise
- Fail: goal is "Unknown task", "Continue current task", or extracted from meta-discussion
- Evidence: Side-by-side quote of `resumesnapshot.goal` vs last substantive user message from transcript

---

**S1.3 — Active files extraction**

*Reference matrix: "activefiles list contains the files actually being edited/read in the session"*

- Procedure: Cross-check `resumesnapshot.activefiles` against Edit/Read tool_use entries in transcript
- Pass: activefiles list contains 1+ actual file paths from Edit/Read operations, not empty array
- Fail: activefiles is empty array despite session having Edit/Read operations
- Evidence: Side-by-side list of activefiles array vs files from Edit/Read tool_use blocks in transcript

---

**S1.4 — Pending operations extraction**

*Reference matrix: "Pending operations list captures incomplete work (skill invocations, edits, commands)"*

- Procedure: Check `resumesnapshot.pendingoperations` array — verify type/target/state match last incomplete operations in transcript
- Pass: pendingoperations array length > 0 when session has incomplete work; accurate type/target/state per operation
- Fail: pendingoperations is empty when session clearly has incomplete skill invocations or mid-edit state
- Evidence: Side-by-side: pendingoperations array vs incomplete operations visible in transcript end

---

**S1.5 — Optional fields wiring**

*Reference matrix: "openquestions and taskssnapshot fields are present and populated when transcript contains questions or tasks"*

- Procedure: Read envelope, check if `openquestions`/`taskssnapshot` keys exist and have length > 0 when expected
- Pass: openquestions array populated when user asked questions; taskssnapshot populated when tasks tracker has active items
- Fail: openquestions always empty even when transcript has '?' user messages; taskssnapshot always empty despite tasks existing
- Evidence: JSON showing openquestions/taskssnapshot arrays when applicable

---

**S2.1 — PostCompact uses envelope (CRITICAL)**

*Reference matrix: "PostCompact additionalContext is derived from the handoff envelope, not hardcoded text or stale state"*

- Procedure: Trigger /compact, read PostCompact hook output JSON, extract `additionalContext` field
- Pass: PostCompact additionalContext contains text matching the envelope's goal/nextstep/activefiles
- Fail: PostCompact additionalContext is generic text, Stop hook feedback, or unrelated to envelope
- Evidence: PostCompact hook JSON output showing additionalContext field; envelope JSON showing matching values

---

**S2.2 — Restore message completeness**

*Reference matrix: "Restore message includes goal, next step, active files, pending ops from envelope"*

- Procedure: After /compact, check first assistant message for presence of envelope-derived context
- Pass: Restore message visible in first post-compact turn contains all envelope fields in structured format
- Fail: Restore message missing any of: goal, currenttask, nextstep, activefiles, pendingoperations
- Evidence: First post-compact assistant message text with highlighted goal/nextstep/activefiles/pendingops sections

---

**S2.3 — No fallback path confusion**

*Reference matrix: "System does not fall back to SessionStart restore or UserPromptSubmit injector when PostCompact should fire"*

- Procedure: Trace hook execution — verify PostCompact fired once, SessionStart did not fire, UserPromptSubmit did not inject duplicate state
- Pass: Only PostCompact fires for intra-session compaction; SessionStart fires only for new session resume
- Fail: Both PostCompact and SessionStart fire for same compaction; or UserPromptSubmit injector fires when PostCompact should
- Evidence: Hook execution log showing which hooks fired and in what order

---

**S2.4 — Restore format matches design**

*Reference matrix: "Restore format matches compact-restore block or verbose SESSION HANDOFF V2 format per design"*

- Procedure: Inspect restore message text format against `snapshot_v2.py`'s `buildrestoremessagecompact()` or `buildrestoremessageverbose()` output
- Pass: Restore text starts with 'compact-restore' or 'SESSION HANDOFF V2' header; contains structured sections for workstate/openloops/toolqueue
- Fail: Restore text is unstructured prose, missing section headers, or uses deprecated Pre-Mortem format
- Evidence: Restore message text with format structure visible (headers, sections, no prose)

---

**S3.1 — Terminal ID consistency (CRITICAL)**

*Reference matrix: "Same terminal ID used in: PreCompact capture, envelope file path, PostCompact restore, marker file"*

- Procedure: After /compact, inspect: (1) envelope `resumesnapshot.terminalid`, (2) envelope file name, (3) marker file name, (4) PostCompact input terminal ID
- Pass: Terminal ID matches across all 4 locations
- Fail: Terminal ID differs between any two of: envelope field, file path, marker, restore session
- Evidence: List showing: envelope.terminalid, envelope file name, marker file name, restore session terminal ID — all matching

---

**S3.2 — Cross-terminal rejection**

*Reference matrix: "Restore rejects envelope when terminalid in envelope != current session's terminal ID"*

- Procedure: Manually edit envelope terminalid to mismatch; trigger restore; verify rejection
- Pass: `evaluateforrestore()` returns `ok=False` with `reason='terminal mismatch'` when envelope terminalid != restore session terminalid
- Fail: Envelope from terminal A is restored in terminal B without rejection
- Evidence: `evaluateforrestore()` output showing rejection when terminal IDs differ

---

**S3.3 — Marker-envelope pairing**

*Reference matrix: "Compaction marker file and handoff envelope use same terminal ID; marker triggers correct envelope load"*

- Procedure: Check marker file name and envelope file name after PreCompact — confirm they share same terminal ID
- Pass: Marker file `.claude/hooks/state/compaction-marker-{terminalid}.json` exists after PreCompact; PostCompact reads matching `{terminalid}-handoff.json`
- Fail: Marker file uses terminal X but PostCompact loads envelope for terminal Y
- Evidence: File listing showing `compaction-marker-{tid}.json` and `{tid}-handoff.json` with same `{tid}`

---

**S4.1 — Checksum validation**

*Reference matrix: "Envelope checksum is validated on restore; corrupted envelope rejected"*

- Procedure: Modify `envelope.checksum` manually; attempt restore; verify `SnapshotValidationError`
- Pass: `validateenvelope()` raises `SnapshotValidationError` when `envelope.checksum != computechecksum(envelope)`
- Fail: Corrupted envelope (modified checksum) is accepted without validation error
- Evidence: `SnapshotValidationError` traceback showing checksum mismatch

---

**S4.2 — Evidence freshness gating (CRITICAL)**

*Reference matrix: "Restore rejected when transcript or file evidence content hashes no longer match"*

- Procedure: Capture envelope; edit a file listed in evidenceindex; trigger restore; verify rejection
- Pass: `verifyevidencefreshness()` returns error message when file contenthash != current file hash; restore blocked
- Fail: Restore succeeds despite file or transcript content changing since capture
- Evidence: `verifyevidencefreshness()` return value showing 'snapshot evidence changed: <filename>' when file edited

---

**S4.3 — Stale rejection behavior**

*Reference matrix: "Stale rejection produces clear error message; envelope status transitions to 'rejected-stale'"*

- Procedure: Force stale scenario (edit file or wait past expiry); attempt restore; check error message and envelope status
- Pass: Stale restore attempt produces message 'HANDOFF NOT RESTORED... Reason: snapshot evidence changed' or similar; `envelope.resumesnapshot.status = 'rejected-stale'`
- Fail: Stale rejection produces generic error; envelope status remains 'pending' instead of transitioning
- Evidence: Stale rejection message text; envelope JSON showing `status='rejected-stale'` and `rejectionreason` field

---

**S5.1 — Capture failure logging**

*Reference matrix: "PreCompact failure produces clear error in hook output and logs; does not silently fail"*

- Procedure: Break PreCompact (invalid transcript path, permission error); trigger compact; check hook output and logs
- Pass: PreCompact hook error produces `decision='block'` with `reason` field explaining failure; logged to `.claude/logs/handoff_capture.log`
- Fail: PreCompact fails silently; no error message, no log entry
- Evidence: PreCompact error output showing `decision='block'` and `reason`; log file excerpt showing error

---

**S5.2 — State file diagnostics**

*Reference matrix: "State file existence, permissions, content validity can be diagnosed without reading code"*

- Procedure: Inspect `.claude/hooks/state/handoff/` and `.claude/hooks/state/` for marker/envelope files; verify JSON validity
- Pass: State dir lists marker file, envelope file, with terminal ID visible; envelope is valid JSON; permissions allow read
- Fail: State files are binary, unreadable JSON, or missing; no way to inspect without debugging
- Evidence: Directory listing of state files; cat envelope.json to verify valid JSON

---

**S5.3 — Restore path tracing**

*Reference matrix: "Restore path can be traced: which hook fired, which envelope loaded, why accepted/rejected"*

- Procedure: Trigger restore; read hook output and `.claude/logs/handoff_capture.log` for restore decision rationale
- Pass: PostCompact or SessionStart output includes 'loaded envelope from <path>' or 'rejected: <reason>'; logs show full restore decision
- Fail: Restore happens or doesn't happen with no visible reason; no log of which envelope was loaded or why rejected
- Evidence: Restore hook output or log showing 'envelope loaded from X' or 'rejected because Y'

---

### PHASE 2: RECALL VALIDATION (14 tests, blocked until Phase 1 passes)

Run R1.1 through R4.3 after S1.1 and S2.1 pass.

---

**R1.1 — Relevant MEMORY.md selection (HIGH)**

*Reference matrix: "PostCompact/SessionStart injects 1-3 MEMORY.md corrections relevant to current task, not random entries"*

- Procedure: After compact, inspect PostCompact additionalContext; count MEMORY.md entries; verify relevance to goal/files
- Pass: PostCompact additionalContext contains 1-3 short MEMORY.md corrections tied to current goal/files/operations; not a dump
- Fail: PostCompact injects >5 MEMORY.md entries, or entries unrelated to goal/files; or injects all corrections indiscriminately
- Evidence: PostCompact output showing 1-3 MEMORY.md corrections with task-relevance highlighted

---

**R1.2 — CLAUDE.md non-injection (HIGH)**

*Reference matrix: "Full CLAUDE.md is NOT injected at UserPromptSubmit or PostCompact; only referenced at session start if needed"*

- Procedure: Grep all hook outputs for 'CLAUDE.md' inline text longer than 10 lines
- Pass: No hook output contains full CLAUDE.md text; SessionStart may reference 'See CLAUDE.md for principles' but not inline full text
- Fail: UserPromptSubmit or PostCompact includes 50+ lines of CLAUDE.md principles
- Evidence: Hook output showing no CLAUDE.md dumps (or only 1-line reference)

---

**R1.3 — Tool-specific reminder routing**

*Reference matrix: "PreToolUse injects tool-specific reminder only when tool/path matches known risk pattern"*

- Procedure: Trigger PreToolUse on safe tool (Read); verify no injection. Trigger on git checkout; verify targeted reminder appears.
- Pass: PreToolUse fires only for high-risk tools with 1-3 line reminder specific to that tool+path (e.g., 'git checkout: run git diff --cached first')
- Fail: PreToolUse fires on every tool call with same generic text; or fires on safe tools (Read, List) unnecessarily
- Evidence: PreToolUse output on safe vs. risky tools; showing selective firing

---

**R1.4 — No generic reminder spam (MEDIUM)**

*Reference matrix: "System does not inject generic reminders without task-specific context"*

- Procedure: Search all injected context for generic phrases; verify each has specific file/tool/task context
- Pass: Generic reminders absent; all injected text ties to specific file, tool, or task context
- Fail: Injected text includes 'always verify', 'best practice', 'remember to' without specific context
- Evidence: List of all injected reminders with specificity check (file/tool/task mentioned)

---

**R2.1 — PostCompact priority (CRITICAL)**

*Reference matrix: "PostCompact is highest-priority injection point; SessionStart is fallback only"*

- Procedure: Compact mid-session; verify PostCompact fires. Start new session; verify SessionStart fires; check no overlap.
- Pass: PostCompact fires for intra-session compaction; SessionStart fires only when new session starts without prior PostCompact state
- Fail: SessionStart fires for intra-session compaction, duplicating PostCompact; or PostCompact never fires
- Evidence: Hook execution log showing PostCompact for compaction, SessionStart for new session only

---

**R2.2 — Size cap enforcement (CRITICAL)**

*Reference matrix: "PostCompact ≤25 lines, PreToolUse ≤5 lines, SessionStart ≤20 lines"*

- Procedure: Count lines in each hook's additionalContext output; verify caps
- Pass: Line count of PostCompact ≤25, PreToolUse ≤5, SessionStart ≤20; no bloat
- Fail: Any injection exceeds line cap; verbose prose or dumps present
- Evidence: Line counts of hook outputs with caps annotated

---

**R2.3 — Deduplication**

*Reference matrix: "Same reminder not injected multiple times in same session or consecutive turns"*

- Procedure: Manually inject same reminder twice; verify second instance suppressed; check dedup log
- Pass: Dedup logic visible in code or logs; same text not in last 5 turns
- Fail: Same reminder appears in turns N, N+1, N+2 without change
- Evidence: Dedup log or code showing 'reminder X skipped: shown in last 3 turns'

---

**R2.4 — Flow-state non-interruption (MEDIUM)**

*Reference matrix: "No reminders injected during active tool-call flow (5+ consecutive calls); PostToolBatch used instead"*

- Procedure: Issue 5+ Edit calls in sequence; verify no mid-flow injection; verify PostToolBatch fires after
- Pass: During 5+ tool call sequence, no UserPromptSubmit or PreToolUse injections; PostToolBatch summary fires after sequence ends
- Fail: Reminders inject mid-flow, interrupting 5+ tool call sequences
- Evidence: Tool call sequence with no mid-flow injection; PostToolBatch output after sequence

---

**R3.1 — Reminder changes action (HIGH)**

*Reference matrix: "Injected reminder demonstrably changes LLM behavior"*

- Procedure: A/B test — run same task with and without reminder; measure behavior difference (tool choice, verification step, etc.)
- Pass: Agent follows correction without prompting
- Fail: Agent ignores correction, no behavior change
- Evidence: Side-by-side: LLM response with reminder (follows rule) vs. without reminder (violates rule)

---

**R3.2 — Ignored reminder escalation (HIGH)**

*Reference matrix: "When same reminder ignored 3+ times, system escalates to blocking validator"*

- Procedure: Track reminder violations in test log; after 3, check if blocker was added to PreToolUse or Stop hook registry
- Pass: After 3 violations of same rule, new blocking PreToolUse or Stop hook added; reminder no longer injected
- Fail: Same reminder injected 5+ times across sessions with no escalation to blocker
- Evidence: Escalation log showing 'rule X violated 3x, adding blocker'; code diff showing new PreToolUse check

---

**R3.3 — Stop hook vs reminder separation (MEDIUM)**

*Reference matrix: "Stop hook violations (EPISTEMIC, fabrication) are NOT in reminder additionalContext; they block, not remind"*

- Procedure: Grep PostCompact additionalContext for 'EPISTEMIC', 'VIOLATION', 'Stop hook'; verify absence
- Pass: PostCompact additionalContext never contains Stop hook feedback or EPISTEMIC VIOLATION text
- Fail: PostCompact output shows 'EPISTEMIC VIOLATION' or Stop hook residue instead of task-relevant corrections
- Evidence: PostCompact output showing task continuity + MEMORY.md corrections only, no validator residue

---

**R4.1 — Relevance scoring (MEDIUM)**

*Reference matrix: "Reminder selection uses relevance score (goal keywords, file path match, recent violation)"*

- Procedure: Inspect reminder selection code for scoring logic; verify higher-scored items selected
- Pass: Relevance scoring visible in code or logs; injected reminders score higher than skipped ones based on goal/file/violation recency
- Fail: Reminders selected randomly or chronologically; no scoring logic
- Evidence: Code showing relevance scoring algorithm; log showing scores for each candidate reminder

---

**R4.2 — Context budget awareness (MEDIUM)**

*Reference matrix: "System checks context size before injection; skips reminders if context >80% full"*

- Procedure: Simulate high context load; trigger injection; verify skipping or truncation
- Pass: Context size check before injection; log shows 'context 85% full, skipping reminder' or similar
- Fail: Reminders injected regardless of context size; context overflow errors
- Evidence: Log showing context size check and skip decision

---

**R4.3 — Freshness filtering (MEDIUM)**

*Reference matrix: "Reminders not re-injected if same text was in last 200 lines of context"*

- Procedure: Inject reminder; immediately trigger compact; verify same reminder not re-injected in PostCompact
- Pass: Freshness filter log shows 'reminder X already in context at line Y, skipping'
- Fail: Same reminder re-injected despite being in recent context
- Evidence: Log showing 'reminder already present at context offset X, skipping'

---

## Output Format

For each test, produce:

```
## T-{TEST_ID}: {Test Name}

**Result**: PASS / FAIL / BLOCKED

**Evidence**:
- [Exact file path or command]
- [JSON excerpt or screenshot]
- [Line numbers where relevant]

**Findings**:
- [What worked]
- [What failed]
- [Root cause if failed]

**Verdict**: [One-line summary]
```

---

## Critical Rules

1. **Evidence is mandatory** — no test passes without documented evidence. "It seemed to work" is not evidence.
2. **No partial credit** — a test either passes all criteria or fails. Mixed results = FAIL.
3. **Follow test order** — dependency chain matters. S1.x before S2.x. Phase 1 before Phase 2.
4. **Quote exact text** — when quoting JSON, file contents, or CLI output, quote exactly (including whitespace).
5. **Document failures completely** — for FAIL, explain WHY it failed, not just that it did.
6. **Test in isolation** — don't let one test's output influence another test's evaluation.

---

## Field Reference

This system uses `resumesnapshot` field inside the handoff envelope:

| Field | Description |
|-------|-------------|
| `goal` | Canonical session intent from last substantive user message |
| `currenttask` | Current task being worked on |
| `progresspercent` | Estimated completion percentage |
| `progressstate` | Current state (e.g., 'in_progress', 'blocked', 'waiting') |
| `blockers` | Known blockers or obstacles |
| `activefiles` | Files currently being edited/read |
| `pendingoperations` | Incomplete operations (skill invocations, edits, commands) |
| `nextstep` | Next action to take |
| `n1transcriptpath` | Transcript path (for evidence freshness checks) |
| `terminalid` | Terminal isolation key |
| `openquestions` | Open questions from the session |
| `taskssnapshot` | Tasks tracker snapshot |

Envelope path: `~/.claude/hooks/state/handoff/{terminalid}-handoff.json`
Marker path: `~/.claude/hooks/state/compaction-marker-{terminalid}.json`
Evidence index: `envelope.evidenceindex[]` — file paths with content hashes for freshness validation

---

## Priority Guidance (If Time-Limited)

If you cannot run all 32 tests, run these first in order:

1. **S1.1** (Required fields) — if this fails, nothing else matters
2. **S2.1** (PostCompact uses envelope) — core restore function
3. **S3.1** (Terminal ID consistency) — cross-terminal safety
4. **S4.1** (Checksum validation) — integrity guarantee
5. **S4.2** (Evidence freshness gating) — the system's key differentiator
6. **R2.1** (PostCompact priority) — recall order matters

If all 6 pass, the system is probably viable. If any fail, the system has fundamental problems.

---

## Known Issue Watch List

Based on prior analysis, these failure modes are likely:

- **S1.1 (Required fields)**: optional fields (openquestions, taskssnapshot) may be missing or null
- **S1.2 (Goal accuracy)**: goal may be "Unknown task" or generic if transcript extraction fails
- **S2.4 (Restore format)**: may be unstructured prose instead of structured sections
- **S4.1 (Checksum)**: checksum may not be validated on restore (dead code path)
- **S4.2 (Evidence freshness)**: verifyevidencefreshness() may never run or always pass
- **R2.2 (Size caps)**: hardcoded injections may exceed line caps
- **R3.3 (Stop hook separation)**: PostCompact additionalContext may contain EPISTEMIC VIOLATION text from Stop hooks

---

## Files to Reference

| File | Path |
|------|------|
| Snapshot validation matrix | `P:/.claude/.artifacts/snapshot_validation_matrix.csv` |
| Recall validation matrix | `P:/.claude/.artifacts/recall_validation_matrix.csv` |
| Test priority guide | `P:/.claude/.artifacts/test_priority_guide.csv` |
| Handoff envelope schema | `P:/packages/snapshot/scripts/hooks/__lib/snapshot_v2.py` |
| PreCompact hook | `P:/.claude/hooks/PreCompact.py` |
| PostCompact hook | `P:/.claude/hooks/PostCompact.py` |
| SessionStart_reminder_recovery | `P:/.claude/hooks/SessionStart_reminder_recovery.py` |

---

## Start Now

Begin with S1.1. Trigger /compact, inspect state files, and work through all tests in order.

Report results using the output format above for each test.