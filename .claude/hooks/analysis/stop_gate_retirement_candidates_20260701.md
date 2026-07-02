# Stop-Gate Retirement Candidates — 2026-07-01

**Purpose:** Data-grounded triage of which Stop gates earn their maintenance cost.
Produced from verified telemetry, not inference. No gate deleted — this is a ranked
candidate list. Removal is reversible (flag → demote-to-telemetry → remove) and each
still needs per-gate confirmation.

## Evidence sources (both verified this session)

| Source | Window | Rows | What it proves |
|--------|--------|------|----------------|
| `logs/diagnostics/stop_blocks.jsonl` | 2026-06-18 → 07-01 (13 days) | 149 blocks / 13 gates | Which gates actually **blocked** |
| `.state/stop_gate_telemetry.jsonl` (+rotated) | **2026-07-01 only — 1 day** | 579 events / 37 gates | Per-gate **decision** distribution (allow/warn/block) |

> **DATA-WINDOW WARNING (added after cross-review):** the telemetry column is a SINGLE
> day. Only the `stop_blocks.jsonl` **block** column spans 13 days. Therefore the Tier-1
> table below is **hypothesis-generating, not decision-ready**: a quality gate that advises
> often but rarely blocks would show 0 blocks (13d) AND its warns would be undersampled in
> a 1-day telemetry window. **Do not demote any gate until ≥7 days of telemetry confirm the
> warn column.** `STOP_TELEMETRY=1` is already live, so this accrues passively — just wait.

**Method:** join per-gate `block` count (13d) + telemetry `warn`/`block` (recent) + `GATE_CLASSES`
(policy vs quality, parsed from `Stop.py`). A gate that never blocked in 13 days AND never
warned/blocked in telemetry is a retirement candidate.

## The 12 gates that do real work (KEEP)

`lazy_workaround_gate`(49), `perf_attribution`(28), `skill_first_stop_gate`(18),
`unverified_stance`(17), `cross_validator`(12), `semantic_critic`(8),
`proposal_critique_gate`(6), `deletion_verification_guard`(5), `cjk_drift_detector`(3),
`epistemic_contract`(1), `safety_gate`(1), `diagnostic_analysis_quality`(1 block + 2 warn).
(numbers = blocks in 13 days)

## CAVEAT — sampling, not blindness (corrected after cross-review)

An earlier draft of this doc claimed advisories are *structurally invisible* to telemetry via
a `_raw_messages` side channel. **That was wrong and is retracted.** Verified: `Stop.py` has
exactly 3 `_raw_messages.append` sites (4732/4736/4808), all in the same gate-loop iteration
on the same `res`; the telemetry `decision` is computed at 4745 from `res["systemMessage"]`,
which is the *same* field the 4808 advisory append requires. So an advisory reaches the model
**iff** telemetry already recorded it as `warn`. Advisories are visible.

The real limitation is **sampling**: the telemetry window is 1 day, so a gate that advises
rarely may show 0 warn simply because it didn't fire in that day. Treat the telemetry `warn`
column as **undersampled**, not as a floor-of-zero. The 13-day *block* history is the only
multi-day signal here. Every candidate is therefore **demote-to-telemetry-and-monitor**, not
**delete** — a ≥7-day (ideally 30-day) telemetry watch confirms before removal. No code change
is needed to enable this; `STOP_TELEMETRY=1` already logs warns correctly.

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

## Addendum 2026-07-01 (evening): dead plugin dispatch trees (pi audit, spot-verified)

pi/MiniMax-M3 liveness audit of 15 files emitting invalid `{"decision":"approve"}`
(CORRECTION 2026-07-01 late: that grep was truncated at head_limit=15 — the full
count is 82 files. All 6 registered entry points are now verified/fixed: skill-guard
2.1.34, cc-aca-epistemic 0.2.70, cc-aca-observability 0.1.22, snapshot 0.5.25,
cc-model-router clean. The remaining ~74 files are unregistered-or-internal and fold
into the July 8 liveness triage — do NOT fix before liveness check.);
Claude spot-verified the settings.json registration claims (only cc-aca-epistemic
L227/L307 + cc-aca-observability are registered among cc-aca plugins; all plugin
hooks.json are `{"hooks":{}}`).

DEAD (no dispatch path — retirement candidates, delete needs per-item approval):
- cc-aca-authority/__lib/router.py + hooks/pretool/PreToolUse_authorization_gate.py
- cc-aca-sdlc/__lib/router.py
- cc-aca-reasoning/__lib/router.py
- cc-aca-safety/__lib/router.py + hooks/pretool/PreToolUse_ownership_colocation_gate.py
- cc-aca-investigation/__lib/router.py + hooks/pretool/PreToolUse_arch_first_enforcer.py
- cc-skills-analysis/skills/gto/hooks/common.py (+ sibling gto hook files, all unregistered)
- skill-guard: skill_forced_eval.py, StopHook_skill_execution_gate.py (from morning sweep)

FIXED 2026-07-01 (live files, approve→{}): skill-guard 2.1.34 (3 events),
cc-aca-epistemic 0.2.70 (router fallback + PreToolUse_investigation_gate).
Inert approve strings remain in in-process Stop gates (never printed) and in
unregistered __main__ paths (perf_attribution L303, deletion_guard L793) — clean
up only if those files survive retirement.

NOTE: cc-aca-safety/PreToolUse_ownership_colocation_gate DEAD contradicts
hooks/CLAUDE.md which documents it as active — but a local copy exists at
P:/.claude/hooks/PreToolUse_ownership_colocation_gate.py (dispatched via local
PreToolUse.py); verify which is canonical before deleting either.
