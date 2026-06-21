# Handoff: Semantic critic — self-critique enforcement + tiered-review plan (2026-06-20)

Session origin: b2014a6e. Companion memory: `semantic-critic-subagent-fallback.md`
(shipped state + model-pool correction). This doc = the FORWARD plan, not yet built.

## Already SHIPPED & live (do not redo)
- `Stop.py` Change A: `semantic_critic.relevant_turn_kinds` += UNKNOWN
  (`_ANALYSIS_OR_UNKNOWN_TURN_KINDS`) — was silently skipping proposal turns.
- `Stop.py` Change B: `_run_semantic_critic` escalates a veto to `decision:block`
  ONLY for high-signal profiles {evaluative_recommendation, software_rca};
  revert via `STOP_GATE_ROLLOUT_SEMANTIC_CRITIC=advisory`.
- `Stop_semantic_critic.py`: coherent clamped fast-path budget (overall 8s < 10s
  outer hook), `BACKENDS_UNAVAILABLE` sentinel → run() emits subagent-delegation
  directive instead of fail-open.
- Tests: `tests/test_semantic_critic_enforcement.py`,
  `hooks/stop/tests/test_semantic_critic_subagent_fallback.py`. Plugin bumped 0.2.51.

## Dispatch facts (verified)
- Live Stop path: `P:/.claude/settings.json:310` → `hook_runner.py` → local
  `Stop.py` aggregator, which imports plugin gate code from SOURCE
  (`Stop.py:87-113`). cc-aca-epistemic is NOT a registered Stop router.
  Editing plugin SOURCE is live; bump only for cache coherence.
- Current combination = CONSERVATIVE VETO (`Stop_semantic_critic.py:1044`,
  any model ok=false → block). Critic JUDGES ANSWER ADEQUACY (redo), not
  "was a self-critique done" (`:323-338`).
- Model defaults stale: `glm-5.1`(:71)→glm-5.2, `mistral-medium-3.5`(:124)→
  mistral-medium-latest; minimax-M3 available. 3-model FAILOVER POOL, all usable;
  quota refresh ~5h (M3/GLM), mistral ~unlimited; a quota'd model is a non-event.

## HARDENED PLAN (after self-review found 4 flaws)
Self-review verdict: original "tiered verifier" plan was too aggressive — it
gutted a working detector on an UNMEASURED hypothesis and over-claimed reuse.
Flaws: (1) Tier-0 reuse false — cc-aca-reasoning self-reflection is
trigger-phrase gated (`sequential_thinking.py:94`) + advisory-only
(`Stop_self_reflection_gate.py:10`), so Tier-0 needs NEW always-on machinery;
(2) first-valid-wins would delete the conservative second opinion;
(3) verifier introduces a gameable "looks-like-a-critique" Goodhart surface;
(4) net detection could REGRESS with zero measurement.

### Phase 1 — low-risk, APPROVED-pending, do now
- Model IDs → glm-5.2 / mistral-medium-latest; add minimax-M3.
- Pool = FAILOVER + KEEP conservative veto (skip quota'd/errored model; any
  available ok=false still vetoes). Failover != first-valid-wins.
- BOUND the subagent fallback (cap / single cheap-model call) — the concrete
  fix for the "no 5m+ review" requirement.
- Add `elapsed_ms` telemetry to critic call-end logs (so cost claims become
  measurable — currently UNVERIFIABLE).
- Preserve shipped budget + BACKENDS_UNAVAILABLE delegation + scoped block.

### Phase 2 — PARKED, measure-first, default OFF
- NEW Tier-0 self-critique injector (not reuse) + Tier-1 cheap verify.
- Run in SHADOW alongside conservative critic; log agreement/disagreement;
  promote only if detection does not regress. Needs explicit user enablement
  (self-modification precedent: guardrail over own output).
- Test delta: shadow-comparison harness (new veto set ⊇ old on fixture corpus).

## Open decisions
- Tier-1 model = mistral-medium-latest (unlimited baseline). Tier-2 redo =
  strongest available (glm-5.2). Failover order: strength for redo, speed for verify.
- Whether Tier-0 self-critique on every high-signal turn is worth the per-turn
  latency — unmeasured; shadow phase decides.

## Next action on resume
Implement Phase 1 (user was approving it). Phase 2 stays parked until user opts
into the shadow experiment.
