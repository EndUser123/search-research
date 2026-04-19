# Replacement ADR + Plan: RCA Enforcement Refactor Aligned to Live Hook Wiring

## Summary

This replaces the current draft with a live-wiring-safe plan.

The direction is better than the original plan, but implementation must shift from “new generic hooks + env toggle + adversarial-rca-first” to “one RCA-specific structural gate on the existing `debugRCA` path, reusing current hook data and keeping only mechanically verifiable blocks hard.”

The core decision is:

- Keep **hard enforcement** for objective omissions and false completion.
- Remove **hard prose-policing** for RCA turns.
- Implement on the **currently enforced RCA path first** (`debugRCA`), not on a parallel skill path.
- Use **turn-scoped `skill_state`**, not a global env toggle, to activate RCA behavior.

## ADR Decisions

### 1. Scope and entrypoint
- Treat `debugRCA` as the production RCA workflow for this refactor because current hooks, tests, and skill-state plumbing already recognize it.
- Update [debugRCA SKILL.md](P:/.claude/skills/debugRCA/SKILL.md) first.
- Keep [adversarial-rca SKILL.md](P:/.claude/skills/adversarial-rca/SKILL.md) in sync as documentation/methodology parity only.
- Do not introduce separate enforcement logic for `adversarial-rca` in this change.
- If the long-term goal is to replace `debugRCA` with `adversarial-rca`, that is a separate migration ADR.

### 2. Activation model
- Do not use `RCA_CONTRACT_MODE` as the per-turn activation mechanism.
- Derive RCA mode from existing turn-scoped metadata already present in [Stop_router.py](P:/.claude/hooks/Stop_router.py), primarily `skill_state`.
- Add one derived field to downstream Stop-hook input:
  - `rca_turn: bool`
  - `rca_skill: str | None`
- Allow a normal rollout flag such as `RCA_CONTRACT_GATE_ENABLED` for enabling/disabling the new hook globally, but not for deciding whether an individual turn is an RCA turn.

### 3. Enforcement model for RCA turns
- Add one new hard gate: `stop/StopHook_rca_contract.py`.
- Keep these hard for RCA turns:
  - `StopHook_skill_execution_gate.py`
  - `Stop_negative_existence_guard.py`
  - `stop/StopHook_directive_obligation.py`
  - `stop/Stop_verification_gate.py`
  - new `stop/StopHook_rca_contract.py`
- Change these for RCA turns:
  - `StopHook_overconfidence_detector.py`: advisory/log-only
  - `StopHook_step_header_verifier.py`: skipped for RCA turns to avoid duplicate format policing
  - `StopHook_unverified_stance.py`: split behavior so completion-claim verification remains hard, but rhetorical “system-behavior claim” regex enforcement is advisory/log-only for RCA turns
- Non-RCA turns keep current behavior unless separately changed.

### 4. No new durable RCA state
- The RCA contract hook must be stateless across turns.
- It must consume only current-turn data already materialized by the Stop router: `assistant_response`, `tool_events`, `skill_state`, snapshot metadata, and any existing turn markers/ledger data.
- Do not add terminal-scoped RCA contract files.
- Multi-terminal safety requirement: no new cross-turn shared mutable state.

### 5. RCA contract semantics
The contract is structural and evidence-linked, not tone-based.

Required sections in RCA responses:
- `Symptom`
- `Evidence`
- `Executed Path`
- `Alternative Hypothesis`
- `Falsifier`
- `Root Cause`
- `Fix`
- `Verification`

The new hook must validate more than section presence:
- `Evidence` must reference at least one actual file/tool observation from this turn.
- `Executed Path` must cite a reachable path supported by current-turn `Read`/`Grep`/`Bash` evidence.
- `Root Cause` must name a file/symbol/path that appears in or is directly supported by `Executed Path`.
- `Alternative Hypothesis` and `Falsifier` must both be present.
- If transcript-time or historical evidence is used, it must be labeled as such; current-state and transcript-time evidence must not be merged implicitly.
- “Missing TTL” or similar static defects must not be accepted as root cause unless the current-turn evidence shows the live path consumes that state/function.

The hook should block on missing structural evidence, not on phrasing style.

## Implementation Changes

### A. Stop router and active-hook policy
- Modify [Stop_router.py](P:/.claude/hooks/Stop_router.py) to derive `rca_turn` and `rca_skill` from `skill_state`.
- Extend hook input payload with those derived fields.
- Add `stop/StopHook_rca_contract.py` to `HOOK_SEQUENCE` and `ACTIVE_RUNTIME_HOOKS`.
- Add RCA-turn hook policy so the router:
  - skips `StopHook_step_header_verifier.py`
  - forces advisory normalization for `StopHook_overconfidence_detector.py`
  - runs only the completion-claim portion of `StopHook_unverified_stance.py`, or passes a flag telling that hook to suppress rhetorical system-claim blocking in RCA mode

### B. RCA contract hook
- Create `P:/.claude/hooks/stop/StopHook_rca_contract.py`.
- Implement as in-process `run(data)` hook compatible with the current Stop router.
- Reuse existing telemetry/logging infrastructure under [__lib](P:/.claude/hooks/__lib), not a new path.
- Emit block reasons that explain the missing structural proof, for example:
  - missing executed path
  - root cause named without reachability proof
  - negative existence claim not backed by same-turn evidence
  - transcript-time evidence used without labeling
- Do not inspect wording like “clearly,” “definitely,” or “the system is broken.”

### C. Existing hook reuse instead of new PreToolUse hook
- Do **not** add `PreToolUse_unverified_claims_gate.py`.
- Reason: negative-existence claims happen in final responses, and this repo already has a live, turn-scoped Stop guard for them in [Stop_negative_existence_guard.py](P:/.claude/hooks/Stop_negative_existence_guard.py).
- Instead:
  - keep `Stop_negative_existence_guard.py` hard for RCA turns
  - optionally extend [PreToolUse_observe_before_act_gate.py](P:/.claude/hooks/PreToolUse_observe_before_act_gate.py) with RCA-aware observation messaging if needed, but do not use PreToolUse as the primary negative-existence claim enforcer

### D. `debugRCA` workflow update
- Update [debugRCA SKILL.md](P:/.claude/skills/debugRCA/SKILL.md) to require:
  - executed-path-first analysis
  - reachability proof before naming a code location as causal
  - one competing hypothesis plus explicit falsifier
  - time-scope labels: `current-state`, `transcript-time`, `inference`
  - no fix plan before executed path is shown
- Required output format for `debugRCA` must match the new RCA contract headings exactly.
- Keep the workflow human-readable; do not require JSON output.

### E. `adversarial-rca` and memory updates
- Update [adversarial-rca SKILL.md](P:/.claude/skills/adversarial-rca/SKILL.md) to mirror the same reasoning methodology, but note that enforcement remains on the production `debugRCA` path for now.
- Update the canonical repo memory file [MEMORY.md](P:/.claude/memory/MEMORY.md) with only stable lessons:
  - prove reachability before naming a cause
  - stale state is not causal unless the live path consumes it
  - separate transcript-time evidence from current-state evidence
  - do not collapse multiple symptoms into one RCA without a proven shared path
- Do not store case-specific bug details there.
- If another project-level memory mirror is maintained automatically, keep that sync mechanism unchanged rather than editing two canonical files manually.

## Test Plan

### Router and activation tests
- Add tests showing RCA mode is derived from `skill_state`, not from a global env toggle.
- Add tests proving non-RCA turns preserve current hook behavior.
- Add tests proving RCA turns skip only the intended hooks and keep hard objective guards enabled.

### RCA contract tests
- Missing `Executed Path` blocks.
- `Root Cause` named without same-turn reachability evidence blocks.
- `Alternative Hypothesis` without `Falsifier` blocks.
- Transcript-only evidence without scope labeling blocks.
- Properly structured RCA with current-turn evidence passes.

### Regression tests from the observed failures
- Add transcript-based fixtures covering the TTL/dead-code misdiagnosis pattern.
- Assert the RCA contract blocks “dead code defect as root cause” when no call-site/path proof exists.
- Assert the later `close_turn()`-style analysis would pass once the executed path is shown.

### Existing objective-guard compatibility tests
- `Stop_negative_existence_guard.py` still blocks unverified “no such” claims during RCA turns.
- `stop/StopHook_directive_obligation.py` still blocks unmet explicit fetch directives during RCA turns.
- Completion/fix verification remains hard-blocked during RCA turns.

## Assumptions and Defaults

- `debugRCA` remains the enforced RCA path in this change.
- `adversarial-rca` gets methodology parity, not separate runtime enforcement.
- No new process-wide RCA mode env var is introduced for per-turn routing.
- One standard enable flag for the new hook is acceptable for rollout, defaulting to enabled only when ready.
- No new terminal-scoped or session-scoped RCA state files are added.
- The preferred implementation path is to reuse current router payloads, hook ledger snapshots, and existing objective guards rather than add more overlapping hooks.
