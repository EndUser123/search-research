---
name: ai-pi-mm-m27
description: Adversarial review via pi using MiniMax M2.7 (10B MoE, 197K context) - multi-provider coding agent dispatch
version: 1.0.0
enforcement: strict
triggers:
  - /ai-pi-minimax-m27
  - /pi-minimax
  - adversarial review minimax
  - review with minimax-m2.7
workflow_steps:
  - Parse target (file path or description)
  - Invoke pi dispatch_single with minimax model
  - Parse JSON output for findings
  - Report score, issues, and synthesis
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-minimax-m27 — Adversarial Review via Pi + MiniMax M2.7

Run adversarial code review using **MiniMax M2.7** (10B MoE, 197K context) via the **pi** multi-provider coding agent.

## Quick Start

```bash
pi --model minimax/MiniMax-M2.7 \
  -p @P:/path/to/file.py \
  "Analyze for security vulnerabilities. Be adversarial. Return JSON with score (0-1), summary, and issues."
```

## Model Info

| Attribute | Value |
|-----------|-------|
| Model | MiniMax-M2.7 |
| Provider | minimax |
| Context | 1M |
| Max Output | 8.2K |
| Thinking | no |
| SWE-Bench | 80.2% |
| Strength | Office/coding fluency, 51% Multi-SWE |

## Verification

```bash
pi --model minimax/MiniMax-M2.7 -p @P:/path/to/file.py "Say hello"
```

If you get `429 status code` — rate limit hit. Wait 30s and retry.
