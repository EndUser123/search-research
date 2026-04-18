# Model Discovery - NVIDIA NIM

NVIDIA NIM provides access to 200+ models through the OpenAI-compatible API.

## Popular NVIDIA Models

| Model ID | Context | Best For |
|----------|---------|----------|
| `nvidia/llama-3.1-nemotron-70b-instruct` | 128K | General purpose, high quality |
| `nvidia/llama-3.3-nemotron-super-49b-v1.5` | 128K | Fast reasoning, efficiency |
| `nvidia/nemotron-4-340b-instruct` | 128K | SOTA performance |
| `nvidia/nemotron-mini-4b-instruct` | 128K | Fast, low latency |
| `meta/llama-3.1-405b-instruct` | 128K | Large scale reasoning |
| `google/gemma-3-27b-it` | 128K | Efficient general purpose |
| `microsoft/phi-3-mini-4k-instruct` | 128K | Fast, compact |

## Model Selection Strategy

```python
# Flagship (highest quality)
flagship = {
    "nemotron-70b": "nvidia/llama-3.1-nemotron-70b-instruct",
    "nemotron-super": "nvidia/llama-3.3-nemotron-super-49b-v1.5",
    "nemotron-340b": "nvidia/nemotron-4-340b-instruct",
}

# Fast (low latency)
fast = {
    "nemotron-mini": "nvidia/nemotron-mini-4b-instruct",
    "phi-3-mini": "microsoft/phi-3-mini-4k-instruct",
    "gemma-2-2b": "google/gemma-2-2b-it",
}

# Cost-optimized
budget = {
    "nemotron-mini": "nvidia/nemotron-mini-4b-instruct",
    "phi-3-mini": "microsoft/phi-3-mini-4k-instruct",
}
```

## Free Tier Models

- `nvidia/llama-3.1-nemotron-70b-instruct` - Free tier available
- `nvidia/nemotron-mini-4b-instruct` - Free tier available
- Many community models (Llama, Gemma, Phi) - Free tier available
