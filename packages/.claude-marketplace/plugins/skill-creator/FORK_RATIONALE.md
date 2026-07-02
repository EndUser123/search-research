# Fork Rationale — skill-creator

**Origin:** Anthropic-official `skill-creator` from the `claude-plugins-official` marketplace (`~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator`).
**Forked:** 2026-07-02. **Local version:** 1.0.0.

## Why we forked (don't forget)

1. **It is the canonical captain of the skill-creator consolidation.** `/claude-audit` found 5 overlapping skill-creators (`write-a-skill`, `writing-skills`, skillet `build`, this `skill-creator`, `plugin-dev:skill-development`). This one wins: it is the only one with a real **eval-driven authoring loop** (draft → eval → benchmark → iterate) — `scripts/run_eval.py`, `aggregate_benchmark.py`, `eval-viewer/`, plus grader/analyzer/comparator agents and `references/schemas.md`. The others are static scaffolders.

2. **We plan to customize it.** Folds scheduled (separate work, after this fork establishes a clean baseline):
   - `writing-skills`' **Iron Law** (no skill without a failing test first — TDD-for-skills).
   - `write-a-skill`'s **progressive-disclosure threshold** (content > ~500 lines → split to a reference file).
   These edits would be overwritten by upstream updates if we consumed it live.

3. **Upstream-merge policy.** We own this copy. When Anthropic ships an improved skill-creator, diff against origin and merge manually — do NOT blindly `cp` over this tree or you lose the folds. Re-pull origin from the path in §Origin above.

## Precedent
Same fork pattern as `glm-plan-usage` (local fork, keyword `fork`, description prefixed `LOCAL FORK of ...`). See marketplace.json entry.

## What NOT to do
- Do not delete this file — it is the audit trail for why the fork exists.
- Do not point `installed_plugins.json` back at the upstream marketplace source; this local copy must stay canonical.
- Do not bump version on every upstream-tracking edit — only on substantive local change (per `plugin-audit-and-fix` convention).
