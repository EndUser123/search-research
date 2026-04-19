---
name: ai-pi-nv-deepseek
description: Adversarial review via pi using DeepSeek V3.2 (deepseek-ai/deepseek-v3.2) via nvidia-nim
version: 1.0.0
enforcement: strict
triggers:
  - /ai-pi-deepseek-v32
  - /pi-deepseek
  - adversarial review deepseek
workflow_steps:
  - Parse target
  - Invoke pi with deepseek-v3.2 via nvidia-nim
  - Parse JSON output
  - Report findings
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-deepseek-v32 — Adversarial Review via Pi + DeepSeek V3.2

## Quick Start

```bash
pi --model nvidia-nim/deepseek-ai/deepseek-v3.2 \
  -p @P:/path/to/file.py \
  "Analyze for security vulnerabilities. Be adversarial. Return JSON with score (0-1), summary, and issues."
```

## Model Info

| Attribute | Value |
|-----------|-------|
| Model | deepseek-v3.2 |
| Provider | nvidia-nim |
| Context | 131K |
| Max Output | 16.4K |
| Thinking | yes |
| Strength | Reasoning, code review |

## Verification

```bash
pi --model nvidia-nim/deepseek-ai/deepseek-v3.2 -p @P:/path/to/file.py "Say hello"
```

If you get `429 status code` — rate limit hit. Wait 30s and retry.
