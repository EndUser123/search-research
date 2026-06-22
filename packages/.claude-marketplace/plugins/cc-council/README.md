# cc-council

Local-first multi-LLM council system for Claude Code on Windows 11.

## Overview

Implements Karpathy-style deliberation with transport-agnostic design:

1. **Independent drafts**: 3 models generate independent opinions
2. **Anonymized peer review**: Reviewer evaluates drafts without seeing model identities
3. **Chairman synthesis**: Final synthesis considers all inputs and contradictions

## Requirements

- Python 3.10+
- Ollama running on `localhost:11434`
- At least 3 models installed (e.g., `llama3:8b`, `mistral:7b`, `phi3:mini`)

## Installation

```bash
# Install Ollama (if not already installed)
# https://ollama.com/download

# Pull some models
ollama pull llama3:8b
ollama pull mistral:7b
ollama pull phi3:mini

# Install plugin via Claude Code marketplace
# Or manually copy to plugins directory
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
│   ├── providers/                # Ollama adapter
│   ├── persistence/              # SQLite state
│   └── policy/                   # Gating and consensus
├── commands/                     # CLI commands
├── hooks/                        # Claude Code hooks
├── agents/                       # Agent prompt definitions
└── tests/                        # Test suite
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

## State Persistence

Council state is persisted to:
```
~/.claude/state/council/state.db
```

Automatic recovery of stale sessions (timeout: 5 minutes).

## Limitations

- Single-round deliberation (v1)
- Ollama-only (future providers planned)
- Windows 11 only (untested elsewhere)
- Simple keyword-based gating
- Keyword-based contradiction detection

## License

MIT