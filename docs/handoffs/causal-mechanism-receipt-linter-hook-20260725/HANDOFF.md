---
thread_id: causal-mechanism-receipt-linter-hook-20260725
parent_handoff_path: none
current_session_id: 019f96f5-dc4a-79d0-9e17-396f2a582186
current_terminal_id: console_9f93f0d3-0b5b-4985-b779-6a2c
produced_at: 2026-07-26T01:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: beb1a58
---

# Handoff: linter hook for causal-mechanism claims in wiki concepts

## Objective

Implement a PreToolUse or PostToolUse hook that greps newly-written wiki concept files for causal-mechanism phrasing ("X happens because...", "the scanner does X", "the system works by...") and warns if no `receipt:` field or `file:line` citation is present. Structural enforcement for the rule documented in `wiki/concepts/causal-mechanism-claims-require-source-receipts-before-durable-write.md`.

## Why this matters

The wiki concept documenting this rule was itself written from inference, then corrected after operator pushback ("explain clearly"). The behavioral rule (read source before writing mechanism claim) is fresh in memory now but will decay. Structural enforcement catches what behavior misses — same lesson as the existing Stop hooks for unverified claims.

**Worked example (the incident this would catch):** session 019f96f5 wrote `close-scanner-verification-gap-stale-read.md` claiming "scanner greps only the parent transcript" without reading `close_accounting.py`. Hook would have fired: "Concept contains 'the scanner' + causal phrasing; no `receipt:` field. Read the source before shipping."

## Scope

### Trigger conditions (all must be true)

- File path matches `.data/wiki/concepts/*.md` (new file or modification)
- File content contains one or more causal-mechanism phrases:
  - `X happens because`
  - `the scanner <verb>`
  - `the system <verb>`
  - `the gate <verb>`
  - `the hook <verb>`
  - `<noun> works by`
  - `<noun> can't see <noun>`
- File does NOT contain a receipt marker:
  - `receipt:` (lowercase, followed by citation)
  - `lines \d+-\d+` (line-number citation)
  - `:\d+` (file:line citation)

### Action

- **Warn, not block.** Hook prints: "⚠️ Concept <path> contains causal-mechanism claims without a receipt citation. Read the source before shipping. Bypass: re-run with same intent."
- Exit code: 0 (warn only — same model as precommit-sibling-collision-hook)
- Bypass: if the operator says "ship anyway" or the content already has receipt markers, hook does not re-fire

## Alternatives considered

1. **Block instead of warn** — too aggressive; many wiki concepts legitimately discuss systems without needing receipts (e.g., "the agent should..." is prescriptive, not causal). False positives would block legitimate writes.

2. **LLM-as-judge hook** — spawn a subagent to evaluate whether each causal claim has a receipt. **Pro:** more accurate than regex. **Con:** expensive (one subagent spawn per wiki write); the regex catches the 80% case (presence of causal phrasing + absence of receipt markers).

3. **Require `receipt:` field for every wiki concept** — too strict; concepts that document decisions (not mechanisms) don't need receipts.

4. **Behavioral rule only (no hook)** — the wiki concept already does this. **Decision:** insufficient; behavior decays under closure pressure (proven by the incident this handoff addresses).

## Acceptance criteria

- [ ] Hook fires on writes to `.data/wiki/concepts/*.md`
- [ ] Hook matches the trigger phrases (causal-mechanism indicators)
- [ ] Hook checks for receipt markers (line citations, `receipt:` field)
- [ ] Hook warns (does not block) when triggers fire and receipts absent
- [ ] Hook is silent when receipts present
- [ ] Hook is silent for non-causal content (prescriptive, declarative, narrative)
- [ ] Test: re-write the original (uncorrected) `close-scanner-verification-gap-stale-read.md` — hook should warn
- [ ] Test: write a concept with receipt citations — hook should be silent
- [ ] Performance: hook runs in <500ms (regex-only, no tool calls)

## Implementation notes

- **Where to install:** `~/.grok/hooks/` as a `PreToolUse` or `PostToolUse` hook matching `write`/`search_replace`/`edit` tools targeting `.data/wiki/concepts/`
- **Matcher:** `\.data/wiki/concepts/.*\.md$` on the file_path argument
- **False-positive risk:** prescriptive claims ("the agent should read the source") use similar phrasing but don't need receipts. Mitigation: only fire when the phrase is in past/present tense ("the scanner does", not "the scanner should"). Imperative/prescriptive mood = skip.
- **Receipt marker format:** tolerate `receipt: <file>:<lines>`, `receipt: <file>:<line>-<line>`, `Lines 422-510`, `:422`, `file:line` patterns.

## Dependencies

- Requires: nothing
- Blocks: nothing
- Non-blocking to: precommit-sibling-collision-hook, close-scanner-check-receipts

## Out of scope

- Linting handoffs, ADRs, or commit messages (different surface; could be added later if pattern proves valuable)
- LLM-based judgment of receipt adequacy (regex is enough for v1)
- Auto-fixing (just warn; the operator/agent fixes manually)

## Related artifacts

- Wiki concept: `causal-mechanism-claims-require-source-receipts-before-durable-write.md` (the rule this hook enforces)
- Incident: `close-scanner-verification-gap-stale-read.md` was written without receipts, corrected after operator pushback
- Existing pattern: Stop hooks for unverified claims (same structural-enforcement philosophy)

## Status

OPEN — ready for implementation. Lower priority than the close-scanner-check-receipts fix because the behavioral rule is fresh; raise priority if the pattern recurs within 30 days.
