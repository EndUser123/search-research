# Prompt Enhancement System

## Overview

The Prompt Enhancement System provides user prompt enhancement through a multi-layer architecture with user choice capability. It integrates with Claude Code via the UserPromptSubmit hook.

## Features

- **Noise Cleaning**: Automatically removes terminal artifacts from prompts
- **Complexity Analysis**: Categorizes prompts by word count (simple, moderate, complex, expert)
- **Domain Detection**: Identifies domain context (security, testing, database, frontend, general)
- **Choice UI**: `/p`-style numbered options for user to accept or decline enhancements
- **Multi-terminal Safe**: Terminal-specific state isolation

## Installation

The hook router automatically discovers packages in `P:/packages/` or `~/.claude/hooks/_packages/`. **No symlinks required.**

### Option A: Local Development (P:/packages/)

For development, place the package in your local packages directory:

```bash
# Package already exists if you're developing from P:/packages/prompt-enhancement/
# The hook router will auto-discover it via sys.path
```

### Option B: Production (Installed from GitHub)

For production use from GitHub:

```bash
# Clone to packages directory
git clone https://github.com/csf-dev/prompt-enhancement.git ~/.claude/hooks/_packages/prompt-enhancement

# Or download and extract release to ~/.claude/hooks/_packages/prompt-enhancement/
```

### Enable in Settings

Add to `P:/.claude/settings.json` (or `~/.claude/settings.json`):

```json
{
  "env": {
    "PROMPT_ENHANCEMENT_ENABLED": "true",
    "PROMPT_ENHANCEMENT_DEBUG": "false",
    "PROMPT_CHOICE_ENABLED": "true"
  }
}
```

### How It Works

The `UserPromptSubmit/registry.py` adds package directories to `sys.path`, then imports `prompt_enhancement` module directly:

```python
# In registry.py
sys.path.insert(0, "P:/packages")  # or ~/.claude/hooks/_packages

# Later, import works:
from prompt_enhancement.hook import prompt_enhancement
```

### Removing

Simply delete the package directory:

```bash
rm -rf P:/packages/prompt-enhancement
# or
rm -rf ~/.claude/hooks/_packages/prompt-enhancement
```

## Configuration

| Environment Variable | Default | Purpose |
|---------------------|---------|---------|
| `PROMPT_ENHANCEMENT_ENABLED` | `false` | Master enable/disable |
| `PROMPT_ENHANCEMENT_DEBUG` | `false` | Debug output to stderr |
| `PROMPT_CHOICE_ENABLED` | `true` | Enable/disable choice UI |

## Usage

Once installed and enabled, the system automatically:

1. **Analyzes** each prompt for complexity and domain
2. **Enhances** with domain-specific guidance
3. **Presents choice** - select `0` for enhanced, `1` for original

```
Your prompt: "implement websocket server"

**💡 Prompt Enhancement Available**

**Your original:**
implement websocket server

**Enhanced version:**
implement websocket server

**Security Context**: Considering security implications including input validation,
output encoding, authentication, authorization, and common vulnerabilities (OWASP Top 10).

**Action Required**

0 - Use enhanced prompt (recommended)
1 - Use your original prompt
```

## Complexity Thresholds

| Level | Word Count | Behavior |
|-------|------------|----------|
| Simple | 0-10 | Pass through, no enhancement |
| Moderate | 10-30 | Lightweight guidance + choice |
| Complex | 30-60 | Guidance + choice |
| Expert | 60+ | Guidance + choice |

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

## Files

| File | Purpose |
|------|---------|
| `hook/prompt_enhancement.py` | Main hook module with router integration |
| `hook/prompt_choice_state.py` | Multi-turn state management |
| `hook/__lib_prompt_enhancement/` | Shared utilities and tests |

## State Management

State files: `.claude/state/prompt_choice/{session_id}.json`

Isolation priority:
1. `session_id` from hook input
2. `terminal_id` from hook input
3. Environment variables (`CLAUDE_SESSION_ID`, `CLAUDE_TERMINAL_ID`)
4. PID fallback (least stable)

Auto-cleanup after 5 minutes.

## License

MIT
