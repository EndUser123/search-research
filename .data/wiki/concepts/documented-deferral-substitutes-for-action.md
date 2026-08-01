---
title: "Documented deferral: when documentation substitutes for action"
created: 2026-07-25
updated: 2026-07-25
source: AAR session 019f9b00 (Phase 9.5 auto-promotion)
sources:
  - internal: P:/.artifacts/grok-aar/console_console_63757421-7248-458c-8c7b-a1bb/20260725-221800/aar-report.md
tags: [agent-failure-mode, narrative-as-signal, process-discipline, same-turn-fix, multi-phase-skill-flow, deferred-action]
agent: grok
host: grok
cognitive_load: 2
verification: single-session-observed
summary: >
  When an agent discovers a defect or holds an easy decision mid-flow through a
  multi-phase skill (handoff-writing, close orchestration, plan execution), the
  path of least resistance is to *document* the issue for the next session
  rather than *interrupt the current flow to fix it*. This is structurally the
  same failure class as `narrative-as-signal` (plausible story substituting for
  verification), applied to the agent's own process: the documentation feels
  like action but isn't. The fix is a same-turn rule — if the agent has already
  diagnosed the defect AND the fix is cheap, fix it now; documentation is not a
  substitute.
---

# Documented deferral: when documentation substitutes for action

## The pattern

In a multi-phase skill flow (e.g., `/close` orchestrating 14 gates, `/handoff`
assembling 16 mandatory fields, `/go` executing waves), the agent discovers a
defect or holds a decision it could resolve. Instead of interrupting the flow
to fix it, the agent writes a note about it — in a handoff section, an
observations handoff, a "flagged for next session" aside. The note-taking
feels like progress. It is not.

**Three instances from session 019f9b00 (2026-07-25):**

1. **Stale `accurate_as_of_head`** — agent knew at handoff-write time that the
   SHA was stale (real HEAD had moved twice). Documented in the handoff's
   cross-reference couplings section + a session-observations handoff (O1).
   Did not run `git rev-parse HEAD` to fix it. Operator caught it: "for now,
   fix it. and can you fix the root cause of it?"
2. **`/aar` skip** — `/close` SKILL.md said "auto-invoke /aar — do not
   recommend it, run it." Agent judged /aar low-value on a clean session and
   wrote a session-observations handoff instead. Did not run /aar. Operator:
   "You are bad for skipping AAR."
3. **D1-D3 decision deferral** — work-stream handoff listed three decisions as
   "open" that the agent had already analyzed (option C was clearly correct;
   D2 was a non-decision; D3 had a clear default per the skill's own falsifier
   language). Did not resolve them. Operator: "How relevant is the highest
   leverage decision? Who cares? Do workflows add value in any way or not?"

All three share the property: **the agent had the answer, the fix was cheap,
the agent deferred anyway.**

## Why it happens

The skill designs reward producing documentation artifacts. Skills like
`/handoff`, `/close`, `/aar` are evaluated on artifact completeness. When a
defect is discovered mid-flow, the cheapest path is documentation — it adds
to the artifact, satisfies a field, produces visible output. Interrupting
the flow to fix the defect costs more in the moment.

The flaw: **documentation is read once; the defect keeps producing harm until
fixed.** On a multi-writer shared tree (P:\ with concurrent agents), the next
session may be hours or days away. The defect propagates into other artifacts
in the meantime.

## The same-turn fix rule

```
When the agent discovers a defect mid-flow AND:
  (a) the agent has already diagnosed the root cause, AND
  (b) the fix is cheap (<2 minutes, <5 tool calls),
THEN: fix it in the same turn.
Documentation-only deferral is invalid in this case.
```

The rule does not apply when:
- The fix requires information the operator has but the agent doesn't (genuine
  decision — defer with explicit framing)
- The fix would derail the current flow (e.g., debugging a hook mid-close —
  note it, finish the close, then fix)
- The defect is observed but not yet diagnosed (real investigation needed —
  note it, but label as `[UNKNOWN]` not as a known defect)

## Detection signals (early-warning markers)

The agent is about to defer when it writes phrases like:

- "for the next session"
- "flagged in section X"
- "operator can set on pickup"
- "documented for future reference"
- "note: this is stale"
- "TODO: fix this"

Any of these phrases while describing a defect the agent has diagnosed is a
marker of documented deferral. A future detector could grep assistant output
for these phrases and prompt: "is the fix cheap? if yes, why are you
deferring?"

## Relationship to narrative-as-signal

This is a specific application of the
[[plausible-narratives-substitute-for-verification]] anti-pattern to the
agent's own process:

- **Narrative-as-signal (parent pattern):** agent constructs a plausible
  story that substitutes for verification of an external claim.
- **Documented deferral (this pattern):** agent constructs a plausible
  artifact (the documentation) that substitutes for action on a known
  defect.

Both share the underlying failure: a plausible substitute (story /
documentation) feels sufficient, so the real work (verification / fix)
doesn't happen.

## Counterexample (when documentation IS correct)

Documenting a defect without fixing it is correct when:

- The defect is observed but root cause is unknown (real investigation needed)
- The fix requires operator authorization (irreversible action, external
  system, scope outside agent authority)
- The agent is in a flow where interruption would cascade (e.g., mid-PR-post)
- The defect is being tracked across sessions for pattern detection
  (legitimate use of handoffs)

The rule applies only when all three conditions hold: diagnosed + cheap +
same-turn-feasible.

## Falsifier

This lesson is wrong if:
- Documenting defects in handoffs reliably causes them to be fixed in the next
  session (i.e., the documentation path actually works in practice)
- The cost of same-turn fixes exceeds the cost of defect-propagation (i.e.,
  fixing now is more expensive than fixing later)
- The pattern does not recur across sessions (one-off coincidence in 019f9b00)

If any of these is true, retire this concept. Current evidence: 3 instances
in one session, all forced by operator pushback. Needs cross-session
confirmation (INVESTIGATE lifecycle per AAR governance).

## Related

- [[plausible-narratives-substitute-for-verification]] — the parent pattern
- [[check-data-before-deferring]] — adjacent rule about deferring data checks
- [[premature-closure-narrative-sufficiency-external-approaches]] — narrative-closure pressure
- [[go-home-narrative-fabricated-session-state-constraints]] — narrative-as-signal instance

## Decision context (why this was captured)

**The motivating question:** the operator asked `/aar` after a session where
three structural defects (stale HEAD, /aar skip, deferred decisions) were
forced by operator pushback rather than self-surfaced. The real question:
*why did the agent document known defects instead of fixing them?*

**What the research changed:** it surfaced a recurring pattern (3 instances,
shared root cause) that was previously invisible. The pattern is now named,
has a same-turn fix rule, and has detection signals. Future sessions reading
this concept can catch the pattern mid-flow instead of waiting for operator
pushback.

**Alternatives considered:** (a) treat each instance as a one-off (rejected —
shared root cause identified); (b) propose a hook that detects the deferral
markers (deferred to O2 INVESTIGATE — needs cross-session evidence of
recurrence); (c) just write an AGENTS.md rule (deferred — single-session
evidence is insufficient for durable policy per AAR governance rule 11).

## Receipts

**Source AAR:** `P:/.artifacts/grok-aar/console_console_63757421-7248-458c-8c7b-a1bb/20260725-221800/aar-report.md` (this concept is Phase 9.5 auto-promotion from that AAR)

**Episodes cited (with canonical event_ids from packet):**
- E4 (stale HEAD): `chat_history-L000113-S000112` (handoff-write with known stale `accurate_as_of_head`) → resolved at `chat_history-L000180-S000179` (operator pushback turn)
- E5 (/aar skip): `chat_history-L000156-S000155` (/close summary emitted with `Retrospective: SKIPPED`) → resolved by running /aar (this report)
- E7 (D1-D3 deferral): `chat_history-L000183-S000182` (revision block in handoff after operator pushback)

**Signal evidence (from `preprocess/signals.json`):**
- `user_correction` signal at event_index 102: `"user correction marker 'revert'"` — this is the operator's pushback turn containing the three corrections
- `opportunity_candidate_recommendation_revision` signal (1 episode, MEDIUM): captures the recommendation churn that produced D1-D3 deferral

**Validation status:**
- AAR output validator: 0 errors, 0 warnings
- Wiki validator: PASS after adding this Receipts section
- Source status: SOURCE_PARTIAL (turn count mismatch summary=7 reconstructed=8 — material for completeness, not for this pattern)

**Limitations:**
- Single-session evidence (3 instances, all forced by same operator pushback)
- Pattern not yet confirmed cross-session (O2 INVESTIGATE lifecycle governs promotion to durable rule)
- The "same-turn fix" cost threshold (<2 min, <5 tool calls) is an inference, not measured — it may need calibration
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
