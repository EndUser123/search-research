# Good Models for Red-Team Review

Models considered high-quality for adversarial document/code review.
The /red-team command uses this list to interpret model requests.

## Harness summary

| Harness | What it is | Role |
|---------|-----------|------|
| **opencode** | The platform you're using now | Agent runtime — provides Bash/Read/Grep/Glob to ALL models it runs. This is how MiniMax-M3, Mistral, and GLM get file-access powers. |
| **agy** | Google Antigravity CLI | Separate agent runtime with its own tool loop. Free. Auto-selects model. |
| **mmx** | MiniMax CLI | API capability wrapper (text, search, vision, image, video, speech, music). Called BY agents, not a competing agent loop. Doesn't execute tool-call loops itself. Could be used WITHIN opencode as a complementary tool for MiniMax search/vision. |

## Tier 1: Default reviewers (always included, session model auto-skipped)

| Model ID | Provider | Harness | Notes |
|----------|----------|---------|-------|
| (agy auto-selects) | Google | agy CLI | Free. Picks Gemini 3.5 Flash / Claude / GPT-OSS. Own agent loop. |
| minimax-coding-plan/MiniMax-M3 | MiniMax | opencode | Strong reasoning. mmx CLI is a capability wrapper, not an agent loop. |
| mistral/mistral-medium-latest | Mistral | opencode | Good general-purpose reviewer |
| zai/glm-5.2 | ZAI | opencode | 1M context, strong code analysis. No official z.ai CLI. |

## Tier 2: OpenCode Go (paid subscription, $10/mo)

Requires `opencode providers login` with OpenCode Go API key.
When configured, models use the `opencode-go/<model-id>` prefix.
These are benchmarked, curated open coding models.

| Model ID | Notes |
|----------|-------|
| opencode-go/glm-5.2 | ZAI GLM-5.2 (top tier reasoning) |
| opencode-go/glm-5.1 | ZAI GLM-5.1 |
| opencode-go/kimi-k2.7-code | Moonshot Kimi K2.7 (code-tuned) |
| opencode-go/kimi-k2.6 | Moonshot Kimi K2.6 |
| opencode-go/mimo-v2.5 | MiMo V2.5 (cheapest) |
| opencode-go/mimo-v2.5-pro | MiMo V2.5 Pro |
| opencode-go/minimax-m3 | MiniMax M3 (Anthropic protocol) |
| opencode-go/minimax-m2.7 | MiniMax M2.7 (Anthropic protocol) |
| opencode-go/minimax-m2.5 | MiniMax M2.5 (Anthropic protocol) |
| opencode-go/qwen3.7-max | Qwen 3.7 Max (top tier, expensive) |
| opencode-go/qwen3.7-plus | Qwen 3.7 Plus |
| opencode-go/qwen3.6-plus | Qwen 3.6 Plus |
| opencode-go/deepseek-v4-pro | DeepSeek V4 Pro |
| opencode-go/deepseek-v4-flash | DeepSeek V4 Flash (cheap) |

## Tier 3: OpenCode Zen free models (always free, no auth needed)

The `opencode/` prefix provides free access to popular models. No subscription
required. These are what we tested and verified work as agentic reviewers.

| Model ID | Notes |
|----------|-------|
| opencode/deepseek-v4-flash-free | DeepSeek, fast |
| opencode/hy3-free | HY3, limited time free |
| opencode/mimo-v2.5-free | MiMo |
| opencode/nemotron-3-ultra-free | NVIDIA Nemotron |
| opencode/north-mini-code-free | North, code-focused |
| opencode/big-pickle | Default free model |

## Tier 4: Other strong models (add when requested by name)

| Model ID | Provider | Harness | Notes |
|----------|----------|---------|-------|
| github-copilot/claude-sonnet-5 | Anthropic | opencode | Top-tier reasoning |
| github-copilot/claude-opus-4.8 | Anthropic | opencode | Strongest, expensive |
| github-copilot/gpt-5.4 | OpenAI | opencode | Top-tier reasoning |
| github-copilot/gemini-3.5-flash | Google | opencode | Fast, capable |
| minimax-coding-plan/MiniMax-M2.7 | MiniMax | opencode | Previous gen, still strong |
| zai-coding-plan/glm-5.2 | ZAI | opencode | Coding-plan tier variant |

## Tier 5: OpenRouter / HuggingFace alternatives (fallback if primary fails)

| Model ID | Provider | Notes |
|----------|----------|-------|
| openrouter/minimax/minimax-m3 | OpenRouter | MiniMax via OR |
| openrouter/mistralai/mistral-medium-3 | OpenRouter | Mistral via OR |
| openrouter/z-ai/glm-5.2 | OpenRouter | GLM via OR |
| huggingface/MiniMaxAI/MiniMax-M3 | HuggingFace | MiniMax via HF |

## Aliases (what the user types → what it maps to)

The /red-team skill resolves these shortcuts:

| Alias | Maps to |
|-------|---------|
| minimax, m3 | minimax-coding-plan/MiniMax-M3 |
| mistral | mistral/mistral-medium-latest |
| glm, zai, glm-5.2 | zai/glm-5.2 |
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