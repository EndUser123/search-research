# Prompt Enhancement System

## Overview

The Prompt Enhancement System provides user prompt enhancement through a multi-layer architecture with user choice capability.

## Architecture

```
User Prompt
    ↓
[Noise Cleaning]
    ↓
[Complexity Analysis]
    ↓
[Domain Detection]
    ↓
┌─────────────────┐
│  Simple (0-10)    │ → Pass through (no enhancement)
│  Moderate (10-30)│ → Guidance + Choice UI
│  Complex (30-60)  │ → Guidance + Choice UI
│  Expert (60+)     │ → Guidance + Choice UI
└─────────────────┘
    ↓
[Save State] ← User chooses "0" or "1" later
    ↓
[Return Choice]
```

## Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Main Hook | `UserPromptSubmit/prompt_enhancement.py` | Router integration, analysis, enhancement logic |
| State Manager | `__lib/prompt_choice_state.py` | Multi-turn state management with terminal isolation |
| Tests | `UserPromptSubmit/tests/test_prompt_enhancement.py` | Unit tests |

## Configuration

Environment variables in `settings.json`:

```json
{
  "env": {
    "PROMPT_ENHANCEMENT_ENABLED": "true",
    "PROMPT_ENHANCEMENT_DEBUG": "false",
    "PROMPT_CHOICE_ENABLED": "true"
  }
}
```

| Variable | Default | Purpose |
|----------|---------|---------|
| `PROMPT_ENHANCEMENT_ENABLED` | `"false"` | Master enable/disable |
| `PROMPT_ENHANCEMENT_DEBUG` | `"false"` | Debug output to stderr |
| `PROMPT_CHOICE_ENABLED` | `"true"` | Enable/disable choice UI |

## Choice UI Format

Uses `/p`-style numbered options:

```
**💡 Prompt Enhancement Available**

**Your original:**
{user's original prompt}

**Enhanced version:**
{original + domain-specific guidance}

**Action Required**

0 - Use enhanced prompt (recommended)
1 - Use your original prompt

---
```

## Complexity Thresholds

| Level | Word Count | Behavior |
|-------|------------|----------|
| Simple | 0-10 | Pass through, no enhancement |
| Moderate | 10-30 | Lightweight guidance + choice |
| Complex | 30-60 | Guidance + choice |
| Expert | 60+ | Guidance + choice |

## Domain-Specific Guidance

| Domain | Guidance |
|--------|----------|
| Security | OWASP Top 10, input validation, authentication |
| Testing | TDD principles, test structure, edge cases |
| Database | Data integrity, transaction safety, indexing |
| Frontend | Component reusability, state management, accessibility |
| General | "Provide specific details" fallback |

## State Management

State files: `.claude/state/prompt_choice/{session_id}.json`

Isolation priority:
1. `session_id` from hook input
2. `terminal_id` from hook input
3. Environment variables (`CLAUDE_SESSION_ID`, `CLAUDE_TERMINAL_ID`)
4. PID fallback (least stable)

Auto-cleanup after 5 minutes.

## Noise Filtering

Automatically removes terminal artifacts:
- Terminal symbols: `❯`, `⎿`, `⚙`, `●`
- Hook messages: `UserPromptSubmit hook error/success`
- Tool artifacts: `Read 1 file`, `Added X lines`
- System reminders: `<system-reminder>...</system-reminder>`
- File paths and code snippets

## Integration

The system integrates via the `UserPromptSubmit` router:

```python
# In UserPromptSubmit/prompt_enhancement.py
@register_hook("prompt_enhancement", priority=8.0)
def prompt_enhancement_hook(context: HookContext) -> HookResult:
    result = process_prompt(context.data)
    if result and "additionalContext" in result:
        return HookResult(context=result["additionalContext"], tokens=result.get("tokens", 0))
    return HookResult.empty()
```

## Testing

Run tests:
```bash
pytest P:/.claude/hooks/UserPromptSubmit/tests/test_prompt_enhancement.py -v
```

## Example Flow

### Turn 1: User submits moderate prompt
```
User: "implement a websocket server with proper error handling"

Hook detects: 11 words (moderate), no ambiguity
Domain detected: "security" (keywords: "error handling")
Guidance injected: Security context
State saved: `session_abc123.json`
Choice UI shown with [0]/[1] options
```

### Turn 2: User chooses enhanced
```
User: "0"

Hook detects: Choice response
Pending state loaded from `session_abc123.json`
Returns: `replacePrompt` with enhanced prompt
State cleared
```

## Development History

- 2025-02-15: Initial implementation with choice UI
- 2025-02-15: Added `/p`-style formatting
- 2025-02-15: Fixed multi-terminal state isolation
- 2025-02-15: Added robust terminal noise filtering
- 2025-02-15: Consolidated (removed redundant bridge file)
