# Handoff — Trigger-test step for skill-dev Mode 2

## Status
OPEN — design clear, implementation not started.

## Objective

Add eval-driven trigger accuracy testing to `/skill-dev` Mode 2 (improve).
Currently skill-dev measures structural quality (defects, leanness,
enforcement) but does NOT measure trigger accuracy — whether the skill
fires when it should and doesn't fire when it shouldn't. The field's #1
recommendation is eval-driven description optimization with train/validation
query sets and trigger-rate measurement.

See [[skill-effectiveness-measurement-gaps-trigger-accuracy-token-efficiency]]
for the research basis.

## Design

### What to add to skill-dev Mode 2

Add a new step between Step 2 (techniques query) and Step 3 (improvement
proposals): **Step 2.8 — Trigger accuracy assessment**.

**Procedure:**
1. Read the target skill's `description` frontmatter field
2. Generate ~20 eval queries from the skill's domain:
   - 10 should-trigger queries (phrasings a user would say when they want this skill)
   - 10 should-not-trigger queries (near-misses that belong to adjacent skills)
3. For each query, reason about whether the description would match it
   (LLM judgment — no automated triggering needed for v1)
4. Score: true positives (should-trigger + matches), false negatives
   (should-trigger + doesn't match), false positives (should-not + matches),
   true negatives (should-not + doesn't match)
5. Compute trigger accuracy: (TP + TN) / total
6. If accuracy < 80%: flag description as needing optimization
7. Propose description improvements targeting the failure cases

### What NOT to add (v1 scope)

- Automated triggering (requires running the agent with each query — too
  expensive for v1). LLM judgment of description-vs-query matching is
  sufficient for the first iteration.
- Token efficiency tracking (separate gap — hand off separately)

## Scope

- **In scope:** `~/.grok/skills/skill-dev/SKILL.md` — add Step 2.8 to Mode 2
- **Out of scope:** modifying other skills, building automated trigger infrastructure

## Acceptance criteria

1. Step 2.8 exists in skill-dev Mode 2 between Steps 2 and 3
2. Step generates eval queries from the skill's domain (not generic queries)
3. Step produces a trigger accuracy score (TP/FP/FN/TN)
4. Step proposes description improvements when accuracy < 80%
5. The eval query generation considers the skill's existing `when-to-use:`
   frontmatter and exclusion clauses
6. The step is documented with examples

## Key files

- Skill: `~/.grok/skills/skill-dev/SKILL.md`
- Research: `P:/.data/wiki/concepts/skill-effectiveness-measurement-gaps-trigger-accuracy-token-efficiency.md`
- Techniques index: `P:/.data/wiki/concepts/skill-techniques-index.md` (T16 is closest)
- Field source: https://agentskills.io/skill-creation/optimizing-descriptions

## Handoff is wrong if

- The trigger accuracy assessment produces generic queries that don't test
  the specific skill's domain
- The step adds >200 lines to skill-dev (it should be ~50-80 lines — a
  focused step, not a sub-skill)
- The LLM-judgment approach (v1) produces wildly inaccurate scores vs
  actual agent triggering (test: compare LLM judgment to transcript
  evidence for 3 skills with known trigger history)
