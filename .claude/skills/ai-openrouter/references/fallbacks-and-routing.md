# Model Fallbacks & Provider Routing

## Fallback Chain

```typescript
const fallbackChain = [
  'anthropic/claude-3.5-sonnet',
  'openai/gpt-4o',
  'anthropic/claude-3-haiku',
  'google/gemini-flash-1.5',
]

async function chatWithFallback(prompt: string): Promise<string> {
  for (const model of fallbackChain) {
    try {
      console.log(`Trying: ${model}`)
      const completion = await client.chat.completions.create({
        model,
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 2000,
      })
      return completion.choices[0].message.content || ''
    } catch (error) {
      console.warn(`Model ${model} failed:`, error)
      if (model === fallbackChain[fallbackChain.length - 1]) {
        throw new Error('All models failed')
      }
    }
  }
  throw new Error('No models available')
}
```

## Provider Routing

```typescript
// Route to specific provider
await client.chat.completions.create({
  model: 'openai/gpt-4o', // Explicit provider
  messages: [{ role: 'user', content: 'Hello' }]
})

// Let OpenRouter choose with provider order
await client.chat.completions.create({
  model: 'gpt-4o',
  extra_body: {
    "provider": {
      "order": ["Azure", "OpenAI"],
      "allow_fallbacks": true
    }
  }
})
```
