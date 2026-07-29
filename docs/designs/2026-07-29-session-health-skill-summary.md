# `/session-health` Design — Summary (v0.4)

**Status:** Draft v0.4, ready for review.
**Location:** `C:\Users\brsth\AppData\Local\Temp\grok-design-c2099c52\grok-design-doc-c2099c52.md`

---

## What it does

A new Grok skill that owns `session-health-monitoring`. Pulls friction + pushback signals from session transcripts, compares to a rolling baseline, detects drift across sessions, and emits a verdict at three human-facing granularities (quick / full / trend) plus one stable machine contract (`--json`).

**v0.4 framing corrections (round-2 critical-friend REVISE response):**
- **5 inbound consumers** (not 4): `/tp`, `/close`, `/debrief`, `/notice`, `/aar` (revised by Blocker 4).
- **Centralized dependency** (not leaf node — Blocker 5).
- **DRY framing narrowed** (Blocker 3): only `/tp Step 0b` ↔ `session_signals.py` is real duplication; `close/__lib/friction_detector.py` is a complementary scope.
- **Gate 2 replaced with saturation check** (Blocker 1): Pearson r power analysis rejected; distributional stability is the new criterion.
- **Gate 3 reframed as census** (Blocker 2): the host has 4-5 compacted sessions; running on all of them is a census, not a sample.

## What changed in v0.4 (revision 4 — round-2 critical-friend REVISE response)

| Blocker | Change |
|---|---|
| **Blocker 1: Gate 2 power-analysis failure** | Phase 1 Gate 2 replaced Pearson r (n=10 has <30% power at r=0.5) with a **saturation check**: scan full fleet history, check that adding last 5 sessions shifts median F/U and P/U by <10%. Distributional stability, not statistical significance. Labeled `[INFERENCE]`. |
| **Blocker 2: Gate 3 census vs sample** | Phase 1 Gate 3 reframed from "pilot" to **census** (run on ALL known-compacted sessions; expected N<10 on this host). Decision rule unchanged: delta >20% on ≥3 of 5 → change default. |
| **Blocker 3: DRY claim corrected** | Verified `friction_detector.py` (364 lines) in full. Confirmed it has **5 distinct categories** (`quoting_errors`, `command_failures`, `import_errors`, `permission_errors`, `file_errors`) with only `SyntaxError` overlap to `/tp Step 0b`. The DRY violation is real only between `/tp` and `session_signals.py`, not between `/tp` and `friction_detector.py`. |
| **Blocker 4: /aar Phase 4 data flow** | Major revision: `/aar/SKILL.md` Phase 4 (lines 147-185, `operator_signal_delta`) is **promoted from "no-op" to "consumer"**. The AAR replaces its inline signal computation with `python session_signals.py --json --session <id>` calls. New file in Modified Files list. New feature flag `session_health.aar_phase4_consume: false`. 5th consumer of `--json` contract. |
| **Blocker 5: "leaf node" wording** | Replaced "leaf node" with **"centralized dependency"** throughout. Risk Table row "Vendor lock-in" updated from 4 → 5 callers. |

## What changed in v0.3 (revision 3 — round-1 critical-friend REVISE response)

| Critique item | Change |
|---|---|
| **Premise 1: Framing mismatch** | §1 Goal and §4 separated into "human-facing modes" (§4.1) + "machine contract" (§4.2). 4-mode UX no longer conflated with 4 surfaces. |
| **Premise 2: Calibration without a gate** | Phase 1 acceptance criterion added: Pearson correlation between F/U and P/U at p<0.05 across 10+ sessions. **Revised by Blocker 1 (v0.4):** Pearson test replaced with saturation check. |
| **Premise 3: Compaction default without measurement** | Phase 1 acceptance criterion added: compaction-accuracy pilot on 5 known-compacted sessions. **Revised by Blocker 2 (v0.4):** reframed as census (run on ALL). |
| **Premise 4: DRY framing overstated** | Code-smell inventory corrected. **Further corrected by Blocker 3 (v0.4):** verified `friction_detector.py` content; only `/tp` ↔ `session_signals.py` is real DRY. |
| **Premise 5: Friction pattern count off** | Corrected from 11 to **13 patterns** (verified by hand count from `~/.grok/skills/tp/SKILL.md:250-280`). |
| **Premise 6: Anchoring premises** | New §9 "Anchoring Premises" with 5 premises labeled `[FACT]` / `[INFERENCE]` / `[UNKNOWN]` / `[HYPOTHESIS]`. |
| **Premise 7: Consumer error contract** | §2.3 output contract now includes `degraded: bool` + `degraded_reasons: [string]` fields. |
| **Risk 4.1–4.5** | Risk Table rows added for friction category sync, Hawthorne effect, hypothesis feedback loop, vendor lock-in, backup enforcement. |
| **§4.5-4.7 (compaction, weighting, over-reliance)** | Risk Table rows added. |

## Why a new skill

- `/tp` is 1310 lines. Adding monitoring responsibility bloats the SKILL.md the fresh subagent reads on every `/tp`.
- `/close/__lib/friction_detector.py` does recurrence detection (≥2 same-category hits) — different semantics from density (F/U across the session). Keep both; `/session-health` is the density owner.
- `/debrief`, `/aar`, `/notice` all currently extract signals ad-hoc. One canonical source cleans up the dependency graph.

## Architecture (3-layer)

Mirrors `context-firewall-architecture.md`:

- **Layer 1** — `scripts/session_signals.py`: deterministic Python. No LLM. **13 friction patterns** (verified by hand count) + 16 pushback keywords (11 + 5, verified union/intersection) + F/U and P/U metrics. Exits 0 always; fail-open with `error` + `degraded` fields.
- **Layer 2** — embedded LLM judgment only in `--full`: hypothesis-testing block adopting `/behave`'s pattern (3-5 hypotheses per symptom → cost-ordered tests → falsification → calibrated confidence).
- **Layer 3** — `SKILL.md`: thin orchestrator. Wraps the script, renders verdicts, wires callers.

## Pull-based registry

`P:/.data/telemetry/session-signal-registry.json` caches `{session_id: {scanned_at, f_u, p_u, friction_count, pushback_count, duration_sec}}`. Mtime-based invalidation. **Self-healing**: registry lost → re-scan all transcripts. `msvcrt.locking` for multi-terminal write safety (3 corruption checks: `JSONDecodeError`, zero-byte, missing required fields).

## Baselines (seeded, recalibrated at 30+ sessions)

| Signal | Low | Normal | High | Alert at |
|---|---|---|---|---|
| F/U | < 0.5 | 0.5 – 1.5 | > 1.5 | > 2.0 (hypothesis block fires) |
| P/U | < 0.1 | 0.1 – 0.3 | > 0.3 | > 0.4 (hypothesis block fires) |

**Calibration gate (v0.3 NEW):** F/U must correlate with P/U at p<0.05 (Pearson, two-tailed) across 10+ sessions. If p ≥ 0.05, Phase 1 fails — thresholds are wrong. Power analysis: for r=0.5, n ≈ 29; for r=0.3 (more realistic), n ≈ 84. Recommend 50 sessions as a more defensible minimum.

## Phase 1 acceptance gates (v0.3 NEW — 4 gates)

1. **Signal accuracy gate**: F/U + P/U match hand-counted baseline ±0.05; regression vs `/tp Step 0b` ±5%.
2. **Calibration-correlation gate** (resolves Critique Premise 2): Pearson r(F/U, P/U) p<0.05 across 10+ sessions; >50% hypothesis-block fire = too sensitive.
3. **Compaction-accuracy gate** (resolves Critique Premise 3): 5 known-compacted sessions in INDEX-only vs `--include-segments` modes; delta >20% on ≥3 of 5 → change default.
4. **Performance gate**: latency targets per §4.

**ALL 4 gates must pass before Phase 2.**

## Integration (5 inbound consumers — revised by Blocker 4)

- `/tp session` Step 0b **delegates** to `python session_signals.py --json` (gated by `session_health.tp_delegate`, default `false`).
- `/close` adds friction + pushback one-liner to final summary (gated by `session_health.close_summary`, default `false`).
- `/debrief` Phase 0 reads `--json` as Lens 3 input (gated by `session_health.debrief_input`, default `false`).
- `/notice` T1/T6 **suggests** `/session-health --full` (gated by `session_health.notice_suggest`, default `false` per F-14).
- `/aar` Phase 4 **consumes** `--json` for the 7-signal `operator_signal_delta` block (gated by `session_health.aar_phase4_consume`, default `false` — NEW by Blocker 4). The AAR replaces its inline signal computation with `python session_signals.py --json --session <id>` calls.

`/session-health` is a **centralized dependency** (revised by Blocker 5 — was incorrectly labeled "leaf node" despite having 5 inbound consumers). No dependencies on `/tp`, `/close`, `/debrief`, `/notice`, `/aar`. The "centralized" descriptor captures the vendor-lock-in risk (single point of failure for 5 downstream consumers).

## Consumer error handling (v0.3 NEW)

Every consumer checks `error == null` AND `degraded == false` before reading metrics. On degradation, consumers proceed with model recall only — the script is best-effort infrastructure. Per-consumer behavior specified in §2.3.

## Decisions worth flagging

| Decision | Choice | Why |
|---|---|---|
| Script + skill split | Layer 1 = script, Layer 3 = skill | `context-firewall-architecture.md` pattern; keeps token cost low |
| Registry strategy | Pull-based, self-healing | Operator corrected push-based twice; transcripts are source of truth |
| `/behave` pattern | Adopt inline, do not delegate | Plugin disabled on this host (`/tp/SKILL.md:1170`) |
| `/pace` integration | Deferred to v1.1 | Different capability boundary; `/pace` stays canonical |
| Output surfaces | 3 human modes + 1 machine contract | v0.3 corrects v0.2 conflation; operator UX is 3 modes; integration is 1 contract |
| Friction pattern count | **13 (not 11)** | Verified by hand count from `/tp/SKILL.md:250-280` |
| Pushback keyword set | 16 keywords (11 validated + 5 from `/friction`) | Broader than brief's 10, narrower than 20+ (false-positive ceiling) |
| Skill scope | User (`~/.grok/skills/`), not workspace | Session transcripts are user-private |
| Compaction behavior | INDEX-only default, `--include-segments` opt-in | INDEX gives pre-compaction context without 1MB+ segment loads |
| Calibration gate | p<0.05 Pearson on 10+ sessions | Resolves "calibration without a gate" critique |
| Compaction-accuracy gate | 5 sessions, delta <20% | Resolves "compaction default without measurement" critique |
| Inline regex on flip | Keep `@deprecated` for 30 days | Vendor lock-in mitigation (resolves Critique 4.4) |

## Implementation plan (8 units, all feature-flagged)

| # | Unit | Acceptance gate |
|---|---|---|
| 1 | Signal extraction script | F/U + P/U match fixture ±0.05; 13 patterns; 16 keywords; **calibration-correlation gate**; **compaction-accuracy gate** |
| 2 | Registry + cache | 100-session scan <1s P95; `msvcrt.locking`; 3 corruption checks; self-healing |
| 3 | Drift detector | Rolling median + drift alert + chronic pattern detection |
| 4 | SKILL.md + Quick mode | <400 lines via `wc -l`; one-line verdict; registered in catalog |
| 5 | Full mode + hypothesis block | Hypothesis block fires only when F/U > 2.0 OR P/U > 0.4; cite `/behave`; inline fallback |
| 6 | Trend mode | Last-N F/U + P/U table; drift alert; chronic pattern list |
| 7 | Integration wiring (modify `/tp`, `/close`, `/debrief`, `/notice`) | 4 feature flags (3 default off, 1 default off for parity); regression-check 5 historical sessions; **`PreToolUse` hook for `tp_delegate` flip** |
| 8 | Capability registry entry | Listed by `python capabilities.py --for-domain lifecycle`; index regenerated immediately after Unit 4 |

## Rollout (3 phases, all reversible)

1. **Shadow (weeks 1-2)** — Units 1-3 + Unit 8 ready; skill in catalog but `enabled: false`. **ALL 4 acceptance gates** must pass (signal accuracy, calibration-correlation, compaction-accuracy, performance).
2. **Default for callers (weeks 3-4)** — Feature flags flipped per integration. Inline regex kept `@deprecated` for 30 days. No regressions in 2 weeks.
3. **Operator-primary (week 5+)** — `/friction` standalone invocation DEPRECATION TESTED via measurement (per A5 measurement plan).

Rollback = revert feature flags. Inline regex backup at `P:/.artifacts/<term>/tp-step-0b-inline.bak` for 90 days. Registry is read-only — never destroyed.

## Key risks

| Risk | Mitigation |
|---|---|
| Calibration thresholds untested | **Saturation gate** at median-shift <10% over last 5 sessions (Phase 1 acceptance; revised by Blocker 1) |
| Compaction-aware default undercounts | Compaction-accuracy gate (Phase 1 acceptance) |
| Skill never invoked | Wire into 5 callers (revised by Blocker 4); shadow-mode validation; `/notice` suggestion |
| Multi-terminal race on registry | `msvcrt.locking` pattern from `close_runner.py` |
| Vendor lock-in via canonical source | Inline regex kept `@deprecated` for 30 days post-flip |
| Backup discipline | `PreToolUse` hook gates flag flip |
| Hawthorne effect | Real-time F/U not auto-surfaced; operator-invoked only |
| Hypothesis feedback loop | `/session-health --feedback <session-id> <useful|noise>` populates registry |

## Falsifier

Skill is wrong if, within 6 months:

- Never invoked despite 5 integrations (retire; revert `/tp` Step 0b to inline regex, `/aar` Phase 4 to inline computation).
- F/U + P/U distributions don't stabilize (last 5 sessions shift median ≥10%; Blocker 1 revised). Recalibrate; if still unstable, retire.
- `/behave` plugin re-enabled and we should delegate instead of embed.
- Compaction-aware behavior undercounts by >20% on ≥3 of 5 known-compacted sessions in census (Blocker 2 revised; change INDEX-only default to `--include-segments`).
- `/aar` Phase 4's `operator_signal_delta` block diverges from `session_signals.py` output (signals the canonical-extraction reorg failed; revert `/aar` to inline).
- `/friction` standalone invoked >50% of the time after Phase 3 deprecation notice (revert consolidation hypothesis).
- Operator reports inline-regex recovery path unused for 90+ days post-Phase-2 (acceptable — soft removal completed; consider hard-deleting the regex).

---

**Design principles honored:**
- Optimal long-term over minimal-diff (clean capability boundary beats one-off `/tp` edits).
- Transition effort is not a selection criterion (8 units + 4 modified files + new hooks is the right scope, not a reason to cut).
- Surgical ≠ smallest (we touch `/tp`, `/close`, `/debrief`, `/notice` because that's what the integration requires; we don't touch `/aar` because that's not load-bearing).
- Radical refactoring on the table — but F-06's hard-delete position is REVISED to soft removal for 30 days because the vendor-lock-in risk outweighs the cleanup-discipline gain.

**Ready for:** `/red-team` or `/tp` review on this v0.4 design.