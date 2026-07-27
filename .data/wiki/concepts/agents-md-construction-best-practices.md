---
title: "AGENTS.md construction best practices — progressive disclosure, instruction budget, and the ball-of-mud anti-pattern"
created: 2026-07-27
source: session-019fa48a (/www research on AGENTS.md best practices)
tags: [agents-md, claude-md, context-engineering, progressive-disclosure, instruction-budget, best-practices, anti-patterns, agent-configuration]
summary: >
  Best practices for constructing AGENTS.md / CLAUDE.md files, grounded in three
  Tier-1 sources: HumanLayer's practical guide (instruction budget, progressive
  disclosure), AIHero's complete guide (ball-of-mud pattern, token economy), and
  ETH Zurich's empirical study (LLM-generated files degrade performance -3%,
  human-written files marginally help +4% but increase cost +19%). The core
  principle: AGENTS.md is the highest-leverage point in the harness — every line
  loads on every request, so it should contain only universally-applicable rules
  with wikilinks to rationale. Progressive disclosure (rule in AGENTS.md, detail
  in separate files loaded on demand) is the consensus pattern across all sources.
cognitive_load: 2
verification: multi-source-verified
host: both
agent: grok
sources:
  - "HumanLayer — Writing a good CLAUDE.md (Nov 2025)"
  - "AIHero — A Complete Guide To AGENTS.md (Jan 2026)"
  - "ETH Zurich / InfoQ — Evaluating AGENTS.md (Feb 2026, arxiv 2602.11988)"
  - "Anthropic — Effective context engineering for AI agents (Sep 2025)"
relations:
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: related
  - target: wiki/concepts/mandatory-step-enforcement-code-over-prose.md
    type: related
  - target: wiki/concepts/agent-config-directory-taxonomy.md
    type: extends
  - target: wiki/concepts/llm-instruction-non-compliance-activation-gap-2026.md
    type: related
---

# AGENTS.md construction best practices

## Decision context

**Why this research was needed:** the operator caught the model embedding
multi-paragraph rationale into AGENTS.md — the always-loaded context file.
The correction: "We shouldn't be using AGENTS.md to document why we are doing
something. If we want AGENTS.md to reference it, why not link to a wiki?" This
prompted research into whether community best practices support that layering
principle. They do — unanimously.

## The core principle: AGENTS.md is an instruction budget, not a knowledge base

AGENTS.md loads into **every single request**, regardless of task relevance.
This creates a hard budget problem (HumanLayer, AIHero):

- Frontier thinking LLMs follow ~150-200 instructions with reasonable consistency
  (arxiv 2507.11538). Smaller models attend to fewer.
- Claude Code's system prompt already contains ~50 instructions — that's a third
  of the budget before AGENTS.md loads.
- As instruction count increases, instruction-following quality decreases
  **uniformly** — the model doesn't ignore newer instructions specifically; it
  degrades on ALL of them.
- Every irrelevant instruction wastes tokens AND degrades attention to the
  instructions that matter.

**Implication:** the ideal AGENTS.md is as small as possible — ideally only
universally-applicable rules. HumanLayer's own AGENTS.md is <60 lines.
Community consensus: <300 lines for complex projects.

## Progressive disclosure (the consensus pattern)

All three sources recommend the same architecture:

| Layer | What it holds | When it loads |
|---|---|---|
| **AGENTS.md** | Rules only (what to do), one-liner project description, pointers | Every request |
| **Separate files / wiki** | Rationale (why), evidence, examples, domain detail | On demand — when the agent reads them |
| **Code** | Deterministic enforcement (linters, hooks, tests) | At execution time |

**Prefer pointers to copies.** Don't duplicate code snippets or file paths in
AGENTS.md — they go stale. Reference file:line or wikilinks instead.

**Nest progressively.** Root AGENTS.md → package-level AGENTS.md → docs/ files
→ wiki concepts. Each level loads only when relevant.

Anti-pattern (AIHero): the "ball of mud" — agent does X wrong → you add a rule →
repeat for months → file becomes unmaintainable and actively hurts performance.
This is the natural feedback loop; without active pruning, every AGENTS.md
becomes a ball of mud.

## The ETH Zurich disconfirmation: context files may hurt

A rigorous empirical study (Gloaguen et al., arxiv 2602.11988, Feb 2026) tested
AGENTS.md files across 138 real-world Python tasks with 4 agents:

| Context file type | Success rate change | Cost change |
|---|---|---|
| **None** (baseline) | — | — |
| **LLM-generated** | **-3%** (worse than nothing) | **+20%** |
| **Human-written** | **+4%** (marginal gain) | **+19%** |

Key finding: agents **follow** AGENTS.md instructions — which causes them to run
more tests, read more files, perform more checks. This "thinking harder" doesn't
produce better patches; it just costs more.

**Important caveat (HN community response):** the study used niche open-source
repos where domain knowledge is largely inferable. For proprietary codebases with
non-inferable domain knowledge (the operator's use case), the value of
human-written AGENTS.md is likely much higher than 4%. The developer response:
"If 4% gains are seen on [OSS] projects... then for bigger projects with
high-quality AGENTS.md's they're invaluable."

**What this means for us:** our AGENTS.md has domain knowledge the model cannot
infer (workspace topology, skill conventions, multi-agent coordination rules).
The ETH Zurich finding doesn't invalidate AGENTS.md for our use case — it
validates **minimizing** it. The marginal-gain finding means: every line we can
move out of AGENTS.md into progressive disclosure is a net win.

## Anti-patterns to avoid

| Anti-pattern | Why it hurts | Source |
|---|---|---|
| **Embedding rationale in AGENTS.md** | Burns tokens on every request for info only needed when the rule is questioned | Operator correction + all sources |
| **Auto-generating AGENTS.md** | Floods the file with "useful for most scenarios" content that's better progressively disclosed | AIHero, HumanLayer |
| **Code style guidelines in AGENTS.md** | LLMs are expensive, slow linters; use actual linters + Stop hooks instead | HumanLayer |
| **Documenting file paths** | Paths change; stale paths send the agent to wrong locations | AIHero |
| **"Hotfix" appending** | Adding a rule every time the agent does something wrong → ball of mud | AIHero |
| **LLM-generated context files** | Empirically degrade performance (-3%) vs no file at all | ETH Zurich |

## What this means for our workspace

Our `~/.grok/AGENTS.md` is the operator-level instruction file (loaded by Grok
Build on every session). It currently runs ~1000+ lines. By the instruction-budget
finding, this is well over the ~150-200 instruction ceiling. The model is already
degrading uniformly on all instructions.

**The progressive-disclosure refactor (not yet done, but validated by this
research):**
1. Keep in AGENTS.md: hard rules that apply to EVERY task (search before proposing,
   no destructive git, file-editing protocol, tool-selection preferences)
2. Move to wiki concepts: rationale, incident histories, evidence, examples
3. Replace rationale paragraphs with `[[wikilinks]]`
4. Move code-style guidelines to hooks/linters where possible
5. Prune "hotfix" rules that were added once and may no longer be load-bearing

**This is a large refactor** — not a single-session task. The principle is clear;
the execution requires per-section evaluation of what's universally applicable
vs. conditionally relevant.

## Falsifier

This concept is wrong if:
- The instruction-budget ceiling (~150-200) is wrong for current frontier models
  (models get better at long-context instruction following)
- Progressive disclosure causes MORE latency than it saves (agent spends more
  time reading wiki files than it would have spent processing inline rules)
- The ETH Zurich finding reverses on proprietary codebases (human-written AGENTS.md
  provides large gains, not marginal)

## Sources

- [HumanLayer — Writing a good CLAUDE.md](https://www.humanlayer.dev/blog/writing-a-good-claude-md) (Nov 2025) — instruction budget, progressive disclosure, <60-line own file
- [AIHero — A Complete Guide To AGENTS.md](https://www.aihero.dev/a-complete-guide-to-agents-md) (Jan 2026) — ball-of-mud pattern, token economy, monorepo nesting
- [ETH Zurich / InfoQ — Evaluating AGENTS.md](https://arxiv.org/abs/2602.11988) (Feb 2026) — empirical study: LLM-generated -3%, human-written +4%, both increase cost
- [Anthropic — Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (Sep 2025) — CLAUDE.md loaded naively; progressive disclosure via tools
- [[mechanical-enforcement-over-behavioral-reminder]] — the layering principle in practice (rules in AGENTS.md, rationale in wiki)
- [[mandatory-step-enforcement-code-over-prose]] — progression from prose rules to code enforcement
