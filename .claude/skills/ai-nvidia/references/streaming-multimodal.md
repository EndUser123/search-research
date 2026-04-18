# Streaming & Multimodal Patterns - NVIDIA NIM

## Python Streaming (OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ.get("NVIDIA_API_KEY"),
)

def stream_chat(prompt: str):
    stream = client.chat.completions.create(
        model="nvidia/llama-3.1-nemotron-70b-instruct",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print()
```

## TypeScript Streaming

```typescript
async function streamChat(prompt: string) {
  const stream = await client.chat.completions.create({
    model: 'nvidia/llama-3.1-nemotron-70b-instruct',
    messages: [{ role: 'user', content: prompt }],
    stream: true,
  })

  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content || ''
    process.stdout.write(content)
  }
}
```

## Image Understanding (Llama 3.2 Vision)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ.get("NVIDIA_API_KEY"),
)

response = client.chat.completions.create(
    model="meta/llama-3.2-90b-vision-instruct",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Extract all visible text from this image."},
            {
                "type": "image_url",
                "image_url": {"url": image_data_url},
            },
        ],
    }],
)
```
