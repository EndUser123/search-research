---
title: "Technique capture and surfacing: 4 mechanisms for durable skill pattern reuse"
created: 2026-07-27
source: session-2026-07-27 (/www research on skill technique capture)
tags: [skill-design, technique-capture, pattern-library, frontmatter, discoverability, reuse, decision]
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
summary: >
  Four mechanisms that form a closed loop for capturing and surfacing reusable
  skill techniques: (1) techniques: frontmatter in SKILL.md captures at write-time,
  (2) technique-discovery prompt in /create-skill and /refactor surfaces at design-time,
  (3) /check technique-coverage audit verifies at verify-time, (4) QMD technique stubs
  make discoverable at search-time. The loop: write → discover → verify → search →
  reuse → write. Each mechanism is lightweight and triggered by an existing skill
  invocation, not a separate maintenance task. Connects to [[skill-techniques-index]],
  [[skill-feature-audit-5-key-skills]], and [[compound-skill-improvement-patterns]].
sources:
  - https://www.designsystemscollective.com/building-reusable-components-the-pattern-library-blueprint-7575930ae184 (Design Systems Collective, 2026)
  - https://daily.dev/posts/building-reusable-component-libraries-that-actually-survive-enterprise-scale-6ceykjdhq (daily.dev, 2025)
relations:
  - target: wiki/concepts/skill-techniques-index.md
    type: extends
  - target: wiki/concepts/skill-feature-audit-5-key-skills.md
    type: related
  - target: wiki/concepts/compound-skill-improvement-patterns.md
    type: related
  - target: wiki/concepts/visible-output-contracts-for-behavioral-skill-steps.md
    type: related
---

# Technique capture and surfacing: 4 mechanisms for durable skill pattern reuse

## Decision context

**Why this decision was needed:** the operator asked "how can we durably and optimally and regularly capture the skill techniques that are potentially useful in other use cases, and surface them in our skill-dev solution space?" An audit of 5 key skills found 75 reusable techniques not in the techniques index. The index was stale (6 days, 6 sessions behind). The problem has two halves: capture (finding techniques when created) and surfacing (making them findable when needed).

**What the research showed:** pattern libraries at enterprise scale fail when stale, bloated, or disconnected from actual usage. The key finding from daily.dev: "many reusable components are never reused" — building a library doesn't guarantee reuse without a discovery mechanism. Our workspace has the library (42+ techniques indexed); the gap is freshness and discoverability.

## The 4 mechanisms (closed loop)

### Mechanism 1: `techniques:` frontmatter (capture at write-time)

Every SKILL.md gains a `techniques:` frontmatter field listing technique IDs it implements. When a skill is edited, the author adds or updates the IDs. The techniques index can be auto-regenerated from the aggregate of all frontmatter fields.

```yaml
---
name: tp
techniques: [T7, T9, T10, T33, T34, T35, T36, T37, T38]
---
```

**Why this works:** the technique is captured at the moment of implementation, not deferred to a separate indexing step. No skill can claim a technique without listing it (structural enforcement). The `index_skills.py` script already runs on every `/wiki` invocation — extend it to also extract `techniques:` fields and build the reverse index (skill → techniques and technique → skills).

**Cost:** 1 line per SKILL.md edit. Near-zero ongoing cost — the field is updated when the skill is edited, not as a separate task. The field is ignored by the skill loader (Grok Build doesn't parse custom frontmatter fields beyond `name` and `description`), so it's documentation-only with no runtime impact.

**Trade-off:** the field requires the author to know technique IDs when editing a skill. If the author doesn't know the ID, they won't add it. Mitigation: mechanism 2 (technique-discovery prompt) surfaces IDs at design-time, so the author sees them before writing.

### Mechanism 2: Technique-discovery prompt (surface at design-time)

`/create-skill` and `/refactor` Step 4.1 gain a technique scan: before designing a new skill structure, `qmd search` the techniques index for applicable patterns. The output is a candidate-techniques list the designer evaluates. Same pattern as `/why` Step 0.5: query before re-deriving.

**Concrete implementation:** one `qmd search` call + one `Select-String` against the techniques index for the failure modes the new skill addresses. Takes ~5 seconds. The designer sees: "T7 Two-lens critique (implemented in: /tp) — prevents single-lens blindness. T10 Spot-check gate (implemented in: /tp, /review) — prevents uncritical synthesis." They decide which to adopt and add the technique IDs to the new skill's frontmatter.

**Trade-off:** adds ~5s to skill creation. Worth it: the alternative is re-inventing techniques that already exist (the exact problem this system solves).

### Mechanism 3: `/check` coverage audit (verify at verify-time)

When a SKILL.md is in `/check` scope, verify: (1) each technique ID in frontmatter exists in the index, (2) each technique in the index claiming this skill is listed in the skill's frontmatter. Flag mismatches as `gap` severity. Bidirectional consistency check catches drift.

**Concrete implementation:** read the skill's `techniques:` field. For each ID, grep the techniques index for `### T<N>`. If not found, flag `gap: technique ID T<N> in <skill> frontmatter not found in index`. Reverse direction: grep the index for `Implemented in: <skill>` — if the skill's frontmatter doesn't list that technique ID, flag `gap: index claims <skill> uses T<N> but frontmatter doesn't list it`.

**Trade-off:** adds ~2s per SKILL.md in scope. The bidirectional check is the structural fix for the staleness problem — it catches both "skill claims a technique that doesn't exist" and "index claims a skill uses a technique the skill doesn't acknowledge."

### Mechanism 4: QMD technique stubs (discoverable at search-time)

Each technique (T1-T42+) gets a 3-line stub in `sources/techniques/T<N>.md` with frontmatter (technique_id, prevents, implemented_in). QMD-indexed, so `qmd search "alternatives gate"` returns the technique directly. Same pattern as skill catalog stubs (972 files in `sources/skills/`).

**Trade-off:** 42-100 stub files to maintain. But they're auto-generated from the techniques index (the script reads each `### T<N>` section and writes a stub). The maintenance cost is one script run after techniques are added. This is the same model as the skill catalog stubs — auto-generated, low-fidelity, sufficient for search.

## What this means for our workspace

The loop is self-maintaining: write (frontmatter) → discover (design-time query) → verify (check-time audit) → search (QMD stubs) → reuse → write. No separate maintenance task. Each mechanism is triggered by an existing skill invocation.

The pilot: add `techniques:` frontmatter to the 5 audited skills (/tp, /why, /close, /review, /refactor). This validates the field format and gives the reverse-index generator real data to work with. The pilot uses the audit's per-skill technique mapping (from [[skill-feature-audit-5-key-skills]]) to populate the initial fields.

**What NOT to do (from the disconfirmation research):**
- Don't build a separate "technique registry" app or database. The wiki IS the registry. The techniques index IS the catalog. Adding infrastructure adds maintenance burden without proportional value.
- Don't auto-extract techniques from SKILL.md via LLM. The audit showed that technique identification requires judgment. LLM auto-extraction would produce noise.
- Don't require every technique to be in the index before use. Techniques can be used first and indexed later. The frontmatter field is the durable capture; the index is the curated surface.

## Implications

This system transforms the techniques index from a manually-maintained document into a self-maintaining infrastructure. The current model (manual updates when someone remembers) produced a 6-day, 75-technique backlog. The new model (frontmatter at write-time + check at verify-time) produces zero backlog by design — every skill edit captures its techniques, and every `/check` verifies consistency.

The system also enables a new skill-dev workflow: when designing a new skill, the designer queries for applicable techniques (mechanism 2), adopts them, and lists the IDs in frontmatter (mechanism 1). The next skill that needs the same pattern finds it via QMD (mechanism 4) and adopts it the same way. This is the [[compound-skill-improvement-patterns]] vision made structural: improvements compound because the techniques are visible and adoptable.

The pilot (5 skills with frontmatter) is the first step. The next session can extend `index_skills.py` to auto-generate the reverse index, add mechanism 2 to `/create-skill`, and generate QMD stubs. Each extension is independent — the system works incrementally.

The design draws on established pattern-library practice (design systems, component reuse) but adapts it for the AI agent skill domain. The key difference from UI pattern libraries: our "components" are behavioral techniques (gates, formats, detection mechanisms), not visual elements. The capture and surfacing mechanisms are the same, but the content is structurally different — techniques compose across skills, while UI components compose within a single application.

## Falsifier

This system is wrong if:
- **The frontmatter field is never maintained after initial addition.** Skills gain techniques but the field isn't updated. Mitigation: mechanism 3 (/check audit) catches drift.
- **The technique IDs are too granular or too coarse.** If every 3-line pattern gets a T-number, the index bloats. If only architectural patterns get T-numbers, useful tactical patterns are invisible. The current granularity (structural techniques, not content) is the right level.
- **QMD stubs add maintenance burden without search benefit.** If QMD already finds techniques inside the index concept, separate stubs are redundant. Test: `qmd search "transcript evidence scan"` — does it return T33 from the index concept, or does it need a stub?
- **The closed loop is too tight.** If every mechanism depends on every other, a failure in one (e.g., frontmatter field not maintained) breaks the whole system. Mitigation: each mechanism degrades independently. Frontmatter missing → index still works manually. Check audit not run → frontmatter still captures. QMD stubs missing → index concept still searchable as a whole.
- **The technique ID namespace collides.** If two sessions assign the same T-number to different techniques, the index corrupts. Mitigation: T-numbers are assigned sequentially from the index's highest current T-number. A new technique gets T<max+1>.

## Receipts

- **"75 unindexed techniques found":** receipt — skill-feature-audit-5-key-skills.md, subagent 019fa482 (explore, 5 tool calls, 135s).
- **"Techniques index was 6 days stale":** receipt — skill-techniques-index.md created 2026-07-21, last updated before this session's T33-T42 addition.
- **"'Many reusable components are never reused'":** receipt — daily.dev article on enterprise component libraries, web_fetch this session.
