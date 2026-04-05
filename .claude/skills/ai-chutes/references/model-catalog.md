# Model Catalog & Comparison

## Popular Models

| Model ID | Context | Best For |
|----------|---------|----------|
| `chutes/moonshotai/Kimi-K2.5-TEE` | 256K | Large context, multimodal, agent swarms |
| `chutes/MiniMaxAI/MiniMax-M2.1-TEE` | 256K | SOTA coding (74% SWE-bench) |
| `chutes/Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8-TEE` | 32K | Code generation |
| `chutes/NousResearch/Hermes-4-70B-Lite-TE` | 8K | Fast reasoning |

## Model Selection Strategy

```python
# Flagship (highest quality)
flagship = {
    "kimi": "chutes/moonshotai/Kimi-K2.5-TEE",  # 256K context
    "minimax": "chutes/MiniMaxAI/MiniMax-M2.1-TEE",  # 74% SWE-bench
    "hermes": "chutes/NousResearch/Hermes-4-70B-Lite-TE",
}

# Fast (low latency)
fast = {
    "hermes-lite": "chutes/NousResearch/Hermes-4-70B-Lite-TE",
    "qwen-coder": "chutes/Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8-TEE",  # pragma: allowlist secret
}

# Cost-optimized (many models are free on Chutes)
budget = {
    "kimi": "chutes/moonshotai/Kimi-K2.5-TEE",  # Free tier
    "minimax": "chutes/MiniMaxAI/MiniMax-M2.1-TEE",  # Free tier
}
```

## Context Window Limits

| Model | Context | Notes |
|-------|---------|-------|
| Kimi K2.5 TEE | 256K | Largest context, multimodal |
| MiniMax M2.1 TEE | 256K | SOTA coding, large files |
| Hermes 4 70B | 8K | Fast reasoning |
| Qwen3 Coder | 32K | Code generation |

## Large Context Usage (256K)

```python
from litellm import completion

# Kimi K2.5 supports 256K context - perfect for entire codebases
response = completion(
    model="chutes/moonshotai/Kimi-K2.5-TEE",
    messages=[{
        "role": "user",
        "content": "Analyze this entire project: " + entire_codebase  # Up to ~200K tokens
    }],
    api_base="https://llm.chutes.ai/v1",
)
```

## Free Models

- `chutes/moonshotai/Kimi-K2.5-TEE` - Free tier available
- `chutes/MiniMaxAI/MiniMax-M2.1-TEE` - Free tier available

## Rate Limits

| Model | Limit |
|-------|-------|
| Kimi K2 | 300,000 tokens/day (TPD) |
| MiniMax | Varies by tier |

## Differences from OpenRouter

| Feature | OpenRouter | Chutes |
|---------|------------|--------|
| Base URL | `https://openrouter.ai/api/v1` | `https://llm.chutes.ai/v1` |
| Model ID Format | `provider/model` | `chutes/{Provider}/{Model}` |
| SDK | OpenAI SDK | litellm or OpenAI SDK |
| Largest Context | 2M (Gemini) | 256K (Kimi K2.5) |
| Free Models | Many available | Many available |
