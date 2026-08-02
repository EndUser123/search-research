---
thread_id: a3b7f2c1-8d4e-4a6b-9c1f-2e5a8b7c3d6e
parent_handoff_path: none
current_session_id: 019fc30c-545e-7432-b46e-7b9712afe9e1
current_terminal_id: grok-main
produced_at: 2026-08-02T16:45:00Z
last_updated_by: 019fc30c-545e-7432-b46e-7b9712afe9e1
last_updated_at: 2026-08-02T16:45:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 0fd7559b970a762f57e8b2111ff44f78b4ffe90e
checkpoint: false
---

# LLM-Judge Stop Hook for Proactive Observation Surfacing — Phase 0 live, Phase 1 gated

## Objective

Design and implement a Stop hook that detects when the agent encountered information worth surfacing but didn't express it, then injects `Maybe:` observations via `additionalContext`.

**Scope bounds:** Phase 0 (passive measurement) is live. Phase 1+ (LLM judge, active injection) is designed but gated on 30-day measurement data.

## Status

OPEN — Phase 0 implemented and smoke-tested. Phase 1+ deferred pending Phase 0 data collection.

## Producing context

Date: 2026-08-02. Session: `019fc30c-545e-7432-b46e-7b9712afe9e1`. Host: Grok Build. Design run ID: `2088aada`.

## Read-first list (ordered)

1. `C:\Users\brsth\AppData\Local\Temp\grok-design-2088aada\grok-design-doc-2088aada.md` — full design doc (~2000 lines, 67 review findings, critical friend PROCEED). **In temp — will be reaped by OS. Copy to `P:/docs/designs/` if you want to keep it.**
2. `C:\Users\brsth\.grok\skills\notice\SKILL.md` — the skill this hook extends (13 triggers, 8-heuristic scoring, calibration)
3. `C:\Users\brsth\.grok\docs\user-guide\10-hooks.md` — Stop hook payload schema, `additionalContext` mechanism
4. `C:\Users\brsth\.grok\hooks\scripts\PostToolUse_tool_log.py` — Phase 0 hook (tool-call logger)
5. `C:\Users\brsth\.grok\hooks\scripts\Stop_text_log.py` — Phase 0 hook (text-capture)
6. `P:\.agents\scripts\analysis\phase0_missed_rate.py` — Phase 0 analysis script (gate to Phase 1)

**Related wiki concepts:**
- [[measure-first-pattern-for-proactive-mechanism-design]]
- [[proactive-ai-volunteering-mechanisms]]
- [[auto-test-stop-hooks-and-property-based-testing]] — `additionalContext` forces continuations (design implication)

## Verified facts

- [FACT] `/notice` skill has 13 triggers (T1-T13, T4 excluded) and 8-heuristic motivation scoring — receipt: Python regex found T1-T13 in SKILL.md, 434 lines
- [FACT] 6 Stop hooks currently registered via JSON files in `~/.grok/hooks/` — receipt: Python json.loads of *.json found behavioral-check, close-enforcement, dbr-language, minimal-bias-gate, quality-gate, wiki-persistence-check
- [FACT] Calibration state files `notice-calibration.json` and `notice-cooldown.json` do NOT exist — receipt: Python `Path.exists()` returned False for both
- [FACT] `additionalContext` via Stop hook forces a turn continuation — receipt: hooks doc line 256, "keeps the agent working, but is surfaced as hook feedback"
- [FACT] Stop hook input includes `lastAssistantMessage` but NOT tool-call history — receipt: hooks doc lines 260-267
- [FACT] Phase 0 hooks compile and pass smoke test with synthetic payloads — receipt: `python P:\tmp\smoke_test_phase0.py` exit 0, all assertions passed
- [FACT] Analysis script produces rate report with gate decision — receipt: smoke test output showed "RETIRE — rate too low" for 1-session synthetic data
- [FACT] Design went through 3 rounds of correctness review (56 findings) + 3 rounds of critical friend (11 findings) = 67 total, all addressed — receipt: review files in `grok-design-2088aada/` scratch dir

## Current state

**Phase 0 (live):**
- `PostToolUse_tool_log.py` + `Stop_text_log.py` are registered and active
- Kill switch: `OBSERVATION_TOOL_LOG_DISABLED=1` env var
- Logs to `~/.grok/state/observation-tool-log/<sha256>.jsonl` and `observation-text-log/<sha256>.jsonl`
- Analysis script committed at `P:/.agents/scripts/analysis/phase0_missed_rate.py`

**Phase 1+ (designed, not built):**
- Design doc has full pseudocode for: Stage 0 entry gate, Stage 1 deterministic filter, Stage 2 DiffusionGemma judge call, injection via `additionalContext`
- Judge model: DiffusionGemma (Nvidia NIM, free, 256K context, different model family)
- All 13 implementation units defined with acceptance criteria, feature flags, and dispositions
- Units 2-13 are DEFERRED (Phase 1+), gated on Phase 0 measurement showing ≥0.5 missed observations/session

**Wiki promotions:**
- [[measure-first-pattern-for-proactive-mechanism-design]] — created
- [[auto-test-stop-hooks-and-property-based-testing]] — updated with `additionalContext` forces-continuation finding

## Task packets

### PHASE0-REVIEW-01: Review Phase 0 data after 7 days
- **Goal:** Check early trend of missed-observation rate
- **In scope:** Run `python P:/.agents/scripts/analysis/phase0_missed_rate.py --per-session`
- **Acceptance:** Report shows missed-observation rate per session
- **Falsifier:** If rate is 0.0 consistently after 7 days, consider retiring the design early
- **Verification level:** LIVE_BEHAVIOR
- **Estimate:** ~5 seconds to run the script; requires 7 days of hook data collection first

### PHASE0-GATE-01: Phase 0 → Phase 1 go/no-go decision
- **Goal:** Decide whether to build the Phase 1 LLM judge
- **In scope:** Run analysis script after 30 days / 50 sessions. If avg missed/session ≥ 0.5 → proceed to Phase 1. If < 0.5 → retire.
- **Acceptance:** Decision documented with data
- **Falsifier:** Rate < 0.5 → retire the design (the `Note:`/`Maybe:` behavioral rules are sufficient)
- **Verification level:** LIVE_BEHAVIOR

### PHASE1-BUILD-01: Build Phase 1 LLM judge (DEFERRED)
- **Goal:** If Phase 0 gate passes, implement Units 2-8 from the design doc
- **In scope:** `observation_judge_call.py`, `observation_judge.py` Stop hook, state files, tests
- **Dependencies:** PHASE0-GATE-01 must pass
- **Falsifier:** Judge FP rate > 20% in shadow mode → tune threshold or retire

## Open decisions

### OD-1: Phase 0 → Phase 1 threshold (§16.13)
- **Question:** Is 0.5 missed observations/session the right threshold?
- **Options:** (a) 0.5/session (current), (b) 1.0/session (more conservative), (c) review after 7 days and adjust
- **Selection criterion:** "If the operator is missing even one observation per session they would have valued, the judge has something to find"
- **Currently leads:** (c) review after 7 days — the threshold is a judgment call, not a measured value
- **What would change it:** 14 days of data showing 0.0/session → retire regardless of threshold

### OD-2: Judge context asymmetry (§16.12)
- **Question:** Does the judge's reduced context (lastAssistantMessage + 5 tool logs vs. full conversation + system prompt) limit its ability to detect missed observations?
- **Falsifier:** 20 turns from Phase 0 corpus, judge run twice (reduced vs full context), agreement ≥ 70% required

## Hard constraints

1. **Fail-open on every error path** — broken judge must never block conversation
2. **Kill switch** — `OBSERVATION_TOOL_LOG_DISABLED=1` (Phase 0), `kill: true` in calibration state (Phase 1+)
3. **Cross-family judge** — must use a different model family from parent Grok
4. **Reuse `/notice` calibration** — single source of truth, not parallel state
5. **Counter-based calibration** — concurrent writes are monotonic increments, not read-modify-write

## Cross-reference couplings

- `~/.grok/hooks/posttooluse-tool-log.json` → calls `PostToolUse_tool_log.py`. If either moves, the hook silently stops logging.
- `~/.grok/hooks/stop-text-log.json` → calls `Stop_text_log.py`. Same coupling.
- `phase0_missed_rate.py` → reads both log dirs. If log dir path changes in the hooks, the analysis script breaks.
- Design doc in temp → will be reaped by OS. The handoff and wiki concepts are the durable artifacts.
- [[measure-first-pattern-for-proactive-mechanism-design]] → cites this design as provenance. If this design retires, the pattern still stands.

## Other outstanding streams

None — this session was focused on a single work stream (the design + Phase 0 implementation).

## Explicit non-goals

- Do NOT build Phase 1 (judge) until Phase 0 data justifies it
- Do NOT modify the `/notice` skill itself (the hook extends it, doesn't replace it)
- Do NOT add Stop hook registrations for Phase 1 until the composition audit (Unit 11) is complete

## Resumption protocol

1. Wait 7+ days for Phase 0 data collection
2. Run: `python P:/.agents/scripts/analysis/phase0_missed_rate.py --per-session`
3. Review the missed-observation rate trend
4. At 30 days / 50 sessions: make the Phase 0 → Phase 1 go/no-go decision

## Suggested next invocation

```
Check Phase 0 missed-observation rate: run python P:/.agents/scripts/analysis/phase0_missed_rate.py --per-session and report whether the rate justifies building the Phase 1 LLM judge.
```

## Last user message (verbatim)

> /handoff

## Epistemic labels

- [FACT] All Phase 0 code is live, compile-checked, and smoke-tested — receipts above
- [FACT] Design went through 67 review findings with PROCEED verdict — receipt: critique-r3.md
- [INFERENCE] The design doc will be reaped by the OS — standard Windows temp behavior, not verified for this specific file
- [UNKNOWN] Whether Phase 0 data will justify Phase 1 — cannot determine until 30 days of collection

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-02T16:45 | 019fc30c... | created — design complete, Phase 0 live, Phase 1 gated |

---

## Original handoff content (pre-revision)

# Design: LLM-Judge Stop Hook for Proactive Observation Surfacing

**Status:** Design complete (2026-08-02). Phase 0 implemented and live. Phase 1+ gated on measurement.

**Design doc:** `C:\Users\brsth\AppData\Local\Temp\grok-design-2088aada\grok-design-doc-2088aada.md` (~2000 lines, 67 review findings addressed, critical friend PROCEED)
**Wiki concept:** [[measure-first-pattern-for-proactive-mechanism-design]]
**Phase 0 code (live):**
- `~/.grok/hooks/scripts/PostToolUse_tool_log.py` — logs tool calls per session
- `~/.grok/hooks/scripts/Stop_text_log.py` — captures lastAssistantMessage per turn
- `~/.grok/hooks/posttooluse-tool-log.json` + `stop-text-log.json` — registrations
- `P:/.agents/scripts/analysis/phase0_missed_rate.py` — missed-observation rate analyzer

**Kill switch:** `OBSERVATION_TOOL_LOG_DISABLED=1` env var disables both hooks.

---

## Design revision (2026-08-02, post-critical-friend)

The critical friend reframed the approach from "build judge immediately" to "measure first." Phase 0 is now **passive log only** (no judge, no API cost, no additionalContext). The judge (Phase 1) is built ONLY if Phase 0 shows ≥0.5 missed observations per session over 30 days / 50 sessions. See [[measure-first-pattern-for-proactive-mechanism-design]] for the transferable pattern.

**Open questions** (in design doc §16):
- §16.13: Is 0.5 missed obs/session the right Phase 0→1 threshold? Review after 7 days of data.
- §16.12: Does the judge's reduced context limit detection? Falsifier: 20 turns, judge run twice (reduced vs full context).

---

## Objective (original)

Build a Stop hook that uses a two-stage filter (deterministic code → LLM judge) to detect when the agent encountered information worth surfacing but didn't express it, then injects `Maybe:` observations back into the conversation via `additionalContext`.

## Problem

The `/notice` skill has 13 triggers, 8-heuristic motivation scoring, adaptive calibration, and hard-skip patterns — the most sophisticated proactive-surfacing design in the workspace. It has never been observed working because it's a skill, not a hook. Skills require invocation; hooks fire automatically. All that trigger infrastructure sits dormant.

The AGENTS.md `Note:` and `Maybe:` rules are behavioral reminders (~60-70% reliable based on correction frequency this session). Hooks are the only mechanism tier with near-100% reliability on this host.

## Proposed solution: two-stage Stop hook

### Stage 1 — Deterministic code filter (5-10ms, every turn)

Python script reads the transcript/tool-call context and applies hard gates:

- **Skip if:** first turn, acceleration mode, implementation skill active (`/go`, `/refactor`, `/grok-parallel`), already has `Note:`/`Maybe:`/`INFO:` line in output
- **Fire if:** turn used observation-producing tools (`read_file`, `grep`, `list_dir`, `web_search`, `web_fetch`, `evaluate_script`) AND zero observation lines in output AND cooldown expired (max 1 per 3 turns)

If stage 1 returns False: exit immediately, no LLM cost.

### Stage 2 — LLM judge (2-5s, only when stage 1 passes)

Send the agent's last turn (tool calls + results + output) to a different-model-family judge with observation-auditing prompt. Score candidates on relevance, novelty, information gap. Return candidates with score ≥3.0 and confidence ≥medium.

### Injection

If observations found, inject via Stop hook `additionalContext`.

## Design decisions to make in the design doc

1. **Judge model selection** — DiffusionGemma (free, 256K context, local), free fleet model, or a small model via direct API.
2. **Transcript packing** — how to efficiently pass the last turn's content to the judge.
3. **False-positive management** — confidence threshold, score threshold, cooldown, adaptive calibration.
4. **Injection reliability** — additionalContext injection can silently fail.
5. **Adaptive calibration** — reuse /notice's calibration state.
6. **Trigger taxonomy reuse** — which /notice triggers map to the hook.
7. **Performance budget** — ≤5s total per fire.
8. **Relationship to /notice skill** — does this hook replace, complement, or merge with /notice?

## Constraints

- Must work in Grok Build (command and http hook types only)
- Must use a different model family from the parent Grok
- Must be non-blocking (fail-open if judge takes >10s)
- Must not duplicate /notice's trigger design — reuse, don't reinvent
- Must have a kill switch

## Research base

- `/notice` SKILL.md — 13 triggers, 8-heuristic motivation scoring, adaptive calibration
- LLM-as-judge research: Luna-2, Reflexion, HaluGate
- Self-preference bias: judge must be different model family
- Two-stage filter pattern: rule-based checks first with short-circuiting
- "Where Facts Go Missing": 73.4% of omission loss comes from deterministic pipeline layers

## File paths

- `/notice` SKILL.md: `~/.grok/skills/notice/SKILL.md`
- Existing calibration state: `~/.grok/state/notice-calibration.json` (DOES NOT EXIST — must be created)
- Hook registration: `~/.grok/config.toml` or `~/.grok/hooks/*.json`
- DiffusionGemma reader: `P:/.agents/scripts/models/dgemma_read.py`
- Existing Stop hook: `P:/.claude/hooks/Stop.py` (5281 lines)

## Acceptance criteria

- [ ] Two-stage filter design documented with data flow diagram
- [ ] Stage 1 deterministic filter implemented and tested
- [ ] Stage 2 LLM judge prompt designed and tested for false-positive rate
- [ ] Injection mechanism verified (additionalContext lands reliably in Grok Build)
- [ ] Judge model selected based on latency + accuracy + model-family diversity
- [ ] Adaptive calibration reused from /notice
- [ ] Kill switch implemented
- [ ] Performance budget met: ≤5s per fire
- [ ] False-positive rate: target ≤20%
- [ ] Relationship to /notice documented
