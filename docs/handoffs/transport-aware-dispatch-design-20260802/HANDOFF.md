---
thread_id: 019fa8f8-transport-dispatch-20260802
parent_handoff_path: P:/docs/handoffs/postsession-20260801/HANDOFF.md
current_session_id: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14
current_terminal_id: grok-main
produced_at: 2026-08-03T07:39:00-06:00
status: open
handoff_type: design
accurate_as_of_head: f7f8706
---

# Handoff: Transport-aware model dispatch — design doc

## 1. Objective

The design doc for transport-aware model dispatch is complete (3 review rounds
+ critical friend, 55 findings addressed) but lives in temp and will be reaped
by the OS. This handoff preserves the design decisions and implementation plan
so a future session can implement without re-deriving.

## 2. Status

OPEN — design complete, implementation not started. Design doc at:
`C:\Users\brsth\AppData\Local\Temp\grok-design-17eea2bf\grok-design-doc-17eea2bf.md`
(OS will reap — copy before closing if you want the full doc)

## 3. Producing context

The LLM orchestrator picks models and dispatches via spawn_subagent without
checking transport compatibility. 17 failure modes catalogued from transcript
evidence. The worst example: this session dispatched nemotron via spawn despite
the policy being in context.

The design went through 3 review rounds (55 findings, all addressed) + 1
critical friend round (10 findings, all addressed). The critical friend caught
over-engineering (HMAC receipts, 4-tier force system) and schema version
collision (fleet-models.json already declares version 2).

## 4. Core design decisions

1. **LLM stops picking models.** It provides a `task_profile` to
   `transport_router.dispatch_model()`. Code picks `(model, transport)`.
2. **`PreToolUse_spawn_model_gate.py` updated** to require a
   `dispatch_decision_receipt`. Direct spawns without one are blocked.
   `GROK_FORCE_SPAWN=1` is the escape hatch during migration.
3. **`fleet-models.json` schema v3** — each model gets a `transports` block
   with per-transport status, `verified_at`, `verified_via`.
4. **In-process audit log** (`dispatch_log.jsonl`) replaces HMAC approach.
5. **False-positive serde_broken reconciliation** — 4 models with stale
   serde_broken entries are moved to `status="working"` during migration.
6. **12 ordered implementation units** — schema migration → transport_router →
   pick_model_with_transport → gate enforcement → rollout.

## 5. Remaining work

### NEXT-1: Copy design doc to durable location

The design doc is at `C:\Users\brsth\AppData\Local\Temp\grok-design-17eea2bf\`.
Copy to `P:/docs/designs/transport-aware-dispatch-20260802.md` before OS reaps.

### NEXT-2: Implement Unit 1 (schema migration)

Convert `fleet-models.json` from v2 (lanes + serde_broken array) to v3
(per-model transports block). Includes false-positive reconciliation for
4 models with stale serde_broken entries.

### NEXT-3: Implement Unit 11 (M3 entry — MAY BE SKIPPED)

Unit 11 was supposed to add M3 to serde_broken based on the FM-18 misdiagnosis.
This was RETRACTED — M3 is not serde-broken. The transient-vs-serde classifier
fix (commit `40bce90`) resolves the root cause. Skip this unit.

## 6. Key corrections from critical friend

- **Dropped HMAC receipts** — LLM can bypass with force=True anyway. Replaced
  with in-process audit log.
- **Schema version is v3, not v2** — fleet-models.json already declares v2.
- **Collapsed force tiers from 4 to 2** — force_transport on DispatchRequest +
  operator_directive in registry.
- **Migration scope wider than stated** — pick_model referenced by 10+ files,
  not just 5 skills.
- **MiniMax case-sensitivity** — fix at source (`fleet_quota.py:708`), not via
  slug_aliases.

## 7. Source files

- Design doc: `C:\Users\brsth\AppData\Local\Temp\grok-design-17eea2bf\grok-design-doc-17eea2bf.md` (TEMP — will be reaped)
- Evidence brief: `C:\Users\brsth\AppData\Local\Temp\grok-design-17eea2bf\evidence-brief.md` (TEMP)
- Review: `C:\Users\brsth\AppData\Local\Temp\grok-design-17eea2bf\grok-design-review-17eea2bf.md` (TEMP)
- Critique: `C:\Users\brsth\AppData\Local\Temp\grok-design-17eea2bf\grok-design-critique-17eea2bf.md` (TEMP)

## Suggested next invocation

```
/go Copy the transport-aware dispatch design doc from C:\Users\brsth\AppData\Local\Temp\grok-design-17eea2bf\grok-design-doc-17eea2bf.md to P:/docs/designs/transport-aware-dispatch-20260802.md before OS reaps it. Then implement Unit 1 (schema migration): convert fleet-models.json from v2 to v3 with per-model transports blocks. Include false-positive reconciliation for 4 models with stale serde_broken entries. Verify: python fleet-models.json loads cleanly with new schema and all 9 active models have transports blocks.
```
