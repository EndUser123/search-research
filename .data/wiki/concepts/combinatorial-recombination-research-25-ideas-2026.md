---
title: "Combinatorial recombination research: 25 novel ideas from cross-domain synthesis"
created: 2026-08-06
source: session-20260806
tags: [combinatorial-creativity, recombination, skill-improvement, fleet-improvement, research]
summary: >
  Decomposed 45 improvement ideas into atomic primitives, explored cross-domain
  pairs for contradiction-resolution potential, and researched all 25 novel
  recombinations. Each idea rated for feasibility and impact on Grok Build.
  The top 8 ideas address documented fleet problems (stale handoffs, dead
  instructions, context bloat, change-amplified degradation) with mature
  external evidence. Notable findings: AgentLTL's dual-purpose spec (R1/R25),
  ByteRover's deliberate-curation memory (R14), SagaLLM's compensation pattern
  (R15), and Grok API's confirmed prefix caching support (R17).
agent: grok
host: grok
cognitive_load: 5
verification: multi-source-verified
relations:
  - target: wiki/concepts/novel-skill-improvement-approaches-2026.md
    type: extends
  - target: wiki/concepts/go-structural-transformation-code-orchestration-2026.md
    type: extends
  - target: wiki/concepts/skill-bloat-research-thresholds-and-techniques-2026.md
    type: extends
  - target: wiki/concepts/adaptive-orchestration-task-shape-classification.md
    type: related
---

# Combinatorial recombination research: 25 novel ideas

## Decision context

The operator asked: "is there use in decomposing all ideas into smallest usable functions, then iterating through all possible combinations to find new usable ideas?" After confirming the combinatorial creativity approach is evidence-backed (TRIZ, morphological analysis, Boden), we decomposed 45 ideas into 45 atomic primitives, scanned ~200 cross-domain pairs, identified 25 novel recombinations, and researched each.

## Related concepts

- [[novel-skill-improvement-approaches-2026]] — the prior research that generated the 45 ideas these recombinations build on
- [[behavioral-compliance-gap-agent-skips-instructed-steps-without-verifying]] — the #1 fleet failure that R1/R22/R25 address
- [[accumulation-problem-resolution-rate-binding-constraint]] — the #1 fleet friction that R5 addresses
- [[context-firewall-architecture]] — the existing infrastructure that R2/R6 extend

## What this means for our workspace

This concept is a **catalog**, not a plan. It maps the full combinatorial space of fleet improvements from cross-domain synthesis. Individual ideas should be triaged by the operator and pursued via `/plan` or `/go` when selected.

## Full research matrix (25 recombinations)

### Tier 1 — High impact, research-backed

| # | Idea | Feasibility | Impact | Evidence | What to build |
|---|---|---|---|---|---|
| R1 | Compliance-gated execution | H | H | AgentLTL (arXiv:2607.02599) — dual-purpose spec | Spec compiler: skill checklist → FO-LTL monitor → PreToolUse gate + /check scorer |
| R5 | Self-healing handoff lifecycle | H | H | Lease/expiration patterns; claim_handoff.py exists | Scheduled sweep: auto-release stale claims, flag dangling references |
| R14 | Agent-writable knowledge store | H | H | ByteRover (arXiv:2604.01599) — SOTA 96.1% LoCoMo | Formalize kb_write/query/correct API over wiki concepts |
| R22 | Adversarial compliance testing | H | H | AgentDojo, NIST ARIA, exec-gate 21 tests | Chaos harness: inject violations per gate, verify caught |
| R24 | Contracts with freshness | H | H | SkillGuard (arXiv:2605.10990), dbt freshness | contracts: frontmatter + validate_contracts.py with staleness |
| R25 | Spec-as-compliance-contract | H-M | H | AgentLTL dual-purpose spec | Constraint compiler: handoff AC → temporal constraints → trace scorer |

### Tier 2 — Strong, medium effort or impact

| # | Idea | Feasibility | Impact | Evidence | What to build |
|---|---|---|---|---|---|
| R2 | Context-firewall bridges | H | M-H | Google A2A, MCP typed protocols | Schema-validated handoff packets at machine boundaries |
| R3 | Traceable execution trees | M | M-H | Traccia (arXiv:2607.14309), GAAT, OTel GenAI | OTel span per decision node in workflow scripts |
| R6 | Budgeted broadcast bus | M-H | H | GWA (arXiv:2604.08206), MMP | Severity field + budget-probe arbiter extending context firewall |
| R7 | Cognitive-load ceremony stripping | H | M | Ares 52.7% token cut (arXiv:2603.07915) | Pre-dispatch classifier setting reasoning.effort |
| R8 | Admission-gated improvement loop | M | H | RSEA (arXiv:2606.28374), held-out gate decisive | Eval harness + keep-better gate + lineage tracking |
| R15 | Transactional agent workflows | M-H | M-H | SagaLLM (arXiv:2503.11951), Cordum | Rhai compensation-registry + LIFO rollback phase |
| R16 | Improvement error budget | M | H | Agent-SRE pattern, change-freeze gates | Correction-rate SLO → pre-commit gate on skill edits |
| R17 | Cache-stable compaction | H | M-H | TokenPilot 56-87% cost cut; Grok API supports caching | Immutable prefix + volatile suffix compaction |
| R20 | Quality-gated stopping | M | M | SHP 38% token cut (arXiv:2606.27009) | Convergence detector for iterative subagent loops |

### Tier 3 — Real but lower certainty or narrower scope

| # | Idea | Feasibility | Impact | Evidence |
|---|---|---|---|---|
| R4 | Resilience-weighted dispatch | M | M | ReliabilityBench (arXiv:2601.06112) |
| R9 | Decomposition-aware skill search | H | M | SkillWeaver (arXiv:2606.18051) |
| R10 | Self-verifying code actions | H | M | Self-Spec, PALM |
| R11 | Decay-driven consolidation | H | M-H | ByteRover AKL, Park 2023 |
| R12 | Utility-ordered DAG | M | M | HEFT, Airflow priority_weight |
| R13 | Zone-specialist routing | M | M | Microsoft Coordinator pattern |
| R18 | Profile-informed blending | M | M | MASA +25.8pt (arXiv:2605.30723) |
| R19 | Tree-structure ordering | L-M | M-H theory | BT theory, Dendron |
| R21 | Unified semantic retrieval | M | M | CoALA, MIRIX (deprioritized in workspace) |
| R23 | Cost-aware parallelism | M | M | BAMAS 86% cost cut |

## Key external discoveries

- **AgentLTL (arXiv:2607.02599)** — the dual-purpose spec (measure + enforce) is exactly R1/R25
- **ByteRover (arXiv:2604.01599)** — deliberate-curation memory with SOTA 96.1% on LoCoMo, validates the wiki approach
- **SagaLLM (arXiv:2503.11951)** — saga pattern applied to agent workflows with compensation agents
- **Grok API prefix caching** — confirmed: automatic, `cached_tokens` telemetry, ~85% cost discount
- **SkillsBench composition cliff** — performance peaks at 2-3 skills, degrades sharply at 4+
- **RSEA held-out gate** — "the decisive reliability ingredient" for self-improvement

## Falsifier

The combinatorial approach produces noise if: (a) primitives are over-decomposed (losing semantic content), (b) pairs are within-domain (not cross-domain), (c) evaluation is left to the LLM instead of operator judgment. The 5-15% useful hit rate from the literature held — 25 ideas from ~200 pairs, with ~6-8 genuinely worth pursuing.

## Receipts

- AgentLTL: arXiv:2607.02599 — dual-purpose compliance spec (read by subagent)
- ByteRover: arXiv:2604.01599 — deliberate curation, 96.1% LoCoMo (read by subagent)
- SagaLLM: arXiv:2503.11951 — saga pattern for agents (cited by subagent)
- RSEA: arXiv:2606.28374 — held-out gate is decisive (cited by subagent)
- SkillGuard: arXiv:2605.10990 — environment contracts, 0 FP/599 neg (cited by subagent)
- Grok API caching: docs.x.ai/developers/advanced-api-usage/prompt-caching (read by subagent)
- ReliabilityBench: arXiv:2601.06112 — model resilience under failure (cited by subagent)
- [INFERENCE] individual idea feasibility ratings are transfer hypotheses, not tested on workspace

## Sources

- AgentLTL (arXiv:2607.02599) — trace verification + online gating
- ByteRover (arXiv:2604.01599) — deliberate-curation memory
- SagaLLM (arXiv:2503.11951) — transactional agent workflows
- SkillGuard (arXiv:2605.10990) — environment contracts
- RSEA (arXiv:2606.28374) — admission-gated self-evolution
- ReliabilityBench (arXiv:2601.06112) — resilience scoring
- SHP (arXiv:2606.27009) — semantic halting for agent loops
- Ares (arXiv:2603.07915) — adaptive reasoning effort selection
- GAAT (arXiv:2604.05119) — governance-aware agent telemetry
- TokenPilot (arXiv:2606.17016) — cache-stable compaction
- GWA (arXiv:2604.08206) — global workspace agents
- MASA (arXiv:2605.30723) — model-aware skill alignment

## Auto-related

- [[skill-catalog]]
- [[skill-graph]]
- [[deep-research-systems-and-web-upgrade]]
- [[web-search-tool-routing]]
- [[notebooklm-gemini-notebook-programmatic-access]]

