# Quick Start Examples

Copy-paste snippets for common Chutes.ai interactions.

## Curl: Text Chat

```bash
curl -s https://llm.chutes.ai/v1/chat/completions \
  -H "Authorization: Bearer $CHUTES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "chutes/moonshotai/Kimi-K2.5-TEE",
    "messages": [
      {"role": "user", "content": "Explain quantum computing in one sentence."}
    ],
    "temperature": 0
  }'
```

## Python: Basic Chat (litellm)

```python
from litellm import completion
import os

response = completion(
    model="chutes/moonshotai/Kimi-K2.5-TEE",
    messages=[{"role": "user", "content": "Hello!"}],
    api_base="https://llm.chutes.ai/v1",
    api_key=os.environ.get("CHUTES_API_KEY")
)

print(response.choices[0].message.content)
```

## Python: Basic Chat (OpenAI SDK)

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
