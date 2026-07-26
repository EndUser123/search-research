---
thread_id: 019f9f4f-enhancement-offsetting-retirement-rule-20260726
parent_handoff_path: P:/docs/handoffs/session-019f9f4f-shipped-work-20260726/HANDOFF.md
current_session_id: 019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9
current_terminal_id: grok-build-terminal
produced_at: 2026-07-26T19:40:00Z
status: open
handoff_type: investigation
accurate_as_of_head: ea0a48be110dee12dd78317a611c1f6231c4d0f5
---

# Handoff: Fleet-wide "enhancement-offsetting-retirement" rule (OA-03)

## Objective

Decide whether to add an AGENTS.md rule requiring every skill enhancement batch to retire a section of comparable size (or explicitly justify why the addition is structural rather than ceremonial) — the structural fix for second-system effect at the skill-fleet level.

## Status

OPEN — BLOCKED on evidence. Requires OA-02 (/design bloat assessment) and a broader audit (≥3 skills) before the rule can be justified or rejected.

## Producing context

- Identifying session: `019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9`
- Originated as "Open Question 3" in the /www self-assessment concept
- Surfaced as LATER #7 in the session's second /tp

## Read-first list

1. `P:/.data/wiki/concepts/research-vs-design-vs-architect-skills-and-www-self-assessment.md` — proposes the rule; documents the /www pattern (3 enhancement batches, 0 retirements, +2000 words net)
2. `P:/docs/handoffs/design-bloat-assessment-20260726/HANDOFF.md` — sibling handoff; produces the /design data point
3. `~/.grok/AGENTS.md` § "Hard rules" and § "Optimal long-term solution (not minimal fix)" — where the rule would live if adopted
4. `~/.grok/skills/www/SKILL.md` § "Provenance" — documents the enhancement-batch pattern at the source (3 batches, all added, none retired)

## Verified facts

- [FACT] /www grew from ~150 lines (v1, 2026-07-21) to 585 lines (pre-pare, 2026-07-26) via 3 enhancement batches — net growth, zero retirements (receipt: provenance section in `~/.grok/skills/www/SKILL.md` as of commit `51d269c`'s parent)
- [FACT] /www was pared to 450 lines this session via deliberate cuts (receipt: commit `51d269c`)
- [FACT] Brooks' second-system effect is the named pattern for this growth shape (receipt: wiki concept cites Wikipedia + original 1975 source)
- [FACT] Anthropic's "smallest set of high-signal tokens" rule directly contradicts unconstrained skill growth (receipt: cited in wiki concept from Anthropic context-engineering blog)
- [FACT] "Avoid feature creep" is a published agent skill (agentskills.me) — the anti-pattern is canonical enough that someone built a reusable artifact for it (receipt: cited in wiki concept)

## Current state

**Evidence available:** 1 skill (/www) shows the pattern clearly — enhancement batches added without offsetting retirements, requiring a deliberate pare after the fact.

**Evidence missing:**
- /design (1015 lines) — being assessed in sibling handoff
- /aar — grew this session (Phase 4 signals + Phase 8.5 profile-age + wait-all gate); no introspection done
- /tp — recently rewritten with 4D matrix; unclear if the rewrite grew or just restructured
- /dream — added Pass 4 this session; small growth
- /close — multiple recent edits from other sessions (visible in git log); not assessed
- /red-team, /why — received wait-all-gate additions this session; small growth

The rule can't be justified or rejected until at least 3 skills are audited.

## Task packets

### EOR-01: Audit enhancement-batch-vs-retirement pattern across ≥3 skills (BLOCKED on OA-02)

- **goal:** produce evidence that the enhancement-without-retirement pattern recurs across enough skills to justify a fleet-wide rule (or evidence that it doesn't, in which case the rule is rejected)
- **in scope:** audit enhancement batches vs retirements in the provenance sections of: /www (done), /design (sibling handoff), /aar, /tp, /dream, /close, /red-team, /why. For each: count enhancement batches, count retirements, net growth direction
- **out of scope:** proposing the rule (EOR-02, after data is in)
- **files / anchors:** provenance sections of each SKILL.md; git log for skills without provenance sections
- **acceptance:** audit table in a wiki concept showing per-skill (enhancement-batch count, retirement count, net growth); concept passes `validate_wiki_entry.py`
- **falsifier:** pattern appears in only 1-2 skills (rule is overkill); OR skills that grew also naturally retired sections at the same rate (rule is redundant with existing practice)
- **verification level required:** STATIC_INSPECTION
- **estimate:** ~30 min (audit 4-6 skills beyond /www and /design)

### EOR-02: Rule proposal (CONDITIONAL on EOR-01 supporting adoption)

- **goal:** one-paragraph AGENTS.md rule draft + go/no-go decision
- **status:** BLOCKED on EOR-01
- **in scope:** if EOR-01 supports adoption (≥3 skills show pattern, retirements are consistently <enhancements): draft rule, propose adoption path, identify whether rule goes in AGENTS.md "Hard rules" or "Optimal long-term solution" section
- **out of scope:** implementing the rule (separate session; needs operator approval)
- **acceptance:** rule draft is one paragraph, actionable, has a falsifier (what would show the rule isn't working)
- **falsifier:** EOR-01 supports adoption but no rule formulation survives review (the pattern is real but a rule can't capture it without being too rigid)

## Open decisions

### Decision 1: Threshold for "pattern recurs"

- **question:** how many skills need to show the enhancement-without-retirement pattern before the rule is justified?
- **options:**
  - (A) ≥3 skills show the pattern (the standard "rule of three" for pattern validity)
  - (B) ≥50% of skills audited show the pattern (proportion-based)
  - (C) Any skill that grew >2× via enhancements without retirements (severity-based)
- **selection criterion:** signal-to-noise — high enough that the rule isn't reacting to noise; low enough that real patterns aren't missed
- **currently leads:** (A) — the rule of three is the standard threshold in software engineering pattern literature
- **what would change this:** if /aar, /tp, /close all show the pattern strongly, (B) becomes the better threshold; if only /www and /design show it, the rule is overfit

### Decision 2: Rule placement (conditional on adoption)

- **question:** where does the rule live if adopted?
- **options:**
  - (A) `~/.grok/AGENTS.md` § "Hard rules" — fires every time a skill is edited
  - (B) `~/.grok/AGENTS.md` § "Optimal long-term solution" — advisory; applies at skill-authoring time
  - (C) Skill-authoring reference doc (loaded only when authoring skills via `/create-skill` or `/writing-skills`)
- **selection criterion:** enforcement vs authoring-time guidance
- **currently leads:** (B) — the rule is about authoring discipline, not runtime enforcement; hard-rule placement would create hook-shaped ceremony
- **what would change this:** if skills continue growing unbounded despite the advisory rule, upgrade to (A) or structural (a hook that warns on skill-file growth beyond a threshold)

## Hard constraints

1. **Anti-"smallest viable" rule applies.** Don't propose the rule just to have a rule. The audit (EOR-01) is the gate; if the pattern doesn't recur, the rule is rejected and the audit's wiki concept documents why.
2. **No structural rule without evidence.** Per the AGENTS.md "Hook enforces, document provides context" pattern — the rule starts as documentation; only escalates to enforcement if documentation doesn't work.
3. **Don't conflate skill growth with skill bloat.** Growth from adding structural capabilities (e.g., /dream adding Pass 4) is different from growth from ceremonial enhancement batches (e.g., /www's Round 2.5 ingestion triggers). The audit must distinguish.

## Cross-reference couplings

- `P:/docs/handoffs/design-bloat-assessment-20260726/HANDOFF.md` → produces the /design data point; if /design doesn't show the pattern, the rule's evidence base weakens
- `P:/.data/wiki/concepts/research-vs-design-vs-architect-skills-and-www-self-assessment` → proposes the rule; this handoff is the validation step
- `~/.grok/AGENTS.md` § "Hard rules" / § "Optimal long-term solution" → destination if the rule is adopted

## Other outstanding streams (not handed off)

- **OA-02 (/design bloat assessment)** — sibling handoff. Produces one of the data points this handoff needs.

## Explicit non-goals

1. **Do not propose the rule before EOR-01 completes.** The rule is hypothesis, not conclusion.
2. **Do not implement the rule (write to AGENTS.md) without operator approval.** Even if EOR-02 produces a rule draft, adoption is the operator's call.
3. **Do not audit hook scripts.** This is about skill files (SKILL.md), not runtime infrastructure.
4. **Do not re-do the /www assessment.** Already done; provides the reference data point.

## Resumption protocol

1. **CHECK BLOCKER FIRST:** is `P:/.data/wiki/concepts/design-skill-bloat-assessment-*.md` present? If not, EOR-01 is blocked on the sibling handoff. Either pick up the sibling first, or proceed with the audit of the other 4-6 skills (/aar, /tp, /dream, /close, /red-team, /why) and add /design when its assessment lands.
2. Read this handoff + the /www self-assessment concept.
3. Execute EOR-01 (audit) — for each skill, count enhancement batches vs retirements in the provenance section. If no provenance section, use `git log --oneline -- <skill-path>` and classify commits as enhancements vs retirements vs other.
4. Resolve Decision 1 (threshold) before deciding go/no-go.
5. If go: execute EOR-02 (rule draft). If no-go: write the wiki concept documenting why the rule was rejected.

## Suggested next invocation

```
Continue work from session 019f9f4f. Read P:/docs/handoffs/enhancement-offsetting-retirement-rule-20260726/HANDOFF.md.

Check blocker: is the /design bloat assessment concept present at
P:/.data/wiki/concepts/design-skill-bloat-assessment-*.md?

Either way, execute EOR-01 (audit enhancement-batch-vs-retirement pattern
across /aar, /tp, /dream, /close, /red-team, /why). For each: count
enhancement batches vs retirements in the provenance section; classify
growth direction. Produce an audit-table wiki concept. Resolve Decision 1
(threshold for "pattern recurs") before deciding go/no-go on the rule.
```

## Last user message (verbatim)

> "do the recommended action   make sure the deferred items have hand-off files."

## Epistemic labels

- All "Verified facts" are `[FACT]` with receipts cited inline.
- "Pattern recurs" claims about /aar, /tp, /close, etc. are `[UNKNOWN]` — these skills have not been audited; the rule's evidence base is currently 1 skill (/www) plus 1 pending (/design).
- Decision 1 "currently leads (A)" is `[INFERENCE]` based on software-engineering pattern-literature convention; not workspace-measured.
- Decision 2 "currently leads (B)" is `[INFERENCE]` based on the AGENTS.md "Hook enforces, document provides context" pattern; not operator-confirmed.
- Estimates are `[INFERENCE]` based on task shape; no measurement.
