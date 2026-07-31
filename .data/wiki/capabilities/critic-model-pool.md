---
title: "critic-model-pool"
domain: model-pool
version: "1.0"
---
# critic-model-pool

## Inputs
- task_type: "code-review" | "adversarial-review" | "logic-check" | "assumption-test" | "tp-critique"

## Outputs
- model_slug: string
- fallback_chain: string[]

## Procedure

### /review (code review) — quota-aware parallel panel

For /review specialist fan-out, use these models in parallel. The operator
has high MiniMax quota and low /review frequency, so M3 is included despite
being subscription quota.

**Review panel (parallel dispatch):**
1. **or-ling-3-flash-free** — free, 5/5 code-exec, fast (2.2s)
2. **zen-deepseek-v4-flash-free** — free, different family (DeepSeek), Tau2 95.6
3. **nim-openai-gpt-oss-20b** — free, 13/13 reasoning, spawn-compatible
4. **minimax-m3** — subscription, high quota available, IFBench #1 for formatting/structured output

**Why these four:** three free-tier models (zero quota cost) plus M3 for
structured-output quality. The diversity across families (Ling, DeepSeek,
OpenAI-oss, MiniMax) catches different bug classes. Decomposition makes any
of them work — per-file or per-lens specialists, not one giant review.

**When to use fewer:** for `--lite` reviews, use or-ling-3-flash-free alone.
For single-file focused reviews, use zen-deepseek-v4-flash-free (strongest
reasoning of the free tier).

### /tp (critical-friend critique) — diversity-first

See reasoning-model-pool.md § "/tp" for the /tp-specific model selection.
The critic pool's role for /tp is to provide cross-model diversity, not
raw analytical power. Key principle: the critic must be from a DIFFERENT
model family than the work being reviewed.

**Cross-model CLI dispatch (for high-stakes critique):**
- /codex (GPT) + /agy (Gemini) in parallel — maximum family diversity
- These are separate from the review panel above

### Selection criteria
Critic tasks require both analytical quality and **model-family diversity**
(context-firewall principle). The critic must be from a different family
than the parent orchestrator (GLM-5.2/Zhipu). Constitutional AI research
(Springer 2026) confirms model behavior dominates prompting for sycophancy
reduction — a weaker-but-different model catches what a stronger-but-same
model misses.

## Review panel models (verified 2026-07-30, operator directive)
or-ling-3-flash-free (5/5 code-exec, $0/M, 2.2s — fast, free, spawn OK)
zen-deepseek-v4-flash-free (13/13 reasoning, $0, Tau2 95.6 — strongest free reasoning)
nim-openai-gpt-oss-20b (4/5 code-exec, 13/13 reasoning, free, spawn OK)
minimax-m3 (4/5 code-exec, 13/13 reasoning, IFBench #1 globally, subscription quota available)

## Cross-model review (separate from this pool)
For cross-model second opinions, use the CLI skills:
- /agy (Gemini/Antigravity) — different model family, different training data
- /codex (GPT-5.6 Luna) — different provider, verified passing
- /mmx (MiniMax CLI) — different API path, web search index access
These are NOT pool members. They are independent model families accessed
through CLI tools, providing genuine model diversity for review.

## Excluded
minimax-m3: agentic #97/129 (25th pct). Cannot sustain the multi-turn
  dialogue needed for adversarial review. Use for bounded formatting only.
groq-*: TPM cap blocks spawn_subagent.

## Selection criteria
Critic tasks require both analytical quality and instruction compliance.
Models must be able to sustain multi-turn dialogue (Tau2 proxy) and
follow complex review instructions (IFEval proxy). The critic must be
from a DIFFERENT model family than the work being reviewed when possible
(context-firewall principle, see [[context-firewall-architecture]]).

## Quality gate
Re-verify BenchLM coding and agentic ranks quarterly.
Re-run code-exec benchmark monthly for infrastructure validation.
