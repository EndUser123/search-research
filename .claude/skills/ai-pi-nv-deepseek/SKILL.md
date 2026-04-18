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
  - Parse JSONL output
  - Report findings
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-deepseek-v32 — Adversarial Review via Pi + DeepSeek V3.2

```bash
pi --mode json --provider nvidia-nim --model deepseek-ai/deepseek-v3.2 "Review P:/path/to/file.py and return JSON"
```

Verified ✓