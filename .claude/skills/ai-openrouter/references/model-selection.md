# Model Selection Strategy

## Model Tiers

```typescript
// Flagship (highest quality)
const flagship = {
  claude: 'anthropic/claude-3.5-sonnet',
  gpt4: 'openai/gpt-4o',
  gemini: 'google/gemini-pro-1.5'
}

// Fast (low latency)
const fast = {
  claude: 'anthropic/claude-3-haiku',
  gpt35: 'openai/gpt-3.5-turbo',
  gemini: 'google/gemini-flash-1.5',
  llama: 'meta-llama/llama-3.1-8b-instruct'
}

// Cost-optimized
const budget = {
  haiku: 'anthropic/claude-3-haiku',      // $0.25/$1.25 per 1M
  gemini: 'google/gemini-flash-1.5',     // $0.075/$0.30 per 1M
  llama: 'meta-llama/llama-3.1-8b-instruct' // $0.06/$0.06 per 1M
}
```

## Model Selector

```typescript
function selectModel(criteria: {
  task: 'chat' | 'code' | 'vision'
  priority: 'quality' | 'speed' | 'cost'
  contextSize?: number
}): string {
  if (criteria.task === 'vision') {
    return 'openai/gpt-4o' // or google/gemini-2.5-flash
  }

  if (criteria.contextSize && criteria.contextSize > 100000) {
    return 'google/gemini-pro-1.5' // 2M context
  }

  switch (criteria.priority) {
    case 'quality': return 'anthropic/claude-3.5-sonnet'
    case 'speed': return 'anthropic/claude-3-haiku'
    case 'cost': return 'google/gemini-flash-1.5'
    default: return 'openai/gpt-4o'
  }
}
```
