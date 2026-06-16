# ai-api Handoff

Date: 2026-06-15

## Objective

Make `cc-skills-ai-api` better in two ways:

1. Improve the quality and trustworthiness of model rankings.
2. Reduce maintenance cost without removing useful behavior.

## Read First

Read these in order:

1. [P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\SKILL.md](P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\SKILL.md)
2. [P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\prompt_policy.py](P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\prompt_policy.py)
3. [P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\routing.py](P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\routing.py)
4. [P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\capabilities.py](P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\capabilities.py)
5. [P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\bf_agent.py](P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\bf_agent.py)
6. [P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_bf_agent.py](P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_bf_agent.py)
7. [P:\.data\ai-api\domain-model-weights.json](P:\.data\ai-api\domain-model-weights.json)
8. [P:\.data\ai-api\benchmarks\](P:\.data\ai-api\benchmarks\)

Why this order:
- `SKILL.md` explains the intended behavior.
- `prompt_policy.py` shows the current domain and alias contract.
- `routing.py` owns per-domain ranking order and persistence.
- `capabilities.py` owns the durable model capability profile and workspace-aware artifact root.
- `bf_agent.py` is the runtime source of truth.
- `test_bf_agent.py` shows the invariants that must not break.
- The `.data/ai-api` artifacts show the current rankings.

## Current State

Already in place:
- Plugin-owned runtime. `tools/mcp/bf_agent.py` is gone.
- Mode-first prompt contracts.
- Tight vs loose prompt handling.
- Source-packet review behavior.
- Critic + local deterministic validation for review-like compare runs.
- `/ai-cli` task aliases normalized into native `ai-api` domains.
- `run_code_agent()` carries the original request forward across turns.
- Per-domain benchmark registry under `.data/ai-api`.

Useful and should stay:
- Grounded claim verification in `_run_skeptic_check_on_claim()`.
- Local validation. Do not add a second LLM just to validate claims.
- The benchmark registry and artifacts as the source of truth.
- The `/ai-cli` alias bridge.

Experimental or optional:
- Epistemic routing.
- Iterative refinement in synthesis.
- Durable competency memory (`model_capabilities.json` and the advisory `model_competence_memory.md`).

## Current Ranking Snapshot

Use this as the fast answer for "what models are good for what domain" before opening the raw JSON.

### Code
- `mistral-medium-latest` - `0.975` - `13` samples
- `glm-5.1` - `0.9237` - `8` samples
- `openrouter/inclusionai/ling-2.6-1t` - `0.8973` - `13` samples
- `moonshotai/kimi-k2.6` - `0.7527` - `11` samples
- `nvidia/nemotron-3-super-120b-a12b` - `0.5131` - `13` samples

### Architecture
- `glm-5.1` - `0.9856` - `8` samples
- `openrouter/inclusionai/ling-2.6-1t` - `0.9731` - `13` samples
- `mistral-medium-latest` - `0.9554` - `13` samples
- `qwen/qwen3-coder-480b-a35b-instruct` - `0.5246` - `13` samples
- `qwen/qwen3.5-397b-a17b` - `0.49` - `13` samples

### Planning
- `openrouter/inclusionai/ling-2.6-1t` - `1.0` - `15` samples
- `mistral-medium-latest` - `1.0` - `15` samples
- `glm-5.1` - `0.9844` - `8` samples
- `qwen/qwen3.5-397b-a17b` - `0.6` - `15` samples
- `qwen/qwen3-coder-480b-a35b-instruct` - `0.463` - `15` samples

### Quick read
- Best code reviewer right now: `mistral-medium-latest`
- Best architecture reviewer right now: `glm-5.1`
- Best planning reviewer right now: tie between `openrouter/inclusionai/ling-2.6-1t` and `mistral-medium-latest`

## Verification Recipe

If you change benchmarks or ranking logic, verify with:

`python -m pytest P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_bf_agent.py -q`

For benchmark refreshes, use the canonical harness entrypoint:
- `P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\scripts\run_model_eval_suite.py`
- or the `run_model_eval_suite(...)` runtime path documented in [SKILL.md](P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\SKILL.md)

If you refresh benchmarks, check:
- `P:\.data\ai-api\domain-model-weights.json`
- `P:\.data\ai-api\benchmarks\`

If you change prompt policy, check:
- `P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\prompt_policy.py`
- `P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\SKILL.md`

## Happy Path Goal

If time is limited, the best-value path is:

1. Make the benchmark data better.
2. Publish a short human-readable model guide.
3. Decide whether the experimental knobs stay core.
4. Only then continue refactoring `bf_agent.py`.

That order matters:
- Better data first.
- Better summary second.
- Code cleanup after the data is trustworthy.

## What Success Looks Like

The handoff is successful if the next LLM can do all of these without re-deriving the project:

1. Read the current benchmark registry and explain which models are best for each domain.
2. Produce a short markdown model guide that a human can use immediately.
3. Say which features are experimental and should stay opt-in.
4. Name the next safe refactor boundaries in `bf_agent.py`.
5. Explain which ideas from ECC / llm-router / NadirClaw / ruflo are worth borrowing and which are not.
6. Keep the plugin-owned architecture intact.

## Highest-Value Remaining Work

### 1. Refresh the benchmark suite

Why:
- The current rankings are useful, but still heuristic.
- More cases per domain will make the scores less sensitive to one odd prompt.

What to do:
- Add more cases per domain.
- Prefer held-out cases, not just prompt variants.
- Keep the cases discriminative between strong and merely adequate models.

Files:
- [P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\bf_agent.py](P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\bf_agent.py)
- [P:\.data\ai-api\benchmarks\](P:\.data\ai-api\benchmarks\)
- [P:\.data\ai-api\domain-model-weights.json](P:\.data\ai-api\domain-model-weights.json)

Done when:
- The registry is regenerated from the broader case set.
- The top rankings are stable enough that small prompt changes do not reshuffle them.

### 2. Produce a short human-readable model guide

Why:
- The JSON registry is machine-friendly, not handoff-friendly.
- A short markdown summary is the best artifact for another LLM or a human.

What to include:
- Best model by domain.
- Best model by job type.
- Short caveats / failure modes.

Recommended location:
- `P:\.data\ai-api\model-guide.md`

Done when:
- A reviewer can read the guide without opening the raw benchmark JSON.

### 3. Borrow useful ideas from other repos

Use these as idea sources, not as authority.

Borrow:
- **ECC** for cross-harness packaging, shared conventions, and security-first plugin layout.
  - [ECC](https://github.com/affaan-m/ecc)
  - [ECC CLAUDE.md](https://github.com/affaan-m/ECC/blob/main/CLAUDE.md)
- **llm-router** for prompt classification, cheapest-capable-first routing, fallback chains, and routing policy ideas.
  - [llm-router README](https://github.com/ypollak2/llm-router/blob/main/README.md)
- **NadirClaw** for proxy-based routing and simple-vs-complex prompt tiering.
  - [NadirClaw](https://github.com/NadirRouter/NadirClaw)
- **ruflo** for multi-agent orchestration and validation discipline.
  - [ruflo](https://github.com/ruvnet/ruflo)

Verify first:
- ECC patterns must not reintroduce a shared-runtime boundary.
- llm-router fallback logic must match our direct-vs-Bifrost behavior before copying policy.
- NadirClaw proxy routing must be worth the extra hop.
- ruflo memory/swarm claims should be treated as inspiration until implementation quality is confirmed.

Ignore for now:
- Broad cost-savings framing unless cost is the explicit goal.
- Claims that one router can optimize every domain equally.
- Big swarm / self-learning / memory claims until they improve `ai-api` in practice.

### 4. Decide whether experimental features stay core

Features to decide on:
- `BF_EPISTEMIC_ROUTING_ENABLED`
- `BF_ITERATIVE_REFINEMENT_ENABLED`
- `model_competence_memory.md`

Recommended default:
- Keep them opt-in or advisory unless they clearly improve outcomes.

Done when:
- The docs say exactly which knobs are experimental.
- The benchmark path does not depend on them being enabled.

### 5. Split `bf_agent.py` by responsibility

Why:
- The file still owns too many concerns.

Good extraction boundaries:
- Transport / provider resolution
- Prompt policy
- Review packet assembly
- Compare / validation / synthesis
- Benchmark logic
- Code-mode loop

Files to watch:
- [P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\bf_agent.py](P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\bf_agent.py)
- [P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\prompt_policy.py](P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\prompt_policy.py)

Done when:
- Behavior stays the same.
- Tests still pass.
- The large file is smaller because responsibilities moved, not because features were cut.

## What Not To Do

- Do not rewrite the whole plugin.
- Do not expand the domain taxonomy just to make the table look richer.
- Do not treat `model_capabilities.json`, `model_competence_memory.md`, or any synthesis memory file as the sole source of truth; the benchmark registry remains authoritative.
- Do not remove functionality just to shrink file count.
- Do not add another LLM validation pass.
- Do not rely on the ranking snapshot alone; always check the underlying registry after benchmark refreshes.

## Open Questions

- Should `model_competence_memory.md` be kept as an advisory artifact, or retired entirely?
- Should `model_capabilities.json` remain the durable memory store for competence data, or should the benchmark registry alone carry that responsibility?
- Should `BF_EPISTEMIC_ROUTING_ENABLED` stay in the runtime at all, or move to a separate experimental branch?
- Should iterative refinement stay enabled by default, or be opt-in?
- Should the benchmark suite grow to include more held-out cases before any more refactors?

## Expected Deliverable From The Next LLM

The next LLM should return:

1. The refreshed benchmark data or a plan to get it.
2. A short markdown model guide.
3. A decision on experimental features.
4. A concrete refactor plan for `bf_agent.py`.
5. A short borrow/verify/ignore note for the external repos above.
6. A note on whether `routing.py` and `capabilities.py` should be treated as core read-first files for ranking work.

## Suggested Next Prompt

Improve `cc-skills-ai-api` in a no-loss way. First refresh the benchmark suite and regenerate the per-domain registry. Then write a short human-readable model guide. Then decide whether epistemic routing, iterative refinement, and competency memory should remain core or become clearly optional. After that, split `bf_agent.py` by responsibility without changing behavior.

When considering ideas from other repos, borrow only the routing, packaging, and orchestration patterns that fit `ai-api`. Verify them against the current plugin-owned architecture first, and ignore anything that would add another shared-runtime boundary or turn cost optimization into the main goal.

The canonical benchmark refresh entrypoint is `P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\scripts\run_model_eval_suite.py`, or the `run_model_eval_suite(...)` runtime path documented in [SKILL.md](P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\SKILL.md). Do not leave the next LLM guessing which path is authoritative.
