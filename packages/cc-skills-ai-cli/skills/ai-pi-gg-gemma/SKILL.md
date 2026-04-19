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
  - Parse JSON output for findings
  - Report score, issues, and synthesis
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-gemma-4-31b-it — Adversarial Review via Pi + Gemma 4-31B-IT

Run adversarial code review using **Gemma 4-31B-IT** via the **pi** multi-provider coding agent.

## Quick Start

```bash
pi --model google/gemma-4-31b-it \
  -p @P:/path/to/file.py \
  "Analyze for security vulnerabilities. Be adversarial. Return JSON with score (0-1), summary, and issues."
```

## Model Info

| Attribute | Value |
|-----------|-------|
| Model | gemma-4-31b-it |
| Provider | google |
| Context | 256K |
| Max Output | 8.2K |
| Thinking | yes |
| Images | yes |
| Strength | Code review, analysis |

## Verification

```bash
pi --model google/gemma-4-31b-it -p @P:/path/to/file.py "Say hello"
```

If you get `429 status code` — rate limit hit. Wait 30s and retry.
