# Stop Hook Advisory Loop Gap — Decision Packet

**Date:** 2026-07-01
**Status:** Ready for parent review (mechanism verified; fix design proposed, not implemented)
**Scope:** `P:/.claude/hooks/` Stop hook loop-protection infrastructure

## Problem statement

A Stop hook loop was observed in a prior session: the agent stated intent to
dispatch a subagent but did not emit the tool call; the semantic critic fired
correctly, flagging the incomplete response; the advisory re-entered the loop
as task fuel, and the cycle repeated across several user-driven turns ("dispatch
NOW", "dispatch the subagent") without any loop protection engaging. The agent
was eventually killed manually.

This packet documents the verified mechanism and proposes a fix design. Per
workspace review discipline, no implementation has been done — the mechanism is
verified end-to-end, the fix is an inference that needs validation.

## Verified facts (code-confirmed)

### V1. The hooks run through a single in-process orchestrator.

`P:/.claude/settings.json` wires three Stop commands. The first,
`hook_runner.py Stop.py`, runs a 4,966-line consolidated orchestrator that
imports and calls ~30 gate functions in a single process per Stop event. The
per-plugin `hooks.json` files (e.g. `cc-aca-epistemic/hooks/hooks.json` =
`{"hooks": {}}`) are unused source artifacts.

**Refs:** `P:/.claude/settings.json` (Stop section);
`P:/.claude/hooks/__lib/hook_runner.py:340-519` (`safe_run` uses
`runpy.run_path` per invocation, then exits).

### V2. Stop hooks execute as a fresh subprocess per Stop event.

`hook_runner.py` is invoked by Claude Code as `python hook_runner.py Stop.py`.
Each invocation is a fresh Python process. `safe_run()` executes the hook via
`runpy.run_path()` as `__main__`, the process exits, and the next Stop event
spawns a new process.

**Consequence:** any in-memory state (module-level dicts, counters) is recreated
empty on every Stop invocation and cannot accumulate across turns.

**Refs:** `hook_runner.py:429` (`runpy.run_path`); `hook_runner.py:521-530`
(`main()` → `sys.exit`).

### V3. The semantic critic's per-session cap is non-functional.

`Stop_semantic_critic.py` declares `SEMANTIC_CRITIC_CAP = 5` and tracks counts
in a module-level dict `_INVOCATION_COUNTS` (line 60). Because each Stop event
is a fresh process (V2), this dict is always empty at start. The cap can never
accumulate past 1 and never binds. The same is true for `_VERIDICAL_COUNTS`
(line 206) and `_VERIDICAL_FAILURE_STREAK` (line 207).

**Refs:** `Stop_semantic_critic.py:60-65` (cap declaration); `:1213-1221` (cap
check, reads `_INVOCATION_COUNTS`); `:212-224` (`_session_key` derivation —
correct, but moot since the backing dict resets).

### V4. The circuit breaker IS functional and file-based.

`__lib/circuit_breaker.py` persists iteration counts to
`~/.claude/hooks/iteration_count_{session_id}.tmp` with `FileLock`
(lines 62-96). Despite docstrings labeling the functions "RED PHASE: Stub"
(lines 103, 113, 123, 146), the implementations are real and operational. The
breaker correctly bounds block-path loops at threshold=3 across subprocesses.

**Refs:** `circuit_breaker.py:62-96` (file-based `CircuitBreaker` class);
`:129-158` (`should_allow_continue`, real logic).

### V5. The circuit breaker only counts when `stop_hook_active=True`.

`should_allow_continue()` returns `False` (do not trip) immediately when
`stop_hook_active` is false (circuit_breaker.py:148-150). Separately, at the
top of each Stop invocation, if `stop_hook_active` is false, the iteration
counter is **reset to zero** (Stop.py:4611-4617).

**Design intent (per comment, Stop.py:4607-4609):** "so quality-gate block
counts never bleed across unrelated turns." The reset prevents stale counts
from one task suppressing blocks in a later, unrelated task.

**Refs:** `circuit_breaker.py:148-150`; `Stop.py:4607-4619`.

### V6. The semantic critic's `general_diagnostic` profile stays advisory.

`_run_semantic_critic` (Stop.py:455-517) escalates to `decision: block` only for
high-signal profiles (`evaluative_recommendation`, `software_rca`) when rollout
is BLOCK (Stop.py:505-516). The `general_diagnostic` profile — which fired in
the observed loop, identified by its remediation template "State the contract
before concluding..." — stays advisory (`{"allow": True, "systemMessage": ...}`,
Stop_semantic_critic.py:1270). Advisory returns do not have `decision: block`,
so they do not flow through the block path of `_process_gate_result` and never
reach the circuit breaker.

**Refs:** `Stop.py:505-516`; `Stop_semantic_critic.py:608-631` (remediation
templates, identifying `general_diagnostic`); `:1268-1270` (advisory return).

### V7. Advisory output DOES reach `_raw_messages`.

Any gate result with a `systemMessage` is appended to `_raw_messages` as
`(name, "warn", message)` regardless of whether it blocked (Stop.py:4807-4808).
The semantic critic's advisory return has `systemMessage`, so
`("semantic_critic", "warn", "<advisory text>")` lands in `_raw_messages`.

**Refs:** `Stop.py:4805-4808`.

### V8. `_raw_messages` is written to cross-turn state AND read back next turn.

- **Write:** at Stop.py:4833-4846, if `_raw_messages` is non-empty, the hook
  names are written to `last_violations.json` via `set_last_violations`
  (`hook_state_manager`, file-based at
  `~/.claude/.artifacts/{terminal_id}/hook_state/`).
- **Read:** when `repetition_blocker` is about to run, `all_violations` is
  populated from `_raw_messages` (Stop.py:4671-4675) as
  `{"type": hook_name, ...}`, so `"semantic_critic"` appears as a violation
  type.

**Refs:** `Stop.py:4671-4675` (populate `all_violations`);
`Stop.py:4833-4846` (write `last_violations`); `hook_state_manager.py:41-45`
(file-based state dir).

### V9. `repetition_blocker` has the right persistence model but the wrong coverage set.

`Stop_repetition_blocker.py`:
- Uses `hook_state_manager` (file-based, survives subprocess, no
  `stop_hook_active` gate) — correct on both counts where the circuit breaker
  is wrong.
- Has gradual escalation: `_LAZY_ESCALATION_TYPES` (advisory → warning → block)
  and `_IMMEDIATE_BLOCK_TYPES` (block on repetition), plus a generic branch.
- **Does NOT include `"semantic_critic"`** in either escalation set (lines
  46-67). The generic branch (lines 113-118) applies: block on count >= 2,
  but only when `check_violation_repeated` returns `is_repeated=True`, which
  requires the violation to have appeared in the *immediately previous* turn's
  `last_violations`.

**Refs:** `Stop_repetition_blocker.py:46-67` (escalation sets, `semantic_critic`
absent); `:97-118` (escalation logic); `:100-102` (`check_violation_repeated`
gates on consecutive appearance).

### V10. `acknowledgment_loop` is intra-turn only.

`Stop_acknowledgment_loop.py` detects acknowledgment + same-violation within a
*single response* (line 13: "No persistent state needed — this is a per-turn
intra-output check"). It structurally cannot detect cross-turn loops and
provides no coverage for this failure mode.

**Refs:** `Stop_acknowledgment_loop.py:7-13`.

## The three gaps (synthesis of V3-V10)

The observed loop fell through three independent gaps simultaneously:

| # | Gap | Ref | Effect |
|---|---|---|---|
| **A** | Advisory path bypasses the circuit breaker | V6 | `general_diagnostic` advisory never produces `decision: block`; breaker never sees it |
| **B** | Breaker resets on fresh user turns | V5 | Even block-path loops driven by repeated user messages reset the counter each turn (`stop_hook_active=False`) |
| **C** | `repetition_blocker` doesn't classify critic advisories as trackable | V9 | The one mechanism with the right persistence model doesn't escalate `semantic_critic` |

**Gap B is systemic:** any quality-class block loop with the shape "user message
→ flagged output → block → user message (repeat) → ..." is invisible to the
circuit breaker. The reset-at-fresh-turn logic assumes fresh user turn =
unrelated to prior turn, which breaks when the user is repeating the same
request because the agent didn't act.

## Inferences (not yet measured)

### I1. The loop was user-driven, so `stop_hook_active` was False throughout.

Strongly inferred from the transcript structure: each "dispatch NOW" /
"dispatch the subagent" is a fresh user message, not a hook-forced regeneration.
Claude Code sets `stop_hook_active=True` only during forced-regeneration
continuations. If this inference holds, Gap B definitively explains why the
breaker never engaged even for block-path gates.

**Not verified:** I cannot read the runtime `data` dict from the past session
to confirm `stop_hook_active` was False. This needs session log confirmation.

### I2. `repetition_blocker`'s generic branch *might* have caught a 3-occurrence loop — but probably didn't.

The generic branch (V9) blocks on count >= 2 for unrecognized types. In theory
this could have caught the loop on the 3rd critic fire. Two reasons it likely
didn't:
- `check_violation_repeated` requires *consecutive* turn appearance. If the
  critic skipped any intermediate turn (because the agent's response was short,
  non-diagnostic, or classified non-substantive), `is_repeated` would be false
  and escalation wouldn't trigger despite cumulative repetition.
- The count increment only fires for types in the *current* turn's
  `current_violation_types`, same gap.

**Not verified:** whether the critic actually fired on every consecutive turn
in the observed loop. Needs session logs.

### I3. The fix design (below) would break the loop.

The fix relies on components all verified functional (V4, V8, V9's persistence).
The additive change is small. But whether the specific threshold and repetition
semantics (consecutive vs. cumulative) actually catch real-world advisory loops
needs calibration against real sessions — not provable from code alone.

## Proposed fix design (inference — not implemented)

**Location:** `Stop_repetition_blocker.py` — the only mechanism with both
file-based persistence and no `stop_hook_active` gate.

**Change:** add a third escalation category for quality-gate advisory names:

```python
# Quality-gate advisories: lower-signal than policy violations, so escalate
# gradually with a higher threshold. These reach _raw_messages via systemMessage
# (Stop.py:4807-4808) and are written to last_violations as the gate name.
_QUALITY_ADVISORY_ESCALATION_TYPES = frozenset({
    "semantic_critic",
    "diagnostic_analysis_quality",
    # Add other quality-class advisory gates as needed
})

_QUALITY_ADVISORY_BLOCK_THRESHOLD = 3  # block on 4th+ occurrence within window
```

In the escalation loop, add a branch for this set with cumulative-within-window
counting rather than the consecutive-only `check_violation_repeated` gate:

```python
elif vtype in _QUALITY_ADVISORY_ESCALATION_TYPES:
    count = get_violation_count(terminal_id, session_id, vtype)
    if count >= _QUALITY_ADVISORY_BLOCK_THRESHOLD:
        blocking_types.add(vtype)
    elif count >= 1:
        warning_types.add(vtype)
```

**Why this location and not the circuit breaker:**
- Gap B's coupling (stale-count prevention ↔ loop detection) makes changing the
  breaker risky — loosening the reset could reintroduce cross-task count
  contamination.
- `repetition_blocker` already has the right design; this extends its coverage
  set additively. No structural change to existing escalation paths.

**Why cumulative-within-window, not consecutive:**
- Advisory loops often interleave with non-advisory turns (the agent produces a
  short acknowledgment that doesn't trigger the critic, then resumes the
  incomplete analysis). Consecutive-only detection (I2) misses these.
- The `hook_state_manager` already supports count tracking; a time-window decay
  (e.g. reset counts older than 10 minutes) would prevent stale cross-task
  contamination — the same concern Gap B's reset solves, but scoped to the
  blocker rather than the global breaker.

**Defense in depth — declarative reframe of remediation templates:**
Independently worthwhile. The imperative phrasing ("State the contract before
concluding...") reads as an assignable task, which is what makes advisory output
behave as loop fuel. Reframing to declarative ("The response did not state the
contract before concluding.") carries the identical critique but reduces the
agent's tendency to treat it as new work. This is in `Stop_semantic_critic.py`
REMEDIATION_TEMPLATES (lines 608-631). Does not depend on the blocker fix.

## Open questions (require evidence gathering before implementation)

### Q1. Consecutive vs. cumulative repetition for advisories.

Does the critic fire on every turn of a real advisory loop, or does it skip
intermediate turns? This determines whether the blocker's existing
consecutive-required `check_violation_repeated` is sufficient or whether the
cumulative-within-window design is necessary.

**How to answer:** inspect session logs (`~/.claude/hooks/logs/diagnostics/`)
for prior advisory-loop sessions; count critic fires per turn and check for
gaps.

### Q2. The right threshold for advisory escalation.

`_QUALITY_ADVISORY_BLOCK_THRESHOLD = 3` is a guess. Too low and legitimate
iterative refinement gets blocked; too high and loops persist too long.

**How to answer:** calibrate against real sessions after a shadow-mode rollout
(log would-escalate events without blocking).

### Q3. Was `stop_hook_active` definitively False in the observed loop? (validates I1)

**How to answer:** the regen cap telemetry log
(`~/.claude/hooks/logs/diagnostics/regen_cap_telemetry.jsonl`, written at
Stop.py:4201) records `stop_hook_active` per gate event. Checking this for the
looping session would confirm Gap B as the cause and quantify how many turns
elapsed.

### Q4. Are there other quality-class advisory gates with the same gap?

`semantic_critic` and `diagnostic_analysis_quality` are confirmed. A full audit
of `GATE_METADATA` for `class: quality` + `rollout_mode: ADVISORY-or-profile-gated`
gates would identify every gate that falls through the same three-gap chain.

## What was NOT verified

- The runtime value of `stop_hook_active` during the observed loop (I1, Q3).
- Whether the critic fired on every consecutive turn (I2, Q1).
- Whether the proposed threshold is appropriate (Q2).
- Whether the fix interacts safely with `_get_rollout_mode` env overrides
  (Stop.py:3526-3538) — the rollout for `semantic_critic` can be forced to
  ADVISORY via `STOP_GATE_ROLLOUT_SEMANTIC_CRITIC=advisory`, which downgrades
  block→warn at Stop.py:4730-4733. The blocker fix is downstream of this
  downgrade and should still fire, but this hasn't been traced end-to-end.
- Whether `_raw_messages` population order guarantees `semantic_critic` appears
  before `repetition_blocker` writes state — confirmed at V7/V8, but the
  gate execution order in `IN_PROCESS_GATES` (Stop.py:4035+) should be checked
  to ensure the blocker runs after the critic.

## Recommendation

Per review discipline, the next allowed action is **evidence gathering** (Q1-Q4),
not implementation. The highest-value evidence is Q3 (the telemetry log), which
would confirm Gap B as the root cause and is a single file read. Q1 and Q4 are
secondary — they refine the fix scope but don't change the design.

If evidence confirms the mechanism, the fix is small and additive
(`Stop_repetition_blocker.py` + optional `Stop_semantic_critic.py` reframe) and
should ship behind a shadow-mode flag for threshold calibration (Q2) before
enforcement.
