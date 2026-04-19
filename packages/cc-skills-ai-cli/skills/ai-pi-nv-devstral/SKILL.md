---
name: ai-pi-nv-devstral
description: Adversarial review via pi using Devstral 2 (mistralai/devstral-2-123b-instruct) via nvidia-nim
version: 1.0.0
enforcement: strict
triggers:
  - /ai-pi-devstral
  - /pi-devstral
  - adversarial review devstral
workflow_steps:
  - Parse target
  - Invoke pi with devstral via nvidia-nim
  - Parse JSON output
  - Report findings
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-devstral — Adversarial Review via Pi + Devstral 2

## Quick Start

```bash
pi --model nvidia-nim/mistralai/devstral-2-123b-instruct-2512 \
  -p @P:/path/to/file.py \
  "Analyze for security vulnerabilities. Be adversarial. Return JSON with score (0-1), summary, and issues."
```

## Model Info

| Attribute | Value |
|-----------|-------|
| Model | devstral-2-123b-instruct-2512 |
| Provider | nvidia-nim |
| Context | 131K |
| Max Output | 32.8K |
| Thinking | no |
| Strength | Code review, security analysis |

## Verification

```bash
pi --model nvidia-nim/mistralai/devstral-2-123b-instruct-2512 -p @P:/path/to/file.py "Say hello"
```

If you get `429 status code` — rate limit hit. Wait 30s and retry.
