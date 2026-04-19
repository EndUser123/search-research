---
name: ai-pi-nv-kimi
description: Adversarial review via pi using Kimi K2.5 (moonshotai/kimi-k2.5) via nvidia-nim
version: 1.0.0
enforcement: strict
triggers:
  - /ai-pi-nv-kimi
  - /pi-nv-kimi
  - adversarial review kimi
workflow_steps:
  - Parse target
  - Invoke pi with kimi-k2.5 via nvidia-nim
  - Parse JSON output
  - Report findings
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-nv-kimi — Adversarial Review via Pi + Kimi K2.5

## Quick Start

```bash
pi --model nvidia-nim/moonshotai/kimi-k2.5 \
  -p @P:/path/to/file.py \
  "Analyze for security vulnerabilities. Be adversarial. Return JSON with score (0-1), summary, and issues."
```

## Model Info

| Attribute | Value |
|-----------|-------|
| Model | kimi-k2.5 |
| Provider | nvidia-nim |
| Context | 262K |
| Max Output | 16.4K |
| Thinking | yes |
| Strength | Long context, coding |

## Verification

```bash
pi --model nvidia-nim/moonshotai/kimi-k2.5 -p @P:/path/to/file.py "Say hello"
```

If you get `429 status code` — rate limit hit. Wait 30s and retry.
