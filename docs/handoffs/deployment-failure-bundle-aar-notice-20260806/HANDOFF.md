# Handoff — deployment-failure bundle: /aar auto-capture + /notice embed

## Status
OPEN — execution-ready, needs fresh session (multi-hour engineering).

## Objective

Two skills share the same deployment-failure pattern: sophisticated detection
logic trapped behind manual invocation. Embed them into automated flows.

## Item 1: /aar detection→capture auto-promotion pipeline

**Problem:** `/aar` has 32 detectors in `C:/Users/brsth/.grok/skills/aar/__lib/detectors.py`
(was incorrectly documented as 12; corrected in wiki concept commit 5d47c62).
Of these, 6 are directly relevant to wiki-worthy auto-capture:

| Detector | Line | Severity | Why relevant |
|----------|------|----------|-------------|
| `detect_user_corrections` | 726 | HIGH | Primary signal — operator corrections |
| `detect_assistant_self_corrections` | 697 | MEDIUM | Tacit knowledge revised mid-session |
| `detect_successful_interventions` | 1345 | MEDIUM | Recovery patterns worth capturing |
| `detect_recommendation_revisions` | 1309 | MEDIUM | Changed recommendations = decisions with rationale |
| `detect_correction_propagation_failure` | 1647 | LOW | Structural gaps to document |
| `detect_context_rederivation` | 1998 | MEDIUM | Same file read ≥3 times = missing wiki concept |

**The gap:** when `/aar` detects any of these signals, it produces a report.
Nobody reads the report unless they explicitly run `/aar`. The missing piece
is: detected signal → run wiki-worthy gate (6 checks from /tp SKILL.md
Step 3 "Wiki save" section) → auto-write concept if it passes.

**Acceptance criteria:**
- A pipeline script that runs the 6 relevant detectors on session transcripts
- Each detected signal is passed through the wiki-worthy gate (structural,
  falsifier, evidence citation, named abstractly, cross-session reusable,
  not already in wiki)
- Passing signals produce a candidate wiki concept at `P:/tmp/auto-capture-candidates/`
- The operator reviews candidates (not fully automated — quality filter)
- Smoke test: run on a recent session with known corrections, verify it
  produces a candidate that matches what a human would have captured

**Key files:**
- `C:/Users/brsth/.grok/skills/aar/__lib/detectors.py` (32 detectors, 102KB)
- `C:/Users/brsth/.grok/skills/tp/SKILL.md` § "Wiki save" (6-check gate, line ~1550)
- `P:/.data/wiki/concepts/agent-improvement-loop-patterns-automated-learning-from-traces.md`
  (corrected concept with the 6-detector table)

**Use a worktree** if touching detectors.py — sibling sessions edit it
concurrently (mtime 2026-08-05 14:50).

## Item 2: /notice deployment-failure fix

**Problem:** `/notice` has 13 triggers and sophisticated motivation scoring.
It has produced 1 observation in 10 days. The detection engine never fires
because it requires manual `/notice` invocation.

**State files:**
- `C:/Users/brsth/.grok/state/notice-observations.jsonl` — 1 entry (2026-07-26)
- `C:/Users/brsth/.grok/state/notice-cooldown.json` — does NOT exist yet

**Four options (from the original handoff):**
1. **Stop hook** — run detection at every turn end. ~2-5s latency. Discretion preserved by motivation scoring.
2. **Embed into /tp session** — add /notice triggers as CROSS-DOMAIN NOTICES checks. No latency, but only fires at session end.
3. **Embed into Stop-text-log hook** — extend `Stop_text_log.py` to run lightweight trigger checks (T1 error state, T3 stuck-loop), write candidates to state. /notice reads accumulated candidates.
4. **Retire** — end-of-turn observation rule + /tp session + /capture may cover enough ground.

**Recommendation:** Option 3 (Stop-text-log embed). Lowest risk, reuses
existing hook infrastructure, doesn't add per-turn latency to the critical
path. The Stop-text-log hook already captures every turn; adding a trigger
check is an extension, not a new hook.

**Acceptance criteria:**
- Stop-text-log hook (or a new lightweight hook) writes trigger candidates to
  `C:/Users/brsth/.grok/state/notice-candidates.jsonl`
- `/notice` reads accumulated candidates instead of running detection from scratch
- Create `notice-cooldown.json` if the cooldown logic needs it
- Smoke test: simulate an error-state turn, verify a candidate is written

**Key files:**
- `C:/Users/brsth/.grok/skills/notice/SKILL.md` (13 triggers, v2.5)
- `C:/Users/brsth/.grok/hooks/scripts/Stop_text_log.py` (existing hook to extend)

## Provenance

- /tp critique session 019fd42f (2026-08-05/06)
- Wiki concepts: `[[non-use-signals-deployment-failure-not-capability-failure]]`,
  `[[mechanical-enforcement-over-behavioral-reminder]]`
- Wiki concept corrected: `agent-improvement-loop-patterns` (detectors 12→32)
- AGENTS.md rule for Item 1 (fabricated explanations) shipped separately
  (commit 1f0d1a8)

## Handoff is wrong if
- The 6 relevant detectors produce too many false positives for the wiki-worthy gate
- The Stop-text-log hook can't be extended without breaking existing functionality
- `/notice` Option 2 (/tp session embed) is simpler and sufficient
