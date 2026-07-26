---
thread_id: why-skill-adoption-gap-20260725
parent_handoff_path: P:\docs\handoffs\why-skill-enhancement-20260725\HANDOFF.md
current_session_id: 019f9a89-d902-7930-ad3a-bab7e682830b
current_terminal_id: console
produced_at: 2026-07-26T00:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: unknown
---

# Handoff: /why skill adoption gap — when to invoke, consider a suggestion hook

## Objective

The `/why` skill was refactored v1→v2→v3 across session 019f9a89 (2026-07-25). The v3 A/B test validated it: v3 produces 11 causes vs v1's 5; meets 5/5 acceptance criteria vs v1's 2.5/5; inline conditional trigger fires correctly; pattern-library query works. **The skill-quality gap is closed.**

But the original handoff's motivation (`P:/docs/handoffs/why-skill-enhancement-20260725/HANDOFF.md`) was partly about quality and partly about adoption: the original `/why` was underused. Operators caught diagnostic errors and patched reactively without invoking `/why`. The skill exists but isn't invoked at the moments it would help most.

**This handoff investigates the adoption gap and proposes structural fixes.**

## Why this matters

A skill that works but isn't invoked has zero impact. The v3 refactor improved quality by ~120% (causes found) but if invocation rate stays the same, the workspace-wide improvement is zero. The adoption gap is the binding constraint.

The session that built v3 used v3 exactly once (on its own errors, at the end). That's 1 invocation in a session that produced 8 commits. If the skill-builders don't invoke it mid-session, operators won't either.

## Evidence for the gap

- **The originating failure (2026-07-25 receipt-system incident):** the agent concluded "hooks not registered" from incomplete evidence. `/why` (or any root-cause skill) was not invoked. The agent patched reactively.
- **The session-019f96f5 failure pattern:** the agent repeatedly produced incomplete work, claimed complete, patched when caught. `/why` was not invoked on any of the recurring instances. The handoff had to be written after the fact.
- **This session (019f9a89):** `/why` was invoked once, at the operator's explicit request, at the end. The model did not proactively suggest `/why` when it made its own over-engineering errors mid-session.
- **Wiki corpus signal:** `/why` is referenced in 3 wiki concepts; the skill has been invoked fewer than 10 times total based on critique-log and handoff evidence. `/tp` and `/aar` are invoked far more frequently.

## Scope

**In scope:**
- Investigate WHY `/why` is not invoked at the moments it would help (after a caught diagnostic error, after a reactive patch cycle, when the operator asks "what went wrong")
- Propose structural fixes: (a) a suggestion hook (UserPromptSubmit or Stop) that detects diagnostic-error patterns and recommends `/why`; (b) integration with `/aar` (which already runs at session close); (c) AGENTS.md rule; (d) something else
- Evaluate whether the adoption gap is real or whether `/aar` + `/debrief` already cover the same ground

**Out of scope:**
- Further `/why` skill improvements (quality gap is closed; this is about adoption)
- Implementing the fix (separate implementation handoff)

## Acceptance criteria

1. Root cause analysis: why is `/why` not invoked when it would help? (behavioral? discoverability? skill-confusion with `/aar`?)
2. Decision: is `/why` redundant with `/aar`? If yes, recommend merging or scoping each clearly. If no, explain the distinction operators should use.
3. At least 2 viable structural fixes for the adoption gap, with selection criterion
4. Recommendation: which fix to ship first (or "no fix — the skill is correctly invoked only by operator choice")

## Read-first list

1. `C:/Users/brsth/.grok/skills/why/SKILL.md` (v3 — the skill whose adoption is in question)
2. `C:/Users/brsth/.grok/skills/aar/SKILL.md` (the sibling skill that may overlap)
3. `P:/docs/handoffs/why-skill-enhancement-20260725/HANDOFF.md` (the originating motivation — note the adoption concern)
4. `P:/.data/wiki/concepts/reactive-pattern-matching-and-closure-pressure.md` (the behavioral pattern that adoption fixes would mitigate)
5. `C:/Users/brsth/.grok/skills/close/SKILL.md` (the `/close` flow that already auto-invokes `/aar` — could it auto-suggest `/why` mid-session?)
6. `~/.grok/active-surface.last.md` (what hooks are available for a suggestion trigger?)

## Hypotheses to investigate

- **H1 — `/why` and `/aar` are confused.** Operators don't know which to invoke when. `/aar` reviews a whole session; `/why` drills into one failure. If operators don't distinguish them, they pick `/aar` (more familiar) and `/why` goes unused.
- **H2 — there's no trigger at the moment of need.** The moment `/why` would help is right after a caught diagnostic error or a reactive patch cycle. Nothing in the system surfaces `/why` at that moment. The operator has to remember it exists.
- **H3 — `/why` is too heavy for mid-session use.** The full protocol (16 steps) takes 5-10 minutes. Operators won't interrupt flow for that. A `/why --quick` mode exists but may not be discoverable.
- **H4 — the skill is correctly invoked only by operator choice.** Auto-suggesting `/why` would be intrusive; the operator should decide when root-cause analysis is worth the time. The adoption gap is a feature, not a bug.

## Constraints

- Do NOT implement the fix in this handoff. Investigation + recommendation only.
- Do NOT merge `/why` into `/aar` without explicit operator decision. Propose, don't execute.
- Any proposed hook must respect the AGENTS.md rules on hook development (Windows path conventions, exit code semantics, etc.)

## Dependencies

- **Requires:** nothing — can start immediately
- **Blocks:** nothing
- **Non-blocking to:** other skill improvements

## Related

- Parent handoff: `P:/docs/handoffs/why-skill-enhancement-20260725/HANDOFF.md` (the quality-improvement workstream; this is the adoption-workstream companion)
- `P:/.data/wiki/concepts/verify-against-existing-state-before-defensive-mechanisms.md` (related principle: check whether existing skills/gates cover the need before proposing new ones)

## Status

OPEN — ready for investigation in a fresh session

## Next steps

1. Read the read-first list
2. Test the hypotheses (H1-H4) against evidence
3. Decide: is the adoption gap real, or is `/why` correctly scoped as operator-invoked?
4. If real, propose structural fixes
5. Hand off the chosen fix for implementation

## Last user message (verbatim)

(implied from the session-close coverage question: "Did the why command close the gap about not having used the why command?")
