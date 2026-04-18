# API Patterns

Detailed code examples for streaming, multimodal, fallbacks, tool calling, cost optimization, rate limiting, and production patterns.

## Streaming Patterns

### Python Streaming (litellm)

```python
from litellm import completion

def stream_chat(prompt: str, model: str = "chutes/moonshotai/Kimi-K2.5-TEE"):
    response = completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        api_base="https://llm.chutes.ai/v1",
    )

    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            full_response += content
            print(content, end="", flush=True)

    print()
    return full_response
```

### Python Streaming (OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://llm.chutes.ai/v1",
    api_key=os.environ.get("CHUTES_API_KEY"),
)

def stream_chat(prompt: str):
    stream = client.chat.completions.create(
        model="chutes/moonshotai/Kimi-K2.5-TEE",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print()
```

## Multimodal Support

### Image Understanding (Kimi K2.5)

```python
from litellm import completion

response = completion(
    model="chutes/moonshotai/Kimi-K2.5-TEE",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Extract all visible text from this image."},
            {"type": "image_url", "image_url": {"url": image_data_url}},
        ],
    }],
    api_base="https://llm.chutes.ai/v1",
)
```

## Model Fallbacks

### Fallback Chain

```python
fallback_chain = [
    'chutes/moonshotai/Kimi-K2.5-TEE',    # 256K context
    'chutes/MiniMaxAI/MiniMax-M2.1-TEE',  # SOTA coding
    'chutes/NousResearch/Hermes-4-70B-Lite-TE',  # Fast reasoning
]

def chat_with_fallback(prompt: str):
    for model in fallback_chain:
        try:
            print(f"Trying: {model}")
            response = completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                api_base="https://llm.chutes.ai/v1",
            )
            return response.choices[0].message.content
        except Exception as error:
            print(f"Model {model} failed: {error}")
            continue

    raise Exception('All models failed')
```

## Tool Calling

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
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["city"]
        }
    }
}]

response = completion(
    model="chutes/MiniMaxAI/MiniMax-M2.1-TEE",
    messages=[{"role": "user", "content": "Weather in Tokyo?"}],
    tools=tools,
    tool_choice="auto",
    api_base="https://llm.chutes.ai/v1",
)

if response.choices[0].message.tool_calls:
    for call in response.choices[0].message.tool_calls:
        args = json.loads(call.function.arguments)
        # Execute tool and send result back
```

## Cost Optimization

### Budget-Constrained Selection

```python
def budget_chat(prompt: str, max_cost=0.01):
    # Try free models first
    free_models = [
        "chutes/moonshotai/Kimi-K2.5-TEE",
        "chutes/MiniMaxAI/MiniMax-M2.1-TEE",
    ]

    for model in free_models:
        try:
            response = completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                api_base="https://llm.chutes.ai/v1",
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Model {model} failed: {e}")
            continue

    raise Exception('No model fits budget')
```

## Rate Limiting

### Exponential Backoff

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

## Production Patterns

### Server-Side Proxy (Security)

**Never expose `CHUTES_API_KEY` to clients.**

```python
# app/api/chat/route.py (FastAPI)
from fastapi import Request
from litellm import completion
import os

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    messages = data.get("messages", [])

    response = completion(
        model="chutes/moonshotai/Kimi-K2.5-TEE",
        messages=messages,
        stream=True,
        api_base="https://llm.chutes.ai/v1",
        api_key=os.environ["CHUTES_API_KEY"],  # Server-side only
    )

    return StreamingResponse(
        stream_response(response),
        media_type="text/plain"
    )

async def stream_response(response):
    for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```
