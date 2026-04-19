---
name: ai-pi-or-qwen-free
description: Adversarial review via pi using Qwen3 Coder (free tier) via openrouter
version: 1.0.0
enforcement: strict
triggers:
  - /ai-pi-qwen3-coder-free
  - /pi-qwen-free
  - adversarial review qwen-free
workflow_steps:
  - Parse target
  - Invoke pi with qwen3-coder:free via openrouter
  - Parse JSON output
  - Report findings
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-qwen3-coder-free — Adversarial Review via Pi + Qwen3 Coder (Free)

## Quick Start

```bash
pi --model openrouter/qwen/qwen3-coder:free \
  -p @P:/path/to/file.py \
  "Analyze for security vulnerabilities. Be adversarial. Return JSON with score (0-1), summary, and issues."
```

## Model Info

| Attribute | Value |
|-----------|-------|
| Model | qwen3-coder:free |
| Provider | openrouter |
| Context | 262K |
| Max Output | 262K |
| Thinking | no |
| Strength | Free tier, good coding |

## Verification

```bash
pi --model openrouter/qwen/qwen3-coder:free -p @P:/path/to/file.py "Say hello"
```

If you get `429 status code` — rate limit hit. Wait 30s and retry.
