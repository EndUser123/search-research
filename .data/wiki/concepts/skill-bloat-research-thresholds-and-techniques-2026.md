---
title: "Skill file bloat research: thresholds, techniques, and what transfers to Grok Build"
created: 2026-08-06
source: session-20260806
tags: [skill-design, skill-bloat, progressive-disclosure, context-engineering, research]
summary: >
  At 926 lines / ~13K tokens, /go is 2.6× the recommended skill body ceiling.
  Controlled studies show measurable reasoning degradation at just 3K tokens
  (Levy et al. ACL 2024). The "500-line" threshold originates from Anthropic's
  official Claude Code docs, not MindStudio. Lazy loading via frontmatter is
  unimplemented; the only proven mechanism is skill-native 3-stage progressive
  disclosure. Rich abstract + link is the highest-ROI technique for extracted
  references.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/risks-skill-improvement-research-2026.md
    type: extends
  - target: wiki/concepts/agents-md-construction-best-practices.md
    type: complements
  - target: wiki/concepts/multi-model-ensemble-design-patterns-for-agent-skills.md
    type: related
---

# Skill file bloat research: thresholds, techniques, and what transfers

## Decision context

**Why this was needed:** after extracting 2 sections from `/go` SKILL.md (926 lines from 1021), the operator asked whether the skill is still bloated and what other techniques exist. The prior research (`risks-skill-improvement-research-2026.md`) covered progressive disclosure for `/risk` but not the general skill-bloat threshold question.

## Key findings

### The compliance cliff (strongest evidence)

| Metric | Source | Evidence tier |
|---|---|---|
| 71% rule adherence at 400+ lines vs 96% at ~50-line focused files | codeforcreatives.com case study | Practitioner measurement |
| 24-point reasoning accuracy drop at just 3K tokens | Levy et al. ACL 2024 | Controlled study (peer-reviewed) |
| "Keep SKILL.md under 500 lines" | Anthropic official Claude Code skills docs | Vendor recommendation |
| ~5K token body ceiling for skills | shinyaz.com 3-stage progressive disclosure | Practitioner |

### Correction from prior research

The "500-line threshold" was attributed to MindStudio in our prior research. It actually originates from **Anthropic's official Claude Code skills docs** (`<Tip>Keep SKILL.md under 500 lines.</Tip>`). MindStudio independently recommends ~2,000-3,000 tokens (~500 lines), but the canonical source is Anthropic. MindStudio's "inverted U" is about task complexity, not file size.

### Lazy loading: aspirational, not real

`loading_strategy: lazy` in frontmatter is **unimplemented or aspirational as of 2026** (wrsmith108 measured zero benefit). The only proven lazy-loading mechanism is:
1. **Skill-native 3-stage progressive disclosure**: metadata (~100 tokens) → body (target <5K) → supporting files on-demand
2. **Claude Code `ToolSearch` for MCP tool schemas** (85% reduction) — does NOT apply to instruction files

The mechanism that works for us: the skill body has explicit `Load reference/X.md` instructions. The agent reads the reference when the step fires. This is progressive disclosure through procedure, not through a flag.

### Rich abstract + link (highest-ROI for extracted references)

wrsmith108's eval found that the quality of the reference pointer matters more than whether you extract:
- **Thin ref** ("see reference/foo.md"): agents open ALL sub-docs on ambiguous tasks (5/5)
- **Rich abstract + link** (3-5 sentence synopsis with concrete facts + trapdoor link): agents open only 1 (main only) on focused tasks, 2 on ambiguous tasks

**Action:** enrich our existing reference pointers with concrete facts so the agent rarely needs to open the reference file.

## Techniques ranked by applicability to Grok Build SKILL.md

| # | Technique | Evidence | Applicability |
|---|---|---|---|
| 1 | Rich abstract + link for extracted references | wrsmith108 eval | HIGH — file-type-agnostic |
| 2 | Continue splitting to ~350 lines (~5K tokens) | shinyaz 3-stage | HIGH — native skill pattern |
| 3 | "Would removing this cause a mistake?" deletion pass | Anthropic + codeforcreatives | HIGH — likely 15-30% redundant |
| 4 | Guidance-at-top / workflow-at-bottom ordering | shinyaz | HIGH — pure reorder |
| 5 | Compress command blocks to terse hints | wrsmith108 | MEDIUM |
| 6 | Reference index at END, not top | wrsmith108 | HIGH — trivial move |

## What this means for our workspace

1. `/go` at 926 lines is in the 71%-adherence regime. Two more extraction rounds could bring it to ~350 lines.
2. Our existing reference extractions (delegation-detection.md, prompt-enhancement.md, model-routing.md) should have their SKILL.md pointers enriched from thin refs to rich abstracts.
3. Prompt caching does NOT change the performance calculus — cached tokens still consume attention budget.
4. The deletion pass (technique #3) is the highest-ROI action that doesn't require structural changes.

## Falsifier

If a controlled A/B test on our specific skill (split vs unsplit, same task set) shows no accuracy difference, the bloat concern is overblown for our context. The evidence is mechanistic + practitioner, not a controlled test on our specific file. Anthropic's skill-creator plugin can run this A/B test.

## Related concepts

- [[risks-skill-improvement-research-2026]] — prior research on progressive disclosure for /risk skill
- [[agents-md-construction-best-practices]] — progressive disclosure pattern for AGENTS.md (same principle, different file type)
- [[adaptive-expansion-evidence-triggered-conditional-steps]] — the pattern structure that enables on-demand loading
- [[multi-model-ensemble-design-patterns-for-agent-skills]] — skill design patterns that affect token budget

## Receipts

- Levy et al. ACL 2024: `aclanthology.org/2024.acl-long.818.pdf` — controlled study, 24pp reasoning drop at 3K tokens (read by subagent)
- Anthropic Claude Code skills docs: `code.claude.com/docs/en/skills` — "Keep SKILL.md under 500 lines" (cited by subagent)
- wrsmith108 lazy loading eval: `github.com/wrsmith108/claude-md-optimizer` README — lazy frontmatter flag added zero benefit (read by subagent)
- codeforcreatives compliance data: `codeforcreatives.com/blog/your-claude.md-is-probably-too-long` — 71% vs 96% adherence (read by subagent)
- [INFERENCE] Our /go at 926 lines is in the "71% adherence regime" — the codeforcreatives data was measured on CLAUDE.md files, not SKILL.md; transferability is likely but unverified on our specific file

## Sources

- Levy et al. "Same Task, More Tokens" (ACL 2024) — controlled study: 24pp drop at 3K tokens
- Liu et al. "Lost in the Middle" (TACL 2023) — U-shaped attention curve at ~4K tokens
- Chroma "Context Rot" (Jul 2025) — focused (~300 tokens) vastly outperforms full (~113K tokens)
- Anthropic "Effective context engineering for AI agents" (Sep 2025) — "smallest set of high-signal tokens"
- Anthropic Claude Code skills docs — "Keep SKILL.md under 500 lines"
- shinyaz.com (Mar 2026) — 355→59 line case study, 3-stage progressive disclosure
- codeforcreatives.com (2026) — 1,578→107 case study, 71% vs 96% compliance data
- wrsmith108/claude-md-optimizer (GitHub 2026) — lazy loading is aspirational; rich abstract + link pattern
- thepromptshelf.dev (2026) — hierarchical CLAUDE.md splitting guide

## Auto-related

- [[skill-catalog]]
- [[user-modeling-for-agentic-clis]]
- [[skill-graph]]
- [[research-vs-design-vs-architect-skills-and-www-self-assessment]]
- [[deep-research-systems-and-web-upgrade]]

