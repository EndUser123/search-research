# Context Handling — /ai-pcli Best Practices

## The --context Flag Is Required

Always use `--context FILE` to pass file content. Piped stdin is **ignored** when auto-context is detected.

```bash
# Correct
/ai-pcli "review this" --context P:\path\to\file.py

# Incorrect — stdin is ignored
type P:\path\to\file.py | /ai-pcli "review this"
```

## Auto-Detection

`ai_cli.py` auto-detects context from:
- `--context` flag (explicit, highest priority)
- `--target` flag (filters session context by relevance)
- Claude Code session context (if neither flag provided)

## Context Size and Timeout

Larger files increase timeout proportionally:
- Base timeout: 180s
- Per-MB overhead: +1s per MB of context
- Example: 5MB file → 185s timeout

Override with `--timeout N` if needed.

## Multiple Context Files

Pass multiple files by repeating the flag or using a glob pattern in the query:
```bash
/ai-pcli "compare these implementations" --context P:\src\a.py --context P:\src\b.py
```

## Target Filtering

Use `--target FILE` to narrow session context to a specific file, reducing noise from irrelevant context:
```bash
/ai-pcli "explain this function" --target P:\path\to\specific.py
```

## Context for Specific CLIs

When using single-CLI targeting (`--gemini-only`, `--codex-only`), the context is still passed to the targeted CLI. Ensure the model supports the context size to avoid truncation.