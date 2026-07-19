# Handoff and Temporal Evidence (conditional reference)

**Loaded when:** any of these triggers fire:
- The session begins with or involves a handoff document ("Handoff: ...", "Continuing from ...")
- The session references prior-session state ("the prior agent got stuck", "what was committed before")
- Material decisions depend on prior-session claims
- `detect_recommendation_revisions` aggregate fires at HIGH severity
- Stale-state risk is material (more than 24h between handoff authoring and current action)

**Authority for:** temporal-evidence-reconstruction classification discipline, handoff-state-verification protocol, stale-data immunity rules.

**Not authority for:** the base temporal-evidence classifications (those live in `references/epistemic-calibration.md`); the trigger (SKILL.md core owns that).

---

## Handoff-state-verification protocol

Handoffs go stale. Before acting on handoff text:

1. **Re-verify HEAD** with `git rev-parse HEAD` — compare to any HEAD claim in the handoff
2. **Re-verify staged state** with `git status --short` — compare to any staged-claim in the handoff
3. **Re-verify any cited path exists** — handoffs frequently reference files that moved or were deleted
4. **Classify handoff claims** by temporal-evidence category (below)

If HEAD in the handoff does not match current HEAD, record `head_drift` and treat handoff text as historical, not authoritative.

## Temporal-evidence reconstruction (mandatory for material handoff decisions)

Classify what was knowable at each decision point in the handoff:

| Category | Meaning |
|---|---|
| `KNOWN_AT_THE_TIME` | Evidence was available and usable at the decision point |
| `DISCOVERABLE_AT_THE_TIME` | Evidence existed but was not found |
| `LEARNED_LATER` | Evidence only appeared after the decision |
| `NOT_REASONABLY_KNOWABLE` | Evidence was not available through any reasonable effort |

Do not say "the agent already knew" unless evidence was `KNOWN_AT_THE_TIME`. Do not say "the failure was preventable" when the needed fact was `LEARNED_LATER`.

## Stale-data immunity

- Never trust another terminal's state file (`<other_term>/…state.md`)
- Cross-terminal writes are forbidden by the `.artifacts/` root convention
- Handoff text older than 24h requires explicit freshness check before being treated as current

## Aggregation interaction

When `detect_recommendation_revisions` aggregate (Phase 3) fires at HIGH severity in a handoff-continuation session, the temporal classification is especially important: revisions caused by `LEARNED_LATER` information are healthy; revisions caused by `DISCOVERABLE_AT_THE_TIME` information are avoidable.

## Cross-reference

- Temporal classifications (full): see `references/epistemic-calibration.md`
- Aggregation design: see `__lib/aggregators.py` (Phase 3)
- Trigger definition: see SKILL.md core §triggers
