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
  - Parse JSON output
  - Report findings
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-or-nemotron-free — Adversarial Review via Pi + Nemotron 3 Super (Free)

## Quick Start

```bash
pi --model openrouter/nvidia/nemotron-3-super-120b-a12b:free \
  -p @P:/path/to/file.py \
  "Read the file at @{path} carefully. Return JSON with score (0-1), summary (1 sentence), and issues. Begin your response with the exact first line of the file, quoted. If you did not read the file, set score to 0.0."
```

## Model Info

| Attribute | Value |
|-----------|-------|
| Model | nemotron-3-super-120b-a12b:free |
| Provider | openrouter |
| Context | 131.1K |
| Max Output | 32.8K |
| Thinking | yes |
| Strength | Free tier, decent coding |

## API Key Setup

pi requires `NVIDIA_NIM_API_KEY` at startup even for openrouter models. Export both keys:

```bash
NV_KEY=$(python -c "import json; d=json.load(open('$USERPROFILE/.pi/agent/auth.json')); print(d.get('nvidia',{}).get('key',''))")
OR_KEY=$(python -c "import json; d=json.load(open('$USERPROFILE/.pi/agent/auth.json')); print(d.get('openrouter',{}).get('key',''))")
export NVIDIA_NIM_API_KEY="$NV_KEY"
export OPENROUTER_API_KEY="$OR_KEY"
pi --model openrouter/nvidia/nemotron-3-super-120b-a12b:free -p @P:/path/to/file.py "Read the file at @{path} carefully. Return JSON with score (0-1), summary (1 sentence), and issues. Begin your response with the exact first line of the file, quoted. If you did not read the file, set score to 0.0."
```

## Verification

```bash
pi --model openrouter/nvidia/nemotron-3-super-120b-a12b:free -p @P:/path/to/file.py "Say hello"
```

If you get `429 status code` — rate limit hit. Wait 30s and retry.
