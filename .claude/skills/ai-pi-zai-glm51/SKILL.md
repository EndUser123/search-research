---
name: ai-pi-zai-glm51
description: Adversarial review via pi using Z.ai GLM-5.1 (131K context) - multi-provider coding agent dispatch
version: 1.0.0
enforcement: strict
triggers:
  - /ai-pi-zai-glm51
  - /pi-zai-glm51
  - adversarial review glm
  - review with glm-5.1
workflow_steps:
  - Parse target (file path or description)
  - Invoke pi dispatch_single with zai-glm51 model
  - Parse JSONL output for findings
  - Report score, issues, and synthesis
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-zai-glm51 — Adversarial Review via Pi + Z.ai GLM-5.1

Run adversarial code review using **GLM-5.1** via the **zai** provider on pi multi-provider coding agent.

## Quick Start

```bash
pi --model z-ai/glm-5.1 \
  -p @P:/path/to/file.py \
  "Analyze for security vulnerabilities. Be adversarial. Return JSON with score (0-1), summary, and issues."
```

## Model Info

| Attribute | Value |
|-----------|-------|
| Model | GLM-5.1 |
| Providers | z-ai (direct), openrouter (zai) |
| Context | 131.1K |
| Strength | Code generation, reasoning, long context |

## Verification

```bash
# Verify which model will be used
pi --model z-ai/glm-5.1 --list-models

# Quick smoke test
pi --model z-ai/glm-5.1 -p @P:/path/to/file.py "Say hello"
```

If you get `429 status code` — rate limit hit. Wait 30s and retry.
