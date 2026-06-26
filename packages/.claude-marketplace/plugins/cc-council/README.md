# cc-council

Multi-LLM council system for Claude Code with transport-agnostic design.

## Overview

Implements Karpathy-style deliberation:

1. **Independent drafts**: 3 models generate independent opinions
2. **Anonymized peer review**: Reviewer evaluates drafts without seeing model identities
3. **Chairman synthesis**: Final synthesis considers all inputs and contradictions

## Requirements

- Python 3.10+
- **cc-skills-ai-api** plugin installed (provides transport layer)
- At least 3 models configured via SDK (e.g., m3, glm-5.2, kimi-k2.7-code)

## Installation

```bash
# Install cc-skills-ai-api first (required for transport)
claude plugin install cc-skills-ai-api@local

# Install cc-council
claude plugin install cc-council@local

# Configure API keys via environment variables
#   Z_AI_API_KEY, MINIMAX_API_KEY, OPENCODE_GO_API_KEY, etc.
```

## Usage

### Automatic (via hook)

The UserPromptSubmit hook intercepts prompts and runs council when gated:

- Prompts > 200 chars
- Keywords: compare, analyze, evaluate, review, assess, debate
- Explicit `@council` prefix

### Manual (via commands)

```bash
# Force council execution
/council-plan Analyze the tradeoffs between REST and GraphQL

# Review a previous session
/council-review <session-id>

# Check system health
/council-debug

# Single-model fallback
/council-decide What is 2+2?
```

## Architecture

```
cc-council/
├── .claude-plugin/plugin.json    # Plugin manifest
├── council_core/                 # Transport-agnostic core
│   ├── contracts/                # Data types
│   ├── engine/                   # Deliberation engine
│   ├── providers/                # ai-api transport adapter
│   ├── persistence/              # SQLite state
│   └── policy/                   # Gating and consensus
├── commands/                     # CLI commands
├── hooks/                        # Claude Code hooks
├── agents/                       # Agent prompt definitions
└── tests/                        # Test suite
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

## Supported Providers

Via **cc-skills-ai-api** transport:
- **z.ai**: glm-5.2
- **MiniMax**: m3 (reasoning-optimized)
- **opencode-go**: deepseek-chat, deepseek-coder
- **kimi**: kimi-k2.7-code
- **groq**: llama-3.3-70b-versatile, llama-3.1-8b-instant
- **mistral**: mistral-large-latest, codestral-latest
- **cerebras**: llama3.1-70b
- **nvidia**: meta/llama-3.1-405b-instruct, meta/llama-3.1-70b-instruct
- **openrouter**: Wildcard support via catalog
- **LM Studio**: Local models via `BF_LOCAL_LMSTUDIO_MODELS` env

## State Persistence

Council state is persisted to:
```
~/.claude/state/council/state.db
```

Automatic recovery of stale sessions (timeout: 5 minutes).

## Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `CC_COUNCIL_TRANSPORT_DIR` | Path to ai-api transport module | Auto-detected |
| `CC_COUNCIL_HEALTH_MODEL` | Model for health check | `m3` |
| `BF_LOCAL_LMSTUDIO_MODELS` | Comma-separated LM Studio models | - |

## Limitations

- Single-round deliberation (v1)
- Requires cc-skills-ai-api transport layer
- Windows 11 only (untested elsewhere)
- Simple keyword-based gating
- Keyword-based contradiction detection

## License

MIT