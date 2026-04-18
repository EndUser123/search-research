---
name: ai-mistral
description: Mistral AI API - OpenAI SDK compatible interface for Mistral's powerful LLMs including Mistral Large, Codestral, and more
version: "1.0.0"
status: stable
author: Claude Code
category: ai-service
tags:
  - ai
  - llm
  - mistral
  - openai-sdk
  - streaming
  - code-generation
progressive_disclosure:
  entry_point:
    summary: "Mistral AI API with OpenAI SDK - access to Mistral Large (128K context), Codestral (code-specialized), and Mistral Small"
    when_to_use: "European data residency, code generation, multilingual tasks, cost-effective inference"
    quick_start: |
      1. Set MISTRAL_API_KEY environment variable
      2. Use OpenAI SDK with base_url=https://api.mistral.ai/v1
      3. POST to /v1/chat/completions
      4. Handle streaming responses
    critical_warning: |
      CRITICAL: Mistral uses OpenAI-compatible API but has specific model IDs.
      Model format: mistral-large-latest, codestral-latest, mistral-small-latest
  context_limit: 500
requires_tools: []
---

# Mistral AI API (OpenAI SDK)

**CRITICAL**: Mistral provides an OpenAI-compatible API. Switch providers via `base_url`.

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://api.mistral.ai/v1",
    api_key=os.environ["MISTRAL_API_KEY"]
)

response = client.chat.completions.create(
    model="mistral-large-latest",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

---

## Model Selection

| Model ID | Context | Best For |
|----------|---------|----------|
| `mistral-large-latest` | 128K | Flagship, complex reasoning |
| `mistral-medium-latest` | 128K | Balanced performance |
| `mistral-small-latest` | 128K | Fast, cost-effective |
| `codestral-latest` | 32K | Code generation |
| `mistral-embed` | - | Embeddings |

---

## Health Check CLI

```bash
# Check API health
python -m .claude.skills.ai-mistral.scripts.cli health

# Run with inference sanity check
python -m .claude.skills.ai-mistral.scripts.cli health --sanity

# List provider status
python -m .claude.skills.ai-mistral.scripts.cli list
```

**Health checks:** API key presence, API connectivity to Mistral, optional inference test.

**Exit codes:** `0` = healthy, `1` = failed

---

## Environment Variables

| Variable | Provider | Required |
|----------|----------|----------|
| `MISTRAL_API_KEY` | Mistral AI | Required |

Get your API key at: https://console.mistral.ai/

---

## Best Practices

1. **Model Selection**: Use Mistral Large for complex tasks, Mistral Small for simple queries
2. **Code Generation**: Use Codestral for code-related tasks
3. **Cost Optimization**: Mistral Small is significantly cheaper for simple tasks
4. **Streaming**: Always use streaming for user-facing applications
5. **Security**: Never expose API keys, use server-side proxies
6. **European Data**: Mistral is EU-based, good for GDPR compliance

---

## Reference Files

- `references/code-patterns.md` -- Python/TypeScript code examples: streaming, function calling, JSON mode, multimodal, Codestral code review, model selector helper
- `references/api-reference.md` -- Pricing table and resource links (docs, API reference, console)
