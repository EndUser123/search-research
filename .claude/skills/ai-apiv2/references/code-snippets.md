# Code Snippets

## Python: Basic Chat (Single Provider)

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://llm.chutes.ai/v1",
    api_key=os.environ.get("CHUTES_API_KEY"),
)

response = client.chat.completions.create(
    model="chutes/moonshotai/Kimi-K2.5-TEE",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

## Python: Multi-Provider with Fallback

```python
from openai import OpenAI
import os

PROVIDER_CHAIN = ["chutes", "openrouter", "nvidia", "gemini", "zai"]

PROVIDERS = {
    "chutes": {"base_url": "https://llm.chutes.ai/v1", "api_key": os.environ.get("CHUTES_API_KEY")},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "api_key": os.environ.get("OPENROUTER_API_KEY")},
    "nvidia": {"base_url": "https://integrate.api.nvidia.com/v1", "api_key": os.environ.get("NVIDIA_API_KEY")},
    "gemini": {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai/", "api_key": os.environ.get("GEMINI_API_KEY")},
    "zai": {"base_url": "https://api.z.ai/api/coding/paas/v4", "api_key": os.environ.get("ZAI_API_KEY")},
}

def chat_with_fallback(prompt: str, model: str) -> str:
    for provider in PROVIDER_CHAIN:
        config = PROVIDERS[provider]
        if not config["api_key"]:
            continue

        try:
            client = OpenAI(base_url=config["base_url"], api_key=config["api_key"])
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"{provider} failed: {e}")
            continue

    raise Exception("All providers failed")
```

## TypeScript: Streaming

```typescript
import OpenAI from 'openai'

const client = new OpenAI({
  baseURL: 'https://llm.chutes.ai/v1',
  apiKey: process.env.CHUTES_API_KEY
})

const stream = await client.chat.completions.create({
  model: 'chutes/moonshotai/Kimi-K2.5-TEE',
  messages: [{ role: 'user', content: 'Tell me a story' }],
  stream: true
})

for await (const chunk of stream) {
  const content = chunk.choices[0]?.delta?.content || ''
  process.stdout.write(content)
}
```
