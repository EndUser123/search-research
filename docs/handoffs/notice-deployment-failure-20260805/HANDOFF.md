# Handoff — /notice deployment-layer failure diagnosis

## Status
OPEN — needs design decision.

## Diagnosis

/notice is a sophisticated skill with 13 triggers, motivation scoring, and
adaptive calibration. But it has produced **1 observation in 10 days**
(2026-07-26). The operator has never seen it work.

**Root cause:** deployment-layer failure (same pattern as harvest).
/notice is a skill that requires manual invocation. The end-of-turn
observation rule in AGENTS.md is prose (~50% compliance ceiling).
Neither fires under session pressure.

The SKILL.md explicitly says "skill not hook — deference requires
discretion; hooks are unconditional." But the trade-off is: discretion
requires firing, and firing doesn't happen. The result is a sophisticated
detection engine that nobody triggers.

## Options

1. **Stop hook:** make /notice fire as a Stop hook that runs the detection
   logic at every turn end. Adds ~2-5s latency per turn. The discretion is
   preserved by the motivation scoring (the hook can still choose silence).
   Risk: adds latency; hook timeout management.

2. **Embed into /tp session:** the CROSS-DOMAIN NOTICES section of /tp
   session already covers some of the same ground (skill composition
   patterns, improvement opportunities). Add /notice's trigger types as
   additional checks during /tp session. No latency cost. But /tp session
   fires only at session end or on manual invocation — still doesn't
   solve mid-session detection.

3. **Embed into the Stop-text-log hook:** the existing Stop_text_log.py
   already captures every turn. Extend it to also run a lightweight
   trigger check (T1 error state, T3 stuck-loop) and write candidates
   to state. /notice (manual invocation) then reads the accumulated
   candidates instead of running detection from scratch.

4. **Retire:** if the detection value is too low to justify the complexity.
   The end-of-turn observation rule + /tp session + /capture may cover
   enough of the same ground.

## Key files
- `~/.grok/skills/notice/SKILL.md` — 13 triggers, v2.5
- `~/.grok/state/notice-observations.jsonl` — 1 entry in 10 days
- `~/.grok/state/notice-cooldown.json` — cooldown state

## Handoff is wrong if
- The end-of-turn observation rule is actually firing but observations
  are being filtered out by the motivation threshold (check state files)
