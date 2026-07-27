---
thread_id: operator-directive-capture-fix-20260727
parent_handoff_path: none
current_session_id: 019fa48a-fb52-79a3-b8dc-d13c5da284d2
current_terminal_id: grok-build-terminal
produced_at: 2026-07-27T12:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 916400f20303869c2ab4ede6b50c95fddb1114c2
---

# Operator-directive capture failure — fix shipped, refinement open

## Objective

Close the remaining refinement items from the "why didn't you know something you should have known" capture-failure fix. The three-layer fix (extractor + wiki concept + AGENTS.md rule) shipped this session; two refinements remain.

## Status

OPEN — core fix shipped, two refinements deferred.

## Problem

The operator stated a model routing preference (use opencode/PI, avoid OpenRouter) in prior sessions, but it was never promoted to a durable artifact. A future session couldn't find it and recommended the wrong default. The structural fix shipped: extractor script + qmd-indexed wiki concept + AGENTS.md retrieval gate. Two refinements remain.

## What shipped this session (all verified)

| Component | Artifact | Verified |
|---|---|---|
| Extractor | `P:/.agents/scripts/extract_operator_directives.py` | py_compile + ran on 1004 sessions (489 candidates, 40s) |
| Durable concept | `P:/.data/wiki/concepts/operator-model-routing-directives.md` | validator-passed, qmd-indexed (top-3 result for routing queries) |
| Retrieval gate | `~/.grok/AGENTS.md` § "Operator directive retrieval" | added under "Search before proposing" |
| Decision concept | `P:/.data/wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md` | validator-passed, qmd-indexed |
| Committed | git `6ec8e1b` | extractor + routing-directives concept |

## Read first

- **`P:/.data/wiki/concepts/operator-model-routing-directives.md`** — the confirmed directives (D1: Nemotron opencode→PI→OR, D2: K3 excluded, D3: prefer direct provider)
- **`P:/.agents/scripts/extract_operator_directives.py`** — the extractor (scoring system: PREFERENCE_SIGNALS × CONTEXT_SIGNALS)
- **`P:/.data/wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md`** — the architectural decision (mechanical > behavioral)
- `~/.grok/AGENTS.md` § "Operator directive retrieval" — the retrieval gate

## Open items

### O1: Strip `<skill_information>` blocks from extractor scoring (refinement)

**Problem:** the extractor scored 489 candidates, but many are false positives from skill body text embedded in user messages. When a user invokes `/red-team` or `/tp`, the skill body gets included in the user message and inflates scores with model/tool mentions.

**Fix:** strip `<skill_information>...</skill_information>` blocks from user message text before scoring in `extract_operator_directives.py`. Mechanical change — add a regex strip in `extract_user_text()` before returning.

**Why deferred:** the extractor is a proposal tool (human curation is the quality filter), so false positives don't affect correctness — they just add noise to the review file. The fix improves signal-to-noise but isn't blocking.

### O2: Scheduled vs on-demand extractor run (needs operator decision)

**Problem:** the extractor currently runs on-demand (`python extract_operator_directives.py`). A scheduled run (e.g., weekly via the scheduler tool) would catch directives more reliably.

**Decision needed:** should the extractor run on a schedule? If yes, what cadence (weekly? at session close?)? The operator hasn't weighed in on this — it's a workflow preference, not a technical decision.

**Why deferred:** genuinely the operator's call. On-demand works for now; scheduling adds a recurring task.

## Acceptance criteria

1. O1: `<skill_information>` blocks are stripped before scoring (test: a `/red-team` invocation no longer produces high-score candidates from the skill body)
2. O2: operator decides whether to schedule the extractor (and if yes, at what cadence)

## Next steps

1. **O1:** add regex strip to `extract_operator_directives.py:extract_user_text()` — `text = re.sub(r'<skill_information>.*?</skill_information>', '', text, flags=re.DOTALL)` before the scoring check. ~5 lines.
2. **O2:** ask the operator. If scheduled, add to `scheduler_create` with weekly cadence.

## Dependencies

- **Requires:** nothing (O1 is mechanical; O2 needs operator input)
- **Blocks:** nothing
- **Non-blocking to:** none

## Evidence

- `/why` RCA on capture failure: git diff proved the preference was not in any durable artifact pre-session
- Extractor run: 1004 sessions, 489 candidates, 40s wall time
- qmd findability verified: routing query returns `operator-model-routing-directives` as top-3

## Last user message (verbatim)

> /handoff

## Falsifier

This handoff is wrong if:
- The extractor's scoring is fundamentally broken (not just noisy) — would need to re-evaluate the PREFERENCE_SIGNALS × CONTEXT_SIGNALS approach
- The retrieval gate in AGENTS.md never fires in practice (buried and forgotten) — would need a hook-based enforcement instead
- The operator-directives concept goes stale (directives overturned but not updated)

## Other outstanding streams

- **`/packet` skill build** (`packet-skill-design-20260727`) — independent
- **Cross-transport model matrix** (`cross-transport-model-matrix-20260726`) — would extend the Nemotron routing context
