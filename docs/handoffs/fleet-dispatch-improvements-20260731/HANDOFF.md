---
# Handoff chain header
current_session_id: 019fb926-211b-79a3-966d-a4e891b7c89d
produced_at: 2026-07-31T23:30:00Z
accurate_as_of_head: 75ab94066af257c54c66811f5cfe393f8b119412
source_transcript: ~/.grok/sessions/P%3A%5C/019fb926-211b-79a3-966d-a4e891b7c89d/chat_history.jsonl
status: open
work_status: READY_FOR_IMPLEMENTATION
---

# Handoff: Fleet model dispatch improvements — graduated quota floor + PreCompact capture hook

## Objective

Two deferred improvements from session 019fb926, each with NEXT_ACTION_PACKETs
already in `P:/.data/harvest/pending/`. Both are `/go`-sized tasks with
designs ready.

## Acceptance criteria

1. **Q5 — Graduated quota floor:** `fleet-models.json` has per-lane `quota_floor`
   fields; `PreToolUse_spawn_model_gate.py` reads the per-lane floor instead of
   the global `QUOTA_THRESHOLD = 10`; mechanical lane floor = 30% (conserve
   subscription quota for higher-value lanes); gate tests pass.
2. **Q6 — PreCompact improvement-capture hook:** `PreCompact_improvement_capture.py`
   fires before compaction, scans transcript for uncaptured friction/correction
   patterns, injects count into compaction context if ≥3; registered via
   `improvement-capture-precompact.json`.

## Read first

- **Design doc:** `P:/docs/designs/2026-07-30-quota-aware-model-routing.md` — the
  three-layer quota system this extends (Layers 1-3). Q5 extends Layer 2.
- **NEXT_ACTION_PACKETs:** `P:/.data/harvest/pending/next-action-precompact-hook.json`
  (Q6) and `P:/.data/harvest/pending/tp-session-019fb926.json` (Q5 item).
- **Spawn gate code:** `~/.grok/hooks/PreToolUse_spawn_model_gate.py` — the file
  Q5 modifies (line 23: `QUOTA_THRESHOLD = 10`; lines 96-107: lane lookup already
  exists in `get_fallback_for_lane`).
- **Gate tests:** `~/.grok/hooks/test_PreToolUse_spawn_model_gate.py` — must pass
  after Q5 changes.
- **fleet-models.json:** `~/.grok/skills/model-quota/scripts/fleet-models.json` —
  the registry Q5 extends with per-lane `quota_floor` fields.
- **PreCompact precedent:** `~/.grok/hooks/quota-cache-precompact.json` — existing
  PreCompact hook pattern Q6 follows.
- **/notice T10:** `~/.grok/skills/notice/SKILL.md` — T10 trigger (already shipped
  this session) is the mid-session complement to Q6's compaction-boundary hook.
- **Related wiki:** `[[intent-mode-gated-auto-composition]]`,
  `[[router-proxy-tool-calling-normalization-patterns]]`,
  `[[model-tool-calling-capability-matrix]]`

## What was discovered this session

1. **The three-layer quota system already exists and is active** (Layers 1-3:
   UserPromptSubmit injector, PreToolUse spawn gate, PostToolUseFailure error
   learner). Q5 extends Layer 2 with per-lane thresholds.
2. **The spawn gate has a single global threshold** (`QUOTA_THRESHOLD = 10`).
   Mechanical-lane dispatches to subscription models (go-mimo-v2-5) burn quota
   that should be conserved for coding/reasoning lanes.
3. **Quota pools are per-provider** (`opencode-go`, `zai`, `minimax`), not
   per-model — verified from the quota cache structure. So per-lane floors
   correctly map to provider quota.
4. **Latency data is mineable from transcripts** via `extract_spawn_latency.py`
   (107 spawns, 23 sessions). High-variance models: ccr-ornith (557s avg, 353s
   stdev), glm-5-2 (177s avg, 656s max). A latency circuit breaker is a potential
   future extension but not in scope for Q5/Q6.

## What was done

| Item | Status | Commit |
|------|--------|--------|
| Injector mtime short-circuit | ✅ Shipped | `714f7b1` |
| Pool quota-check Step 0 (all 4 pools) | ✅ Shipped | `adef081` |
| extract_spawn_latency.py | ✅ Shipped | `adef081` |
| /notice T10 trigger | ✅ Shipped | `7bfc35e` |
| Hook efficiency checklist in 10-hooks.md | ✅ Shipped | `cbde201` |
| Wiki: router-proxy normalization | ✅ Shipped | `94c471a` |
| Wiki: intent-mode auto-composition | ✅ Shipped | `94c471a` |
| Wiki: overclaiming under pressure | ✅ Shipped | `75ab940` |
| Q5 graduated quota floor | ❌ Deferred | — |
| Q6 PreCompact hook | ❌ Deferred | — |
| /codex SKILL.md baseline stale | ❌ Minor | — |

## Open items / next steps

### Q5 — Graduated quota floor per lane

1. Add `quota_floor` to each lane in `fleet-models.json`:
   ```json
   "mechanical": { "quota_floor": 30, ... }
   "coding":     { "quota_floor": 10, ... }
   "reasoning":  { "quota_floor": 10, ... }
   "critic":     { "quota_floor": 15, ... }
   ```
2. Modify `PreToolUse_spawn_model_gate.py` line 23: replace global
   `QUOTA_THRESHOLD = 10` with per-lane lookup. The lane is already determined
   at gate-check time (lines 96-107, `get_fallback_for_lane`).
3. Run `test_PreToolUse_spawn_model_gate.py` — must pass.
4. Run `/review` (touches dispatch chain per AGENTS.md).

### Q6 — PreCompact improvement-capture hook

1. Write `~/.grok/hooks/PreCompact_improvement_capture.py`:
   - Scan `chat_history.jsonl` for exit≠0, Traceback, Hook denied, correction patterns
   - Count uncaptured items (not followed by /capture, /harvest, /wiki, handoff)
   - If count ≥3, inject `additionalContext` into compaction context
2. Register via `~/.grok/hooks/improvement-capture-precompact.json`
3. Follow the existing PreCompact pattern (quota-cache-precompact.json)

**Assumptions to verify:**
- PreCompact hooks can inject `additionalContext` (confirmed this session via
  `10-hooks.md` — PreCompact fires before compaction, can inject context,
  cannot block)
- `chat_history.jsonl` is accessible at PreCompact time (likely yes — the
  transcript hasn't been compacted yet)

## Decisions made this session

1. **Pool quota-check at decision point (operator's idea):** put the quota
   check in the pool Procedure section, not in a behavioral reminder or
   per-skill integration. The pool is the authoritative source skills read.
2. **Intent-mode-gated auto-composition:** auto-route within same intent mode;
   operator-gate at research→implementation boundary. NEXT_ACTION_PACKET as
   structural fix for manual skill-to-skill routing.
3. **Latency circuit breaker deferred:** no data showed it was needed until
   transcript mining revealed it. Now data exists (107 spawns); build if
   variance proves problematic in practice.
4. **/notice T10 for uncaptured-accumulation:** surfaces (informational), doesn't
   auto-fire /capture (would cross work-mode to review-mode without consent).

## Evidence

- AAR report: `P:/.artifacts/grok-aar/console_console_95317f7f-6665-4f25-9918-5c70/session-019fb926/aar-report.md`
- Latency benchmarks: `~/.cache/opencode/spawn-latency-benchmarks.json`
- Spawn gate code: `~/.grok/hooks/PreToolUse_spawn_model_gate.py:23` (QUOTA_THRESHOLD)
- NEXT_ACTION_PACKETs: `P:/.data/harvest/pending/`

## Last user message (verbatim)

```
/handoff
```

## Other outstanding streams

- **/codex SKILL.md baseline stale:** line 480 says `model = "gpt-5.6-luna"` but
  actual config shows `model = "gpt-5.6-sol"`. One-line fix. No handoff needed —
  AAR report flags it as open.

## Falsifier

This handoff is wrong if:
- The graduated quota floor proves unnecessary (free-tier models are always
  available and sufficient for mechanical work — the floor would then block
  working models without conserving anything useful)
- The PreCompact hook's transcript scan is too slow (fires at compaction time;
  if scanning chat_history.jsonl takes >5s, it could delay compaction)
- The quota-pool model is wrong (if pools are per-model not per-provider, the
  per-lane floor mechanism is incorrect and should be per-model)

## Cross-reference couplings

- Session AAR: `P:/.artifacts/grok-aar/console_console_95317f7f-6665-4f25-9918-5c70/session-019fb926/aar-report.md`
- Session ship receipt: `/ship` run this session (SHIP DONE, both repos on main)
- Wiki concepts: `router-proxy-tool-calling-normalization-patterns.md`,
  `intent-mode-gated-auto-composition.md`,
  `overclaiming-under-exploration-to-recommendation-pressure.md`

---

## Revision 1 — 2026-08-01 (session 019fb177)

**Context:** Post-compaction continuation session built tp_dispatch.py, parallel lens panel, and --detail flag — all of which touch the fleet dispatch surface this handoff covers.

**What shipped that supersedes parts of this handoff:**

| Item | Status | Note |
|------|--------|------|
| /codex SKILL.md baseline stale (gpt-5.6-luna vs gpt-5.6-sol) | **Superseded** — Luna price drop (80%) and parallel panel work updated the cascade. The model reference in tp_dispatch.py defaults to `gpt-5.6-luna`. Operator confirmed Luna is correct. |
| Q5 graduated quota floor | **Still deferred** — not touched this session |
| Q6 PreCompact hook | **Still deferred** — not touched this session |
| Parallel panel replaces cascade | **Shipped** (commit `62fb4c7`) — the cascade this handoff's "model cascade" section describes has been replaced with parallel dispatch. The fleet-dispatch improvements (Q5, Q6) are still relevant for the spawn pool lane but the overall architecture is now parallel-first. |

**New handoffs that cover post-compaction fleet work:**
- `tp-parallel-panel-dispatch-20260801` — tp_dispatch.py, parallel panel, --detail flag, agy wrapper
- `premature-recommendation-pattern-20260801` — behavioral pattern related to agy dispatch
