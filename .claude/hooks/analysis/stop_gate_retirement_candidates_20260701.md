# Stop-Gate Retirement Candidates — 2026-07-01

**Purpose:** Data-grounded triage of which Stop gates earn their maintenance cost.
Produced from verified telemetry, not inference. No gate deleted — this is a ranked
candidate list. Removal is reversible (flag → demote-to-telemetry → remove) and each
still needs per-gate confirmation.

## Evidence sources (both verified this session)

| Source | Window | Rows | What it proves |
|--------|--------|------|----------------|
| `logs/diagnostics/stop_blocks.jsonl` | 2026-06-18 → 07-01 (13 days) | 149 blocks / 13 gates | Which gates actually **blocked** |
| `.state/stop_gate_telemetry.jsonl` (+rotated) | recent (~this session, small n) | 571 events / 37 gates | Per-gate **decision** distribution (allow/warn/block) |

**Method:** join per-gate `block` count (13d) + telemetry `warn`/`block` (recent) + `GATE_CLASSES`
(policy vs quality, parsed from `Stop.py`). A gate that never blocked in 13 days AND never
warned/blocked in telemetry is a retirement candidate.

## The 12 gates that do real work (KEEP)

`lazy_workaround_gate`(49), `perf_attribution`(28), `skill_first_stop_gate`(18),
`unverified_stance`(17), `cross_validator`(12), `semantic_critic`(8),
`proposal_critique_gate`(6), `deletion_verification_guard`(5), `cjk_drift_detector`(3),
`epistemic_contract`(1), `safety_gate`(1), `diagnostic_analysis_quality`(1 block + 2 warn).
(numbers = blocks in 13 days)

## CAVEAT — the one thing this data cannot see

Advisory-only gates that emit via the `_raw_messages` side channel (not `res.systemMessage`)
log as `decision=allow` in telemetry — `semantic_critic`'s `general_diagnostic` profile is the
proven example. So **"0 warn" in telemetry undercounts advisory activity.** The 13-day *block*
history is the reliable signal; treat telemetry `warn` as a floor. This is why every candidate
below is framed as **demote-to-telemetry-and-monitor**, not **delete** — a 30-day telemetry
watch with the advisory-visibility fix (see companion note) confirms before removal.

## Tier 1 — strongest retire/demote candidates (quality class, ran ≥15×, never fired)

These demonstrably executed 15–16× and produced zero warn, zero block, zero 13-day blocks:

| gate | class | telemetry allow | 13d blocks |
|------|-------|-----------------|-----------|
| `comparative_claim_guard` | quality | 15 | 0 |
| `dependency_chain_guard` | quality | 15 | 0 |
| `intent_artifact_alignment` | quality | 15 | 0 |
| `reasoning_quality_gate` | quality | 15 | 0 |
| `recommendation_gate` | quality | 15 | 0 |
| `reflect_integration` | quality | 15 | 0 |
| `phase0_depends_on_skills` | quality | 16 | 0 |
| `task_contract_fit` | quality | 16 | 0 |
| `tool_sanity` | quality | 16 | 0 |
| `behavior_audit` | quality | 15 | 0 (telemetry-only by design — confirm) |

## Tier 2 — verify wiring first (quality class, 0 telemetry events)

Never even ran in the telemetry window — may be dormant, conditionally-gated, or unwired.
Confirm they execute at all before deciding:

`advisory`, `anti_sycophancy_quality`, `behavior_gates_guidance`, `existence_gate`,
`meta_analysis_trap`, `narrative_intent`, `reasoning_enhanced`

## HOLD — zero-signal POLICY gates (do NOT auto-retire)

Policy gates are safety backstops; rare firing can be correct (the bad thing rarely happens).
Review individually, keep unless proven dead: `acknowledgment_loop`, `artifact_enforcement`,
`cited_content_guard`, `command_execution_validator`, `fake_done`, `frameguard_stop`,
`git_diff_reground`, `cks_correction_anchor`, `removal_completeness`, `repetition_blocker`,
`runtime_claim_enforcement`, `skill_dir_correlation`, `verification_enforcement`,
`post_skill_prose_gate`, `behavior_gates_agreement`, `behavior_gates_blacklist`,
`correction_acknowledgment`.

Note `repetition_blocker`: **0 blocks in 13 days** — the fix proposals earlier this session
targeted it as the site to extend. That it has never fired weakens (does not kill) that plan;
it may simply lack a trackable pattern. Decide with the advisory-visibility data, not now.

## Parse-artifact / unclassified (ignore or classify)

`class` = false parse (matched `"class": "policy"` in GATE_METADATA, not a gate).
`subagent_opportunity`, `task_contract_fit_v2`, `clear_referent_anchors` = real telemetry
gates absent from `GATE_CLASSES` — classify them before any pass.

## Recommended action (reversible, staged)

1. Flip Tier 1 gates to **telemetry-only / advisory** (no block) behind their existing flags.
2. Land the advisory-visibility fix so side-channel advisories become countable.
3. Watch 30 days. Any gate still at zero warn+block → remove (with `git mv`, per repo rule).
4. Re-run this join monthly; it is cheap and self-updating.
