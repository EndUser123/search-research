---
title: "L4 'order the lab' protocol — durable fix for fabricated causal claims"
status: OPEN
created: 2026-08-08
session: 019fe3ff-afbc-71c1-b2a3-3cfbccfd2bc7
assignee: unassigned
---

# L4 "order the lab" protocol — design investigation

## Problem

The agent fabricated three causal claims in one session (019fe3ff):
1. "Satisfies all three invariants by construction" — didn't read the code
2. "Codex is stuck" — didn't check process state (it had exited normally)
3. "Keyed by GROK_SESSION_ID" — didn't verify env var (it's empty)

All three share one root cause: the agent substituted plausible narratives
for verification. The "Claims require receipts" prose rule (AGENTS.md) has
a ~68% compliance ceiling (IFScale benchmark) and didn't fire under closure
pressure.

The shipped confabulation_gate regex extension (commit `4a6a9eb`) is a
**rate-reducer** (L3 output scanning), not a **durable fix**. The wiki
research confirms LLM-as-judge detection has a 41.1% localization ceiling
(AgentHallu). The field's consensus: durable fixes live at L4 (action
enforcement) or L5 (runtime contracts).

## What to design

An "order the lab" protocol — a workflow step where the agent must run a
verification command before asserting process-state or code-structure claims.
From the Algorithme essay (cited in wiki): "Stop trying to make the
pattern-matcher perfect. Order the lab."

The protocol would:
- Identify claim types that require verification (process state, code
  structure, runtime behavior, env var presence)
- For each type, define the verification command (e.g., `Test-Path`,
  `$env:VAR`, `Get-Process`, `read_file`)
- Enforce: the verification must happen BEFORE the claim is stated, not after
- Live at L4 (PreToolUse or workflow step), not L3 (output scanning)

## Open design questions
- Should this be a PreToolUse hook (intercepts the agent's text output) or a
  workflow protocol (skill-level step)?
- How to distinguish claims that need verification from analytical prose?
- What's the latency cost of requiring verification before every causal claim?
- Does this compose with the existing confabulation_gate (L3), or replace it?

## Acceptance criteria
- [ ] Design doc produced (via /design or /plan)
- [ ] Protocol distinguishes claim types that need verification from analytical prose
- [ ] Protocol tested against the 3 specific failures from session 019fe3ff
- [ ] Protocol evaluated against the 41.1% detection ceiling — does L4 do better?

## Evidence
- AAR report: `P:/.artifacts/console_77a0d2fd-13d8-4ebe-9b08-fe1d/grok-aar-20260808/aar-report.md`
- Wiki: `[[narrative-sufficiency-awareness-enforcement-gap-2026]]`
- Confabulation_gate extension: commit `4a6a9eb`
- Field research: IFScale (68% ceiling), AgentHallu (41.1% localization), arXiv:2606.06460 (0/40 mid-flight halts)
