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
  - Parse JSONL output
  - Report findings
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-nv-kimi — Adversarial Review via Pi + Kimi K2.5

```bash
pi --mode json --provider nvidia-nim --model moonshotai/kimi-k2.5 "Review P:/path/to/file.py and return JSON"
```