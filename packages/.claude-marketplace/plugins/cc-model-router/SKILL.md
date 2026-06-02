# cc-model-router

Automatic model-tier routing (haiku/sonnet/opus) based on prompt complexity heuristics.

## Features

- **Dual-mode operation**: warn (systemMessage injection) or autoswitch (exit 2 + atomic settings.json write)
- **Config walk-up**: plugin-level, global user-level, project-level override
- **Terminal+session scoped state** at `.claude/state/model-router/`
- **Python-only hooks** per ARCH-002

## Usage

### warn mode (default)

```json
{
  "action_mode": "warn"
}
```

SystemMessage injected into prompt when complexity threshold exceeded.

### autoswitch mode

```json
{
  "action_mode": "autoswitch"
}
```

Stop hook exits 2 to block response, settings.json updated atomically.

## Configuration

Place `claude-model-router.json` at:
1. Plugin level (default)
2. User level: `~/.claude/hooks/`
3. Project level: `.claude/hooks/` (highest priority)

## Tiers

| Tier | max_lines | max_file_size | max_tools |
|------|-----------|---------------|-----------|
| haiku | 100 | 10 | 5 |
| sonnet | 500 | 50 | 20 |
| opus | unlimited | unlimited | unlimited |

## State Files

State path: `.claude/state/model-router/{terminal_id}/{session_id}/recommendation.json`

TTL: 300 seconds. Fail-open ordering.
