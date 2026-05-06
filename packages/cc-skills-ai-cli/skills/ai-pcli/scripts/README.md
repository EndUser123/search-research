# sync_models.py

Syncs pi's `~/.pi/agent/models.json` with free models from multiple providers.

## Quick Start

```bash
# Sync all providers
python sync_models.py

# Preview what would change
python sync_models.py --dry-run

# Sync specific providers
python sync_models.py --cerebras --groq

# List currently configured models
python sync_models.py --list

# Show provider endpoints and key info
python sync_models.py --providers
```

## What It Does

| Action | Description |
|--------|-------------|
| **Fetch** | Queries each provider's `/v1/models` endpoint |
| **Add** | New models get added with sensible defaults |
| **Remove** | Models no longer in the API get removed |
| **Preserve** | User overrides (`name`, `compat`, `cost`) on existing models are kept |
| **Filter** | Models with <128K context or non-chat types are excluded |

## Providers

| Provider | Flag | What's synced | API format |
|----------|------|---------------|------------|
| OpenRouter | `--openrouter` | Free ($0) models + preserves manually-added paid models | OpenAI |
| NVIDIA NIM | `--nvidia` | All models (free API) | OpenAI |
| Cerebras | `--cerebras` | All models (free tier) | OpenAI |
| Groq | `--groq` | All models (free tier) | OpenAI |
| z.ai | `--zai` | GLM models (coding plan) | OpenAI |
| MiniMax | `--minimax` | All models (token plan) | Anthropic |

## API Key Resolution

Keys are resolved in order:
1. `~/.pi/agent/auth.json` (pi's built-in auth store)
2. Environment variable (e.g. `GROQ_API_KEY`)
3. Provider default (e.g. NVIDIA uses `"nvidia"`)

## Filters

- **Context window**: Models below 128K are excluded
- **Non-chat models**: whisper, tts, speech, guard, embed, tool-use, etc.
- **OpenRouter paid**: Manually-added paid models are preserved across syncs (as long as they meet the context minimum)

## Configuration

| File | Purpose |
|------|---------|
| `~/.pi/agent/models.json` | pi's model registry (read on `/model`, no restart needed) |
| `~/.pi/agent/auth.json` | API keys for providers |

No changes to `models.json` require a pi restart — just re-open `/model`.
