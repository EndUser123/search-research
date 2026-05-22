# Bifrost v1.5.2 Provider Configuration Backup

## Config File
`C:\Users\brsth\AppData\Roaming\bifrost\config.json`

## Providers (8 total)

### 1. Cerebras
| Field | Value |
|-------|-------|
| Type | Standard |
| API Key Env Var | `CEREBRAS_API_KEY` |
| Weight | 1 |
| Enabled | ON |
| Base URL | (default) |

### 2. Gemini
| Field | Value |
|-------|-------|
| Type | Standard |
| API Key Env Var | `GEMINI_API_KEY` |
| Weight | 1 |
| Enabled | ON |
| Base URL | (default) |

### 3. Groq
| Field | Value |
|-------|-------|
| Type | Standard |
| API Key Env Var | `GROQ_API_KEY` |
| Weight | 1 |
| Enabled | ON |
| Base URL | (default) |

### 4. Minimax (CUSTOM)
| Field | Value |
|-------|-------|
| Type | Custom |
| API Key Env Var | `MINIMAX_API_KEY` |
| Weight | 1 |
| Enabled | ON |
| Base URL | `https://api.minimax.io/anthropic` |
| Base Provider Type | Anthropic |
| Is Keyless | No |

**Allowed Request Types:** List Models, Chat Completion, Chat Completion Stream, Responses, Responses Stream, Count Tokens

### 5. Mistral AI
| Field | Value |
|-------|-------|
| Type | Standard |
| API Key Env Var | `MISTRAL_API_KEY` |
| Weight | 1 |
| Enabled | ON |
| Base URL | (default) |

### 6. Nvidia (CUSTOM)
| Field | Value |
|-------|-------|
| Type | Custom |
| API Key Env Var | `NVIDIA_API_KEY` |
| Weight | 1 |
| Enabled | ON |
| Base URL | `https://integrate.api.nvidia.com/` |
| Base Provider Type | OpenAI |
| Is Keyless | No |

**Allowed Request Types:** List Models, Text Completion, Text Completion Stream, Chat Completion, Chat Completion Stream, Responses, Responses Stream, Embedding, Speech

### 7. OpenRouter
| Field | Value |
|-------|-------|
| Type | Standard |
| API Key Env Var | `OPENROUTER_API_KEY` |
| Weight | 1 |
| Enabled | ON |
| Base URL | (default) |

### 8. Z.AI (CUSTOM)
| Field | Value |
|-------|-------|
| Type | Custom |
| API Key Env Var | `ZAI_API_KEY` |
| Weight | 1 |
| Enabled | ON |
| Base URL | `https://api.z.ai/api/coding` |
| Base Provider Type | OpenAI |
| Is Keyless | No |

**Allowed Request Types:** List Models, Text Completion, Text Completion Stream, Chat Completion, Chat Completion Stream, Responses, Responses Stream, Embedding, Speech

## Network Defaults (all providers)
| Setting | Value |
|---------|-------|
| Timeout | 30s |
| Stream Idle Timeout | 60s |
| Max Retries | 0 |
| Initial Backoff | 500ms |
| Max Backoff | 5000ms |
| Max Connections Per Host | 5000 |
| Enforce HTTP/2 | OFF |
| Skip TLS Verification | OFF |
| Extra Headers | none |
| CA Certificate | none |

## Routing Rules (governance block in config.json)

### M27 → Minimax/MiniMax-M2.7
```json
{
  "id": "route_m27",
  "name": "M27",
  "cel_expression": "model == \"MiniMax-M2.7\" || model == \"M27\"",
  "scope": "global",
  "priority": 40,
  "enabled": true,
  "targets": [{ "provider": "Minimax", "model": "MiniMax-M2.7", "weight": 1.0 }]
}
```

### GLM-5.1 → Nvidia/z-ai/glm-5.1
```json
{
  "id": "route_glm_5_1",
  "name": "GLM-5.1",
  "cel_expression": "model == \"GLM-5.1\"",
  "scope": "global",
  "priority": 80,
  "enabled": true,
  "targets": [{ "provider": "Nvidia", "model": "z-ai/glm-5.1", "weight": 1.0 }]
}
```

### GLM-4.7 → cerebras/zai-glm-4.7
```json
{
  "id": "870145ee-9bd6-42d0-8b79-b462e6bbcb69",
  "name": "GLM-4.7",
  "cel_expression": "model == \"glm-4.7\"",
  "scope": "global",
  "priority": 81,
  "enabled": true,
  "targets": [{ "provider": "cerebras", "model": "zai-glm-4.7", "weight": 1.0 }]
}
```

### Groq-GPT-OSS-120b → groq/openai/gpt-oss-120b
```json
{
  "id": "32c518fe-afa6-4a1e-814a-27003ab03c3b",
  "name": "Groq-GPT-OSS-120b",
  "cel_expression": "model == \"Groq-GPT-OSS-120b\"",
  "scope": "global",
  "priority": 30,
  "enabled": true,
  "targets": [{ "provider": "groq", "model": "openai/gpt-oss-120b", "weight": 1.0 }]
}
```

## Catalog Provider Names (exact spelling required)
Bifrost catalog uses these exact provider names — mismatches cause routing failures:

| Provider | Catalog ID |
|----------|------------|
| Cerebras | `cerebras` |
| Gemini | `gemini` |
| Groq | `groq` |
| Minimax | `Minimax` (capital M) |
| Mistral | `mistral` |
| Nvidia | `Nvidia` |
| OpenRouter | `openrouter` |

**Note:** `minimax` (lowercase), `z.ai`, and `z-ai` are NOT valid catalog provider names in v1.5.2. Use `Minimax` for MiniMax provider.