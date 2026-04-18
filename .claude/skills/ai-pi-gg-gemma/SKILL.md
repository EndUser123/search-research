---
name: ai-pi-gg-gemma
description: Adversarial review via pi using Gemma 4-31B-IT (Google) - multi-provider coding agent dispatch
version: 1.0.0
enforcement: strict
triggers:
  - /ai-pi-gemma-4-31b-it
  - /pi-gemma
  - adversarial review gemma
  - review with gemma-4-31b-it
workflow_steps:
  - Parse target (file path or description)
  - Invoke pi dispatch_single with gemma model
  - Parse JSONL output for findings
  - Report score, issues, and synthesis
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-gemma-4-31b-it — Adversarial Review via Pi + Gemma 4-31B-IT

Run adversarial code review using **Gemma 4-31B-IT** via the **pi** multi-provider coding agent.

## Quick Start

```bash
# Single target review
pi --mode json --provider google --model gemma-4-31b-it "Review P:/path/to/file.py and return JSON with score (0-1), summary, and issues list"
```

## How It Works

This skill wraps the SQD dispatcher layer (`sqd/layers/dispatcher.py`) for single-model adversarial review:

1. **pi** dispatches to Google Gemma 4-31B-IT via `google/gemma-4-31b-it`
2. JSONL output is parsed for `type: agent_end` with assistant message
3. Finding extracted: score (0.0-1.0), summary, issues list

## Dispatcher Config

```
Model: google/gemma-4-31b-it
Provider: google
Timeout: 300s
Output: finding_gemma.json
```

## Integration

- SQD dispatcher: `P:/packages/sdlc/skills/sqd/layers/dispatcher.py`
- Output path: per-session `findings/` directory
- Exit codes: 0=consensus, 1=divergent, 2=failure, 3=not found

## Model Info

| Attribute | Value |
|-----------|-------|
| Model ID | gemma-4-31b-it |
| Provider | google |
| Context | ~32K |
| Strength | Code review, analysis |

## Verification

Run the verification ritual before first use:

```bash
pi --help | grep -E "(provider|model|mode)"
pi --mode json --provider google --model gemma-4-31b-it "Say hello"
```

If you get `429 status code` — rate limit hit. Wait 30s and retry, or use `deepseek`/`claude` as fallback providers.