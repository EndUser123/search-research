---
name: ai-apiv2
description: >
  Multi-provider LLM API using OpenAI SDK - Unified access to Chutes, OpenRouter,
  NVIDIA NIM, Gemini, and z.ai through single OpenAI-compatible interface.
  Use this skill for code review, multi-model execution, streaming responses, and
  provider fallbacks.
version: "2.0.0"
status: stable
author: Claude Code
category: ai-service
tags:
  - ai
  - llm
  - multi-provider
  - openai-sdk
  - streaming
  - code-review
  - fallbacks
progressive_disclosure:
  entry_point:
    summary: "OpenAI SDK unified interface for 5 providers (Chutes, OpenRouter, NVIDIA, Gemini, z.ai)"
    when_to_use: "Multi-provider apps, code review, provider fallbacks, streaming chat, cost optimization"
    quick_start: |
      1. Set provider API keys (CHUTES_API_KEY, OPENROUTER_API_KEY, etc.)
      2. Use OpenAI SDK with provider-specific base_url
      3. POST to /v1/chat/completions
      4. Handle streaming responses
    critical_warning: |
      ⚠️ CRITICAL: All 5 providers expose OpenAI-compatible APIs.
      Model IDs vary by provider: chutes/{Provider}/{Model}, provider/model, glm-*.
  context_limit: 713
requires_tools: []
---

# Multi-Provider LLM API (OpenAI SDK)

**CRITICAL**: All providers use OpenAI-compatible `/v1/chat/completions`. Switch providers via `base_url`.

```python
from openai import OpenAI
client = OpenAI(base_url="https://llm.chutes.ai/v1", api_key=os.environ["CHUTES_API_KEY"])
response = client.chat.completions.create(model="chutes/moonshotai/Kimi-K2.5-TEE", messages=[...])
```

> Full code examples (Python basic chat, multi-provider fallback, TypeScript streaming): See `references/code-snippets.md`

---

## Provider Matrix

| Provider | Base URL | Model ID Format | Best For |
|----------|----------|-----------------|----------|
| **Chutes** | `https://llm.chutes.ai/v1` | `chutes/{Provider}/{Model}` | 256K context, SOTA coding |
| **OpenRouter** | `https://openrouter.ai/api/v1` | `provider/model` | 300+ models, routing |
| **NVIDIA NIM** | `https://integrate.api.nvidia.com/v1` | `provider/model` | GPU acceleration, 128K context |
| **Gemini** | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-*` | 2M context, fast |
| **z.ai** | `https://api.z.ai/api/coding/paas/v4` | `glm-*` | GLM-4.7, coding focus |

---

> Full model catalog per provider: See `references/provider-models.md`

---

## Patterns

> Streaming, code review, and cost optimization implementations: See `references/patterns.md`

---

## Health Check CLI

```bash
python -m .claude.skills.ai-apiv2.scripts.cli health          # all providers
python -m .claude.skills.ai-apiv2.scripts.cli health --sanity  # with inference test
```

> Full CLI reference (commands, flags, exit codes): See `references/health-check.md`

---

## Environment Variables

| Variable | Provider | Required |
|----------|----------|----------|
| `CHUTES_API_KEY` | Chutes | Optional |
| `OPENROUTER_API_KEY` | OpenRouter | Optional |
| `NVIDIA_API_KEY` | NVIDIA NIM | Optional |
| `GEMINI_API_KEY` | Gemini | Optional |
| `ZAI_API_KEY` | z.ai | Optional |

---

## Best Practices

1. **Provider Selection**: Use Chutes for 256K context, OpenRouter for model variety, NVIDIA for GPU acceleration
2. **Fallbacks**: Always implement provider fallback chains for reliability
3. **Streaming**: Use streaming for user-facing applications
4. **Cost Optimization**: Prioritize free tiers (Chutes, NVIDIA, Gemini Flash)
5. **Security**: Never expose API keys, use server-side proxies
6. **Model IDs**: Use exact provider-specific formats

---

## Migration from litellm

> Side-by-side migration guide (litellm to OpenAI SDK): See `references/migration-litellm.md`

---

## Resources

- [Chutes Documentation](https://chutes.ai/docs)
- [OpenRouter Documentation](https://openrouter.ai/docs)
- [NVIDIA NIM Documentation](https://docs.nvidia.com/ai-enterprise/nim-llm-api-intro.html)
- [Gemini API](https://ai.google.dev/gemini-api/docs)
- [z.ai Documentation](https://docs.z.ai)
