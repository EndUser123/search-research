---
name: ai-pi-or-nemotron-free
description: Adversarial review via pi using Nemotron 3 Super 120B A12B (free tier) via openrouter
version: 1.0.0
enforcement: strict
triggers:
  - /ai-pi-or-nemotron-free
  - /pi-nemotron-free
  - adversarial review nemotron-free
workflow_steps:
  - Parse target
  - Invoke pi with nemotron-3-super-120b-a12b:free via openrouter
  - Parse JSON output
  - Report findings
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-or-nemotron-free — Adversarial Review via Pi + Nemotron 3 Super (Free)

## Quick Start

```bash
pi --model openrouter/nvidia/nemotron-3-super-120b-a12b:free \
  -p @P:/path/to/file.py \
  "Analyze for security vulnerabilities. Be adversarial. Return JSON with score (0-1), summary, and issues."
```

## Model Info

| Attribute | Value |
|-----------|-------|
| Model | nemotron-3-super-120b-a12b:free |
| Provider | openrouter |
| Context | 262K |
| Max Output | 4K |
| Thinking | yes |
| Strength | Free tier, decent coding |

## Verification

```bash
pi --model openrouter/nvidia/nemotron-3-super-120b-a12b:free -p @P:/path/to/file.py "Say hello"
```

If you get `429 status code` — rate limit hit. Wait 30s and retry.
