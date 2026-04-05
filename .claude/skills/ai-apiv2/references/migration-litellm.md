# Migration from litellm

## Before (litellm)

```python
from litellm import completion

response = completion(
    model="chutes/moonshotai/Kimi-K2.5-TEE",
    messages=[{"role": "user", "content": "Hello"}],
    api_base="https://llm.chutes.ai/v1",
    api_key=os.environ["CHUTES_API_KEY"]
)
```

## After (OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://llm.chutes.ai/v1",
    api_key=os.environ["CHUTES_API_KEY"]
)
response = client.chat.completions.create(
    model="chutes/moonshotai/Kimi-K2.5-TEE",
    messages=[{"role": "user", "content": "Hello"}]
)
```

## Benefits

- Single dependency (`openai`) vs 50+ from litellm
- More explicit and debuggable
- Industry standard SDK
- All target providers are OpenAI-compatible anyway
