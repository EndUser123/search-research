# Handoff: /skill-dev orchestrator plan v2 (routing + audit mode)

**Status:** OPEN — plan revised (v2), reviewed by /tp (2/3 lenses, REVISE with 3 clarifications), ready for implementation  
**Created:** 2026-08-01  
**Source session:** 019fb177-e5d5-7520-92f5-0158f87639c9

## Objective

Transform /skill-dev from a 3-mode skill (measure, improve, audit-active) into a single-entry-point orchestrator for all skill lifecycle questions. Add routing layer + audit mode (8-category rubric) + delegation wiring to existing skills.

## What was done this session

1. v1 plan written (7 phases, 5 new modes absorbing from 5 Claude-side skills)
2. v1 reviewed by /tp parallel panel (spawn + codex) → REVISE: 3 modes duplicate existing skills, 2 modes invented, skillopt doesn't exist, 7 phases over-scoped
3. v2 plan written (2 phases: routing table + audit mode + delegation wiring)
4. v2 reviewed by /tp parallel panel (spawn + codex) → REVISE (light): 3 clarifications needed before PROCEED
5. v1.3 already shipped: cross-invocation complementary skill recommendations (Step 4.5, Step 7.5)

## The 3 clarifications (from /tp v2 review)

1. **Routing table replaces `argument-hint:` or coexists?** Answer: replaces it.
2. **Audit-mode is single-skill-deep or batch?** Answer: single-skill-deep (different from /skill-prune's batch hygiene).
3. **For each of 8 audit categories, name what /skill-dev produces that /skill-prune + /tp + /fmea + /review don't.** Categories that fail this test get cut or delegated. 5 of 8 overlap with existing skills — consider composable checklist (delegate structural checks to /skill-prune, design checks to /tp, I/O checks to /fmea) rather than reimplementing.

## Open work

### Phase 1: Routing table (30 min)
Add intent-based routing table to SKILL.md after Product Rule section. Update description/solves frontmatter.

### Phase 2: Audit mode (60 min)
Add audit mode with composable categories. 3 categories implemented directly (frontmatter, instruction quality/adaptive-pathing, cross-invocation integration). 5 categories delegated to existing skills. Score 0-100 per category, letter grade.

### Fix: frontmatter says "Two modes" but body has three
Pre-existing inconsistency. Update description to reflect actual 3 modes + new audit mode.

## Acceptance criteria

1. `/skill-dev <skill-name>` routes correctly based on question shape
2. `/skill-dev audit <skill-name>` produces scored report
3. Existing modes unchanged
4. Delegation wiring correct (eval→/grok-verify, preflight→grok-discovery, create→/create-skill, prune→/skill-prune)

## Constraints

- Do NOT absorb techniques from reflect/prospect/skillopt (noted in wiki for future)
- Do NOT add eval, preflight, from-docs, or similarity modes
- Do NOT restructure to reference/ files (skill is 25KB, healthy)
