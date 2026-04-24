---
name: ai-pi-zai-glm51
description: Adversarial review via pi using GLM-5.1 (zai) - multi-provider coding agent dispatch
version: 1.0.0
enforcement: strict
triggers:
  - /ai-pi-zai-glm51
  - /pi-glm
  - adversarial review glm
  - review with glm-5.1
workflow_steps:
  - Parse target (file path or description)
  - Invoke pi dispatch_single with glm-5.1 model
  - Parse JSON output for findings
  - Report score, issues, and synthesis
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-zai-glm51 — Adversarial Review via Pi + GLM-5.1

Run adversarial code review using **GLM-5.1** via the **pi** multi-provider coding agent.

## Quick Start

```bash
pi --model zai/glm-5.1 \
  -p @P:/path/to/file.py \
  "Read the file at @{path} carefully. Return JSON with score (0-1), summary (1 sentence), and issues. Begin your response with the exact first line of the file, quoted. If you did not read the file, set score to 0.0."
```

## Model Info

| Attribute | Value |
|-----------|-------|
| Model | GLM-5.1 |
| Provider | zai |
| Context | ~200K |
| Thinking | yes |

## API Key Setup

pi requires `NVIDIA_NIM_API_KEY` at startup even for zai models. Export both keys:

```bash
NV_KEY=$(python -c "import json; d=json.load(open('$USERPROFILE/.pi/agent/auth.json')); print(d.get('nvidia',{}).get('key',''))")
export NVIDIA_NIM_API_KEY="$NV_KEY"
pi --model zai/glm-5.1 -p @P:/path/to/file.py "Read the file at @{path} carefully. Return JSON with score (0-1), summary (1 sentence), and issues. Begin your response with the exact first line of the file, quoted. If you did not read the file, set score to 0.0."
```

## Verification

```bash
pi --model zai/glm-5.1 -p @P:/path/to/file.py "Say hello"
```

If you get `429 status code` — rate limit hit. Wait 30s and retry.
