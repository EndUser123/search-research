# HANDOFF: Model benchmark overhaul, pool contracts, Codex OAuth bridge, skill wiring

## Status: OPEN — validation pending

## Objective

Overhaul the fleet model benchmark system, create pool contracts for model
selection by role, integrate GPT-5.6 via Codex OAuth bridge, and wire pool
contracts into all subagent-dispatching skills.

## What was done (this session)

### Benchmark overhaul
- Added 10 new deep-reasoning problems (total 13) to benchmark_tiers.py
- Fixed DeepReasoningTier budget cap (removed 16384 artificial limit)
- Fixed _extract_answer_float regex for comma-separated numbers
- Fixed --tier gating (bypass capability gate when tier explicitly set)
- Ran 13-problem sweep: 60 models, 780 calls, 718 OK
- Committed in ~/.grok repo

### Pool contracts (4 contracts)
- capabilities/coding-model-pool.md (updated: Ling 3.0 Flash added to tier-1)
- capabilities/reasoning-model-pool.md (NEW: GLM-5.2 primary, zen-deepseek backup)
- capabilities/mechanical-model-pool.md (NEW: speed-first)
- capabilities/critic-model-pool.md (NEW: code review + adversarial)
- All with YAML frontmatter for capabilities.py resolution

### Pool wiring (9 skills)
- Added consumes: declarations for pool contracts to /tp, /www, /debrief,
  /review, /aar, /refine, /handoff, /harvest, /why, /go
- Removed ALL hardcoded model slugs from skill text
- Verified: capabilities.py --for-skill resolves all pool names

### Codex OAuth bridge
- Installed PandelisZ/grok-bypass bridge at ~/.local/share/grok-codex-bridge/
- Bridge endpoint: http://127.0.0.1:11435/v1
- Codex endpoint: https://chatgpt.com/backend-api/codex/responses
- Added gpt-5-6-luna, gpt-5-6-terra, gpt-5-6-sol to config.toml
- Validated: Luna works as Grok parent model (grok -m gpt-5-6-luna PASS)
- Health check: ~/.grok/scripts/check-codex-bridge.ps1
- Token extractor: ~/.grok/scripts/get-openai-codex-token.ps1

### Wiki concepts (6 new, 2 updated)
- model-role-assignment-public-vs-custom-benchmarks.md
- openai-subscription-models-in-grok-build.md
- fleet-benchmark-results-2026-07-29.md (updated)
- model-benchmark-testing-quirks.md
- model-fleet-provider-pools.md (updated)
- coding-model-pool-tier-1-tier-2.md (updated)

### Public benchmark integration
- Decision: use public benchmarks (IFEval, IFBench, Tau2) for capability
  assessment; custom benchmark for infrastructure validation only
- GLM-5.2 confirmed as thought partner: Tau2 #1 (99.1), agentic #21
- M3 confirmed as bounded-task: IFBench #1, but agentic #97

## What needs validation

1. **Pool wiring in production:** run a real /debrief or /tp and confirm
   subagents dispatch from pool files, not hardcoded defaults
2. **Bridge under real load:** tested simple prompts, NOT tested with
   streaming, tool calling, long context, or multi-turn as parent
3. **Code-exec benchmark with 13 problems:** current 5-problem set is too
   easy to discriminate coding pool — IN PROGRESS this session

## What does NOT need a session start hook

The bridge runs independently in PowerShell. No hook needed — just run
`codex-bridge` before starting a Grok session that will use GPT-5.6 models.
The `check-codex-bridge.ps1` script is for manual verification only.

## Acceptance criteria

- [ ] One successful /debrief using pool-sourced models
- [ ] One successful Grok session running on GPT-5.6 Luna through bridge
      with tool calls and multi-turn dialogue
- [ ] Code-exec benchmark expanded to 13 problems and run

## Key files

| File | Repo | What |
|------|------|------|
| `skills/model-benchmark/scripts/benchmark_tiers.py` | ~/.grok | 13 problems, budget fix |
| `skills/model-benchmark/scripts/benchmark.py` | ~/.grok | --tier gating fix |
| `config.toml` | ~/.grok | GPT-5.6 entries, GLM-5.2 first |
| `capabilities/coding-model-pool.md` | P: | Ling 3.0 tier-1 |
| `capabilities/reasoning-model-pool.md` | P: | GLM-5.2 + Tau2 data |
| `capabilities/mechanical-model-pool.md` | P: | speed-first |
| `capabilities/critic-model-pool.md` | P: | review + adversarial |
| `scripts/check-codex-bridge.ps1` | ~/.grok | health check |
| `scripts/get-openai-codex-token.ps1` | ~/.grok | token extractor |
| `.local/share/grok-codex-bridge/` | ~/.grok | bridge scripts |
| `.local/bin/codex-bridge.bat` | ~/.grok | bridge launcher |

## Constraints for next session

- Do NOT modify config.toml model entries without operator approval
- Bridge depends on undocumented chatgpt.com/backend-api/codex endpoint
- Pool contracts are gitignored in capabilities/ — use git add -f
- Bridge must be running before GPT-5.6 models work (start with codex-bridge)
