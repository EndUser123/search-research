# Good Models for Red-Team Review

Models considered high-quality for adversarial document/code review.
The /red-team command uses this list to interpret model requests.

Empirical rankings based on real test runs:
`~/.config/opencode/red-team-results.md`

## Harness summary

| Harness | What it is | Role |
|---------|-----------|------|
| **opencode** | The platform you're using now | Agent runtime — provides Bash/Read/Grep/Glob to ALL models it runs. This is how MiniMax-M3, Mistral, and GLM get file-access powers. |
| **agy** | Google Antigravity CLI | Separate agent runtime with its own tool loop. Free. Auto-selects model. |
| **mmx** | MiniMax CLI | API capability wrapper (text, search, vision, image, video, speech, music). Called BY agents, not a competing agent loop. Doesn't execute tool-call loops itself. Could be used WITHIN opencode as a complementary tool for MiniMax search/vision. |

## Fallback chains

If a primary reviewer fails (quota, auth, timeout), cascade to the next:

| Role | Primary | Fallback 1 | Fallback 2 |
|------|---------|------------|------------|
| Top-tier reasoning | minimax-coding-plan/MiniMax-M3 | zai-coding-plan/glm-5.2 | opencode/deepseek-v4-flash-free |
| General-purpose | mistral/mistral-medium-latest | opencode/deepseek-v4-flash-free | opencode/nemotron-3-ultra-free |
| Free/fast | opencode/deepseek-v4-flash-free | opencode/nemotron-3-ultra-free | opencode/hy3-free |
| External perspective | agy (auto-selects) | — | — |

## Tier 1: Default reviewers (always included, session model auto-skipped)

| Model ID | Provider | Harness | Risk profile | Notes |
|----------|----------|---------|---------------|-------|
| (agy auto-selects) | Google | agy CLI | Low risk — independent training data, catches blind spots | Free. Picks Gemini 3.5 Flash / Claude / GPT-OSS. Own agent loop. |
| minimax-coding-plan/MiniMax-M3 | MiniMax | opencode | Medium risk — strong SWE-bench, best for logic/code bugs | Strong reasoning. mmx CLI is a capability wrapper, not an agent loop. |
| mistral/mistral-medium-latest | Mistral | opencode | Low risk — independent model family, good for general review | Good general-purpose reviewer. |
| zai-coding-plan/glm-5.2 | ZAI | opencode | Medium risk — 1M context, strong code analysis, but same family as session model sometimes | Coding-plan tier. No official z.ai CLI. |

## Tier 2: OpenCode Go (paid subscription, $10/mo)

Requires `opencode providers login` with OpenCode Go API key.
When configured, models use the `opencode-go/<model-id>` prefix.
These are benchmarked, curated open coding models.

| Model ID | Risk profile | Notes |
|----------|---------------|-------|
| opencode-go/glm-5.2 | Top-tier reasoning | ZAI GLM-5.2 |
| opencode-go/glm-5.1 | Strong reasoning | ZAI GLM-5.1 |
| opencode-go/kimi-k2.7-code | High risk for code review — code-tuned, catches bugs others miss | Moonshot Kimi K2.7 |
| opencode-go/kimi-k2.6 | Medium risk | Moonshot Kimi K2.6 |
| opencode-go/mimo-v2.5 | Low cost, lower accuracy | MiMo V2.5 (cheapest) |
| opencode-go/mimo-v2.5-pro | Balanced | MiMo V2.5 Pro |
| opencode-go/minimax-m3 | Medium risk — strong SWE-bench | MiniMax M3 (Anthropic protocol) |
| opencode-go/minimax-m2.7 | Medium risk | MiniMax M2.7 |
| opencode-go/minimax-m2.5 | Lower risk | MiniMax M2.5 |
| opencode-go/qwen3.7-max | High cost, high accuracy | Qwen 3.7 Max (top tier) |
| opencode-go/qwen3.7-plus | Balanced | Qwen 3.7 Plus |
| opencode-go/qwen3.6-plus | Balanced | Qwen 3.6 Plus |
| opencode-go/deepseek-v4-pro | Strong reasoning | DeepSeek V4 Pro |
| opencode-go/deepseek-v4-flash | Low cost, fast | DeepSeek V4 Flash |

## Tier 3: OpenCode Zen free models (always free, no auth needed)

The `opencode/` prefix provides free access to popular models. No subscription
required. These are what we tested and verified work as agentic reviewers.

| Model ID | Risk profile | Notes |
|----------|---------------|-------|
| opencode/deepseek-v4-flash-free | Low risk — fast, decent accuracy for basic review | DeepSeek, fast |
| opencode/hy3-free | Unproven for logic — use for coverage, not authority | HY3, limited time free |
| opencode/mimo-v2.5-free | Unproven for logic — use for coverage, not authority | MiMo |
| opencode/nemotron-3-ultra-free | Unproven for logic — NVIDIA model, different training | NVIDIA Nemotron |
| opencode/north-mini-code-free | Code-focused but small — good for syntax, weak for architecture | North, code-focused |
| opencode/big-pickle | Mixed model — unpredictable | Default free model |

## Tier 4: Other strong models (add when requested by name)

| Model ID | Provider | Harness | Risk profile | Notes |
|----------|----------|---------|---------------|-------|
| github-copilot/claude-sonnet-5 | Anthropic | opencode | Lowest risk — top-tier reasoning, catches subtle bugs | Top-tier |
| github-copilot/claude-opus-4.8 | Anthropic | opencode | Lowest risk — strongest model available | Strongest, expensive |
| github-copilot/gpt-5.4 | OpenAI | opencode | Low risk — top-tier reasoning | OpenAI flagship |
| github-copilot/gemini-3.5-flash | Google | opencode | Low risk — fast, capable, independent training | Google model |
| minimax-coding-plan/MiniMax-M2.7 | MiniMax | opencode | Medium risk — previous gen | Still strong |
| zai-coding-plan/glm-5.2 | ZAI | opencode | Same as Tier 1 glm | Coding-plan tier |

## Tier 5: OpenRouter / HuggingFace alternatives (fallback if primary fails)

| Model ID | Provider | Notes |
|----------|----------|-------|
| openrouter/minimax/minimax-m3 | OpenRouter | MiniMax via OR |
| openrouter/mistralai/mistral-medium-3 | OpenRouter | Mistral via OR |
| openrouter/z-ai/glm-5.2 | OpenRouter | GLM via OR |
| huggingface/MiniMaxAI/MiniMax-M3 | HuggingFace | MiniMax via HF |

## Empirical test results

Real-world rankings based on standardized test runs against planted bugs:

**Test file:** `P:\.agents\skills\contract-status\test_review.py` (6 planted issues: SQL injection, missing return, missing import, division by zero, hardcoded path, no rounding)

**Results log:** `~/.config/opencode/red-team-results.md`

The results file tracks: date, model, pass/fail per issue, notes. Rankings
update as data accumulates. See the results file for current standings.

**Important:** The test file currently has planted-issue descriptions in comments
at the top. For real testing, reviewers see the answers. Consider creating a
clean version without the comment hints for blind testing.

## Aliases (what the user types → what it maps to)

The /red-team skill resolves these shortcuts:

| Alias | Maps to |
|-------|---------|
| minimax, m3 | minimax-coding-plan/MiniMax-M3 |
| mistral | mistral/mistral-medium-latest |
| glm, zai, glm-5.2 | zai-coding-plan/glm-5.2 |
| deepseek | opencode/deepseek-v4-flash-free |
| hy3 | opencode/hy3-free |
| mimo | opencode/mimo-v2.5-free |
| nemotron | opencode/nemotron-3-ultra-free |
| north | opencode/north-mini-code-free |
| free | All Tier 3 free models |
| go | All Tier 2 OpenCode Go models |
| strong | All Tier 4 models |
| all | Tier 1 + Tier 3 + Tier 4 (everything, excluding Go unless configured) |
| big-pickle, pickle | opencode/big-pickle |
