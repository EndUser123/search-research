# Model Discovery

Best practice: query the live catalog instead of hardcoding models.

## List All Models

```typescript
const models = await fetch("https://openrouter.ai/api/v1/models", {
  headers: { Authorization: `Bearer ${apiKey}` }
}).then(r => r.json())

console.log(models.data.map((m: any) => m.id))
```

## Filter Free Models

> **Context-free alternative**: Use `fetch-free-models.py` in this skill's directory. Cache auto-refreshes at 00:00/12:00 UTC and notifies on changes:
> ```bash
> # Auto-refresh if expired (00:00 or 12:00 UTC)
> OPENROUTER_API_KEY=xxx python .claude/skills/openrouter/fetch-free-models.py
>
> # Check if expired (exit 1 if expired, 0 if fresh)
> python .claude/skills/openrouter/fetch-free-models.py --check-stale
>
> # Force refresh
> OPENROUTER_API_KEY=xxx python .claude/skills/openrouter/fetch-free-models.py --fresh
> ```

**Programmatic filter** (queries catalog in-context):

```typescript
const res = await fetch("https://openrouter.ai/api/v1/models", {
  headers: { Authorization: `Bearer ${apiKey}` }
})
const json = await res.json()

const freeModels = json.data.filter((model: any) => {
  const pricing = model?.pricing ?? {}
  return ["prompt", "completion", "request", "image"].every((key) => {
    const value = pricing[key]
    return value == null || value === "0"
  })
})
```

## Image Generation Models

```typescript
const imageModels = json.data.filter((model: any) =>
  model.architecture?.output_modalities?.includes("image")
)
```

## Health Check CLI

```bash
# Check API health (validates key, tests connectivity)
python -m .claude.skills.ai-openrouter.scripts.cli health

# Run with inference sanity check (tests free model)
python -m .claude.skills.ai-openrouter.scripts.cli health --sanity
```

**Health checks:**
- API key presence
- API connectivity to `/api/v1/models`
- Optional inference test with `google/gemma-2-9b-it:free`

**Exit codes:** `0` = healthy, `1` = failed
