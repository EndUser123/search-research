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
  - Parse JSONL output
  - Report findings
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-or-nemotron-free — Adversarial Review via Pi + Nemotron 3 Super (Free)

```bash
pi --mode json --provider openrouter --model nvidia/nemotron-3-super-120b-a12b:free "Review P:/path/to/file.py and return JSON"
```
