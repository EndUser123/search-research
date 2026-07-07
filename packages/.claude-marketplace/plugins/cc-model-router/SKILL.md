---
name: cc-model-router
version: "0.2.16"
status: "active"
description: Automatic model-tier routing (haiku/sonnet/opus) based on prompt complexity heuristics
category: infrastructure
enforcement: advisory
workflow_steps:
  - name: Classify
    trigger: "UserPromptSubmit"
    description: "model_router_classify.py scores the prompt and writes recommendation.json"
  - name: Apply
    trigger: "UserPromptSubmit"
    description: "model_router_apply.py consumes the recommendation (advisory-only: marks consumed + audit-logs). CCR enforces routing; this hook never rewrites settings.json."
triggers:
  - autoswitch
  - model-router
aliases:
  - model-router
---

# cc-model-router

Automatic model-tier routing (haiku/sonnet/opus) based on prompt complexity heuristics.

## Features

- **Advisory-only operation**: classify writes recommendation.json + injects a systemMessage; apply marks consumed + audit-logs. CCR enforces routing; the plugin never rewrites settings.json.
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

### autoswitch (legacy — retained for audit history, not live-routing)

```json
{
  "action_mode": "autoswitch"
}
```

Historical behavior was: apply hook rewrites `settings.json["model"]` — that
path is now **non-functional** in production. CCR is the routing authority;
the apply hook only marks `recommendation.json` as consumed and appends an
audit row. See "Routing contract" below for the full authority split.

## Routing contract (read before reasoning about this plugin)

Hard fact from CC docs ([code.claude.com/docs/en/settings](https://code.claude.com/docs/en/settings)):

- CC reads `settings.json["model"]` **once at session start**. `model` is a
  documented hot-reload **exception** — edits apply on next restart, not
  mid-session. `/model` and `ANTHROPIC_MODEL` are the live mid-session
  controls (in-memory override / startup env), not the file.

CC vs CCR authority split (stable mental model):

- **CC** caches `model` at session start and sends it as `req.body.model` —
  a *label*, not the final route.
- **CCR** (Claude Code Router, `~/.claude-code-router/config.json`) is the
  per-request routing authority. It maps that label (and `default` /
  `background` / `think` / `longContext` slots, `longContextThreshold`) to a
  backend provider+model. A `CUSTOM_ROUTER_PATH` module runs before the
  default Router and can return a different route per request.
- Hooks (this plugin) produce **hints / config writes**, never an override
  of CCR's Router rules. If a hook writes a model CCR has no slot for, CCR's
  `default` slot decides — always work that gate question.

Design requirement for any same-turn autoswitch:

- Place the decision **at request time, inside CCR** (`CUSTOM_ROUTER_PATH`),
  not in a file CC only reads at startup. Treat hook outputs (tier hints,
  signal files) as **inputs to CCR's router function**, not standalone
  routing decisions.
- "Fast enough" = decision at `UserPromptSubmit`, effect on the **next**
  request CCR builds. Never propose mid-request swaps, and never claim
  "current turn" without source or a falsification test.

Two load-bearing **hypotheses** (unverified — require tests before any
"meets the goal" claim):

- **H-A:** CC never re-reads `settings.json["model"]` mid-session → the
  current apply path is inert for same-turn routing.
- **H-B:** CCR invokes `CUSTOM_ROUTER_PATH` on every request **including
  intra-turn tool-call round-trips** (not once-per-turn with a cached
  result). If CCR caches the route per turn, a persistent "background" hint
  poisons every tool call in the turn (STATE-3 turn-poisoning).

Falsification tests (gates — no success claim until these run):

1. **Settings cadence (H-A):** set `MODEL_ROUTER_APPLY_DRY_RUN=1` for ≥3
   sessions; join `apply_audit.jsonl` (`new_model`) against CCR's request
   log (the model actually routed). Match → write reaches the turn;
   mismatch → inert, apply path must move into CCR.
2. **CCR cadence (H-B):** add an entry counter to `ccr-custom-router.js`'s
   `router()`; confirm per-turn `router()` call count equals per-turn
   request count. If fewer, CCR caches per turn and the hint must be
   consume-once-per-prompt (unlink-after-read) inside the router.

Current code is **non-compliant with the same-turn goal** until
`ccr-custom-router.js` v2 (hint-read + tier→provider map +
consume-on-read) exists and both tests pass. Audit log:
`.claude/state/model-router/apply_audit.jsonl`.

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
