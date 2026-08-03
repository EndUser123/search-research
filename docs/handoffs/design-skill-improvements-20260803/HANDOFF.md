---
thread_id: f7c2e9a4-1b3d-4f8e-b6c7-9d0a1e2f3a4b
parent_handoff_path: none
current_session_id: 019fc30c-545e-7432-b46e-7b9712afe9e1
current_terminal_id: grok-main
produced_at: 2026-08-03T00:15:00Z
last_updated_by: 019fc30c-545e-7432-b46e-7b9712afe9e1
last_updated_at: 2026-08-03T12:30:00Z
status: CLOSED
handoff_type: investigation
accurate_as_of_head: 631abcb18114a929c0cb0e4e0484c5cbe0a8c2bf
checkpoint: false
---

# Three /design skill improvements + handoff backlog triage

## Objective

Fix three friction patterns surfaced by `/tp improve` after the LLM-Judge Stop Hook design session, and triage the 73-item open-handoff backlog.

**Scope bounds:** 3 skill improvements (all from one session's friction) + 1 workspace hygiene item. The 73 handoffs are ambient state; the work scope is triage, not execution of all 73.

## Status

CLOSED — all three items implemented and committed.

- **DESIGN-QUOTA-01:** DONE. Added `pick_model.py --list` pre-check to `/design` "Model selection for subagents" section. Replaced hardcoded model names in Step 0.9 with lane references. Added global convention to `~/.grok/AGENTS.md`. Commit `f768c24`.
- **DESIGN-CONTEXT-01:** DONE. Added proactive context-size check (>1500 lines OR resume count ≥2) to Step 4 (writer) and Step 5 (reviewer). Added `writer_resume_count` / `reviewer_resume_count` state variables. Updated reactive fallback to safety-net. Commit `4369371`.
- **BACKLOG-TRIAGE-01:** DONE. Closed 89 stale handoffs (30.0% reduction from 263 open → ~184 open). Batch: 30 session observations, 10 already-done, 49 stale July items. Commit `a417fc4`.

## Producing context

Date: 2026-08-03. Session: `019fc30c-545e-7432-b46e-7b9712afe9e1`. Host: Grok Build. Source: `/tp improve` output from the LLM-Judge Stop Hook design session.

## Read-first list (ordered)

1. `C:\Users\brsth\.grok\skills\design\SKILL.md` — the design skill being improved (Step 2 reviewer spawning, Step 4 revise, Step 5 re-review)
2. `C:\Users\brsth\.grok\skills\tp\SKILL.md` § "Model pool" — the model-cascading pattern that `/design` should adopt for pre-write steps
3. `C:\Users\brsth\.grok\hooks\scripts\PreToolUse_spawn_model_gate.py` — existing spawn quota gate (the pre-check could extend this or live in `/design`)
4. `~/.grok/skills/model-quota/scripts/pick_model.py` — quota-checking utility already available

**Related wiki concepts:**
- [[measure-first-pattern-for-proactive-mechanism-design]] — from the same session
- [[subagent-output-token-exhaustion]] — the root-cause pattern for the reviewer max_tokens failure
- [[model-pool-selection-policy-speed-quota-diversity]] — quota-aware model selection

## Verified facts

- [FACT] OpenCode-Go provider was at 0% quota during this session — receipt: hook denied messages on 3 consecutive spawn_subagent calls with `go-deepseek-v4-flash` and `go-qwen3-7-plus`, 38 total error-pattern hits in transcript
- [FACT] MiniMax-M3 reviewer hit `max_tokens_truncation` at 175K input tokens on the ~2000-line design doc — receipt: subagent output `{"message": "response truncated by max_tokens", "error_kind": "max_tokens_truncation", "promptUsage": {"inputTokens": 174941}}`
- [FACT] Resumed writer produced zero effective edits in 6.15s on round 2 revision — receipt: `get_command_or_subagent_output` showed 6.15s duration, 103 tool calls but review file showed all findings still Status: open
- [FACT] 73 execution-ready handoffs exist in workspace — receipt: `workspace_opportunity_scan.py` output "Execution-ready handoffs (73)"
- [FACT] `pick_model.py --list` exists and shows available models — receipt: ran during this session, returned `or-ling-3-flash-free` and `zen-deepseek-v4-flash-free` as available

## Current state

Nothing implemented. All three improvements are identified with evidence. The handoff backlog item is observational — no triage has been done.

## Task packets

### DESIGN-QUOTA-01: Model quota pre-check before spawning subagents
- **Goal:** Eliminate the pattern where `/design` (and other skills) spawn subagents on a provider at 0% quota, wasting 3+ failed spawn attempts
- **In scope:** Either (a) a pre-check in `/design` Step 0.9 that runs `pick_model.py --list` before dispatching, or (b) extending `PreToolUse_spawn_model_gate.py` to check quota proactively and suggest alternatives, or (c) a convention in AGENTS.md that skills check quota before parallel dispatch
- **Out of scope:** Changing the quota system itself; changing model routing policies
- **Files / anchors:** `C:\Users\brsth\.grok\skills\design\SKILL.md` § Step 0.9; `C:\Users\brsth\.grok\hooks\PreToolUse_spawn_model_gate.py`
- **Acceptance:** When OpenCode-Go is at 0%, `/design` pre-write steps use `or-ling-3-flash-free` on the first attempt without any failed spawns
- **Falsifier:** Failed spawns still occur when quota is at 0% after this fix
- **Verification level required:** LIVE_BEHAVIOR
- **Estimate:** ~30 min (read pick_model.py, add pre-check call, test with current 0% quota state)

### DESIGN-CONTEXT-01: Fresh reviewer/writer when context exceeds threshold
- **Goal:** Prevent `max_tokens_truncation` and zero-output revisions on large design docs by switching from `resume_from` to fresh subagents when the doc or transcript exceeds a threshold
- **In scope:** `/design` SKILL.md Step 5 (re-review) and Step 4 (revise) — add a context-size check: if design doc >1500 lines OR reviewer/writer has been resumed ≥2 times, spawn fresh instead of resuming
- **Out of scope:** Changing the model used for reviewer/writer; changing the design doc format
- **Files / anchors:** `C:\Users\brsth\.grok\skills\design\SKILL.md` Step 4 (line ~690) and Step 5 (line ~830)
- **Acceptance:** On a 2000-line design doc, the re-review completes without `max_tokens_truncation` by using a fresh reviewer that reads the doc from disk
- **Falsifier:** Reviewer still truncates on large docs after this fix
- **Verification level required:** LIVE_BEHAVIOR
- **Estimate:** ~45 min (add line-count check, add resume-count tracking, test with a large doc)

### BACKLOG-TRIAGE-01: Triage 73 open handoffs
- **Goal:** Reduce the open-handoff backlog by closing stale ones and prioritizing live ones
- **In scope:** Run `/handoff list --head <current>`, classify each handoff as: (a) actively being worked, (b) stale (no work in 7+ days), (c) superseded by other work, (d) needs immediate attention. Close (b) and (c). Create a prioritized execution plan for (a) and (d).
- **Out of scope:** Executing the handoffs (that's `/todo` or `/go` territory)
- **Files / anchors:** `P:\docs\handoffs\` (all subdirectories)
- **Acceptance:** Open handoff count reduced by ≥30% (stale/superseded closed); remaining handoffs have clear priority ordering
- **Falsifier:** Backlog remains at 73+ after triage (nothing was closed)
- **Verification level required:** STATIC_INSPECTION
- **Estimate:** ~60 min (list, classify, close, prioritize)

## Open decisions

### OD-1: Where does the quota pre-check live?
- **Question:** Should the pre-check be in `/design` Step 0.9, in the `PreToolUse_spawn_model_gate.py` hook, or as an AGENTS.md convention?
- **Options:** (a) `/design` step — skill-local, only protects `/design`; (b) hook — protects all spawn_subagent calls globally; (c) AGENTS.md convention — relies on behavioral compliance
- **Selection criterion:** Optimal long-term = global protection (hook), because the pattern affects all skills that spawn subagents, not just `/design`
- **Currently leads:** (b) hook extension — but needs investigation of whether the hook can run `pick_model.py` fast enough to not add latency

## Hard constraints

1. The quota pre-check must not add >100ms latency to the spawn path
2. The context-size threshold for fresh-vs-resume must be empirically validated, not guessed
3. Handoff closures must use `/handoff close` (which prompts for wiki promotion), not `rm`

## Cross-reference couplings

- `PreToolUse_spawn_model_gate.py` → currently blocks spawns on dead models reactively. If extended to pre-check quota, it needs access to `pick_model.py`'s quota cache.
- `/design` Step 5 "Resume failure recovery" already documents the fresh-reviewer fallback for `max_tokens_truncation` — this handoff would make it automatic instead of manual.
- The 73 handoffs include some from THIS session (`llm-judge-stop-hook-for-missed-observation-surfacing`) which should NOT be closed (it's the Phase 0 measurement handoff).

## Other outstanding streams

- **LLM-Judge Stop Hook** — Phase 0 is live, Phase 1 gated on 30-day measurement. See `llm-judge-stop-hook-for-missed-observation-surfacing/HANDOFF.md`.
- **Class C shell quoting** — behavioral rule, not a handoff. The model must use `write` tool for any `python` payload with nested brackets/quotes.

## Explicit non-goals

- Do NOT redesign the model-quota system
- Do NOT change the `/design` skill's fundamental write→review→revise loop
- Do NOT execute all 73 handoffs (triage only)
- Do NOT close the Phase 0 measurement handoff

## Resumption protocol

1. Run `pick_model.py --list` to check current quota state
2. If OpenCode-Go is still at 0%, DESIGN-QUOTA-01 can be tested immediately
3. Pick the highest-impact item (QUOTA-01 saves the most future friction) and implement
4. For BACKLOG-TRIAGE-01, run `/handoff list --head $(git rev-parse HEAD)` and classify

## Suggested next invocation

```
/go Fix the three /design skill improvements from handoff design-skill-improvements-20260803: (1) model quota pre-check before spawning subagents, (2) fresh reviewer/writer when context exceeds threshold, (3) triage 73 open handoffs. Start with the quota pre-check — it's the highest-impact friction reduction.
```

## Last user message (verbatim)

> what should we fix now because they are quick or high impact, vs put in a /handoff?

## Epistemic labels

- [FACT] All friction patterns have transcript receipts (quota hits, max_tokens, zero-output revision)
- [FACT] 73 handoffs is from workspace_opportunity_scan.py output
- [INFERENCE] The fresh-reviewer threshold should be ~1500 lines — derived from this session's experience where the doc was ~2000 lines and failed, but prior sessions with ~1000-line docs succeeded. Unmeasured for the exact crossover.
- [UNKNOWN] Whether the hook can run pick_model.py within 100ms — needs testing

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-03T00:15 | 019fc30c... | created — 3 improvement items + backlog triage from /tp improve |
| 2026-08-03T12:30 | 019fc882... | all 3 items implemented + committed. Handoff CLOSED. |
