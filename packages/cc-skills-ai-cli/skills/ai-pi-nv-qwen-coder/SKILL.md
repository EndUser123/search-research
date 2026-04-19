---
name: ai-pi-nv-qwen-coder
description: Adversarial review via pi using Qwen3 Coder 480B A35B (35B MoE, 262K context) - multi-provider coding agent dispatch
version: 1.0.0
enforcement: strict
triggers:
  - /ai-pi-qwen3-coder-480b
  - /pi-qwen3-coder
  - adversarial review qwen
  - review with qwen3-coder-480b
workflow_steps:
  - Parse target (file path or description)
  - Invoke pi dispatch_single with qwen model
  - Parse JSON output for findings
  - Report score, issues, and synthesis
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-qwen3-coder-480b — Adversarial Review via Pi + Qwen3 Coder 480B A35B

Run adversarial code review using **Qwen3 Coder 480B A35B** (35B MoE, 262K context) via the **pi** multi-provider coding agent.

## Quick Start

```bash
pi --model nvidia-nim/qwen/qwen3-coder-480b-a35b-instruct \
  -p @P:/path/to/file.py \
  "Read the file at @{path} carefully. Return JSON with score (0-1), summary (1 sentence), and issues. Begin your response with the exact first line of the file, quoted. If you did not read the file, set score to 0.0."
```

## Model Info

| Attribute | Value |
|-----------|-------|
| Model | qwen3-coder-480b-a35b-instruct |
| Provider | nvidia-nim |
| Context | 131.1K |
| Max Output | 32.8K |
| Thinking | yes |
| SWE-Bench | ~70.6% (related) |
| Strength | Repo/long-context specialist |

## API Key Setup

pi requires `NVIDIA_NIM_API_KEY` at startup. Export from auth.json:

```bash
NV_KEY=$(python -c "import json; d=json.load(open('$USERPROFILE/.pi/agent/auth.json')); print(d.get('nvidia',{}).get('key',''))")
export NVIDIA_NIM_API_KEY="$NV_KEY"
pi --model nvidia-nim/qwen/qwen3-coder-480b-a35b-instruct -p @P:/path/to/file.py "Read the file at @{path} carefully. Return JSON with score (0-1), summary (1 sentence), and issues. Begin your response with the exact first line of the file, quoted. If you did not read the file, set score to 0.0."
```

## Verification

```bash
pi --model nvidia-nim/qwen/qwen3-coder-480b-a35b-instruct -p @P:/path/to/file.py "Say hello"
```

If you get `429 status code` — rate limit hit. Wait 30s and retry.
