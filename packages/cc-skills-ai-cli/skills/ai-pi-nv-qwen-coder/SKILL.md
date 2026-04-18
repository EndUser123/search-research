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
  - Parse JSONL output for findings
  - Report score, issues, and synthesis
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-qwen3-coder-480b — Adversarial Review via Pi + Qwen3 Coder 480B A35B

Run adversarial code review using **Qwen3 Coder 480B A35B** (35B MoE, 262K context) via the **pi** multi-provider coding agent.

## Quick Start

```bash
pi --mode json --provider nvidia-nim --model qwen/qwen3-coder-480b-a35b-instruct "Review P:/path/to/file.py and return JSON with score (0-1), summary, and issues list"
```

## Model Info

| Attribute | Value |
|-----------|-------|
| Model | qwen/qwen3-coder-480b-a35b-instruct |
| Provider | nvidia-nim |
| Context | 262K |
| SWE-Bench | ~70.6% (related) |
| Strength | Repo/long-context specialist |

## Verification

```bash
pi --mode json --provider nvidia-nim --model qwen/qwen3-coder-480b-a35b-instruct "Say hello"
```

If you get `429 status code` — rate limit hit. Wait 30s and retry.