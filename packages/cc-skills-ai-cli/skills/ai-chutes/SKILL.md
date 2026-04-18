---
name: ai-chutes
description: >
  Chutes.ai unified AI API - Access 100+ models through single interface with
  intelligent routing, streaming, multimodal support, and cost optimization.
  Use this skill when integrating Chutes, building multi-model applications,
  implementing streaming responses, or working with large context models.
version: "1.0.0"
status: stable
author: Claude Code
category: ai-service
tags:
  - ai
  - llm
  - chutes
  - streaming
  - multimodal
  - cost-optimization
  - multi-model
progressive_disclosure:
  entry_point:
    summary: "Unified AI gateway for 100+ models (Qwen, Kimi, MiniMax, Hermes) via litellm-compatible API"
    when_to_use: "Multi-model AI apps, cost-optimized inference, model fallbacks, streaming chat, large context (256K+)"
    quick_start: |
      1. Get API key at chutes.ai
      2. Use litellm SDK with base_url=https://llm.chutes.ai/v1
      3. POST to /v1/chat/completions
      4. Handle streaming responses
    critical_warning: |
      CRITICAL: Chutes exposes an OpenAI-compatible API (/chat/completions).
      Model IDs use chutes/{Provider}/{Model} format (e.g., chutes/moonshotai/Kimi-K2.5-TEE).
  context_limit: 713
requires_tools: []
---

# Chutes.ai - Unified AI API Gateway

**CRITICAL**: Model IDs use `chutes/{Provider}/{Model}` format.

```python
# litellm
from litellm import completion
response = completion(
    model="chutes/moonshotai/Kimi-K2.5-TEE",
    messages=[{"role": "user", "content": "Hello!"}],
    api_base="https://llm.chutes.ai/v1",
    api_key=os.environ["CHUTES_API_KEY"]
)

# OpenAI SDK
import openai
client = openai.OpenAI(
    base_url="https://llm.chutes.ai/v1",
    api_key=os.environ["CHUTES_API_KEY"]
)
```

---

## Quick Reference

### Popular Models

| Model ID | Context | Best For |
|----------|---------|----------|
| `chutes/moonshotai/Kimi-K2.5-TEE` | 256K | Large context, multimodal, agent swarms |
| `chutes/MiniMaxAI/MiniMax-M2.1-TEE` | 256K | SOTA coding (74% SWE-bench) |
| `chutes/Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8-TEE` | 32K | Code generation |
| `chutes/NousResearch/Hermes-4-70B-Lite-TE` | 8K | Fast reasoning |

### Free Models

- `chutes/moonshotai/Kimi-K2.5-TEE` - Free tier available
- `chutes/MiniMaxAI/MiniMax-M2.1-TEE` - Free tier available

### Rate Limits

| Model | Limit |
|-------|-------|
| Kimi K2 | 300,000 tokens/day (TPD) |
| MiniMax | Varies by tier |

---

## CLI Tools

```bash
# Health check (validates key, tests connectivity)
python -m .claude.skills.ai-chutes.scripts.cli health
python -m .claude.skills.ai-chutes.scripts.cli health --sanity  # with inference test

# List models (24-hour cache at ~/.claude/cache/ai-chutes/models.json)
python -m .claude.skills.ai-chutes.scripts.cli list
python -m .claude.skills.ai-chutes.scripts.cli list --refresh   # force refresh
python -m .claude.skills.ai-chutes.scripts.cli list --verbose   # detailed info

# Quota check
python -m .claude.skills.ai-chutes.scripts.cli quota
```

**Exit codes:** `0` = healthy, `1` = failed

---

## Best Practices

1. **Model Selection**: Use Kimi K2.5 for large context (256K), MiniMax for coding
2. **Cost Optimization**: Many Chutes models have free tiers - prioritize them
3. **Streaming**: Always use streaming for user-facing apps
4. **Error Handling**: Implement retry logic with exponential backoff
5. **Security**: Never expose API keys, use server-side proxies
6. **Model IDs**: Use exact `chutes/{Provider}/{Model}` format
7. **Context Windows**: Leverage 256K context for entire codebase analysis

---

## Differences from OpenRouter

| Feature | OpenRouter | Chutes |
|---------|------------|--------|
| Base URL | `https://openrouter.ai/api/v1` | `https://llm.chutes.ai/v1` |
| Model ID Format | `provider/model` | `chutes/{Provider}/{Model}` |
| SDK | OpenAI SDK | litellm or OpenAI SDK |
| Largest Context | 2M (Gemini) | 256K (Kimi K2.5) |
| Free Models | Many available | Many available |

---

## References

Detailed documentation is split into reference files:

| File | Contents |
|------|----------|
| `references/quick-start-examples.md` | Curl, Python (litellm/OpenAI SDK), TypeScript snippets |
| `references/api-patterns.md` | Streaming, multimodal, fallbacks, tool calling, cost optimization, rate limiting, production proxy |
| `references/model-catalog.md` | Full model list, selection strategy, context windows, free tiers |

## Resources

- [Chutes Documentation](https://chutes.ai/docs)
- [litellm Documentation](https://docs.litellm.ai/)
- [Model List](https://chutes.ai/models)
