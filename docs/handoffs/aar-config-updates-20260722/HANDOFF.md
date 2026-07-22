---
thread_id: e038a06f-1450-4574-86cd-993e2fa14a5a
parent_handoff_path: none
current_session_id: 019f8507-6395-7bc0-87a9-9122e28d68c8
current_terminal_id: console_896ff2fb-4053-4c04-9d6a-74e4
produced_at: 2026-07-22T05:10:29Z
status: open
handoff_type: investigation
accurate_as_of_head: b3fb5225caa69e4759ca6697df715b6b6214259d
---

# HANDOFF — Config/doc updates: secret rotation + tool-fallbacks documentation

## 1. Objective

Two small independent items from AAR report session 019f8507 that need attention but are too small for individual handoffs. Batched here.

## 2. Status

**OPEN** — neither item started. Both are small, independent, non-blocking.

## 3. Producing context

- **Date:** 2026-07-22
- **Session:** `019f8507-6395-7bc0-87a9-9122e28d68c8`
- **AAR report:** `P:/.artifacts/grok-aar/console_console_896ff2fb-4053-4c04-9d6a-74e4/20260721-224551/aar-report.md`

## 4. Read-first list

1. `~/.grok/config.toml` lines 100-130 — the `[model.*]` sections containing API keys
2. `~/.grok/tool-fallbacks.md` — the known-broken model/tool combinations table

## 5. Verified facts

- [FACT] Reading `~/.grok/config.toml` at event 78 exposed API keys (`sk-Z…bq#ba1d61d6`) in tool output. The keys are now in the session transcript and AAR packet.
- [FACT] `nvidia-diffusiongemma-26b` failed twice with "Empty content is not allowed for assistant messages" (API 400).
- [FACT] `nvidia-nemotron-3-ultra` failed twice with "serialization error: invalid type: null, expected u32" (API error).
- [FACT] `ccr-ornith` produced a false-positive critical bug (hook executable permissions) that was empirically refuted.

## 6. Current state

Neither item actioned.

### Item 1: Secret rotation (E1 from AAR)

The exposed key (`sk-Z…` from the `zen-big-pickle` / OpenCode Zen configuration) is in the transcript. The key needs rotation. **This requires operator action** (log into the provider console, generate a new key, update config.toml).

The agent cannot do this autonomously. This handoff flags it for the operator.

### Item 2: Tool-fallbacks documentation (E6 from AAR)

`~/.grok/tool-fallbacks.md` should document:
- `nvidia-diffusiongemma-26b`: fails with "Empty content not allowed" on specialist reviews (2026-07-21, 2 occurrences)
- `nvidia-nemotron-3-ultra`: fails with "serialization error: invalid type: null" on specialist reviews (2026-07-21, 2 occurrences)
- `ccr-ornith`: works but produces false-positive critical bugs on Windows file-permission analysis (9B model below quality floor for security review)

This is a one-file update the agent can do.

## 7. Task packets

### TASK-01: Document free-model API failures in tool-fallbacks.md

- goal: Add 3 rows to `~/.grok/tool-fallbacks.md` for the diffusiongemma, nemotron, and ccr-ornith failures observed this session.
- in scope: `~/.grok/tool-fallbacks.md`
- out of scope: fixing the API errors (upstream); changing model selection logic
- files / anchors: `~/.grok/tool-fallbacks.md`
- acceptance: the file has 3 new entries with date, symptom, workaround
- falsifier: if the entries are wrong (wrong model slug, wrong symptom, wrong date), they mislead future sessions
- verification level required: STATIC_INSPECTION

### TASK-02: Rotate exposed API key (OPERATOR ACTION)

- goal: Rotate the `sk-Z…` key exposed at event 78.
- in scope: operator logs into OpenCode Zen console, generates new key, updates `~/.grok/config.toml`
- out of scope: agent action (cannot authenticate to provider console)
- files / anchors: `~/.grok/config.toml` lines 126-130 (`[model.zen-big-pickle]` section)
- acceptance: new key in config.toml; old key revoked at provider
- falsifier: old key still works after rotation
- verification level required: LIVE_BEHAVIOR

## 8. Open decisions

Whether to also filter `config.toml` reads in the future to exclude `[model.*]` sections (prevention). This is a separate concern from rotation (containment).

## 9. Hard constraints

1. Do NOT commit API keys to any repo with a remote.
2. Do NOT echo config.toml contents in tool output without filtering.

## 10. Cross-reference couplings

- `~/.grok/config.toml [model.zen-big-pickle]` → the exposed key
- `~/.grok/tool-fallbacks.md` → the file to update for TASK-01
- AAR report E1 + E6 → the source items

## 11. Other outstanding streams

- AAR batch handoff 1: narrativization hook enhancement

## 12. Explicit non-goals

- Do NOT change the model selection logic in `/go` SKILL.md (the failures are transient infrastructure issues, not model-capability issues).
- Do NOT remove the free models from the model catalog (they may work tomorrow).

## 13. Resumption protocol

1. Read this handoff.
2. For TASK-01: open `~/.grok/tool-fallbacks.md`, append 3 entries.
3. For TASK-02: surface to operator — "the key at config.toml line ~127 needs rotation; it was exposed in session 019f8507's transcript."

## 14. Suggested next invocation

```
Update ~/.grok/tool-fallbacks.md with 3 entries for the free-model API failures
observed on 2026-07-21 (diffusiongemma, nemotron, ccr-ornith). Then surface
to operator that the zen-big-pickle API key needs rotation (exposed at AAR
event 78).
```

## 15. Last user message (verbatim)

> /handoff P:/.artifacts/grok-aar/console_console_896ff2fb-4053-4c04-9d6a-74e4/20260721-224551/aar-report.md

## 16. Epistemic labels

- [FACT] API key exposed at event 78 (AAR signal `secret_exposure_in_tool_output`)
- [FACT] 2 free models failed with API errors (AAR E6)
- [FACT] ccr-ornith produced a false positive (empirically refuted via `git push` test)
- [INFERENCE] The API failures are transient infrastructure issues, not permanent model incapabilities

## Dependencies

- **Requires:** nothing — TASK-01 can start immediately; TASK-02 requires operator action
- **Blocks:** nothing
- **Non-blocking to:** AAR batch handoff 1 (narrativization hook)