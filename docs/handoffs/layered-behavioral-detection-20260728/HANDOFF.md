---
thread_id: layered-behavioral-detection-20260728
parent_handoff_path: none
current_session_id: 019fa48a-fb52-79a3-b8dc-d13c5da284d2
current_terminal_id: grok-build-terminal
produced_at: 2026-07-28T15:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: LATEST
---

# Layered behavioral detection — structural checks + periodic self-check

## Objective (one sentence)

Build the medium and long-term tiers of the behavioral detection architecture:
structural checks (PostToolUse: did the model search before recommending?)
and periodic LLM-as-judge self-check (batched /tp check on last N turns).

## Status

PARTIALLY RESOLVED — Tier 1 shipped + lastAssistantMessage bug fixed.
Tier 2 found already handled by quality_gate.py Stop hook. Tiers 3-4 remain open.

## RESOLVED (2026-07-28): Tier 1 lastAssistantMessage bug + Tier 2 coverage

### lastAssistantMessage payload bug (CRITICAL)

Both `behavioral_check.py` and `wiki_persistence_check.py` used the wrong field
name to extract the response text from the Stop hook payload. They checked
`response`, `messages`, and `transcript_path` — but the Grok Build Stop hook
provides `lastAssistantMessage` (user-guide/10-hooks.md:262).

Without this fix, both hooks would have been **permanently silent in production**.
Fixed by adding `lastAssistantMessage` as the first check in
`extract_response_text()`. Verified end-to-end with realistic payloads.

Existing hooks (`dbr_language_check.py`, `quality_gate.py`) already used the
correct field — only the new hooks had the bug.

### Tier 2 already handled by quality_gate.py

The "Tier 2 gap" (nothing fires between per-edit and per-session) was identified
as a missing PostToolUse advisory hook. Investigation revealed:

1. **PostToolUse stdout is ignored on Grok Build** (user-guide/10-hooks.md:304):
   "For events like SessionStart or PostToolUse, stdout is ignored."
2. The existing `quality_gate.py` Stop hook already enforces scoped-test
   verification: it tracks code modifications, blocks at end of turn with
   specific file hints (`_build_file_hints`), and creates continuation
   obligations that require satisfying receipts.
3. The "gap" was actually caused by the capability derivation bug — the Stop
   hook was blocking hook script edits with `NO_COVERING_RECEIPT` because
   `runtime_hook` (rank 5) exceeded what pytest provides (`unit_behavior`, rank 3).
   Fix: `quality_gate.py _derive_required_capability` now classifies hook
   scripts as `static_analysis` (rank 2). See
   [[hook-script-capability-derivation-receipt-loop-fix]].

**Conclusion:** Tier 2 is already handled by the existing Stop hook. No new
PostToolUse hook needed. The Stop hook fires at the right time (end of turn,
when the agent claims completion) with the right enforcement level (block
until verified, not just advise).

## What's already shipped (this session)

1. **Behavioral anti-pattern detector** (`~/.grok/hooks/scripts/behavioral_check.py`)
   — Stop hook, regex patterns for fabricated fatigue, unnecessary deferral,
   deferred persistence, narrative closure, equivalence claims. Non-blocking.
   12/12 tests pass.

2. **Wiki persistence verifier** (`~/.grok/hooks/scripts/wiki_persistence_check.py`)
   — Stop hook, checks that referenced wiki concepts exist on disk. Catches
   "I'll write that" → never wrote it.

3. **Premier-model path in /tp** — /tp SKILL.md updated with /agy, /codex,
   and grok-4.5 as premier options for high-stakes critique where anti-sycophancy
   matters.

## What this handoff covers

### Tier 2: Structural checks (PostToolUse hook)

**The gap:** nothing fires between "I finished editing this file" and "let me
run /check on the whole session." A PostToolUse hook that detects "N edits to
.py files since last scoped test run" would remind/incentivize running scoped
tests.

**Design:**
- PostToolUse hook on Write/Edit/search_replace tools
- Counter: track .py file edits since last `pytest` call
- When counter > threshold (e.g., 3), emit advisory: "N code files edited
  since last test run — consider running scoped tests"
- Non-blocking, advisory only

**Acceptance criteria:**
1. PostToolUse hook fires after code edits
2. Counter resets when pytest is detected in run_terminal_command
3. Advisory message is non-blocking and actionable

### Tier 3: Periodic LLM-as-judge self-check

**The gap:** some violations (question-reframing, complex workarounds) can't
be detected by regex or structural checks. They require judgment.

**Design:**
- Run a `/tp check` on the last N turns periodically (every 10 turns or at
  skill boundaries)
- Use the /notice skill's infrastructure for mid-conversation surfacing
- The check runs as a lightweight inline scan, not a full subagent spawn
- Catches: question-reframing, answer-the-wrong-question, over-engineering

**Acceptance criteria:**
1. Periodic check fires at skill boundaries (not every turn — too expensive)
2. Uses /notice's trigger infrastructure (T2 task boundary)
3. Non-blocking, advisory

### Tier 4: Search-before-recommendation enforcement

**The gap:** the #1 rule in AGENTS.md ("search before proposing") is still a
behavioral rule. The operator caught it being violated twice this session.

**Design:**
- PostToolUse hook: when `write` or `search_replace` is called on a file that
  looks like a recommendation (config, AGENTS.md, skill file), check whether
  `qmd search` or `grep` was called in the same turn
- If not, emit advisory: "writing a recommendation without preceding search"
- False positive risk: legitimate edits that don't need search. Gate on
  specific file patterns (AGENTS.md, config files, skill files)

**Acceptance criteria:**
1. PostToolUse fires on writes to AGENTS.md, config, skill files
2. Checks for preceding grep/qmd search in the same session turn
3. Advisory, non-blocking

## Falsifier

This design is wrong if:
- The PostToolUse hooks add noticeable latency (>50ms per edit)
- The advisory messages become noise (fire too often)
- The periodic self-check consumes too many tokens

## Related

- Wiki: [[model-fit-and-post-hoc-behavioral-detection]]
- Wiki: [[mechanical-enforcement-over-behavioral-reminder]]
- Wiki: [[verification-receipt-systems-design-landscape]]
- Handoff: verification-protocol-design-20260728 (the 5-tier model)
- Hooks shipped: behavioral_check.py, wiki_persistence_check.py
