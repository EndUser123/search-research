---
name: cc-model-router
version: "0.2.0"
status: "stable"
description: Automatic model-tier routing (haiku/sonnet/opus) based on prompt complexity heuristics
category: infrastructure
enforcement: advisory
workflow_steps:
  - name: Classify
    trigger: "UserPromptSubmit"
    description: "model_router_classify.py scores the prompt and writes recommendation.json"
  - name: Apply
    trigger: "UserPromptSubmit"
    description: "model_router_apply.py consumes the recommendation and rewrites settings.json before the next response is generated (v0.2.0+)"
triggers:
  - autoswitch
  - model-router
aliases:
  - model-router
---

# cc-model-router

Automatic model-tier routing (haiku/sonnet/opus) based on prompt complexity heuristics.

## Features

- **Dual-mode operation**: warn (systemMessage injection) or autoswitch (exit 2 + atomic settings.json write)
- **Config walk-up**: plugin-level, global user-level, project-level override
- **Terminal+session scoped state** at `.claude/state/model-router/`
- **Python-only hooks** per ARCH-002

## Usage

### warn mode (default)

```json
{
  "action_mode": "warn"
}
```

SystemMessage injected into prompt when complexity threshold exceeded.

### autoswitch mode

```json
{
  "action_mode": "autoswitch"
}
```

UserPromptSubmit apply hook (v0.2.0+) rewrites `settings.json` before
generation, so the new model is in effect for the **current** turn.
Autoswitch is handled entirely in that apply step.

Set `MODEL_ROUTER_APPLY_DRY_RUN=1` in the environment to log the would-be
switch to `apply_audit.jsonl` without touching `settings.json`. Use this
for 3+ sessions to verify the harness actually picks up the per-turn
rewrite (the falsification test the design identifies) before flipping
to live mode.

Audit log: `.claude/state/model-router/apply_audit.jsonl`

## Configuration

Place `claude-model-router.json` at:
1. Plugin level (default)
2. User level: `~/.claude/hooks/`
3. Project level: `.claude/hooks/` (highest priority)

## Tiers

| Tier | max_lines | max_file_size | max_tools |
|------|-----------|---------------|-----------|
| haiku | 100 | 10 | 5 |
| sonnet | 500 | 50 | 20 |
| opus | unlimited | unlimited | unlimited |

## State Files

State path: `.claude/state/model-router/{terminal_id}/{session_id}/recommendation.json`

TTL: 300 seconds. Fail-open ordering.
