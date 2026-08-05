---
thread_id: skill-script-defects-cleanup-20260805
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

# Handoff — Skill script defects cleanup (121 defects across 6 skills)

## 1. Objective

Fix 121 code-level defects (lint findings from `script_scan.py`) across 6 skills' `__lib/` Python scripts.

## 2. Status

OPEN — discovered by `/todo` scanner, never previously handed off.

## 3. Producing context

- **Date:** 2026-08-05
- **Source:** `/todo` scanner (`skill_scripts` source)
- **Scanner command:** `python ~/.grok/skills/todo/__lib/scan_functions.py`

## 4. Read-first list

1. `/todo` scanner output — run `python ~/.grok/skills/todo/__lib/scan_functions.py --source skill_scripts` for current defect list
2. Per-skill `__lib/` directories — see defect counts below

## 5. Verified facts

- [FACT] Defect counts (from `/todo` scan 2026-08-05T04:57Z):
  - `close`: 61 defects (close_accounting.py: 39, close_authority.py: 2, close_runner.py: 2, others)
  - `ship-py`: 24 defects (ship_receipt.py: 23)
  - `aar`: 12 defects
  - `model-web`: 11 defects (SKILL.md craft: 2, fusion_orchestrate.py: 4, run_state.py: 5)
  - `handoff`: 9 defects
  - `tp`: 4 defects (SKILL.md craft: 1, agy_lens.py: 1, tp_critique_log.py: 1, tp_display: 1)

## 6. Current state

These are lint findings, not runtime failures. The skills work despite the defects. Priority: close (61) and ship (24) have the most defects and are high-traffic skills.

## 7. Task packets

### AC-01: close skill (61 defects)
- **Goal:** fix 61 lint findings in close `__lib/` scripts
- **Files:** `~/.grok/skills/close/__lib/close_accounting.py` (39 findings), `close_authority.py` (2), `close_runner.py` (2)
- **Acceptance:** `script_scan.py --source skill_scripts` shows 0 defects for close
- **Falsifier:** any defect remains

### AC-02: ship skill (24 defects)
- **Goal:** fix 24 lint findings in ship `__lib/` scripts
- **Files:** `~/.grok/skills/ship-py/__lib/ship_receipt.py` (23 findings), SKILL.md (1 craft finding)
- **Acceptance:** `script_scan.py --source skill_scripts` shows 0 defects for ship
- **Falsifier:** any defect remains

### AC-03: aar, model-web, handoff, tp (36 defects total)
- **Goal:** fix remaining defects across 4 skills
- **Acceptance:** `script_scan.py --source skill_scripts` shows 0 defects for all 6 skills
- **Falsifier:** any defect remains

## 8. Open decisions

None.

## 9. Hard constraints

- Do NOT change runtime behavior — these are lint fixes, not logic changes
- Run existing tests after fixing each skill to ensure no regressions

## 10. Cross-reference couplings

- `/ship` Phase 3 runs `ship_receipt.py` — if the 23 findings are logic bugs, they may affect ship verification

## 11. Other outstanding streams

None for this work.

## 12. Explicit non-goals

- Do NOT refactor skill architecture while fixing lint findings
- Do NOT fix the `/ship` skill path confusion (ship vs ship-py vs ship-rhai) — that's a separate stream

## 13. Resumption protocol

1. Run `python ~/.grok/skills/todo/__lib/scan_functions.py --source skill_scripts` for current defect list
2. Start with AC-01 (close: 61 defects) — highest count, highest-traffic skill
3. Fix in worktree or directly on main with surgical commits

## 14. Suggested next invocation

`/maintain` — this is fleet maintenance work

## 15. Last user message (verbatim)

> "are those open items captured?"

## 16. Epistemic labels

- [FACT] defect counts verified by `/todo` scanner run at 2026-08-05T04:57Z
- [INFERENCE] "lint findings, not runtime failures" — the skills are in active use and working

## 17. Suggested skills for next session

- `/maintain` — fleet maintenance orchestrator
- `/check` — after fixing defects, verify no regressions

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-05T06:00 | 019fce56... | created — backlog-to-handoff bridge |
