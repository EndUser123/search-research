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
  - Parse JSON output
  - Report findings
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-nv-kimi — Adversarial Review via Pi + Kimi K2.5

## Quick Start

```bash
pi --model nvidia-nim/moonshotai/kimi-k2.5 \
  -p @P:/path/to/file.py \
  "Read the file at @{path} carefully. Return JSON with score (0-1), summary (1 sentence), and issues. Begin your response with the exact first line of the file, quoted. If you did not read the file, set score to 0.0."
```

## Model Info

| Attribute | Value |
|-----------|-------|
| Model | kimi-k2.5 |
| Provider | nvidia-nim |
| Context | 131.1K |
| Max Output | 32.8K |
| Thinking | yes |
| Strength | Long context, coding |

## API Key Setup

pi requires `NVIDIA_NIM_API_KEY` at startup. Export from auth.json:

```bash
NV_KEY=$(python -c "import json; d=json.load(open('$USERPROFILE/.pi/agent/auth.json')); print(d.get('nvidia',{}).get('key',''))")
export NVIDIA_NIM_API_KEY="$NV_KEY"
pi --model nvidia-nim/moonshotai/kimi-k2.5 -p @P:/path/to/file.py "Read the file at @{path} carefully. Return JSON with score (0-1), summary (1 sentence), and issues. Begin your response with the exact first line of the file, quoted. If you did not read the file, set score to 0.0."
```

## Verification

```bash
pi --model nvidia-nim/moonshotai/kimi-k2.5 -p @P:/path/to/file.py "Say hello"
```

If you get `429 status code` — rate limit hit. Wait 30s and retry.
