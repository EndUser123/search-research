---
type: concept
title: "Pi Agent Harness: Architecture, Concurrency, and Multi-LLM"
created: 2026-04-18
source: ~/Downloads/hooks_implementation_plan 2.md
hash: 6e29ef00e690d59f033409a9927f886e4ecb9cf6f1f961f98e4f3576801f3566
tags:
  - pi
  - agent-harness
  - multi-llm
  - architecture
  - opencode
summary: "Pi is a minimal TypeScript agent harness, model-agnostic, designed for extensibility. No SQLite locking issues. Supports 15+ providers. Architecture comparison vs OpenCode and Claude Code."
---

# Pi Agent Harness

## What Pi Is

Pi is a **minimal, programmable TypeScript agent harness** written to be:
- Small, composable, with in-process hooks
- Model-agnostic: plug in whatever LLM backend you want
- Designed for extensibility over built-in features

**Not**: a local CLI that fronts a shared SQLite DB with subprocess contention.

## Key Property: No SQLite Locking

Pi runs as a **single long-running in-process agent** — not separate CLI subprocesses hitting a shared SQLite file.

- LLM calls and tools invoked from inside one process
- Any persistence you add is **your choice** (in-memory, Redis, Postgres, etc.)
- The "opencode SQLite lock" failure mode **does not apply**

## Architecture Comparison

| | Pi | OpenCode | Claude Code |
|--|-----|----------|------------|
| **Architecture** | In-process TS harness | CLI + local SQLite DB | Integrated harness |
| **Concurrency** | Internal, controlled | Serialized (SQLite locking) | Native concurrency |
| **Extensibility** | Very high (TS hooks, extensions) | High (configs, plugins) | Lower |
| **Multi-LLM** | 15+ providers, mid-session switching | Broad provider support | Limited (Anthropic-centric) |
| **SQLite issue** | None (unless you add it) | Yes — shared DB locking | N/A |

## Multi-LLM Support

Pi explicitly supports: Anthropic, OpenAI, Google, Azure, Bedrock, Mistral, Groq, Cerebras, xAI, Hugging Face, Kimi, MiniMax, OpenRouter, Ollama.

Switch models mid-session with `/model` or `Ctrl+L`.

## Adding Providers via API Keys

### Environment Variables (fastest)
```powershell
$env:ANTHROPIC_API_KEY = "..."
$env:OPENROUTER_API_KEY = "..."
$env:GEMINI_API_KEY = "..."
pi
```

### auth.json (persistent)
```
~/.pi/agent/auth.json
```

```json
{
  "anthropic": { "type": "api-key", "apiKey": "sk-ant-..." },
  "openrouter": { "type": "api-key", "apiKey": "sk-or-..." },
  "google": { "type": "api-key", "apiKey": "AIza..." },
  "zai": { "type": "api-key", "apiKey": "..." },
  "minimax": { "type": "api-key", "apiKey": "..." }
}
```

## Extensions

Pi extensions are TypeScript modules in `~/.pi/agent/extensions/` or `.pi/extensions/` (project-local).

Key capabilities:
- `pi.registerTool(...)` — add LLM-callable tools
- `pi.registerCommand(...)` — add user commands
- `pi.on(...)` lifecycle hooks like `before_provider_request`
- `pi.registerProvider(...)` — custom provider (routing, proxies, gateways)

## When to Use Pi Over OpenCode

- You want **real parallelism** without SQLite lock workarounds
- You need **fine-grained control** over provider routing, request interception
- You're building custom orchestration patterns
- You want **provider hedging**: mix frontier + cheap + local in one session

## Best Fit for Your Stack

- **Primary quality**: Claude-class frontier model via Anthropic
- **Routing layer**: OpenRouter for breadth and quick experiments
- **Fast/cheap**: Groq/Cerebras for iterative edits
- **Local fallback**: Ollama for offline/private work

## Related

- [[wiki/concepts/opencode-sqlite-parallelism]] — why OpenCode has SQLite locking issues
- [[wiki/concepts/skill-enforcement-layers]] — Pi doesn't need the same enforcement architecture as Claude Code hooks
