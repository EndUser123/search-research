---
thread_id: dispatch-paths-fallback-019fc95d
parent_handoff_path: docs/handoffs/model-benchmark-dispatch-019fc95d/HANDOFF.md
current_session_id: 019fc95d-8132-7181-a6f4-9ab6d1624cd5
current_terminal_id: noterm
produced_at: 2026-08-05T20:35:00Z
last_updated_by: 019fc95d-8132-7181-a6f4-9ab6d1624cd5
last_updated_at: 2026-08-05T20:35:00Z
status: open
handoff_type: investigation
accurate_as_of_head:
  P: 8b05bae
  grok: 08e3ac5
---

# Handoff: dispatch_paths fallback — don't block models from pool when only spawn is broken

## Objective

Revert the `tool_grounded_spawn_broken` pool-exclusion in `pick_model.py` so that models known to fail tool-grounded spawn_subagent stay in the selection pool and use `dispatch_paths` to fall back to PI/OC/HTTP instead of being blocked entirely.

## Status

OPEN — critical design fix identified by operator, not yet implemented. The `tool_grounded_spawn_broken` list was committed (commit `6f38320`) and currently blocks 3 models from all lanes in `pick_model.py`.

## Producing context

- Date: 2026-08-05
- Session: `019fc95d-8132-7181-a6f4-9ab6d1624cd5`
- Terminal: noterm
- Parent handoff: `model-benchmark-dispatch-019fc95d`

## Background — why this matters

### The problem

The critic lane in `fleet-models.json` has 3 models:
1. `zen-deepseek-v4-flash-free` — spawn-broken per tool-fallbacks wiki (serde error on tool-grounded prompts)
2. `nim-deepseek-ai-deepseek-v4-flash` — spawn-broken, AND in `tool_grounded_spawn_broken` list → blocked from pool
3. `nim-openai-gpt-oss-20b` — verified working for spawn → the only model pick_model returns

After the tool-fallbacks update (commit `70479f9`), both DeepSeek variants are documented as spawn-broken for tool-grounded work. But `pick_model.py`'s `is_available()` returns `False` for models in the `tool_grounded_spawn_broken` list, which means they're excluded from the pool entirely — even though they work perfectly via PI, OpenCode, and HTTP transports.

### Operator's directive (verbatim)

> "The critic lane in fleet-models.json has 3 models: zen-deepseek-v4-flash-free, nim-deepseek-ai-deepseek-v4-flash, nim-openai-gpt-oss-20b. After the tool-fallbacks update this session, both zen-deepseek and nim-deepseek are documented as spawn-broken for tool-grounded work. That leaves nim-openai-gpt-oss-20b as the only verified spawn model in the critic lane. Risk #2 is confirmed as real."
>
> "but we have PI, so why limit ourselves to spawn?"

### The correct design

The model works — the spawn transport doesn't. `dispatch_paths` already exists in fleet-models.json for exactly this purpose: `["spawn", "PI", "HTTP", "OC"]`. The `tool_grounded_spawn_broken` list should be **transport metadata** (tells callers "skip spawn, try PI first"), not a **pool-exclusion filter** (blocks the model entirely).

## Read-first list

1. `~/.grok/skills/model-quota/scripts/pick_model.py` — the `is_available()` function at line ~98 that currently blocks tool_grounded_spawn_broken models
2. `~/.grok/skills/model-quota/scripts/fleet-models.json` — the `tool_grounded_spawn_broken` list (top-level + derived_views) and per-model `dispatch_paths`
3. `~/.grok/skills/tp/SKILL.md` — the spawn lens Step that uses pick_model.py output
4. `~/.grok/hooks/PreToolUse_spawn_model_gate.py` — the spawn gate hook (does NOT currently use dispatch_path — this is fine; the fallback belongs in the caller)
5. `P:/.data/wiki/concepts/tool-fallbacks.md` — documents which models are spawn-broken
6. `P:/.data/wiki/concepts/dedicated-quota-first-dispatch-routing.md` — the dispatch_paths design rationale

## Verified facts

- [FACT] `pick_model.py` `is_available()` returns `False, "tool-grounded-spawn-broken"` for models in the list (pick_model.py line ~113-115, read 2026-08-05)
- [FACT] `fleet-models.json` has `tool_grounded_spawn_broken: ["nvidia-nemotron-3-ultra", "nim-deepseek-ai-deepseek-v4-flash", "nim-deepseek-ai-deepseek-v4-pro"]` (both top-level and derived_views)
- [FACT] `pick_model.py critic --exclude-self --json` returns `zen-deepseek-v4-flash-free` (NOT in tool_grounded_spawn_broken list) with `nim-deepseek-ai-deepseek-v4-flash` as fallback marked `available: false, reason: tool-grounded-spawn-broken` (verified 2026-08-05)
- [FACT] `zen-deepseek-v4-flash-free` is NOT in the `tool_grounded_spawn_broken` list despite being documented as spawn-broken in tool-fallbacks.md — the list is incomplete
- [FACT] `PreToolUse_spawn_model_gate.py` does not reference `dispatch_path` or `dispatch_paths` at all — it validates model availability pre-spawn, doesn't handle transport fallback
- [FACT] commit `6f38320` added the `tool_grounded_spawn_broken` list and the `is_available()` block

## Current state

**What's in place:**
- `dispatch_paths` chains exist for every model in fleet-models.json
- `pick_model.py` returns `dispatch_paths` as a list alongside the single `dispatch_path`
- The `tool_grounded_spawn_broken` list is populated with 3 models
- `/tp` spawn lens uses `pick_model.py critic --exclude-self` dynamically

**What's wrong:**
- `is_available()` treats `tool_grounded_spawn_broken` as a hard exclusion (returns False) — models can't be selected at all
- The caller has no way to say "give me the model anyway, I'll try PI instead of spawn"
- `zen-deepseek-v4-flash-free` should also be in the list (it's documented as spawn-broken in tool-fallbacks.md) but isn't

## Task packets

### DP-01: Remove tool_grounded_spawn_broken from is_available() exclusion

- **goal:** Stop blocking models from the pool when only spawn_subagent is broken; keep the list as metadata
- **in scope:** `pick_model.py` `is_available()` function — remove the `tool_grounded_spawn_broken` check that returns False
- **out of scope:** changes to fleet-models.json structure (the list stays), changes to callers
- **files / anchors:** `~/.grok/skills/model-quota/scripts/pick_model.py` lines ~100-115 (the tool_grounded_spawn_broken block in is_available)
- **acceptance:** `pick_model.py critic --exclude-self --json` returns `nim-deepseek-ai-deepseek-v4-flash` as available when it's the best tier match; `tool_grounded_spawn_broken` models show `available: true` but with a `spawn_broken: true` or `spawn_limitation` field
- **falsifier:** `pick_model.py critic --json` still excludes models in the `serde_broken` or `learned_broken` sets (those are real hard exclusions); only `tool_grounded_spawn_broken` stops being a hard exclusion
- **verification level required:** UNIT_TEST — run `pytest test_pick_model.py -v` (16 tests must pass)
- **estimate:** 15 min

### DP-02: Add spawn_limitation field to pick_model output

- **goal:** When a model is in `tool_grounded_spawn_broken`, surface this in the pick_model output as a `spawn_limitation` field so callers know to skip spawn and try the next dispatch_path
- **in scope:** `pick_model.py` result construction — add `spawn_limitation: "tool-grounded-spawn-broken"` (or null) to the returned dict
- **out of scope:** changes to how callers consume the field (that's DP-03)
- **files / anchors:** `pick_model.py` pick_model() return dict construction
- **acceptance:** JSON output includes `spawn_limitation` field for tool_grounded_spawn_broken models, null for others
- **falsifier:** a model NOT in the list shows `spawn_limitation: null`
- **verification level required:** UNIT_TEST
- **estimate:** 10 min

### DP-03: /tp spawn lens uses dispatch_paths fallback

- **goal:** When `/tp` dispatches a spawn lens and the model has `spawn_limitation: "tool-grounded-spawn-broken"`, skip spawn_subagent and use PI (`pi -p`) or the next dispatch_path instead
- **in scope:** `/tp` SKILL.md Step 2 spawn lens dispatch logic, or the `tp_dispatch.py` script if it handles dispatch
- **out of scope:** other skills that use pick_model (/go, /check) — they'll benefit from DP-01/02 but don't need per-skill changes for this handoff
- **files / anchors:** `~/.grok/skills/tp/SKILL.md` Step 2, `~/.grok/skills/tp/__lib/tp_dispatch.py` (if it exists)
- **acceptance:** /tp critic with a tool_grounded_spawn_broken model in the critic lane successfully returns a critique via PI instead of failing via spawn
- **falsifier:** /tp still tries spawn_subagent for a tool_grounded_spawn_broken model and gets the serde error
- **verification level required:** LIVE_BEHAVIOR — test with actual /tp invocation
- **estimate:** 30 min

### DP-04: Add zen-deepseek to tool_grounded_spawn_broken list

- **goal:** Ensure the list is complete — zen-deepseek-v4-flash-free is documented as spawn-broken in tool-fallbacks.md but not in the list
- **in scope:** `fleet-models.json` `tool_grounded_spawn_broken` array (both top-level and derived_views)
- **out of scope:** pick_model.py logic (DP-01 handles that)
- **files / anchors:** `fleet-models.json` lines ~1121 and ~2070
- **acceptance:** After DP-01, pick_model shows zen-deepseek with `spawn_limitation: "tool-grounded-spawn-broken"` in JSON output
- **falsifier:** zen-deepseek shows `spawn_limitation: null` (would mean it's not in the list)
- **verification level required:** STATIC_INSPECTION
- **estimate:** 5 min

## Open decisions

### Should callers auto-fallback or should pick_model prefer non-broken models?

The two design options:

1. **pick_model prefers non-broken spawn models** — when selecting from a lane, models with `spawn_limitation` are ranked lower than those without. If a working-spawn model exists, it's selected first. Tool_grounded_spawn_broken models are fallback only. (Current behavior with the exclusion, but soft preference instead of hard block.)

2. **pick_model returns best model regardless, caller handles fallback** — pick_model doesn't care about spawn_limitation for selection; the caller reads `spawn_limitation` and `dispatch_paths` to decide transport. More flexible but requires every caller to be smart.

**Selection criterion:** minimal caller complexity. **Currently leaning toward option 1** (soft preference) — it's the smaller change from current behavior and doesn't require every caller to be rewritten. The `spawn_limitation` field is still surfaced for callers that want to use it explicitly.

**What would change the lead:** if callers need to select transport dynamically based on prompt characteristics (not just spawn availability), option 2 is more general.

## Hard constraints

1. **serde_broken and learned_broken stay as hard exclusions** — those models genuinely cannot produce output at all. Only `tool_grounded_spawn_broken` changes from hard to soft.
2. **dispatch_paths chains must be correct** — the fallback only works if `dispatch_paths` accurately reflects which transports the model works on. Verify before relying on it.
3. **No hardcoded model slugs** — the /tp lens must stay dynamic (pick_model.py critic --exclude-self). The fix is in the infrastructure, not in hardcoding a "known good" model.

## Cross-reference couplings

- `fleet-models.json` `tool_grounded_spawn_broken` list → read by `pick_model.py` `is_available()`. If the list changes, the filtering logic must match.
- `pick_model.py` output → consumed by `/tp` SKILL.md spawn lens, `/go` dispatch, spawn gate hook. Changes to the output shape affect all consumers.
- `P:/.data/wiki/concepts/tool-fallbacks.md` → documents which models are spawn-broken. Should stay in sync with the `tool_grounded_spawn_broken` list in fleet-models.json.
- Parent handoff `model-benchmark-dispatch-019fc95d` Revision 3 → names this handoff as remaining work item #1.

## Other outstanding streams (not handed off)

- **Multi-method quality benchmarking** — design section in benchmark SKILL.md, not implemented. Belongs in parent handoff scope.
- **Spawn gate hook** (`PreToolUse_spawn_model_gate.py`) — does not use dispatch_path. If we want automatic transport fallback at the hook level (not just caller level), the hook needs updating. Deferred — caller-level fallback (DP-03) is sufficient for now.
- **Unpushed ~/.grok commit** — `08e3ac5` not yet pushed. Operator decision.

## Explicit non-goals

- Do NOT remove the `tool_grounded_spawn_broken` list from fleet-models.json — it's useful metadata. Only the `is_available()` hard-exclusion is being removed.
- Do NOT implement a hook-level transport fallback — that's a larger change. The fix is in pick_model + callers.
- Do NOT hardcode model slugs as a workaround. The /tp lens must stay dynamic.

## Resumption protocol

1. Read `pick_model.py` `is_available()` (line ~98-120)
2. Remove the `tool_grounded_spawn_broken` check that returns False (DP-01)
3. Add `spawn_limitation` field to pick_model output (DP-02)
4. Add soft preference: rank tool_grounded_spawn_broken models lower in selection (if option 1 chosen)
5. Add `zen-deepseek-v4-flash-free` to the list (DP-04)
6. Run `pytest test_pick_model.py -v` — all 16 tests must pass
7. Update `/tp` SKILL.md to use dispatch_paths fallback when spawn_limitation is set (DP-03)

## Suggested next invocation

```
/go implement DP-01 through DP-04 from P:/docs/handoffs/dispatch-paths-fallback-not-spawn-block-20260805/HANDOFF.md
```

## Last user message (verbatim)

> "The critic lane in fleet-models.json has 3 models: zen-deepseek-v4-flash-free, nim-deepseek-ai-deepseek-v4-flash, nim-openai-gpt-oss-20b. After the tool-fallbacks update this session, both zen-deepseek and nim-deepseek are documented as spawn-broken for tool-grounded work. That leaves nim-openai-gpt-oss-20b as the only verified spawn model in the critic lane. Risk #2 is confirmed as real."
>
> "but we have PI, so why limit ourselves to spawn?"

## Epistemic labels

- [FACT] The `tool_grounded_spawn_broken` list currently blocks 3 models from pick_model (verified via JSON output, 2026-08-05)
- [FACT] `dispatch_paths` chains exist for all models in fleet-models.json (verified via JSON output)
- [FACT] `zen-deepseek-v4-flash-free` is missing from the list despite being spawn-broken per tool-fallbacks.md (verified via grep)
- [INFERENCE] Option 1 (soft preference) is the minimal-change path — it requires only removing the hard exclusion and adding a sort key
- [UNKNOWN] Whether callers other than /tp need updating — /go and /check also use pick_model but may not need transport fallback if they don't spawn tool-grounded prompts

## Suggested skills for next session

- `/go` — 4 task packets ready to execute (3 code changes + 1 data update)
- `/check` — verify pick_model output shape didn't break consumers after DP-01/02
- `/tp` — test the dispatch_paths fallback with a real critic invocation (DP-03 acceptance)

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-05T20:35 | 019fc95d-8132-7181-a6f4-9ab6d1624cd5 | created — spun off from model-benchmark-dispatch-019fc95d Revision 3 |
