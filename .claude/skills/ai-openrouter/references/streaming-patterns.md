# Streaming Patterns

## TypeScript Streaming (Robust)

```typescript
async function robustStreamChat(prompt: string, model: string) {
  try {
    const stream = await client.chat.completions.create({
      model,
      messages: [{ role: 'user', content: prompt }],
      stream: true,
      max_tokens: 4000,
    })

    let fullResponse = ''

    for await (const chunk of stream) {
      const delta = chunk.choices[0]?.delta

      if (delta?.content) {
        fullResponse += delta.content
        process.stdout.write(delta.content)
      }

      if (chunk.choices[0]?.finish_reason) {
        console.log(`\n[Finished: ${chunk.choices[0].finish_reason}]`)
      }
    }

    return fullResponse
  } catch (error) {
    console.error('Streaming error:', error)
    throw error
  }
}
```

## Python Streaming

```python
def stream_chat(prompt: str, model: str = "anthropic/claude-3.5-sonnet"):
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )

    full_response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            full_response += content
            print(content, end="", flush=True)

    print()
    return full_response
```

## React Streaming Component

```tsx
'use client'

import { useState } from 'react'

export function StreamingChat() {
  const [response, setResponse] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)

  async function handleSubmit(prompt: string) {
    setIsStreaming(true)
    setResponse('')

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'anthropic/claude-3.5-sonnet',
          messages: [{ role: 'user', content: prompt }],
          stream: true,
        }),
      })

      const reader = res.body?.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader!.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n').filter(line => line.trim())

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') continue

            try {
              const parsed = JSON.parse(data)
              const content = parsed.choices[0]?.delta?.content || ''
              setResponse(prev => prev + content)
            } catch { }
          }
        }
      }
    } finally {
      setIsStreaming(false)
    }
  }

  return (
    <div>
      <textarea value={response} readOnly rows={20} />
      <button onClick={() => handleSubmit('Hello')}>
        {isStreaming ? 'Streaming...' : 'Send'}
      </button>
    </div>
  )
}
```
