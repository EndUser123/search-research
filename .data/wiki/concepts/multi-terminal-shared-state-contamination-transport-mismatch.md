---
title: "Multi-terminal shared-state contamination: concurrent session cleared serde_broken list based on wrong transport"
created: 2026-08-02
source: session-019fa8f8
tags: [multi-terminal, shared-state, concurrent-session, contamination, serde_broken, fleet-models, transport-mismatch, rollback, race-condition]
summary: >
  A concurrent session cleared the serde_broken list in fleet-models.json
  after verifying models via PI CLI — a different transport than
  spawn_subagent. The serde bug is specific to Grok Build's
  spawn_subagent deserializer (u32 vs null for optional OpenAI fields).
  PI CLI and direct API work fine. The concurrent session's verification
  was correct for PI but wrong for spawn_subagent. The shared
  fleet-models.json file was corrupted for all sessions using spawn.
  Root cause: shared mutable state with no write provenance or transport
  qualification. The file doesn't record WHO changed it, WHY, or which
  transport was used for verification.
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - "Session 019fa8f8: serde_broken list restored after concurrent session cleared it"
  - "Workspace wiki: model-tool-calling-capability-matrix.md line 180 — dual cross-transport test"
relations:
  - target: wiki/concepts/concurrent-session-commit-collision.md
    type: same-family
    note: "Same class: concurrent sessions mutating shared state without coordination"
  - target: wiki/concepts/multi-terminal-hook-state-isolation.md
    type: related
    note: "Hook state is session-scoped; fleet-models.json is shared workspace state"
  - target: wiki/concepts/invariants-beat-environment-comfort.md
    type: applies
    note: "The invariant (serde_broken models must stay blocked via spawn) was violated by a concurrent session"
---

# Multi-terminal shared-state contamination via transport mismatch

## Decision context

**The motivating problem:** session 019fa8f8 discovered that `fleet-models.json`'s `serde_broken` list had been cleared to `[]` by a concurrent session (commit `e7da24f`: "NVIDIA models verified via PI agentic harness — all PASS"). The concurrent session tested the models via PI CLI and confirmed they work. But the serde bug is specific to Grok Build's `spawn_subagent` transport — PI uses a different code path that correctly handles `null` for optional OpenAI fields.

Result: all 11 serde_broken models were unblocked. The spawn gate stopped blocking them. Any session that spawned these models via `spawn_subagent` would hit the same serde error that was already diagnosed and documented in `model-tool-calling-capability-matrix.md`.

## The pattern

```
TRIGGER:     Concurrent session verifies a shared-state entry using a
             different transport than the one the entry was created for.
EXPECTATION: The shared-state entry should only be modified after
             verification via the SAME transport that produced the original
             finding.
FAILURE:     The entry is cleared/modified based on cross-transport
             verification that doesn't apply to the original transport.
CATCH:       The next session that uses the original transport hits the
             original failure that was already diagnosed and documented.
ROOT CAUSE:  Shared mutable state has no write provenance — no record of
             WHO changed it, WHY, or WHICH TRANSPORT was used for the
             decision.
```

## Why this is a multi-terminal hazard

`fleet-models.json` is shared workspace state — every session reads it, any session can write it. Unlike hook state (session-scoped via `GROK_SESSION_ID`), the registry has no isolation. A concurrent session's incorrect modification affects all sessions immediately.

This is the same hazard class as [[concurrent-session-commit-collision]] — shared mutable state on a multi-agent filesystem — but with a twist: the modification was intentional and well-reasoned (the models DO work via PI), just applied to the wrong scope (spawn_subagent-specific state was cleared based on PI-specific verification).

## Generalization: transport-specific state in shared files

The pattern extends beyond serde_broken:
- `spawn_broken` list — a model might work via spawn but fail via direct API (or vice versa)
- Quota cache `source` field — "error-hook" marks are spawn-specific but stored in a shared cache
- `learned-serde-broken.json` — entries are spawn-specific but any PostToolUseFailure hook can write them

Any shared-state file that records transport-specific findings is vulnerable to cross-transport contamination.

## What this means for our workspace

1. **fleet-models.json serde_broken list** needs a `verified_via` field recording which transport was used for the last verification. If verification was via PI/direct API, the spawn_subagent-specific block should NOT be cleared.

2. **Any code that clears serde_broken entries** must verify via `spawn_subagent`, not PI or direct API. The verification transport must match the blocking transport.

3. **Git history is the rollback path** — when contamination is detected, `git show HEAD:fleet-models.json` recovers the prior state. But this requires knowing the contamination happened, which requires monitoring.

## Receipts

- `fleet-models.json:serde_broken` — the list that was cleared. Confirmed empty at `git show e7da24f`.
- `fleet-models.json:serde_broken` (after restore) — 11 entries restored by commit `fcd89ca` in session 019fa8f8.
- `model-tool-calling-capability-matrix.md:180` — dual cross-transport test confirming serde bug is Grok Build spawn_subagent only.
- `PreToolUse_spawn_model_gate.py:77` — gate checks `serde_broken` set from registry. When list is empty, all models pass.

## Related concepts

- [[concurrent-session-commit-collision]] — same class: concurrent sessions mutating shared state without coordination
- multi-terminal-hook-state-isolation — hook state is session-scoped; fleet-models.json is shared workspace state
- [[invariants-beat-environment-comfort]] — the invariant (serde_broken models must stay blocked via spawn) was violated by a concurrent session

## Falsifier

This pattern is wrong if:
- A future Grok Build version fixes the serde bug upstream (u32 → Option<u32>), making all transports equivalent. In that case, cross-transport verification becomes valid.
- The serde_broken list is moved to per-session state (each session maintains its own list). In that case, contamination is structurally impossible.
- No concurrent session ever modifies the registry again (unlikely on a multi-agent host).

## Auto-related

- [[mcp-server-sharing-multi-terminal]]
- [[skill-catalog]]
- [[stateless-cli-vs-mcp-for-cross-agent-email-access]]
- [[session-close-out-skill-design]]
- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]

