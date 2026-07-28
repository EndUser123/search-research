---
thread_id: 93d08b55-1f1e-4d76-a1c8-186730432440
parent_handoff_path: P:/docs/handoffs/auto-model-switch-on-rate-limit-20260728/HANDOFF.md
current_session_id: 019fa94d-5608-7b21-b8d7-dbe609f92df3
current_terminal_id: console_38b8d474-5cd0-4bf1-a306-6a77
produced_at: 2026-07-28T17:45:00Z
status: open
handoff_type: implementation
accurate_as_of_head: a622490
---

# AMS-02: Shared spawn_subagent pool helper

## Objective

Build one reusable Python helper that `/tp`, `/check`, `/review`, and `/go` call to spawn subagents with **automatic try-next-model on 429/401/serialization/empty** — no user intervention required for children when one model is rate-limited.

## Status

OPEN — not started; design clear from parent handoff.

## Read-first list

1. `P:/docs/handoffs/auto-model-switch-on-rate-limit-20260728/HANDOFF.md` — role matrix (M3 deny for parent; spawn-OK for children)
2. `C:/Users/brsth/.grok/skills/tp/SKILL.md` Step 2 — pool prose (try glm → mimo → parent → inline)
3. `C:/Users/brsth/.grok/tool-fallbacks.md` — known-broken slugs + spawn compatibility
4. `P:/.agents/scripts/log_spawn.py` — telemetry (extend with `--failure-reason`)
5. `P:/.data/wiki/concepts/model-pool-not-chain.md`
6. `P:/.data/wiki/concepts/model-tool-calling-capability-matrix.md`

## Verified facts

- [FACT] `/tp` Step 2 already describes pool-before-inline but has **no mechanical helper** — relies on orchestrator obeying prose under pressure.
- [FACT] `spawn_subagent` compatible slugs verified in tool-fallbacks.md (glm-5-2, go-mimo-v2-5, parent-inherited; NOT nemotron/kimi via spawn).
- [FACT] 8 serialization errors this session (transcript scan) — pool try-next would have helped.
- [FACT] `log_spawn.py` exists but does not capture failure reason.

## Task packets

### POOL-01 — spawn_pool.py helper

- **goal:** `P:/.agents/scripts/spawn_pool.py` that takes (prompt, pool_list, role) → tries each model → returns first success → logs all failures.
- **in scope:** the helper script + `log_spawn.py --failure-reason` extension.
- **out of scope:** parent-session auto-switch (AMS-03); wiring all skills (separate PR per skill).
- **acceptance:**
  1. Helper script works with a 2-model pool where first returns simulated error.
  2. Failure log captures: slug, error_type, timestamp, caller.
  3. Returns content from second model.
- **falsifier:** first model 429 → immediate inline without trying peer.
- **verification level required:** UNIT_TEST + LIVE_BEHAVIOR

### POOL-02 — Wire /tp Step 2 to use helper

- **goal:** Replace pool prose in `/tp` SKILL.md with "call spawn_pool.py."
- **acceptance:** /tp spawn path goes through helper; Step 3 disclosure cites which model ran.
- **risk_of_change:** M

### POOL-03 — Wire /check + /review spawns to use helper

- **goal:** Same wiring for `/check` verifiers and `/review` specialists.
- **acceptance:** both skills' spawn paths go through helper.
- **risk_of_change:** M

## Hard constraints

- Role gate: spawn pool may include M3 for doc/mechanical roles; **never** auto-parent.
- go-kimi-k3 / nemotron NOT in auto-pool (operator policy).
- Soft-fail logging (non-blocking).
- Pool order: free-first, then subscription, then parent-inherited last (per model-pool policy).

## Suggested next invocation

```text
Read P:/docs/handoffs/spawn-pool-helper-ams02-20260728/HANDOFF.md.
Implement POOL-01: spawn_pool.py + extend log_spawn.py with --failure-reason.
Smoke: 2-model pool where first fails, second succeeds.
```
