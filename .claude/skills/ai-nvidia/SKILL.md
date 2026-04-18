---
name: ai-nvidia
description: >
  NVIDIA NIM unified AI API - Access 200+ models through single interface with
  intelligent routing, streaming, multimodal support, and GPU-accelerated inference.
  Use this skill when integrating NVIDIA NIM, building multi-model applications,
  implementing streaming responses, or working with NVIDIA's hosted models.
version: "1.0.0"
status: stable
author: Claude Code
category: ai-service
tags:
  - ai
  - llm
  - nvidia
  - nim
  - streaming
  - multimodal
  - gpu
  - multi-model
progressive_disclosure:
  entry_point:
    summary: "Unified AI gateway for 200+ models (Llama, Nemotron, Gemma, Phi) via OpenAI-compatible API"
    when_to_use: "Multi-model AI apps, GPU-accelerated inference, model fallbacks, streaming chat, vision models"
    quick_start: |
      1. Get API key at build.nvidia.com
      2. Use OpenAI SDK with base_url=https://integrate.api.nvidia.com/v1
      3. POST to /v1/chat/completions
      4. Handle streaming responses
    critical_warning: |
      CRITICAL: NVIDIA NIM exposes an OpenAI-compatible API (/chat/completions).
      Model IDs use provider/model format (e.g., nvidia/llama-3.1-nemotron-70b-instruct).
  context_limit: 713
requires_tools: []
---

# NVIDIA NIM - Unified AI API Gateway

**CRITICAL**: Model IDs use `provider/model` format.

```python
import openai

client = openai.OpenAI(
  base_url="https://integrate.api.nvidia.com/v1",
  api_key=os.environ["NVIDIA_API_KEY"]
)

response = client.chat.completions.create(
    model="nvidia/llama-3.1-nemotron-70b-instruct",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

---

## Reference Files

| Topic | File | Contents |
|-------|------|----------|
| Quick Snippets | `references/quick-snippets.md` | Curl, Python, TypeScript copy-paste starters |
| Model Discovery | `references/model-discovery.md` | Popular models table, selection strategy, free tiers |
| Streaming & Multimodal | `references/streaming-multimodal.md` | Python/TS streaming, vision/image understanding |
| Production Patterns | `references/production-patterns.md` | Proxy setup, fallback chains, budget selection, rate limiting, tool calling, provider comparison |

---

## Popular Models (Quick Reference)

| Model ID | Context | Best For |
|----------|---------|----------|
| `nvidia/llama-3.1-nemotron-70b-instruct` | 128K | General purpose, high quality |
| `nvidia/nemotron-mini-4b-instruct` | 128K | Fast, low latency |
| `meta/llama-3.1-405b-instruct` | 128K | Large scale reasoning |

See `references/model-discovery.md` for full model catalog and selection strategy.

---

## Health Check CLI

```bash
# Check API health (validates key, tests connectivity)
python -m .claude.skills.ai-nvidia.scripts.cli health

# Run with inference sanity check
python -m .claude.skills.ai-nvidia.scripts.cli health --sanity
```

**Health checks:** API key presence, API connectivity, optional inference test.
**Exit codes:** `0` = healthy, `1` = failed

---

## Best Practices

1. **Model Selection**: Use Nemotron-70B for general purpose, Nemotron-mini for speed
2. **Cost Optimization**: Many NVIDIA models have free tiers - prioritize them
3. **Streaming**: Always use streaming for user-facing apps
4. **Error Handling**: Implement retry logic with exponential backoff
5. **Security**: Never expose API keys, use server-side proxies
6. **Model IDs**: Use exact `provider/model` format
7. **Context Windows**: Leverage 128K context for large document analysis

---

## Resources

- [NVIDIA NIM Documentation](https://docs.nvidia.com/ai-enterprise/nim-llm-api-intro.html)
- [Build NVIDIA Portal](https://build.nvidia.com/)
- [Model Catalog](https://build.nvidia.com/explore/discover#llm-models)
