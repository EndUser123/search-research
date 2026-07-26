---
thread_id: missed-decisions-wiki-capture-investigation-20260725
parent_handoff_path: none
current_session_id: 019f9a89-d902-7930-ad3a-bab7e682830b
current_terminal_id: console
produced_at: 2026-07-26T00:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: unknown
---

# Handoff: investigate why decisions keep missing wiki capture

## Objective

Investigate the recurring pattern where substantive architectural decisions made during sessions are NOT captured as wiki concepts until after-the-fact auditing catches them. The 2026-07-25 session missed 2 of its 7 wiki-worthy decisions (Nemotron `/tp` demote + wiki-captures-decisions-default) until the operator explicitly asked "did we capture all decisions?" The §4b decisions gate exists (shipped same session) but the model does not consistently apply it during the session — only when prompted.

## Why this matters

Decisions without wiki capture evaporate into transcripts. Future sessions re-litigate them without the original rationale, steelman, or falsifier. The §4b gate was built specifically to prevent this, but the gate only fires at write-time — if the model never decides to write, the gate never runs.

The pattern: model makes a decision → ships the code change → moves to the next task → never circles back to capture the decision as a wiki concept. The decision is in the commit message (maybe) but not queryable via `/wiki`.

## Evidence for the gap

- **2026-07-25 session:** 7 wiki-worthy decisions made; 5 captured (3 via the /why synthesis, 1 Nemotron canonical, 1 lexical-vs-semantic finding); 2 missed until operator prompted (Nemotron demote, wiki-decisions-default). Miss rate: 2/7 = 29% even in a session that was explicitly about wiki capture.
- **Prior sessions (inferred):** the wiki has ~35 concepts total; many decisions are documented only in commit messages or handoffs, not as wiki concepts. A systematic audit would likely find more missed decisions.

## Scope

**In scope:**
- Investigate WHY the model doesn't capture decisions in real-time during sessions
- Propose structural fixes (hook? skill step? /close gate enhancement? AGENTS.md rule?)
- Estimate the scope of missed decisions across prior sessions (sample audit)

**Out of scope:**
- Implementing the fix (separate implementation handoff after investigation)
- Backfilling all missed decisions (separate bulk-capture workstream)

## Acceptance criteria

1. Root cause analysis of why decisions are missed (behavioral? structural? both?)
2. At least 2 viable structural fixes proposed, with selection criterion and steelman for each
3. A sample audit of N prior sessions showing the miss rate (quantified, not estimated)
4. Recommendation: which fix to ship first, or "no fix needed — the §4b gate is sufficient once habituated"

## Read-first list

1. `P:/.data/wiki/SCHEMA.md` §4b (the decisions gate that should fire but doesn't consistently)
2. `P:/.data/wiki/concepts/wiki-captures-decisions-by-default.md` (the decision to add §4b)
3. `P:/.data/wiki/concepts/verify-against-existing-state-before-defensive-mechanisms.md` (related: model skips named steps under generative load)
4. `C:/Users/brsth/.grok/skills/close/SKILL.md` "Decisions" gate (the existing close-time capture mechanism — does it work? why does it miss?)
5. `P:/docs/handoffs/session-observations-20260725/HANDOFF.md` O1-O8 (this session's observations, several relevant)

## Hypotheses to investigate

- **H1 — the close-time decisions gate fires too late.** By the time `/close` runs, the model has context-fatigue and the decision's rationale is buried in transcript. The gate asks "what decisions were made?" but the model can't reliably reconstruct them from memory.
- **H2 — there's no real-time trigger.** Decisions are made mid-flow; nothing prompts "capture this as a wiki concept now." The model would have to interrupt its own flow to write the concept, which it doesn't do under generative load.
- **H3 — the §4b gate's criteria are unclear at decision-time.** The model doesn't always recognize a decision AS a decision when it's making it. "Should this be a wiki concept?" is a meta-question the model doesn't ask itself.
- **H4 — the decisions gate in `/close` works but is scoped to "substantive" decisions, which is subjective.** The model applies too-strict a filter and misses medium-weight decisions.

## Constraints

- Do NOT implement the fix in this handoff. Investigation + recommendation only.
- Do NOT backfill missed decisions in this handoff. Sample audit only.
- Respect the §4b gate: any fix proposed must itself pass §4b (architectural + criterion + rationale + steelman + falsifier).

## Dependencies

- **Requires:** nothing — can start immediately
- **Blocks:** nothing
- **Non-blocking to:** future skill improvements

## Status

OPEN — ready for investigation in a fresh session

## Next steps

1. Read the read-first list
2. Sample-audit 3-5 prior sessions for missed decisions (quantify miss rate)
3. Test the hypotheses against the evidence
4. Propose structural fixes
5. Hand off the chosen fix for implementation

## Last user message (verbatim)

"Create a handoff to investigate why we keep missing decisions capture in the wiki."
