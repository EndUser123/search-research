---
title: "Brainstorming and ideation with LLMs: mental models, frameworks, and what works"
created: 2026-07-22
source: session-2026-07-22
sources:
  - https://arxiv.org/abs/2503.00946
  - https://arxiv.org/abs/2504.20643
  - https://arxiv.org/abs/2405.06373
  - https://arxiv.org/abs/2509.21685
  - https://miro.com/brainstorming/what-is-brainstorming/
  - https://craftingcases.com/issue-tree-guide/
  - https://caseinterview.com/issue-tree
  - https://github.com/Orchestra-Research/AI-Research-SKILLs
  - https://github.com/moranmiz/Cooking-Up-Creativity
tags: [brainstorming, ideation, mental-models, llm-creativity, mece, morphological-analysis, scamper, consulting, frameworks, research]
host: both
agent: grok
cognitive_load: 4
verification: multi-source-verified
summary: >
  Comprehensive survey of brainstorming mental models, what works for LLMs, consulting
  frameworks, repos, and research papers. The decomposition→patterns→friction process
  maps to MECE + morphological analysis + inversion. Structured recombination beats
  raw prompting. LLMs are best at generation/refinement, worst at scope/evaluation.
---

# Brainstorming and ideation with LLMs

## The decomposition → patterns → friction process has a name

The operator's natural brainstorming process (decompose elements → look for patterns, similarities, differences, alignments, friction) maps to four named frameworks:

| Step | Framework | Origin |
|---|---|---|
| Decompose elements | MECE decomposition | McKinsey / Barbara Minto |
| Explore all combinations | Morphological analysis | Fritz Zwicky, 1969 |
| Find failure modes | Inversion | Munger / Stoics |
| Build from fundamentals | First principles | Aristotle → Musk |

## Brainstorming mental models (full landscape)

| Model | What it does | LLM-adaptable |
|---|---|---|
| SCAMPER | Systematic idea mutation (7 letters) | ✅ Excellent — each letter = prompt template |
| Six Thinking Hats | Perspective switching (6 roles) | ✅ Assign each hat to a subagent |
| Mind mapping | Visual decomposition | ⚠️ Structured output only |
| Brainwriting | Silent generation before sharing | ✅ Parallel subagent fan-out |
| Reverse brainstorming | "How to guarantee failure" | ✅ Strong — avoids positivity bias |
| Morphological analysis | Decompose → recombine all pairs | ✅ Strongest per research |
| Pre-mortem | "It failed. Why?" | ✅ Already used as /risk |

## What works for LLMs (from research)

**arxiv:2503.00946** (61 studies, Hourglass Framework):
- LLMs best at: idea generation, refinement, breaking fixation
- LLMs worst at: scope specification, multi-idea evaluation, novelty assessment

**arxiv:2504.20643** (Cooking Up Creativity, Hebrew U + Stanford):
- Structured recombination > raw prompting
- Extract structure → manipulate → translate back

**arxiv:2405.06373** (LLM Discussion):
- Divergent + convergent personas > single-model brainstorming

## Key takeaways for LLM brainstorming

1. Decompose before ideate (MECE or morphological)
2. Structured recombination beats "be creative"
3. Separate divergent from convergent
4. Inversion is highest-ROI for LLMs
5. SCAMPER maps to prompt templates
6. LLMs are bad at knowing if an idea is good — human judgment essential for convergence
7. The operator's natural process IS a named methodology

## Consulting frameworks

| Technique | Use |
|---|---|
| Issue trees (MECE) | Decomposition step |
| Hypothesis-driven | 80/20 of issue trees |
| Pyramid Principle | Structure LLM output |
| Porter's Five Forces | Pre-built MECE for industries |
| Jobs-to-be-Done | Alternative decomposition axis |

## Repos

- `Orchestra-Research/AI-Research-SKILLs` — creative thinking skill
- `yupeng2025/ideacyclone` — idea multiplication engine
- `moranmiz/Cooking-Up-Creativity` — structured recombination code
- `TobiasBlask/open-paper-machine` — /brainstorm command

## Related

- [[deliberation-waste-re-deriving-same-answer]] — related cognitive pattern
- [[compensating-for-weaker-models-ensemble-multi-pass]] — multi-perspective fan-out
- [[testing-methodology-both-outcomes-informative]] — hypothesis-driven approach

## Fleet and ensemble brainstorming (multi-agent)

### Multi-agent LLM teams outperform humans (d=1.50)

**arxiv:2605.17885** (Cambridge + Microsoft Research, May 2026): 4,541 LLM ideas vs 341 human ideas across 6 tasks. Multi-agent LLM teams substantially outperform human teams in creativity (Cohen's d=1.50), driven by novelty while maintaining comparable usefulness. The top 5% LLM ideas scored 58% higher than top human ideas.

### Discussion structure matters

| Structure | What it does | Best for |
|---|---|---|
| Iterative refinement | Propose, compare, keep best | Non-reasoning models (largest gain) |
| Progressive improvement | Explicit divergent→convergent | Novelty + usefulness balance |
| Open discussion | Unstructured + summary | Reasoning models (minimal effect) |
| None | No discussion | Baseline for reasoning models |

### Diversity collapse is the enemy

ACL 2026: multi-agent LLM systems exhibit semantic collapse — agents converge on similar ideas. Same-model different-persona doesn't prevent it. Mitigations: different model families, random diversion tokens, structured recombination.

### Claude dynamic workflow patterns

Six patterns that recur when orchestrating agent fleets:
1. Classify-and-act
2. Fan-out-and-synthesize
3. Adversarial verification
4. Generate-and-filter (purpose-built for ideation)
5. Tournament (purpose-built for selection)
6. Loop-until-done

Key innovation: the orchestrator is code (zero coordination tokens), not model turns.

### Fleet papers

- arxiv:2605.17885 — multi-agent outperforms humans (d=1.50)
- ACL 2026 — diversity collapse in multi-agent systems
- arxiv:2512.04488 — persona-based multi-agent brainstorming
- arxiv:2601.00475 — MIDAS distributed agentic ideation
- Gary King (Harvard) — random diversion for sustained diversity

### Fleet repos

- `kyegomez/awesome-multi-agent-papers` — curated research
- `microsoft/autogen` — multi-agent conversation
- `geekan/MetaGPT` — multi-agent software dev

## Claude Code thinking/reasoning/brainstorming tools (verified 2026-07-22)

### ultrathink — per-turn deep reasoning trigger

Claude Code detects trigger words in prompts and allocates more thinking tokens:

| Trigger | Effect | Scope |
|---|---|---|
| `think` | Small boost | Single turn |
| `think hard` | Medium | Single turn |
| `think harder` | Extended | Single turn |
| `ultrathink` | Maximum (~32K thinking tokens) | Single turn |

Maps to the `/effort` session setting: `low` → `medium` → `high` → `max` → `xhigh` (Opus 4.7+ only).
`ultrathink` ≈ `max` territory. Triggers are prompt cues, not official settings. For guaranteed control, use `/effort`.

Sources: kentgigger.com, developersdigest.tech, code.claude.com/docs

### ultracode — dynamic workflow orchestrator (the big one)

Two behaviors sharing one name:

**As a prompt keyword:** `ultracode` in a prompt → Claude writes a JavaScript orchestration script that runs in the background, coordinating up to 16 concurrent subagents (1,000 total per run cap).

**As `/effort ultracode`:** sets model to `xhigh` AND enables automatic workflow orchestration for every substantive task.

**Key architecture: "code orchestrates, model judges."** The JS script spends ZERO model tokens on coordination. 113 agents spent 1.95M tokens; the coordinating script spent zero. Intermediate results live in script variables, not in the model's context window.

Limits: 16 concurrent agents, 1,000 total per run, no mid-run user input, script has no FS/shell access (agents do), agents run in `acceptEdits` mode.

Sources: developersdigest.tech, code.claude.com/docs/en/workflows (official Anthropic docs)

### Six workflow patterns (reusable shapes)

| Pattern | What it does | Brainstorming use |
|---|---|---|
| Classify-and-act | One agent decides type, script routes | Route ideation to right framework |
| Fan-out-and-synthesize | One agent per item, merge in code | Parallel brainstorming across N perspectives |
| Adversarial verification | Separate agents check against rubric | Challenge ideas before selecting |
| Generate-and-filter | Many candidates, filter, dedupe, keep | Pure divergent→convergent |
| Tournament | N agents attempt differently, judges compare | Select best from multiple approaches |
| Loop-until-done | Keep spawning until stop condition | Explore until no new ideas |

### Superpowers plugin — structured skills approach

Installed in workspace at `~/.grok/installed-plugins/superpowers-21e2a56d/`. 14+ skills including:

| Skill | What it does | Our equivalent |
|---|---|---|
| brainstorming | Socratic design refinement before coding | None — /tp critiques, doesn't brainstorm |
| systematic-debugging | Structured debugging methodology | /aar (retrospective) |
| test-driven-development | TDD workflow | testing.md rule |
| writing-plans | Multi-step plan before code | /plan + /design |
| requesting-code-review | Trigger review workflow | /review |
| dispatching-parallel-agents | Fan-out independent tasks | /grok-parallel |

The brainstorming skill uses a SessionStart hook to ensure it fires before creative work. Our workspace lacks a pre-implementation ideation skill — /tp is post-hoc critique, not pre-implementation exploration.

Source: obra/superpowers GitHub, datacamp.com, blog.fsck.com

### /deep-research — bundled Claude Code workflow

Built-in workflow: fans out web searches across angles, fetches/cross-checks sources, votes on claims, returns cited report. Claims that don't survive cross-checking are filtered out.

Architecturally similar to our /www but runs as a background workflow (code-orchestrated, zero coordination tokens) vs /www (model-orchestrated pipeline).

### Codex (OpenAI) — adaptive thinking, no keyword triggers

Codex adapts thinking time dynamically based on task complexity. No ultrathink equivalent. Uses 93.7% fewer tokens on simple tasks. Closer to Claude's `adaptive` thinking mode (Opus 4.6+) than keyword-trigger approach.

### Grok Build gaps identified

| Claude Code feature | Our equivalent | Gap |
|---|---|---|
| ultrathink (per-turn) | reasoning_effort (session-level only) | No per-turn nudge |
| ultracode (code workflows) | /go (model-orchestrated) | Coordination costs model tokens |
| Dynamic workflows (JS scripts) | None | Major architectural gap |
| Superpowers brainstorming | /tp (critique, not ideation) | No pre-implementation ideation |
| /deep-research | /www (model-orchestrated) | Less scalable |
| Generate-and-filter pattern | Not implemented | Missing for brainstorming |

## Auto-related

- [[multi-agent-correlated-errors]]
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
