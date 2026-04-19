---
name: ai-pi-nv-nemotron-3-super
description: Adversarial review via pi using Nemotron 3 Super 120B A12B via nvidia-nim
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
pi --model nvidia-nim/nvidia/nemotron-3-super-120b-a12b \
  -p @P:/path/to/file.py \
  "Read the file at @{path} carefully. Return JSON with score (0-1), summary (1 sentence), and issues. Begin your response with the exact first line of the file, quoted. If you did not read the file, set score to 0.0."
```

## Model Info

| Attribute | Value |
|-----------|-------|
| Model | nemotron-3-super-120b-a12b |
| Provider | nvidia-nim |
| Context | 131.1K |
| Max Output | 32.8K |
| Thinking | yes |
| Strength | Code generation, review |

## API Key Setup

pi requires `NVIDIA_NIM_API_KEY` at startup. Export from auth.json:

```bash
NV_KEY=$(python -c "import json; d=json.load(open('$USERPROFILE/.pi/agent/auth.json')); print(d.get('nvidia',{}).get('key',''))")
export NVIDIA_NIM_API_KEY="$NV_KEY"
pi --model nvidia-nim/nvidia/nemotron-3-super-120b-a12b -p @P:/path/to/file.py "Read the file at @{path} carefully. Return JSON with score (0-1), summary (1 sentence), and issues. Begin your response with the exact first line of the file, quoted. If you did not read the file, set score to 0.0."
```

## Verification

```bash
pi --model nvidia-nim/nvidia/nemotron-3-super-120b-a12b -p @P:/path/to/file.py "Say hello"
```

If you get `429 status code` — rate limit hit. Wait 30s and retry.
