---
name: ai-pi-or-elephant
description: Adversarial review via pi using Elephant Alpha (100B dense, 262K context) - multi-provider coding agent dispatch
version: 1.0.0
enforcement: strict
triggers:
  - /ai-pi-elephant-alpha
  - /pi-elephant
  - adversarial review elephant
  - review with elephant-alpha
workflow_steps:
  - Parse target (file path or description)
  - Invoke pi dispatch_single with elephant model
  - Parse JSON output for findings
  - Report score, issues, and synthesis
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-elephant-alpha — Adversarial Review via Pi + Elephant Alpha

Run adversarial code review using **Elephant Alpha** (100B dense, 262K context, LiveBench coding 36%) via the **pi** multi-provider coding agent.

## Quick Start

```bash
pi --model openrouter/elephant-alpha \
  -p @P:/path/to/file.py \
  "Analyze for security vulnerabilities. Be adversarial. Return JSON with score (0-1), summary, and issues."
```

## Model Info

| Attribute | Value |
|-----------|-------|
| Model | elephant-alpha |
| Provider | openrouter |
| Context | 262K |
| Max Output | 32.8K |
| Thinking | no |
| LiveBench Coding | 36% |
| Strength | Real-world fit; leaderboard-proven |

## Verification

```bash
pi --model openrouter/elephant-alpha -p @P:/path/to/file.py "Say hello"
```

If you get `429 status code` — rate limit hit. Wait 30s and retry.
