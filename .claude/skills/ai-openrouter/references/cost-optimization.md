# Cost Optimization

## Token Counting & Estimation

```typescript
import { encoding_for_model } from 'tiktoken'

const modelPricing = {
  'anthropic/claude-3.5-sonnet': { input: 3.00, output: 15.00 },  // per 1M
  'anthropic/claude-3-haiku': { input: 0.25, output: 1.25 },
  'openai/gpt-4o': { input: 2.50, output: 10.00 },
  'google/gemini-flash-1.5': { input: 0.075, output: 0.30 },
}

function estimateCost(prompt: string, expectedCompletion: number, model: string) {
  const encoder = encoding_for_model('gpt-4')
  const promptTokens = encoder.encode(prompt).length

  const pricing = modelPricing[model] || { input: 0, output: 0 }
  const promptCost = (promptTokens / 1_000_000) * pricing.input
  const completionCost = (expectedCompletion / 1_000_000) * pricing.output

  return {
    promptTokens,
    completionTokens: expectedCompletion,
    totalCost: promptCost + completionCost,
  }
}
```

## Exact Cost Lookup (Post-Hoc)

```typescript
async function getGenerationCost(generationId: string) {
  const res = await fetch(`https://openrouter.ai/api/v1/generation?id=${generationId}`, {
    headers: { Authorization: `Bearer ${apiKey}` }
  })
  const json = await res.json()

  return {
    id: json.data.id,
    model: json.data.model,
    totalCost: json.data.total_cost,
    promptTokens: json.data.tokens_prompt,
    completionTokens: json.data.tokens_completion,
  }
}
```

## Budget-Constrained Selection

```typescript
async function budgetOptimizedChat(prompt: string, maxCost = 0.01) {
  const models = ['anthropic/claude-3.5-sonnet', 'anthropic/claude-3-haiku', 'google/gemini-flash-1.5']

  for (const model of models) {
    const estimate = estimateCost(prompt, 1000, model)
    if (estimate.totalCost <= maxCost) {
      console.log(`Selected: ${model} (est. $${estimate.totalCost.toFixed(4)})`)
      return await client.chat.completions.create({
        model,
        messages: [{ role: 'user', content: prompt }],
      })
    }
  }

  throw new Error('No model fits budget')
}
```
