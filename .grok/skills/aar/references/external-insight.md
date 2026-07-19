# External Insight Expansion (conditional reference)

**Loaded when:** any of these triggers fire (all explicit — this reference is NOT loaded by default):
- The user explicitly asks for broader research ("search the internet", "does anyone actually use this", "look up", "research")
- The session reveals a potentially reusable or general failure class
- A root-cause hypothesis would benefit from external evidence
- Current platform or tool capabilities may have changed
- The proposed improvement may already exist elsewhere
- Local evidence supports several competing explanations
- Cross-domain analogies may reveal useful mechanisms
- A full continual-improvement AAR has already been triggered (per §promotion-triggers in core)

**Authority for:** external-research discipline, insight schema, source-type classification, research-output-vs-action separation.

**Not authority for:** the trigger (SKILL.md core owns the 1-line trigger definition); the decision to act on insights (Phase 7 disposition in `references/opportunity-discovery.md` owns that).

---

## Purpose

Use authoritative research, current documentation, comparable systems, and relevant open-source implementations to discover failure patterns, opportunities, and improvement mechanisms that are not recoverable from the transcript alone.

This is NOT mandatory for every AAR. The reference is intentionally loaded only when one of the explicit triggers fires.

Do not activate merely because the session is long or imperfect.

## Research discipline

For each externally derived insight, record:

```text
external_insight_id
claim
source_type
source
relevance_to_session
supporting_session_evidence
what_new_value_it_adds
confidence
limitations
existing_capability_relation
recommended_disposition
```

Distinguish: `DIRECTLY_APPLICABLE` · `USEFUL_ANALOGY` · `POSSIBLE_TRANSFER` · `CONTRADICTS_CURRENT_APPROACH` · `ALREADY_IMPLEMENTED` · `NOT_RELEVANT` · `INSUFFICIENT_EVIDENCE`

Do not import ideas merely because they are novel or popular. Do not import speculative internet ideas as `ACT_NOW` opportunities.

## Fail-open

If research tools are unavailable or inconclusive: report the limitation, continue the local AAR, do not block, do not fabricate external support.

Status values: `NOT_TRIGGERED` · `COMPLETED` · `PARTIAL` · `UNAVAILABLE` · `NO_MATERIAL_DELTA`

## Separation of concerns

Keep two research purposes distinct:

- **Task-domain research** — research needed to evaluate the subject of the session (e.g. current Grok capabilities, retailer stock, API behavior).
- **AAR-improvement research** — research used to discover better ways to analyze the session or improve the agent system (e.g. failure taxonomies, human factors, evaluation design).

Label them separately so task facts are not confused with meta-improvement ideas.

## Research output remains proposal-only

External research may produce opportunity candidates, rejected ideas, experiment proposals, or wiki candidates. It must NOT automatically:
- alter AGENTS.md, alter CLAUDE.md, write to durable memory, modify /wiki
- promote a new rule, change routing, or create new infrastructure

Promotion remains an explicit downstream disposition.

## Cross-reference

- Trigger definition: see SKILL.md core §triggers
- Opportunity schema (where external insights land): see `references/opportunity-discovery.md`
- Calibration of external claims: see `references/epistemic-calibration.md` (especially `scope_confidence` — external claims rarely achieve `VERY_HIGH`)
