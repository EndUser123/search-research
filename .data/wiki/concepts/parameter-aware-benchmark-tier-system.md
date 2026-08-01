---
title: "Parameter-aware benchmark tier system: capability-gated testing per model"
created: 2026-07-28
source: session-2026-07-28
tags: [benchmark, tier-system, parameter-aware, capability-gating, strategy-pattern, gsm8k, humaneval, architecture-decision]
summary: >
  Replaced uniform benchmark tiers (every model tested identically) with a
  capability-gated matrix: universal tiers (mechanical, reasoning-base,
  code-exec, tool-calling) run for all models, while capability tiers
  (long-context, deep-reasoning, multimodal) run only for models that
  declare the relevant parameter. Each tier is a class implementing a common
  Tier protocol. The engine has zero tier-specific knowledge.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/model-fleet-provider-pools.md
    type: extends
  - target: wiki/concepts/groq-free-tier-tpm-limit-6000.md
    type: related
  - target: wiki/concepts/model-pool-not-chain.md
    type: related
---

# Parameter-aware benchmark tier system

## Decision context

The model-benchmark skill tested every model identically: same prompts, same
max_tokens, same scoring. This was structurally blind to the parameters that
differentiate models — context window (8K to 1M), reasoning capability (26
flagged vs 74 not), max_completion_tokens (2K to 65K). The benchmark couldn't
answer "which models write working code?" (it tested code description, not
execution) or "do 1M-context models work at depth?" (max prompt was 15K tokens).

The operator asked: "There's some huge differences in model parameters, and
our testing can't see the impact."

## The decision: capability-gated tier matrix

Chose a **Strategy pattern** with capability gating over three alternatives:

| Alternative | Rejected because |
|---|---|
| Uniform restructure (replace all tiers with parameter-scaled) | Breaks telemetry comparability; no gradual migration |
| Add-on tiers (keep old + add new) | Keeps broken tiers alongside new ones, doubling cost |
| Data-driven from config.toml (tiers defined in config) | Over-engineers config schema; tier logic is code, not data |

**Selection criterion:** signal density per API call (118 models; wasted calls
are expensive). Capability gating routes work to where it produces signal —
testing a 32K-context model on long-context retrieval wastes a call.

## Tier taxonomy

**Universal tiers** (every model, TPM-safe budgets < 6000):

| Tier | Tests | Scoring | Budget |
|------|-------|---------|--------|
| mechanical | Latency + reachability | Keyword match | 512 |
| reasoning-base | GSM8K math (5 problems) | Exact-match on parsed answer | 512/5000 |
| code-exec | HumanEval-style (5 problems) | Execution-based pass/fail in subprocess | 1024 |
| tool-calling | Function calling | Structural validation of tool_calls array | 512 |

**Capability-gated tiers** (`--deep` flag):

| Tier | Gate | Tests | Scoring | Budget |
|------|------|-------|---------|--------|
| long-context | `context_window > 32768` | Needle-in-haystack at 32K depth | Exact match on passkey | 128 |
| deep-reasoning | `reasoning = true` | Competition math (3 problems) | Exact-match after float normalization | min(capacity, 16384) |
| multimodal | `[T+I+]` tag | Image shape+color recognition | Keyword match | 512 |

## The Tier protocol (architectural decision)

Each tier is a class implementing:

```python
class Tier:
    name: str
    needs_tools: bool = False
    default_budget: int

    def build_prompt(self, model, problem_index=0) -> list[dict]: ...
    def score(self, content, problem_index=0, **kwargs) -> float: ...
    def get_budget(self, model) -> int: ...
    @property
    def num_problems(self) -> int: ...
```

The engine stores `TIERS = {"mechanical": MechanicalTier(), ...}` and calls
`TIERS[tier].build_prompt(model)` — **zero tier-specific branches**. Adding a
new tier requires only adding a class to `benchmark_tiers.py`. No engine changes.

**Steelman of rejected alternative (if/elif dispatch):** simpler to implement
initially, no class hierarchy overhead. But adding the 8th tier means editing
the dispatcher, the prompt builder, and the scoring function — three touch
points instead of one. The coupling is real (verified during refactor: the
pre-refactor engine had 3 `if tier ==` branches that the `/check` verifiers
found were missing context_window wiring).

**Falsifier:** if the Tier protocol adds complexity without reducing coupling
(i.e., the engine still needs special cases after the refactor), the pattern is
wrong. After the refactor (`a54eb80`), the engine has zero `if tier ==` branches.
The protocol reduced coupling as designed.

## Multi-problem iteration

Tiers with multiple problems (5 GSM8K, 5 HumanEval, 3 competition math) test
ALL problems and produce averaged quality scores. This changed quality scores
from single-shot (Q=0.0 or 1.0) to statistical (Q=0.0..1.0 across N problems).

**Behavior change:** existing telemetry comparisons across the pre/post boundary
are non-comparable. Single-problem scores before vs averaged scores after. This
is the intended improvement — a single correct/incorrect answer is not a
reliable capability signal.

## What this means for fleet routing

The benchmark can now answer questions the old one couldn't:

| Question | Old benchmark | New benchmark |
|---|---|---|
| Which models write working code? | Can't answer | code-exec: pass@1 per model |
| Do 1M-context models work at depth? | Can't answer | long-context: retrieval at 32K |
| Can reasoning models solve hard problems? | One riddle | deep-reasoning: competition math |
| Which models produce valid tool calls? | Not in defaults | tool-calling: structural validation |

This connects to [[model-fleet-provider-pools]] (the fleet inventory that
drives which models are tested), [[model-pool-not-chain]] (the pool philosophy
that makes provider diversity valuable), and [[groq-free-tier-tpm-limit-6000]]
(the rate-limit finding that motivated per-tier budgets). The multi-problem
pattern complements [[iterative-refinement-in-llm-code-generation]] (which
documents HumanEval pass@k methodology).

## Sources

- `/www` research session 2026-07-28: 3 parallel subagents on reasoning benchmarks,
  coding benchmarks, and expert features
- `/review` correctness specialist: 17 findings, 3 critical fixed
- `/refactor all`: Tier protocol + multi-problem + cleanup (commit `a54eb80`)
- `/check`: 50/50 tests pass, 3 integration bugs found and fixed

## Receipts

- `~/.grok/skills/model-benchmark/scripts/benchmark_tiers.py` — the Tier protocol,
  all tier implementations, problem sets, scoring functions, gating logic
- `~/.grok/skills/model-benchmark/scripts/benchmark.py` — the engine that calls
  `TIERS[tier].build_prompt()`, `TIERS[tier].score()`, `TIERS[tier].get_budget()`
- `~/.grok/skills/model-benchmark/tests/test_tier_budgets.py` — 50 tests covering
  budget scaling, TPM safety, override behavior, tier coverage
- Commit `f66c1b9`: initial parameter-aware tier system
- Commit `a54eb80`: Tier protocol refactor (zero engine special cases)
- Commit `c243392`: context_window parsing fix (found by `/check`)
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
