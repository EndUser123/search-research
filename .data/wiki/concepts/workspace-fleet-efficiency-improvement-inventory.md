---
title: "Workspace fleet efficiency: 18 improvement ideas across 4 framings"
created: 2026-08-07
source: session-019fd820
tags: [improvement-cycle, efficiency, token-reduction, constraint-decay, leverage, fleet-optimization, brainstorming]
summary: >
  A brainstorming session across four framings of the workspace improvement
  problem (loop compression, deterministic code, knowledge-to-action, leverage)
  produced 18 concrete ideas. The four framings converge on a shared insight:
  measurement before addition. The highest-leverage ideas serve 3+ framings
  simultaneously — skill validation, bloat trimming, rule consolidation, and
  knowledge actionability auditing.
agent: grok
host: grok
cognitive_load: 3
verification: observed
relations:
  - target: wiki/concepts/measurement-before-addition-principle.md
    type: extends
  - target: wiki/concepts/session-derived-improvements-from-insight-work.md
    type: extends
  - target: wiki/concepts/signal-prioritization-for-improvement-detection.md
    type: complements
  - target: wiki/concepts/compound-skill-improvement-patterns.md
    type: related
  - target: wiki/concepts/mechanical-enforcement-of-llm-skill-steps-2026.md
    type: related
---

# Workspace fleet efficiency: 18 improvement ideas across 4 framings

## Decision context

**Why this was needed:** the operator asked for ideas that improve efficiency,
effectiveness, smoothness, token reduction, and creativity. The brainstorming
process diverged on four problem framings before generating solutions,
producing a structured inventory that maps each idea to the framings it serves.
This entry preserves the inventory so future sessions can pick up specific
ideas without re-deriving the analysis.

## The four framings

| Framing | Core problem | Key metric |
|---------|-------------|------------|
| **A: Loop compression** | Improvement cycles are too long (7 phases) and lose signal at boundaries | Phases per improvement cycle |
| **B: Deterministic code** | Prose rules have a ~50% compliance ceiling; 261 known defects across 72 skills | Defects caught by code vs prose |
| **C: Knowledge-to-action** | Wiki has 244+ concepts but unknown retrieval rate — "graveyard of documented-but-unused patterns" | Concept-to-action conversion rate |
| **D: Leverage over completeness** | Skills are bloated (top 5: tp 1662, design 1444, model-web 1350, www 1260, review 1166 lines) — constraint decay | Tokens per invocation × frequency |

## Tier 1 ideas (serve ≥3 framings)

### Skill validator + pre-commit hook (A2, B1, D1)

**What:** `skill_validator.py` checks SKILL.md frontmatter, content structure,
and description-body consistency at commit time. Catches the 106 measured
defect classes. Eliminates reactive review cycles.

**Status:** handed off at `P:/docs/handoffs/skill-md-structural-validator-019fd820/HANDOFF.md`.
Rule specification drawn from [[session-derived-improvements-from-insight-work]]
and the skill-linter taxonomy (47 rules across 5 categories).

**Measurement:** 106 defects across 72 skills (49 missing version, 21 missing
host, 12 over 500 lines). Already measured.

### Skill bloat audit + trim pass (B2, D1, D3)

**What:** identify skills over 500 lines / 5000 tokens. Trim enhancement-batch
history, repeated rules, ceremony steps. Move to `reference/` files.

**Why it matters:** the top 5 skills (`tp` 1662, `design` 1444, `model-web`
1350, `www` 1260, `review` 1166) consume 8,000-12,000 tokens each — a quarter
of the context window on every invocation. Constraint decay research shows
LLMs lose 30+ accuracy points as rules accumulate.

**Measurement needed:** token count per skill (currently unknown). A
`context_budget.py` script would compute this and rank by cost × frequency.

### Rule consolidation pass (B3, D1, D3)

**What:** grep all SKILL.md files for repeated instruction patterns. Each
duplicated rule costs tokens every time either skill loads. Externalize to
shared `reference/workspace-rules.md`, link with one line.

**Estimated savings:** 50-200 tokens per skill invocation across the fleet.

**Measurement needed:** cross-skill grep for repeated patterns.

### Wiki concept actionability audit (C1, C4, D1)

**What:** measure what % of wiki concepts are retrieved after creation.
Concepts not retrieved in 90+ days → stale. 180+ days → prune candidates.

**Why it matters:** [[signal-prioritization-for-improvement-detection]]
documents that SRE teams target 30-50% alert-to-action conversion. Below 20%
= noise problem. We don't know our wiki concept retrieval rate.

**Measurement needed:** `concept_retrieval.py` — grep session transcripts for
concept slug references after creation date.

## Tier 2 ideas (serve 2 framings)

| Idea | Framings | What |
|------|----------|------|
| Context-budget dashboard | D2, B2 | Rank skills by token cost × frequency |
| `/www` + `/tp` fusion | A1, B4 | Combine research with counterexample checking; cuts loop from 7 to 4 |
| Handoff-to-completion tracker | C2, C3 | Measure handoff pickup rate; close cross-session accountability |
| Wiki lifecycle (last_retrieved) | C4, D1 | Track when concepts were last referenced |
| Ceremony audit | D4, A3 | Find procedural steps that never change outcomes |
| Wiki → enforcement gate pipeline | B4, C4 | Turn documented failure patterns into blocking sensors |

## Tier 3 ideas (single-framing, creative)

| Idea | Framing | What |
|------|---------|------|
| Cross-domain analogy injection | D (creativity) | Surface analogies from other domains when stuck |
| "What if opposite?" steelman prompt | D (creativity) | Auto-generate steelman of rejected options |
| Cross-session connection surfacing | D (creativity) | Extend `/notice` T7 to handoff patterns |
| Skill-change checklist hook | A3 | Mechanical checks when SKILL.md is edited |
| Stated-intent cross-session tracker | C3 | Track whether handoff tasks get done |
| Fix `claim_handoff.py` | A (infra) | Broken tooling blocks handoff claiming fleet-wide |
| `/www` Step 3.15 as script | B1 | Automate workspace-counterexample check |
| `propagation_check.ps1` as git hook | B1 | Automate manual propagation check |

## The convergence pattern

All four framings converge on the same starting point:
[[measurement-before-addition-principle]]. Before implementing any idea:
1. Measure the current state (defect rate, token cost, retrieval rate, cycle length)
2. Identify the bottleneck (scarcity vs overflow vs decay vs inaction)
3. Then implement the fix that addresses the measured bottleneck

The inventory is prioritized by framing-coverage (Tier 1 serves 3+) because
ideas that serve multiple framings have the highest leverage — fixing one
thing improves multiple dimensions simultaneously.

## What this means for our workspace

- **Start with measurement:** the context-budget dashboard and wiki
  actionability audit are prerequisites for knowing where to invest. Without
  them, any implementation is guessing.
- **The skill validator is already handed off** — it's the one idea where
  the measurement is complete (106 defects measured) and the implementation
  path is clear (extend `script_scan.py`).
- **The bloat audit is the highest-leverage trim:** if the top 5 skills lost
  30% of their body, that's ~2,000 tokens saved per invocation × 5 skills ×
  every session. That's real context budget freed for actual work.
- **The knowledge-to-action gap is the most uncertain:** we don't know if the
  wiki graveyard problem is real or perceived. The measurement must come first.

## Falsifier

This inventory is wrong if:
- The ideas are individually sound but mutually exclusive (implementing one
  prevents another) — needs dependency analysis before starting
- The measurement-first pattern produces analysis paralysis (measuring forever,
  never implementing) — needs a time-box per measurement
- The token savings from bloat trimming are offset by reduced rule compliance
  (shorter skills = fewer rules followed = more defects) — the validator
  catches this if wired before the trim

## Receipts

- `P:/tmp/skill_audit.py` — measured 106 structural defects across 72 skills.
  Session 019fd820.
- `~/.grok/skills/skill-dev/__lib/script_scan.py` — existing scanner that found
  155 code-level defects. Source: handoff `batch-skill-defect-cleanup-20260806`.
- Session transcript 019fd820: `/brain` output produced the 18-idea inventory
  across 4 framings, with the convergence analysis.
- `/tp` critique subagent (019fd85c): produced the blind-spot finding that
  motivated framing C (knowledge-to-action gap).

## Sources

- Session 019fd820 brainstorming output (4 framings, 18 ideas)
- [lucidshark.com constraint decay research](https://lucidshark.com/blog/constraint-decay-llm-agents-backend-code-quality-gates-2026) (2026-05) — 30+ accuracy points lost as constraints accumulate
- [incident.io SRE alerting best practices](https://incident.io/blog/sre-alerting-best-practices) (2026-03) — 30-50% alert-to-action conversion rate target
- [[measurement-before-addition-principle]] — the convergence pattern
- [skill-linter (aicatalyst-team)](https://github.com/aicatalyst-team/skill-linter) — 47-rule taxonomy for SKILL.md validation
- [ai-linter (fchastanet)](https://github.com/fchastanet/ai-linter) — Python SKILL.md validator with pre-commit integration
- [agent-gates (zl190)](https://github.com/zl190/agent-gates) — structural vs semantic quality gate distinction

## Auto-related

- [[skill-graph]]
- [[improvement-surfacing-fleet-fragmentation-routing-and-meta-improvement]]
- [[skill-catalog]]
- [[self-improving-agent-systems-techniques-and-workspace-gaps]]
- [[solo-director-ai-fleet-coordination-isolation-best-practices]]

