# Mistral Code Patterns

Detailed code examples for common Mistral API tasks. See SKILL.md for quick start and model selection.

---

## Python: Basic Chat

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://api.mistral.ai/v1",
    api_key=os.environ.get("MISTRAL_API_KEY"),
)

response = client.chat.completions.create(
    model="mistral-large-latest",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

## TypeScript: Streaming

```typescript
import OpenAI from 'openai'

const client = new OpenAI({
  baseURL: 'https://api.mistral.ai/v1',
  apiKey: process.env.MISTRAL_API_KEY
})

const stream = await client.chat.completions.create({
  model: 'mistral-large-latest',
  messages: [{ role: 'user', content: 'Tell me a story' }],
  stream: true
})

for await (const chunk of stream) {
  const content = chunk.choices[0]?.delta?.content || ''
  process.stdout.write(content)
}
```

---

## Streaming Patterns

### Python Streaming

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.mistral.ai/v1",
    api_key=os.environ.get("MISTRAL_API_KEY"),
)

def stream_chat(prompt: str, model: str = "mistral-large-latest"):
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print()
```

---

## Code Generation with Codestral

### Code Review Pattern

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.mistral.ai/v1",
    api_key=os.environ.get("MISTRAL_API_KEY"),
)

def review_code(code: str):
    response = client.chat.completions.create(
        model="codestral-latest",
        messages=[{
            "role": "user",
            "content": f"Review this code for bugs and best practices:\n\n{code}"
        }],
    )
    return response.choices[0].message.content
```

---

## Multimodal Support

### Image Understanding (Mistral Large)

```python
response = client.chat.completions.create(
    model="mistral-large-latest",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Describe this image."},
            {"type": "image_url", "image_url": {"url": image_url}},
        ],
    }],
)
```

---

## Function Calling

### Basic Tools

```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get weather for a city",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
            },
            "required": ["city"]
        }
    }
}]

response = client.chat.completions.create(
    model="mistral-large-latest",
    messages=[{"role": "user", "content": "Weather in Paris?"}],
    tools=tools,
)

if response.choices[0].message.tool_calls:
    for call in response.choices[0].message.tool_calls:
        args = json.loads(call.function.arguments)
        # Execute tool and send result back
```

---

## JSON Mode

### Structured Output

```python
response = client.chat.completions.create(
    model="mistral-large-latest",
    messages=[{
        "role": "user",
        "content": "Extract names from this text: John and Mary went to Paris."
    }],
    response_format={"type": "json_object"},
)

data = json.loads(response.choices[0].message.content)
```

---

## Model Selector Helper

```python
def select_mistral_model(task: str, priority: str) -> str:
    if task == "code":
        return "codestral-latest"
    if priority == "quality":
        return "mistral-large-latest"
    if priority == "speed":
        return "mistral-small-latest"
    return "mistral-medium-latest"
```
