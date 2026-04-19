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
  - Parse JSON output
  - Report findings
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-devstral — Adversarial Review via Pi + Devstral 2

## Quick Start

```bash
pi --model nvidia-nim/mistralai/devstral-2-123b-instruct-2512 \
  -p @P:/path/to/file.py \
  "Read the file at @{path} carefully. Then return ONLY valid JSON:
{
  \"file_first_line\": \"quote the first non-empty line exactly\",
  \"file_line_count\": N,
  \"score\": <0-1>,
  \"summary\": \"<1 sentence>\",
  \"issues\": [\"<issue with line numbers>\"]
}
If you did not read the file, set score to 0.0 and note \"did not read file\" in issues."
```

## Model Info

| Attribute | Value |
|-----------|-------|
| Model | devstral-2-123b-instruct-2512 |
| Provider | nvidia-nim |
| Context | 131.1K |
| Max Output | 32.8K |
| Thinking | yes |
| Strength | Code review, security analysis |

## API Key Setup

pi requires `NVIDIA_NIM_API_KEY` at startup. Export from auth.json:

```bash
NV_KEY=$(python -c "import json; d=json.load(open('$USERPROFILE/.pi/agent/auth.json')); print(d.get('nvidia',{}).get('key',''))")
export NVIDIA_NIM_API_KEY="$NV_KEY"
pi --model nvidia-nim/mistralai/devstral-2-123b-instruct-2512 -p @P:/path/to/file.py "Read the file at @{path} carefully. Return JSON with score (0-1), summary (1 sentence), and issues. Begin your response with the exact first line of the file, quoted. If you did not read the file, set score to 0.0."
```

## Verification

```bash
pi --model nvidia-nim/mistralai/devstral-2-123b-instruct-2512 -p @P:/path/to/file.py "Say hello"
```

If you get `429 status code` — rate limit hit. Wait 30s and retry.
