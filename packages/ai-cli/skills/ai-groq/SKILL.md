---
name: ai-groq
description: Groq API - Ultra-fast LLM inference with OpenAI SDK. Access to Llama, Mixtral, Gemma, and DeepSeek models with industry-leading speed.
version: "1.0.0"
status: stable
author: Claude Code
category: ai-service
tags:
  - ai
  - llm
  - groq
  - openai-sdk
  - streaming
  - fast-inference
progressive_disclosure:
  entry_point:
    summary: "Groq API - ultra-fast inference with LPU (Language Processing Units). Access Llama 3.3, Mixtral 8x7B, Gemma 2, and DeepSeek R1."
    when_to_use: "Real-time applications, low-latency requirements, fast prototyping, cost-effective inference"
    quick_start: |
      1. Set GROQ_API_KEY environment variable
      2. Use OpenAI SDK with base_url=https://api.groq.com/openai/v1
      3. POST to /v1/chat/completions
      4. Experience ultra-low latency
    critical_warning: |
      CRITICAL: Groq provides OpenAI-compatible API with specific model IDs.
      Model format: llama-3.3-70b-versatile, mixtral-8x7b-32768, gemma2-9b-it
      Speed: Up to 300+ tokens/second on LPUs
  context_limit: 500
requires_tools: []
---

# Groq API - Ultra-Fast LLM Inference

**CRITICAL**: Groq provides an OpenAI-compatible API with industry-leading speed. Switch providers via `base_url`.

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ["GROQ_API_KEY"]
)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

---

## Model Selection

| Model ID | Context | Best For | Speed |
|----------|---------|----------|-------|
| `llama-3.3-70b-versatile` | 128K | General purpose, reasoning | Fast |
| `llama-3.1-70b-versatile` | 128K | Balanced performance | Fast |
| `mixtral-8x7b-32768` | 32K | Multilingual, creative | Very Fast |
| `gemma2-9b-it` | 8K | Lightweight tasks | Ultra Fast |
| `deepseek-r1-distill-llama-70b` | 128K | Reasoning, math | Fast |
| `qwen-2.5-coder-32b-instruct` | 32K | Code generation | Fast |

---

## Health Check CLI

```bash
# Check API health
python -m .claude.skills.ai-groq.scripts.cli health

# Run with inference sanity check
python -m .claude.skills.ai-groq.scripts.cli health --sanity

# List provider status
python -m .claude.skills.ai-groq.scripts.cli list
```

**Exit codes:** `0` = healthy, `1` = failed

---

## Environment Variables

| Variable | Provider | Required |
|----------|----------|----------|
| `GROQ_API_KEY` | Groq | Required |

Get your free API key at: https://console.groq.com/

---

## Best Practices

1. **Model Selection**: Use Llama 3.3 for general tasks, Gemma 2 for ultra-fast responses
2. **Code Generation**: Use Qwen 2.5 Coder for code-related tasks
3. **Reasoning**: Use DeepSeek R1 Distill for complex reasoning
4. **Streaming**: Essential for real-time applications - Groq's speed shines here
5. **Cost**: Groq offers very competitive pricing with a generous free tier
6. **Speed**: Groq's LPU inference delivers 300+ tokens/second

---

## References

- **Code examples** (Python chat, TypeScript streaming, function calling, JSON mode, code review): See [references/code-examples.md](references/code-examples.md)
- **Pricing and advantages**: See [references/pricing-and-advantages.md](references/pricing-and-advantages.md)

## Resources

- [Groq Documentation](https://console.groq.com/docs)
- [API Reference](https://console.groq.com/docs/openai)
- [Groq Console](https://console.groq.com/)
- [Model Catalog](https://groq.com/models)
