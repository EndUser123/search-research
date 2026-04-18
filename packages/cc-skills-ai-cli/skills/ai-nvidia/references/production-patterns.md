# Production Patterns - NVIDIA NIM

## Server-Side Proxy (Security)

**Never expose `NVIDIA_API_KEY` to clients.**

```python
# app/api/chat/route.py (FastAPI)
from fastapi import Request
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ["NVIDIA_API_KEY"],  # Server-side only
)

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    messages = data.get("messages", [])

    stream = client.chat.completions.create(
        model="nvidia/llama-3.1-nemotron-70b-instruct",
        messages=messages,
        stream=True,
    )

    return StreamingResponse(
        stream_response(stream),
        media_type="text/plain"
    )

async def stream_response(response):
    for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

## Model Fallback Chain

```python
fallback_chain = [
    'nvidia/llama-3.1-nemotron-70b-instruct',
    'nvidia/llama-3.3-nemotron-super-49b-v1.5',
    'nvidia/nemotron-mini-4b-instruct',
    'meta/llama-3.1-405b-instruct',
]

def chat_with_fallback(prompt: str):
    for model in fallback_chain:
        try:
            print(f"Trying: {model}")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        except Exception as error:
            print(f"Model {model} failed: {error}")
            continue

    raise Exception('All models failed')
```

## Budget-Constrained Selection

```python
def budget_chat(prompt: str, max_tokens=1000):
    # Try free models first
    free_models = [
        "nvidia/llama-3.1-nemotron-70b-instruct",
        "nvidia/nemotron-mini-4b-instruct",
        "microsoft/phi-3-mini-4k-instruct",
    ]

    for model in free_models:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Model {model} failed: {e}")
            continue

    raise Exception('No model fits budget')
```

## Rate Limiting with Exponential Backoff

NVIDIA NIM rate limits are based on:
- API tier (free vs. paid)
- Model type
- Request frequency

```python
import time

def retry_with_backoff(fn, max_retries=5):
    last_error = None

    for i in range(max_retries):
        try:
            return fn()
        except Exception as error:
            last_error = error

            if "429" in str(error) or "rate limit" in str(error).lower():
                delay = 2 ** i
                print(f"Rate limited. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise error

    raise last_error
```

## Tool Calling

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
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["city"]
        }
    }
}]

response = client.chat.completions.create(
    model="nvidia/llama-3.1-nemotron-70b-instruct",
    messages=[{"role": "user", "content": "Weather in Tokyo?"}],
    tools=tools,
    tool_choice="auto",
)

if response.choices[0].message.tool_calls:
    for call in response.choices[0].message.tool_calls:
        args = json.loads(call.function.arguments)
        # Execute tool and send result back
```

## Provider Comparison

| Feature | OpenRouter | Chutes | NVIDIA NIM |
|---------|------------|--------|------------|
| Base URL | `https://openrouter.ai/api/v1` | `https://llm.chutes.ai/v1` | `https://integrate.api.nvidia.com/v1` |
| Model ID Format | `provider/model` | `chutes/{Provider}/{Model}` | `provider/model` |
| SDK | OpenAI SDK | litellm or OpenAI SDK | OpenAI SDK |
| Context | Up to 2M | Up to 256K | Up to 128K |
| GPU Access | No | No | Yes (NVIDIA hardware) |
