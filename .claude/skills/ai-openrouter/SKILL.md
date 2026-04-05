---
name: ai-openrouter
description: >
  OpenRouter unified AI API - Access 300+ models through single interface with
  intelligent routing, streaming, multimodal support, cost optimization, and
  production-ready patterns. Use this skill when integrating OpenRouter,
  building multi-model applications, implementing streaming responses, or
  working with image/PDF content.
version: "1.0.0"
status: stable
author: Ensemble (bobmatnyc + bnishit + ozbo1973 + fgarofalo56)
category: ai-service
tags:
  - ai
  - llm
  - openai-compatible
  - streaming
  - multimodal
  - cost-optimization
  - multi-model
progressive_disclosure:
  entry_point:
    summary: "Unified AI gateway for 300+ models (Claude, GPT-4, Gemini, Llama) via OpenAI-compatible API"
    when_to_use: "Multi-model AI apps, cost-optimized inference, model fallbacks, streaming chat, image/PDF processing"
    quick_start: |
      1. Get API key at openrouter.ai
      2. Use OpenAI SDK (NOT Anthropic SDK) with baseURL=https://openrouter.ai/api/v1
      3. POST to /api/v1/chat/completions
      4. Handle streaming responses
    critical_warning: |
      CRITICAL: OpenRouter exposes an OpenAI-compatible API (/chat/completions), NOT Anthropic-compatible (/messages).
      Use the `openai` SDK, never `@anthropic-ai/sdk`. The Anthropic SDK will result in 404 errors.
  context_limit: 713
requires_tools: []
---

# OpenRouter - Unified AI API Gateway

**CRITICAL**: Use OpenAI SDK, NOT Anthropic SDK. OpenRouter is OpenAI-compatible.

```typescript
// CORRECT
import OpenAI from 'openai'
const client = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: process.env.OPENROUTER_API_KEY
})

// WRONG - Will 404
import Anthropic from '@anthropic-ai/sdk'
```

---

## Quick Start

See `references/quick-start.md` for copy-paste snippets (curl, TypeScript, Python, streaming).

**Minimal TypeScript setup:**

```typescript
import OpenAI from 'openai'
const client = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: process.env.OPENROUTER_API_KEY,
  defaultHeaders: {
    'HTTP-Referer': 'https://your-app.com',
    'X-Title': 'Your App Name'
  }
})
const completion = await client.chat.completions.create({
  model: 'anthropic/claude-3.5-sonnet',
  messages: [{ role: 'user', content: 'Hello!' }]
})
```

---

## Model Selection Quick Reference

| Priority | Model | Use Case |
|----------|-------|----------|
| Quality | `anthropic/claude-3.5-sonnet` | Complex reasoning, code |
| Quality | `openai/gpt-4o` | General purpose, vision |
| Speed | `anthropic/claude-3-haiku` | Fast chat, classification |
| Speed | `google/gemini-flash-1.5` | Low-latency tasks |
| Cost | `meta-llama/llama-3.1-8b-instruct` | Budget inference ($0.06/1M) |
| Large context | `google/gemini-pro-1.5` | 2M token context window |
| Vision | `openai/gpt-4o` or `google/gemini-2.5-flash` | Image understanding |

See `references/model-selection.md` for model tiers and selector function.
See `references/model-discovery.md` for live catalog queries, free model filtering, and health check CLI.

---

## Topic Reference Index

| Topic | Reference File | Contents |
|-------|---------------|----------|
| Quick start snippets | `references/quick-start.md` | curl, TypeScript, Python, streaming basics |
| Model discovery | `references/model-discovery.md` | List/filter models, free models, health check CLI |
| Model selection | `references/model-selection.md` | Tiers (flagship/fast/budget), selector function |
| Streaming | `references/streaming-patterns.md` | TypeScript/Python streaming, React SSE component |
| Multimodal | `references/multimodal.md` | Image understanding, image generation, PDF processing |
| Cost optimization | `references/cost-optimization.md` | Token estimation, cost lookup, budget-constrained selection |
| Fallbacks & routing | `references/fallbacks-and-routing.md` | Fallback chains, provider routing |
| Tool calling | `references/tool-calling.md` | Basic tools, multi-step loops |
| Rate limiting | `references/rate-limiting.md` | Rate-limited client, exponential backoff |
| Production patterns | `references/production-patterns.md` | Server-side proxy, request/response logging |

---

## Common Pitfalls

| Problem | Fix |
|---------|-----|
| 404 from OpenRouter | Use `openai` SDK, not `@anthropic-ai/sdk`. Anthropic SDK POSTs to `/messages` |
| Model ID 404 | Use `provider/model` format (e.g. `openai/gpt-4o`). No `openrouter/` prefix |
| SSR hydration mismatch (Tiptap) | Add `immediatelyRender: false` to `useEditor` |
| API key exposed to client | Keep `OPENROUTER_API_KEY` server-side only (no `NEXT_PUBLIC_` prefix) |
| Stream never ends | Ensure `writer.close()` is in `finally` block |
| Two consecutive same-role messages | Always alternate user/assistant |
| Editor not clearing | Call `editor.commands.clearContent()` after send |

---

## Best Practices

1. **Model Selection**: Use fast models for simple tasks, flagship for complex reasoning
2. **Cost Optimization**: Estimate costs, use cheaper models when possible, cache responses
3. **Streaming**: Always use streaming for user-facing apps
4. **Error Handling**: Implement retry logic with exponential backoff, use model fallbacks
5. **Rate Limiting**: Use request queues and exponential backoff
6. **Security**: Never expose API keys, use server-side proxies
7. **Monitoring**: Track token usage, response times, and errors
8. **Discovery**: Query `/api/v1/models` for live catalog, don't hardcode

---

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [Model List](https://openrouter.ai/models)
- [API Reference](https://openrouter.ai/docs/api-reference)
- [Pricing](https://openrouter.ai/docs/pricing)

---

## Ensemble Credits

| Feature | Primary Source |
|---------|----------------|
| Progressive disclosure structure | bobmatnyc |
| Model discovery & multimodal | bnishit |
| React streaming + Tiptap | ozbo1973 |
| Concise quick reference | fgarofalo56 |
| Production playbooks | bnishit |
| Rate limiting class | bobmatnyc |
| SSE parsing helpers | bnishit |
