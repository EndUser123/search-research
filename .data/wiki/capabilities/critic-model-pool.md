# critic-model-pool

## Inputs
- task_type: "code-review" | "adversarial-review" | "logic-check" | "assumption-test" | "tp-critique"

## Outputs
- model_slug: string
- fallback_chain: string[]

## Procedure

1. Check pool health.
2. Select from tier-1 based on task subtype:
   - Code review: mistral-medium-latest (BenchLM coding #12, 91st pct)
   - Adversarial / logic check: glm-5-2 (Tau2 #1, knowledge #9)
   - Cross-model second opinion: use CLI skills (/agy, /codex, /mmx) — NOT from this pool
3. If tier-1 unavailable, fall to tier-2.

## Tier-1 (verified 2026-07-29)
### Code review lane
mistral-medium-latest (BenchLM coding #12/130 91st pct, 5/5 code-exec, spawn OK)
  - Use for: maintainability review, correctness check, structural analysis
nim-openai-gpt-oss-20b (BenchLM coding via provider, 13/13 reasoning, spawn OK)

### Adversarial / logic / assumption testing
glm-5-2 (Tau2 #1, knowledge #9, agentic #21)
  - Use for: assumption challenging, logic flaw detection, "could you be wrong" prompts
nvidia-nemotron-3-ultra (IFBench #2, 13/13 reasoning, 1M context)
  - Use for: large-context review, long-document analysis

## Tier-2 (fallback)
or-ling-3-flash-free (13/13, $0/M, 2.2s — fast but no public review benchmark data)
zen-deepseek-v4-flash-free (13/13, $0, spawn untested)
go-qwen3-7-max (IFEval 94.3%, 13/13, 19s)

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
