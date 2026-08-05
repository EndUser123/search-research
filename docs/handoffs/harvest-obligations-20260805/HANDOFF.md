---
thread_id: harvest-obligations-20260805
parent_handoff_path: none
current_session_id: 019fce56-da32-79c3-85f1-1ff2d6677580
parent_session: none
current_terminal_id: grok-main
produced_at: 2026-08-05T06:00:00-06:00
last_updated_by: 019fce56-da32-79c3-85f1-1ff2d6677580
last_updated_at: 2026-08-05T06:00:00-06:00
status: open
handoff_type: investigation
accurate_as_of_head: 7cf15174d33e97c16ba5aa2d1bb8c032a57798b8
---

# Handoff — Harvest obligations (2 open items)

## 1. Objective

Action 2 pending harvest obligations that have not been implemented.

## 2. Status

OPEN — discovered by `/todo` scanner.

## 3. Producing context

- **Date:** 2026-08-05
- **Source:** `/todo` scanner (`harvest` source), reading `.data/harvest/pending/`

## 4. Read-first list

1. `P:/.data/harvest/pending/` — JSON files with pending obligations
2. `/www` SKILL.md — for the NEXT_ACTION_PACKET prototype obligation
3. `/codex` SKILL.md — for the tool_choice=required obligation

## 5. Verified facts

- [FACT] 2 pending harvest obligations (from `/todo` scan 2026-08-05T04:57Z):
  1. NEXT_ACTION_PACKET prototype in /www — replace prose skill suggestion with structured packet so operator-gated skill routing costs one keystroke
  2. tool_choice=required injection in /codex — lighter GPT-5 tiers intermittently emit text-only instead of tool calls; conductor should inject tool_choice=required

## 6. Current state

Both obligations are in harvest JSON but not in handoff format. They require skill design work — not just a config tweak.

## 7. Task packets

### AC-01: NEXT_ACTION_PACKET prototype in /www
- **Goal:** design and implement a structured packet that /www emits after research, suggesting next skills
- **Files:** `~/.grok/skills/www/SKILL.md` (post-research step)
- **Acceptance:** /www produces a numbered recommendation packet after research runs
- **Falsifier:** packet format is ignored by operator (same as current prose suggestions)

### AC-02: tool_choice=required in /codex
- **Goal:** inject `tool_choice=required` for lighter GPT-5 tiers that intermittently emit text-only
- **Files:** `~/.grok/skills/codex/SKILL.md` (conductor section)
- **Acceptance:** lighter-tier GPT-5 models produce tool calls instead of text-only
- **Falsifier:** tool_choice=required causes issues with models that don't support it

## 8. Open decisions

None — both obligations have clear goals.

## 9. Hard constraints

- Test against live models — don't assume tool_choice behavior from docs alone

## 10. Cross-reference couplings

- `/www` post-research step reads `/wiki` post-completion recommendations — NEXT_ACTION_PACKET would replace or extend that mechanism

## 11. Other outstanding streams

None for this work.

## 12. Explicit non-goals

- Do NOT redesign /www's research pipeline — just the output packet format
- Do NOT change /codex's model routing logic — just the tool_choice injection

## 13. Resumption protocol

1. Read `/www` SKILL.md post-research step for current suggestion format
2. Read `/codex` SKILL.md conductor section for current model invocation
3. Design AC-01 first (lower risk, higher operator value)

## 14. Suggested next invocation

`/refine` — both obligations need design tightening before implementation

## 15. Last user message (verbatim)

> "are those open items captured?"

## 16. Epistemic labels

- [FACT] 2 obligations in `.data/harvest/pending/` — verified by scanner
- [INFERENCE] both require skill design work, not just config changes

## 17. Suggested skills for next session

- `/refine` — tighten the task packets before implementing
- `/go` — once refined, execute the implementation

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-05T06:00 | 019fce56... | created — backlog-to-handoff bridge |
