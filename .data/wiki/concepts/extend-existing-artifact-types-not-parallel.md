---
title: "Extend existing artifact types instead of creating parallel ones"
created: 2026-08-03
updated: 2026-08-03
source: session 019fc0a7
tags: [design-principle, artifact-types, handoff-extension, anti-pattern, schema]
host: grok
agent: grok
verification: red-team-verified-2026-08-02
cognitive_load: 2
summary: >
  When adding structured state for a new feature, extend the existing
  authoritative artifact type (handoff, wiki concept, skill) rather than
  creating a parallel directory/file format. Parallel artifact types
  duplicate schema, create competing authorities, and contradict the
  workspace's own constraints.
---

## Decision context

Session 019fc0a7: the agent created `P:/docs/investigations/` with a new investigation-state artifact type for `/why --persist`. The red-team review (5 specialists, 29 findings) proved from three independent angles that this was wrong:

1. **AUTH-1 (BLOCK):** The proposal's own "don't do" list said "no new InvestigationState artifact type" — but Step 16.5 created exactly that. The discriminator the proposal relied on (markdown vs not-markdown) was not the discriminator this workspace uses (does it have frontmatter, lifecycle, identity, and cross-skill consumers?).

2. **AUTH-5 (REVISE):** The investigation file was structurally a handoff with extra fields. The mutual-exclusivity rule between Step 14 (handoff) and Step 16.5 (persistence) masked the schema duplication.

3. **PERF-006 (medium):** The mutual-exclusivity gate suppressed the highest-value persistence target — unresolved investigations, which contain hypotheses and discriminating tests most valuable to future sessions.

The fix: collapse Step 16.5 into the handoff schema. Add an optional `investigation_state:` block to handoff frontmatter. No new directory, no new artifact type, no mutual-exclusivity problem.

## The pattern

**Anti-pattern:** creating a new directory + file format + lifecycle for a feature that is structurally a specialization of an existing artifact type.

**Correct pattern:** extend the existing artifact type with an optional block:
- Handoff gains `investigation_state:` frontmatter block (question, root_cause, confidence_tier, hypotheses, cited_source_files, pattern_match)
- Handoff body gains optional sections (## Hypotheses, ## Evidence, ## Falsifier, ## Test outcomes)
- Existing consumers (close scanner, harvest, list_handoffs.py) work unchanged — the block is optional and additive
- Lifecycle uses the handoff's existing status field (open/closed/superseded)

**Test before creating a new artifact type:**
1. Does it have frontmatter? → If yes, it's an artifact type, not just a file.
2. Does it have a lifecycle (created → updated → closed)? → If yes, check if an existing artifact type already has this lifecycle.
3. Do other skills consume it? → If yes, check if those skills already query an existing artifact type.
4. Does it duplicate fields from an existing artifact? → If yes, extend instead of creating parallel.

## Falsifier

This pattern is wrong when:
- The existing artifact type genuinely cannot accommodate the new fields without breaking other consumers (then a separate type with an ADR is justified)
- The new artifact has a fundamentally different lifecycle (e.g., immutable audit trail vs mutable work document)
- The consumer query patterns are incompatible (e.g., temporal range queries vs keyword search)

## What this means for our workspace

When a future session proposes creating a new directory or file format for structured state, it should first check whether an existing artifact type (handoff, wiki concept, skill) can be extended with an optional block. The `investigation_state:` block in handoff frontmatter is the worked example — it added structured investigation fields without creating a parallel persistence layer.

The test is simple: if the new artifact has frontmatter, lifecycle, identity binding, and cross-skill consumers, check whether an existing artifact type already provides those. If yes, extend; don't create parallel.

Related patterns: [[mechanical-enforcement-over-behavioral-reminder]] (structural fixes over behavioral rules), [[no-question-theater]] (acting on derived defaults), [[trust-over-believability]] (the proposal believed its own "don't do" list while violating it).

## Receipts

- `~/.grok/skills/handoff/references/core-fields.md` lines 172-217 — the `investigation_state:` optional frontmatter block
- `~/.grok/skills/why/SKILL.md` line 484-489 — Step 14 `--persist` routing to handoff
- Red-team findings AUTH-1, AUTH-5, PERF-006, CORR-4 (session 019fc0a7, `P:/.artifacts/review/019fc0a7/20260802/FINDINGS.md`)
- Commit `653db5b` (Phase 1: collapse investigation persistence into handoff schema)
- Reverted: `P:/docs/investigations/` directory (removed, commit `a309fa5`)
