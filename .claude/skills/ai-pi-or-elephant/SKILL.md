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
  - Parse JSONL output for findings
  - Report score, issues, and synthesis
allowed_tools:
  - Bash
  - Read
---

# /ai-pi-elephant-alpha — Adversarial Review via Pi + Elephant Alpha

Run adversarial code review using **Elephant Alpha** (100B dense, 262K context, LiveBench coding 36%) via the **pi** multi-provider coding agent.

## Quick Start

```bash
pi --mode json --provider together --model elephant-alpha "Review P:/path/to/file.py and return JSON with score (0-1), summary, and issues list"
```

## Model Info

| Attribute | Value |
|-----------|-------|
| Model | elephant-alpha |
| Provider | together (Elephant Alpha hosted on Together) |
| Params | ~100B dense |
| Context | 262K |
| LiveBench Coding | 36% |
| Leaderboard | #13 |
| Strength | Real-world fit; leaderboard-proven |

## Verification

Run the verification ritual before first use:

```bash
pi --help | grep -E "(provider|model|mode)"
pi --mode json --provider together --model elephant-alpha "Say hello"
```

If you get `429 status code` — rate limit hit. Wait 30s and retry, or use `deepseek`/`claude` as fallback providers.