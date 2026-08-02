---
thread_id: 019fa8f8-shared-state-protection-20260802
parent_handoff_path: P:/docs/handoffs/postsession-20260801/HANDOFF.md
current_session_id: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14
current_terminal_id: grok-main
produced_at: 2026-08-02T09:00:00-06:00
status: open
handoff_type: investigation
accurate_as_of_head: f17b724e94333b998470cd4ab888c63ac2e370b9
---

# Handoff: Concurrent-session write protection for fleet-models.json

## 1. Objective

Prevent concurrent sessions from corrupting shared state by modifying transport-specific entries based on cross-transport verification.

## 2. Status

OPEN — wiki concept written, implementation deferred.

## 3. Producing context

A concurrent session cleared the `serde_broken` list in `fleet-models.json` based on PI CLI tests. The serde bug is specific to `spawn_subagent`, not PI. The shared file has no write provenance — no record of who changed it, why, or which transport was used. Wiki concept: `multi-terminal-shared-state-contamination-transport-mismatch.md`.

## 4. Read-first list

1. `~/.grok/skills/model-quota/scripts/fleet-models.json` — the shared registry
2. `~/.grok/hooks/PreToolUse_spawn_model_gate.py` — reads `serde_broken` from registry
3. `P:/.data/wiki/concepts/multi-terminal-shared-state-contamination-transport-mismatch.md` — the finding

## 5. Task packets

### SHARED-STATE-01: Add `verified_via` field to serde_broken entries
- **goal:** when a model is tested and cleared from serde_broken, record which transport was used
- **scope:** fleet-models.json structure change + pick_model.py + spawn gate
- **acceptance:** serde_broken entries have `{"slug": "model", "verified_via": "spawn_subagent"}` format. Models verified via PI/direct API cannot clear spawn-specific blocks.
- **falsifier:** if all transports converge (Grok Build fixes the serde bug), the field becomes unnecessary

### SHARED-STATE-02: Add write-audit log for registry changes
- **goal:** any modification to serde_broken/spawn_broken lists logs to an audit file
- **scope:** new audit log at `~/.cache/opencode/fleet-models-audit.jsonl`
- **format:** `{"ts": ..., "session_id": ..., "change": "cleared serde_broken entry nim-openai-gpt-oss-20b", "reason": "verified via PI", "transport": "pi"}`
- **acceptance:** audit log exists and can be used to rollback contamination
- **falsifier:** if the audit log is never read, it's dead state

## 6. Hard constraints

- Don't make the registry write path heavier (hooks read it on every spawn)
- The audit log should be append-only (no locking needed)
- Multi-terminal safe: audit log uses atomic append (open with O_APPEND)
assigned_to: grok
---
assigned_at: 2026-08-02T21:27
---
assigned_by: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14
---

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-02T21:27 | 019fa8f8... | claimed by grok |
