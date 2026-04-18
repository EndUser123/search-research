# Quick Snippets - NVIDIA NIM

Copy-paste starter code for common operations.

## Curl: Text Chat

```bash
curl -s https://integrate.api.nvidia.com/v1/chat/completions \
  -H "Authorization: Bearer $NVIDIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nvidia/llama-3.1-nemotron-70b-instruct",
    "messages": [
      {"role": "user", "content": "Explain quantum computing in one sentence."}
    ],
    "temperature": 0
  }'
```

## Python: Basic Chat (OpenAI SDK)

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ.get("NVIDIA_API_KEY"),
)

response = client.chat.completions.create(
    model="nvidia/llama-3.1-nemotron-70b-instruct",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

## TypeScript: Basic Chat

```typescript
import OpenAI from 'openai'

const client = new OpenAI({
  baseURL: 'https://integrate.api.nvidia.com/v1',
  apiKey: process.env.NVIDIA_API_KEY
})

const completion = await client.chat.completions.create({
  model: 'nvidia/llama-3.1-nemotron-70b-instruct',
  messages: [{ role: 'user', content: 'Hello!' }]
})

console.log(completion.choices[0].message.content)
```

## TypeScript: Streaming

```typescript
const stream = await client.chat.completions.create({
  model: 'nvidia/llama-3.1-nemotron-70b-instruct',
  messages: [{ role: 'user', content: 'Tell me a story' }],
  stream: true
})

for await (const chunk of stream) {
  const content = chunk.choices[0]?.delta?.content || ''
  process.stdout.write(content)
}
```
