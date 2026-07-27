---
thread_id: close-runner-needs-llm-check-block-20260726
parent_handoff_path: P:/docs/handoffs/close-scanner-bugs/HANDOFF.md
current_session_id: 019f9bfe-1b89-7602-9384-0212224ff30b
current_terminal_id: P%3A%5C
produced_at: 2026-07-27T00:45:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 25b93e102fd5e0c89391852e1ba92b949705c2d7
---

# close_runner.py rejects `needs_llm_check` gates — should emit one-line verdict per SKILL.md

## Objective

Fix `close_runner.py` so it does not hard-fail when a gate state is `needs_llm_check`. The SKILL.md explicitly says `needs_llm_check` should produce "one line in summary" — not block the close. Today's `/close` invocation hit this bug: the runner rejected the scanner output with "gates not clean: gate 'git_state' is 'needs_llm_check'", producing a CLOSE INCOMPLETE report despite the scanner having resolved all gates to known states with the LLM-judgment fields properly marked.

## The problem (one sentence)

`close_runner.py` treats `needs_llm_check` as a failure state (like `needs_attention`), but SKILL.md Step 2 says it should produce "one line in summary" — the runner has no way to accept the LLM's judgment that the gate is satisfied.

## Verified facts (with receipts)

- `[FACT]` SKILL.md Step 2 gate-state table (line 108-110): `needs_llm_check` action = "Check conversation context. Emit one-sentence verdict." Output = "One line in summary."
- `[FACT]` Scanner produced valid JSON with `git_state.state = "needs_llm_check"` and full detail: "receipt-proven session files already committed; 49 other uncommitted files remain; cross-repo checks need review: git_state_check exit 1." Receipt: `python ~/.grok/skills/close/__lib/close_accounting.py --session $sess --format json` this session.
- `[FACT]` Runner output verbatim: "Error: gates not clean: gate 'git_state' is 'needs_llm_check'" + "REJECT: terminal state is 'failed'". Receipt: `close_runner.py --session ... --variant standard` this session (two attempts).
- `[FACT]` Runner `--validate-claim` flag exists but is for post-close claim validation, not gate acceptance. Receipt: `close_runner.py --help` shows only `--session`, `--deadline`, `--variant`, `--validate-claim` flags.
- `[FACT]` The LLM had a valid judgment ready to emit ("49 P:/ + 6 ~/.grok uncommitted files are sibling sessions' in-flight work; session_write_paths empty; all receipt-proven session files committed; dirty_age clean. Ownership judgment: not this session's work.") but no way to deliver it through the runner.
- `[FACT]` Scanner detail showed `session_write_paths: []` (empty) and `receipt_count: 139` — meaning all this session's writes were receipt-proven committed. The `needs_llm_check` is purely about the cross-repo checks (sibling sessions' dirty files), which require LLM judgment, not mechanical resolution.
- `[FACT]` dirty_age.py returned `exit 0`, `status: clean`, `dirty_files: 49`, `stale_7d: 0` — all 49 dirty files are fresh (<1 day), so none are stale.
- `[FACT]` `/close` produced "CLOSE INCOMPLETE" output despite: scanner resolved all 14 gates; 7 `needs_attention` (auto-resolvable tier-1 items + LLM-judgment fields); 3 `needs_llm_check` (LLM judgment required); 4 `pre_satisfied` (mechanically complete).

## Root cause hypothesis

The runner's terminal-state logic (in `close_runner.py`) appears to use a strict gate-state allowlist (`pre_satisfied`, `skip`, `needs_attention` post-resolution) and rejects anything else as "not clean." But `needs_llm_check` is a valid terminal state per SKILL.md — the runner should accept the scanner output and pass it to the LLM for the one-line verdict, not reject the run.

The bug shape is: runner enforces a stricter contract than SKILL.md specifies. Either:
- (a) The runner was written before `needs_llm_check` was added to the gate-state vocabulary, and never updated
- (b) The runner was intentionally strict but the SKILL.md was later relaxed without updating the runner
- (c) The runner expects the LLM to do something specific (call a flag, emit a verdict line) before the runner accepts — but no such mechanism is documented or flagged

## Reproduction

```powershell
$sess = "<any session with git_state.needs_llm_check>"
python ~/.grok/skills/close/__lib/close_runner.py --session $sess --variant standard
# Expected per SKILL.md: scan completes, runner emits compact report with needs_llm_check as one-line entries
# Actual: runner exits 1 with "gates not clean: gate 'git_state' is 'needs_llm_check'"
```

The bug fires whenever any gate resolves to `needs_llm_check`. The most common trigger is the `git_state` gate when there are cross-repo uncommitted files (sibling sessions' in-flight work) — which is the normal state of this multi-agent workspace.

## Impact

- `/close` cannot complete cleanly on this workspace whenever sibling sessions have uncommitted work — which is the normal state, not the exception.
- The operator must either (a) manually inspect the scanner JSON to confirm gates are actually satisfied, (b) commit sibling sessions' work (wrong — not this session's responsibility), or (c) defer `/close` until sibling sessions commit (fragile coordination).
- The bug defeats the SKILL.md's "fast path" design: a session where the LLM has done `/wiki`, `/aar`, written handoffs, and verified work should produce a short structured report via the runner, but instead produces CLOSE INCOMPLETE.

## Recommended fix

Two options:

1. **Runner-side fix (preferred):** update `close_runner.py` terminal-state logic to accept `needs_llm_check` as a valid state that requires LLM judgment. The runner emits the compact report with `needs_llm_check` gates marked for LLM attention; the LLM fills the one-line verdict in the summary. No scanner changes needed.

2. **Scanner-side fix (alternative):** change the gate resolution logic so `git_state` doesn't fall to `needs_llm_check` when the session's own writes are all committed (`session_write_paths: []`). The cross-repo checks (`git_state_check exit 1` because of sibling dirty files) should produce an informational note, not block the gate. The LLM judgment ("those are siblings' files") becomes implicit — the scanner already has the data to make that determination.

**Recommended:** option 1. Option 2 hides the LLM-judgment step, which is a legitimate part of close (the operator may want to see the cross-repo state even when it's not this session's responsibility). Option 1 preserves the LLM's role while removing the spurious block.

## Dependencies

- **Requires:** nothing — bug is in code, fixable immediately.
- **Blocks:** clean `/close` invocations on any multi-agent workspace with concurrent sibling sessions.
- **Non-blocking to:** the close workflow as a whole — the LLM can produce a valid close summary by inspecting the scanner JSON directly (as this session did). But the runner's compact-renderer path is broken.

## Cross-reference couplings

- `C:/Users/brsth/.grok/skills/close/__lib/close_runner.py` — the buggy runner
- `C:/Users/brsth/.grok/skills/close/__lib/close_accounting.py` — scanner (produces correct `needs_llm_check` state)
- `C:/Users/brsth/.grok/skills/close/SKILL.md` lines 108-110 — the gate-state table the runner contradicts
- `P:/docs/handoffs/close-scanner-bugs/HANDOFF.md` — parent handoff for close-scanner bugs (BUG-01: AAR receipt session-ID binding; BUG-02: compact format KeyError; this is BUG-03)
- `P:/.agents/scripts/git_state_check.py` — the script whose `exit 1` (correctly) flags the cross-repo dirty state
- `P:/.agents/scripts/dirty_age.py` — the script whose `exit 0` correctly reports no stale files

## Other outstanding streams in this session (named, not handed off)

- **Scope-matching rule adoption** — handed off at `scope-matching-rule-adoption-post-redteam-20260726/HANDOFF.md` (BLOCK verdict; structural mechanism recommended)
- **Cross-transport model matrix** — handed off at `cross-transport-model-matrix-20260726/HANDOFF.md` (~90 tests across ~30 models × 3 transports)
- **Nemotron spawn failure investigation** — handed off at `nemotron-spawn-failure-investigation-20260726/HANDOFF.md` (technical question resolved via cross-transport test; revision block appended)

## Read first (related wiki concepts)

- `best-practices-enforcement-mechanism-grok-build.md` — the validated architecture (detection derives from external state + enforcement = block + prompt)
- `mandatory-step-enforcement-code-over-prose.md` — the prose-vs-code enforcement distinction (this bug is code-enforcement that contradicts its own prose spec)

## Last user message (verbatim)

> /handoff

## Provenance

Written from session 019f9bfe-1b89-7602-9384-0212224ff30b at `/close` time after the runner failed twice with "gates not clean: gate 'git_state' is 'needs_llm_check'." The session produced a valid close summary by inspecting the scanner JSON directly (bypassing the runner), but the bug should be fixed so future `/close` invocations don't require manual JSON inspection. Parent handoff `close-scanner-bugs-20260724/HANDOFF.md` is the prior batch of close-scanner bugs; this is a third bug in the same area.
