---
name: ai-pi-or-qwen-free
description: Adversarial review via pi using Qwen3 Coder (free tier) via openrouter
version: 1.0.0
enforcement: strict
triggers:
  - /ai-pi-qwen3-coder-free
  - /pi-qwen-free
  - adversarial review qwen-free
workflow_steps:
  - Parse target
  - Invoke pi with qwen3-coder:free via openrouter
  - Parse JSONL output
  - Report findings
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-qwen3-coder-free — Adversarial Review via Pi + Qwen3 Coder (Free)

```bash
pi --mode json --provider openrouter --model qwen/qwen3-coder:free "Review P:/path/to/file.py and return JSON"
```