# Bifrost v1.5.2 Provider Configuration

## Config File
`C:\Users\brsth\AppData\Roaming\bifrost\config.db` (SQLite database)
`C:\Users\brsth\AppData\Roaming\bifrost\config.json` (empty - governance in DB only)

## Providers (9 total)

### Key Working Providers

#### Z.AI (CUSTOM) - GLM Models
| Field | Value |
|-------|-------|
| Type | Custom |
| API Key Env Var | `ZAI_API_KEY` |
| Enabled | ON |
| Base URL | `https://api.z.ai/api/anthropic` |
| Base Provider Type | **Anthropic** |
| Timeout | 300s |

**Allowed Request Types:** List Models, Chat Completion, Chat Completion Stream, Responses, Responses Stream, Count Tokens

**Critical:** Z.AI uses Anthropic protocol at `/api/anthropic`, NOT OpenAI protocol at `/api/coding/paas/v4`

#### Minimax (CUSTOM) - M27/M2.7
| Field | Value |
|-------|-------|
| Type | Custom |
| API Key Env Var | `MINIMAX_API_KEY` |
| Enabled | ON |
| Base URL | `https://api.minimax.io/anthropic` |
| Base Provider Type | Anthropic |
| Timeout | 300s |

**Allowed Request Types:** List Models, Chat Completion, Chat Completion Stream, Responses, Responses Stream, Count Tokens

**Operational note:** Minimax has a 120s stream-idle timeout and 2 retries in the live Bifrost config. The prior 60s idle timeout was too short for some long-thinking `responses_stream` requests and showed up as `wsarecv`/`Error reading stream` failures.

#### Nvidia (CUSTOM)
| Field | Value |
|-------|-------|
| Type | Custom |
| API Key Env Var | `NVIDIA_API_KEY` |
| Enabled | ON |
| Base URL | `https://integrate.api.nvidia.com/` |
| Base Provider Type | OpenAI |
| Timeout | 30s |

**Allowed Request Types:** List Models, Chat Completion, Chat Completion Stream, Responses, Responses Stream, Count Tokens, Embedding

### Standard Providers (default configuration)
- Cerebras (`CEREBRAS_API_KEY`)
- Gemini (`GEMINI_API_KEY`)
- Groq (`GROQ_API_KEY`)
- Mistral AI (`MISTRAL_API_KEY`)
- OpenRouter (`OPENROUTER_API_KEY`)
- Huggingface

### OpenCode Go
- `OpenCodeGoOpenAI` for OpenAI-compatible Go models:
  - `glm-5.1`
  - `glm-5`
  - `kimi-k2.6`
  - `kimi-k2.5`
  - `deepseek-v4-pro`
  - `deepseek-v4-flash`
  - `mimo-v2.5`
  - `mimo-v2.5-pro`
- `OpenCodeGoAnthropic` for Anthropic-compatible Go models:
  - `minimax-m3`
  - `minimax-m2.7`
  - `minimax-m2.5`
  - `qwen3.7-plus`
  - `qwen3.6-plus`

Use `value: "env.OPENCODE_GO_API_KEY"` for the key so Bifrost resolves the subscription key from `P:\.env` at startup.
OpenCode Go also needs a browser-shaped `User-Agent` header to avoid Cloudflare `1010` blocks from this environment, so both providers include a static `extra_headers.User-Agent` entry.

Important for Claude Code: the `responses` path must use the Anthropic-compatible OpenCode Go routes. In this environment, `OpenCodeGoOpenAI/deepseek-v4-flash` and `OpenCodeGoOpenAI/deepseek-v4-pro` work for `chat/completions` but 404 on `responses`, while `OpenCodeGoAnthropic/qwen3.7-plus`, `OpenCodeGoAnthropic/deepseek-v4-flash`, and `OpenCodeGoAnthropic/deepseek-v4-pro` succeed on `responses`. DeepSeek Flash has returned `tools[0].function` deserialization failures on tool-heavy Claude Code requests, so Claude Code now enters through the local Bifrost tool shim at `http://localhost:3005/anthropic` before reaching Bifrost at `http://localhost:8080`. Keep non-DeepSeek fallbacks in DeepSeek chains until a full Claude Code tool-heavy replay passes consistently. Do not add `qwen3.7-max` back to Claude Code fallbacks unless explicitly requested.

### OpenCode Zen Free

`OpenCodeZenOpenAI` is separate from OpenCode Go:

- Base URL: `https://opencode.ai/zen`
- Base Provider Type: OpenAI
- Is Keyless: yes
- Active free routes:
  - `opencode-zen/mimo-v2.5-free` -> `OpenCodeZenOpenAI/mimo-v2.5-free`
  - `opencode-zen/nemotron-3-super-free` -> `OpenCodeZenOpenAI/nemotron-3-super-free`
  - `opencode-zen/nemotron-3-ultra-free` -> `OpenCodeZenOpenAI/nemotron-3-ultra-free`
  - `opencode-zen/big-pickle` -> `OpenCodeZenOpenAI/big-pickle`

Do not put these on `OpenCodeGoOpenAI` or `OpenCodeGoAnthropic`; the Go API key is rejected by `/zen/v1` for most free Zen models. Also do not add `minimax-m3-free` to active failover: direct `/zen/v1/chat/completions` probes return `Free promotion has ended for MiniMax M3 Free`.

### Claude Code Tool Shim

`P:\.claude\provider-configs\scripts\bifrost_tool_shim.js` is a zero-dependency Node.js sidecar managed by `cc-bifrost.ps1`.

- Listens on `127.0.0.1:3005`
- Forwards the original request path to `http://localhost:8080`
- Fills missing `tool.function.name` from top-level `tool.name` for OpenAI-shaped function tools
- Drops empty OpenAI function tool objects
- Downgrades forced object `tool_choice` values to `"auto"` only for configured DeepSeek route names
- Leaves native Anthropic `input_schema` tools unchanged
- Logs to `%APPDATA%\bifrost\tool-shim.log`

### Current Claude Tier Routing

The live Bifrost DB keeps automatic failover inside the 1M-context pool:

| Claude tier | CEL rule | Route |
|-------------|----------|-------|
| Haiku | `model == "claude-haiku-4-5" || model == "claude-haiku-4-5-20251001"` | `OpenCodeGoAnthropic/deepseek-v4-flash` with fallback to `qwen3.7-plus`, `OpenCodeZenOpenAI/mimo-v2.5-free`, `nemotron-3-super-free`, `nemotron-3-ultra-free`, `big-pickle`, then `z.ai/glm-5.1` |
| Sonnet | `model == "claude-sonnet-4-6"` | Same as Haiku |
| Opus | `model == "claude-opus-4-8"` | `Minimax/MiniMax-M3` with fallback to `OpenCodeGoAnthropic/qwen3.7-plus`, `OpenCodeZenOpenAI/mimo-v2.5-free`, `nemotron-3-super-free`, `nemotron-3-ultra-free`, `big-pickle`, then `z.ai/glm-5.1` |

If these routes change, keep the replacement models in the same 1M-context class so failover does not silently shrink the prompt window.

## Routing Rules (from database)

### GLM Models → z.ai
```json
{
  "cel_expression": "model == \"glm-5.1\"",
  "priority": 80,
  "targets": [{"provider": "z.ai", "model": "glm-5.1"}]
}
```
```json
{
  "cel_expression": "model == \"glm-4.7\"",
  "priority": 81,
  "targets": [{"provider": "z.ai", "model": "glm-4.7"}]
}
```

### M27 → Minimax
```json
{
  "cel_expression": "model == \"MiniMax-M2.7\" || model == \"M27\"",
  "priority": 40,
  "targets": [{"provider": "Minimax", "model": "MiniMax-M2.7"}]
}
```

## Verification

Test GLM through Bifrost:
```bash
curl -X POST "http://localhost:8080/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "x-vk: $env:BIFROST_VK" \
  -d '{"model":"glm-5.1","messages":[{"role":"user","content":"say ok"}],"max_tokens":10}'
```

## Backups

- **Database backup:** `P:\backups\bifrost_config_20260601.db`
- **Config JSON:** `P:\.claude\provider-configs\bifrost_config_20260601.json`

## Update History

- **2026-06-01:** Fixed z.ai provider to use Anthropic endpoint `/api/anthropic`. GLM models now working through Bifrost.
- **2026-06-06:** Raised Minimax stream idle timeout to 120s and retries to 2 after repeated `responses_stream` disconnects on `claude-sonnet-4-6`.
- **2026-06-08:** Kept the live `claude-sonnet-4-6` rule on `OpenCodeGoAnthropic/deepseek-v4-flash` but added `OpenCodeGoAnthropic/qwen3.7-plus` as the immediate fallback after DeepSeek returned tool-schema deserialization failures on `responses_stream` requests.
- **2026-06-08:** Moved the live `claude-haiku-4-5` rule from `OpenCodeGoAnthropic/deepseek-v4-flash` to `OpenCodeGoAnthropic/qwen3.7-plus` after verifying the exact Claude Code tool-heavy `responses` payload succeeds on Qwen Plus and fails on DeepSeek Flash.
- **2026-06-08:** Corrected the Opus fallback chain so the live `claude-opus-4-8` rule now falls back from `Minimax/MiniMax-M3` to `OpenCodeGoAnthropic/qwen3.7-plus` instead of the OpenAI `mimo-v2.5` route, which 404ed on `responses`.
- **2026-06-08:** Added a local Bifrost tool shim in front of Claude Code traffic to normalize DeepSeek-incompatible function-tool payloads before forwarding to Bifrost.
- **2026-06-08:** Updated the live `claude-haiku-4-5` rule to match Sonnet at the time; this older note was superseded later the same day when `qwen3.7-max` was removed from Claude Code fallbacks.
- **2026-06-08:** Added keyless `OpenCodeZenOpenAI` for free Zen models and inserted `mimo-v2.5-free`, `nemotron-3-super-free`, `nemotron-3-ultra-free`, and `big-pickle` into Haiku/Sonnet/Opus fallback chains before `z.ai/glm-5.1`. Verified logs show MiniMax/OpenCode Go 429s falling through to `OpenCodeZenOpenAI/mimo-v2.5-free`.
- **2026-06-08:** Removed `OpenCodeGoAnthropic/qwen3.7-max` and `openrouter/openrouter/owl-alpha` from Claude Code fallback chains by user preference. Do not add them back unless explicitly requested.
