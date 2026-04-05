# Production Patterns

## Server-Side Proxy (Security)

**Never expose `OPENROUTER_API_KEY` to clients.**

```typescript
// app/api/chat/route.ts (Next.js)
import OpenAI from 'openai'

const client = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: process.env.OPENROUTER_API_KEY, // Server-side only
})

export async function POST(req: Request) {
  const { messages, model } = await req.json()

  const stream = await client.chat.completions.create({
    model: model || 'anthropic/claude-3.5-sonnet',
    messages,
    stream: true,
  })

  return new Response(
    new ReadableStream({
      async start(controller) {
        for await (const chunk of stream) {
          const text = chunk.choices[0]?.delta?.content || ''
          controller.enqueue(new TextEncoder().encode(text))
        }
        controller.close()
      },
    }),
    {
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    }
  )
}
```

## Request/Response Logging

```typescript
class LoggingClient {
  async chat(prompt: string, model: string) {
    const startTime = Date.now()

    console.log('[Request]', {
      timestamp: new Date().toISOString(),
      model,
      promptLength: prompt.length,
    })

    try {
      const completion = await client.chat.completions.create({
        model,
        messages: [{ role: 'user', content: prompt }],
      })

      const duration = Date.now() - startTime

      console.log('[Response]', {
        timestamp: new Date().toISOString(),
        duration,
        usage: completion.usage,
        finishReason: completion.choices[0].finish_reason,
      })

      return completion
    } catch (error) {
      console.error('[Error]', {
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        error,
      })
      throw error
    }
  }
}
```
