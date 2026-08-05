---
title: "Wiki-integrated skills: the query-at-start, save-at-end pattern"
created: 2026-07-25
source: session-2026-07-25 (skill audit for wiki integration gaps)
tags: [skill-design, wiki-integration, feedback-loop, query-then-save, skill-improvement, transferable-pattern]
agent: grok
host: both
cognitive_load: 2
verification: local-only
summary: >
  Skills that produce durable findings should integrate with the wiki at two
  points: query at start (Step 0.5 — what patterns already exist?) and save
  at end (Step N — what did this run learn that future runs should find?).
  This creates a closed loop where each invocation compounds on prior ones.
  /why is the gold standard (Step 0.5 pattern-library query + Step 15
  feedback-to-wiki with mechanical gate + cross-model review). Audit of 36
  user skills found 7 with proper integration, 6 with partial integration,
  and 2 clear gaps (wargame, model-benchmark). The pattern is the skill-scale
  instance of the "code orchestrates, model judges" principle: the wiki
  query/save is deterministic; the skill's analysis is the judgment.
relations:
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale
    type: companion
  - target: wiki/concepts/compound-skill-improvement-patterns
    type: refines
  - target: wiki/concepts/skill-lifecycle-toolkit
    type: extends
---

# Wiki-integrated skills: the query-at-start, save-at-end pattern

## Decision context

**The motivating question:** the operator asked "what skills should have a wiki function?" The real question: *which skills produce findings that should compound across sessions, and do they actually close the loop?*

A skill that produces a finding but doesn't save it to the wiki is **one-shot** — the next invocation starts from scratch. A skill that saves but doesn't query is **write-only** — it populates the wiki but never benefits from prior entries. The closed loop (query → work → save → future query) is what makes a skill **cumulative**.

## The three integration points

### 1. Step 0.5: Query the wiki before working

Before doing the analysis, query the wiki for prior patterns matching the task shape. This turns the skill from a one-shot analyzer into a cumulative-knowledge system.

```powershell
qmd search --collection wiki --query "<task-shape keywords>" --top-k 5
```

**What to look for:**
- A concept whose `summary:` or `## Decision context` describes the same shape
- A concept whose `tags:` match the task domain

**If a known pattern matches:** START from the known finding. Verify or disconfirm it against current evidence — do NOT re-derive from scratch.

**If no match:** proceed with full analysis. The absence of a prior pattern means this may be a new finding worth saving at Step N.

**Reference:** `/why` Step 0.5 — "Before investigating from scratch, query the wiki for known patterns matching the failure shape."

### 2. Step N: Save systemic findings to wiki

After producing findings, save the ones that are:
- **Systemic/architectural** (not session-specific one-offs)
- **Cross-session reusable** (would apply to a future invocation in a different context)
- **Has a falsifier** (could be proven wrong, not a tautology)

**Mechanical gate (not prose):** the save should be gated by deterministic criteria, not model self-assessment. Per `code-orchestrates-model-judges-skill-scale`, a prose gate breaks under closure pressure.

`/why` Step 15a is the reference: 5 mechanical criteria (classification, falsifier, receipt, named abstractly, cross-session reusable). If any fails, skip the save.

**Cross-model review:** `/why` Step 15b adds a synchronous cross-model review before writing. This catches model-family blind spots in the finding. The review is the quality gate; the mechanical criteria are the threshold to invoke it.

### 3. The closed loop

Future invocations find prior findings via Step 0.5. Without the save (Step N), the query (Step 0.5) returns nothing and the skill stays one-shot. Without the query, the save populates a wiki nobody reads. Both halves are needed.

## Which skills need this pattern

A skill needs wiki integration when it produces **findings that future invocations should learn from**. Symptoms:

1. The skill analyzes something and reaches conclusions (not just executes a procedure)
2. The same type of problem recurs across sessions
3. The findings are reusable (not session-specific)
4. The skill's value would increase if it had access to prior findings

**Does NOT need integration:** thin CLI wrappers, infrastructure skills, utilities, one-shot executors.

## Audit results (2026-07-25)

### ✅ Proper integration (query + save loop)

| Skill | Shape | Notes |
|---|---|---|
| `/why` | Step 0.5 query + Step 15 save (mechanical gate + cross-model review) | **Gold standard** |
| `/aar` | Phase 9.5 wiki promotion | Prose-gated (candidate for code enforcement per observe-then-refactor) |
| `/www` | IS wiki-web-wiki | The query→research→persist pipeline |
| `/close` | Scanner checks wiki existence | Existence not coverage (Fix 4 in handoff) |
| `/crawl4ai` | Ingests INTO wiki | One-directional (save only, by design) |
| `/design` | References wiki in workflow | Partial |
| `/wiki` | IS the wiki skill | — |

### ⚠️ Partial — needs the other half of the loop

| Skill | Has | Missing | Priority |
|---|---|---|---|
| `/debrief` | 4 refs | No Step 15 equivalent (same shape as /aar but no save loop) | **High** — produces exactly the findings that should compound |
| `/tp` | Step 0.5 preflight | No wiki query for prior critique patterns; critique log is local-only | **Medium** — the `tp_critique_log.py` should feed the wiki |
| `/check` | 3 refs | No query/save loop | Low — verifies sessions, not patterns |
| `/review` | 2 refs | Could query known bug patterns | Medium |
| `/risks` | 1 ref | Could query known attack/failure patterns | Medium |
| `/handoff` | 5 refs | Doesn't systematically save decisions | Medium |

### ❌ Clear gaps — should have integration, has none

| Skill | Why it needs it | Priority |
|---|---|---|
| `/wargame` | Failure-mode analysis. Should query known failure modes + save new ones. | **High** |
| `/model-benchmark` | Longitudinal data is the entire value. Currently evaporates. | **High** |

## How to add wiki integration to a skill

The refactoring sequence (per skill):

1. **Add Step 0.5 query.** ~5 lines. Before the skill's main work, query the wiki for patterns matching the task shape. State the match (or "no match") in the output header.
2. **Add Step N save.** ~15 lines + a mechanical gate. After producing findings, check the 5 criteria (systemic, reusable, falsifiable, named abstractly, receipt-backed). If all pass, write to wiki + log.
3. **(Optional) Add cross-model review.** If the skill's findings are high-stakes, add a synchronous cross-model review before writing (per `/why` Step 15b).
4. **Test the loop.** Run the skill twice on related tasks. The second run should find the first run's findings via Step 0.5.

## When NOT to add wiki integration

- The skill is a thin wrapper (CLI conductor, alias)
- The skill produces session-specific output (handoffs, commits)
- The skill's findings are not reusable (one-off debugging)
- The maintenance burden exceeds the compound value (the wiki concept `code-orchestrates-model-judges-skill-scale` "don't like" #6)

## Falsifier

This concept is wrong if:
- Skills with wiki integration don't actually perform better than skills without it (the query doesn't find relevant patterns; the save writes concepts nobody reads)
- The maintenance burden of keeping wiki concepts current exceeds the value of querying them
- The closed loop never closes (save writes but query doesn't find, because slugs/tags don't match)

**Measurement:** after adding integration to a skill, track: (a) how often Step 0.5 finds a relevant pattern, (b) how often Step N writes a concept, (c) whether future runs cite the prior concept. If (a) is near-zero after 20 runs, the query is too narrow or the wiki doesn't have the patterns.

## Related

- [[code-orchestrates-model-judges-skill-scale]] — the save gate should be code-enforced, not prose. This concept is the wiki-integration companion.
- [[compound-skill-improvement-patterns]] — the /www recursive self-improvement pattern; this concept generalizes it to any skill
- [[skill-lifecycle-toolkit]] — where wiki integration sits in the skill lifecycle
- [[skill-performance-and-reliability]] — measuring whether the integration actually helps

## Sources

- `/why` SKILL.md Step 0.5 + Step 15 — the gold-standard implementation
- `/aar` SKILL.md Phase 9.5 — wiki promotion of headline lessons
- Session 019f9488 skill audit (this session) — 36 skills surveyed
- `compound-skill-improvement-patterns` wiki concept — prior art on recursive skill improvement
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
