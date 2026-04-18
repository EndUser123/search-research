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
  - Parse JSONL output
  - Report findings
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-devstral — Adversarial Review via Pi + Devstral 2

```bash
pi --mode json --provider nvidia-nim --model mistralai/devstral-2-123b-instruct-2512 "Review P:/path/to/file.py and return JSON"
```