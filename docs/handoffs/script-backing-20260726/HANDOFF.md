---
current_session_id: 019f8b39-95e3-7121-a8de-4e3f117e511a
last_updated_by: 019f8b39-95e3-7121-a8de-4e3f117e511a
last_updated_at: 2026-07-26T22:02:40.921048
parent_session: none
produced_at: 2026-07-26T22:02:40.921048
status: open
handoff_type: investigation
---
# Handoff: Script-backing for rules shipped 2026-07-26

**Thread ID:** 019f9f4f-script-backing-20260726
**Parent handoff:** none
**Status:** ready-for-execution
**Estimated scope:** 3 small Python scripts + minimal tests; ~half-day for a fresh session
**Authority boundary:** additive only — creates new state files and computation helpers; does NOT modify any existing skill logic or hook dispatch

---

## Objective

Three skills shipped rule-shaped this session (`/notice`, `/aar` Phase 4, `/aar` Phase 8.5). Each references state files or computations that don't exist yet. The rules are correct as written — they degrade gracefully (silent when state is absent) — but they cannot fire mechanically without script backing. This handoff scopes the minimum script work to make them fire.

**Anti-"smallest viable" rule applies.** Don't ship one-off helpers; ship small but properly-tested modules that future skills can consume. Specifically: the signal-baseline computation should be a reusable module, not inline in `/aar`.

## The three gaps

### Gap 1: `/notice` state files

`/notice` SKILL.md (committed `3034e02`) references two state files that don't exist:

- `~/.grok/state/notice-cooldown.json` — tracks `{session_id, last_surfaced_turn, turn_count_at_last_surfaced, calibration}`. Read at start of every `/notice` invocation to enforce the cooldown gate. Written after every surfaced observation. Default calibration: `rare` (1 per 10 turns); hard floor: 1 per 5 turns.
- `~/.grok/state/notice-observations.jsonl` — append-only log of surfaced observations AND dropped candidates (with drop reason). Consumed by `/aar` Phase 4 for cross-session signal synthesis.

**Acceptance criteria:**
- [ ] `notice_state.py` module at `~/.grok/skills/notice/__lib/notice_state.py` with: `read_cooldown(session_id) -> dict | None`, `write_cooldown(session_id, turn_count, calibration)`, `append_observation(session_id, observation, status, reason=None)`, `is_within_cooldown(session_id, calibration) -> bool`
- [ ] Atomic write (tmp + `os.replace`); utf-8 encoding
- [ ] Graceful degradation: missing state file → behave as if first invocation (no cooldown, no observations)
- [ ] Schema documented in module docstring
- [ ] Tests at `~/.grok/skills/notice/tests/test_notice_state.py` covering: missing state, write-read roundtrip, cooldown math at each calibration, append-idempotency

### Gap 2: `/aar` Phase 8.5 profile-review state

`/aar` Phase 8.5 step 7 (committed `33e17bd`) references `~/.grok/state/profile-review.json` for refresh-trigger dismissal. The step says: "dismissing the flag resets a `profile_reviewed_at` timestamp at `~/.grok/state/profile-review.json` without touching content."

The state file doesn't exist. Without it, the dismissal doesn't persist — every `/aar` run re-flags the operator profile as needing review even after they've dismissed it.

**Acceptance criteria:**
- [ ] `profile_review.py` module at `~/.grok/skills/aar/__lib/profile_review.py` with: `get_last_reviewed() -> str (ISO date) | None`, `mark_reviewed(date=None)`, `needs_review(threshold_days=90) -> tuple[bool, str]` (returns (needs_review, detail_message))
- [ ] Atomic write (tmp + `os.replace`); utf-8 encoding
- [ ] Graceful degradation: missing file → `get_last_reviewed()` returns None → `needs_review()` returns `(True, "never reviewed")`
- [ ] Tests at `~/.grok/skills/aar/tests/test_profile_review.py` covering: missing file, mark+read roundtrip, threshold math at 90/180/365 days

### Gap 3: `/aar` Phase 4 signal baseline computation

`/aar` Phase 4 `operator_signal_delta` block (committed `33e17bd`) emits: `pushback_count`, `pushback_categories`, `trust_loss_markers`, `reactive_adversarial_invocations`, `meta_cognition_verbs`, `deferred_persistence_count`, `friction_signal_baseline_delta`. The last one requires a baseline from the last 10 sessions (or 30 days, whichever is smaller). No computation exists.

**Acceptance criteria:**
- [ ] `signal_baseline.py` module at `~/.grok/skills/aar/__lib/signal_baseline.py` with: `compute_baseline(session_ids: list[str]) -> dict[str, float]` (mean per signal across sessions), `compute_delta(current_signals: dict, baseline: dict) -> dict[str, float]` (current/baseline ratio per signal)
- [ ] Input: list of session IDs → read each session's AAR report (if completed) → extract the 6 signals → average. If <3 prior sessions have data, return `{"baseline": "insufficient"}` and `compute_delta` returns the current signals unchanged with a `baseline: insufficient` flag.
- [ ] Tests at `~/.grok/skills/aar/tests/test_signal_baseline.py` covering: empty input, <3 sessions, ≥3 sessions with mixed data, current/baseline delta math, division-by-zero guard (baseline=0)

## What this handoff does NOT include

- **No changes to SKILL.md files.** The rules are correct; only the script backing is missing.
- **No hook or dispatch changes.** These are state-management modules consumed by skills, not runtime hooks.
- **No `/dream` Pass 4 backing.** Pass 4 is proposal-only (operator promotes via `/wiki` write flow); it doesn't need state files to function. If `/dream` Pass 4 later needs state (e.g., to track proposals the operator has rejected to avoid re-proposing), that's a separate handoff.
- **No live transcript reading for /notice.** The current /notice design reads `/aar` Phase 4 signals (post-session) and the current transcript for T1/T2/T3 triggers. Live mid-turn transcript reading is a v2 enhancement, deferred until T1/T2/T3 fire rate is measured.

## Verification path

After implementation:
1. Run `/notice` — should not crash; should report "first invocation, no cooldown" or similar
2. Run `/aar` on a recent session — Phase 4 should emit signals with `baseline: insufficient` (since <3 sessions have data); Phase 8.5 step 7 should fire correctly with profile-age check
3. All three test files pass: `python -m pytest ~/.grok/skills/notice/tests/ ~/.grok/skills/aar/tests/test_profile_review.py ~/.grok/skills/aar/tests/test_signal_baseline.py`

## Why this is a handoff not a do-now

- **Three independent modules** — clean parallelization for a fresh session
- **Mechanical scope** — well-defined inputs, outputs, acceptance criteria; no design decisions
- **Session fatigue** — current session has shipped 4 skills + 5 wiki concepts + 1 hook fix; script backing is the kind of mechanical work that benefits from fresh attention
- **Compounding cost is low** — the rules degrade gracefully without the scripts; the cost of not-doing is that /notice never fires mechanically and /aar Phase 8.5 re-flags every run, neither of which compounds

## Related artifacts

- `/notice` SKILL.md: `~/.grok/skills/notice/SKILL.md` (committed `3034e02`)
- `/aar` Phase 4 emissions: `~/.grok/skills/aar/SKILL.md` § "Operator signal delta" (committed `33e17bd`)
- `/aar` Phase 8.5 step 7: `~/.grok/skills/aar/SKILL.md` § "Operator profile age" (committed `33e17bd`)
- Research base: `P:/.data/wiki/concepts/proactive-ai-volunteering-mechanisms.md`
- Operator-modeling concept: `P:/.data/wiki/concepts/user-modeling-for-agentic-clis.md`

## Open questions for the next session

1. Should the signal-baseline computation live in `/aar/__lib/` or in a shared `~/.grok/__lib/signals/` so `/dream` Pass 4 and `/notice` can consume it too? **Recommendation: shared** — three consumers visible already (`/aar` produces, `/notice` consumes live, `/dream` Pass 4 consumes for drift detection).
2. Should `/notice` observations log rotate, or grow unbounded? **Recommendation: rotate at 1000 lines** — keeps `/aar` synthesis input bounded.
3. Should `profile_review.py` support multiple profiles (one per operator persona), or just one? **Recommendation: one for now** — YAGNI until there's evidence of multiple-operator use.

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-07-26T22:02 | 019f8b39-95e... | backfilled session_id from transcript scan |
