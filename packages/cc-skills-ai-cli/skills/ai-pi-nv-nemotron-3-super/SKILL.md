---
name: ai-pi-nv-nemotron-3-super
description: Adversarial review via pi using Llama 3.3 Nemotron Super (49B) via nvidia-nim
version: 1.0.0
enforcement: strict
triggers:
  - /ai-pi-nemotron-super
  - /pi-nemotron-super
  - adversarial review nemotron-super
workflow_steps:
  - Parse target
  - Invoke pi with nemotron-super via nvidia-nim
  - Parse JSON output
  - Report findings
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-nemotron-super — Adversarial Review via Pi + Llama 3.3 Nemotron Super

## Quick Start

```bash
pi --model nvidia-nim/nvidia/llama-3.3-nemotron-super-49b-v1.5 \
  -p @P:/path/to/file.py \
  "Analyze for security vulnerabilities. Be adversarial. Return JSON with score (0-1), summary, and issues."
```

## Model Info

| Attribute | Value |
|-----------|-------|
| Model | llama-3.3-nemotron-super-49b-v1.5 |
| Provider | nvidia-nim |
| Context | 131K |
| Max Output | 2K |
| Thinking | yes |
| Strength | Code generation, review |

## Verification

```bash
pi --model nvidia-nim/nvidia/llama-3.3-nemotron-super-49b-v1.5 -p @P:/path/to/file.py "Say hello"
```

If you get `429 status code` — rate limit hit. Wait 30s and retry.
