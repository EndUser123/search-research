# Rate Limiting

## Rate Limited Client (TypeScript)

```typescript
class RateLimitedClient {
  private requestQueue: Array<() => Promise<any>> = []
  private processing = false
  private requestsPerMinute = 60
  private requestInterval = 60000 / this.requestsPerMinute

  async enqueue<T>(request: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.requestQueue.push(async () => {
        try {
          resolve(await request())
        } catch (error) {
          reject(error)
        }
      })
      this.processQueue()
    })
  }

  private async processQueue() {
    if (this.processing || this.requestQueue.length === 0) return

    this.processing = true
    while (this.requestQueue.length > 0) {
      const request = this.requestQueue.shift()!
      await request()
      await new Promise(resolve => setTimeout(resolve, this.requestInterval))
    }
    this.processing = false
  }
}

// Usage
const rateLimitedClient = new RateLimitedClient()
const result = await rateLimitedClient.enqueue(() =>
  client.chat.completions.create({
    model: 'anthropic/claude-3.5-sonnet',
    messages: [{ role: 'user', content: 'Hello' }],
  })
)
```

## Exponential Backoff

```typescript
async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries = 5
): Promise<T> {
  let lastError: Error

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn()
    } catch (error: any) {
      lastError = error

      if (error.status === 429) { // Rate limit
        const delay = Math.pow(2, i) * 1000
        console.log(`Rate limited. Retrying in ${delay}ms...`)
        await new Promise(resolve => setTimeout(resolve, delay))
      } else {
        throw error // Non-retryable
      }
    }
  }

  throw lastError!
}
```
