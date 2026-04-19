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
  - Parse JSON output
  - Report findings
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-nemotron-ultra — Adversarial Review via Pi + Llama 3.1 Nemotron Ultra

## Quick Start

```bash
pi --model nvidia-nim/nvidia/llama-3.1-nemotron-ultra-253b-v1 \
  -p @P:/path/to/file.py \
  "Read the file at @{path} carefully. Return JSON with score (0-1), summary (1 sentence), and issues. Begin your response with the exact first line of the file, quoted. If you did not read the file, set score to 0.0."
```

## Model Info

| Attribute | Value |
|-----------|-------|
| Model | llama-3.1-nemotron-ultra-253b-v1 |
| Provider | nvidia-nim |
| Context | 131.1K |
| Max Output | 32.8K |
| Thinking | yes |
| Strength | Complex reasoning, code review |

## API Key Setup

pi requires `NVIDIA_NIM_API_KEY` at startup. Export from auth.json:

```bash
NV_KEY=$(python -c "import json; d=json.load(open('$USERPROFILE/.pi/agent/auth.json')); print(d.get('nvidia',{}).get('key',''))")
export NVIDIA_NIM_API_KEY="$NV_KEY"
pi --model nvidia-nim/nvidia/llama-3.1-nemotron-ultra-253b-v1 -p @P:/path/to/file.py "Read the file at @{path} carefully. Return JSON with score (0-1), summary (1 sentence), and issues. Begin your response with the exact first line of the file, quoted. If you did not read the file, set score to 0.0."
```

## Verification

```bash
pi --model nvidia-nim/nvidia/llama-3.1-nemotron-ultra-253b-v1 -p @P:/path/to/file.py "Say hello"
```

If you get `429 status code` — rate limit hit. Wait 30s and retry.
