# Groq API Code Examples

## Python: Basic Chat

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY"),
)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

## TypeScript: Streaming

```typescript
import OpenAI from 'openai'

const client = new OpenAI({
  baseURL: 'https://api.groq.com/openai/v1',
  apiKey: process.env.GROQ_API_KEY
})

const stream = await client.chat.completions.create({
  model: 'llama-3.3-70b-versatile',
  messages: [{ role: 'user', content: 'Tell me a story' }],
  stream: true
})

for await (const chunk of stream) {
  const content = chunk.choices[0]?.delta?.content || ''
  process.stdout.write(content)
}
```

## Python Streaming

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY"),
)

def stream_chat(prompt: str, model: str = "llama-3.3-70b-versatile"):
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

## Code Review Pattern

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY"),
)

def review_code(code: str):
    response = client.chat.completions.create(
        model="qwen-2.5-coder-32b-instruct",
        messages=[{
            "role": "user",
            "content": f"Review this code for bugs and best practices:\n\n{code}"
        }],
    )
    return response.choices[0].message.content
```

## Model Selector

```python
def select_groq_model(task: str, priority: str) -> str:
    if task == "code":
        return "qwen-2.5-coder-32b-instruct"
    if task == "reasoning":
        return "deepseek-r1-distill-llama-70b"
    if priority == "speed":
        return "gemma2-9b-it"
    if priority == "quality":
        return "llama-3.3-70b-versatile"
    return "llama-3.1-70b-versatile"
```

## JSON Mode (Structured Output)

```python
response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{
        "role": "user",
        "content": "Extract names from this text: John and Mary went to Paris."
    }],
    response_format={"type": "json_object"},
)

data = json.loads(response.choices[0].message.content)
```

## Function Calling

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
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Weather in Tokyo?"}],
    tools=tools,
)

if response.choices[0].message.tool_calls:
    for call in response.choices[0].message.tool_calls:
        args = json.loads(call.function.arguments)
        # Execute tool and send result back
```
