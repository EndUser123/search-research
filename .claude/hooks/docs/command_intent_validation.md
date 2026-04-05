# Command Intent Validation Gate

## Problem

When user invokes slash commands, Claude sometimes adds unauthorized restrictive flags:

```
User: /ask-cli4 "review the plan"
Claude executes: python ask_cli.py "..." --qwen-only  ← UNAUTHORIZED
```

The user wanted all 4 CLIs (the default), but Claude unilaterally restricted to qwen only.

## Solution

Two-part hook system:

### 1. UserPromptSubmit (state storage)

When a slash command is detected, `UserPromptSubmit_router.py` stores:
- The skill name
- The user's original prompt
- Expiry timestamp (5 minutes)

Location: `P:/.claude/hooks/state/pending_command_intent.json`

### 2. PreToolUse (validation)

`PreToolUse_command_intent_gate.py` runs before every Bash command:
1. Checks if there's a pending slash command intent
2. If the bash command is executing the skill
3. Scans for **restrictive flags** (--qwen-only, --skip-*, etc.)
4. Validates flags are justified by user's prompt
5. **BLOCKS** unauthorized restrictions

## Restrictive vs Helpful Flags

| Flag Type | Examples | Blocked? |
|-----------|----------|----------|
| **Restrictive** | `--qwen-only`, `--skip-push`, `--dry-run` | Yes, unless justified |
| **Helpful** | `--context`, `--verbose`, `--output-format` | No |

## Justification Rules

A restrictive flag is justified if the user's prompt contains relevant keywords:

| Flag | Justified by |
|------|--------------|
| `--qwen-only` | "qwen", "use qwen", "just qwen", "only qwen" |
| `--gemini-only` | "gemini", "use gemini", "just gemini" |
| `--dry-run` | "dry run", "simulate", "test run", "don't actually" |
| `--skip-push` | "skip push", "don't push", "no push" |

## Examples

### Allowed

```
User: /ask-cli4 use qwen to review the code
Command: python ask_cli.py "review the code" --qwen-only
Result: ✓ ALLOWED (user said "use qwen")
```

### Blocked

```
User: /ask-cli4 "review the plan"
Command: python ask_cli.py "review the plan" --qwen-only
Result: ⛔ BLOCKED (user didn't authorize qwen-only restriction)
```

## Configuration

### settings.json

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/.claude/hooks/PreToolUse_command_intent_gate.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

## Logging

All decisions logged to: `P:/.claude/logs/command_intent_gate.jsonl`

```json
{
  "timestamp": "2026-01-25T10:30:00",
  "skill": "ask-olymp",
  "user_prompt": "review the plan",
  "command": "python ask_cli.py ... --qwen-only",
  "decision": "deny",
  "reason": "Unauthorized restrictive flags: --qwen-only"
}
```

## Adding New Skills

To add intent validation for a new skill:

1. Add to `SKILL_COMMAND_PATTERNS`:
```python
SKILL_COMMAND_PATTERNS = {
    "new-skill": ["pattern1", "pattern2"],
}
```

2. Add restrictive flags if any:
```python
RESTRICTIVE_FLAGS = {
    "new-skill": ["--skip-something", "--only-partial"],
}
```

## Future Enhancement: Haiku Validation

For more complex intent matching, the hook can be converted to use Claude Code's built-in prompt-based hooks:

```json
{
  "PreToolUse": [
    {
      "matcher": "Bash",
      "hooks": [
        {
          "type": "prompt",
          "prompt": "User invoked /{skill} with: {prompt}. Claude is executing: {command}. Does this match intent? Return 'approve' or 'deny'."
        }
      ]
    }
  ]
}
```

This would use Haiku for semantic intent matching, handling natural language variations better than pattern matching.
