---
title: "Plugin skill migration: port, absorb, or retire with version tracking"
created: 2026-08-04
source: session-2026-08-04
tags: [plugin-migration, skill-lifecycle, version-tracking, source-plugin, vendored-skills, port-absorb-retire, transferable-technique]
summary: >
  When disabling a plugin that provides skills, each skill needs a disposition:
  port (copy natively with source_plugin + source_commit frontmatter for drift
  detection), absorb (extract the technique into an existing skill), or retire
  (capability covered elsewhere). The version-tracking via source_plugin +
  source_commit + check_vendored_skills.py enables upstream drift detection
  without locking the native version to the plugin's update cycle. Applied to
  mattpocock-skills: 10 ported, 4 absorbed, 28 retired.
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - Git commit 9a24ade (10 skills ported with source_plugin frontmatter)
  - Git commit bf6e7dd (skill graph updated for new skills)
  - check_vendored_skills.py output (all 11 vendored skills at up_to_date)
relations:
  - target: wiki/concepts/config-disabled-list-bare-name-collision.md
    type: related — both are hazards surfaced during the same plugin migration
  - target: wiki/concepts/agent-config-directory-taxonomy.md
    type: extends — that concept documents skill directory taxonomy; this adds the migration methodology
  - target: wiki/concepts/skill-host-applicability-convention.md
    type: related — ported skills need host: grok frontmatter per the host provenance convention
---

# Plugin skill migration: port, absorb, or retire with version tracking

## Decision context

**Why this was needed:** the mattpocock-skills plugin provided 22 loaded skills. Some were unique (teach, wayfinder, triage); some duplicated native skills (handoff, code-review); some contained techniques worth extracting but not worth standalone skills (ubiquitous-language, design-an-interface). The operator wanted to disable the plugin (to eliminate duplicate skill entries in the picker) while keeping the valuable capabilities. The question: what's the systematic way to decide what to keep and how to track it?

## The port/absorb/retire framework

For each skill in the plugin, assign exactly one disposition:

| Disposition | What it means | When to choose | Frontmatter |
|-------------|--------------|----------------|-------------|
| **PORT** | Copy the SKILL.md natively to `~/.grok/skills/<name>/` | Unique capability, no native equivalent, actively useful | Add `source_plugin`, `source_commit`, `host: grok` |
| **ABSORB** | Extract the technique into an existing native skill | Technique is valuable but doesn't warrant a standalone skill | Document in the absorbing skill's body; no new file |
| **RETIRE** | Don't port — capability covered elsewhere or not applicable | Duplicate of a native skill, or not relevant to this workspace | Nothing to do; dies with the plugin |

## Version tracking for ported skills

Each ported skill gets two frontmatter fields:

```yaml
source_plugin: mattpocock-skills
source_commit: 2ab958093e83e0ec752e6c1c5932da465bf23e0c
```

A check script (`~/.grok/scripts/check_vendored_skills.py`) reads all skills with `source_plugin:` frontmatter, compares their `source_commit` against the plugin's current git HEAD, and reports drift. Run manually or wire into `/maintain`.

**Two-tier check:**
- Tier 1 (fast, 5ms): git HEAD compare — if same, upstream unchanged
- Tier 2 (if HEAD changed, 50ms): per-file SHA256 to identify which specific skills changed

This enables upstream drift detection without locking the native version to the plugin's update cycle. The native skill can diverge from the source (adapted, improved, extended) while still tracking whether the upstream has new changes worth reviewing.

## Worked example: mattpocock-skills migration (2026-08-04)

| Disposition | Count | Skills |
|-------------|-------|--------|
| **PORT** | 10 | teach, writing-great-skills, to-spec, to-tickets, wayfinder, triage, improve-codebase-architecture, diagnosing-bugs, tdd, wizard |
| **ABSORB** | 4 | design-an-interface → `/design --design-it-twice`; ubiquitous-language → `/domain-terms`; edit-article → `/write` revise mode; request-refactor-plan → `/refactor` Fowler invariant |
| **RETIRE** | 28 | handoff (native exists), code-review (native /review), research (native /www), ask-matt (native /ask), grilling/grill-me/grill-with-docs/batch-grill-me/loop-me (replaced by /grill-me), tdd/prototype/codebase-design/domain-modeling/resolving-merge-conflicts (superpowers duplicates), all deprecated/misc/personal skills |

**Absorption details:** for absorbed techniques, the extraction point is documented in the absorbing skill's body. Example: `/design` SKILL.md has a `--design-it-twice` mode section that references the source technique. This preserves provenance without creating a standalone skill.

## What this means for future plugin migrations

1. **Inventory first:** run `grok inspect` to list all skills the plugin provides. Categorize each as port/absorb/retire before touching any files.
2. **Clean the disabled list before creating native skills:** the pre-migration disabled list will contain names that are about to become native skill names (see [[config-disabled-list-bare-name-collision]]).
3. **Tag everything:** every ported skill gets `source_plugin` + `source_commit`. This is non-negotiable — without it, drift detection is impossible.
4. **Absorb techniques, not skills:** when a plugin skill has a useful technique but doesn't warrant a standalone skill, extract the technique into the most relevant existing skill's body. Document where it came from.
5. **Disable the plugin after migration:** once all valuable skills are ported/absorbed, disable the plugin. The retired skills die with it.
6. **Verify with check_vendored_skills.py:** after migration, run the drift checker to confirm all ported skills are at the expected commit.

## Falsifier

This methodology is wrong if:
- Ported skills diverge so far from upstream that the version tracking is meaningless (source_commit points at a version that no longer resembles the native skill)
- The plugin is never updated, making drift detection unnecessary overhead
- A future Grok Build release adds native plugin-skill-level disabling, making the port/absorb/retire framework unnecessary

## Receipts

- **`check_vendored_skills.py`:** `C:/Users/brsth/.grok/scripts/check_vendored_skills.py` — the drift detection script
- **10 ported SKILL.md files:** each at `~/.grok/skills/<name>/SKILL.md` with `source_plugin: mattpocock-skills` and `source_commit: 2ab958093e83e0ec752e6c1c5932da465bf23e0c`
- **Git commit 9a24ade:** the commit that ported 10 skills + created /grill-me, /domain-terms, /write + disabled the plugin

## Related concepts

- [[config-disabled-list-bare-name-collision]] — the hazard that fires when disabled-list bare names match newly-created native skills
- [[agent-config-directory-taxonomy]] — the skill directory taxonomy that explains why native vs plugin resolution priority matters
- [[skill-host-applicability-convention]] — ported skills need `host: grok` frontmatter for cross-host provenance

## Auto-related

- [[skill-catalog]]
- [[skill-graph]]
- [[Python-Behavior-Tree-Framework-for-Autonomous-LLM-Agents--Technical-Specificatio]]
- [[config-disabled-list-bare-name-collision]]
- [[close-single-authority-renderer]]

