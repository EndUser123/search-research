---
current_session_id: 019fba6f-bfc9-7900-a5e8-7cb4ea3a01da
last_updated_by: 019fba6f-bfc9-7900-a5e8-7cb4ea3a01da
last_updated_at: 2026-07-31T17:09:29.134955
parent_session: none
produced_at: 2026-07-31T17:09:29.134955
status: open
handoff_type: investigation
---
# Handoff: Probe-Before-Spawn Helper

**Status:** OPEN — design needed, not started. Surfaced from AAR Q10a.
**Date:** 2026-07-29
**Source:** session 019fa48a AAR, tool-fallbacks.md gemini-2 404 entry

## Problem

The session-start model catalog lists models that may not be accessible via the API. When `/design` spawned a critical-friend subagent with `model="gemini-2"`, the API returned HTTP 404 ("model does not exist or your team does not have access"). This wasted a spawn cycle and required retry with a different model.

The same risk applies to any skill that specifies `model=` for a subagent: `/tp` (critic pool), `/review` (specialists), `/check` (verifiers), `/debrief` (lens agents). All of these trust the model catalog as a guarantee, but it's only a registry of what could be available.

## Objective

Build a lightweight probe helper that skills can call before committing to a multi-minute `spawn_subagent` with `model=X`. The probe sends a trivial prompt to verify the model is actually accessible, and only then commits to the real spawn.

## Acceptance criteria

1. The helper accepts a model slug and returns `accessible: true/false` in <5 seconds
2. The helper uses a minimal prompt (e.g., "Reply READY") to minimize cost
3. Skills call the helper before spawning any subagent with `model=X` where X is from the catalog
4. If the probe fails, the skill falls back to the next pool member (existing behavior in `/tp` Step 2)
5. The helper caches results for the session (don't re-probe the same model on every spawn)

## Design questions

- **Where does it live?** Options: (a) `~/.grok/hooks/scripts/model_probe.py` (standalone, callable by any skill), (b) `~/.grok/skills/tp/__lib/` (tp-specific), (c) shared `__lib` across skills
- **What's the probe mechanism?** Options: (a) `spawn_subagent` with a trivial prompt + short timeout, (b) direct API call (bypasses spawn overhead), (c) check `tool-fallbacks.md` known-broken table first (fastest, but stale)
- **Caching?** Session-scoped cache at `~/.grok/state/model-probe-{session_id}.json`. TTL = session lifetime. Clear on session end.

## Approach

The simplest viable version: a Python script that reads `tool-fallbacks.md` for known-broken models, then optionally probes with a trivial spawn. Most models are either known-good (parent-inherited) or known-broken (tool-fallbacks). Only models in the "untested" category need a live probe.

## Dependencies

- None blocking. Can start independently.

## Related

- tool-fallbacks.md: gemini-2 404 entry, MiniMax-M3 resume truncation entry
- Wiki concept: `multi-subagent-orchestration-workflow-failure-patterns` (finding #3)
- `/tp` Step 2: pool selection logic that would consume this helper

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-07-31T17:09 | 019fba6f-bfc... | backfilled session_id from transcript scan |
