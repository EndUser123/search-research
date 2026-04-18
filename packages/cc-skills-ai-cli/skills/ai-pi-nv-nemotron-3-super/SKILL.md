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
  - Parse JSONL output
  - Report findings
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-nemotron-super — Adversarial Review via Pi + Llama 3.3 Nemotron Super

```bash
pi --mode json --provider nvidia-nim --model nvidia/llama-3.3-nemotron-super-49b-v1.5 "Review P:/path/to/file.py and return JSON"
```