# Tool Calling

## Basic Tools

```typescript
const tools = [{
  type: 'function',
  function: {
    name: 'get_weather',
    description: 'Get weather for a city',
    parameters: {
      type: 'object',
      properties: {
        city: { type: 'string' },
        unit: { type: 'string', enum: ['celsius', 'fahrenheit'] }
      },
      required: ['city']
    }
  }
}]

const response = await client.chat.completions.create({
  model: 'openai/gpt-4o',
  messages: [{ role: 'user', content: 'Weather in Tokyo?' }],
  tools,
  tool_choice: 'auto'
})

if (response.choices[0].message.tool_calls) {
  for (const call of response.choices[0].message.tool_calls) {
    const args = JSON.parse(call.function.arguments)
    // Execute tool and send result back
  }
}
```

## Multi-Step Loop

```typescript
async function multiStepToolCall(userQuery: string) {
  const messages = [{ role: 'user', content: userQuery }]

  for (let i = 0; i < 5; i++) {
    const completion = await client.chat.completions.create({
      model: 'openai/gpt-4o',
      messages: [...messages],
      tools,
      tool_choice: 'auto',
    })

    const message = completion.choices[0].message
    messages.push(message)

    if (!message.tool_calls) {
      return message.content // Final response
    }

    // Execute tools and append results
    for (const call of message.tool_calls) {
      const result = await executeTool(call.function.name, JSON.parse(call.function.arguments))
      messages.push({
        role: 'tool',
        tool_call_id: call.id,
        content: JSON.stringify(result),
      })
    }
  }
}
```
