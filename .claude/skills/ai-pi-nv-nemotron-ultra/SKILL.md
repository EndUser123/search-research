---
name: ai-pi-nv-nemotron-ultra
description: Adversarial review via pi using Llama 3.1 Nemotron Ultra (253B) via nvidia-nim
version: 1.0.0
enforcement: strict
triggers:
  - /ai-pi-nemotron-ultra
  - /pi-nemotron-ultra
  - adversarial review nemotron-ultra
workflow_steps:
  - Parse target
  - Invoke pi with nemotron ultra via nvidia-nim
  - Parse JSONL output
  - Report findings
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-nemotron-ultra — Adversarial Review via Pi + Llama 3.1 Nemotron Ultra

```bash
pi --mode json --provider nvidia-nim --model nvidia/llama-3.1-nemotron-ultra-253b-v1 "Review P:/path/to/file.py and return JSON"
```